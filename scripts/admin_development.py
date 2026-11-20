"""Switch the Admin service in the existing Compose project."""
import argparse
from contextlib import suppress
import fcntl
import os
import re
import sys
import subprocess

from compose_runtime import (
    ADMIN_DEV_IMAGE_FILE, ADMIN_DEV_OVERLAY, ROOT, ComposeContext, docker_env, write_private,
)

IMAGE_ID = re.compile(r'sha256:[0-9a-f]{64}')


def switch_admin(context, action):
    image_file = context.runtime / ADMIN_DEV_IMAGE_FILE
    saved = image_file.read_text().strip() if image_file.exists() else None
    if saved is not None and not IMAGE_ID.fullmatch(saved):
        raise RuntimeError('Invalid saved regular Admin image ID')
    enable = action == 'on'
    if enable and saved:
        raise RuntimeError('Switch Admin development off before enabling it again')
    if not enable and not saved:
        print('Admin uses its regular image.')
        return

    containers = context.command(['ps', '-aq', 'admin']).stdout.split()
    if not containers and not enable:
        image_file.unlink()
        print('Admin development cleared. Start the regular stack.')
        return
    if len(containers) != 1:
        raise RuntimeError('Expected one Admin container. Start the configured stack first.')
    result = subprocess.run(
        ['docker', 'inspect', '--format',
         '{{.Image}} {{.State.Running}} {{with .State.Health}}{{.Status}}{{else}}-{{end}} '
         '{{index .Config.Labels "com.docker.compose.project.config_files"}}', containers[0]],
        env=docker_env(), capture_output=True, text=True,
    )
    if result.returncode:
        raise RuntimeError('Could not read the current Admin image and status')
    previous, status, health, files = result.stdout.strip().split(maxsplit=3)
    running = status == 'true'
    active = files.endswith(',' + str(ADMIN_DEV_OVERLAY))
    if enable and not (running and health == 'healthy'):
        raise RuntimeError('Start the configured stack and wait for a healthy Admin before switching.')

    source = ROOT.parent / 'dateninfrastruktur-admin'
    state = context.runtime / 'admin-dev'
    dev = {'DI_ADMIN_DEV_SOURCE': str(source), 'DI_ADMIN_DEV_STATE': str(state)}
    if state.is_symlink():
        raise RuntimeError('Admin development directory may not be a symlink')
    candidate = saved
    if enable:
        if not (source / 'scripts/dev_reload.py').is_file():
            raise RuntimeError('Admin development requires the Admin source checkout')
        state.mkdir(mode=0o700, exist_ok=True)
        candidate = f'dateninfrastruktur-admin-dev:{context.project}'
        context.command(['build', 'admin'], admin_dev=True, overrides=dict(dev, DI_ADMIN_DEV_IMAGE=candidate))
        write_private(image_file, previous + '\n')

    def replace(image, development, wait):
        timeout = '900' if development else '240'
        flags = ['--wait', '--wait-timeout', timeout] if wait else ['--no-start']
        overrides = dict(dev, DI_ADMIN_DEV_IMAGE=image) if development else {'ADMIN_IMAGE': image}
        context.command(['up', '--no-deps', '--no-build', '--pull', 'never', *flags, 'admin'],
                        admin_dev=development, overrides=overrides)

    try:
        replace(candidate, enable, running)
    except RuntimeError as error:
        details = ''
        with suppress(OSError, RuntimeError):
            logs = context.command(['logs', '--tail', '40', 'admin'], check=False)
            details = context.redact(logs.stdout + logs.stderr)[-6000:]
        try:
            replace(previous, active, running)
        except RuntimeError as rollback_error:
            raise RuntimeError(
                f'Admin switch failed: {error}\n{details}\nRestoring the previous Admin failed: {rollback_error}\n'
                'Development state retained. Retry admin_development.py off with the same --env.'
            ) from rollback_error
        if not saved:
            image_file.unlink()
        raise RuntimeError(f'Admin switch failed. Previous Admin restored.\n{error}\n{details}') from error

    if not enable:
        image_file.unlink()
    print('Admin development enabled.' if enable else 'Regular Admin image restored.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('on', 'off'))
    parser.add_argument('--env', required=True)
    args = parser.parse_args()
    context = ComposeContext(args.env)
    directory = os.open(context.runtime, os.O_RDONLY)
    try:
        fcntl.flock(directory, fcntl.LOCK_EX)
        switch_admin(context, args.action)
    finally:
        os.close(directory)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError):
        sys.exit('Invalid or inaccessible private Compose configuration')
    except RuntimeError as error:
        sys.exit(str(error))
