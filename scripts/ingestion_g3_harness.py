"""Synthetic G3 runtime helpers. Never use an active/user Compose context."""
import base64,json,os,pathlib,re,shutil,subprocess,time,urllib.parse,urllib.request,uuid
from compose_runtime import ROOT,ComposeContext,init_context,update_context,write_private
from test_consolidation_f1 import reserve_ports,cleanup
from migration_db import target_sql

ADMIN=ROOT.parent/'dateninfrastruktur-admin'
JENKINS=ROOT.parent/'dateninfrastruktur-jenkins-dev'
def owned(c):
    if not c.project.startswith(('mag-g3-','mag-g4-')) or c.values['DI_TEST_FIXTURE']!='true':raise RuntimeError('Isolated G3 test context required')
    c.verify_project()
def compose(c,args,log):
    owned(c);p=c.command(args,check=False);write_private(c.runtime/log,c.redact(p.stdout+p.stderr))
    if p.returncode:raise RuntimeError('Isolated G3 step failed; private '+str(c.runtime/log))
    return p.stdout

def shell(c,cmd,log,cwd=None,env=None):
    owned(c);p=subprocess.run(cmd,cwd=cwd or ROOT,env=env,capture_output=True,text=True)
    safe=c.redact(p.stdout+p.stderr);safe=re.sub(r'([?&]code=)[^&\s]+',r'\1[REDACTED]',safe)
    write_private(c.runtime/log,safe)
    if p.returncode:raise RuntimeError('Isolated G3 command failed; private '+str(c.runtime/log))
    return p.stdout

def subject(c):
    from ingestion_clients import executor_subject
    return executor_subject(c.values)[1]

def browser(c,stage):
    def ready():
        try:
            with urllib.request.urlopen('http://localhost:'+c.values['GATEWAY_PORT']+'/jenkins/login',timeout=5) as response:
                return response.status==200
        except OSError:return False
    wait_for(c,'Jenkins route through APISIX after lifecycle change',ready,bool,85)
    env=os.environ.copy();env.update(DI_G3_GATEWAY='http://localhost:'+c.values['GATEWAY_PORT'],DI_G3_USER_PASSWORD=c.values['KEYCLOAK_DEMO_PASSWORD'],DI_G3_STAGE=stage,DI_G3_BROWSER_RESULT=str(c.runtime/'g3-browser.json'))
    java=sorted((pathlib.Path.home()/'.sdkman/candidates/java').glob('25*-tem'))
    if java:env.update(JAVA_HOME=str(java[-1]),PATH=str(java[-1]/'bin')+':'+env['PATH'])
    shell(c,['./gradlew','integrationTest','--tests','*DeliveryG3BrowserIT','--console=plain'],'browser-'+stage+'.log',ADMIN,env)
    import xml.etree.ElementTree as ET
    report=ADMIN/'build/test-results/integrationTest/TEST-ch.so.agi.dateninfrastruktur.admin.DeliveryG3BrowserIT.xml'
    result=ET.parse(report).getroot();assert result.get('tests')=='1' and all(result.get(k)=='0' for k in ['failures','errors','skipped'])
    for line in (result.findtext('system-out') or '').splitlines():
        if line.startswith('PASS '):print(line,flush=True)

def probe_image(c,source):
    actual=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',source],text=True).strip()
    if actual!=c.values['JENKINS_IMAGE']:raise RuntimeError('Probe parent must be the bound normal image')
    name='dateninfrastruktur-jenkins-probe:'+c.project
    d=c.runtime/'probe-context';d.mkdir(mode=0o700);shutil.copyfile(ROOT/'tests/ingestion/g3-probe.groovy',d/'g3-probe.groovy')
    (d/'Dockerfile').write_text('FROM '+source+'\nCOPY --chown=jenkins:jenkins g3-probe.groovy /usr/share/jenkins/ref/init.groovy.d/di-g3-probe.groovy\n')
    shell(c,['docker','build','-t',name,str(d)],'probe-image.log');return name

