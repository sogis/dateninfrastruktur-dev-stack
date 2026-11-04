#!/usr/bin/env python3
"""Focused real Keycloak regression for MA permissions of overlapping UUIDs."""
import copy,json,secrets,uuid
from compose_runtime import ROOT,init_context,write_private
from consolidation import private_write
from migration_identity import Keycloak,reconcile,IdentityConflict,permission_plan
from test_consolidation_f1 import reserve_ports,cleanup,token

def run(c):
    c.command(['build','management-tool-build'])
    c.command(['up','--no-build','-d','--wait','--wait-timeout','180','postgres'])
    c.command(['--profile','setup','run','--rm','--no-deps','postgres-init'])
    c.command(['up','--no-build','-d','--wait','--wait-timeout','240','keycloak'])
    kc=Keycloak('http://localhost:'+c.values['KEYCLOAK_PORT'],'admin',c.values['KEYCLOAK_ADMIN_PASSWORD']);realm='dateninfrastruktur'
    anna=kc.api(realm+'/users/0b7c9d5e-1f2a-4d3b-8c4e-5f6a7b8c9d01');anna['firstName']='Current MA profile';anna.update(realmRoles=['ma-reader'],groups=['/ma-team'],clientRoles={'ma-client':['read']})
    newcomer={'id':str(uuid.uuid4()),'username':'ma-only','firstName':'MA','lastName':'Only','email':'ma-only@example.invalid','emailVerified':True,'enabled':True,'credentials':[{'type':'password','value':c.values['KEYCLOAK_DEMO_PASSWORD'],'temporary':False}],'realmRoles':['ma-reader'],'groups':['/ma-team'],'clientRoles':{'ma-client':['read']}}
    group={'id':str(uuid.uuid4()),'name':'ma-team','path':'/ma-team','realmRoles':['ma-reader'],'subGroups':[{'id':str(uuid.uuid4()),'name':'child','path':'/ma-team/child'}]}
    anna['groups'].append('/ma-team/child');newcomer['groups'].append('/ma-team/child')
    client={'id':str(uuid.uuid4()),'clientId':'ma-client','enabled':True,'protocol':'openid-connect','publicClient':True}
    export={'realm':realm,'users':[anna,newcomer],'clients':[client],'groups':[group],'roles':{'realm':[{'id':str(uuid.uuid4()),'name':'ma-reader','description':'MA permission','composite':False}],'client':{'ma-client':[{'id':str(uuid.uuid4()),'name':'read','composite':False}]}}}
    file=c.runtime/'permission-source.json';private_write(file,export)
    foreign_before={x['id'] for x in kc.users(realm)};clients_before={x['id'] for x in kc.api(realm+'/clients')}
    reconcile(c,file);reconcile(c,file)
    assert foreign_before.issubset({x['id'] for x in kc.users(realm)}) and clients_before.issubset({x['id'] for x in kc.api(realm+'/clients')})
    assert next(x for x in kc.api(realm+'/clients') if x['clientId']=='ma-client')['id']==client['id']
    for user in [anna,newcomer]:
        base=realm+'/users/'+user['id']
        assert 'ma-reader' in {r['name'] for r in kc.api(base+'/role-mappings/realm')}
        assert 'read' in {r['name'] for r in kc.api(base+'/role-mappings/clients/'+client['id'])}
        assert {group['id'],group['subGroups'][0]['id']}.issubset({g['id'] for g in kc.api(base+'/groups')})
    token(c,'anna');token(c,'ma-only')
    before=kc.api(realm+'/users/'+anna['id']);bad=copy.deepcopy(export);bad['roles']['realm'][0]['description']='conflicting meaning';bad['users'][0]['firstName']='must not be written';private_write(file,bad)
    try:permission_plan(kc,realm,bad,kc.api(realm+'/clients'),kc.groups(realm))
    except IdentityConflict:pass
    else:raise AssertionError('Conflicting role definition accepted')
    try:reconcile(c,file)
    except IdentityConflict:pass
    else:raise AssertionError('Conflicting role definition accepted')
    assert kc.api(realm+'/users/'+anna['id'])==before
    print('PASS F10 delta: same-UUID and MA-only users retain realm/client roles and group UUID/membership; Foundation login and foreign identities retained; replay no-op; role conflict rejects before profile write',flush=True)

if __name__=='__main__':
    c=init_context('maf-f2-identity-'+secrets.token_hex(5),reserve_ports(),True)
    try:run(c)
    finally:cleanup(c)
