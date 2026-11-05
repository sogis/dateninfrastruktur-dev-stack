#!/usr/bin/env python3
"""Focused G14/G19 regression; no browser/schema migration or user resources."""
import secrets
from compose_runtime import ROOT,init_context,ComposeContext,write_private
from test_consolidation_f1 import reserve_ports,cleanup
def run():
    c=init_context('mag-g1-foundation-'+secrets.token_hex(5),reserve_ports(),True)
    def command(args):
        p=c.command(args,check=False)
        with (c.runtime/'foundation-test.log').open('a') as stream:stream.write(c.redact(p.stdout+p.stderr))
        if p.returncode:raise RuntimeError('Focused Foundation fixture failed; private '+str(c.runtime/'foundation-test.log'))
        return p.stdout
    try:
        command(['build','postgres','management-tool-build'])
        command(['up','--no-build','-d','--wait','--wait-timeout','120','garage'])
        command(['--profile','setup','run','--rm','--no-deps','garage-setup']);c=ComposeContext(c.env_file)
        command(['--profile','setup','run','--rm','--no-deps','--entrypoint','python3','management-setup','-c',"from pathlib import Path; assert not Path('/opt/stack-tools/cutover_g1.py').exists(); print('PASS G19 normal tool image has no one-shot cutover module')"])
        write_private(c.runtime/'cutover_g1.py',(ROOT/'tests/ingestion/retired/cutover_g1.py').read_text())
        write_private(c.runtime/'foundation-fixture.py',(ROOT/'tests/ingestion/foundation-fixture.py').read_text())
        names=['DI_TEST_FIXTURE','COMPOSE_PROJECT_NAME','INSTANCE_ID','DI_STORAGE_BUCKET','DI_STORAGE_ENDPOINT','DI_STORAGE_REGION']
        print(command(['--profile','setup','run','--rm','--no-deps',*[v for name in names for v in ['-e',name]],'--entrypoint','python3','management-setup','/runtime/foundation-fixture.py']).strip())
    finally:cleanup(c)
if __name__=='__main__':run()
