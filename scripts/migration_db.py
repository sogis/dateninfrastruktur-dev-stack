"""Logical PostgreSQL migration. Source IDs are rechecked before every access.
Archives and row contents never leave private paths; no host PostgreSQL client.
"""
import hashlib,json,os,pathlib,re,subprocess
from consolidation import reference,verify_ownership,private_write,digest,inspect
from compose_runtime import ComposeContext,ROOT,write_private
DATABASES=['keycloak','superset','dateninfrastruktur_management']
ROLE_SETS={'foundation':['keycloak','superset'],'management':['di_owner','di_audit_owner','di_migrator','di_writer','di_authz','di_public','di_audit_reader']}
def ident(value):
    if not re.fullmatch('[a-z_][a-z0-9_]*',value):raise RuntimeError('Unsafe database identifier')
    return '"'+value+'"'
def literal(value):return "'"+str(value).replace("'","''")+"'"
def private_bytes(path,data):
    path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.parent.chmod(0o700)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'wb') as f:f.write(data)
    path.chmod(0o600)
def verify_source(ref,scope):
    if ref.get('source_kind')!='compose-fixture':return verify_ownership(ref,scope)
    context=ComposeContext(ref['context']['path'])
    if not context.project.startswith('maf-') or digest(context.env_file)!=ref['context']['sha256']:raise RuntimeError('SOURCE_CHANGED: fixture context')
    obj=inspect(ref['id']);actual=reference(obj)
    if any(actual[k]!=ref[k] for k in ['id','name','image_id','mounts']):raise RuntimeError('OWNERSHIP_MISMATCH: fixture source identity')
    labels=actual['labels']
    if labels.get('di.instance')!=context.values['INSTANCE_ID'] or labels.get('com.docker.compose.project')!=context.project or labels.get('com.docker.compose.project.config_files')!=str(ROOT/'compose.yaml') or labels.get('com.docker.compose.project.working_dir')!=str(ROOT) or labels.get('com.docker.compose.service')!=ref['service']:raise RuntimeError('OWNERSHIP_MISMATCH: fixture source labels')
    return ref['id']
def source_call(plan,ref,args,data=None):
    cid=verify_source(ref,plan['scope']);p=subprocess.run(['docker','exec','-i',cid]+args,input=data,capture_output=True)
    if p.returncode:
        private_write(ROOT/'.runtime/migration-source-error.json',{'command':args,'stderr':p.stderr.decode(errors='replace'),'query':data.decode(errors='replace') if data else None})
        raise RuntimeError('SOURCE_READ_FAILED: private diagnostic retained; details withheld')
    return p.stdout
def source_sql(plan,ref,db,query):
    return source_call(plan,ref,['psql','-X','-q','-At','-U','postgres','-d',db,'-v','ON_ERROR_STOP=1'],query.encode()).decode().strip()
def target_call(context,args,data=None):
    context.verify_project();env={k:os.environ[k] for k in ['PATH','HOME','DOCKER_HOST','DOCKER_CONTEXT','DOCKER_CONFIG','TMPDIR'] if k in os.environ};env.update(context.values)
    p=subprocess.run(context.base+list(args),cwd=ROOT,env=env,input=data,capture_output=True)
    if p.returncode:raise RuntimeError('RESTORE_FAILED: target command details withheld')
    return p.stdout
def target_sql(context,db,query):return target_call(context,['exec','-T','postgres','psql','-X','-q','-At','-U','postgres','-d',db,'-v','ON_ERROR_STOP=1'],query.encode()).decode().strip()
def row_hash_sql(query):
    return "SELECT encode(sha256(convert_to(coalesce(string_agg(to_jsonb(row_data)::text,E'\\n' ORDER BY to_jsonb(row_data)::text COLLATE \"C\"),''),'UTF8')),'hex') FROM ("+query.rstrip(';')+") row_data"
