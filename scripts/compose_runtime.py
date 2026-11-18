"""Generate private configuration and check an explicit Compose context."""
import argparse,json,os,pathlib,re,secrets,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
ADMIN_DEV_OVERLAY = ROOT / 'compose.admin-dev.yaml'
ADMIN_DEV_MARKER = 'admin-dev.json'
VOLUMES = {
    'POSTGRES_VOLUME': ('postgres-data', None),
    'GARAGE_META_VOLUME': ('garage-meta', 'GARAGE_VOLUMES_EXTERNAL'),
    'GARAGE_DATA_VOLUME': ('garage-data', 'GARAGE_VOLUMES_EXTERNAL'),
    'JENKINS_VOLUME': ('jenkins-home', 'JENKINS_VOLUME_EXTERNAL'),
    'CLICKHOUSE_DATA_VOLUME': ('clickhouse-data', 'CLICKHOUSE_VOLUMES_EXTERNAL'),
    'CLICKHOUSE_LOG_VOLUME': ('clickhouse-logs', 'CLICKHOUSE_VOLUMES_EXTERNAL'),
    'SUPERSET_VOLUME': ('superset-home', 'SUPERSET_VOLUME_EXTERNAL'),
}
LOCAL_IMAGES = {
    'ADMIN_IMAGE': 'admin', 'SODATA_IMAGE': 'sodata', 'JENKINS_IMAGE': 'jenkins',
    'POSTGRES_IMAGE': 'postgres', 'SUPERSET_IMAGE': 'superset', 'TOOL_IMAGE': 'tools',
    'TEST_TOOL_IMAGE': 'test-tools',
}


def jenkins_image_id(reference):
    result = subprocess.run(
        ['docker', 'image', 'inspect', '--format',
         '{{.Id}} {{index .Config.Labels "io.dateninfrastruktur.gretl.version"}}', '--', reference],
        env=docker_env(), capture_output=True, text=True,
    )
    fields = result.stdout.split()
    if (result.returncode or len(fields) != 2 or not re.fullmatch(r'sha256:[0-9a-f]{64}', fields[0])
            or fields[1] != '6.0.0-SNAPSHOT'):
        raise RuntimeError('Expected a local Jenkins image with GRETL 6.0.0-SNAPSHOT')
    return fields[0]


def docker_env():
    return {key: os.environ[key] for key in (
        'PATH', 'HOME', 'DOCKER_HOST', 'DOCKER_CONTEXT', 'DOCKER_CONFIG', 'TMPDIR', 'SSH_AUTH_SOCK',
    ) if key in os.environ}


