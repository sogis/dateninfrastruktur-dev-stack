#!/usr/bin/env python3
"""Submission authorization and HTTP security in a fresh, isolated canonical PG project, synthetic data only."""
import secrets
from compose_runtime import init_context,update_context,write_private
from ingestion_test_runtime import reserve_ports,cleanup

def run():
    c=init_context('mag-submission-backend-'+secrets.token_hex(5),reserve_ports(),True)
    def command(args):
        result=c.command(args,check=False)
        with (c.runtime/'backend.log').open('a') as out:out.write(c.redact(result.stdout+result.stderr))
        if result.returncode:raise RuntimeError('Submission backend check failed; private '+str(c.runtime/'backend.log'))
        return result.stdout
    try:
        command(['build','postgres','test-tool-build'])
        c=update_context(c,{'TOOL_IMAGE':c.values['TEST_TOOL_IMAGE']})
        command(['up','--no-build','-d','--wait','--wait-timeout','120','postgres'])
        command(['--profile','setup','run','--rm','--no-deps','postgres-init'])
        # test-fixture uses the test-tools image. Explicit setup, never startup migration/seed.
        command(['--profile','setup','run','--rm','--no-deps','--entrypoint','python3','management-setup','/opt/admin/scripts/setup_explicit.py','setup'])
        output=command(['--profile','test','run','--rm','--no-deps','--entrypoint','java','test-fixture','-cp','/opt/compose-test/classes:/opt/compose-test/lib/*','ch.so.agi.dateninfrastruktur.admin.SubmissionAuthorizationIT'])
        for line in output.splitlines():
            if line.startswith('PASS '):print(line)
        assert 'PASS G28 ' in output,'No completed assertion run'
        output=command(['--profile','test','run','--rm','--no-deps','-e','DI_CH_PROJECTOR_PASSWORD',
            '--entrypoint','java','test-fixture','-cp','/opt/compose-test/classes:/opt/compose-test/lib/*',
            'ch.so.agi.dateninfrastruktur.admin.IngestionHttpSecurityIT'])
        assert 'PASS G24 real RSA/JWKS HTTP' in output,'No completed cryptographic HTTP test'
        print('PASS G24 real RSA/JWKS HTTP authentication, strict JSON, user/service/role separation')
        print('ASSERTIONS=7 SKIP=0')
    finally:cleanup(c)
if __name__=='__main__':run()
