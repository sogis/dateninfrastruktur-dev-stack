#!/usr/bin/env python3
"""Test ili2pg public views, Sodata and APISIX on an owned Rancher Desktop stack."""
import base64
import hashlib
import json
import os
import re
import time
from uuid import uuid4

from compose_runtime import ComposeContext, init_context, write_private
from ingestion_test_runtime import cleanup, http, reserve_ports, token
from test_management_bootstrap import FIXTURE, operator, put, sql

OPEN = '/downloads/7706c1f8-f0f4-5c8b-8981-2a925be1f730/synthetic.csv'
RESTRICTED = '/downloads/a60f1c63-d07e-484f-aadf-7c4d88c00358/restricted.csv'
DATA = b'zone;value\n1;synthetic\n'
VIEWS = ('datasets', 'issues', 'versions', 'distributions', 'offices',
         'themes', 'keywords', 'contacts', 'schemas', 'attributes')


def public_sql(context, query, *, failure=None):
    process = context.command([
        'exec', '-T', 'postgres', 'sh', '-ec',
        'IFS= read -r PGPASSWORD; export PGPASSWORD; '
        'exec psql -X -q -At -v ON_ERROR_STOP=1 -h 127.0.0.1 -U di_public -d dateninfrastruktur_management',
    ], input=context.values['DI_PUBLIC_PASSWORD'] + '\n' + query, check=False)
    if failure:
        assert process.returncode and failure in process.stderr, context.redact(process.stderr)
    else:
        assert process.returncode == 0, context.redact(process.stderr)
        return process.stdout.strip()


def view_checks(context):
    for name in VIEWS:
        assert public_sql(context, f'SELECT count(*) FROM di_api_public.{name};').isdigit()
    for name in ('principal', 'authorityassignment', 'submission', 'distribution'):
        public_sql(context, f'SELECT * FROM di_management.{name};', failure='permission denied')
    public_sql(context, 'SELECT objectkey FROM di_api_public.distributions;', failure='does not exist')
    public_sql(context, "UPDATE di_api_public.offices SET name='forbidden';", failure='permission denied')
    public_sql(context, 'INSERT INTO di_api_public.offices (id) VALUES (\'forbidden\');',
               failure='permission denied')
    assert public_sql(context, """
        SELECT count(*) || ':' || count(DISTINCT d.id)
        FROM di_api_public.datasets d;
    """) == '2:2'
    assert int(public_sql(context, 'SELECT max(length(owner_office)) FROM di_api_public.datasets;')) > 255
    assert public_sql(context, '''
        SELECT d.identifier || ':' ||
            (SELECT count(*) FROM di_api_public.themes t WHERE t.dataset_id=d.id) || ':' ||
            (SELECT count(*) FROM di_api_public.keywords k WHERE k.dataset_id=d.id) || ':' ||
            (SELECT count(*) FROM di_api_public.contacts c WHERE c.dataset_id=d.id)
        FROM di_api_public.datasets d ORDER BY d.identifier;
    ''').splitlines() == ['test-open:2:2:2', 'test-restricted:0:0:0']
    assert public_sql(context, 'SELECT download_path FROM di_api_public.distributions ORDER BY 1;').splitlines() == [OPEN, RESTRICTED]
    print('PUBLIC_VIEWS_ASSERTIONS=21 SKIP=0', flush=True)


def seed(context):
    digest = hashlib.sha256(DATA).hexdigest()
    sql(context, f"""
        INSERT INTO di_management.contactpoint (t_id, t_basket, t_ili_tid, aname)
        SELECT nextval('di_management.t_ili2db_seq'), t_basket, 'ch.so.test.contact.z', 'Zweiter Kontakt'
        FROM di_management.contactpoint LIMIT 1;
        INSERT INTO di_management.datasetcontact (t_id, t_basket, datasets, contactpoints)
        SELECT nextval('di_management.t_ili2db_seq'), link.t_basket, link.datasets, c.t_id
        FROM di_management.datasetcontact link CROSS JOIN di_management.contactpoint c
        WHERE c.t_ili_tid='ch.so.test.contact.z';
        INSERT INTO di_management.dataversion
            (t_id, t_basket, t_ili_tid, versionkey, asequence, availability, acceptedat,
             objectcount, validationstatus, issue, aschema)
        SELECT nextval('di_management.t_ili2db_seq'), t_basket, 'a60f1c63-d07e-484f-aadf-7c4d88c00359',
             'restricted-first', 1, 'available', now(), 1, 'success', t_id, aschema
        FROM di_management.datasetissue WHERE t_ili_tid='4f7785b6-f07f-5986-9bab-7cc11b8538f9';
        INSERT INTO di_management.distribution
            (t_id, t_basket, t_ili_tid, aformat, filename, mediatype, availability, bytesize, sha256, objectkey, version)
        SELECT nextval('di_management.t_ili2db_seq'), t_basket, 'a60f1c63-d07e-484f-aadf-7c4d88c00358',
             'csv', 'restricted.csv', 'text/csv', 'available', {len(DATA)}, '{digest}', '{RESTRICTED[1:]}', t_id
        FROM di_management.dataversion WHERE versionkey='restricted-first';
        UPDATE di_management.datasetissue SET currentversion=
            (SELECT t_id FROM di_management.dataversion WHERE versionkey='restricted-first')
            WHERE t_ili_tid='4f7785b6-f07f-5986-9bab-7cc11b8538f9';
        UPDATE di_management.distribution SET bytesize={len(DATA)}, sha256='{digest}'
            WHERE t_ili_tid='7706c1f8-f0f4-5c8b-8981-2a925be1f730';
    """)


