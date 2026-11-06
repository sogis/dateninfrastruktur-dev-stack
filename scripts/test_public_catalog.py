#!/usr/bin/env python3
"""Run the Sodata and Admin catalog mutation contract on one owned PostgreSQL."""
import os
import secrets
import socket
import subprocess
import time
import xml.etree.ElementTree as ET

from compose_runtime import ROOT, init_context, write_private
from ingestion_test_runtime import cleanup, reserve_ports


def main():
    ports = reserve_ports()
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    context = init_context('mag-public-catalog-'+secrets.token_hex(5), ports, True)
    container = None
    try:
        context.command(['build','postgres','management-tool-build'])
        container = context.command([
            'run','--no-deps','-d','--use-aliases','--publish',f'127.0.0.1:{port}:5432','postgres',
        ]).stdout.strip().splitlines()[-1]
        context.verify_project()
        for _ in range(60):
            ready = subprocess.run(['docker','exec',container,'pg_isready','-U','postgres'],
                                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            if ready.returncode==0:
                break
            time.sleep(1)
        else:
            raise RuntimeError('Isolated PostgreSQL did not become ready')
        context.command(['--profile','setup','run','--rm','--no-deps','postgres-init'])
        context.command(['--profile','setup','run','--rm','--no-deps','management-setup','setup'])

        admin = ROOT.parent/'dateninfrastruktur-admin'
        sodata = ROOT.parent/'dateninfrastruktur-sodata'
        fixture = context.runtime/'public-catalog-fixture.json'
        url = f'jdbc:postgresql://127.0.0.1:{port}/dateninfrastruktur_management'
        env = dict(os.environ, DI_TEST_URL=url, DI_PUBLIC_TEST_URL=url, DI_ADMIN_SOURCE=str(admin),
            DI_PORTAL_FIXTURE=str(fixture), DI_TEST_WRITER_PASSWORD=context.values['DI_WRITER_PASSWORD'],
            DI_TEST_AUTHZ_PASSWORD=context.values['DI_AUTHZ_PASSWORD'],
            DI_TEST_ADMIN_PASSWORD=context.values['POSTGRES_ADMIN_PASSWORD'],
            DI_PUBLIC_TEST_ADMIN_PASSWORD=context.values['POSTGRES_ADMIN_PASSWORD'],
            DI_PUBLIC_TEST_PASSWORD=context.values['DI_PUBLIC_PASSWORD'])
        run_test(context,admin,env,'integrationTest','ch.so.agi.dateninfrastruktur.admin.DatabaseCatalogFixtureIT')
        run_test(context,sodata,env,'managementDatabaseTest',
                 'ch.so.agi.datenportal.catalog.database.DatabaseCatalogModeIT')
        run_test(context,sodata,env,'managementDatabaseTest',
                 'ch.so.agi.datenportal.catalog.database.PublicCatalogRoleIT')
        print('PASS catalog mutation is visible without reload in two live Sodata instances')
        print('PASS Sodata outage fails closed; public role can only read approved views')
        print('ASSERTIONS=3 SKIP=0')
    finally:
        if container:
            context.verify_project()
            subprocess.run(['docker','rm','--force',container],check=True,capture_output=True)
        cleanup(context)


def run_test(context, source, env, task, test):
    process = subprocess.run(['./gradlew','--no-daemon',task,'--tests',test,'--console=plain'],
                             cwd=source,env=env,capture_output=True,text=True)
    path = context.runtime/(test.rsplit('.',1)[-1]+'.log')
    write_private(path,context.redact(process.stdout+process.stderr))
    if process.returncode:
        raise RuntimeError(f'Catalog test failed; private log {path}')
    report = source/'build/test-results'/task/f'TEST-{test}.xml'
    suite = ET.parse(report).getroot()
    expected = {'tests':'1','failures':'0','errors':'0','skipped':'0'}
    if any(suite.get(key)!=value for key,value in expected.items()):
        raise RuntimeError(f'Expected one executed test with no failures or skips: {test}')


if __name__=='__main__':
    main()
