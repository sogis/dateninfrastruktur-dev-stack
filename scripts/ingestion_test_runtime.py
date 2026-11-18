"""Shared isolated MA-G test transport and resource teardown."""
import json,re,socket,subprocess,urllib.error,urllib.parse,urllib.request

from compose_operations import LOCAL_IMAGES


def reserve_ports():
    sockets=[]
    try:
        for _ in range(5):
            s=socket.socket();s.bind(('127.0.0.1',0));sockets.append(s)
        return dict(zip(['GATEWAY_PORT','KEYCLOAK_PORT','SUPERSET_PORT','CLICKHOUSE_HTTP_PORT','CLICKHOUSE_NATIVE_PORT'],[s.getsockname()[1] for s in sockets]))
    finally:
        for s in sockets:s.close()
def sql(context, query, *, failure=None):
    result = context.command(['exec', '-T', 'postgres', 'psql', '-X', '-q', '-At',
                              '-v', 'ON_ERROR_STOP=1', '-U', 'postgres', '-d', 'dateninfrastruktur_management'],
                             input=query, check=False)
    if failure:
        assert result.returncode and failure in result.stderr, context.redact(result.stderr)
        return
    assert result.returncode == 0, context.redact(result.stderr)
    return result.stdout.strip()


def http(url,token=None,method='GET',headers=None,data=None):
    h=dict(headers or {})
    if token:h['Authorization']='Bearer '+token
    request=urllib.request.Request(url,data=data,method=method,headers=h)
    try:
        with urllib.request.urlopen(request,timeout=20) as r:return r.status,dict(r.headers),r.read()
    except urllib.error.HTTPError as e:return e.code,dict(e.headers),e.read()
def token(c,user):
    body=urllib.parse.urlencode(dict(grant_type='password',client_id='management-test',username=user,password=c.values['KEYCLOAK_DEMO_PASSWORD'])).encode()
    code,_,data=http('http://localhost:'+c.values['KEYCLOAK_PORT']+'/realms/dateninfrastruktur/protocol/openid-connect/token',method='POST',data=body)
    detail=json.loads(data) if code!=200 else {}
    assert code==200,'real Keycloak token issuance failed: '+user+' HTTP '+str(code)+' '+str(detail.get('error'))+' '+str(detail.get('error_description'))
    return json.loads(data)['access_token']
def cleanup(c):
    if c.values.get('DI_TEST_FIXTURE')!='true' or not re.fullmatch(r'mag-[a-z0-9-]+',c.project):
        raise RuntimeError('Refusing to clean a non-fixture Compose project')
    c.verify_project()
    ids=subprocess.check_output(['docker','volume','ls','-q','--filter','label=com.docker.compose.project='+c.project],text=True).split()
    expected={c.values[k] for k in ['POSTGRES_VOLUME','GARAGE_META_VOLUME','GARAGE_DATA_VOLUME','JENKINS_VOLUME','CLICKHOUSE_DATA_VOLUME','CLICKHOUSE_LOG_VOLUME','SUPERSET_VOLUME']}
    volumes = json.loads(subprocess.check_output(['docker', 'volume', 'inspect', *ids], text=True)) if ids else []
    for volume in volumes:
        name = volume['Name']
        if (name not in expected
                or (volume.get('Labels') or {}).get('com.docker.compose.project') != c.project):
            raise RuntimeError('Refusing to remove an unowned fixture volume: ' + name)
    # Some volumes are external, and Compose resolves named volumes even
    # when they carry another project's labels. Remove only the inspected set.
    c.command(['--profile', '*', 'down'])
    for volume in volumes:
        name = volume['Name']
        current = json.loads(subprocess.check_output(['docker', 'volume', 'inspect', name], text=True))[0]
        if current != volume:
            raise RuntimeError('Fixture volume identity changed: ' + name)
        subprocess.run(['docker','volume','rm',name],check=True,capture_output=True)
    # A configured shared or release tag is outside the fixture's ownership.
    images = []
    for key, name in LOCAL_IMAGES.items():
        reference = f'dateninfrastruktur-{name}:{c.project}'
        if reference not in (c.values.get(key), c.command_overrides.get(key)):
            continue
        tags = subprocess.check_output(
            ['docker', 'image', 'ls', '--filter', f'reference={reference}',
             '--format', '{{.Repository}}:{{.Tag}}'],
            text=True,
        ).splitlines()
        if reference in tags:
            images.append(reference)
    if images:
        subprocess.run(['docker', 'image', 'rm', '--no-prune', *images], check=True, capture_output=True)
