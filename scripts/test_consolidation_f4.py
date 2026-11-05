#!/usr/bin/env python3
"""F17–F20: final normal Compose journey, security boundary and actual recreate.
Default: own transient fixture project only. --env explicitly selects a prepared
local target, adds only a new namespaced acceptance dataset, and never cleans it.
"""
import argparse,base64,hashlib,json,os,pathlib,secrets,subprocess,sys,urllib.request
from compose_runtime import ROOT,ComposeContext,init_context,write_private
from compose_operations import build,setup
from consolidation import private_write,digest
from migration_db import snapshot,target_sql
from migration_identity import Keycloak
from test_consolidation_f1 import reserve_ports,cleanup,seed,http,SERVICES
from test_consolidation_f3 import wrapper

def check_topology(c):
    config=json.loads(c.command(['config','--format','json']).stdout)
    assert {name for name,service in config['services'].items() if not service.get('profiles')}==SERVICES
    rows=[json.loads(line) for line in c.command(['ps','--format','json']).stdout.splitlines()]
    assert len(rows)==10 and {row['Service'] for row in rows}==SERVICES
    assert all(row['State']=='running' and row.get('Health')=='healthy' for row in rows)
    for name in SERVICES:
        service=config['services'][name]
        assert not service.get('container_name') and not service.get('network_mode')
        if name in {'postgres','garage','origin','admin','sodata','jenkins'}:assert not service.get('ports')
        assert not any('.jar' in str(mount.get('source','')) for mount in service.get('volumes',[]))
    assert set(target_sql(c,'postgres',"SELECT datname FROM pg_database WHERE NOT datistemplate AND datname!='postgres';").splitlines())=={'keycloak','superset','dateninfrastruktur_management'}

def browser(c,verify=False):
    env=os.environ.copy();env.update(PLAYWRIGHT_SKIP_BROWSER_GC='1',DI_COMPOSE_GATEWAY='http://localhost:'+c.values['GATEWAY_PORT'],DI_COMPOSE_ISSUER='http://localhost:'+c.values['KEYCLOAK_PORT']+'/realms/dateninfrastruktur',DI_COMPOSE_DEMO_PASSWORD=c.values['KEYCLOAK_DEMO_PASSWORD'],DI_COMPOSE_OIDC_SECRET=c.values['DI_OIDC_CLIENT_SECRET'],DI_COMPOSE_FIXTURE=str(c.runtime/'fixture.json'),DI_COMPOSE_VERIFY_ONLY=str(verify).lower())
    homes=sorted((pathlib.Path.home()/'.sdkman/candidates/java').glob('25*-tem'))
    if not env.get('JAVA_HOME') and homes:env['JAVA_HOME']=str(homes[-1]);env['PATH']=str(homes[-1]/'bin')+':'+env['PATH']
    result=subprocess.run(['./gradlew','--no-daemon','integrationTest','--tests','*ComposeAcceptanceIT'],cwd=ROOT.parent/'dateninfrastruktur-admin',env=env,capture_output=True,text=True)
    log=c.runtime/('f4-browser-recreate.log' if verify else 'f4-browser.log');write_private(log,c.redact(result.stdout+result.stderr))
    if result.returncode:raise RuntimeError('F4 browser acceptance failed; private '+log.name)
    import xml.etree.ElementTree as ET
    report=ET.parse(ROOT.parent/'dateninfrastruktur-admin/build/test-results/integrationTest/TEST-ch.so.agi.dateninfrastruktur.admin.ComposeAcceptanceIT.xml').getroot()
    assert int(report.get('tests','0'))==1 and all(int(report.get(k,'0'))==0 for k in ['failures','errors','skipped'])
    print('PASS F19 normal fresh-login rights after recreate' if verify else 'PASS F17/F18 real browser and standard-flow same-JWT journey',flush=True)

