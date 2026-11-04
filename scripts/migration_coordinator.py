"""Small explicit operator coordinator; no normal application lifecycle here."""
import json,pathlib,subprocess
from consolidation import inspect,private_write,digest
from compose_runtime import ComposeContext
from migration_db import DATABASES,verify_source,source_snapshots,snapshot,target_sql,source_role_checkpoints

def verify_source_checkpoint(plan,metadata):
    if source_snapshots(plan)!={db:metadata['databases'][db]['snapshot'] for db in DATABASES} or source_role_checkpoints(plan)!=metadata['role_checkpoints']:raise RuntimeError('SOURCE_CHANGED: logical source checkpoint no longer matches backup')

def restart_order(states,modes):
    by_id={state['ref']['id']:state for state in states};ordered=[];pending=list(states)
    while pending:
        progress=False
        for state in list(pending):
            mode=modes[state['ref']['id']]
            if state['running'] and mode.startswith('container:'):
                parent=mode.split(':',1)[1]
                candidates=[s for s in states if s['ref']['id']==parent or s['ref']['name'].lstrip('/')==parent]
                if len(candidates)!=1 or not candidates[0]['running']:raise RuntimeError('OWNERSHIP_MISMATCH: namespace parent is not an explicitly selected running source')
                if candidates[0] not in ordered:continue
            ordered.append(state);pending.remove(state);progress=True
        if not progress:raise RuntimeError('OWNERSHIP_MISMATCH: cyclic source namespace dependency')
    return ordered

def rollback(plan,context,journal):
    if journal.get('status')=='RETIRED':raise RuntimeError('ROLLBACK_UNSAFE: retired resources require explicit archived reconstruction')
    if journal.get('database_restored'):
        expected=journal.get('target_management_baseline')
        if not expected or snapshot(lambda db,q:target_sql(context,db,q),'dateninfrastruktur_management')!=expected:raise RuntimeError('ROLLBACK_UNSAFE: target contains unaccounted writes; preserve and reconcile first')
    elif target_sql(context,'postgres',"SELECT count(*) FROM pg_database WHERE datname='dateninfrastruktur_management';")!='0':raise RuntimeError('ROLLBACK_UNSAFE: unverified management target exists')
    states=plan.get('source_states',[])
    if not states:raise RuntimeError('OWNERSHIP_MISMATCH: no explicit source restart state')
    # Verify ALL sources before touching the target or starting even one source.
    for state in states:verify_source(state['ref'],plan['scope'])
    modes={state['ref']['id']:inspect(state['ref']['id'])['HostConfig']['NetworkMode'] for state in states}
    ordered=restart_order(states,modes)
    context.command(['stop'])
    for state in ordered:
        cid=verify_source(state['ref'],plan['scope']);running=inspect(cid)['State']['Running']
        if running!=state['running']:
            p=subprocess.run(['docker','start' if state['running'] else 'stop',cid],capture_output=True)
            if p.returncode:raise RuntimeError('ROLLBACK_FAILED: own source state restoration')
    journal['status']='ROLLED_BACK'
    print('Rollback verified: owned target stopped, exact original source containers resumed; no data/volume reset')

def verify_identity_effect(plan,context,metadata):
    from migration_db import source_sql
    db='dateninfrastruktur_management';query="SELECT coalesce(json_agg(to_jsonb(t) ORDER BY t_id),'[]') FROM di_management.principal t;"
    original=json.loads(source_sql(plan,plan['sources']['management_pg'],db,query));actual=json.loads(target_sql(context,db,query))
    if len(original)!=len(actual):raise RuntimeError('VERIFICATION_FAILED: principal cardinality changed')
    for before,after in zip(original,actual):
        expected=dict(before)
        if before['akind']=='user':
            if before['aissuer']!=plan['source_old_issuer']:raise RuntimeError('IDENTITY_CONFLICT: unexpected source issuer')
            expected['aissuer']=plan['target_issuer'];expected['row_version']+=1;expected['t_user']='di_migrator';expected['t_lastchange']=after['t_lastchange']
        if expected!=after:raise RuntimeError('VERIFICATION_FAILED: principal changed beyond its current issuer and audited system stamp')
    current=snapshot(lambda name,q:target_sql(context,name,q),db);before=metadata['databases'][db]['snapshot']
    allowed={'di_management.principal','audit.row_change','di_ops.schema_revision','di_ops.contract_fingerprint'}
    if any(current['tables'].get(name)!=value for name,value in before['tables'].items() if name not in allowed):raise RuntimeError('VERIFICATION_FAILED: business rows outside identity migration changed')

