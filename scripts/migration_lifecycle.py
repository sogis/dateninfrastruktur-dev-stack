"""Explicit, reviewed local cutover. Normal startup never invokes migration."""
import json,pathlib
from consolidation import private_write,inspect
from compose_runtime import ROOT
from migration_db import snapshot,target_sql
from migration_retirement import quiesce,backup_layers,retire,recover_retired

def fixture(operation):
    return operation.context.project.startswith('maf-') and operation.context.values['DI_TEST_FIXTURE']=='true' and all(r.get('source_kind')=='compose-fixture' for r in operation.plan['source_refs'])

def verify_services(operation):
    context=operation.context;context.verify_project()
    rows=[json.loads(line) for line in context.command(['ps','--format','json']).stdout.splitlines()]
    required=set('postgres keycloak garage origin gateway sodata admin jenkins clickhouse superset'.split())
    if len(rows)!=10 or {r['Service'] for r in rows}!=required or any(r['State']!='running' or r.get('Health')!='healthy' for r in rows):raise RuntimeError('VERIFICATION_FAILED: exactly ten healthy canonical services required')
    context.command(['--profile','setup','run','--rm','--no-deps','management-setup','verify'])
    operation.storage('verify-target')
    from migration_identity import Keycloak
    realm=Keycloak('http://localhost:'+context.values['KEYCLOAK_PORT'],'admin',context.values['KEYCLOAK_ADMIN_PASSWORD'])
    actual={u['id'] for u in realm.users('dateninfrastruktur')}
    if not {u['id'] for u in json.loads((operation.root/'target-users.json').read_text())}.issubset(actual):raise RuntimeError('VERIFICATION_FAILED: target identity disappeared')
    check="""from superset.app import create_app
app=create_app()
with app.app_context():
 from superset import db
 from superset.models.core import Database
 from sqlalchemy import text
 d=db.session.query(Database).filter_by(database_name='clickhouse_foundation').one()
 with d.get_sqla_engine() as engine:
  with engine.connect() as connection:assert connection.execute(text('SELECT 1')).scalar()==1
 print('Existing encrypted Superset connection usable')
"""
    result=context.command(['exec','-T','superset','python','-'],check,check=False)
    if result.returncode:raise RuntimeError('VERIFICATION_FAILED: existing encrypted Superset connection; SQL/credentials withheld')
    from migration_prepare import jenkins_jobs
    from consolidation import digest
    jobs=jenkins_jobs(context.values['GATEWAY_PORT'],context.values['JENKINS_ADMIN_PASSWORD'])
    expected_jobs=operation.journal.get('source_jenkins_final_sha256') or operation.plan.get('source_jenkins_sha256')
    if expected_jobs:
        source=operation.root/('source-jenkins-final.json' if operation.journal.get('source_jenkins_final_sha256') else 'source-jenkins.json')
        if digest(source)!=expected_jobs or json.loads(source.read_text())['names']!=jobs:raise RuntimeError('VERIFICATION_FAILED: original Jenkins jobs were not retained')
    private_write(operation.root/'target-readiness.json',{'services':sorted(required),'jenkins_job_names':jobs,'keycloak_users':len(actual),'superset_connection':True})
    print('Canonical services, current schema/identities, private bytes, retained Jenkins login and encrypted Superset connection verified; final user journey remains separate')

def cutover(operation):
    operation.assert_target_binding()
    if not fixture(operation):
        if (ROOT/'.runtime/active-recovery.json').exists():raise RuntimeError('ROLLBACK_UNSAFE: an explicit recovery is active; normal target activation blocked')
        active=ROOT/'.runtime/active-compose.json'
        if active.exists():
            value=json.loads(active.read_text())
            if value['env']!=str(operation.context.env_file) or value['instance']!=operation.context.values['INSTANCE_ID']:raise RuntimeError('OWNERSHIP_MISMATCH: another active target must not be replaced')
    if operation.journal['status'] in ['CUTOVER','RETIRED']:
        verify_services(operation);return
    if operation.journal['status']=='INVENTORIED':
        # Image build is completed while the old frontends still serve users.
        from compose_operations import build
        build(operation.context)
        quiesce(operation);operation.backup()
    operation.restore();operation.verify_sources()
    quiesce(operation,all_sources=True);backup_layers(operation)
    operation.context.command(['up','--no-build','-d','--wait','--wait-timeout','300'])
    verify_services(operation)
    if snapshot(lambda db,q:target_sql(operation.context,db,q),'dateninfrastruktur_management')!=operation.journal['target_management_baseline']:raise RuntimeError('VERIFICATION_FAILED: unexpected target business writes before activation')
    operation.journal['live_status']='LOCAL_CUTOVER_PENDING_FINAL_JOURNEY';operation.save('CUTOVER')
    from compose_operations import volume_bindings
    private_write(operation.context.runtime/'setup-complete.json',{'instance':operation.context.values['INSTANCE_ID'],'mode':'verified-migration','volumes':volume_bindings(operation.context)})
    if not fixture(operation):
        from compose_operations import activate
        activate(operation.context,operation.path)
    print('Single target activated; exact original sources stopped and fully archived; final journey/retirement must still be recorded')

def block_target_start(operation):
    marker={'operation_id':operation.plan['operation_id'],'status':'ROLLBACK_IN_PROGRESS','target_env':str(operation.context.env_file),'recovery_project':operation.journal.get('recovery_project')}
    if not fixture(operation):
        global_marker=ROOT/'.runtime/active-recovery.json'
        if global_marker.exists() and json.loads(global_marker.read_text())['operation_id']!=marker['operation_id']:raise RuntimeError('OWNERSHIP_MISMATCH: another recovery is active')
        private_write(global_marker,marker)
    private_write(operation.context.runtime/'rollback-active.json',marker)

def rollback(operation):
    if not fixture(operation):
        active=ROOT/'.runtime/active-compose.json'
        if active.exists() and json.loads(active.read_text())['instance']!=operation.context.values['INSTANCE_ID']:raise RuntimeError('OWNERSHIP_MISMATCH: active target differs; no rollback started')
    if operation.journal['status']=='RETIRED':recover_retired(operation)
    else:
        from migration_coordinator import rollback as original
        original(operation.plan,operation.context,operation.journal,before_stop=lambda:block_target_start(operation));operation.save()
    marker={'operation_id':operation.plan['operation_id'],'status':operation.journal['status'],'target_env':str(operation.context.env_file),'recovery_project':operation.journal.get('recovery_project')}
    private_write(operation.context.runtime/'rollback-active.json',marker)
    if not fixture(operation):
        active=ROOT/'.runtime/active-compose.json'
        if active.exists():
            value=json.loads(active.read_text())
            if value['instance']!=operation.context.values['INSTANCE_ID']:raise RuntimeError('OWNERSHIP_MISMATCH: active context differs after rollback')
            active.rename(operation.root/'active-compose-before-rollback.json')
        private_write(ROOT/'.runtime/active-recovery.json',marker)