def clickhouse(c):
    auth='Basic '+base64.b64encode(('default:'+c.values['CLICKHOUSE_DEFAULT_PASSWORD']).encode()).decode()
    def query(q):
        req=urllib.request.Request('http://localhost:'+c.values['CLICKHOUSE_HTTP_PORT']+'/',data=q.encode(),headers={'Authorization':auth})
        with urllib.request.urlopen(req,timeout=30) as response:return response.read().decode()
    tables=[json.loads(line) for line in query("SELECT database,name,engine,create_table_query FROM system.tables WHERE database NOT IN ('system','information_schema','INFORMATION_SCHEMA') ORDER BY database,name FORMAT JSONEachRow").splitlines()];results=[]
    for t in tables:
        quoted='`'+t['database'].replace('`','``')+'`.`'+t['name'].replace('`','``')+'`';rows=sorted(query('SELECT * FROM '+quoted+' FORMAT JSONEachRow').splitlines())
        results.append({'database':t['database'],'table':t['name'],'engine':t['engine'],'schema_sha256':hashlib.sha256(t['create_table_query'].encode()).hexdigest(),'rows':len(rows),'rows_sha256':hashlib.sha256(('\n'.join(rows)+'\n').encode()).hexdigest()})
    return results

def service_sentinels(c,marker):
    from migration_prepare import jenkins_jobs
    jobs=jenkins_jobs(c.values['GATEWAY_PORT'],c.values['JENKINS_ADMIN_PASSWORD'],require_idle=True)
    assert c.command(['exec','-T','jenkins','cat',marker]).stdout=='MA-F4 retention\n'
    script="""from superset.app import create_app
app=create_app()
with app.app_context():
 from superset import db
 from superset.models.core import Database
 from sqlalchemy import text
 d=db.session.query(Database).filter_by(database_name='clickhouse_foundation').one()
 with d.get_sqla_engine() as engine:
  with engine.connect() as connection:assert connection.execute(text('SELECT 1')).scalar()==1
 print('Preserved encrypted connection usable')
"""
    result=c.command(['exec','-T','superset','python','-'],script,check=False)
    if result.returncode:raise RuntimeError('F19 encrypted Superset connection failed; credentials withheld')
    return {'jobs':jobs,'clickhouse':clickhouse(c)}

def security_delta(c,fixture):
    gateway='http://localhost:'+c.values['GATEWAY_PORT'];file=next(f for f in fixture['files'] if f['kind']=='open');jwt=json.loads((c.runtime/'f4-tokens.json').read_text())['ben']
    assert http(gateway+file['path'],jwt)[0]==200
    c.command(['stop','--timeout','30','admin'])
    try:assert http(gateway+file['path'],jwt)[0]==503,'Authorization API outage must fail closed even for open bytes'
    finally:c.command(['up','--no-build','-d','--wait','--wait-timeout','180','admin'])
    assert http(gateway+file['path'],jwt)[0]==200
    # Replace only the download upstream for a bounded measurement; keep the
    # normal OIDC/forward-auth chain, and restore exact route bytes in finally.
    route=c.runtime/'apisix.yaml';original=route.read_text();probe=c.project+'-header-observer';record=c.runtime/'f4-observer.json';record.unlink(missing_ok=True)
    payload=(c.runtime/'payload'/(file['kind']+'-'+file['filename'])).read_bytes()
    code="""from http.server import BaseHTTPRequestHandler,HTTPServer
import json,pathlib
SENSITIVE={'authorization','cookie','x-access-token','x-id-token','x-userinfo','x-di-gateway-credential'}
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  observed=sorted(k.lower() for k in self.headers if k.lower() in SENSITIVE)
  pathlib.Path('/runtime/f4-observer.json').write_text(json.dumps({'credential_header_names':observed}))
  body=PAYLOAD;self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def log_message(self,*args):pass
HTTPServer(('0.0.0.0',8080),Handler).serve_forever()
""".replace('PAYLOAD',repr(payload))
    write_private(c.runtime/'f4-observer.py',code)
    cid=None
    try:
        cid=c.command(['--profile','setup','run','-d','--rm','--no-deps','--use-aliases','--name',probe,'--entrypoint','python3','management-setup','/runtime/f4-observer.py']).stdout.strip()
        config=json.loads(original.split('\n#END')[0]);next(r for r in config['routes'] if r['id']=='download')['upstream']['nodes']={'management-setup:8080':1};write_private(route,json.dumps(config)+'\n#END\n');route.chmod(0o644)
        c.command(['restart','gateway']);c.command(['up','--no-build','-d','--wait','--wait-timeout','120','gateway'])
        status,_,body=http(gateway+file['path'],jwt,headers={'Cookie':'own-test=canary','X-Access-Token':'canary','X-ID-Token':'canary','X-Userinfo':'canary','X-DI-Gateway-Credential':'canary'})
        assert status==200 and body==payload,'Observer requires successful normal authorization and exact positive bytes'
        assert json.loads(record.read_text())['credential_header_names']==[],'Credentials reached download upstream'
    finally:
        write_private(route,original);route.chmod(0o644);c.command(['restart','gateway']);c.command(['up','--no-build','-d','--wait','--wait-timeout','120','gateway'])
        if cid:
            c.verify_project();subprocess.run(['docker','stop','--time','10',cid],check=True,capture_output=True)
    assert http(gateway+file['path'],jwt)[0]==200 and route.read_text()==original
    print('PASS F18: Authorization API outage503, recovery200; temporary Compose observer receives zero credential headers; exact normal routes restored',flush=True)

