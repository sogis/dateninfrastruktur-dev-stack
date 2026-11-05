"""Single fixed Keycloak delivery-client representation for fresh and explicit existing setup."""
import base64,json,urllib.parse,urllib.request,uuid
EXECUTOR='di-ingestion-executor'
JENKINS='jenkins-delivery'
ROLE_NAMES=('dispatch','execute')

def audience(name):
    return {'name':name+' audience','protocol':'openid-connect','protocolMapper':'oidc-audience-mapper','config':{'included.custom.audience':name,'access.token.claim':'true','id.token.claim':'false','introspection.token.claim':'true','userinfo.token.claim':'false'}}

def clients(values):
    gateway='http://localhost:'+values['GATEWAY_PORT'];jenkins=gateway+'/jenkins/'
    common={'enabled':True,'protocol':'openid-connect','publicClient':False,'directAccessGrantsEnabled':False,'implicitFlowEnabled':False}
    return [{**common,'clientId':JENKINS,'secret':values['DI_JENKINS_OIDC_CLIENT_SECRET'],'standardFlowEnabled':True,'serviceAccountsEnabled':False,
             'redirectUris':[jenkins+'securityRealm/finishLogin'],'webOrigins':[gateway],
             'attributes':{'pkce.code.challenge.method':'S256','post.logout.redirect.uris':jenkins,'di.managed':'ingestion-v1'},'protocolMappers':[audience('di-ingestion-user')]},
            {**common,'clientId':EXECUTOR,'secret':values['DI_INGESTION_EXECUTOR_CLIENT_SECRET'],'standardFlowEnabled':False,'serviceAccountsEnabled':True,
             'redirectUris':[],'webOrigins':[],'fullScopeAllowed':False,'defaultClientScopes':['roles'],'optionalClientScopes':[],
             'attributes':{'di.managed':'ingestion-v1'},'protocolMappers':[audience(EXECUTOR)]}]

def extend_fresh(realm,values):
    realm['clients'].extend(clients(values))
    realm.setdefault('roles',{}).setdefault('client',{})[EXECUTOR]=[{'name':role} for role in ROLE_NAMES]
    realm.setdefault('clientScopeMappings',{})[EXECUTOR]=[{'client':EXECUTOR,'roles':list(ROLE_NAMES)}]
    # Explicit technical client identity, not a human/PG Fach seed.
    subject=str(uuid.uuid5(uuid.NAMESPACE_URL,'urn:di:ingestion-executor:'+values['INSTANCE_ID']))
    realm['users'].append({'id':subject,'username':'service-account-'+EXECUTOR,'enabled':True,'serviceAccountClientId':EXECUTOR,'clientRoles':{EXECUTOR:list(ROLE_NAMES)}})
    return subject

def executor_subject(values):
    issuer='http://localhost:'+str(int(values['KEYCLOAK_PORT']))+'/realms/dateninfrastruktur'
    body=urllib.parse.urlencode({'grant_type':'client_credentials','client_id':EXECUTOR,'client_secret':values['DI_INGESTION_EXECUTOR_CLIENT_SECRET']}).encode()
    with urllib.request.urlopen(urllib.request.Request(issuer+'/protocol/openid-connect/token',data=body),timeout=15) as response:
        token=json.loads(response.read(32769))['access_token']
    segment=token.split('.')[1];claims=json.loads(base64.urlsafe_b64decode(segment+'='*(-len(segment)%4)));roles=claims.get('resource_access',{})
    if set(roles)!={EXECUTOR} or set(roles[EXECUTOR]['roles'])!=set(ROLE_NAMES) or claims.get('iss')!=issuer or claims.get('azp')!=EXECUTOR or claims.get('typ')!='Bearer':raise RuntimeError('Unexpected effective executor identity profile')
    audience=claims['aud'] if isinstance(claims['aud'],list) else [claims['aud']]
    if EXECUTOR not in audience or 'management-api' in audience or 'di-ingestion-user' in audience:raise RuntimeError('Unexpected executor audience')
    return issuer,str(uuid.UUID(claims['sub']))
