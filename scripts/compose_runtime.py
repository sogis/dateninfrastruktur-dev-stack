"""One explicit Compose context. No secondary container lifecycle."""
import json,os,pathlib,re,secrets,subprocess
from ingestion_clients import extend_fresh
ROOT=pathlib.Path(__file__).resolve().parents[1]
ADMIN_DEV_OVERLAY = ROOT / 'compose.admin-dev.yaml'
ADMIN_DEV_MARKER = 'admin-dev.json'
def encode_env(value):
    # Docker dotenv double quotes plus escaped dollars; JSON covers quotes,
    # backslashes and line breaks. No shell evaluation is involved.
    return json.dumps(str(value),ensure_ascii=False).replace('$','$$')
def read_env(path):
    path=pathlib.Path(path).resolve();source=path.read_text()
    keys=list(dict.fromkeys(re.findall(r'^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=',source,re.M)))
    if not keys:raise RuntimeError('Empty private configuration')
    model={'services':{'env-reader':{'image':'scratch','environment':{k:'${'+k+'}' for k in keys}}}}
    env={k:os.environ[k] for k in ['PATH','HOME','DOCKER_CONFIG'] if k in os.environ}
    result=subprocess.run(['docker','compose','--env-file',str(path),'--file','-','config','--format','json'],input=json.dumps(model),env=env,cwd=ROOT,capture_output=True,text=True)
    if result.returncode:raise RuntimeError('Invalid private dotenv configuration; details withheld')
    # Compose's config serializer escapes dollars again for a reusable model.
    return {k:v.replace('$$','$') for k,v in json.loads(result.stdout)['services']['env-reader']['environment'].items()}
def write_private(path,text):
    path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.parent.chmod(0o700)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w') as f:f.write(text)
    path.chmod(0o600)
class ComposeContext:
    def __init__(self,env_file):
        self.env_file=pathlib.Path(env_file).resolve()
        if not self.env_file.is_relative_to((ROOT/'.runtime').resolve()):raise RuntimeError('Compose environment must be inside this checkout runtime')
        self.values=read_env(self.env_file);self.project=self.values['COMPOSE_PROJECT_NAME'];self.runtime=pathlib.Path(self.values['RUNTIME_DIR']).resolve()
        if not re.fullmatch('[a-z][a-z0-9-]{3,62}',self.project) or not self.runtime.is_relative_to((ROOT/'.runtime').resolve()) or self.env_file.parent!=self.runtime:raise RuntimeError('Compose project/runtime binding mismatch')
        self.command_overrides={}
        self.base=['docker','compose','--project-name',self.project,'--env-file',str(self.env_file),'--file',str(ROOT/'compose.yaml')]
    def redact(self,value):
        for k,v in self.values.items():
            if v and re.search('PASSWORD|SECRET|TOKEN|ACCESS_KEY',k):value=value.replace(v,'[REDACTED]')
        return value
    def verify_project(self):
        ids = subprocess.check_output(
            ['docker', 'ps', '-aq', '--filter', 'label=com.docker.compose.project=' + self.project],
            text=True,
        ).split()
        containers = json.loads(subprocess.check_output(['docker', 'inspect', *ids], text=True)) if ids else []
        compose_file = str(ROOT / 'compose.yaml')
        for container in containers:
            labels = container['Config'].get('Labels') or {}
            files = labels.get('com.docker.compose.project.config_files')
            development_admin = (
                files == f'{compose_file},{ADMIN_DEV_OVERLAY}'
                and labels.get('com.docker.compose.service') == 'admin'
                and (self.runtime / ADMIN_DEV_MARKER).is_file()
            )
            if (labels.get('di.instance') != self.values['INSTANCE_ID']
                    or labels.get('com.docker.compose.project.working_dir') != str(ROOT)
                    or (files != compose_file and not development_admin)):
                raise RuntimeError('OWNERSHIP_MISMATCH: existing project requires planned migration')
        return containers

    def command(self,args,input=None,check=True,*,admin_dev=False,overrides=None):
        if any(arg in ['up','down','stop','restart','run','exec','rm'] for arg in args):
            self.verify_project()
        base = self.base + (['--file', str(ADMIN_DEV_OVERLAY)] if admin_dev else [])
        env={k:os.environ[k] for k in ['PATH','HOME','DOCKER_HOST','DOCKER_CONTEXT','DOCKER_CONFIG','TMPDIR','SSH_AUTH_SOCK'] if k in os.environ};env.update(self.values);env.update(self.command_overrides)
        env.update(DI_TEST_HOST_UID=str(os.getuid()),DI_TEST_HOST_GID=str(os.getgid()))
        env.update(overrides or {})
        p=subprocess.run(base+list(args),cwd=ROOT,env=env,input=input,capture_output=True,text=True)
        if p.returncode and check:raise RuntimeError(self.redact((p.stdout+p.stderr)[-8000:]))
        return p