def run(c,fresh=False,resume=False):
    if fresh:
        build(c);setup(c);c.command(['up','--no-build','-d','--wait','--wait-timeout','300'])
    c.verify_project();check_topology(c)
    if not resume:
        if (c.runtime/'fixture.json').exists():raise RuntimeError('Existing fixture output must not be overwritten; use --resume only for this owned F4 run')
        # The normal management-test client remains disabled: all browser/token
        # authentication below uses the normal standard-flow gateway client.
        kc=Keycloak('http://localhost:'+c.values['KEYCLOAK_PORT'],'admin',c.values['KEYCLOAK_ADMIN_PASSWORD'])
        for client in kc.api('dateninfrastruktur/clients'):
            if client['clientId']=='management-test' and client.get('enabled'):
                if c.values['DI_TEST_FIXTURE']!='true':raise RuntimeError('Normal target unexpectedly has an enabled test client; refusing to change an existing client during acceptance')
                client['enabled']=False;kc.api('dateninfrastruktur/clients/'+client['id'],client,'PUT')
        prefix='maf-f4-'+secrets.token_hex(5)
        seed(c,fixture_args=['-e','DI_COMPOSE_TEST_FIXTURE=true','-e','DI_TEST_DATASET_PREFIX='+prefix],preserve_storage_config=True)
    fixture=json.loads((c.runtime/'fixture.json').read_text());assert fixture['prefix'].startswith('maf-f4-')
    browser(c)
    security_delta(c,fixture)
    recreate(c,fixture)

