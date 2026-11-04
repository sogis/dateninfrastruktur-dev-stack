"""Select the already inventoried local sources and retain actual configuration privately."""
import json,pathlib,uuid
from consolidation import STACK,WORKSPACE,verify_ownership,private_write,digest,inspect
from migration_binding import artifact_hashes,runtime_hashes
from compose_runtime import ComposeContext,init_context,read_env,update_context,render,write_private

def environment(ref,scope):
    value=inspect(verify_ownership(ref,scope));return dict(item.split('=',1) for item in value['Config'].get('Env',[]) if '=' in item)
def mounted_volume(ref,destination):
    values=[m['Name'] for m in ref['mounts'] if m['Type']=='volume' and m['Destination']==destination]
    if len(values)!=1:raise RuntimeError('OWNERSHIP_MISMATCH: expected exactly one persistent source volume')
    return values[0]
def bound_file(ref,destination):
    values=[m['Source'] for m in ref['mounts'] if m['Type']=='bind' and m['Destination']==destination]
    if len(values)!=1 or not pathlib.Path(values[0]).is_file():raise RuntimeError('OWNERSHIP_MISMATCH: missing source configuration bind')
    return pathlib.Path(values[0])

def prepare(inventory,output,target_project='dateninfrastruktur'):
    output=pathlib.Path(output).resolve()
    if not output.is_relative_to((STACK/'.runtime').resolve()):raise RuntimeError('Private migration plan must remain under STACK/.runtime')
    if output.exists():
        plan=json.loads(output.read_text())
        if plan['target_project']!=target_project:raise RuntimeError('OWNERSHIP_MISMATCH: existing operation target')
        for ref in plan['source_refs']:verify_ownership(ref,plan['scope'])
        return plan
    scope=inventory['scope'];refs=inventory['source_refs']
    if pathlib.Path(scope['workspace']).resolve()!=WORKSPACE.resolve():raise RuntimeError('OWNERSHIP_MISMATCH: inventory workspace')
    for ref in refs:verify_ownership(ref,scope)
    foundation={r['service']:r for r in refs if r['source_kind']=='foundation'}
    required={'postgres','keycloak','garage','jenkins','clickhouse','superset','sodata','downloads','s3-browser'}
    if set(foundation)!=required:raise RuntimeError('SOURCE_SELECTION_CONFLICT: Foundation service set changed; re-inventory explicitly')
    pg=[r for r in refs if r['source_kind']=='management' and r['labels'].get('di.phase')=='MA-B']
    if len(pg)!=1:raise RuntimeError('SOURCE_SELECTION_CONFLICT: need exactly one explicitly bound management database')
    candidates=[]
    for state in inventory['state_refs']:
        if not state.get('runtime_id'):continue
        value=json.loads(pathlib.Path(state['path']).read_text())
        if value.get('database')==pg[0]['id']:candidates.append((state,value))
    if len(candidates)!=1:raise RuntimeError('SOURCE_SELECTION_CONFLICT: current identity/runtime binding is not unique')
    state_ref,managed=candidates[0];by_id={r['id']:r for r in refs}
    if not {'keycloak','garage'}.issubset(managed['services']):raise RuntimeError('SOURCE_SELECTION_CONFLICT: selected MA runtime lacks required services')
    sources={'foundation_pg':foundation['postgres'],'management_pg':pg[0],'management_keycloak':by_id[managed['services']['keycloak']],'management_garage':by_id[managed['services']['garage']]}
    path=pathlib.Path(state_ref['path']);roles_file=path.parent.parent/'database/roles.json'
    if not roles_file.is_file():raise RuntimeError('CREDENTIAL_REFERENCE_MISSING: management roles')
    roles=json.loads(roles_file.read_text());ef=inventory['foundation_env_ref']
    if not ef or digest(ef['path'])!=ef['sha256']:raise RuntimeError('SOURCE_CHANGED: selected Foundation environment reference')
    values=read_env(ef['path']);actual={service:environment(foundation[service],scope) for service in ['keycloak','superset','garage','jenkins','clickhouse']}
    # Actual running service values take precedence over possibly stale .env values.
    for service in ['superset','garage','jenkins','clickhouse']:
        for key,value in actual[service].items():
            if key in values:values[key]=value
    for old,new in [('KC_DB_PASSWORD','KEYCLOAK_DB_PASSWORD'),('KC_BOOTSTRAP_ADMIN_PASSWORD','KEYCLOAK_ADMIN_PASSWORD')]:
        if actual['keycloak'].get(old):values[new]=actual['keycloak'][old]
    needed=['KEYCLOAK_DB_PASSWORD','KEYCLOAK_ADMIN_PASSWORD','KEYCLOAK_DEMO_PASSWORD','SUPERSET_DB_PASSWORD','SUPERSET_ADMIN_PASSWORD','SUPERSET_SECRET_KEY','CLICKHOUSE_DEFAULT_PASSWORD','CLICKHOUSE_ADMIN_PASSWORD','CLICKHOUSE_TEST_READER_PASSWORD','CLICKHOUSE_SUPERSET_READER_PASSWORD','JENKINS_ADMIN_PASSWORD','GARAGE_DEFAULT_ACCESS_KEY','GARAGE_DEFAULT_SECRET_KEY']
    if any(not values.get(k) for k in needed) or any(not roles.get(r) for r in ['di_writer','di_authz','di_public','di_audit_reader','di_migrator']):raise RuntimeError('CREDENTIAL_REFERENCE_MISSING: selected application configuration')
    context=init_context(target_project)
    updates={k:values[k] for k in needed}
    updates.update({r.upper()+'_PASSWORD':v for r,v in roles.items() if r in ['di_writer','di_authz','di_public','di_audit_reader','di_migrator']})
    updates.update({'DI_OIDC_CLIENT_SECRET':managed['clientSecret'],'DI_SESSION_SECRET':managed['sessionSecret'],'DI_GATEWAY_SECRET':managed['gatewaySecret'],'GARAGE_ORIGIN_ACCESS_KEY':managed['originKey'],'GARAGE_ORIGIN_SECRET_KEY':managed['originSecret'],'GARAGE_MANAGED_ACCESS_KEY':managed['storageKey'],'GARAGE_MANAGED_SECRET_KEY':managed['storageSecret'],'MIGRATION_SOURCE_NETWORK':managed['network'],'MIGRATION_KEYCLOAK_IMAGE':sources['management_keycloak']['image_id'],'KEYCLOAK_IMAGE':foundation['keycloak']['image_id'],'GARAGE_IMAGE':foundation['garage']['image_id'],'CLICKHOUSE_IMAGE':foundation['clickhouse']['image_id'],'JENKINS_IMAGE':foundation['jenkins']['image_id'],'DI_MIGRATION_IMPORT_KEYS':'true','GARAGE_VOLUMES_EXTERNAL':'true','CLICKHOUSE_VOLUMES_EXTERNAL':'true','SUPERSET_VOLUME_EXTERNAL':'true','JENKINS_VOLUME_EXTERNAL':'true'})
    for key in ['GATEWAY_PORT','KEYCLOAK_PORT','SUPERSET_PORT','CLICKHOUSE_HTTP_PORT','CLICKHOUSE_NATIVE_PORT']:
        if key in values:updates[key]=values[key]
    for key,service,destination in [('GARAGE_META_VOLUME','garage','/var/lib/garage/meta'),('GARAGE_DATA_VOLUME','garage','/var/lib/garage/data'),('JENKINS_VOLUME','jenkins','/var/jenkins_home'),('CLICKHOUSE_DATA_VOLUME','clickhouse','/var/lib/clickhouse'),('CLICKHOUSE_LOG_VOLUME','clickhouse','/var/log/clickhouse-server'),('SUPERSET_VOLUME','superset','/app/superset_home')]:updates[key]=mounted_volume(foundation[service],destination)
    context=update_context(context,updates)
    if context.values['POSTGRES_VOLUME'] in {m.get('Name') for r in [foundation['postgres'],pg[0]] for m in r['mounts']}:raise RuntimeError('OWNERSHIP_MISMATCH: logical restore must use a NEW PostgreSQL volume')
    garage_config=bound_file(foundation['garage'],'/etc/garage.toml');write_private(context.runtime/'garage.toml',garage_config.read_text());render(context)
    plan={'schema_version':1,'operation_id':str(uuid.uuid4()),'mode':'migrate','status':'INVENTORIED','scope':scope,'source_refs':refs,'sources':sources,'source_states':[{'ref':r,'running':inspect(r['id'])['State']['Running'],'restart':r['restart']} for r in refs],'target_project':context.project,'target_env':str(context.env_file),'target_instance':context.values['INSTANCE_ID'],'target_env_sha256':digest(context.env_file),'target_artifacts':artifact_hashes(),'target_runtime_files':runtime_hashes(context),'source_old_issuer':managed['keycloak']+'/realms/dateninfrastruktur','target_issuer':'http://localhost:'+context.values['KEYCLOAK_PORT']+'/realms/dateninfrastruktur','retire_allowlist':[r['id'] for r in refs],'retained_volumes':sorted({m['Name'] for r in refs for m in r['mounts'] if m['Type']=='volume'}),'secret_refs':[ef,{'path':str(roles_file),'sha256':digest(roles_file)},state_ref],'source_storage':{'path':state_ref['path'],'sha256':state_ref['sha256'],'format':'json','access_field':'storageKey','secret_field':'storageSecret'},'foundation_garage_config':{'path':str(garage_config),'sha256':digest(garage_config)},'identity_policy':'Exact existing UUID only; Foundation password credentials; current selected MA profile; Foundation master/control-plane identity retained; old MA control-plane state kept in complete H2 backup','live_status':'LOCAL_CUTOVER_PENDING'}
    private_write(output,plan);private_write(context.runtime/'migration/source-inspect.json',{r['id']:inspect(r['id']) for r in refs})
    return plan