def snapshot(execute,db):
    catalog=json.loads(execute(db,"SELECT json_build_object('tables',(SELECT coalesce(json_agg(json_build_array(n.nspname,c.relname) ORDER BY n.nspname,c.relname),'[]') FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind='r' AND n.nspname NOT IN ('pg_catalog','information_schema') AND n.nspname NOT LIKE 'pg_toast%'),'sequences',(SELECT coalesce(json_agg(json_build_array(schemaname,sequencename) ORDER BY schemaname,sequencename),'[]') FROM pg_sequences WHERE schemaname NOT IN ('pg_catalog','information_schema')));"))
    result={'tables':{},'sequences':{},'security':{}}
    security={
     'relations':"SELECT n.nspname,c.relname,c.relkind,pg_get_userbyid(c.relowner),(SELECT coalesce(string_agg(CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END||':'||a.privilege_type||':'||a.is_grantable::text||':'||pg_get_userbyid(a.grantor),',' ORDER BY CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END,a.privilege_type),'') FROM aclexplode(coalesce(c.relacl,acldefault(CASE WHEN c.relkind='S' THEN 'S'::\"char\" ELSE 'r'::\"char\" END,c.relowner))) a),c.relrowsecurity,c.relforcerowsecurity FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname NOT IN ('pg_catalog','information_schema') AND n.nspname NOT LIKE 'pg_toast%' ORDER BY 1,2;",
     'schemas':"SELECT nspname,pg_get_userbyid(nspowner),coalesce(nspacl::text,'') FROM pg_namespace WHERE nspname NOT IN ('pg_catalog','information_schema') AND nspname NOT LIKE 'pg_toast%' AND nspname NOT LIKE 'pg_temp%' ORDER BY 1;",
     'functions':"SELECT n.nspname,p.proname,pg_get_function_identity_arguments(p.oid),pg_get_userbyid(p.proowner),p.prosecdef,(SELECT coalesce(string_agg(CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END||':'||a.privilege_type||':'||a.is_grantable::text||':'||pg_get_userbyid(a.grantor),',' ORDER BY CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END,a.privilege_type),'') FROM aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname NOT IN ('pg_catalog','information_schema') ORDER BY 1,2,3;",
     'triggers':"SELECT n.nspname,c.relname,t.tgname,t.tgenabled,pg_get_triggerdef(t.oid) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE NOT t.tgisinternal ORDER BY 1,2,3;",
     'extensions':"SELECT extname,extversion FROM pg_extension ORDER BY 1;",
     'database':"SELECT pg_get_userbyid(datdba),datcollate,datctype,pg_encoding_to_char(encoding),coalesce((SELECT string_agg(CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END||':'||a.privilege_type||':'||a.is_grantable::text,',' ORDER BY CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END,a.privilege_type) FROM aclexplode(coalesce(datacl,acldefault('d',datdba))) a),'') FROM pg_database WHERE datname=current_database();"}
    statements=["BEGIN READ ONLY; SET LOCAL timezone='UTC'; SET LOCAL datestyle='ISO, YMD';"]
    for schema,table in catalog['tables']:
        query=row_hash_sql('SELECT * FROM '+ident(schema)+'.'+ident(table))
        statements.append("SELECT json_build_array('tables',"+literal(schema+'.'+table)+",("+query+"));")
    for schema,name in catalog['sequences']:
        statements.append("SELECT json_build_array('sequences',"+literal(schema+'.'+name)+",last_value::text||'|'||is_called) FROM "+ident(schema)+'.'+ident(name)+';')
    for name,query in security.items():statements.append("SELECT json_build_array('security',"+literal(name)+",("+row_hash_sql(query)+"));")
    statements.append('ROLLBACK;')
    for line in execute(db,'\n'.join(statements)).splitlines():
        kind,key,value=json.loads(line);result[kind][key]=value
    return result
def source_snapshots(plan):
    return {db:snapshot(lambda name,q:source_sql(plan,plan['sources']['management_pg' if db=='dateninfrastruktur_management' else 'foundation_pg'],name,q),db) for db in DATABASES}