def bind_identity(context, access_token):
    encoded = access_token.split('.')[1]
    claims = json.loads(base64.urlsafe_b64decode(encoded + '=' * (-len(encoded) % 4)))
    assert claims['iss'] == 'http://localhost:' + context.values['KEYCLOAK_PORT'] + '/realms/dateninfrastruktur'
    assert re.fullmatch(r'[0-9a-f-]{36}', claims['sub'])
    sql(context, f"""
        UPDATE di_management.principal SET aissuer='{claims['iss']}', asubject='{claims['sub']}'
        WHERE t_ili_tid=(SELECT beneficiary.t_ili_tid FROM di_management.accessgrant g
            JOIN di_management.principal beneficiary ON beneficiary.t_id=g.beneficiary
            WHERE g.t_ili_tid='fe217685-7fdb-5153-9811-de500c845d35');
        UPDATE di_management.accessgrant SET validfrom=timezone('UTC', now()) - interval '1 day'
        WHERE t_ili_tid='fe217685-7fdb-5153-9811-de500c845d35';
    """)


def stage_files(context):
    source = put(context, 'catalog-download.csv', DATA)
    for path in (OPEN, RESTRICTED):
        context.command(['--profile', 'setup', 'run', '--rm', '--no-deps', '--entrypoint', 'rclone',
                         'management-setup', '--config', '/runtime/operator.conf', 'copyto',
                         '/runtime/' + source.name, 'storage:ch.so.daten' + path])


def trace_downloads(context):
    path = context.runtime / 'apisix.yaml'
    config = json.loads(path.read_text().split('\n#END', 1)[0])
    route = next(row for row in config['routes'] if row['id'] == 'download')
    route['plugins']['file-logger'] = {
        'path': '/tmp/di-public-downloads.log',
        'log_format': {'probe': '$http_x_di_scenario_probe', 'origin': '$upstream_addr', 'status': '$status'},
    }
    write_private(path, json.dumps(config) + '\n#END\n')
    path.chmod(0o644)


def verify_download_traces(context, expected):
    origin = next(container for container in context.verify_project()
                  if container['Config']['Labels']['com.docker.compose.service'] == 'origin')
    network, = origin['NetworkSettings']['Networks'].values()
    address = network['IPAddress'] + ':8080'
    for _ in range(20):
        result = context.command(['exec', '-T', 'gateway', 'cat', '/tmp/di-public-downloads.log'], check=False)
        rows = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
        found = [row for row in rows if row.get('probe') in expected]
        if len(found) >= len(expected):
            break
        time.sleep(0.5)
    assert len(found) == len(expected)
    assert {row['probe'] for row in found} == expected.keys()
    for row in found:
        status = expected[row['probe']]
        assert int(row['status']) == status
        upstream = row.get('origin')
        if status == 200:
            assert upstream == address
        else:
            assert upstream in (None, '', '-'), 'Denied request reached the file origin'


