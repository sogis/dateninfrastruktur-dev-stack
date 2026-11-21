"""Explicitly provision the databases, storage and roles of one Compose instance."""
import argparse
import fcntl
import os
import sys

from compose_runtime import FOUNDATION_UP, SETUP_RUN, ComposeContext, render_gateway


def setup(context):
    for filename in ('garage.toml', 'realm-initial.json'):
        if not (context.runtime / filename).is_file():
            raise RuntimeError(f'Missing private {filename}; restore it before setup')

    context.command([*FOUNDATION_UP, 'postgres'])
    context.command([*SETUP_RUN, 'postgres-init'])
    context.command([*SETUP_RUN, 'management-setup', 'setup'])

    context.command([*FOUNDATION_UP, 'garage'])
    context.command([*SETUP_RUN, 'garage-setup'])
    context.values = ComposeContext(context.env_file).values
    render_gateway(context)
    context.command([*FOUNDATION_UP, 'clickhouse'])
    context.command([*SETUP_RUN, 'clickhouse-init'])
    print('Explicit setup complete')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env', required=True)
    args = parser.parse_args()
    context = ComposeContext(args.env)
    # Serialize deliberate changes to this instance without a runtime marker.
    directory = os.open(context.runtime, os.O_RDONLY)
    try:
        fcntl.flock(directory, fcntl.LOCK_EX)
        setup(context)
    finally:
        os.close(directory)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError):
        sys.exit('Invalid or inaccessible private Compose configuration')
    except RuntimeError as error:
        sys.exit(str(error))
