#!/usr/bin/env python3
"""Exercise the delivery domain against the new management schema on Rancher Desktop."""
import argparse
import base64
import csv
from http.cookiejar import CookieJar, DefaultCookiePolicy
from html.parser import HTMLParser
import hashlib
import json
import os
import re
import time
import urllib.parse
import urllib.request
from uuid import UUID, uuid4

from bind_jenkins_image import verified_image_id
from compose_runtime import ComposeContext, init_context
from ingestion_test_runtime import cleanup, http, reserve_ports, sql, token
from test_management_bootstrap import FIXTURE, operator, put


def delivery_identities(context):
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

    return user_token, service_token


def verify_garage_delivery(context, user_token, service_token):
    def call(method, path, jwt, expected, payload=None, origin=False, text=False):
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
        return body if origin or text else json.loads(body)

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
        assert 'schemaModel' not in state
        model = call('GET', submission + '/model.ili', service_token, 200, text=True)
        assert 'MODEL ' + state['schemaModelName'] in model
        assert [column['name'] for column in state['columns']] == ['zone', 'code']
        return submission, state

    def stage(state, contents):
        key = state['candidatePrefix'] + 'snapshot.csv'
        source = put(context, 's3-a-candidate-' + str(uuid4()) + '.csv', contents)
        context.command(['--profile', 'setup', 'run', '--rm', '--no-deps', '--entrypoint', 'rclone',
                         'management-setup', '--config', '/runtime/operator.conf', 'copyto',
                         '/runtime/' + source.name, 'storage:ch.so.daten/' + key])
        assert call('GET', '/' + key, None, 200, origin=True).encode() == contents

    def complete(submission, expected):
        return call('POST', submission + '/complete', service_token, expected, {'objectCount': 1})

    submission, state = start()
    stage(state, data)
    assert complete(submission, 200)['status'] == 'accepted'
    first_key = state['candidatePrefix'] + 'snapshot.csv'
    append, append_state = start('append')
    assert append_state['baseCsvKey'] == first_key
    call('POST', append + '/fail', service_token, 200, {'message': 'Append metadata fixture'})
    submission, state = start()
    stage(state, b'')
    complete(submission, 409)
    assert call('GET', submission, user_token, 200)['status'] == 'processing'
    context.command(['stop', 'origin'])
    complete(submission, 503)
    assert call('GET', submission, user_token, 200)['status'] == 'processing'
    context.command(['up', '--no-build', '-d', '--wait', 'origin'])
    submission, state = start()
    stage(state, data)
    assert complete(submission, 200)['status'] == 'accepted'


class Forms(HTMLParser):
    def __init__(self, document):
        super().__init__()
        self.forms = []
        self.feed(document)

    def handle_starttag(self, tag, attributes):
        if tag == 'form':
            self.forms.append(dict(attributes))


