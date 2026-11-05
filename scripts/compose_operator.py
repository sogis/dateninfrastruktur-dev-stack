#!/usr/bin/env python3
"""Scoped operator activation through the canonical Compose context."""
import argparse,sys
from compose_operations import resolve

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['activate']);p.add_argument('--env');p.add_argument('--project');p.add_argument('values',nargs=3);a=p.parse_args()
    c=resolve(a.env,a.project)
    result=c.command(['--profile','tools','run','--rm','--no-deps','management-operator','activate',*a.values])
    print(c.redact(result.stdout),end='')
if __name__=='__main__':
    try:main()
    except Exception as error:print(str(error) if isinstance(error,RuntimeError) else 'Explicit operator failed; private details retained',file=sys.stderr);sys.exit(1)
