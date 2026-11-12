#!/usr/bin/env python3
"""Qualify the explicit management setup with real ili2pg and PostgreSQL."""
import os
import re
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
from xml.etree import ElementTree as ET

from compose_runtime import ROOT, init_context
from ingestion_test_runtime import cleanup, reserve_ports

ADMIN = ROOT.parent / 'dateninfrastruktur-admin'
MANAGEMENT = 'dateninfrastruktur_management'
TRANSFER = '{http://www.interlis.ch/xtf/2.4/INTERLIS}'
FIXTURE = ADMIN / 'tests/fixtures/management-bootstrap.xtf'


def transfer_ids(path):
    document = ET.parse(path)
    baskets = {}
    objects = {}
    for basket in document.getroot().find(TRANSFER + 'datasection'):
        bid = basket.attrib[TRANSFER + 'bid']
        assert bid not in baskets
        baskets[bid] = basket.tag
        for child in basket:
            tid = child.get(TRANSFER + 'tid')
            if tid is not None:
                assert tid not in objects
                objects[tid] = (bid, child.tag)
    return baskets, objects


def sql(context, query, *, failure=None):
    result = context.command(['exec', '-T', 'postgres', 'psql', '-X', '-q', '-At',
                              '-v', 'ON_ERROR_STOP=1', '-U', 'postgres', '-d', MANAGEMENT],
                             input=query, check=False)
    if failure:
        assert result.returncode and failure in result.stderr, context.redact(result.stderr)
        return
    assert result.returncode == 0, context.redact(result.stderr)
    return result.stdout.strip()


def tool(context, *args):
    return context.command(['--profile', 'setup', 'run', '--rm', '--no-deps',
                            'management-setup', *args]).stdout.strip()


def operator(context, action, path, *, failure=None):
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/compose_operator.py'),
                             action, str(path), '--env', str(context.env_file)],
                            text=True, capture_output=True)
    output = context.redact(result.stdout + result.stderr)
    if failure:
        assert result.returncode and failure in output, output
        print(f'{path.name}: refused ({failure})')
    else:
        assert result.returncode == 0, output
        print(output.strip())


def put(context, name, source):
    path = context.runtime / name
    with path.open('xb') as target:
        path.chmod(0o600)
        target.write(source)
    return path


def snapshot(context):
    tables = sql(context, """
        SELECT tablename FROM pg_tables WHERE schemaname='di_management' ORDER BY tablename;
    """).splitlines()
    assert tables and all(re.fullmatch(r'[a-z_0-9]+', table) for table in tables)
    data = [
        sql(context, f'SELECT jsonb_agg(to_jsonb(x) ORDER BY to_jsonb(x)) '
                     f'FROM di_management.{table} x;')
        for table in tables
    ]
    views = sql(context, """
        SELECT jsonb_object_agg(viewname, definition) FROM pg_views WHERE schemaname='di_api_public';
    """)
    return tables, data, views


def database_ids(context, expected):
    rows = sql(context, 'SELECT iliname, sqlname FROM di_management.t_ili2db_classname;')
    tables = dict(row.split('|') for row in rows.splitlines())
    result = {}
    for tag in sorted({tag for _, tag in expected.values()}):
        namespace, name = tag.removeprefix('{').split('}')
        model = namespace.rsplit('/', 1)[-1]
        topic = model.split('_')[-2]
        table = tables[f'{model}.{topic}.{name}']
        assert re.fullmatch(r'[a-z_0-9]+', table)
        rows = sql(context, f"""
            SELECT x.t_ili_tid::text, b.t_ili_tid
            FROM di_management.{table} x JOIN di_management.t_ili2db_basket b ON b.t_id=x.t_basket;
        """)
        for row in rows.splitlines():
            tid, bid = row.split('|')
            assert tid not in result
            result[tid] = (bid, tag)
    return result


