"""Private Keycloak reconciliation: Foundation is authoritative; UUIDs prove users."""
import copy,hashlib,json,pathlib,urllib.error,urllib.parse,urllib.request
from consolidation import private_write,digest
class IdentityConflict(RuntimeError):pass
class Keycloak:
    def __init__(self,url,user,password):
        self.url=url.rstrip('/');body=urllib.parse.urlencode({'grant_type':'password','client_id':'admin-cli','username':user,'password':password}).encode()
        try:
            with urllib.request.urlopen(urllib.request.Request(self.url+'/realms/master/protocol/openid-connect/token',data=body),timeout=20) as r:self.token=json.load(r)['access_token']
        except Exception:raise RuntimeError('KEYCLOAK_AUTH_FAILED: credentials withheld') from None
    def api(self,path,body=None,method=None):
        req=urllib.request.Request(self.url+'/admin/realms/'+path,data=None if body is None else json.dumps(body).encode(),headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json'},method=method)
        try:
            with urllib.request.urlopen(req,timeout=30) as r:
                raw=r.read();return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:raise RuntimeError('KEYCLOAK_OPERATION_FAILED: HTTP '+str(e.code)) from None
    def users(self,realm):
        result=[];first=0
        while True:
            page=self.api(realm+'/users?first='+str(first)+'&max=100&briefRepresentation=false');result+=page
            if len(page)<100:return result
            first+=100

    def groups(self,realm):
        def pages(path):
            values=[];first=0
            while True:
                page=self.api(path+('&' if '?' in path else '?')+'first='+str(first)+'&max=100');values+=page
                if len(page)<100:return values
                first+=100
        def children(group):
            group['subGroups']=pages(realm+'/groups/'+group['id']+'/children?briefRepresentation=false')
            for child in group['subGroups']:children(child)
        result=pages(realm+'/groups?briefRepresentation=false&populateHierarchy=false')
        for group in result:children(group)
        return result

def identity_plan(export,users,groups,clients):
    if export.get('realm')!='dateninfrastruktur':raise IdentityConflict('IDENTITY_CONFLICT: unexpected source realm')
    target={u['id']:u for u in users};source=export.get('users',[])
    if len(target)!=len(users) or len({u['id'] for u in source})!=len(source):raise IdentityConflict('IDENTITY_CONFLICT: duplicate user UUID')
    additions=[];overlaps=[];updates=[]
    for user in source:
        if any(t['id']!=user['id'] and (t.get('username','').casefold()==user.get('username','').casefold() or (user.get('email') and t.get('email','').casefold()==user['email'].casefold())) for t in users):raise IdentityConflict('IDENTITY_CONFLICT: equal name/email is not a UUID proof')
        if user['id'] in target:
            overlaps.append(user['id'])
            fields=['username','enabled','email','emailVerified','firstName','lastName','attributes','requiredActions']
            update={k:user[k] for k in fields if k in user}
            if any(target[user['id']].get(k)!=v for k,v in update.items()):updates.append({'id':user['id'],**update})
            continue # Foundation password credentials retained; selected MA person's current profile carried over.
        additions.append(copy.deepcopy(user))
    by_group_id={g['id']:path for g,path in group_entries(groups)};by_path={path:g for g,path in group_entries(groups)};new_groups=[]
    for group in export.get('groups',[]):
        # Whole new subtrees are imported; collisions anywhere in an existing subtree fail closed.
        for g,path in group_entries([group]):
            if g['id'] in by_group_id:
                if path!=by_group_id[g['id']]:raise IdentityConflict('IDENTITY_CONFLICT: group UUID/path changed')
            elif path in by_path:raise IdentityConflict('IDENTITY_CONFLICT: same group path with another UUID')
        if group['id'] not in by_group_id:new_groups.append(copy.deepcopy(group))
        elif any(g['id'] not in by_group_id for g,_ in group_entries([group])):raise IdentityConflict('IDENTITY_CONFLICT: existing nested group needs explicit reconciliation')
    builtins={'account','account-console','admin-cli','broker','realm-management','security-admin-console','management-test'}
    by_client={c['clientId']:c for c in clients};new_clients=[]
    for client in export.get('clients',[]):
        cid=client['clientId']
        if cid in builtins or cid=='management-gateway':continue
        if cid in by_client:
            if client['id']!=by_client[cid]['id']:raise IdentityConflict('IDENTITY_CONFLICT: custom client ID collision')
        else:new_clients.append(copy.deepcopy(client))
    return {'users':additions,'updates':updates,'groups':new_groups,'clients':new_clients,'overlapping_user_uuids':overlaps,'foundation_credentials_retained':len(overlaps)}

def group_entries(values,parent=''):
    for group in values:
        path=group.get('path') or parent+'/'+group['name']
        yield group,path
        yield from group_entries(group.get('subGroups',[]),path)

def permission_plan(kc,realm,export,clients,groups):
    """Preserve the union only for proven persons/groups and equivalent roles."""
    builtin_clients={'account','account-console','admin-cli','broker','realm-management','security-admin-console'}
    builtin_roles={'default-roles-'+realm,'offline_access','uma_authorization'}
    by_client={c['clientId']:c for c in clients}
    expected_clients={c['clientId'] for c in export.get('clients',[])}|set(by_client)
    new_roles={'realm':[],'client':{}}
    available={}
    scopes={'realm':export.get('roles',{}).get('realm',[])}
    scopes.update({client:roles for client,roles in export.get('roles',{}).get('client',{}).items() if client not in builtin_clients})
    def current_roles(scope):
        if scope=='realm':return kc.api(realm+'/roles')
        if scope not in by_client:return []
        return kc.api(realm+'/clients/'+by_client[scope]['id']+'/roles')
    def business(role):return {k:role.get(k) or default for k,default in [('description',''),('attributes',{})]}
    for scope,definitions in scopes.items():
        if scope!='realm' and (scope not in expected_clients or (definitions and scope in {'management-test','management-gateway'} and scope not in by_client)):raise IdentityConflict('IDENTITY_CONFLICT: roles refer to missing client')
        current={r['name']:r for r in current_roles(scope)};available[scope]=set(current)|{r['name'] for r in definitions}
        for role in definitions:
            name=role['name']
            if scope=='realm' and name in builtin_roles:continue
            if name not in current:
                if scope=='realm':new_roles['realm'].append(role)
                else:new_roles['client'].setdefault(scope,[]).append(role)
            else:
                existing=kc.api(realm+'/roles-by-id/'+current[name]['id'])
                if business(existing)!=business(role):raise IdentityConflict('IDENTITY_CONFLICT: role definition differs')
                wanted={('realm',n) for n in role.get('composites',{}).get('realm',[])}
                wanted|={(c,n) for c,names in role.get('composites',{}).get('client',{}).items() for n in names}
                children=kc.api(realm+'/roles-by-id/'+existing['id']+'/composites') if existing.get('composite') else []
                client_names={c['id']:c['clientId'] for c in clients}
                actual={(client_names.get(r.get('containerId')) if r.get('clientRole') else 'realm',r['name']) for r in children}
                if actual!=wanted:raise IdentityConflict('IDENTITY_CONFLICT: composite role differs')
    known_paths={path for _,path in group_entries(groups)}|{path for _,path in group_entries(export.get('groups',[]))}
    for principal in [*export.get('users',[]),*(g for g,_ in group_entries(export.get('groups',[])))]:
        if not set(principal.get('realmRoles',[])).issubset(available.get('realm',set())):raise IdentityConflict('IDENTITY_CONFLICT: missing realm role')
        for scope,names in principal.get('clientRoles',{}).items():
            if scope not in available:available[scope]={r['name'] for r in current_roles(scope)}
            if not set(names).issubset(available[scope]):raise IdentityConflict('IDENTITY_CONFLICT: missing client role')
        if not set(principal.get('groups',[])).issubset(known_paths):raise IdentityConflict('IDENTITY_CONFLICT: missing group membership')
    return new_roles

def apply_permissions(kc,realm,export):
    clients={c['clientId']:c for c in kc.api(realm+'/clients')}
    paths={path:g for g,path in group_entries(kc.groups(realm))}
    principals=[('users',u) for u in export.get('users',[])]+[('groups',g) for g,_ in group_entries(export.get('groups',[]))]
    for kind,principal in principals:
        base=realm+'/'+kind+'/'+principal['id']
        def assign(suffix,names,role_path):
            wanted=set(names)
            if not wanted:return
            definitions={r['name']:r for r in kc.api(role_path)}
            current={r['name'] for r in kc.api(base+'/role-mappings/'+suffix)}
            missing=wanted-current
            if missing:kc.api(base+'/role-mappings/'+suffix,[definitions[n] for n in sorted(missing)],'POST')
            if not wanted.issubset({r['name'] for r in kc.api(base+'/role-mappings/'+suffix)}):raise IdentityConflict('IDENTITY_CONFLICT: role membership not preserved')
        assign('realm',principal.get('realmRoles',[]),realm+'/roles')
        for client,names in principal.get('clientRoles',{}).items():
            cid=clients[client]['id'];assign('clients/'+cid,names,realm+'/clients/'+cid+'/roles')
        if kind=='users':
            current={g['id'] for g in kc.api(base+'/groups?max=10000')}
            for path in principal.get('groups',[]):
                group=paths[path]
                if group['id'] not in current:kc.api(base+'/groups/'+group['id'],{},'PUT')
            if not {paths[p]['id'] for p in principal.get('groups',[])}.issubset({g['id'] for g in kc.api(base+'/groups?max=10000')}):raise IdentityConflict('IDENTITY_CONFLICT: group membership not preserved')


def reconcile(context,export_file):
    export_file=pathlib.Path(export_file);export=json.loads(export_file.read_text());realm='dateninfrastruktur'
    prior=context.runtime/'migration/identity-result.json'
    if prior.exists() and json.loads(prior.read_text())['source_export_sha256']!=digest(export_file):raise IdentityConflict('IDENTITY_CONFLICT: prior source export changed')
    kc=Keycloak('http://localhost:'+context.values['KEYCLOAK_PORT'],'admin',context.values['KEYCLOAK_ADMIN_PASSWORD'])
    before=kc.users(realm);clients=kc.api(realm+'/clients');groups=kc.groups(realm)
    if prior.exists():
        gateway=next((c for c in clients if c['clientId']=='management-gateway'),None)
        if not gateway or kc.api(realm+'/clients/'+gateway['id']+'/client-secret')['value']!=json.loads(prior.read_text())['gateway_client_secret']:raise IdentityConflict('IDENTITY_CONFLICT: prior gateway binding changed')
    plan=identity_plan(export,before,groups,clients)
    new_roles=permission_plan(kc,realm,export,clients,groups)
    # All conflicts detected before this first mutation. Source client UUIDs stay stable.
    for client in plan['clients']:kc.api(realm+'/clients',client,'POST')
    if new_roles['realm'] or new_roles['client']:kc.api(realm+'/partialImport',{'ifResourceExists':'FAIL','roles':new_roles},'POST')
    if plan['users'] or plan['groups']:kc.api(realm+'/partialImport',{'ifResourceExists':'FAIL','users':plan['users'],'groups':plan['groups']},'POST')
    for update in plan['updates']:kc.api(realm+'/users/'+update['id'],update,'PUT')
    after=kc.users(realm);after_ids={u['id'] for u in after}
    if not {u['id'] for u in before}.issubset(after_ids) or not {u['id'] for u in export.get('users',[])}.issubset(after_ids):raise IdentityConflict('IDENTITY_CONFLICT: imported user UUID not preserved')
    all_groups=kc.groups(realm)
    if not {g['id'] for g,_ in group_entries(export.get('groups',[]))}.issubset({g['id'] for g,_ in group_entries(all_groups)}):raise IdentityConflict('IDENTITY_CONFLICT: group UUID was not preserved')
    all_clients={c['clientId']:c for c in kc.api(realm+'/clients')}
    if any(all_clients.get(c['clientId'],{}).get('id')!=c['id'] for c in plan['clients']):raise IdentityConflict('IDENTITY_CONFLICT: custom client UUID was not preserved')
    apply_permissions(kc,realm,export)
    wanted=next((c for c in export.get('clients',[]) if c['clientId']=='management-gateway'),{})
    current=next((c for c in clients if c['clientId']=='management-gateway'),None)
    desired={'clientId':'management-gateway','enabled':True,'protocol':'openid-connect','publicClient':False,'standardFlowEnabled':True,'directAccessGrantsEnabled':False,'redirectUris':['http://localhost:'+context.values['GATEWAY_PORT']+'/oidc/callback'],'webOrigins':['http://localhost:'+context.values['GATEWAY_PORT']],'protocolMappers':[{'name':'management-api audience','protocol':'openid-connect','protocolMapper':'oidc-audience-mapper','config':{'included.custom.audience':'management-api','access.token.claim':'true','id.token.claim':'false'}}]}
    if current:
        secret=kc.api(realm+'/clients/'+current['id']+'/client-secret')['value'];current.update(desired);kc.api(realm+'/clients/'+current['id'],current,'PUT')
    else:
        secret=wanted.get('secret') or context.values['DI_OIDC_CLIENT_SECRET'];desired['secret']=secret
        if wanted.get('id'):desired['id']=wanted['id']
        kc.api(realm+'/clients',desired,'POST')
    if context.values['DI_TEST_FIXTURE']!='true':
        test=next((c for c in kc.api(realm+'/clients') if c['clientId']=='management-test'),None)
        if test:test['enabled']=False;kc.api(realm+'/clients/'+test['id'],test,'PUT')
    folder=context.runtime/'migration';folder.mkdir(exist_ok=True);folder.chmod(0o700)
    proof=folder/'target-users.json'
    if not proof.exists():private_write(proof,after)
    elif not {u['id'] for u in json.loads(proof.read_text())}.issubset(after_ids):raise IdentityConflict('IDENTITY_CONFLICT: previously verified target person disappeared')
    result_path=folder/'identity-result.json'
    if result_path.exists():
        previous=json.loads(result_path.read_text())
        if previous['source_export_sha256']!=digest(export_file) or previous['gateway_client_secret']!=secret:raise IdentityConflict('IDENTITY_CONFLICT: prior source/client binding changed')
        return after
    private_write(result_path,{'source_export_sha256':digest(export_file),'preserved_foundation_users':len(before),'imported_ma_only_users':len(plan['users']),'updated_ma_profiles':len(plan['updates']),'foundation_credentials_retained':plan['foundation_credentials_retained'],'gateway_client_secret':secret})
    return after
