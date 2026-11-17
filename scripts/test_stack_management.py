#!/usr/bin/env python3
"""Qualify the normal Compose runtime and management UI in a synthetic fixture."""
import argparse
import os
import json
import re
import subprocess
from uuid import uuid4
from xml.etree import ElementTree

from compose_operations import build, select_images, setup, start
from compose_runtime import ROOT, init_context, write_private
from ingestion_test_runtime import cleanup, http, reserve_ports, sql, token
from test_management_bootstrap import FIXTURE, operator, put


def integration(context, repo, task, *filters):
    env = {**os.environ,
           'DI_TEST_GATEWAY': 'http://localhost:' + context.values['GATEWAY_PORT'],
           'DI_TEST_DEMO_PASSWORD': context.values['KEYCLOAK_DEMO_PASSWORD']}
    source = ROOT.parent / ('dateninfrastruktur-' + repo)
    command = ['./gradlew', '--no-daemon', task, '--console=plain']
    for name in filters:
        command.extend(['--tests', '*.' + name])
    result = subprocess.run(command, cwd=source, env=env, capture_output=True, text=True)
    path = context.runtime / (repo + '-integration.log')
    write_private(path, context.redact(result.stdout + result.stderr))
    if result.returncode:
        raise RuntimeError(f'{repo} integration failed. Redacted evidence: {path}')
    reports = [ElementTree.parse(path).getroot()
               for path in (source / 'build' / 'test-results' / task).glob('TEST-*.xml')]
    assert {report.attrib['name'].rsplit('.', 1)[-1] for report in reports} == set(filters)
    assert all(report.get(key) == '0' for report in reports for key in ('skipped', 'failures', 'errors'))
    return sum(int(report.attrib['tests']) for report in reports)


def run_smoke(context):
    rows = [json.loads(line) for line in
            context.command(['ps', '--format', 'json']).stdout.splitlines()]
    expected = set('postgres keycloak garage origin gateway sodata admin jenkins clickhouse superset'.split())
    assert len(rows) == len(expected) and {row['Service'] for row in rows} == expected
    assert all(row['State'] == 'running' and row['Health'] == 'healthy' for row in rows)
    databases = sql(context, "SELECT datname FROM pg_database WHERE NOT datistemplate AND datname<>'postgres';")
    assert set(databases.splitlines()) == {'keycloak', 'superset', 'dateninfrastruktur_management'}
    context.command(['--profile', 'setup', 'run', '--rm', '--no-deps', 'management-setup', 'verify'])
    for port, path in [('GATEWAY_PORT', '/'), ('GATEWAY_PORT', '/jenkins/login'),
                       ('KEYCLOAK_PORT', '/realms/dateninfrastruktur/.well-known/openid-configuration'),
                       ('SUPERSET_PORT', '/health')]:
        assert http('http://localhost:' + context.values[port] + path)[0] == 200, path