def exercise(context):
    context.command(['--profile', 'build-tools', 'build', 'postgres', 'management-tool-build'])
    context.command(['up', '--no-build', '-d', '--wait', '--wait-timeout', '150', 'postgres'])
    context.command(['--profile', 'setup', 'run', '--rm', '--no-deps', 'postgres-init'])

    sql(context, 'CREATE SCHEMA incompatible;')
    result = context.command(['--profile', 'setup', 'run', '--rm', '--no-deps',
                              'management-setup'], check=False)
    assert result.returncode and 'Unknown, incomplete or legacy' in result.stderr
    assert sql(context, "SELECT to_regnamespace('di_management') IS NULL;") == 't'
    sql(context, 'DROP SCHEMA incompatible;')
    print(tool(context, 'setup'))
    assert sql(context, """
        SELECT string_agg(nspname, ',' ORDER BY nspname) FROM pg_namespace
        WHERE nspname NOT LIKE 'pg_%' AND nspname NOT IN ('public','information_schema');
    """) == 'di_api_public,di_management'
    assert sql(context, """
        SELECT count(*) FROM information_schema.views WHERE table_schema='di_api_public';
    """) == '10'
    assert sql(context, """
        SELECT data_type||':'||character_maximum_length FROM information_schema.columns
        WHERE table_schema='di_management' AND table_name='office' AND column_name='t_ili_tid';
    """) == 'character varying:1024'
    assert sql(context, """
        SELECT data_type FROM information_schema.columns WHERE table_schema='di_management'
        AND table_name='principal' AND column_name='t_ili_tid';
    """) == 'uuid'
    source = put(context, 'management-bootstrap.xtf', FIXTURE.read_bytes())
    document = ET.parse(source)
    baskets, objects = transfer_ids(source)
    assert len(baskets) == 4 and max(map(len, objects)) > 255
    datasection = document.getroot().find(TRANSFER + 'datasection')
    reference = next(node for node in datasection.iter()
                     if node.get(TRANSFER + 'ref') and node.get(TRANSFER + 'bid'))
    ref = reference.get(TRANSFER + 'ref')
    reference.set(TRANSFER + 'bid', next(bid for bid in baskets if bid != objects[ref][0]))
    wrong = put(context, 'wrong-bid.xtf', ET.tostring(document.getroot(), encoding='utf-8'))
    operator(context, 'import', wrong, failure='Reference BID does not match')
    assert sql(context, 'SELECT count(*) FROM di_management.t_ili2db_basket;') == '0'
    missing = ET.parse(source)
    first_object = next(node for node in missing.getroot().iter() if node.get(TRANSFER + 'tid'))
    del first_object.attrib[TRANSFER + 'tid']
    path = put(context, 'missing-tid.xtf', ET.tostring(missing.getroot(), encoding='utf-8'))
    operator(context, 'import', path, failure='Missing, empty or duplicate object TID')
    assert sql(context, 'SELECT count(*) FROM di_management.t_ili2db_basket;') == '0'
    operator(context, 'import', source)
    assert database_ids(context, objects) == objects
    assert set(sql(context, 'SELECT t_ili_tid FROM di_management.t_ili2db_basket;').splitlines()) == set(baskets)
    assert sql(context, """
        SELECT count(*) FROM di_management.dataset d JOIN di_management.office o ON o.t_id=d.owneroffice
        WHERE length(o.t_ili_tid)>255;
    """) == '1'
    assert sql(context, 'SET ROLE di_public; SELECT count(*) FROM di_api_public.datasets;') == '2'
    sql(context, 'SET ROLE di_public; SELECT * FROM di_management.principal;', failure='permission denied')
    assert sql(context, "SELECT has_table_privilege('di_public', 'di_api_public.datasets', 'DELETE');") == 'f'
    sql(context, 'SET ROLE di_public; DELETE FROM di_api_public.datasets;', failure='cannot delete from view')
    sql(context, 'UPDATE di_management.office SET t_ili_tid=NULL;', failure='not-null constraint')
    sql(context, "UPDATE di_management.office SET t_ili_tid='same';", failure='duplicate key')
    initial = snapshot(context)
    print(tool(context, 'setup'))
    assert snapshot(context) == initial
    operator(context, 'import', source, failure='Bootstrap requires empty management baskets')
    assert snapshot(context) == initial
    target = context.runtime / 'management-export.xtf'
    operator(context, 'export', target)
    assert transfer_ids(target) == (baskets, objects), 'Export changed basket or object identities'
    assert target.stat().st_mode & 0o777 == 0o600
    context.command(['--profile', 'setup', 'run', '--rm', '--no-deps', '--entrypoint', 'java',
                     'management-setup', '-jar', '/opt/admin/.runtime/tools/ilivalidator/ilivalidator-1.15.0.jar',
                     '--modeldir', '/opt/admin/models', '/runtime/management-export.xtf'])
    assert snapshot(context) == initial
    print('PostgreSQL and export preserved synthetic BIDs and TIDs')


def main():
    if not __debug__:
        raise RuntimeError('Assertions must be enabled')
    os.environ.setdefault('DOCKER_CONTEXT', 'rancher-desktop')
    context = init_context('mag-s1b-roundtrip-' + uuid4().hex[:12], reserve_ports(), True)
    print(f'Owned Compose fixture: {context.project}', flush=True)
    try:
        exercise(context)
    finally:
        cleanup(context)
    assert not context.command(['ps', '-aq']).stdout.strip()
    assert not subprocess.check_output(['docker', 'volume', 'ls', '-q', '--filter',
        'label=com.docker.compose.project=' + context.project], text=True).strip()
    print('ASSERTIONS=26 SKIP=0')


if __name__ == '__main__':
    main()
