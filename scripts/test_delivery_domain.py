#!/usr/bin/env python3
"""Exercise the delivery domain against the new management schema on Rancher Desktop."""
import base64
import hashlib
import json
import os
import urllib.parse
from uuid import UUID, uuid4

from compose_runtime import ComposeContext, init_context
from ingestion_test_runtime import cleanup, http, reserve_ports, sql, token
from test_management_bootstrap import FIXTURE, operator, put


def verify_garage_delivery(context):
    issuer = 'http://localhost:' + context.values['KEYCLOAK_PORT'] + '/realms/dateninfrastruktur'
    form = urllib.parse.urlencode({
        'grant_type': 'client_credentials', 'client_id': 'gretl-delivery',
        'client_secret': context.values['DI_GRETL_DELIVERY_CLIENT_SECRET'],
    }).encode()
    status, _, payload = http(issuer + '/protocol/openid-connect/token', method='POST', data=form)
    assert status == 200
    service_token = json.loads(payload)['access_token']
    user_token = token(context, 'anna')
    for name, jwt in [('anna', user_token), ('gretl', service_token)]:
        segment = jwt.split('.')[1]
        claims = json.loads(base64.urlsafe_b64decode(segment + '=' * (-len(segment) % 4)))
        assert claims['iss'] == issuer and 'management-api' in claims['aud']
        subject = str(UUID(claims['sub']))
        sql(context, f"UPDATE di_management.principal SET aissuer='{issuer}', asubject='{subject}' WHERE asubject='{name}'")

    def call(method, path, jwt, expected, payload=None, origin=False):
        port = 'http://origin:8080' if origin else 'http://admin:8080/internal/deliveries'
        args = ['--profile', 'setup', 'run', '--rm', '-T', '--no-deps',
                '--entrypoint', 'python3', 'management-setup', '-c', """
import json, sys, urllib.request, urllib.error
v = json.load(sys.stdin)
headers = {'Authorization': 'Bearer ' + v['jwt']} if v['jwt'] else {}
data = None
if v['payload'] is not None:
    headers['Content-Type'] = 'application/json'
    data = json.dumps(v['payload']).encode()
request = urllib.request.Request(v['url'], data=data, headers=headers, method=v['method'])
try:
    with urllib.request.urlopen(request, timeout=20) as response:
        print(json.dumps([response.status, response.read().decode()]))
except urllib.error.HTTPError as error:
    print(json.dumps([error.code, error.read().decode()]))
"""]
        request = dict(method=method, url=port + path, jwt=jwt, payload=payload)
        result = context.command(args, input=json.dumps(request))
        status, body = json.loads(result.stdout)
        assert status == expected, (method, path, status, expected)
        return body if origin else json.loads(body)

    target = call('GET', '/eligible', user_token, 200)[0]
    data = b'zone,code\nA,1\n'
    sha = hashlib.sha256(data).hexdigest()

    def start(mode='replace'):
        submission = '/' + str(uuid4())
        call('PUT', submission, user_token, 200, dict(
            datasetId=target['datasetId'], issueId=target['issueId'], mode=mode,
            originalFileName='source.csv', inputSize=len(data), inputSha256=sha))
        call('POST', submission + '/start', user_token, 403)
        state = call('POST', submission + '/start', service_token, 200)
        assert state['inputSize'] == len(data) and state['inputSha256'] == sha
        assert [column['name'] for column in state['columns']] == ['zone', 'code']
        return submission, state

    def stage(state, contents):
        key = state['candidatePrefix'] + 'snapshot.csv'
        source = put(context, 's3-a-candidate-' + str(uuid4()) + '.csv', contents)
        context.command(['--profile', 'setup', 'run', '--rm', '--no-deps', '--entrypoint', 'rclone',
                         'management-setup', '--config', '/runtime/operator.conf', 'copyto',
                         '/runtime/' + source.name, 'storage:ch.so.daten/' + key])
        assert call('GET', '/' + key, None, 200, origin=True).encode() == contents

    def complete(submission, state, expected):
        return call('POST', submission + '/complete', service_token, expected, dict(
            schemaId=state['schemaId'], baseVersionId=state['baseVersionId'],
            fileName='snapshot.csv', byteSize=len(data), sha256=sha, objectCount=1))

    submission, state = start()
    stage(state, data)
    assert complete(submission, state, 200)['status'] == 'accepted'
    first_key = state['candidatePrefix'] + 'snapshot.csv'
    append, append_state = start('append')
    assert append_state['baseCsvKey'] == first_key
    call('POST', append + '/fail', service_token, 200, {'message': 'Append metadata fixture'})
    submission, state = start()
    stage(state, data.replace(b'A,1', b'B,1'))
    complete(submission, state, 409)
    assert call('GET', submission, user_token, 200)['status'] == 'processing'
    context.command(['stop', 'origin'])
    complete(submission, state, 503)
    assert call('GET', submission, user_token, 200)['status'] == 'processing'
    context.command(['up', '--no-build', '-d', '--wait', 'origin'])
    submission, state = start()
    stage(state, data)
    assert complete(submission, state, 200)['status'] == 'accepted'


def main():
    if not __debug__:
        raise RuntimeError('Assertions must be enabled')
    os.environ.setdefault('DOCKER_CONTEXT', 'rancher-desktop')
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
        context.command(['build', 'admin'])
        context.command(['up', '--no-build', '-d', '--wait', '--wait-timeout', '240', 'garage'])
        context.command(['--profile', 'setup', 'run', '--rm', '--no-deps', 'garage-setup'])
        context = ComposeContext(context.env_file)
        context.command(['up', '--no-build', '-d', '--wait', '--wait-timeout', '300',
                         'keycloak', 'origin', 'admin'])
        verify_garage_delivery(context)

    finally:
        cleanup(context)
    assert not context.command(['ps', '-aq']).stdout.strip()
    print('ASSERTIONS=82 SKIP=0')


if __name__ == '__main__':
    main()
