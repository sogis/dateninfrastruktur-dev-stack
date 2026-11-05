#!/usr/bin/env python3
"""Nonempty Foundation + MA fixtures, canonical target; no user state/credentials."""
import copy,hashlib,json,pathlib,secrets,subprocess,sys,uuid
from compose_runtime import ROOT,ComposeContext,init_context,update_context,write_private,render
from test_consolidation_f1 import reserve_ports,seed,sql,cleanup
from migration_db import backup_databases,restore_databases,source_snapshots,source_sql,target_sql,snapshot,verify_source
from consolidation import reference,inspect,private_write,digest
from migration_backup import backup_keycloak
from migration_identity import Keycloak,reconcile,identity_plan,IdentityConflict

def fixture_ref(c,service):
    cid=c.command(['ps','-aq',service]).stdout.strip();r=reference(inspect(cid));r.update(source_kind='compose-fixture',service=service,context={'path':str(c.env_file),'sha256':digest(c.env_file)});return r

def create_fixtures(f,m,t):
    f.command(['build','admin','sodata','management-tool-build','test-tool-build','superset'])
    from migration_fixture import legacy_tool
    f,legacy=legacy_tool(f)
    images={k:v for k,v in f.values.items() if k.endswith('_IMAGE') and k!='LEGACY_TOOL_IMAGE'}
    m=update_context(m,{**images,'TOOL_IMAGE':legacy,'LEGACY_TOOL_IMAGE':legacy})
    t=update_context(t,images)
    for c in [f,m]:
        c.command((['--profile','migration-fixture'] if c is m else [])+['up','--no-build','-d','--wait','--wait-timeout','150','fixture-postgres-old' if c is m else 'postgres','garage'])
        for service in ['postgres-init','legacy-management-setup' if c is m else 'management-setup','garage-setup']:c.command(['--profile','setup','--profile','migration-fixture','run','--pull','never','--rm','--no-deps',service])
    f=ComposeContext(f.env_file);m=ComposeContext(m.env_file)
    f.command(['up','--no-build','-d','--wait','--wait-timeout','240','clickhouse'])
    f.command(['--profile','setup','run','--pull','never','--rm','--no-deps','clickhouse-init'])
    f.command(['up','--no-build','-d','--wait','--wait-timeout','300','keycloak','superset'])
    m.command(['--profile','migration-fixture','up','--no-build','-d','--wait','--wait-timeout','180','fixture-keycloak-h2'])
    live=Keycloak('http://localhost:'+m.values['KEYCLOAK_PORT'],'admin',m.values['KEYCLOAK_ADMIN_PASSWORD'])
    live.api('dateninfrastruktur/users',{'id':str(uuid.uuid4()),'username':'ma-only-person','firstName':'MA','lastName':'Only','enabled':True,'email':'ma-only@example.invalid','emailVerified':True,'credentials':[{'type':'password','value':m.values['KEYCLOAK_DEMO_PASSWORD'],'temporary':False}]},'POST')
    source_person=live.api('dateninfrastruktur/users/0b7c9d5e-1f2a-4d3b-8c4e-5f6a7b8c9d01');source_person['firstName']='Anna MA current profile'
    live.api('dateninfrastruktur/users/0b7c9d5e-1f2a-4d3b-8c4e-5f6a7b8c9d01',source_person,'PUT')
    live.api('dateninfrastruktur/clients',{'id':str(uuid.uuid4()),'clientId':'ma-only-client','enabled':True,'protocol':'openid-connect','publicClient':True},'POST')
    # Permissions created after startup must survive for an overlapping UUID too.
    realm='dateninfrastruktur';live.api(realm+'/roles',{'name':'ma-reader','description':'MA permission'},'POST')
    role=live.api(realm+'/roles/ma-reader')
    live.api(realm+'/groups',{'name':'ma-team'},'POST');group=next(g for g in live.groups(realm) if g['name']=='ma-team')
    client=next(c for c in live.api(realm+'/clients') if c['clientId']=='ma-only-client')
    live.api(realm+'/clients/'+client['id']+'/roles',{'name':'read'},'POST');client_role=live.api(realm+'/clients/'+client['id']+'/roles/read')
    for user in [u for u in live.users(realm) if u['username'] in ['anna','ma-only-person']]:
        base=realm+'/users/'+user['id'];live.api(base+'/role-mappings/realm',[role],'POST');live.api(base+'/role-mappings/clients/'+client['id'],[client_role],'POST');live.api(base+'/groups/'+group['id'],{},'PUT')
    # A legacy Foundation object must survive; its key must not gain access to managed private files.
    write_private(f.runtime/'foundation-sentinel.txt','foundation legacy bytes retained\n')
    f.command(['--profile','tools','run','--pull','never','--rm','--no-deps','storage-tool','copyto','/runtime/foundation-sentinel.txt','managed:ch.so.daten/foundation-sentinel.txt'])
    kc=Keycloak('http://localhost:'+f.values['KEYCLOAK_PORT'],'admin',f.values['KEYCLOAK_ADMIN_PASSWORD'])
    kc.api('dateninfrastruktur/clients',{'id':str(uuid.uuid4()),'clientId':'foundation-foreign-client','enabled':True,'protocol':'openid-connect','publicClient':True},'POST')
    sql(m,"CREATE EXTENSION IF NOT EXISTS fuzzystrmatch; CREATE EXTENSION IF NOT EXISTS postgis_topology; CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder; ALTER ROLE di_audit_reader IN DATABASE dateninfrastruktur_management SET statement_timeout TO '7s';",service='fixture-postgres-old')
    seed(m,database_service='fixture-postgres-old');m.command(['--profile','test','run','--pull','never','--rm','--no-deps','test-fixture','migration-sentinels'])
    # Quiesce only the isolated source fixture writers before checkpoint/dump/export.
    f.command(['stop','--timeout','60','keycloak','superset']);m.command(['--profile','migration-fixture','stop','--timeout','60','fixture-keycloak-h2'])
    return f,m,t

