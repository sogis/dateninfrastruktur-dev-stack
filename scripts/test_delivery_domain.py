#!/usr/bin/env python3
"""Exercise the delivery domain against the new management schema on Rancher Desktop."""
import os
from uuid import uuid4

from compose_runtime import init_context
from ingestion_test_runtime import cleanup, reserve_ports
from test_management_bootstrap import FIXTURE, operator, put


def main():
    if not __debug__:
        raise RuntimeError('Assertions must be enabled')
    os.environ['DOCKER_CONTEXT'] = 'rancher-desktop'
    context = init_context('mag-s1d-delivery-' + uuid4().hex[:12], reserve_ports(), True)
    print(f'Owned Compose fixture: {context.project}', flush=True)
    try:
        context.command(['--profile', 'build-tools', 'build', 'postgres', 'management-tool-build', 'test-tool-build'])
        context.command(['up', '--no-build', '-d', '--wait', '--wait-timeout', '150', 'postgres'])
        for service in ('postgres-init', 'management-setup'):
            context.command(['--profile', 'setup', 'run', '--rm', '--no-deps', service])
        source = put(context, 'management-bootstrap.xtf', FIXTURE.read_bytes())
        operator(context, 'import', source)
        result = context.command(['--profile', 'test', 'run', '--rm', '--no-deps',
            '--entrypoint', 'java', 'test-fixture', '-cp', '/opt/compose-test/classes:/opt/compose-test/lib/*',
            'ch.so.agi.dateninfrastruktur.admin.DeliveryDomainProbe'], check=False)
        output = context.redact(result.stdout + result.stderr)
        print(output)
        assert result.returncode == 0, 'Domain probe failed'
        assert 'DELIVERY_DOMAIN_ASSERTIONS=38 SKIP=0' in output.splitlines()
        assert 'DELIVERY_HTTP_ASSERTIONS=15 SKIP=0' in output.splitlines()
        assert 'ACCESS_CATALOG_CASES=5 SKIP=0' in output.splitlines()
        context.command(['--profile', 'setup', 'run', '--rm', '--no-deps', '--entrypoint', 'java',
            'management-setup', '-jar', '/opt/admin/.runtime/tools/ili2c/ili2c.jar',
            '--no-auto', '/runtime/DI_ExampleCsv.ili'])
        operator(context, 'export', context.runtime / 'delivery-export.xtf')
        context.command(['--profile', 'setup', 'run', '--rm', '--no-deps', '--entrypoint', 'java',
            'management-setup', '-jar', '/opt/admin/.runtime/tools/ilivalidator/ilivalidator-1.15.0.jar',
            '--modeldir', '/opt/admin/models', '/runtime/delivery-export.xtf'])
    finally:
        cleanup(context)
    assert not context.command(['ps', '-aq']).stdout.strip()
    print('ASSERTIONS=62 SKIP=0')


if __name__ == '__main__':
    main()
