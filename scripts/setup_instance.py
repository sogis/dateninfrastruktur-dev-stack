"""Explicitly provision the databases, storage and roles of one Compose instance."""
import argparse
import fcntl
import json
import sys

from compose_runtime import ADMIN_DEV_MARKER, ComposeContext, render, write_private


def setup(context):
    context.verify_resources()
    if (context.runtime / ADMIN_DEV_MARKER).exists():
        raise RuntimeError('Switch Admin development off before setup')
    retained = context.has_setup()
    if not retained:
        jenkins_id = context.configured_jenkins_id()
    up = ['up', '--no-build', '--pull', 'never', '-d', '--wait', '--wait-timeout', '240']
    run = ['--profile', 'setup', 'run', '--rm', '--no-deps', '--pull', 'never']

    context.command([*up, 'postgres'])
    query = "SELECT count(*) FROM pg_database WHERE datname='dateninfrastruktur_management';"
    count = context.command(['exec', '-T', 'postgres', 'psql', '-X', '-q', '-At',
                             '-U', 'postgres', '-d', 'postgres', '-c', query]).stdout.strip()
    if retained and count != '1':
        raise RuntimeError('Known management database is missing; restore it before setup')
    if count not in {'0', '1'}:
        raise RuntimeError('Could not determine whether the management database exists')

    if count == '0':
        context.command([*run, 'postgres-init'])
    context.command([*run, 'management-setup', *(['verify'] if count == '1' else [])])
    context.command([*up, 'garage'])
    context.command([*run, 'garage-setup'])
    context.values = ComposeContext(context.env_file).values
    render(context)
    if not retained:
        context.command([*up, 'clickhouse'])
        context.command([*run, 'clickhouse-init'])
        context.command(['up', '--no-start', '--no-deps', '--no-build', '--pull', 'never', 'jenkins', 'superset'],
                        overrides={'JENKINS_IMAGE': jenkins_id})
        context.verify_resources(require_volumes=True)
        write_private(context.runtime / 'setup-complete.json', json.dumps({
            'instance': context.values['INSTANCE_ID'], 'mode': 'explicit-setup',
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
