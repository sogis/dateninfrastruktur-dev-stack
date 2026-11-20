"""Explicitly provision the databases, storage and roles of one Compose instance."""
import argparse
import fcntl
import json
import sys

from compose_runtime import (
    ADMIN_DEV_MARKER, FOUNDATION_UP, SETUP_RUN, VOLUMES, ComposeContext, docker_output, render_gateway, write_private,
)


def setup(context):
    _, retained = context.verify_resources()
    if (context.runtime / ADMIN_DEV_MARKER).exists():
        raise RuntimeError('Switch Admin development off before setup')

    context.command([*FOUNDATION_UP, 'postgres'])
    action = 'verify'
    if not retained:
        query = "SELECT EXISTS (SELECT FROM pg_database WHERE datname='dateninfrastruktur_management');"
        exists = context.command(['exec', '-T', 'postgres', 'psql', '-X', '-q', '-At',
                                  '-U', 'postgres', '-d', 'postgres', '-c', query]).stdout.strip()
        if exists not in {'f', 't'}:
            raise RuntimeError('Could not determine whether the management database exists')
        if exists == 'f':
            context.command([*SETUP_RUN, 'postgres-init'])
            action = 'setup'
    context.command([*SETUP_RUN, 'management-setup', action])

    for filename in ('garage.toml', 'realm-initial.json'):
        if not (context.runtime / filename).is_file():
            raise RuntimeError(f'Missing private {filename}; restore it before setup')
    context.command([*FOUNDATION_UP, 'garage'])
    context.command([*SETUP_RUN, 'garage-setup'])
    context.values = ComposeContext(context.env_file).values
    render_gateway(context)
    if not retained:
        context.command([*FOUNDATION_UP, 'clickhouse'])
        context.command([*SETUP_RUN, 'clickhouse-init'])
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