def migration_plan(f,m,t):
    f.command(['stop','--timeout','60','garage','clickhouse'])
    inherited={k:f.values[k] for k in ['KEYCLOAK_DB_PASSWORD','KEYCLOAK_ADMIN_PASSWORD','KEYCLOAK_DEMO_PASSWORD','SUPERSET_DB_PASSWORD','SUPERSET_ADMIN_PASSWORD','SUPERSET_SECRET_KEY','CLICKHOUSE_DEFAULT_PASSWORD','CLICKHOUSE_ADMIN_PASSWORD','CLICKHOUSE_TEST_READER_PASSWORD','CLICKHOUSE_SUPERSET_READER_PASSWORD','GARAGE_DEFAULT_ACCESS_KEY','GARAGE_DEFAULT_SECRET_KEY','GARAGE_META_VOLUME','GARAGE_DATA_VOLUME','CLICKHOUSE_DATA_VOLUME','CLICKHOUSE_LOG_VOLUME','SUPERSET_VOLUME']}
    inherited.update({k:m.values[k] for k in ['DI_WRITER_PASSWORD','DI_AUTHZ_PASSWORD','DI_PUBLIC_PASSWORD','DI_AUDIT_READER_PASSWORD','DI_MIGRATOR_PASSWORD','DI_OIDC_CLIENT_SECRET','DI_SESSION_SECRET','DI_GATEWAY_SECRET']})
    inherited.update({'GARAGE_ORIGIN_ACCESS_KEY':m.values['GARAGE_ORIGIN_ACCESS_KEY'],'GARAGE_ORIGIN_SECRET_KEY':m.values['GARAGE_ORIGIN_SECRET_KEY'],'GARAGE_MANAGED_ACCESS_KEY':m.values['GARAGE_DEFAULT_ACCESS_KEY'],'GARAGE_MANAGED_SECRET_KEY':m.values['GARAGE_DEFAULT_SECRET_KEY'],'DI_MIGRATION_IMPORT_KEYS':'true','GARAGE_VOLUMES_EXTERNAL':'true','CLICKHOUSE_VOLUMES_EXTERNAL':'true','SUPERSET_VOLUME_EXTERNAL':'true','MIGRATION_SOURCE_NETWORK':m.project+'_default','MIGRATION_KEYCLOAK_IMAGE':fixture_ref(m,'fixture-keycloak-h2')['image_id']})
    t=update_context(t,inherited);write_private(t.runtime/'garage.toml',(f.runtime/'garage.toml').read_text());render(t)
    refs=[fixture_ref(f,s) for s in ['postgres','keycloak','superset','garage','clickhouse']]+[fixture_ref(m,s) for s in ['fixture-postgres-old','fixture-keycloak-h2','garage']]
    sources={'foundation_pg':refs[0],'management_pg':refs[5],'management_keycloak':refs[6],'management_garage':refs[7]}
    from migration_binding import artifact_hashes,runtime_hashes
    plan={'schema_version':1,'mode':'migrate','scope':{'workspace':str(ROOT.parent),'foundation_project':f.project},'operation_id':str(uuid.uuid4()),'source_refs':refs,'retire_allowlist':[r['id'] for r in refs],'source_states':[{'ref':r,'running':True} for r in refs],'sources':sources,'target_env':str(t.env_file),'target_instance':t.values['INSTANCE_ID'],'target_env_sha256':digest(t.env_file),'target_artifacts':artifact_hashes(),'target_runtime_files':runtime_hashes(t),'target_project':t.project,'source_old_issuer':'http://localhost:'+m.values['KEYCLOAK_PORT']+'/realms/dateninfrastruktur','target_issuer':'http://localhost:'+t.values['KEYCLOAK_PORT']+'/realms/dateninfrastruktur','source_storage':{'path':str(m.env_file),'sha256':digest(m.env_file),'format':'dotenv','access_field':'GARAGE_DEFAULT_ACCESS_KEY','secret_field':'GARAGE_DEFAULT_SECRET_KEY'}}
    file=t.runtime/'migration/plan.json';private_write(file,plan);return f,m,t,file

