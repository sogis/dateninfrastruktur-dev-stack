"""Explicitly provision the databases, storage and roles of one Compose instance."""
import argparse
import fcntl
import json
import sys

from compose_runtime import ADMIN_DEV_MARKER, ComposeContext, read_env, render, write_private


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
        # Compose must allocate both volumes before the complete marker can bind them.
        context.command(['up', '--no-start', '--no-deps', '--no-build', '--pull', 'never', 'jenkins', 'superset'],
                        overrides={'JENKINS_IMAGE': context.configured_jenkins_id()})
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