def gateway_checks(context):
    base = 'http://localhost:' + context.values['GATEWAY_PORT']

    traced = {}

    def request(path, expected, identity=None, method='GET', data=None):
        probe = str(uuid4())
        if path.startswith('/downloads/') and '?' not in path:
            traced[probe] = expected
        status, headers, body = http(base + path, identity, method=method,
                                     headers={'X-DI-Scenario-Probe': probe})
        assert status == expected, (method, path, status, expected)
        if data is not None:
            assert body == data, (method, path)
        elif path.startswith('/downloads/'):
            assert body != DATA
        if path.startswith('/downloads/'):
            assert 'no-store' in next(v for k,v in headers.items() if k.lower() == 'cache-control')

    for identifier, path in [('test-open', OPEN), ('test-restricted', RESTRICTED)]:
        status, _, page = http(base + '/datasets/' + identifier)
        assert status == 200, (identifier, status)
        assert path.encode() in page and b'objectkey' not in page.lower() and b'ch.so.daten/' not in page
    status, _, page = http(base + '/datasets?q=Bootstrap')
    assert status == 200 and b'test-open' in page and b'test-restricted' not in page
    status, _, page = http(base + '/datasets/test-open/structure-quality-origin')
    assert status == 200 and b'zone' in page
    sql(context, "UPDATE di_management.dataset SET title='Katalog live aktualisiert' WHERE identifier='test-open';")
    status, _, page = http(base + '/datasets/test-open')
    assert status == 200 and b'Katalog live aktualisiert' in page
    request(OPEN, 200, data=DATA)
    request(OPEN, 200, method='HEAD', data=b'')
    request(RESTRICTED, 401)
    anna, ben = token(context, 'anna'), token(context, 'ben')
    bind_identity(context, anna)
    request(RESTRICTED, 403, ben)
    request(RESTRICTED, 200, anna, data=DATA)
    sql(context, "UPDATE di_management.accessgrant SET validuntil=timezone('UTC', now());")
    request(RESTRICTED, 403, anna)
    request(OPEN.replace('synthetic.csv', 'unknown.csv'), 404)
    request(OPEN + '?download=true', 400)
    request(OPEN, 405, method='POST')
    request('/internal/authorization/check', 403)
    request('/s3' + OPEN, 403)
    sql(context, "UPDATE di_management.distribution SET objectkey='private/other.csv' WHERE filename='synthetic.csv';")
    assert public_sql(context, "SELECT count(*) FROM di_api_public.distributions WHERE file_name='synthetic.csv';") == '0'
    request(OPEN, 404)
    sql(context, f"UPDATE di_management.distribution SET objectkey='{OPEN[1:]}' WHERE filename='synthetic.csv';")
    sql(context, "UPDATE di_management.datasetissue SET publicationstatus='draft' WHERE t_ili_tid='c5bc014f-39c5-50db-b480-7e782bf09f60';")
    request(OPEN, 404)
    status, _, page = http(base + '/datasets/test-open')
    assert status == 200 and OPEN.encode() not in page
    sql(context, "UPDATE di_management.datasetissue SET publicationstatus='published' WHERE t_ili_tid='c5bc014f-39c5-50db-b480-7e782bf09f60';")
    sql(context, "UPDATE di_management.dataversion SET availability='withdrawn' WHERE versionkey='one';")
    request(OPEN, 404)
    status, _, page = http(base + '/datasets/test-open')
    assert status == 200 and OPEN.encode() not in page
    sql(context, "UPDATE di_management.dataversion SET availability='available' WHERE versionkey='one';")
    context.command(['stop', 'admin'])
    request(OPEN, 503)
    verify_download_traces(context, traced)
    sql(context, """
        ALTER ROLE di_public NOLOGIN;
        SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename='di_public';
    """)
    try:
        status, _, _ = http(base + '/datasets/test-open')
        assert status == 503
    finally:
        sql(context, 'ALTER ROLE di_public LOGIN;')
    print('PUBLIC_GATEWAY_CASES=25 SKIP=0', flush=True)


def main():
    if not __debug__:
        raise RuntimeError('Assertions must be enabled')
    os.environ.setdefault('DOCKER_CONTEXT', 'rancher-desktop')
    context = init_context('mag-s1e-public-' + uuid4().hex[:12], reserve_ports(), True)
    print(f'Owned Compose fixture: {context.project}', flush=True)
    try:
        context.command(['build', 'postgres', 'management-tool-build', 'admin', 'sodata'])
        context.command(['up', '--no-build', '-d', '--wait', '--wait-timeout', '240', 'postgres', 'garage'])
        for service in ('postgres-init', 'management-setup', 'garage-setup'):
            context.command(['--profile', 'setup', 'run', '--rm', '--no-deps', service])
        context = ComposeContext(context.env_file)
        source = put(context, 'management-bootstrap.xtf', FIXTURE.read_bytes())
        operator(context, 'import', source)
        seed(context)
        view_checks(context)
        stage_files(context)
        trace_downloads(context)
        context.command(['up', '--no-build', '--no-deps', '-d', '--wait', '--wait-timeout', '300',
                         'keycloak', 'admin', 'sodata', 'origin', 'gateway'])
        gateway_checks(context)
    finally:
        cleanup(context)
    assert not context.command(['ps', '-aq']).stdout.strip()
    print('ASSERTIONS=46 SKIP=0')


if __name__ == '__main__':
    main()
