#!/usr/bin/env python3
"""Explicit scoped first manage_submitters assignment; no file activation bypass."""
import argparse,pathlib,sys
from compose_operations import resolve

def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['bootstrap-submitters']);parser.add_argument('request_file');parser.add_argument('--env');parser.add_argument('--project');args=parser.parse_args()
    context=resolve(args.env,args.project);path=pathlib.Path(args.request_file).absolute()
    if path.is_symlink() or not path.is_file() or path.stat().st_mode&0o077 or path.stat().st_size>16384:raise RuntimeError('Private bounded regular bootstrap request required')
    path=path.resolve()
    if not path.is_relative_to(context.runtime):raise RuntimeError('Place the explicit bootstrap request inside the selected private runtime')
    result=context.command(['--profile','tools','run','--rm','--no-deps','management-operator','/runtime/'+path.relative_to(context.runtime).as_posix()])
    print(context.redact(result.stdout),end='')
if __name__=='__main__':
    try:main()
    except Exception as error:print(str(error) if isinstance(error,RuntimeError) else 'Explicit operator failed; private details retained',file=sys.stderr);sys.exit(1)
