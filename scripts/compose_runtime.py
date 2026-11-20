"""Generate private instance configuration and verify the management schema before startup."""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ADMIN_DEV_OVERLAY = ROOT / 'compose.admin-dev.yaml'
ADMIN_DEV_IMAGE_FILE = 'admin-dev.image'
FOUNDATION_UP = ('up', '--no-deps', '--no-build', '--pull', 'never', '-d', '--wait', '--wait-timeout', '240')
SETUP_RUN = ('run', '--rm', '--pull', 'never')
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


def encode_env(value):
    # Compose parses double quotes and escaped dollars without shell evaluation.
    return json.dumps(str(value), ensure_ascii=False).replace('$', '$$')


def read_env(path):
    # Ask Compose to project dotenv values into JSON via a throwaway service.
    # config --environment cannot delimit values that contain newlines.
    keys = re.findall(r'^[ \t]*(?:export[ \t]+)?([A-Za-z_][A-Za-z0-9_]*)[ \t]*=', path.read_text(), re.M)
    if not keys:
        raise RuntimeError('Empty private configuration')
    model = {'services': {'env-reader': {'image': 'scratch',
                                       'environment': {key: '${' + key + '}' for key in keys}}}}
    result = subprocess.run(
        ['docker', 'compose', '--env-file', str(path), '--file', '-', 'config', '--format', 'json'],
        input=json.dumps(model), env=docker_env(), cwd=ROOT, capture_output=True, text=True,
    )
    if result.returncode:
        raise RuntimeError('Invalid private dotenv configuration; details withheld')
    # Compose escapes dollars again in the serialized model.
    return {key: value.replace('$$', '$')
            for key, value in json.loads(result.stdout)['services']['env-reader']['environment'].items()}