def run_fixture(c,executor,host_classes=False):
    args=['--profile','test','run','--rm','--no-deps']
    if host_classes:args+=['--volume',str(ADMIN/'build/compose-test')+':/opt/compose-test:ro']
    compose(c,args+['--entrypoint','java','test-fixture','-cp','/opt/compose-test/classes:/opt/compose-test/lib/*','ch.so.agi.dateninfrastruktur.admin.DeliveryG3FixtureCommand',executor],'g3-fixture.log')

def wait_for(c,description,query,predicate,seconds=150):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        value=query()
        if predicate(value):return value
        time.sleep(2)
    raise RuntimeError('Timed out waiting for '+description+'; private '+str(c.runtime))

def delivery_rows(c,ids):
    bindings=','.join("'"+str(uuid.UUID(ids[key]))+"'::uuid" for key in ['first','second','waiting'])
    result=target_sql(c,'dateninfrastruktur_management',"SELECT row_to_json(r) FROM (SELECT id,status,input_sha256,input_size,(SELECT count(*) FROM di_ingest.execution e WHERE e.submission_id=s.id) AS executions FROM di_ingest.submission s WHERE id IN ("+bindings+")) r;")
    return {v['id']:v for v in (json.loads(line) for line in result.splitlines())}

def verify_run_hygiene(c,require_binding=True,require_cps=False):
    # Encoded only for transport to this in-memory assertion; never write raw run XML/CPS/logs to artifacts.
    cmd=['exec','-T','jenkins','sh','-ec','find /var/jenkins_home/jobs/di-csv-ingest/builds -type f \\( -name build.xml -o -name log -o -name program.dat \\) -exec cat {} + | base64']
    raw=base64.b64decode(c.command(cmd).stdout);assert raw
    assert not re.search(rb'eyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{15,}',raw) and b'refresh_token' not in raw
    for key in ['DI_INGESTION_PLUGIN_SECRET','DI_INGESTION_EXECUTOR_CLIENT_SECRET','DI_JENKINS_OIDC_CLIENT_SECRET','DI_INGESTION_LEASE_SECRET','KEYCLOAK_DEMO_PASSWORD','JENKINS_ADMIN_PASSWORD','DI_STORAGE_WRITER_ACCESS_KEY','DI_STORAGE_WRITER_SECRET_KEY','DI_CH_LOADER_PASSWORD']:
        if c.values.get(key):assert c.values[key].encode() not in raw
    assert not re.search(rb'<lease>[0-9a-f]{64}</lease>',raw)
    if require_binding:assert b'DeliveryRunBindingAction' in raw and re.search(rb'<lease>\{[A-Za-z0-9+/=]+\}</lease>',raw)
    if require_cps:
        present=c.command(['exec','-T','jenkins','sh','-ec','find /var/jenkins_home/jobs/di-csv-ingest/builds -type f -name program.dat -size +0c']).stdout
        assert present.strip(),'A non-empty paused/live CPS program is required'
    files=c.command(['exec','-T','jenkins','sh','-ec','find /var/jenkins_home/jobs/di-csv-ingest/builds -type d -name archive']).stdout.strip();assert not files
    print('PASS G37 no user/service token or credentials in '+('live CPS and build records' if require_cps else 'completed build records')+'; no artifact archive',flush=True)

def revoke_fixture(c):
    v=json.loads((c.runtime/'g3-fixture.json').read_text());grant=str(uuid.UUID(v['grant']));issuer='http://localhost:'+c.values['KEYCLOAK_PORT']+'/realms/dateninfrastruktur';actor='2d9e1f70-3b4c-5d6e-af70-8b9c0d1e2f03'
    target_sql(c,'dateninfrastruktur_management',f"""BEGIN;
    SET LOCAL di.actor_issuer='{issuer}'; SET LOCAL di.actor_subject='{actor}'; SET LOCAL di.actor_kind='user';
    SET LOCAL di.request_id='{uuid.uuid4()}'; SET LOCAL di.command_id='{uuid.uuid4()}'; SET LOCAL di.action='test.g3_revoke';
    UPDATE di_management.authorityassignment SET revokedat=timezone('UTC',clock_timestamp()),revocationreason='Synthetic G3 stale-page test',revokedby=(SELECT t_id FROM di_management.principal WHERE aissuer='{issuer}' AND asubject='{actor}') WHERE t_ili_tid='{grant}'::uuid; COMMIT;""")
