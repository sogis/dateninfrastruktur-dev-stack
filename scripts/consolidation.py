#!/usr/bin/env python3
"""MA-F source inventory and guarded plan. Discovery never starts or stops services."""
import argparse,datetime,hashlib,json,os,pathlib,re,subprocess
STACK=pathlib.Path(__file__).resolve().parents[1];WORKSPACE=STACK.parent
REPOS=['dateninfrastruktur-dev-stack','dateninfrastruktur-admin','dateninfrastruktur-sodata','dateninfrastruktur-jenkins-dev','dateninfrastruktur-jenkins-gretl-plugin','dateninfrastruktur-themenrepo']
LEGACY_STATES=['managed/identity/state.json','managed-test/identity/state.json','identity/state.json','managed/database/connection.json','managed-test/database/connection.json','management-db/connection.json']
def command(args,input=None):
    p=subprocess.run(args,input=input,capture_output=True,text=True)
    if p.returncode:raise RuntimeError('Command failed: '+args[0]+' '+args[1]+' (details withheld)')
    return p.stdout
def digest(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def private_write(path,value):
    path=pathlib.Path(path).absolute();path.parent.mkdir(parents=True,exist_ok=True);path.parent.chmod(0o700)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w') as f:json.dump(value,f,indent=2,ensure_ascii=False);f.write('\n')
    path.chmod(0o600)
def inspect(cid):
    if not re.fullmatch('[0-9a-f]{64}',cid):raise RuntimeError('OWNERSHIP_MISMATCH: full container ID required')
    return json.loads(command(['docker','inspect',cid]))[0]
def reference(container):
    labels=container['Config'].get('Labels') or {}
    secret_fields=sorted(v.split('=',1)[0] for v in container['Config'].get('Env',[]) if re.search(r'PASSWORD|SECRET|TOKEN|ACCESS_KEY|CREDENTIAL',v.split('=',1)[0]))
    return {'id':container['Id'],'name':container['Name'],'image':container['Config']['Image'],'image_id':container['Image'],'state':container['State']['Status'],'labels':{k:v for k,v in labels.items() if k.startswith(('com.docker.compose.','di.'))},'mounts':[{k:m.get(k) for k in ['Type','Name','Source','Destination','RW']} for m in container['Mounts']],'ports':container['HostConfig'].get('PortBindings') or {},'restart':container['HostConfig']['RestartPolicy'],'secret_fields':secret_fields}
def state_refs(workspace=WORKSPACE):
    base=workspace/'dateninfrastruktur-admin/.runtime';result=[]
    for relative in LEGACY_STATES:
        path=base/relative
        if not path.is_file():continue
        if not path.resolve().is_relative_to(base.resolve()):raise RuntimeError('OWNERSHIP_MISMATCH: state path escapes runtime')
        value=json.loads(path.read_text());ids=set(value.get('containers',[]))|set(value.get('services',{}).values())
        ids.update(value[k] for k in ['container','database'] if value.get(k))
        result.append({'path':str(path.resolve()),'sha256':digest(path),'ids':sorted(ids),'runtime_id':value.get('id'),'database_name':value.get('name'),'issuer_reference':value.get('keycloak'),'secret_fields':[k for k in value if any(x in k.lower() for x in ['secret','password']) or k.endswith('Key')]})
    return result
def verify_ownership(ref,scope,observed=None):
    """Recheck immutable identity, scope, labels and mounts BEFORE a supplied operation."""
    actual=reference(observed if observed is not None else inspect(ref['id']))
    for key in ['id','name','image_id','mounts']:
        if actual[key]!=ref[key]:raise RuntimeError('OWNERSHIP_MISMATCH: source identity changed')
    labels=actual['labels'];workspace=pathlib.Path(scope['workspace']).resolve()
    if ref['source_kind']=='foundation':
        expected_root=str(workspace/'dateninfrastruktur-dev-stack')
        if labels.get('com.docker.compose.project')!=scope['foundation_project'] or labels.get('com.docker.compose.project.working_dir')!=expected_root or labels.get('com.docker.compose.project.config_files')!=expected_root+'/compose.yaml' or labels.get('com.docker.compose.service')!=ref['service']:
            raise RuntimeError('OWNERSHIP_MISMATCH: Compose project or service changed')
    elif ref['source_kind']=='management':
        allowed={str((workspace/'dateninfrastruktur-admin/.runtime'/p).resolve()) for p in LEGACY_STATES}
        state=pathlib.Path(ref['state_ref']['path'])
        if not state.resolve().is_relative_to((workspace/'dateninfrastruktur-admin/.runtime').resolve()) or str(state.resolve()) not in allowed or digest(state)!=ref['state_ref']['sha256']:raise RuntimeError('SOURCE_CHANGED: private state binding changed')
        value=json.loads(state.read_text());ids=set(value.get('containers',[]))|set(value.get('services',{}).values())|{value.get('container'),value.get('database')}
        if actual['id'] not in ids:raise RuntimeError('OWNERSHIP_MISMATCH: container not bound by private state')
        if value.get('id'):
            if labels.get('di.identity')!=value['id'] and not (value.get('database')==actual['id'] and labels.get('di.phase')=='MA-B'):raise RuntimeError('OWNERSHIP_MISMATCH: management label')
        elif labels.get('di.phase')!='MA-B' or actual['name']!='/'+value.get('name',''):raise RuntimeError('OWNERSHIP_MISMATCH: management DB binding')
    else:raise RuntimeError('OWNERSHIP_MISMATCH: unselected source kind')
    return actual['id']
def with_verified_resource(ref,scope,operation):return operation(verify_ownership(ref,scope))
def discover_sources(workspace=WORKSPACE,project='dateninfrastruktur-dev-stack'):
    workspace=pathlib.Path(workspace).resolve();states=state_refs(workspace);scope={'workspace':str(workspace),'foundation_project':project}
    inventory={'schema_version':1,'mode':'inventory','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':scope,'repositories':[],'source_refs':[],'unselected':[],'state_refs':states,'volumes':[],'foundation_env_ref':None}
    env_file=workspace/'dateninfrastruktur-dev-stack/.env'
    if env_file.is_file():inventory['foundation_env_ref']={'path':str(env_file),'sha256':digest(env_file),'fields':re.findall(r'^([A-Z][A-Z0-9_]*)=',env_file.read_text(),re.M)}
    for name in REPOS:
        repo=workspace/name
        inventory['repositories'].append({'name':name,'head':command(['git','-C',str(repo),'rev-parse','HEAD']).strip(),'dirty':command(['git','-C',str(repo),'status','--porcelain']),'remotes':command(['git','-C',str(repo),'remote','-v'])})
    for cid in command(['docker','ps','-aq','--no-trunc']).split():
        raw=inspect(cid);ref=reference(raw);labels=ref['labels']
        if labels.get('com.docker.compose.project')==project:
            ref.update(source_kind='foundation',service=labels.get('com.docker.compose.service'))
        else:
            matches=[s for s in states if cid in s['ids']]
            if not matches:inventory['unselected'].append({'id':cid,'name':ref['name'],'state':ref['state']});continue
            # A DB can appear in both paired state files; the connection binding is preferred.
            selected=next((s for s in matches if s['path'].endswith('/connection.json')),matches[0]);ref.update(source_kind='management',state_ref=selected)
        verify_ownership(ref,scope,raw);inventory['source_refs'].append(ref)
    for name in command(['docker','volume','ls','-q']).split():
        value=json.loads(command(['docker','volume','inspect',name]))[0]
        used=[r['id'] for r in inventory['source_refs'] if any(m.get('Name')==name for m in r['mounts'])]
        if used:inventory['volumes'].append({'name':name,'labels':value.get('Labels') or {},'users':used,'driver':value['Driver']})
    return inventory
def database_facts(ref,scope):
    cid=verify_ownership(ref,scope)
    def sql(db,statement):return command(['docker','exec','-i',cid,'psql','-X','-U','postgres','-d',db,'-At','-v','ON_ERROR_STOP=1'],input='BEGIN READ ONLY;\n'+statement+'\nROLLBACK;').strip().splitlines()[1:-1]
    version=sql('postgres',"SELECT current_setting('server_version_num');")[0]
    databases=sql('postgres',"SELECT datname FROM pg_database WHERE NOT datistemplate ORDER BY datname;")
    facts={'server_version_num':int(version),'databases':{}}
    for db in databases:
        if db not in ['keycloak','superset','dateninfrastruktur_management']:continue
        facts['databases'][db]={'catalog':sql(db,"SELECT datcollate||'|'||datctype||'|'||pg_encoding_to_char(encoding) FROM pg_database WHERE datname=current_database();"),'extensions':sql(db,"SELECT extname||'|'||extversion FROM pg_extension ORDER BY extname;"),'relation_count':int(sql(db,"SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind='r' AND n.nspname NOT IN ('pg_catalog','information_schema');")[0])}
        if db=='dateninfrastruktur_management':
            facts['databases'][db]['counts']=sql(db,"SELECT 'dataset='||count(*) FROM di_management.dataset UNION ALL SELECT 'principal='||count(*) FROM di_management.principal UNION ALL SELECT 'grant='||count(*) FROM di_management.accessgrant UNION ALL SELECT 'decision='||count(*) FROM di_management.accessdecision UNION ALL SELECT 'audit='||count(*) FROM audit.row_change;")
            facts['databases'][db]['issuers']=sql(db,"SELECT DISTINCT aissuer FROM di_management.principal ORDER BY aissuer;")
    return facts
def build_plan(inventory):
    sources=inventory['source_refs'];management=[r for r in sources if r['source_kind']=='management' and r.get('database',{}).get('databases',{}).get('dateninfrastruktur_management')]
    return {'schema_version':1,'mode':'migrate','status':'INVENTORIED','scope':inventory['scope'],'source_refs':sources,'database_mapping':{'keycloak':'Foundation PostgreSQL → canonical postgres/keycloak','superset':'Foundation PostgreSQL → canonical postgres/superset','dateninfrastruktur_management':[r['id'] for r in management]},'source_choice':'UNIQUE_MANAGEMENT_SOURCE' if len(management)==1 else 'BLOCKED_SOURCE_SELECTION','identity_mapping_status':'PENDING_OFFLINE_MA_KEYCLOAK_EXPORT_AND_UUID_VERIFICATION','target_project':inventory['scope']['foundation_project'],'retire_allowlist':[r['id'] for r in sources if r['source_kind']=='management'],'volume_policy':'retain all source volumes; new named logical-restore PG target; retain Foundation Garage/Jenkins/ClickHouse/Superset volumes','cutover_authorized_now':False,'secret_refs':{'management':inventory['state_refs'],'foundation':inventory.get('foundation_env_ref')}}
def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['inventory','plan','prepare','backup','restore','verify','rollback']);p.add_argument('--output');p.add_argument('--inventory');p.add_argument('--project',default='dateninfrastruktur-dev-stack');p.add_argument('--plan');p.add_argument('--target-project',default='dateninfrastruktur');p.add_argument('--apply',action='store_true');a=p.parse_args()
    if a.action in ['backup','restore','verify','rollback']:
        if not a.plan:raise RuntimeError('Explicit private migration plan required')
        if a.action!='verify' and not a.apply:raise RuntimeError('Explicit --apply required for migration operation')
        from migration_coordinator import Migration
        operation=Migration(a.plan);getattr(operation,a.action)();return
    if not a.output:raise RuntimeError('Explicit private output required')
    output=pathlib.Path(a.output).resolve()
    if not output.is_relative_to((STACK/'.runtime').resolve()) or output.suffix!='.json':raise RuntimeError('Output must be a private .runtime JSON file')
    if a.action=='prepare':
        if not a.inventory:raise RuntimeError('Explicit private inventory required')
        from migration_prepare import prepare
        value=prepare(json.loads(pathlib.Path(a.inventory).read_text()),output,a.target_project)
        print('Private migration plan prepared; original services/volumes unchanged; target not activated');return
    if a.action=='inventory':
        value=discover_sources(project=a.project)
        for ref in value['source_refs']:
            if ref.get('service')=='postgres' or ref['labels'].get('di.phase')=='MA-B':ref['database']=database_facts(ref,value['scope'])
    else:
        if not a.inventory:raise RuntimeError('Explicit private inventory required')
        value=build_plan(json.loads(pathlib.Path(a.inventory).read_text()))
    private_write(a.output,value);print('Private '+a.action+' written. No runtime resource mutated; no credentials emitted.')
if __name__=='__main__':main()
