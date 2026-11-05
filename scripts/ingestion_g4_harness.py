"""Isolated G4 helpers. Commands and credentials are fixed to the owned fixture."""
import base64,hashlib,hmac,json,os,pathlib,re,shutil,urllib.error,urllib.parse,urllib.request,uuid
from ingestion_g3_harness import ADMIN,ROOT,compose,owned,shell,subject,target_sql,wait_for,write_private
from provision_ingestion_oidc import provision

TOPICS=ROOT.parent/'dateninfrastruktur-themenrepo'

def seed(c,host_classes=False):
    c,_=provision(c);executor=subject(c)
    args=['--profile','test','run','--rm','--no-deps']
    if host_classes:args+=['--volume',str(ADMIN/'build/compose-test')+':/opt/compose-test:ro']
    args+=['--entrypoint','java','test-fixture','-cp','/opt/compose-test/classes:/opt/compose-test/lib/*','ch.so.agi.dateninfrastruktur.admin.DeliveryG4FixtureCommand',executor]
    compose(c,args,'g4-fixture.log')
    return c

def stage(c):
    compose(c,['up','-d','--wait','--wait-timeout','180','--no-deps','admin','jenkins','origin','gateway'],'g4-normal-start.log')

def browser(c,command,label):
    owned(c)
    path=c.runtime/'g4-browser-command.json';write_private(path,json.dumps(command))
    env=os.environ.copy();env.update(DI_G3_GATEWAY='http://localhost:'+c.values['GATEWAY_PORT'],DI_G3_USER_PASSWORD=c.values['KEYCLOAK_DEMO_PASSWORD'],DI_G4_BROWSER_COMMAND=str(path))
    homes=sorted((pathlib.Path.home()/'.sdkman/candidates/java').glob('25*-tem'))
    if homes:env.update(JAVA_HOME=str(homes[-1]),PATH=str(homes[-1]/'bin')+':'+env['PATH'])
    shell(c,['./gradlew','integrationTest','--tests','*DeliveryG4BrowserIT','--console=plain'],'browser-'+label+'.log',ADMIN,env)
    import xml.etree.ElementTree as ET
    result=ET.parse(ADMIN/'build/test-results/integrationTest/TEST-ch.so.agi.dateninfrastruktur.admin.DeliveryG4BrowserIT.xml').getroot()
    assert result.get('tests')=='1' and all(result.get(k)=='0' for k in ['failures','errors','skipped'])

def submit(c,dataset,filename,mode='replace',label=None,actual=False):
    fixture=json.loads((c.runtime/'g4-fixture.json').read_text());source=(TOPICS/'fixtures/csv-g4'/filename).resolve()
    assert source.parent==TOPICS/'fixtures/csv-g4'
    path=c.runtime/filename;write_private(path,source.read_text())
    command={**fixture[dataset],'mode':mode,'csv':str(path),'actualBrowserUpload':actual,'verifyDisabled':actual}
    for name in ('paused','draft'):
        command[name+'DatasetId']=fixture[name]['datasetId'];command[name+'IssueId']=fixture[name]['issueId']
    browser(c,command,label or source.stem)
    id=json.loads((c.runtime/'g4-browser-result.json').read_text())['submissionId']
    return str(uuid.UUID(id))

def delivery(c,id):
    id=str(uuid.UUID(id))
    q=f"""
    SELECT row_to_json(r) FROM (
      SELECT s.id,s.status,s.last_error_code,s.input_size,s.input_sha256,s.status_version,s.published_version_id,s.reserved_version_id,
        (SELECT count(*) FROM di_ingest.execution e WHERE e.submission_id=s.id) AS executions,
        (SELECT e.plan FROM di_ingest.execution e WHERE e.submission_id=s.id ORDER BY e.attempt_number DESC LIMIT 1) AS plan,
        (SELECT json_object_agg(cp.checkpoint,cp.evidence) FROM di_ingest.execution_checkpoint cp
          WHERE cp.execution_id=(SELECT id FROM di_ingest.execution e WHERE e.submission_id=s.id ORDER BY e.attempt_number DESC LIMIT 1)) AS evidence
      FROM di_ingest.submission s WHERE id='{id}'::uuid) r;
    """
    raw=target_sql(c,'dateninfrastruktur_management',q);return json.loads(raw) if raw.strip() else None

def wait_delivery(c,id,expected,seconds=240):
    terminals={'PUBLISHED','REJECTED_VALIDATION','REJECTED_AUTHORIZATION','FAILED_RETRYABLE','CONFLICT','CANCELLED'}
    row=wait_for(c,'delivery '+id+' '+expected,lambda:delivery(c,id),lambda r:r and (r['status']==expected or r['status'] in terminals),seconds)
    if row['status']!=expected:raise AssertionError(f"Expected {expected}; actual {row['status']} / {row['last_error_code']}, checkpoints {list(row['evidence'] or {})}")
    return row