class Migration:
    def __init__(self,path):
        self.path=pathlib.Path(path).resolve();self.plan=json.loads(self.path.read_text());self.context=ComposeContext(self.plan['target_env']);self.root=self.context.runtime/'migration'
        self.root.mkdir(exist_ok=True);self.root.chmod(0o700);self.journal_path=self.root/'journal.json'
        if self.plan.get('target_instance') and self.plan['target_instance']!=self.context.values['INSTANCE_ID']:raise RuntimeError('OWNERSHIP_MISMATCH: target instance binding')
        from migration_binding import artifact_hashes
        if self.plan.get('target_artifacts')!=artifact_hashes():raise RuntimeError('SOURCE_CHANGED: reviewed target executable files changed')
        self.journal=json.loads(self.journal_path.read_text()) if self.journal_path.exists() else {'operation_id':self.plan['operation_id'],'plan_sha256':digest(self.path),'status':'INVENTORIED','target_env_sha256':self.plan['target_env_sha256'],'target_runtime_files':self.plan['target_runtime_files']}
        if self.journal['operation_id']!=self.plan['operation_id'] or self.journal['plan_sha256']!=digest(self.path):raise RuntimeError('SOURCE_CHANGED: operation plan binding')
        self.assert_target_binding()
    def assert_target_binding(self):
        from migration_binding import artifact_hashes,runtime_hashes
        if runtime_hashes(self.context)!=self.journal['target_runtime_files']:raise RuntimeError('SOURCE_CHANGED: rendered target configuration')
        if digest(self.context.env_file)!=self.journal['target_env_sha256'] or artifact_hashes()!=self.plan['target_artifacts']:raise RuntimeError('SOURCE_CHANGED: target configuration or executable binding')
    def save(self,status=None):
        self.assert_target_binding()
        if status:self.journal['status']=status
        private_write(self.journal_path,self.journal)
    def metadata(self):
        p=self.root/'databases/database-manifest.json'
        if self.journal.get('database_manifest_sha256')!=digest(p):raise RuntimeError('SOURCE_CHANGED: database manifest')
        return json.loads(p.read_text())
    def storage(self,action):
        self.assert_target_binding()
        from compose_runtime import read_env
        from migration_db import verify_source
        ref=self.plan['sources']['management_garage'];raw=inspect(verify_source(ref,self.plan['scope']));secret=self.plan['source_storage']
        if digest(secret['path'])!=secret['sha256']:raise RuntimeError('SOURCE_CHANGED: storage credential reference')
        values=json.loads(pathlib.Path(secret['path']).read_text()) if secret['format']=='json' else read_env(secret['path'])
        network=self.context.values['MIGRATION_SOURCE_NETWORK']
        if network not in raw['NetworkSettings']['Networks']:raise RuntimeError('OWNERSHIP_MISMATCH: source storage network')
        target_name=self.context.project+'-garage-1'
        # Exact private config; source credentials are never command arguments or report content.
        private_write(self.root/'storage.json',{'bucket':'di-managed-private','source':{'endpoint':'http://'+raw['Name'].lstrip('/')+':3900','access_key':values[secret['access_field']],'secret_key':values[secret['secret_field']]},'target':{'endpoint':'http://'+target_name+':3900','access_key':self.context.values['GARAGE_MANAGED_ACCESS_KEY'],'secret_key':self.context.values['GARAGE_MANAGED_SECRET_KEY']}})
        self.context.command(['--profile','migration','run','--pull','never','--rm','--no-deps','migration-storage',action])
    def verify_sources(self):
        from migration_backup import verify_keycloak_source
        if digest(self.root/'keycloak-original-manifest.json')!=self.journal['keycloak_manifest_sha256'] or digest(self.root/'storage-manifest.json')!=self.journal['storage_manifest_sha256']:raise RuntimeError('SOURCE_CHANGED: bound backup manifest')
        verify_source_checkpoint(self.plan,self.metadata());verify_keycloak_source(self.plan,self.context);self.storage('source-inventory')
    def backup(self):
        from migration_backup import backup_keycloak
        from migration_db import backup_databases
        if self.journal['status']!='INVENTORIED':self.verify_sources();return
        # Only the two database servers and selected MA storage may remain up.
        allowed={self.plan['sources'][key]['id'] for key in ['foundation_pg','management_pg','management_garage']}
        for state in self.plan['source_states']:
            cid=verify_source(state['ref'],self.plan['scope'])
            if cid not in allowed and inspect(cid)['State']['Running']:raise RuntimeError('SOURCE_NOT_QUIESCED: selected writer/frontend still active')
        backup_keycloak(self.plan,self.context);backup_databases(self.plan,self.root/'databases');self.storage('source-inventory')
        self.journal['database_manifest_sha256']=digest(self.root/'databases/database-manifest.json');self.journal['keycloak_manifest_sha256']=digest(self.root/'keycloak-original-manifest.json');self.journal['storage_manifest_sha256']=digest(self.root/'storage-manifest.json');self.save('BACKED_UP')
    def restore(self):
        self.assert_target_binding()
        from migration_db import restore_databases
        if self.journal['status'] not in ['BACKED_UP','TARGET_RESTORED','IDENTITIES_MIGRATED','VERIFIED']:raise RuntimeError('VERIFICATION_FAILED: explicit backup required before restore')
        self.verify_sources()
        if self.journal['status']=='VERIFIED':self.verify();return
        self.context.command(['up','--no-build','-d','--wait','--wait-timeout','180','postgres'])
        if not self.journal.get('database_restored'):
            restore_databases(self.context,self.metadata(),self.journal)
            self.journal['target_management_baseline']=snapshot(lambda db,q:target_sql(self.context,db,q),'dateninfrastruktur_management');self.save('TARGET_RESTORED')
        if self.journal['status']=='TARGET_RESTORED':self.identities()
        self.storage('copy');self.verify()
    def identities(self):
        import hashlib
        from compose_runtime import update_context,render
        from migration_identity import reconcile
        from migration_db import row_hash_sql
        context=self.context;db='dateninfrastruktur_management';self.verify_sources()
        context.command(['up','--no-build','-d','--wait','--wait-timeout','300','garage','keycloak'])
        context.command(['--profile','setup','run','--pull','never','--rm','--no-deps','garage-setup'])
        export=self.root/'keycloak-export/dateninfrastruktur-realm.json';reconcile(context,export)
        result=json.loads((self.root/'identity-result.json').read_text());self.assert_target_binding();self.context=context=update_context(context,{'DI_OIDC_CLIENT_SECRET':result['gateway_client_secret']});self.journal['target_env_sha256']=digest(context.env_file);render(context);from migration_binding import runtime_hashes;self.journal['target_runtime_files']=runtime_hashes(context);self.save()
        old_max=target_sql(context,db,'SELECT coalesce(max(change_id),0) FROM audit.row_change;')
        if 'audit_prefix' not in self.journal:self.journal['audit_prefix']={'max_id':old_max,'sha256':target_sql(context,db,row_hash_sql('SELECT * FROM audit.row_change WHERE change_id<='+old_max)+';')};self.save()
        context.command(['--profile','migration','run','--pull','never','--rm','--no-deps','management-upgrade'])
        self.journal['target_management_baseline']=snapshot(lambda name,q:target_sql(context,name,q),db);self.save()
        mapping_file=self.root/'identity-mapping.json'
        if not mapping_file.exists():
            rows=json.loads(target_sql(context,db,"SELECT coalesce(json_agg(json_build_object('principal_uuid',t_ili_tid,'old_issuer',aissuer,'old_subject',asubject,'new_subject',asubject)),'[]') FROM di_management.principal WHERE akind='user';"))
            for row in rows:
                if row['old_issuer']!=self.plan['source_old_issuer']:raise RuntimeError('IDENTITY_CONFLICT: unexpected current principal issuer')
                row['new_issuer']=self.plan['target_issuer']
            private_write(mapping_file,{'operation_id':self.plan['operation_id'],'expected_fingerprint':target_sql(context,db,'SELECT di_ops.contract_fingerprint();'),'source_export':{'path':'/runtime/migration/keycloak-export/dateninfrastruktur-realm.json','sha256':digest(export)},'target_users':{'path':'/runtime/migration/target-users.json','sha256':digest(self.root/'target-users.json')},'mapping':rows})
        for action in ['plan','apply','verify']:context.command(['--profile','migration','run','--pull','never','--rm','--no-deps','identity-migrate',action,'/runtime/migration/identity-mapping.json'])
        verify_identity_effect(self.plan,context,self.metadata())
        prefix=self.journal['audit_prefix']
        if target_sql(context,db,row_hash_sql('SELECT * FROM audit.row_change WHERE change_id<='+prefix['max_id'])+';')!=prefix['sha256']:raise RuntimeError('VERIFICATION_FAILED: old audit contents changed')
        self.journal['target_management_baseline']=snapshot(lambda name,q:target_sql(context,name,q),db);self.save('IDENTITIES_MIGRATED')
    def verify(self):
        from migration_db import row_hash_sql,verify_restored_roles
        verify_restored_roles(self.context,self.metadata())
        if self.journal['status'] not in ['IDENTITIES_MIGRATED','VERIFIED']:raise RuntimeError('VERIFICATION_FAILED: target migration incomplete')
        if snapshot(lambda db,q:target_sql(self.context,db,q),'dateninfrastruktur_management')!=self.journal['target_management_baseline']:raise RuntimeError('VERIFICATION_FAILED: target changed outside recorded migration')
        prefix=self.journal['audit_prefix']
        if target_sql(self.context,'dateninfrastruktur_management',row_hash_sql('SELECT * FROM audit.row_change WHERE change_id<='+prefix['max_id'])+';')!=prefix['sha256']:raise RuntimeError('VERIFICATION_FAILED: immutable historical audit prefix')
        self.storage('verify');self.save('VERIFIED')
        print('Target verified privately: logical restore, current identity bindings, immutable old audit and exact object bytes/metadata; not yet cut over')
    def rollback(self):
        self.assert_target_binding()
        rollback(self.plan,self.context,self.journal);self.save()
