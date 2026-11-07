"""Switch the Admin service in the existing Compose project."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from compose_runtime import ADMIN_DEV_MARKER, ADMIN_DEV_OVERLAY, ROOT, write_private

IMAGE_ID = re.compile(r'sha256:[0-9a-f]{64}')


def image_available(reference):
    return subprocess.run(['docker', 'image', 'inspect', reference], capture_output=True).returncode == 0


def development_overrides(context, *, require_sources):
    source = ROOT.parent / 'dateninfrastruktur-admin'
    topics = (ROOT / context.values.get('THEMEN_REPO_DIR', '../dateninfrastruktur-themenrepo')).resolve()
    state = context.runtime / 'admin-dev'
    if require_sources:
        if not (source / 'scripts/dev_reload.py').is_file() or not (topics / 'contracts').is_dir():
            raise RuntimeError('Admin development requires the Admin and Topics source checkouts')
        if state.is_symlink():
            raise RuntimeError('OWNERSHIP_MISMATCH: Admin development directory is a symlink')
        state.mkdir(mode=0o700, exist_ok=True)
    dockerfile = ROOT / 'services/admin-dev/Dockerfile'
    revision = hashlib.sha256(dockerfile.read_bytes()).hexdigest()[:16]
    return {
        'DI_ADMIN_DEV_IMAGE': f'dateninfrastruktur-admin-dev:{context.values["INSTANCE_ID"]}-{revision}',
        'DI_ADMIN_DEV_SOURCE': str(source),
        'DI_ADMIN_DEV_TOPICS': str(topics),
        'DI_ADMIN_DEV_STATE': str(state),
    }


def current_admin(containers):
    rows = [row for row in containers
            if row['Config']['Labels'].get('com.docker.compose.service') == 'admin'
            and row['Config']['Labels'].get('com.docker.compose.oneoff', '').lower() != 'true']
    if len(rows) != 1:
        raise RuntimeError('Expected one existing Admin container. Start the configured stack first.')
    return rows[0]


def switch_admin(context, action):
    marker = context.runtime / ADMIN_DEV_MARKER
    containers = context.verify_project()
    before = current_admin(containers)
    labels = before['Config']['Labels']
    active = labels['com.docker.compose.project.config_files'].endswith(',' + str(ADMIN_DEV_OVERLAY))
    running = before['State']['Running']
    if action == 'off' and not marker.exists():
        print('Admin uses its regular image.')
        return
    if marker.exists():
        saved = json.loads(marker.read_text())
        original = saved['image']
        original_reference = saved['reference']
        if saved['instance'] != context.values['INSTANCE_ID'] or not IMAGE_ID.fullmatch(original):
            raise RuntimeError('OWNERSHIP_MISMATCH: Admin development state')
    else:
        original = before['Image']
        original_reference = before['Config']['Image']

    if action == 'on' and not running:
        raise RuntimeError('Start the configured stack before enabling Admin development.')
    if action == 'on' and not active and before['State'].get('Health', {}).get('Status') != 'healthy':
        raise RuntimeError('The regular Admin container must be healthy before switching to development.')

    postgres_running = any(
        row['Config']['Labels'].get('com.docker.compose.service') == 'postgres' and row['State']['Running']
        for row in containers
    )
    dev = development_overrides(context, require_sources=(action == 'on')) if active or action == 'on' else {}
    if not image_available(original):
        raise RuntimeError('Previous Admin image is missing. Restore it locally before switching.')
    if action == 'on' and not image_available(dev['DI_ADMIN_DEV_IMAGE']):
        context.command(['build', 'admin'], admin_dev=True, overrides=dev)

    def replace(development, wait, rollback=False):
        # Prefer the original reference when it still identifies the exact image.
        normal_image = original
        if not development:
            probe = subprocess.run(
                ['docker', 'image', 'inspect', '--format', '{{.Id}}', original_reference],
                capture_output=True, text=True,
            )
            if probe.returncode == 0 and probe.stdout.strip() == original:
                normal_image = original_reference
        development_env = dev if not rollback else {**dev, 'DI_ADMIN_DEV_IMAGE': before['Image']}
        flags = ['--wait', '--wait-timeout', '420'] if wait else ['--no-start']
        context.command(
            ['up', '--no-deps', '--no-build', '--pull', 'never', *flags, 'admin'],
            admin_dev=development, overrides=development_env if development else {'ADMIN_IMAGE': normal_image},
        )

    if not marker.exists():
        with tempfile.TemporaryDirectory(dir=context.runtime) as directory:
            pending = Path(directory) / marker.name
            write_private(pending, json.dumps({
                'instance': context.values['INSTANCE_ID'], 'image': original, 'reference': original_reference,
            }) + '\n')
            pending.replace(marker)
    try:
        replace(action == 'on', running or postgres_running)
    except RuntimeError as error:
        logs = context.command(['logs', '--tail', '40', 'admin'], check=False)
        details = context.redact(logs.stdout[-6000:])
        try:
            replace(active, running, rollback=True)
        except RuntimeError as rollback_error:
            raise RuntimeError(
                f'Admin switch failed: {error}\n{details}\nRestoring the previous Admin failed: {rollback_error}\n'
                'Development state retained. Retry dev.sh admin off.'
            ) from rollback_error
        if not active:
            marker.unlink()
        raise RuntimeError(f'Admin switch failed. Previous Admin restored.\n{error}\n{details}') from error

    if action == 'off':
        marker.unlink()
    print('Admin development enabled.' if action == 'on' else 'Regular Admin image restored.')