def recreate(c,fixture):
    kc=Keycloak('http://localhost:'+c.values['KEYCLOAK_PORT'],'admin',c.values['KEYCLOAK_ADMIN_PASSWORD'])
    client_name=fixture['prefix']+'-retention'
    clients=[x for x in kc.api('dateninfrastruktur/clients') if x['clientId']==client_name]
    if not clients:
        kc.api('dateninfrastruktur/clients',{'clientId':client_name,'enabled':False,'publicClient':False,'standardFlowEnabled':False,'directAccessGrantsEnabled':False,'serviceAccountsEnabled':False,'secret':secrets.token_hex(32),'attributes':{'ma-f4-sentinel':fixture['prefix']}},'POST')
    def client_sentinel():
        current=Keycloak('http://localhost:'+c.values['KEYCLOAK_PORT'],'admin',c.values['KEYCLOAK_ADMIN_PASSWORD'])
        client=next(x for x in current.api('dateninfrastruktur/clients') if x['clientId']==client_name)
        assert client['enabled'] is False and client['attributes']['ma-f4-sentinel']==fixture['prefix']
        secret=current.api('dateninfrastruktur/clients/'+client['id']+'/client-secret')['value']
        return {key:client[key] for key in ['id','clientId','enabled','attributes']}|{'secret_sha256':hashlib.sha256(secret.encode()).hexdigest()}
    client_before=client_sentinel()
    marker='/var/jenkins_home/'+fixture['prefix']+'.txt';c.command(['exec','-T','jenkins','sh','-c','test ! -e "$1" && printf "MA-F4 retention\\n" > "$1" || test "$(cat "$1")" = "MA-F4 retention"','sh',marker])
    # A harmless real Gradle execution uses retained GRETL tooling, never a data publication.
    script="""set -eu
mkdir -p /tmp/maf-f4-gradle
printf '%s\\n' "allprojects { layout.buildDirectory = file('/tmp/maf-f4-gradle/build') }" >/tmp/maf-f4-gradle/init.gradle
export JAVA_HOME=/opt/java/openjdk17
export PATH="$JAVA_HOME/bin:$PATH"
cd /workspace/themenrepo
./gradlew --offline --no-daemon --project-cache-dir /tmp/maf-f4-gradle/cache -I shared/gradle/init.gradle -I /tmp/maf-f4-gradle/init.gradle tasks --all
"""
    result=c.command(['exec','-T','jenkins','bash','-s'],script,check=False)
    write_private(c.runtime/'f4-gretl.log',c.redact(result.stdout+result.stderr));assert result.returncode==0,'Harmless retained GRETL execution failed'
    before=service_sentinels(c,marker);db_before=snapshot(lambda db,q:target_sql(c,db,q),'dateninfrastruktur_management');secrets_before=digest(c.env_file)
    print('F19: nonempty DB/audit, eight-job Jenkins/GRETL, ClickHouse, encrypted Superset and Keycloak checkpoints saved; recreating canonical services',flush=True)
    ids={row['Service']:row['ID'] for row in (json.loads(l) for l in c.command(['ps','--format','json']).stdout.splitlines())}
    users_before=sorted(u['id'] for u in Keycloak('http://localhost:'+c.values['KEYCLOAK_PORT'],'admin',c.values['KEYCLOAK_ADMIN_PASSWORD']).users('dateninfrastruktur'))
    wrapper(c,'down.sh');wrapper(c,'up.sh','--skip-build');check_topology(c)
    ids_after={row['Service']:row['ID'] for row in (json.loads(l) for l in c.command(['ps','--format','json']).stdout.splitlines())}
    assert set(ids)==set(ids_after) and all(ids[s]!=ids_after[s] for s in ids),'Actual container recreation required'
    assert service_sentinels(c,marker)==before and digest(c.env_file)==secrets_before
    assert snapshot(lambda db,q:target_sql(c,db,q),'dateninfrastruktur_management')==db_before
    assert sorted(u['id'] for u in Keycloak('http://localhost:'+c.values['KEYCLOAK_PORT'],'admin',c.values['KEYCLOAK_ADMIN_PASSWORD']).users('dateninfrastruktur'))==users_before
    assert client_sentinel()==client_before,'Explicit Keycloak client change/UUID/secret lost during recreate'
    audit_before=int(target_sql(c,'dateninfrastruktur_management','SELECT max(change_id) FROM audit.row_change;'))
    browser(c,verify=True);check_topology(c)
    assert int(target_sql(c,'dateninfrastruktur_management','SELECT max(change_id) FROM audit.row_change;'))>audit_before,'New audited write must advance restored sequence after recreate'
    rows=[json.loads(l) for l in c.command(['ps','--all','--format','json']).stdout.splitlines()]
    assert len([r for r in rows if r['State']=='running'])==10
    assert not any(r['Service'] not in ids for r in rows if r['State']=='running')
    private_write(c.runtime/'f4-accepted-local.json',{'status':'FINAL_COMPOSE_JOURNEY_VERIFIED','project':c.project,'fixture_prefix':fixture['prefix'],'checks':['F17','F18','F19','F20'],'all_ten_recreated':True,'management_snapshot_preserved':True,'identities_preserved':True,'jenkins_job_count':len(before['jobs']),'clickhouse':before['clickhouse'],'secrets_unchanged':True,'test_client_used':False,'observer_removed':True})
    print('PASS F19/F20: all ten actually recreated; DB/audit/sequences/identities/secrets, active/revoked grants, files and retained Jenkins/CH/encrypted Superset preserved; only ten canonical services, no active probe',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--env');parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    c=ComposeContext(args.env) if args.env else init_context('maf-f4-'+secrets.token_hex(5),reserve_ports(),True)
    write_private(ROOT/'.runtime/maf-f4-current.json',json.dumps({'env':str(c.env_file),'own_fixture':not bool(args.env)}))
    try:run(c,fresh=not bool(args.env),resume=args.resume)
    except Exception as error:print(c.redact(str(error)),file=sys.stderr);raise SystemExit(1)
    finally:
        if not args.env:cleanup(c)