def init_context(project,ports=None,test_fixture=False):
    if not re.fullmatch('[a-z][a-z0-9-]{3,62}',project):raise RuntimeError('Invalid project')
    runtime=ROOT/'.runtime'/project;env_file=runtime/'runtime.env'
    if env_file.exists():return ComposeContext(env_file)
    # Fresh mode never adopts an existing running foundation under its default name.
    existing=subprocess.check_output(['docker','ps','-aq','--filter','label=com.docker.compose.project='+project],text=True).strip()
    if existing:raise RuntimeError('Existing project requires explicit planned migration, never fresh init')
    values={'COMPOSE_PROJECT_NAME':project,'INSTANCE_ID':secrets.token_hex(16),'RUNTIME_DIR':str(runtime),'GATEWAY_PORT':'18081','KEYCLOAK_PORT':'18080','SUPERSET_PORT':'18088','CLICKHOUSE_HTTP_PORT':'18123','CLICKHOUSE_NATIVE_PORT':'19000','POSTGRES_VOLUME':project+'_postgres','GARAGE_META_VOLUME':project+'_garage-meta','GARAGE_DATA_VOLUME':project+'_garage-data','JENKINS_VOLUME':project+'_jenkins-home','CLICKHOUSE_DATA_VOLUME':project+'_clickhouse-data','CLICKHOUSE_LOG_VOLUME':project+'_clickhouse-logs','SUPERSET_VOLUME':project+'_superset-home','DI_TEST_FIXTURE':'true' if test_fixture else 'false','CLICKHOUSE_ADMIN_USER':'ch_admin','CLICKHOUSE_SUPERSET_USER':'superset_reader','THEMEN_REPO_DIR':str(ROOT.parent/'dateninfrastruktur-themenrepo')}
    if ports:values.update({k:str(v) for k,v in ports.items()})
    for key in ['POSTGRES_ADMIN_PASSWORD','KEYCLOAK_DB_PASSWORD','KEYCLOAK_ADMIN_PASSWORD','KEYCLOAK_DEMO_PASSWORD','SUPERSET_DB_PASSWORD','SUPERSET_ADMIN_PASSWORD','SUPERSET_SECRET_KEY','CLICKHOUSE_DEFAULT_PASSWORD','CLICKHOUSE_ADMIN_PASSWORD','CLICKHOUSE_TEST_READER_PASSWORD','CLICKHOUSE_SUPERSET_READER_PASSWORD','JENKINS_ADMIN_PASSWORD','DI_WRITER_PASSWORD','DI_AUTHZ_PASSWORD','DI_PUBLIC_PASSWORD','DI_AUDIT_READER_PASSWORD','DI_GATEWAY_SECRET','DI_OIDC_CLIENT_SECRET','DI_SESSION_SECRET','DI_INGESTION_PLUGIN_SECRET','DI_INGESTION_LEASE_SECRET','DI_JENKINS_OIDC_CLIENT_SECRET','DI_INGESTION_EXECUTOR_CLIENT_SECRET','DI_CH_LOADER_PASSWORD','DI_CH_PROJECTOR_PASSWORD','DI_CH_READER_PASSWORD']:values[key]=secrets.token_hex(32)
    values.update(DI_STORAGE_BUCKET='ch.so.daten',DI_STORAGE_ENDPOINT='http://garage:3900',DI_STORAGE_REGION='garage')
    for kind in ['WRITER','READER']:
        values['DI_STORAGE_'+kind+'_ACCESS_KEY']='';values['DI_STORAGE_'+kind+'_SECRET_KEY']=''
    for key,tag in [('ADMIN_IMAGE','admin'),('TOOL_IMAGE','tools'),('TEST_TOOL_IMAGE','test-tools'),('POSTGRES_IMAGE','postgres'),('SODATA_IMAGE','sodata'),('SUPERSET_IMAGE','superset')]:values[key]='dateninfrastruktur-'+tag+':'+project
    # Placeholder until an explicit candidate build is bound by immutable ID.
    values['JENKINS_IMAGE']='dateninfrastruktur-jenkins:'+project
    write_private(env_file,''.join(k+'='+encode_env(v)+'\n' for k,v in values.items()))
    context=ComposeContext(env_file);render(context);return context