def role_checkpoint(execute,names):
    selected=','.join(literal(n) for n in names)
    queries={
      'roles':"SELECT rolname,rolsuper,rolinherit,rolcreaterole,rolcreatedb,rolcanlogin,rolreplication,rolconnlimit,rolpassword,rolvaliduntil,rolbypassrls FROM pg_authid WHERE rolname IN ("+selected+")",
      'memberships':"SELECT r.rolname,m.rolname,g.rolname,a.admin_option,a.inherit_option,a.set_option FROM pg_auth_members a JOIN pg_roles r ON r.oid=a.roleid JOIN pg_roles m ON m.oid=a.member JOIN pg_roles g ON g.oid=a.grantor WHERE m.rolname IN ("+selected+")",
      'settings':"SELECT r.rolname,coalesce(d.datname,''),s.setconfig FROM pg_db_role_setting s JOIN pg_roles r ON r.oid=s.setrole LEFT JOIN pg_database d ON d.oid=s.setdatabase WHERE r.rolname IN ("+selected+")"}
    return {kind:execute('postgres',row_hash_sql(query)+';') for kind,query in queries.items()}
def source_role_checkpoints(plan):
    return {kind:role_checkpoint(lambda db,q:source_sql(plan,plan['sources'][kind+'_pg'],db,q),names) for kind,names in ROLE_SETS.items()}
def extension_compatibility(execute,db):
    lock=json.loads((ROOT/'services/postgres/compatibility/bao-3.5.2-concavehull.json').read_text());signature=lock['signature']
    if execute(db,"SELECT to_regtype('public.geometry') IS NOT NULL;")!='t':return []
    if execute(db,'SELECT to_regprocedure('+literal(signature)+') IS NOT NULL;')!='t':return []
    definition=execute(db,'SELECT pg_get_functiondef('+literal(signature)+'::regprocedure);')
    evidence=execute(db,"SELECT pg_get_userbyid(p.proowner)||'|'||p.prosecdef||'|'||e.extname||'|'||e.extversion FROM pg_proc p JOIN pg_depend d ON d.classid='pg_proc'::regclass AND d.objid=p.oid AND d.deptype='e' JOIN pg_extension e ON e.oid=d.refobjid WHERE p.oid="+literal(signature)+'::regprocedure;')
    if hashlib.sha256(definition.encode()).hexdigest()!=lock['source_definition_sha256'] or evidence!='postgres|false|postgis|3.5.2':raise RuntimeError('VERIFICATION_FAILED: unapproved legacy PostGIS definition')
    return [{'id':'bao-3.5.2-concavehull','definition':definition,'definition_sha256':lock['source_definition_sha256']}]
def install_extension_compatibility(context,db,names):
    for item in names:
        name=item['id']
        if name!='bao-3.5.2-concavehull':raise RuntimeError('VERIFICATION_FAILED: unknown extension compatibility')
        root=ROOT/'services/postgres/compatibility';lock=json.loads((root/(name+'.json')).read_text());definition=item['definition'].strip()
        if hashlib.sha256(definition.encode()).hexdigest()!=lock['source_definition_sha256']:raise RuntimeError('VERIFICATION_FAILED: compatibility source hash')
        target_sql(context,db,"CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public VERSION '3.5.2';")
        if target_sql(context,db,'SELECT to_regprocedure('+literal(lock['signature'])+') IS NOT NULL;')=='t':raise RuntimeError('TARGET_NOT_EMPTY: compatibility function already present')
        target_sql(context,db,'BEGIN;'+definition+'; ALTER EXTENSION postgis ADD FUNCTION '+lock['signature']+';COMMIT;')
