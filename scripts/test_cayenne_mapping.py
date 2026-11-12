#!/usr/bin/env python3
"""Regenerate the Cayenne map and qualify TID/basket writes in an owned Compose fixture."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
from uuid import uuid4

from compose_runtime import ROOT, init_context
from ingestion_test_runtime import cleanup, reserve_ports
from test_management_bootstrap import FIXTURE, database_ids, operator, put, transfer_ids

ADMIN = ROOT.parent / 'dateninfrastruktur-admin'
MAP = Path('src/main/resources/cayenne/management.map.xml')
MODEL = Path('src/main/java/ch/so/agi/dateninfrastruktur/admin/model')
PROBE = 'ch.so.agi.dateninfrastruktur.admin.CayenneMappingProbe'
NEW_IDS = {
    'ch.so.test.cayenne.' + 'long-office-identity-' * 14: 'Office',
    '31a3ed65-194e-42a6-994f-4d137ea113a1': 'Principal',
    '43d011ed-0615-4678-ad95-a2bb3ceec8ca': 'Dataset',
    'e76580b3-7f50-4e7f-b582-28499da3df45': 'DatasetIssue',
    '959788e9-0d55-4036-ab1f-830ddde77be8': 'Submission',
}


def regenerate(context):
    project = context.runtime / 'generation'
    project.mkdir(mode=0o700)
    for name in ('build.gradle', 'settings.gradle', 'gradlew'):
        shutil.copy2(ADMIN / name, project / name)
    shutil.copytree(ADMIN / 'gradle', project / 'gradle')
    (project / 'scripts').mkdir()
    shutil.copy2(ADMIN / 'scripts/normalize_cayenne_uuid.py', project / 'scripts')
    (project / MAP.parent).mkdir(parents=True)
    (project / MODEL).mkdir(parents=True)
    command = """
        cd /runtime/generation
        export DI_MAPPING_URL=jdbc:postgresql://postgres:5432/dateninfrastruktur_management
        export DI_MAPPING_USER=di_writer DI_MAPPING_PASSWORD="$DI_WRITER_PASSWORD"
        ./gradlew --no-daemon --console=plain cdbimport cgen
    """
    result = context.command(['--profile', 'setup', 'run', '--rm', '--no-deps',
                              '--entrypoint', 'sh', 'management-setup', '-ec', command])
    output = context.redact(result.stdout + result.stderr)
    assert '> Task :cdbimport' in output and '> Task :cgen' in output
    assert (project / MAP).read_bytes() == (ADMIN / MAP).read_bytes(), 'cdbimport differs from committed map'
    expected = {p.name: p.read_bytes() for p in (ADMIN / MODEL / 'auto').glob('*.java')}
    generated = {p.name: p.read_bytes() for p in (project / MODEL / 'auto').glob('*.java')}
    assert expected == generated and expected, 'cgen differs from committed classes'
    assert {p.name for p in (project / MODEL).glob('*.java')} == {
        p.name for p in (ADMIN / MODEL).glob('*.java')
    }
    print(f'cdbimport and cgen reproduced the map and {len(expected)} generated classes')


def probe(context, scenario):
    result = context.command(['--profile', 'test', 'run', '--rm', '--no-deps',
                              '--entrypoint', 'java', 'test-fixture', '-cp',
                              '/opt/compose-test/classes:/opt/compose-test/lib/*', PROBE, scenario])
    output = context.redact(result.stdout)
    expected = 'CAYENNE_MISSING_BASKET=PASS' if scenario == 'missing-basket' else 'CAYENNE_INSERTS=PASS'
    assert expected in output.splitlines()
    assert 'CAYENNE_WRITER_BOUNDARY=PASS' in output.splitlines()
    print(expected)
    print('CAYENNE_WRITER_BOUNDARY=PASS')


def exercise(context):
    context.command(['--profile', 'build-tools', 'build', 'postgres', 'management-tool-build', 'test-tool-build'])
    context.command(['up', '--no-build', '-d', '--wait', '--wait-timeout', '150', 'postgres'])
    for service in ('postgres-init', 'management-setup'):
        context.command(['--profile', 'setup', 'run', '--rm', '--no-deps', service])
    regenerate(context)
    probe(context, 'missing-basket')
    source = put(context, 'management-bootstrap.xtf', FIXTURE.read_bytes())
    baskets, imported = transfer_ids(source)
    operator(context, 'import', source)
    probe(context, 'insert')
    exported = context.runtime / 'cayenne-export.xtf'
    operator(context, 'export', exported)
    actual_baskets, actual = transfer_ids(exported)
    assert actual_baskets == baskets
    assert set(actual) == set(imported) | set(NEW_IDS)
    assert all(actual[tid] == identity for tid, identity in imported.items())
    assert all(actual[tid][1].endswith('}' + kind) for tid, kind in NEW_IDS.items())
    assert database_ids(context, actual) == actual
    context.command(['--profile', 'setup', 'run', '--rm', '--no-deps', '--entrypoint', 'java',
                     'management-setup', '-jar', '/opt/admin/.runtime/tools/ilivalidator/ilivalidator-1.15.0.jar',
                     '--modeldir', '/opt/admin/models', '/runtime/cayenne-export.xtf'])
    print('Pinned ilivalidator accepted the export with all five new object TIDs')


def main():
    if not __debug__:
        raise RuntimeError('Assertions must be enabled')
    os.environ['DOCKER_CONTEXT'] = 'rancher-desktop'
    context = init_context('mag-s1c-mapping-' + uuid4().hex[:12], reserve_ports(), True)
    print(f'Owned Compose fixture: {context.project}', flush=True)
    try:
        exercise(context)
    finally:
        cleanup(context)
    assert not context.command(['ps', '-aq']).stdout.strip()
    assert not subprocess.check_output(['docker', 'volume', 'ls', '-q', '--filter',
        'label=com.docker.compose.project=' + context.project], text=True).strip()
    print('ASSERTIONS=16 SKIP=0')


if __name__ == '__main__':
    main()