def verify_jenkins_delivery(context):
    base = 'http://localhost:' + context.values['GATEWAY_PORT']
    # Browsers send Secure cookies on localhost, including the HTTP test realm.
    cookies = CookieJar(policy=DefaultCookiePolicy(secure_protocols=('https', 'wss', 'http')))
    browser = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    try:
        with browser.open(base + '/anlieferung', timeout=30) as response:
            page = response.read().decode()
            page_url = response.url
    except urllib.error.HTTPError as error:
        assert error.code in (401, 403), error.code
        page = ''
        page_url = base
    if 'di-upload' not in page:
        if 'kc-form-login' not in page:
            login_url = base + '/jenkins/securityRealm/commenceLogin?from=/jenkins/anlieferung/'
            with browser.open(login_url, timeout=30) as response:
                page = response.read().decode()
                page_url = response.url
        action = next(form['action'] for form in Forms(page).forms if form.get('id') == 'kc-form-login')
        login = urllib.parse.urljoin(page_url, action)
        issuer = 'http://localhost:' + context.values['KEYCLOAK_PORT']
        assert login.startswith(issuer + '/realms/dateninfrastruktur/')
        credentials = urllib.parse.urlencode({
            'username': 'anna', 'password': context.values['KEYCLOAK_DEMO_PASSWORD'],
        }).encode()
        try:
            with browser.open(login, data=credentials, timeout=30) as response:
                assert response.url.startswith(base + '/jenkins/')
                page = response.read().decode()
        except urllib.error.HTTPError as error:
            path = urllib.parse.urlsplit(error.url).path
            body = error.read(4096).decode(errors='replace')
            title = re.search(r'<title>([^<]*)</title>', body, re.IGNORECASE)
            details = [known for known in ('Cookie not found', 'Invalid username or password',
                       'Invalid code', 'Invalid request') if known.lower() in body.lower()]
            summary = ', '.join(details) if details else title.group(1) if title else ''
            raise AssertionError(f'OIDC callback {path} returned HTTP {error.code} {summary}') from None

    forms = [form for form in Forms(page).forms if 'di-upload' in form.get('class', '').split()]
    assert len(forms) == 1, 'Expected one authorised CSV upload form'
    form = forms[0]
    # The preceding domain probe tests access changes on this synthetic dataset.
    dataset = UUID(form['data-dataset'])
    sql(context, f"UPDATE di_management.dataset SET accesslevel='open' WHERE t_ili_tid='{dataset}'")

    def upload(csv, mode='replace'):
        boundary = uuid4().hex
        data = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="source.csv"\r\n'
                'Content-Type: text/csv\r\n\r\n').encode() + csv + f'\r\n--{boundary}--\r\n'.encode()
        request = urllib.request.Request(base + form['data-endpoint'], data=data, headers={
            'Content-Type': 'multipart/form-data; boundary=' + boundary,
            'Origin': base,
            form['data-crumb-field']: form['data-crumb'],
            'X-Delivery-Dataset': form['data-dataset'],
            'X-Delivery-Issue': form['data-issue'],
            'X-Delivery-Mode': mode,
        })
        try:
            with browser.open(request, timeout=30) as response:
                assert response.status == 201
                status_url = base + json.load(response)['statusUrl']
        except urllib.error.HTTPError as error:
            raise AssertionError('Jenkins upload returned HTTP ' + str(error.code)) from None
        id_ = UUID(urllib.parse.parse_qs(urllib.parse.urlsplit(status_url).query)['id'][0])
        recorded = sql(context, f"SELECT concat_ws(':', inputsize, inputsha256) FROM di_management.submission WHERE t_ili_tid='{id_}'")
        assert recorded == f'{len(csv)}:{hashlib.sha256(csv).hexdigest()}'
        return id_, status_url

    status_errors = []

    def await_result(submission, expected):
        id_, status_url = submission
        for _ in range(60):
            record = sql(context, f"SELECT astatus FROM di_management.submission WHERE t_ili_tid='{id_}'")
            if record not in ('pending', 'processing'):
                break
            time.sleep(2)
        if record != expected:
            result = context.command(['exec', '-T', 'jenkins', 'sh', '-c',
                'for log in "$JENKINS_HOME"/jobs/di-csv-ingest/builds/*/log; do '
                'if [ -f "$log" ]; then tail -30 "$log"; fi; done'], check=False)
            print(context.redact(result.stdout), flush=True)
            raise AssertionError((record, expected))
        with browser.open(status_url, timeout=20) as response:
            page = response.read().decode()
            page_path = urllib.parse.urlsplit(response.url).path
        label = {'accepted': 'Angenommen', 'rejected': 'CSV abgelehnt', 'failed': 'Technischer Fehler'}[expected]
        rendered = re.search(r"""id=['" ]*di-delivery-state['" ]*[^>]*>([^<]*)</p>""", page)
        if not rendered or rendered[1].strip() != label:
            title = re.search(r'<title>([^<]*)</title>', page, re.IGNORECASE)
            diagnostic = (page_path, title[1].strip() if title else '', label,
                          rendered[1].strip() if rendered else 'missing status element')
            status_errors.append(diagnostic)
            print('Jenkins status view mismatch', diagnostic, flush=True)
        return id_

    def accepted(submission, expected_rows):
        id_ = await_result(submission, 'accepted')
        state = sql(context, f"""
            SELECT concat_ws(':', d.objectkey, v.objectcount, d.bytesize)
            FROM di_management.submission s
            JOIN di_management.dataversion v ON v.t_id=s.acceptedversion
            JOIN di_management.datasetissue i ON i.currentversion=v.t_id
            JOIN di_management.distribution d ON d.version=v.t_id WHERE s.t_ili_tid='{id_}'
        """)
        key, count, size = state.split(':')
        assert key.endswith('/snapshot.csv') and int(count) == expected_rows and int(size) > 0
        code, _, data = http(base + '/' + key)
        assert code == 200, code
        table = 'default.snapshot_' + id_.hex
        credentials = 'ch_delivery:' + context.values['DI_CH_LOADER_PASSWORD']
        auth = 'Basic ' + base64.b64encode(credentials.encode()).decode()
        status, _, actual = http('http://localhost:' + context.values['CLICKHOUSE_HTTP_PORT'],
                                 method='POST', headers={'Authorization': auth},
                                 data=('SELECT zone, code FROM ' + table + ' ORDER BY zone FORMAT CSV').encode())
        assert status == 200
        return list(csv.reader(data.decode().splitlines())), list(csv.reader(actual.decode().splitlines()))

    expected = [['zone', 'code'], ['A', '1']]
    content, rows = accepted(upload(b'zone,code\nA,1\n'), 1)
    assert content == expected and rows == expected[1:], (content, rows)
    content, rows = accepted(upload(b'zone,code\nB,2\n', 'append'), 2)
    assert content == expected + [['B', '2']] and rows == content[1:], (content, rows)
    content, rows = accepted(upload(b'zone,code\n'), 0)
    assert content == [['zone', 'code']] and rows == [], (content, rows)
    current = sql(context, f"SELECT currentversion FROM di_management.datasetissue WHERE t_ili_tid='{UUID(form['data-issue'])}'")
    assert current
    await_result(upload(b'zone,code\nA,1\nA,1\n'), 'rejected')
    context.command(['stop', 'clickhouse'])
    await_result(upload(b'zone,code\nA,1\n'), 'failed')
    assert current == sql(context, f"SELECT currentversion FROM di_management.datasetissue WHERE t_ili_tid='{UUID(form['data-issue'])}'")
    assert not status_errors, status_errors
    print('JENKINS_DELIVERY_CASES=5 SKIP=0', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jenkins-image', help='Run the five Jenkins delivery cases with this locally built image')
    args = parser.parse_args()
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
        assert 'DELIVERY_DOMAIN_ASSERTIONS=43 SKIP=0' in output.splitlines()
        assert 'DELIVERY_HTTP_ASSERTIONS=24 SKIP=0' in output.splitlines()
        assert 'ACCESS_CATALOG_CASES=5 SKIP=0' in output.splitlines()
        context.command(['--profile', 'setup', 'run', '--rm', '--no-deps', '--entrypoint', 'java',
            'management-setup', '-jar', '/opt/admin/.runtime/tools/ili2c/ili2c.jar',
            '--no-auto', '/runtime/DI_ExampleCsv.ili'])
        operator(context, 'export', context.runtime / 'delivery-export.xtf')
        context.command(['--profile', 'setup', 'run', '--rm', '--no-deps', '--entrypoint', 'java',
            'management-setup', '-jar', '/opt/admin/.runtime/tools/ilivalidator/ilivalidator-1.15.1.jar',
            '--modeldir', '/opt/admin/models', '/runtime/delivery-export.xtf'])
        context.command(['build', 'admin'])
        context.command(['up', '--no-build', '-d', '--wait', '--wait-timeout', '240', 'garage'])
        context.command(['--profile', 'setup', 'run', '--rm', '--no-deps', 'garage-setup'])
        context = ComposeContext(context.env_file)
        context.command(['up', '--no-build', '-d', '--wait', '--wait-timeout', '300',
                         'keycloak', 'origin', 'admin'])
        identities = delivery_identities(context)
        if args.jenkins_image:
            context.command_overrides['JENKINS_IMAGE'] = verified_image_id(args.jenkins_image)
            context.command(['build', 'sodata'])
            context.command(['up', '--no-build', '-d', '--wait', '--wait-timeout', '300', 'clickhouse'])
            context.command(['--profile', 'setup', 'run', '--rm', '--no-deps', 'clickhouse-init'])
            context.command(['up', '--no-build', '-d', '--wait', '--wait-timeout', '300', 'gateway'])
            verify_jenkins_delivery(context)
        else:
            verify_garage_delivery(context, *identities)

    finally:
        cleanup(context)
    assert not context.command(['ps', '-aq']).stdout.strip()
    print('ASSERTIONS=82 SKIP=0')


if __name__ == '__main__':
    main()