def ch(c,user,sql,expected=200):
    owned(c)
    users={'default':'CLICKHOUSE_DEFAULT_PASSWORD','di_csv_loader':'DI_CH_LOADER_PASSWORD','di_csv_projector':'DI_CH_PROJECTOR_PASSWORD','di_csv_view_reader':'DI_CH_READER_PASSWORD','ch_test_reader':'CLICKHOUSE_TEST_READER_PASSWORD','superset_reader':'CLICKHOUSE_SUPERSET_READER_PASSWORD'}
    request=urllib.request.Request('http://127.0.0.1:'+c.values['CLICKHOUSE_HTTP_PORT']+'/?wait_end_of_query=1',data=sql.encode(),headers={'X-ClickHouse-User':user,'X-ClickHouse-Key':c.values[users[user]]})
    try:
        with urllib.request.urlopen(request,timeout=20) as result:status=result.status;body=result.read(1048577)
    except urllib.error.HTTPError as error:status=error.code;body=error.read(65537)
    if expected is not None and status!=expected:raise AssertionError(f'ClickHouse {user} status {status}; expected {expected}: '+c.redact(body.decode(errors='replace')[:180]))
    return status,body

def get(c,path,token=None):
    owned(c);headers={'Authorization':'Bearer '+token} if token else {}
    request=urllib.request.Request('http://localhost:'+c.values['GATEWAY_PORT']+path,headers=headers)
    try:
        with urllib.request.urlopen(request,timeout=20) as r:return r.status,r.read(1048577)
    except urllib.error.HTTPError as e:return e.code,e.read(1048577)

def storage(c,key):
    owned(c);assert re.fullmatch(r'(?:downloads|ingestion)/[a-z0-9./-]+',key) and '..' not in key
    # Base64 only for safe binary transport over the text Compose adapter.
    p=c.command(['--profile','setup','run','--rm','--no-deps','-T','--entrypoint','sh','management-setup','-ec','rclone --config /runtime/operator.conf copyto "$1" /tmp/data --retries 1 >/dev/null && base64 /tmp/data','fixture','storage:ch.so.daten/'+key],check=False)
    if p.returncode:raise AssertionError('Private fixture object was not readable using the bound storage writer')
    return base64.b64decode(p.stdout)

def complete_again(c,row,change=None):
    id=str(uuid.UUID(row['plan']['executionId']));raw=target_sql(c,'dateninfrastruktur_management',f"SELECT row_to_json(r) FROM (SELECT dispatch_id,runner_principal,jenkins_run_id,fence,plan_digest FROM di_ingest.execution WHERE id='{id}') r;")
    binding=json.loads(raw)
    secret=hmac.new(c.values['DI_INGESTION_LEASE_SECRET'].encode(),f"di-lease-v1\n{id}\n{binding['dispatch_id']}\n{binding['runner_principal']}\n{binding['jenkins_run_id']}\n{binding['fence']}".encode(),hashlib.sha256).hexdigest()
    issuer='http://localhost:'+c.values['KEYCLOAK_PORT']+'/realms/dateninfrastruktur'
    form=urllib.parse.urlencode({'grant_type':'client_credentials','client_id':'di-ingestion-executor','client_secret':c.values['DI_INGESTION_EXECUTOR_CLIENT_SECRET']}).encode()
    with urllib.request.urlopen(urllib.request.Request(issuer+'/protocol/openid-connect/token',data=form),timeout=15) as response:token=json.loads(response.read(32769))['access_token']
    names={'input':'INPUT_VERIFIED','incoming':'INCOMING_VALIDATED','snapshot':'SNAPSHOT_VALIDATED','candidate':'CANDIDATE_VERIFIED','outputs':'ARTIFACTS_VERIFIED'}
    manifest={'schemaVersion':1,'submissionId':row['id'],'executionId':id,'fence':binding['fence'],'planDigest':binding['plan_digest'],**{k:row['evidence'][v] for k,v in names.items()}}
    if change:change(manifest)
    p=json.dumps({'id':id,'token':token,'body':{'binding':{'fence':binding['fence'],'leaseSecret':secret},'manifest':manifest}})
    program="""import json,sys,uuid,urllib.request,urllib.error
x=json.load(sys.stdin)
r=urllib.request.Request('http://admin:8080/internal/ingestion/executions/'+str(uuid.UUID(x['id']))+'/complete',data=json.dumps(x['body']).encode(),
 headers={'Content-Type':'application/json','Authorization':'Bearer '+x['token'],'Idempotency-Key':str(uuid.uuid4())})
try:
 with urllib.request.urlopen(r,timeout=15) as response:print(json.dumps([response.status,json.loads(response.read(8192))]))
except urllib.error.HTTPError as e: print(json.dumps([e.code,{}]))
"""
    result=c.command(['--profile','setup','run','--rm','--no-deps','-T','--entrypoint','python3','management-setup','-c',program],input=p,check=False)
    if result.returncode:raise AssertionError('Internal completion retry could not be checked')
    return json.loads(result.stdout)