def wait_identity(c):
    import time
    from test_consolidation_f1 import http
    for attempt in range(100):
        try:
            if http('http://localhost:'+c.values['KEYCLOAK_PORT']+'/realms/dateninfrastruktur/.well-known/openid-configuration')[0]==200:return
        except Exception:pass
        time.sleep(.3)
    raise RuntimeError('Restored own source identity service unavailable')

def probe_storage(c,key,action,f=None):
    data={'key':key,'action':action}
    if f:
        endpoint='http://'+inspect(c.command(['ps','-q','garage']).stdout.strip())['Name'].lstrip('/')+':3900'
        data.update(foundation={'endpoint':endpoint,'access_key':f.values['GARAGE_DEFAULT_ACCESS_KEY'],'secret_key':f.values['GARAGE_DEFAULT_SECRET_KEY']},origin={'endpoint':endpoint,'access_key':c.values['GARAGE_ORIGIN_ACCESS_KEY'],'secret_key':c.values['GARAGE_ORIGIN_SECRET_KEY']})
    private_write(c.runtime/'migration/storage-probe.json',data)
    result=c.command(['--profile','migration','run','--pull','never','--rm','--no-deps','--entrypoint','python3','migration-storage','-'],(ROOT/'tests/consolidation/storage_probe.py').read_text());print(result.stdout.strip(),flush=True)

