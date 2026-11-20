#!/usr/bin/env python3
"""Import a bootstrap XTF or export the selected management database."""
import argparse
import os
from pathlib import Path
import sys

from compose_runtime import SETUP_RUN, ComposeContext


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('import', 'export'))
    parser.add_argument('file', type=Path)
    parser.add_argument('--env', required=True)
    args = parser.parse_args()
    context = ComposeContext(args.env)
    path = args.file.absolute()
    if path != path.resolve() or not path.is_relative_to(context.runtime):
        raise RuntimeError('Place the XTF file in the selected private runtime')
    if args.action == 'import' and (not path.is_file() or path.stat().st_mode & 0o077):
        raise RuntimeError('Import requires a private regular XTF file')
    context.verify_resources()
    inside = '/runtime/' + path.relative_to(context.runtime).as_posix()
    result = context.command([*SETUP_RUN,
                              '--user', f'{os.getuid()}:{os.getgid()}',
                              '-e', 'DI_TOOL_RUNTIME=/tmp/di-management-transfer',
                              'management-setup', args.action, inside])
    print(context.redact(result.stdout), end='')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError):
        sys.exit('Invalid or inaccessible private Compose configuration')
    except RuntimeError as error:
        print(error, file=sys.stderr)
        sys.exit(1)