def backup_databases(plan,folder):
    folder=pathlib.Path(folder);folder.mkdir(parents=True,exist_ok=True);folder.chmod(0o700)
    before=source_snapshots(plan);globals_before=source_role_checkpoints(plan);metadata={'databases':{},'roles':{},'memberships':[],'database_role_settings':[],'role_checkpoints':globals_before}
    for kind in ['foundation','management']:
        ref=plan['sources'][kind+'_pg'];names=ROLE_SETS[kind];name_sql=','.join(literal(n) for n in names)
        roles=json.loads(source_sql(plan,ref,'postgres',"SELECT coalesce(json_agg(json_build_object('name',rolname,'login',rolcanlogin,'password',rolpassword,'super',rolsuper,'createdb',rolcreatedb,'createrole',rolcreaterole,'replication',rolreplication,'bypassrls',rolbypassrls,'inherit',rolinherit,'limit',rolconnlimit,'validuntil',rolvaliduntil,'config',(SELECT setconfig FROM pg_db_role_setting WHERE setrole=pg_authid.oid AND setdatabase=0)) ORDER BY rolname),'[]') FROM pg_authid WHERE rolname IN ("+name_sql+");"))
        if {r['name'] for r in roles}!=set(names) or any(r[x] for r in roles for x in ['super','createdb','createrole','replication','bypassrls']):raise RuntimeError('VERIFICATION_FAILED: missing or privileged application roles')
        metadata['roles'].update({r['name']:r for r in roles})
        members=json.loads(source_sql(plan,ref,'postgres',"SELECT coalesce(json_agg(json_build_object('role',r.rolname,'member',m.rolname,'admin',a.admin_option,'inherit',a.inherit_option,'set',a.set_option) ORDER BY r.rolname,m.rolname),'[]') FROM pg_auth_members a JOIN pg_roles r ON r.oid=a.roleid JOIN pg_roles m ON m.oid=a.member WHERE m.rolname IN ("+name_sql+");"))
        if any(m['role'] not in names or m['member'] not in names for m in members):raise RuntimeError('VERIFICATION_FAILED: unexpected role membership')
        metadata['memberships']+=members
        settings=json.loads(source_sql(plan,ref,'postgres',"SELECT coalesce(json_agg(json_build_object('role',r.rolname,'database',d.datname,'settings',s.setconfig) ORDER BY r.rolname,d.datname),'[]') FROM pg_db_role_setting s JOIN pg_roles r ON r.oid=s.setrole JOIN pg_database d ON d.oid=s.setdatabase WHERE r.rolname IN ("+name_sql+") AND d.datname IN ('keycloak','superset','dateninfrastruktur_management');"))
        metadata['database_role_settings']+=settings
        private_bytes(folder/(kind+'-globals.sql'),source_call(plan,ref,['pg_dumpall','-U','postgres','--globals-only']))
    for db in DATABASES:
        ref=plan['sources']['management_pg' if db=='dateninfrastruktur_management' else 'foundation_pg']
        properties=json.loads(source_sql(plan,ref,db,"SELECT json_build_object('owner',pg_get_userbyid(datdba),'encoding',pg_encoding_to_char(encoding),'collate',datcollate,'ctype',datctype,'acl',(SELECT coalesce(json_agg(json_build_object('grantee',CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END,'type',a.privilege_type,'grantable',a.is_grantable) ORDER BY CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END,a.privilege_type),'[]') FROM aclexplode(coalesce(datacl,acldefault('d',datdba))) a)) FROM pg_database WHERE datname=current_database();"))
        file=folder/(db+'.dump');private_bytes(file,source_call(plan,ref,['pg_dump','-U','postgres','-Fc','--dbname',db]));metadata['databases'][db]={**properties,'file':str(file),'sha256':digest(file),'snapshot':before[db],'extension_compatibility':extension_compatibility(lambda name,q:source_sql(plan,ref,name,q),db)}
    if source_snapshots(plan)!=before or source_role_checkpoints(plan)!=globals_before:raise RuntimeError('SOURCE_CHANGED: database or application roles changed during backup')
    private_write(folder/'database-manifest.json',metadata);return metadata

def verify_restored_roles(context,metadata):
    for kind,names in ROLE_SETS.items():
        if role_checkpoint(lambda db,q:target_sql(context,db,q),names)!=metadata['role_checkpoints'][kind]:raise RuntimeError('VERIFICATION_FAILED: restored role credentials/memberships/settings')