def http_security_integration(context):
    test_class = 'ch.so.agi.dateninfrastruktur.admin.ManagementHttpSecurityIT'
    result = context.command([
        '--profile', 'test', 'run', '--rm', '--no-deps', 'test-fixture',
        'org.junit.platform.console.ConsoleLauncher', 'execute',
        '--select-class', test_class, '--fail-if-no-tests',
        '--reports-dir', '/runtime/http-security',
    ], check=False)
    path = context.runtime / 'http-security.log'
    write_private(path, context.redact(result.stdout + result.stderr))
    if result.returncode:
        raise RuntimeError(f'Management HTTP security integration failed. Redacted evidence: {path}')
    report = ElementTree.parse(context.runtime / 'http-security' / 'TEST-junit-jupiter.xml').getroot()
    cases = report.findall('testcase')
    assert cases and {case.attrib['classname'] for case in cases} == {test_class}
    assert all(report.get(key) == '0' for key in ('skipped', 'failures', 'errors'))
    print(f'MANAGEMENT_HTTP_SECURITY={len(cases)} SKIP=0', flush=True)
    return len(cases)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release-staging-tag')
    args = parser.parse_args()
    if not __debug__:
        raise RuntimeError('Assertions must be enabled')
    context = init_context('mag-s1f-stack-' + uuid4().hex[:12], reserve_ports(), True)
    print(f'Owned Compose fixture: {context.project}', flush=True)
    try:
        select_images(context, 'local')
        build(context)
        setup(context)
        assert sql(context, 'SELECT count(*) FROM di_management.dataset;') == '0'
        assert sql(context, 'SELECT count(*) FROM di_management.t_ili2db_basket;') == '0'
        start(context, 'local')
        run_smoke(context)
        assert sql(context, 'SELECT count(*) FROM di_management.dataset;') == '0'
        assert sql(context, 'SELECT count(*) FROM di_management.t_ili2db_basket;') == '0'
        base = 'http://localhost:' + context.values['GATEWAY_PORT']
        assert http(base + '/jenkins/data-delivery/')[0] == 403

        source = put(context, 'management-bootstrap.xtf', FIXTURE.read_bytes())
        operator(context, 'import', source)

        issuer = 'http://localhost:' + context.values['KEYCLOAK_PORT'] + '/realms/dateninfrastruktur'
        assert re.fullmatch(r'http://localhost:[0-9]+/realms/dateninfrastruktur', issuer)
        assert token(context, 'anna')
        sql(context, f"""
            UPDATE di_management.principal SET aissuer='{issuer}',
                asubject='0b7c9d5e-1f2a-4d3b-8c4e-5f6a7b8c9d01' WHERE asubject='anna';
            UPDATE di_management.authorityassignment SET validfrom=timezone('UTC',now()) - interval '1 day';
            UPDATE di_management.authorityassignment SET dataset=NULL,
                office=(SELECT owneroffice FROM di_management.dataset WHERE identifier='test-open')
            WHERE capability IN ('publish','manage_submitters');
        """)
        admin = http_security_integration(context)
        admin += integration(context, 'admin', 'integrationTest', 'StackManagementIT', 'ManagementBrowserIT')
        portal = integration(context, 'sodata', 'managementDatabaseTest', 'StackCatalogIT')
        assert admin >= 4 and portal >= 1
        assert sql(context, """
            SELECT concat_ws(':', d.publicationstatus, i.publicationstatus, count(DISTINCT a.t_id),
                count(DISTINCT u.t_id), count(DISTINCT f.t_id), count(DISTINCT c.t_id))
            FROM di_management.dataset d
            JOIN di_management.datasetissue i ON i.dataset=d.t_id AND i.issuekey='default'
            JOIN di_management.attributedefinition a ON a.aschema=i.aschema
            JOIN di_management.uniquedefinition u ON u.aschema=i.aschema
            JOIN di_management.uniquefield f ON f.uniquedefinition=u.t_id
            JOIN di_management.datasetcontact c ON c.datasets=d.t_id
            WHERE d.identifier='s1f-browser'
            GROUP BY d.publicationstatus, i.publicationstatus;
        """) == 'published:published:2:1:2:1'
        transfer = context.runtime / 'browser-export.xtf'
        operator(context, 'export', transfer)
        context.command(['--profile', 'setup', 'run', '--rm', '--no-deps', '--entrypoint', 'java',
            'management-setup', '-jar', '/opt/admin/.runtime/tools/ilivalidator/ilivalidator-1.15.1.jar',
            '--modeldir', '/opt/admin/models', '/runtime/browser-export.xtf'])
        # Keep the imported catalogue chain and the dataset published through
        # the browser, including the physical database and row identities.
        retained = '''
            SELECT db.oid, d.t_id, d.t_ili_tid, d.identifier, d.publicationstatus,
                   i.t_id, i.t_ili_tid, i.publicationstatus, v.t_id, v.t_ili_tid, v.asequence
            FROM pg_database db CROSS JOIN di_management.dataset d
            JOIN di_management.datasetissue i ON i.t_id=d.currentissue
            LEFT JOIN di_management.dataversion v ON v.t_id=i.currentversion
            WHERE db.datname=current_database() AND d.identifier IN ('test-open', 's1f-browser')
            ORDER BY d.identifier;
        '''
        before_restart = sql(context, retained)
        assert len(before_restart.splitlines()) == 2
        start(context, 'local', restart=True)
        run_smoke(context)
        assert sql(context, retained) == before_restart
        if args.release_staging_tag:
            for name in ('admin', 'jenkins', 'postgres', 'superset', 'tools'):
                key = ('TOOL' if name == 'tools' else name.upper()) + '_IMAGE'
                subprocess.run(['docker', 'tag', context.command_overrides[key],
                                f'dateninfrastruktur-{name}:{args.release_staging_tag}'], check=True)
        print(f'ADMIN_INTEGRATION={admin} SODATA_INTEGRATION={portal} SKIP=0', flush=True)
    finally:
        cleanup(context)
    assert not context.command(['ps', '-aq']).stdout.strip()
    print(f'ASSERTIONS={admin + portal + 13} SKIP=0')


if __name__ == '__main__':
    main()