def render(context):
    v=context.values;r=context.runtime
    garage=(ROOT/'services/garage/garage.toml.template').read_text()
    for key in ['RPC_SECRET','ADMIN_TOKEN','METRICS_TOKEN']:garage=garage.replace('__'+key+'__',secrets.token_hex(32))
    if not (r/'garage.toml').exists():write_private(r/'garage.toml',garage)
    def storage_conf(kind):
        key=v.get('DI_STORAGE_'+kind+'_ACCESS_KEY');secret=v.get('DI_STORAGE_'+kind+'_SECRET_KEY')
        if not key or not secret:raise RuntimeError('Explicit dedicated storage '+kind.lower()+' credential missing; run reviewed setup')
        return '\n'.join(['[storage]','type = s3','provider = Other','env_auth = false','access_key_id = '+key,'secret_access_key = '+secret,'endpoint = http://garage:3900','region = garage','force_path_style = true','no_check_bucket = true',''])
    # Fresh init precedes explicit Garage setup. Never render an empty or more privileged fallback.
    if v.get('DI_STORAGE_READER_ACCESS_KEY') or v.get('DI_STORAGE_READER_SECRET_KEY'):
        write_private(r/'origin.conf',storage_conf('READER'))
    if v.get('DI_STORAGE_WRITER_ACCESS_KEY') or v.get('DI_STORAGE_WRITER_SECRET_KEY'):
        write_private(r/'operator.conf',storage_conf('WRITER'))
    realm=json.loads((ROOT/'services/keycloak/realm-template.json').read_text())
    if v['DI_TEST_FIXTURE']!='true':realm['users']=[]
    for user in realm['users']:user['credentials'][0]['value']=v['KEYCLOAK_DEMO_PASSWORD']
    audience={'name':'management-api audience','protocol':'openid-connect','protocolMapper':'oidc-audience-mapper','config':{'included.custom.audience':'management-api','access.token.claim':'true','id.token.claim':'false'}}
    realm['clients']=[{'clientId':'management-gateway','enabled':True,'protocol':'openid-connect','publicClient':False,'secret':v['DI_OIDC_CLIENT_SECRET'],'standardFlowEnabled':True,'directAccessGrantsEnabled':False,'redirectUris':['http://localhost:'+v['GATEWAY_PORT']+'/oidc/callback'],'webOrigins':['http://localhost:'+v['GATEWAY_PORT']],'protocolMappers':[audience]}]
    if v['DI_TEST_FIXTURE']=='true':realm['clients'].append({'clientId':'management-test','enabled':True,'protocol':'openid-connect','publicClient':True,'standardFlowEnabled':False,'directAccessGrantsEnabled':True,'protocolMappers':[audience]})
    if not (r/'realm-initial.json').exists():
        extend_fresh(realm,v)
        write_private(r/'realm-initial.json',json.dumps(realm,indent=2))
    # Non-root Keycloak reads the bind-mounted initial definition; parent remains0700.
    (r/'realm-initial.json').chmod(0o644)
    template=json.loads((ROOT/'services/apisix/routes.template.json').read_text())
    def substitute(value):
        if isinstance(value,dict):return {k:substitute(x) for k,x in value.items()}
        if isinstance(value,list):return [substitute(x) for x in value]
        if isinstance(value,str):
            for k,x in v.items():value=value.replace('${'+k+'}',x)
        return value
    write_private(r/'apisix.yaml',json.dumps(substitute(template),indent=2)+'\n#END\n');(r/'apisix.yaml').chmod(0o644)

def update_context(context,updates):
    values={**context.values,**updates}
    write_private(context.env_file,''.join(k+'='+encode_env(v)+'\n' for k,v in values.items()))
    return ComposeContext(context.env_file)

def setup_context(context):
    context.command(['up','--no-build','-d','--wait','--wait-timeout','240','postgres','garage','clickhouse'])
    for service in ['postgres-init','management-setup','garage-setup','clickhouse-init','clickhouse-ingestion-setup']:
        context.command(['--profile','setup','run','--rm','--no-deps',service])
        if service=='garage-setup':
            context.values=read_env(context.env_file)
            render(context)
    print('Explicit setup complete; no application demo seed')