def restore_databases(context,metadata,journal):
    if journal.get('database_restored'):
        verify_restored_roles(context,metadata)
        for db in DATABASES:
            if snapshot(lambda name,q:target_sql(context,name,q),db)!=metadata['databases'][db]['snapshot']:raise RuntimeError('VERIFICATION_FAILED: changed restored target')
        return
    actual=target_sql(context,'postgres',"SELECT datname FROM pg_database WHERE NOT datistemplate AND datname<>'postgres';")
    if actual:
        if set(actual.splitlines())==set(DATABASES) and all(snapshot(lambda name,q:target_sql(context,name,q),db)==metadata['databases'][db]['snapshot'] for db in DATABASES):verify_restored_roles(context,metadata);journal['database_restored']=True;return
        raise RuntimeError('TARGET_NOT_EMPTY: no database will be dropped or overwritten')
    for db,m in metadata['databases'].items():
        if digest(m['file'])!=m['sha256']:raise RuntimeError('SOURCE_CHANGED: backup archive checksum')
        if m['encoding']!='UTF8' or m['owner'] not in ['postgres',*metadata['roles']]:raise RuntimeError('VERIFICATION_FAILED: database encoding/owner')
    roles=[]
    for name,r in metadata['roles'].items():
        if name not in sum(ROLE_SETS.values(),[]):raise RuntimeError('VERIFICATION_FAILED: unknown role')
        # A fresh target cluster must not contain application role conflicts.
        if target_sql(context,'postgres','SELECT count(*) FROM pg_roles WHERE rolname='+literal(name)+';')!='0':raise RuntimeError('TARGET_NOT_EMPTY: existing application role')
        roles.append('CREATE ROLE '+ident(name)+(' LOGIN' if r['login'] else ' NOLOGIN')+' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS'+(' INHERIT' if r['inherit'] else ' NOINHERIT')+' CONNECTION LIMIT '+str(r['limit'])+(' PASSWORD '+literal(r['password']) if r['password'] else '')+(' VALID UNTIL '+literal(r['validuntil']) if r['validuntil'] else '')+';')
        for setting in r['config'] or []:
            key,_,value=setting.partition('=')
            if not re.fullmatch('[a-z_.]+',key):raise RuntimeError('VERIFICATION_FAILED: role configuration')
            roles.append('ALTER ROLE '+ident(name)+' SET '+key+' TO '+literal(value)+';')
    for m in metadata['memberships']:
        for option in ['admin','inherit','set']:roles.append('GRANT '+ident(m['role'])+' TO '+ident(m['member'])+' WITH '+option.upper()+' '+str(m[option]).upper()+';')
    target_sql(context,'postgres','BEGIN;'+''.join(roles)+'COMMIT;')
    for db,m in metadata['databases'].items():
        target_sql(context,'postgres','CREATE DATABASE '+ident(db)+' OWNER '+ident(m['owner'])+' TEMPLATE template0 ENCODING '+literal(m['encoding'])+' LC_COLLATE '+literal(m['collate'])+' LC_CTYPE '+literal(m['ctype'])+';')
        install_extension_compatibility(context,db,m.get('extension_compatibility',[]))
        target_call(context,['exec','-T','postgres','pg_restore','-U','postgres','--exit-on-error','--single-transaction','--dbname',db],pathlib.Path(m['file']).read_bytes())
        acl=['REVOKE ALL ON DATABASE '+ident(db)+' FROM PUBLIC;']
        for role in ['postgres',*metadata['roles']]:acl.append('REVOKE ALL ON DATABASE '+ident(db)+' FROM '+ident(role)+';')
        for grant in m['acl']:
            if grant['grantee'] not in ['PUBLIC','postgres',*metadata['roles']] or grant['type'] not in ['CONNECT','CREATE','TEMPORARY']:raise RuntimeError('VERIFICATION_FAILED: database ACL outside controlled roles')
            acl.append('GRANT '+grant['type']+' ON DATABASE '+ident(db)+' TO '+('PUBLIC' if grant['grantee']=='PUBLIC' else ident(grant['grantee']))+(' WITH GRANT OPTION' if grant['grantable'] else '')+';')
        target_sql(context,db,''.join(acl))
        if snapshot(lambda name,q:target_sql(context,name,q),db)!=m['snapshot']:raise RuntimeError('VERIFICATION_FAILED: restored rows/security/sequences differ for '+db)
    for setting in metadata.get('database_role_settings',[]):
        for item in setting['settings']:
            key,_,value=item.partition('=')
            if not re.fullmatch('[a-z_.]+',key) or setting['role'] not in metadata['roles'] or setting['database'] not in DATABASES:raise RuntimeError('VERIFICATION_FAILED: role/database setting')
            target_sql(context,'postgres','ALTER ROLE '+ident(setting['role'])+' IN DATABASE '+ident(setting['database'])+' SET '+key+' TO '+literal(value)+';')
    verify_restored_roles(context,metadata)
    journal['database_restored']=True