def docker_output(*args):
    result = subprocess.run(['docker', *args], env=docker_env(), capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('Docker resource check failed; check the selected Docker context')
    return result.stdout


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
        path = pathlib.Path(env_file).absolute()
        self.env_file = path.resolve()
        if ((ROOT / '.runtime').is_symlink() or path.is_symlink() or path.parent.is_symlink()
                or not self.env_file.is_file()
                or self.env_file.stat().st_mode & 0o077
                or self.env_file.parent.stat().st_mode & 0o077):
            raise RuntimeError('Select a private runtime.env in a private runtime directory')
        if not self.env_file.is_relative_to((ROOT/'.runtime').resolve()):raise RuntimeError('Compose environment must be inside this checkout runtime')
        self.values=read_env(self.env_file);self.project=self.values['COMPOSE_PROJECT_NAME'];self.runtime=pathlib.Path(self.values['RUNTIME_DIR']).resolve()
        if (not re.fullmatch('[a-z][a-z0-9-]{3,62}', self.project)
                or not self.runtime.is_relative_to(ROOT / '.runtime') or self.env_file.parent != self.runtime):
            raise RuntimeError('Compose project/runtime binding mismatch')
        if not self.values.get('INSTANCE_ID') or any(
                k.startswith('COMPOSE_') and k != 'COMPOSE_PROJECT_NAME' for k in self.values):
            raise RuntimeError('Invalid instance identity or Compose control variable')
        self.command_overrides={}
        self.base=['docker','compose','--project-name',self.project,'--env-file',str(self.env_file),'--file',str(ROOT/'compose.yaml')]
    def redact(self,value):
        for k,v in self.values.items():
            if v and re.search('PASSWORD|SECRET|TOKEN|ACCESS_KEY',k):value=value.replace(v,'[REDACTED]')
        return value
    def verify_project(self):
        ids = docker_output('ps', '-aq', '--filter', 'label=com.docker.compose.project=' + self.project).split()
        containers = json.loads(docker_output('inspect', *ids)) if ids else []
        compose_file = str(ROOT / 'compose.yaml')
        for container in containers:
            labels = container['Config'].get('Labels') or {}
            files = labels.get('com.docker.compose.project.config_files')
            development_admin = (
                files == f'{compose_file},{ADMIN_DEV_OVERLAY}'
                and labels.get('com.docker.compose.service') == 'admin'
                and (self.runtime / ADMIN_DEV_MARKER).is_file()
            )
            if (labels.get('com.docker.compose.project') != self.project
                    or labels.get('di.instance') != self.values['INSTANCE_ID']
                    or labels.get('com.docker.compose.project.working_dir') != str(ROOT)
                    or (files != compose_file and not development_admin)):
                raise RuntimeError('OWNERSHIP_MISMATCH: existing project requires planned migration')
        return containers

    def configured_jenkins_id(self):
        model = json.loads(self.command(['config', '--format', 'json', 'jenkins']).stdout)
        return jenkins_image_id(model['services']['jenkins']['image'])

    def volume_bindings(self):
        return {key: self.values[key] for key in VOLUMES}

    def has_setup(self):
        marker = self.runtime / 'setup-complete.json'
        if not marker.exists():
            return False
        state = json.loads(marker.read_text())
        if state.get('instance') != self.values['INSTANCE_ID'] or state.get('volumes') != self.volume_bindings():
            raise RuntimeError('OWNERSHIP_MISMATCH: setup instance or persistent volume mapping changed')
        return True

    def verify_resources(self, *, require_setup=False, require_volumes=False):
        containers = self.verify_project()
        retained = self.has_setup()
        if require_setup and not retained:
            raise RuntimeError('Explicit setup is required before normal start')
        if self.values.get('DI_STORAGE_BUCKET') != 'ch.so.daten':
            raise RuntimeError('Explicit reviewed storage cutover required')
        network = self.project + '_default'
        for identifier in docker_output('network', 'ls', '-q', '--filter', f'name=^{network}$').split():
            labels = json.loads(docker_output('network', 'inspect', identifier))[0].get('Labels') or {}
            if (labels.get('com.docker.compose.project') != self.project
                    or labels.get('com.docker.compose.network') != 'default'):
                raise RuntimeError('OWNERSHIP_MISMATCH: default Compose network')
        present = set(docker_output('volume', 'ls', '-q').splitlines())
        bindings = self.volume_bindings()
        if (len(set(bindings.values())) != len(bindings)
                or not all(re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]+', name) for name in bindings.values())):
            raise RuntimeError('Persistent volumes must have valid, distinct names')
        names = sorted(present.intersection(bindings.values()))
        inspected = json.loads(docker_output('volume', 'inspect', *names)) if names else []
        labels_by_name = {volume['Name']: volume.get('Labels') or {} for volume in inspected}
        for key, name in bindings.items():
            logical, external = VOLUMES[key]
            if external and self.values.get(external, '').lower() == 'true':
                if not retained or name not in present:
                    raise RuntimeError('External volume requires verified setup and an existing volume: ' + key)
                continue
            if name not in present:
                if retained or require_volumes:
                    raise RuntimeError('Configured persistent volume is missing: ' + key)
                continue
            labels = labels_by_name[name]
            if (labels.get('com.docker.compose.project') != self.project
                    or labels.get('com.docker.compose.volume') != logical):
                raise RuntimeError('OWNERSHIP_MISMATCH: persistent volume ' + key)
        return containers

    def command(self,args,input=None,check=True,*,admin_dev=False,overrides=None):
        if any(arg in ['up','down','stop','restart','run','exec','rm'] for arg in args):
            self.verify_project()
        base = self.base + (['--file', str(ADMIN_DEV_OVERLAY)] if admin_dev else [])
        env = docker_env()
        env.update(self.command_overrides)
        env.update(DI_TEST_HOST_UID=str(os.getuid()), DI_TEST_HOST_GID=str(os.getgid()))
        env.update(overrides or {})
        p=subprocess.run(base+list(args),cwd=ROOT,env=env,input=input,capture_output=True,text=True)
        if p.returncode and check:raise RuntimeError(self.redact((p.stdout+p.stderr)[-8000:]))
        return p
def init_context(project,ports=None,test_fixture=False):
    if not re.fullmatch('[a-z][a-z0-9-]{3,62}',project):raise RuntimeError('Invalid project')
    if (ROOT / '.runtime').is_symlink():
        raise RuntimeError('Checkout runtime may not be a symlink')
    runtime=ROOT/'.runtime'/project;env_file=runtime/'runtime.env'
    if env_file.exists():
        context = ComposeContext(env_file)
        if context.project != project:
            raise RuntimeError('Compose project/runtime binding mismatch')
        context.verify_project()
        return context
    if runtime.exists() or runtime.is_symlink():
        raise RuntimeError('Runtime directory already exists without its private configuration')
    # Fresh mode never adopts an existing running foundation under its default name.
    existing = any(docker_output(resource, 'ls', '-q', '--filter', 'label=com.docker.compose.project=' + project).strip()
                   for resource in ('volume', 'network'))
    if existing or docker_output('ps', '-aq', '--filter', 'label=com.docker.compose.project=' + project).strip():
        raise RuntimeError('Existing project requires explicit planned migration, never fresh init')
    values={'COMPOSE_PROJECT_NAME':project,'INSTANCE_ID':secrets.token_hex(16),'RUNTIME_DIR':str(runtime),'GATEWAY_PORT':'18081','KEYCLOAK_PORT':'18080','SUPERSET_PORT':'18088','CLICKHOUSE_HTTP_PORT':'18123','CLICKHOUSE_NATIVE_PORT':'19000','POSTGRES_VOLUME':project+'_postgres','GARAGE_META_VOLUME':project+'_garage-meta','GARAGE_DATA_VOLUME':project+'_garage-data','JENKINS_VOLUME':project+'_jenkins-home','CLICKHOUSE_DATA_VOLUME':project+'_clickhouse-data','CLICKHOUSE_LOG_VOLUME':project+'_clickhouse-logs','SUPERSET_VOLUME':project+'_superset-home','DI_TEST_FIXTURE':'true' if test_fixture else 'false','CLICKHOUSE_ADMIN_USER':'ch_admin','CLICKHOUSE_SUPERSET_USER':'superset_reader'}
    if ports:values.update({k:str(v) for k,v in ports.items()})
    for key in ['POSTGRES_ADMIN_PASSWORD','KEYCLOAK_DB_PASSWORD','KEYCLOAK_ADMIN_PASSWORD','KEYCLOAK_DEMO_PASSWORD','SUPERSET_DB_PASSWORD','SUPERSET_ADMIN_PASSWORD','SUPERSET_SECRET_KEY','CLICKHOUSE_DEFAULT_PASSWORD','CLICKHOUSE_ADMIN_PASSWORD','CLICKHOUSE_TEST_READER_PASSWORD','CLICKHOUSE_SUPERSET_READER_PASSWORD','JENKINS_ADMIN_PASSWORD','DI_WRITER_PASSWORD','DI_PUBLIC_PASSWORD','DI_GATEWAY_SECRET','DI_OIDC_CLIENT_SECRET','DI_SESSION_SECRET','DI_JENKINS_OIDC_CLIENT_SECRET','DI_GRETL_DELIVERY_CLIENT_SECRET','DI_CH_LOADER_PASSWORD']:values[key]=secrets.token_hex(32)
    values.update(DI_STORAGE_BUCKET='ch.so.daten',DI_STORAGE_ENDPOINT='http://garage:3900',DI_STORAGE_REGION='garage')
    for kind in ['WRITER','READER']:
        values['DI_STORAGE_'+kind+'_ACCESS_KEY']='';values['DI_STORAGE_'+kind+'_SECRET_KEY']=''
    values.update({key: f'dateninfrastruktur-{tag}:{project}' for key, tag in LOCAL_IMAGES.items()})
    runtime.mkdir(mode=0o700, parents=True)
    write_private(env_file,''.join(k+'='+encode_env(v)+'\n' for k,v in values.items()))
    context=ComposeContext(env_file);render(context);return context
def render(context):
    v=context.values;r=context.runtime
    garage=(ROOT/'services/garage/garage.toml.template').read_text()
    for key in ['RPC_SECRET','ADMIN_TOKEN','METRICS_TOKEN']:garage=garage.replace('__'+key+'__',secrets.token_hex(32))
    if not (r/'garage.toml').exists():write_private(r/'garage.toml',garage)
    realm=json.loads((ROOT/'services/keycloak/realm-template.json').read_text())
    if v['DI_TEST_FIXTURE']!='true':realm['users']=[]
    for user in realm['users']:user['credentials'][0]['value']=v['KEYCLOAK_DEMO_PASSWORD']
    audience={'name':'management-api audience','protocol':'openid-connect','protocolMapper':'oidc-audience-mapper','config':{'included.custom.audience':'management-api','access.token.claim':'true','id.token.claim':'false'}}
    realm['clients']=[{'clientId':'management-gateway','enabled':True,'protocol':'openid-connect','publicClient':False,'secret':v['DI_OIDC_CLIENT_SECRET'],'standardFlowEnabled':True,'directAccessGrantsEnabled':False,'redirectUris':['http://localhost:'+v['GATEWAY_PORT']+'/oidc/callback'],'webOrigins':['http://localhost:'+v['GATEWAY_PORT']],'protocolMappers':[audience]}]
    if v.get('DI_GRETL_DELIVERY_CLIENT_SECRET'):
        realm['clients'].append({
            'clientId': 'gretl-delivery', 'enabled': True, 'protocol': 'openid-connect',
            'publicClient': False, 'secret': v['DI_GRETL_DELIVERY_CLIENT_SECRET'],
            'standardFlowEnabled': False, 'directAccessGrantsEnabled': False,
            'serviceAccountsEnabled': True, 'protocolMappers': [audience],
        })
    if v['DI_TEST_FIXTURE']=='true':realm['clients'].append({'clientId':'management-test','enabled':True,'protocol':'openid-connect','publicClient':True,'standardFlowEnabled':False,'directAccessGrantsEnabled':True,'protocolMappers':[audience]})
    gateway = 'http://localhost:' + v['GATEWAY_PORT']
    realm['clients'].append({
        'clientId': 'jenkins-delivery', 'enabled': True, 'protocol': 'openid-connect',
        'publicClient': False, 'secret': v['DI_JENKINS_OIDC_CLIENT_SECRET'],
        'standardFlowEnabled': True, 'directAccessGrantsEnabled': False,
        'redirectUris': [gateway + '/jenkins/securityRealm/finishLogin'],
        'webOrigins': [gateway],
        'attributes': {
            'pkce.code.challenge.method': 'S256',
            'post.logout.redirect.uris': gateway + '/jenkins/',
        },
        'protocolMappers': [audience],
    })
    if not (r/'realm-initial.json').exists():
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    init = commands.add_parser('init', help='Generate a private environment for a new project')
    init.add_argument('project')
    check = commands.add_parser('check', help='Verify ownership before a direct Compose command')
    check.add_argument('--env', required=True)
    check.add_argument('--start', action='store_true', help='Require completed setup and print the checked Jenkins image ID')
    redact = commands.add_parser('redact', help='Filter configured secrets from a private log stream')
    redact.add_argument('--env', required=True)
    args = parser.parse_args()
    if args.action == 'init':
        print(init_context(args.project).env_file)
        return
    context = ComposeContext(args.env)
    if args.action == 'redact':
        context.verify_project()
        for line in sys.stdin:
            print(context.redact(line), end='', flush=True)
        return
    if (context.runtime / ADMIN_DEV_MARKER).exists():
        raise RuntimeError('Switch Admin development off before changing the regular stack')
    context.verify_resources(require_setup=args.start)
    if args.start:
        print(context.configured_jenkins_id())


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError):
        sys.exit('Invalid or inaccessible private Compose configuration')
    except RuntimeError as error:
        sys.exit(str(error))
