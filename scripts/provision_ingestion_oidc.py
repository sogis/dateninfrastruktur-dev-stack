#!/usr/bin/env python3
"""Explicit, scoped creation/verification of two clients in the owned local Keycloak realm."""
import argparse,hmac,json,urllib.error,urllib.parse,urllib.request,uuid
from compose_operations import resolve
from compose_runtime import ComposeContext,write_private
from ingestion_clients import clients,executor_subject,EXECUTOR,JENKINS,ROLE_NAMES
from prepare_ingestion_credentials import prepare,KEYS

CH_KEYS=('DI_CH_LOADER_PASSWORD','DI_CH_PROJECTOR_PASSWORD','DI_CH_READER_PASSWORD')
OIDC_KEYS=('DI_JENKINS_OIDC_CLIENT_SECRET','DI_INGESTION_EXECUTOR_CLIENT_SECRET')

def call(base,path,method='GET',token=None,data=None,expected=(200,)):
    headers={'Accept':'application/json'}
    if token:headers['Authorization']='Bearer '+token
    if isinstance(data,bytes):headers['Content-Type']='application/x-www-form-urlencoded'
    elif data is not None:headers['Content-Type']='application/json';data=json.dumps(data).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(base+path,data=data,headers=headers,method=method),timeout=20) as response:
            if response.status not in expected:raise RuntimeError('Unexpected Keycloak operator HTTP status')
            raw=response.read(524289)
            if len(raw)>524288:raise RuntimeError('Keycloak operator response too large')
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:raise RuntimeError('Explicit Keycloak client operation rejected (HTTP '+str(error.code)+')') from None

def provision(context):
    context.verify_project()
    rows=context.command(['ps','-q','keycloak']).stdout.split();assert len(rows)==1,'Exactly one owned Keycloak service required'
    base='http://localhost:'+str(int(context.values['KEYCLOAK_PORT']));admin='/admin/realms/dateninfrastruktur'
    # Existing local operator credential is used transiently; supplier clients forbid password grant.
    form=urllib.parse.urlencode({'grant_type':'password','client_id':'admin-cli','username':'admin','password':context.values['KEYCLOAK_ADMIN_PASSWORD']}).encode()
    token=call(base,'/realms/master/protocol/openid-connect/token','POST',data=form)['access_token']
    def get(path):return call(base,admin+path,token=token)
    def post(path,value,expected=(201,204)):return call(base,admin+path,'POST',token,value,expected)
    def find(client):
        matches=[item for item in get('/clients?clientId='+urllib.parse.quote(client)) if item.get('clientId')==client]
        if len(matches)>1:raise RuntimeError('Ambiguous delivery client')
        return matches[0] if matches else None
    existing={name:find(name) for name in (JENKINS,EXECUTOR)}
    for name,value in existing.items():
        if value and value.get('attributes',{}).get('di.managed')!='ingestion-v1':raise RuntimeError('Unowned delivery client collision; no change')
        key=OIDC_KEYS[0] if name==JENKINS else OIDC_KEYS[1]
        if value and key not in context.values:raise RuntimeError('Owned client credential not bound to this runtime; no rotation')
    prepare(context,KEYS+OIDC_KEYS+CH_KEYS);context=ComposeContext(context.env_file)
    def verify_representation(want,have):
        for key in ('clientId','protocol','publicClient','enabled','directAccessGrantsEnabled','standardFlowEnabled','serviceAccountsEnabled','implicitFlowEnabled','redirectUris','webOrigins','fullScopeAllowed','defaultClientScopes','optionalClientScopes'):
            if key in want:
                fallback=False if isinstance(want[key],bool) else [] if isinstance(want[key],list) else None
                actual=have.get(key,fallback)
                if isinstance(want[key],list):actual=sorted(actual)
                expected=sorted(want[key]) if isinstance(want[key],list) else want[key]
                if actual!=expected:raise RuntimeError('Existing delivery client differs in '+key+'; no replacement')
        for key,value in want.get('attributes',{}).items():
            if have.get('attributes',{}).get(key)!=value:raise RuntimeError('Existing delivery client attribute differs; no replacement')
        identifier=str(uuid.UUID(have['id']))
        mapper=[{k:m.get(k) for k in ('name','protocol','protocolMapper','config')} for m in get('/clients/'+identifier+'/protocol-mappers/models')]
        if mapper!=want['protocolMappers']:raise RuntimeError('Existing delivery audience mapper differs; no replacement')
        secret=get('/clients/'+identifier+'/client-secret').get('value','')
        if not hmac.compare_digest(secret,want['secret']):raise RuntimeError('Existing delivery client secret differs; no rotation')
        return identifier
    desired=clients(context.values)
    # Validate both existing profiles before creating either missing client.
    for want in desired:
        if existing[want['clientId']]:verify_representation(want,existing[want['clientId']])
    ids={}
    for want in desired:
        if not existing[want['clientId']]:post('/clients',want)
        ids[want['clientId']]=verify_representation(want,find(want['clientId']))
    prefix='/clients/'+ids[EXECUTOR];roles=get(prefix+'/roles');names={row['name'] for row in roles}
    if names-set(ROLE_NAMES):raise RuntimeError('Unexpected existing executor role; no removal')
    for missing in set(ROLE_NAMES)-names:post(prefix+'/roles',{'name':missing})
    roles=get(prefix+'/roles');scope=prefix+'/scope-mappings/clients/'+ids[EXECUTOR]
    missing=set(ROLE_NAMES)-{row['name'] for row in get(scope)}
    if missing:post(scope,[r for r in roles if r['name'] in missing])
    account=str(uuid.UUID(get(prefix+'/service-account-user')['id']));mapping='/users/'+account+'/role-mappings/clients/'+ids[EXECUTOR]
    missing=set(ROLE_NAMES)-{row['name'] for row in get(mapping)}
    if missing:post(mapping,[r for r in roles if r['name'] in missing])
    issuer,subject=executor_subject(context.values)
    if subject!=account:raise RuntimeError('Token subject does not match the owned client service account')
    request={'schemaVersion':1,'commandId':str(uuid.uuid5(uuid.NAMESPACE_URL,'urn:di:executor:'+context.values['INSTANCE_ID'])),'issuer':issuer,'subject':subject}
    path=context.runtime/'delivery-executor-identity.json'
    if path.exists():
        if json.loads(path.read_text())!=request:raise RuntimeError('Existing executor identity binding differs; no overwrite')
    else:write_private(path,json.dumps(request,indent=2)+'\n')
    return context,path

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--env');p.add_argument('--project');p.add_argument('--register-pg',action='store_true');a=p.parse_args();c,path=provision(resolve(a.env,a.project))
    if a.register_pg:
        c.command(['--profile','tools','run','--rm','--no-deps','--entrypoint','java','management-operator','-Dloader.main=ch.so.agi.dateninfrastruktur.admin.operator.DeliveryServiceIdentityCommand','-cp','/opt/admin/app.jar','org.springframework.boot.loader.launch.PropertiesLauncher','/runtime/'+path.name])
    print('Explicit delivery clients verified; existing human identities/clients retained; no Fach grants created.')