def write_private(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(text)


class ComposeContext:
    def __init__(self,env_file):
        path = Path(env_file).absolute()
        self.env_file = path.resolve()
        if ((ROOT / '.runtime').is_symlink() or path.is_symlink() or path.parent.is_symlink()
                or self.env_file.parent.parent != ROOT / '.runtime'
                or self.env_file.name != 'runtime.env' or not self.env_file.is_file()
                or self.env_file.stat().st_mode & 0o077
                or self.env_file.parent.stat().st_mode & 0o077):
            raise RuntimeError('Select a private runtime.env in a private runtime directory')
        self.values = read_env(self.env_file)
        self.project = self.values['COMPOSE_PROJECT_NAME']
        self.runtime = Path(self.values['RUNTIME_DIR']).resolve()
        if (not re.fullmatch('[a-z][a-z0-9-]{3,62}', self.project)
                or self.runtime != ROOT / '.runtime' / self.project
                or self.env_file.parent != self.runtime):
            raise RuntimeError('Compose project/runtime binding mismatch')
        if any(key.endswith(('_VOLUME', '_VOLUMES_EXTERNAL', '_VOLUME_EXTERNAL')) for key in self.values):
            raise RuntimeError('Legacy runtime uses explicit volume names. Use a new project and private runtime.')
        if any(
                k.startswith('COMPOSE_') and k != 'COMPOSE_PROJECT_NAME' for k in self.values):
            raise RuntimeError('Unexpected Compose control variable in runtime.env')
        self.base = ['docker', 'compose', '--project-name', self.project,
                     '--env-file', str(self.env_file), '--file', str(ROOT / 'compose.yaml')]

    def redact(self, value):
        for key, secret in self.values.items():
            if secret and re.search('PASSWORD|SECRET|TOKEN|ACCESS_KEY', key):
                value = value.replace(secret, '[REDACTED]')
                if '\n' in secret or '\r' in secret:
                    for line in filter(None, secret.splitlines()):
                        value = value.replace(line, '[REDACTED]')
        return value

    def command(self, args, input=None, check=True, *, admin_dev=False, overrides=None):
        base = self.base + (['--file', str(ADMIN_DEV_OVERLAY)] if admin_dev else [])
        env = docker_env()
        env.update(DI_TEST_HOST_UID=str(os.getuid()), DI_TEST_HOST_GID=str(os.getgid()))
        env.update(overrides or {})
        result = subprocess.run(base + list(args), cwd=ROOT, env=env, input=input,
                                capture_output=True, text=True)
        if result.returncode and check:
            raise RuntimeError(self.redact(result.stdout + result.stderr)[-8000:])
        return result


def init_context(project, ports=None, test_fixture=False):
    if not re.fullmatch('[a-z][a-z0-9-]{3,62}', project):
        raise RuntimeError('Invalid project name')
    if (ROOT / '.runtime').is_symlink():
        raise RuntimeError('Checkout runtime may not be a symlink')
    runtime = ROOT / '.runtime' / project
    env_file = runtime / 'runtime.env'
    if runtime.exists() or runtime.is_symlink():
        raise RuntimeError('Choose a new project name; its private runtime already exists')
    values = {
        'COMPOSE_PROJECT_NAME': project,
        'INSTANCE_ID': secrets.token_hex(16),
        'RUNTIME_DIR': str(runtime),
        'GATEWAY_PORT': '18081',
        'KEYCLOAK_PORT': '18080',
        'SUPERSET_PORT': '18088',
        'CLICKHOUSE_HTTP_PORT': '18123',
        'CLICKHOUSE_NATIVE_PORT': '19000',
        'DI_TEST_FIXTURE': 'true' if test_fixture else 'false',
        'CLICKHOUSE_ADMIN_USER': 'ch_admin',
        'CLICKHOUSE_SUPERSET_USER': 'superset_reader',
    }
    if ports:values.update({k:str(v) for k,v in ports.items()})
    for key in ['POSTGRES_ADMIN_PASSWORD','KEYCLOAK_DB_PASSWORD','KEYCLOAK_ADMIN_PASSWORD','KEYCLOAK_DEMO_PASSWORD','SUPERSET_DB_PASSWORD','SUPERSET_ADMIN_PASSWORD','SUPERSET_SECRET_KEY','CLICKHOUSE_DEFAULT_PASSWORD','CLICKHOUSE_ADMIN_PASSWORD','CLICKHOUSE_TEST_READER_PASSWORD','CLICKHOUSE_SUPERSET_READER_PASSWORD','JENKINS_ADMIN_PASSWORD','DI_WRITER_PASSWORD','DI_PUBLIC_PASSWORD','DI_GATEWAY_SECRET','DI_OIDC_CLIENT_SECRET','DI_SESSION_SECRET','DI_JENKINS_OIDC_CLIENT_SECRET','DI_GRETL_DELIVERY_CLIENT_SECRET','DI_CH_LOADER_PASSWORD']:values[key]=secrets.token_hex(32)
    values.update(DI_STORAGE_BUCKET='ch.so.daten',DI_STORAGE_ENDPOINT='http://garage:3900',DI_STORAGE_REGION='garage')
    for kind in ['WRITER','READER']:
        values['DI_STORAGE_'+kind+'_ACCESS_KEY']='';values['DI_STORAGE_'+kind+'_SECRET_KEY']=''
    values.update({key: f'dateninfrastruktur-{tag}:{project}' for key, tag in LOCAL_IMAGES.items()})
    runtime.mkdir(mode=0o700, parents=True)
    write_private(env_file,''.join(k+'='+encode_env(v)+'\n' for k,v in values.items()))
    context = ComposeContext(env_file)
    garage = (ROOT / 'services/garage/garage.toml.template').read_text()
    for key in ('RPC_SECRET', 'ADMIN_TOKEN', 'METRICS_TOKEN'):
        garage = garage.replace('__' + key + '__', secrets.token_hex(32))
    write_private(runtime / 'garage.toml', garage)

    realm_file = runtime / 'realm-initial.json'
    realm = json.loads((ROOT / 'services/keycloak/realm-template.json').read_text())
    fixture = values['DI_TEST_FIXTURE'] == 'true'
    if not fixture:
        realm['users'] = []
    for user in realm['users']:
        user['credentials'][0]['value'] = values['KEYCLOAK_DEMO_PASSWORD']
    gateway = 'http://localhost:' + values['GATEWAY_PORT']
    client = {
        'enabled': True, 'protocol': 'openid-connect', 'publicClient': False,
        'standardFlowEnabled': False, 'directAccessGrantsEnabled': False,
        'protocolMappers': [{
            'name': 'management-api audience', 'protocol': 'openid-connect',
            'protocolMapper': 'oidc-audience-mapper', 'config': {
                'included.custom.audience': 'management-api',
                'access.token.claim': 'true', 'id.token.claim': 'false',
            },
        }],
    }
    realm['clients'] = [
        dict(client, clientId='management-gateway', secret=values['DI_OIDC_CLIENT_SECRET'],
             standardFlowEnabled=True, redirectUris=[gateway + '/oidc/callback'], webOrigins=[gateway]),
        dict(client, clientId='jenkins-delivery', secret=values['DI_JENKINS_OIDC_CLIENT_SECRET'],
             standardFlowEnabled=True, redirectUris=[gateway + '/jenkins/securityRealm/finishLogin'],
             webOrigins=[gateway], attributes={'pkce.code.challenge.method': 'S256',
                                             'post.logout.redirect.uris': gateway + '/jenkins/'}),
    ]
    if values.get('DI_GRETL_DELIVERY_CLIENT_SECRET'):
        realm['clients'].append(dict(client, clientId='gretl-delivery', serviceAccountsEnabled=True,
                                     secret=values['DI_GRETL_DELIVERY_CLIENT_SECRET']))
    if fixture:
        realm['clients'].append(dict(client, clientId='management-test', publicClient=True,
                                     directAccessGrantsEnabled=True))
    write_private(realm_file, json.dumps(realm, indent=2))
    # Keycloak runs as non-root. The host directory remains private.
    realm_file.chmod(0o644)
    render_gateway(context)
    return context


def render_gateway(context):
    routes = (ROOT / 'services/apisix/routes.template.json').read_text()
    # Preserve literal dollar anchors in route regexes.
    routes = re.sub(r'\$\{([A-Z_]+)\}',
                    lambda match: json.dumps(context.values[match[1]], ensure_ascii=False)[1:-1], routes)
    path = context.runtime / 'apisix.yaml'
    write_private(path, routes + '\n#END\n')
    path.chmod(0o644)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    init = commands.add_parser('init', help='Generate a private environment for a new project')
    init.add_argument('project_prefix', help='Prefix for a new, uniquely named Compose project')
    check = commands.add_parser('preflight', help='Verify the management schema and print the checked Jenkins image ID')
    check.add_argument('--env', required=True)
    redact = commands.add_parser('redact', help='Filter configured secrets from a private log stream')
    redact.add_argument('--env', required=True)
    args = parser.parse_args()
    if args.action == 'init':
        print(init_context(f'{args.project_prefix}-{secrets.token_hex(6)}').env_file)
        return
    context = ComposeContext(args.env)
    if args.action == 'redact':
        for line in sys.stdin:
            print(context.redact(line), end='', flush=True)
        return
    if (context.runtime / ADMIN_DEV_IMAGE_FILE).exists():
        raise RuntimeError('Switch Admin development off before changing the regular stack')
    if not (context.runtime / 'origin.conf').is_file():
        raise RuntimeError('Run explicit setup before starting the stack')
    model = json.loads(context.command(['config', '--format', 'json', 'jenkins']).stdout)
    image = jenkins_image_id(model['services']['jenkins']['image'])
    context.command([*FOUNDATION_UP, '--no-recreate', 'postgres'])
    context.command([*SETUP_RUN, 'management-setup', 'verify'])
    print(image)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError):
        sys.exit('Invalid or inaccessible private Compose configuration')
    except RuntimeError as error:
        sys.exit(str(error))