def run(f,m,t):
    from migration_coordinator import Migration,rollback,verify_source_checkpoint
    f,m,t=create_fixtures(f,m,t);f,m,t,file=migration_plan(f,m,t);plan=json.loads(file.read_text());root=t.runtime/'migration'
    # Failure after a real database backup, before any activation. Sources still exist.
    probe=backup_databases(plan,root/'precutover-probe-databases')
    t.command(['up','--no-build','-d','--wait','--wait-timeout','180','postgres'])
    failed={'status':'FAILED_BEFORE_CUTOVER','database_restored':False};rollback(plan,t,failed)
    assert failed['status']=='ROLLED_BACK';wait_identity(f);wait_identity(m)
    # The old source account can still log in; its persisted current H2 profile remains.
    old=Keycloak('http://localhost:'+m.values['KEYCLOAK_PORT'],'admin',m.values['KEYCLOAK_ADMIN_PASSWORD'])
    assert next(u for u in old.users('dateninfrastruktur') if u['id']=='0b7c9d5e-1f2a-4d3b-8c4e-5f6a7b8c9d01')['firstName']=='Anna MA current profile'
    source_sql(plan,plan['sources']['management_pg'],'postgres',"ALTER ROLE di_audit_reader SET statement_timeout='8s';")
    try:verify_source_checkpoint(plan,probe)
    except RuntimeError as error:assert 'SOURCE_CHANGED' in str(error)
    else:raise AssertionError('Changed global application role accepted')
    source_sql(plan,plan['sources']['management_pg'],'postgres',"ALTER ROLE di_audit_reader RESET statement_timeout;")
    current=Keycloak('http://localhost:'+f.values['KEYCLOAK_PORT'],'admin',f.values['KEYCLOAK_ADMIN_PASSWORD']);current.api('dateninfrastruktur/clients',{'clientId':'after-snapshot-client','enabled':True,'protocol':'openid-connect','publicClient':True},'POST')
    try:verify_source_checkpoint(plan,probe)
    except RuntimeError as error:assert 'SOURCE_CHANGED' in str(error)
    else:raise AssertionError('Changed source snapshot accepted')
    f.command(['stop','--timeout','60','keycloak','superset','garage','clickhouse']);m.command(['--profile','migration-fixture','stop','--timeout','60','fixture-keycloak-h2'])
    print('PASS F12 partial: real pre-cutover failure/rollback resumed exact sources; later source change invalidates earlier backup',flush=True)
    migration=Migration(file)
    # Put nontrivial source metadata in the fixture BEFORE the bound final inventory.
    # Configure only the source SDK endpoint; no target application is started here.
    migration.storage('source-inventory');files=json.loads((m.runtime/'fixture.json').read_text())['files'];key=files[0]['key']
    probe_storage(t,key,'customize-source')
    # That deliberate test change must be detected; a new final source inventory is explicit.
    try:migration.storage('source-inventory')
    except RuntimeError as error:assert 'SOURCE_CHANGED' in str(error)
    else:raise AssertionError('Changed S3 checkpoint accepted')
    # Only this disposable pre-final manifest is reset; user archives are never removed.
    assert t.project.startswith('maf-f2-');(root/'storage-manifest.json').rename(root/'pre-final-storage-manifest.json')
    migration.backup()
    proof=root/'keycloak-export/dateninfrastruktur-realm.json';original=proof.read_text();write_private(proof,original+'\n')
    try:migration.verify_sources()
    except RuntimeError as error:assert 'SOURCE_CHANGED' in str(error)
    else:raise AssertionError('Changed archived identity proof accepted')
    write_private(proof,original)
    migration.restore();migration.restore()
    t=migration.context;metadata=migration.metadata()
    assert target_sql(t,'postgres',"SELECT s.setconfig::text FROM pg_db_role_setting s JOIN pg_roles r ON r.oid=s.setrole JOIN pg_database d ON d.oid=s.setdatabase WHERE r.rolname='di_audit_reader' AND d.datname='dateninfrastruktur_management';")=="{statement_timeout=7s}"
    assert int(target_sql(t,'superset','SELECT count(*) FROM dbs;'))>=1
    assert target_sql(t,'dateninfrastruktur_management','SELECT count(*) FROM di_management.accessgrant;')=='2'
    export=json.loads((root/'keycloak-export/dateninfrastruktur-realm.json').read_text());initial=json.loads((m.runtime/'realm-initial.json').read_text())
    assert len(export['users'])>len(initial['users']) and next(u for u in export['users'] if u['id']=='0b7c9d5e-1f2a-4d3b-8c4e-5f6a7b8c9d01')['firstName']!=initial['users'][0]['firstName']
    assert source_sql(plan,plan['sources']['management_pg'],'postgres',"SELECT current_setting('server_version_num');")=='160009'
    print('PASS F09/F10: nonempty full logical restore PG16.9→16.10, normalized owners/ACLs/sequences, current H2 export, UUID/client/profile/credential policy and audited issuer mapping; whole coordinator replay no-op',flush=True)
    manifest=json.loads((root/'storage-manifest.json').read_text());assert len(manifest)==8 and any(v['metadata'].get('Metadata') for v in manifest.values())
    probe_storage(t,key,'permission-boundaries',f)
    for action,expected in [('target-bytes-conflict','STORAGE_CONFLICT'),('target-metadata-conflict','STORAGE_CONFLICT'),('source-changed','SOURCE_CHANGED')]:
        probe_storage(t,key,action)
        try:migration.storage('copy')
        except RuntimeError as error:assert expected in str(error)
        else:raise AssertionError('S3 collision/change accepted')
        probe_storage(t,key,'restore-source' if action=='source-changed' else 'restore-target')
    migration.storage('verify')
    print('PASS F11: eight unique historical byte streams and metadata, idempotent copy; byte/metadata conflict and changed source rejected; origin read-only and legacy-key private denial with positive controls',flush=True)
    # An ambiguous person proof and a forged migrator context must not mutate the DB.
    target_users=json.loads((root/'target-users.json').read_text());bad=copy.deepcopy(export);bad['users'][0]['id']=str(uuid.uuid4())
    try:identity_plan(bad,target_users,[],[])
    except IdentityConflict:pass
    else:raise AssertionError('Equal name/email merged different subject IDs')
    before=snapshot(lambda db,q:target_sql(t,db,q),'dateninfrastruktur_management')
    mapping=json.loads((root/'identity-mapping.json').read_text());badmap=copy.deepcopy(mapping);badmap['mapping'][0]['new_subject']=str(uuid.uuid4());private_write(root/'invalid-mapping.json',badmap)
    result=t.command(['--profile','migration','run','--pull','never','--rm','--no-deps','identity-migrate','apply','/runtime/migration/invalid-mapping.json'],check=False)
    assert result.returncode!=0 and 'IDENTITY_CONFLICT' in result.stdout+result.stderr
    code="""import os,subprocess,json
m=json.load(open('/runtime/migration/identity-mapping.json'));row=m['mapping'][0]
e=os.environ.copy();e.update(PGUSER='di_writer',PGPASSWORD=os.environ['DI_WRITER_PASSWORD'])
def lit(v):return "'"+v.replace("'","''")+"'"
q="BEGIN; SELECT set_config('di.actor_issuer','urn:di:migration',true),set_config('di.actor_kind','service',true),set_config('di.actor_subject',"+lit(m['operation_id'])+",true),set_config('di.action','operator.migrate_identity',true),set_config('di.request_id',"+lit(m['operation_id'])+",true),set_config('di.command_id',"+lit(m['operation_id'])+",true),set_config('di.migration_operation',"+lit(m['operation_id'])+",true),set_config('di.migration_target_issuer','http://localhost:9999/realms/dateninfrastruktur',true); UPDATE di_management.principal SET aissuer='http://localhost:9999/realms/dateninfrastruktur' WHERE t_ili_tid="+lit(row['principal_uuid'])+"::uuid; COMMIT;"
p=subprocess.run(['psql','-X','-q','-At','-v','ON_ERROR_STOP=1'],input=q,env=e,capture_output=True,text=True)
assert p.returncode!=0 and 'principal external identity immutable' in p.stderr
print('writer cannot forge privileged migration context')
"""
    t.command(['--profile','setup','run','--pull','never','--rm','--no-deps','--entrypoint','python3','management-setup','-c',code])
    assert snapshot(lambda db,q:target_sql(t,db,q),'dateninfrastruktur_management')==before
    # Open the restored target using the SAME default Compose services, not a test app topology.
    pg_before=inspect(t.command(['ps','-q','postgres']).stdout.strip())
    t.command(['up','--no-build','-d','--wait','--wait-timeout','300'])
    pg_after=inspect(t.command(['ps','-q','postgres']).stdout.strip())
    assert pg_before['Id']==pg_after['Id'] and pg_before['Image']==pg_after['Image'],'runtime job unexpectedly rebuilt/recreated PostgreSQL'
    from test_consolidation_f1 import token,http,check_topology
    check_topology(t)
    anna=token(t,'anna');ben=token(t,'ben');gateway='http://localhost:'+t.values['GATEWAY_PORT']
    for filedata in files:
        status,_,body=http(gateway+filedata['path'],anna);assert status==200 and hashlib.sha256(body).hexdigest()==filedata['sha256']
        if filedata['kind']=='restricted':assert http(gateway+filedata['path'],ben)[0]==403
    check="""from superset.app import create_app
app=create_app()
with app.app_context():
 from superset import db
 from superset.models.core import Database
 from sqlalchemy import text
 d=db.session.query(Database).filter_by(database_name='clickhouse_foundation').one()
 with d.get_sqla_engine() as engine:
  with engine.connect() as connection:assert connection.execute(text('SELECT count(*) FROM foundation.smoke_metrics')).scalar()==3
 print('restored encrypted Superset connection remains usable')
"""
    t.command(['exec','-T','superset','python','-'],check)
    assert t.values['SUPERSET_SECRET_KEY']==f.values['SUPERSET_SECRET_KEY']
    for path in root.rglob('*'):
        if path.is_file():assert path.stat().st_mode&0o077==0,'backup file is not private'
    print('PASS F13: retained Foundation password authenticates same subjects; all imported grants/revocations govern files; complete Superset DB/SECRET_KEY decrypts existing connection; private backups',flush=True)
    # Prove restored ili2db PKs can advance through an actual audited Cayenne operation.
    t.command(['--profile','tools','run','--pull','never','--rm','--no-deps','--entrypoint','java','management-operator','-Dloader.main=ch.so.agi.dateninfrastruktur.admin.operator.AuthorityBootstrapCommand','-cp','/opt/admin/app.jar','org.springframework.boot.loader.launch.PropertiesLauncher','bootstrap-office',plan['target_issuer'],'0b7c9d5e-1f2a-4d3b-8c4e-5f6a7b8c9d01','maf-restored-sequence','Restore sequence sentinel'])
    assert int(target_sql(t,'dateninfrastruktur_management',"SELECT t_id FROM di_management.office WHERE identifier='maf-restored-sequence';"))>int(metadata['databases']['dateninfrastruktur_management']['snapshot']['sequences']['di_management.t_ili2db_seq'].split('|')[0])
    try:migration.rollback()
    except RuntimeError as error:assert 'ROLLBACK_UNSAFE' in str(error)
    else:raise AssertionError('Target writes silently discarded by rollback')
    assert http(gateway+files[0]['path'],anna)[0]==200
    print('PASS F12: restart/replay creates no duplicates; restored sequence supports audited Cayenne write; rollback refuses subsequent target writes before stopping anything',flush=True)
    print('PASS MA-F2 F09–F13',flush=True)
    return f,m,t

if __name__=='__main__':
    paths=[init_context('maf-f2-'+kind+'-'+secrets.token_hex(4),reserve_ports(),True) for kind in ['foundation','management','target']]
    write_private(ROOT/'.runtime/maf-f2-current.json',json.dumps(dict(zip(['foundation','management','target'],[str(c.env_file) for c in paths]))))
    try:run(*paths)
    except Exception as error:
        value=str(error)
        for context in paths:value=context.redact(value)
        print(value,file=sys.stderr);raise SystemExit(1)
    finally:
        # Reread contexts: setup/identity reconciliation legitimately persisted values.
        for context in reversed(paths):
            cleanup(ComposeContext(context.env_file))
