"""Switch the Admin service in the existing Compose project."""
import argparse
from contextlib import suppress
import fcntl
import json
from pathlib import Path
import re
import sys
import tempfile

from compose_runtime import ADMIN_DEV_MARKER, ADMIN_DEV_OVERLAY, ROOT, ComposeContext, write_private

IMAGE_ID = re.compile(r'sha256:[0-9a-f]{64}')


def switch_admin(context, action):
    marker = context.runtime / ADMIN_DEV_MARKER
    containers, _ = context.verify_resources(require_setup=True)
    saved = json.loads(marker.read_text()) if marker.exists() else None
    if saved is not None and (saved['instance'] != context.values['INSTANCE_ID'] or not IMAGE_ID.fullmatch(saved['image'])):
        raise RuntimeError('OWNERSHIP_MISMATCH: Admin development state')
    enable = action == 'on'
    if not enable and not saved:
        print('Admin uses its regular image.')
        return
    if not enable and not containers:
        marker.unlink()
        print('Admin development cleared. Start the regular stack.')
        return

    admins = [row for row in containers
              if row['Config']['Labels'].get('com.docker.compose.service') == 'admin'
              and row['Config']['Labels'].get('com.docker.compose.oneoff', '').lower() != 'true']
    if len(admins) != 1:
        raise RuntimeError('Expected one existing Admin container. Start the configured stack first.')
    before, = admins
    active = before['Config']['Labels']['com.docker.compose.project.config_files'].endswith(
        ',' + str(ADMIN_DEV_OVERLAY))
    running = before['State']['Running']
    healthy = before['State'].get('Health', {}).get('Status') == 'healthy'
    if enable and not (running and (active or healthy)):
        raise RuntimeError('Start the configured stack and wait for a healthy Admin before switching.')

    instance = context.values['INSTANCE_ID']
    source = ROOT.parent / 'dateninfrastruktur-admin'
    state = context.runtime / 'admin-dev'
    dev = {'DI_ADMIN_DEV_SOURCE': str(source), 'DI_ADMIN_DEV_STATE': str(state)}
    if (enable or active) and state.is_symlink():
        raise RuntimeError('OWNERSHIP_MISMATCH: Admin development directory is a symlink')
    if enable:
        if not (source / 'scripts/dev_reload.py').is_file():
            raise RuntimeError('Admin development requires the Admin source checkout')
        state.mkdir(mode=0o700, exist_ok=True)
        candidate = f'dateninfrastruktur-admin-dev:{instance}'
        context.command(['build', 'admin'], admin_dev=True, overrides=dict(dev, DI_ADMIN_DEV_IMAGE=candidate))
    else:
        candidate = saved['image']

    if not saved:
        with tempfile.TemporaryDirectory(dir=context.runtime) as directory:
            pending = Path(directory) / marker.name
            write_private(pending, json.dumps({'instance': instance, 'image': before['Image']}) + '\n')
            pending.replace(marker)

    def replace(image, development, wait):
        timeout = '900' if development else '240'
        flags = ['--wait', '--wait-timeout', timeout] if wait else ['--no-start']
        overrides = dict(dev, DI_ADMIN_DEV_IMAGE=image) if development else {'ADMIN_IMAGE': image}
        context.command(['up', '--no-deps', '--no-build', '--pull', 'never', *flags, 'admin'],
                        admin_dev=development, overrides=overrides)

    postgres_running = any(
        row['Config']['Labels'].get('com.docker.compose.service') == 'postgres' and row['State']['Running']
        for row in containers
    )
    try:
        replace(candidate, enable, running or postgres_running)
    except RuntimeError as error:
        details = ''
        with suppress(OSError, RuntimeError):
            logs = context.command(['logs', '--tail', '40', 'admin'], check=False)
            details = context.redact(logs.stdout + logs.stderr)[-6000:]
        try:
            replace(before['Image'], active, running)
        except RuntimeError as rollback_error:
            raise RuntimeError(
                f'Admin switch failed: {error}\n{details}\nRestoring the previous Admin failed: {rollback_error}\n'
                'Development state retained. Retry admin_development.py off with the same --env.'
            ) from rollback_error
        if not saved:
            marker.unlink()
        raise RuntimeError(f'Admin switch failed. Previous Admin restored.\n{error}\n{details}') from error

    if not enable:
        marker.unlink()
    print('Admin development enabled.' if enable else 'Regular Admin image restored.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('on', 'off'))
    parser.add_argument('--env', required=True)
    args = parser.parse_args()
    context = ComposeContext(args.env)
    with (context.runtime / 'lifecycle.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        switch_admin(context, args.action)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError):
        sys.exit('Invalid or inaccessible private Compose configuration')
    except RuntimeError as error:
        sys.exit(str(error))
