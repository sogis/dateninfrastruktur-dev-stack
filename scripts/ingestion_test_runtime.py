"""Shared isolated MA-G test transport and resource teardown."""
import json,re,socket,urllib.error,urllib.parse,urllib.request


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
def cleanup(context):
    if (context.values.get('DI_TEST_FIXTURE') != 'true'
            or not re.fullmatch(r'mag-[a-z0-9-]+-[0-9a-f]{10,12}', context.project)):
        raise RuntimeError('Refusing to clean a non-fixture Compose project')
    context.command(['--profile', '*', 'down', '--volumes', '--remove-orphans'])
