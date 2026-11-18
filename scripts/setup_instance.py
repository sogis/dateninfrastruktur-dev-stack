"""Explicitly provision the databases, storage and roles of one Compose instance."""
import argparse
import fcntl
import json
import sys

from compose_runtime import ADMIN_DEV_MARKER, VOLUMES, ComposeContext, docker_output, read_env, render, write_private


def setup(context):
    context.verify_resources()
    if (context.runtime / ADMIN_DEV_MARKER).exists():
        raise RuntimeError('Switch Admin development off before setup')
    retained = context.has_setup()
    up = ['up', '--no-build', '--pull', 'never', '-d', '--wait', '--wait-timeout', '240']
    run = ['--profile', 'setup', 'run', '--rm', '--no-deps', '--pull', 'never']

    context.command([*up, 'postgres'])
    query = "SELECT count(*) FROM pg_database WHERE datname='dateninfrastruktur_management';"
    count = context.command(['exec', '-T', 'postgres', 'psql', '-X', '-q', '-At',
                             '-U', 'postgres', '-d', 'postgres', '-c', query]).stdout.strip()
    if count == '1':
        context.command([*run, 'management-setup', 'verify'])
    elif count == '0' and not retained:
        context.command([*run, 'postgres-init'])
        context.command([*run, 'management-setup'])
    else:
        raise RuntimeError('Known management database is missing; restore it before setup')

    render(context)
    context.command([*up, 'garage'])
    context.command([*run, 'garage-setup'])
    context.values = read_env(context.env_file)
    if not retained:
        context.command([*up, 'clickhouse'])
        context.command([*run, 'clickhouse-init'])
        # Bind the two application volumes before either application is installed.
        for key in ('JENKINS_VOLUME', 'SUPERSET_VOLUME'):
            docker_output('volume', 'create', '--label', f'com.docker.compose.project={context.project}',
                          '--label', f'com.docker.compose.volume={VOLUMES[key][0]}', '--', context.values[key])
        context.verify_resources(require_volumes=True)
        write_private(context.runtime / 'setup-complete.json', json.dumps({
            'instance': context.values['INSTANCE_ID'],
            'volumes': context.volume_bindings(),
        }, indent=2) + '\n')
    print('Explicit setup complete')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env', required=True)
    args = parser.parse_args()
    context = ComposeContext(args.env)
    with (context.runtime / 'lifecycle.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        setup(context)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError):
        sys.exit('Invalid or inaccessible private Compose configuration')
    except RuntimeError as error:
        sys.exit(str(error))
