#!/usr/bin/env python3
"""One explicit local cutover, bound to the reviewed MA-G5 sources and existing state."""
from concurrent.futures import ThreadPoolExecutor
import argparse, fcntl, hashlib, json, os, pathlib, re, subprocess, sys, time, urllib.request, uuid

from bind_jenkins_image import bind
from compose_database import row_hash_sql, target_sql
from compose_operations import ACTIVE, resolve, volume_bindings
from compose_runtime import ComposeContext, ROOT, encode_env, render, update_context, write_private
from provision_ingestion_oidc import provision
from retire_legacy_jenkins_g3 import run as retire

ADMIN=ROOT.parent/'dateninfrastruktur-admin'
JENKINS=ROOT.parent/'dateninfrastruktur-jenkins-dev'
DOCS=ROOT/'docs/implementation/storage-and-delivery'
UPGRADE=ADMIN/'db/upgrade'
DB='dateninfrastruktur_management'
NAMES=set('postgres keycloak garage origin gateway sodata admin jenkins clickhouse superset'.split())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, data):
    write_private(path,json.dumps(data,sort_keys=True,indent=2)+'\n')

def approval(run_id):
    if not re.fullmatch(r'\d{8}T\d{6}Z',run_id):
        raise RuntimeError('Explicit independently approved MA-G5 candidate ID required')
    run=ROOT/'.runtime/ingestion-review/MA-G5'/run_id
    paths={'handoff':run/'handoff.json','report':run/'output/review.json','runner':run/'runner.json'}
    marker=json.loads((run/'ACCEPTED.json').read_text())
    if marker!={name+'_sha256':sha(path) for name,path in paths.items()}:
        raise RuntimeError('MA-G5 gate evidence changed')
    sys.path.insert(0,str(ROOT/'scripts/management'))
    from review_gate import validate
    cwd=pathlib.Path.cwd()
    try:
        os.chdir(run)
        validate(paths['handoff'],paths['report'],json.loads(paths['runner'].read_text()))
    finally:
        os.chdir(cwd)
    for repo in json.loads(paths['handoff'].read_text())['repositories']:
        checkout=ROOT.parent/repo['name']
        head=subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()
        if head!=repo['head_sha'] or subprocess.check_output(['git','-C',str(checkout),'status','--porcelain','--untracked-files=no'],text=True):
            raise RuntimeError('Source differs from independently accepted candidate: '+repo['name'])
    return marker

def step(c, args, path):
    p=c.command(args,check=False)
    write_private(path,c.redact(p.stdout+p.stderr))
    if p.returncode:
        raise RuntimeError('Cutover step failed; private '+path.name)
    return p.stdout

def physical(c):
    c.verify_project()
    rows=[json.loads(line) for line in c.command(['ps','--format','json']).stdout.splitlines()]
    if {x['Service'] for x in rows}!=NAMES or len(rows)!=10 or any(x.get('Health')!='healthy' for x in rows):
        raise RuntimeError('Expected exactly ten healthy services of the verified local project')
    info=json.loads(subprocess.check_output(['docker','inspect',*[x['ID'] for x in rows]],text=True))
    out={i['Config']['Labels']['com.docker.compose.service']:{'id':i['Id'],'image':i['Image'],
         'namedVolumes':sorted(x['Name'] for x in i['Mounts'] if x['Type']=='volume')} for i in info}
    return out

def sql(c, statement, database=DB):
    return target_sql(c,database,statement)

def retention_bound(c):
    principals=sql(c,'SELECT t_id FROM di_management.principal ORDER BY t_id;').splitlines()
    users=sql(c,'SELECT id FROM public.user_entity ORDER BY id;','keycloak').splitlines()
    for user in users:uuid.UUID(user)
    audit=sql(c,'SELECT coalesce(max(change_id),0) FROM audit.row_change;')
    return {'principals':[int(i) for i in principals],'users':users,'auditMaxId':int(audit)}

def business(c, bound=None):
    mapping=json.loads((UPGRADE/'ma-g1-mapping.json').read_text())
    columns={}
    for item in mapping['columns']:
        name=item['table_name'];column=item['column_name']
        if not name.startswith('t_ili2db_'):
            if not all(re.fullmatch(r'[a-z_][a-z0-9_]*',part) for part in (name,column)):
                raise RuntimeError('Invalid frozen source mapping')
            columns.setdefault(name,[]).append(column)
    result={}
    for name,cols in sorted(columns.items()):
        fields=','.join(['"'+col+'"' for col in cols]+['row_version'])
        origin='di_management.'+name
        if bound and name=='principal':
            origin+=' WHERE t_id IN ('+','.join(str(i) for i in bound['principals'])+')'
        result[name]=[int(sql(c,'SELECT count(*) FROM '+origin)),sql(c,row_hash_sql('SELECT '+fields+' FROM '+origin))]
    audit='audit.row_change'+(' WHERE change_id<='+str(bound['auditMaxId']) if bound else '')
    result['audit']=[int(sql(c,'SELECT count(*) FROM '+audit)),sql(c,row_hash_sql('SELECT * FROM '+audit))]
    for table in ('user_entity','credential','user_role_mapping','user_group_membership','federated_identity'):
        origin='public.'+table
        if bound:
            field='id' if table=='user_entity' else 'user_id'
            origin+=' WHERE '+field+' IN ('+','.join("'"+str(uuid.UUID(i))+"'" for i in bound['users'])+')'
        result['identity.'+table]=[int(sql(c,'SELECT count(*) FROM '+origin,'keycloak')),
                                  sql(c,row_hash_sql('SELECT * FROM '+origin),'keycloak')]
    return result

OBJECT_PROBE="""import boto3,configparser,hashlib,json,pathlib
from botocore.config import Config
config=configparser.ConfigParser(interpolation=None)
config.read('/runtime/operator.conf')
entry=config['storage']
assert entry['endpoint']=='http://garage:3900' and entry['region']=='garage'
client=boto3.client('s3',endpoint_url=entry['endpoint'],region_name=entry['region'],
  aws_access_key_id=entry['access_key_id'],aws_secret_access_key=entry['secret_access_key'],
  config=Config(s3={'addressing_style':'path'},retries={'max_attempts':1}))
data=[]
for row in json.loads(pathlib.Path('/runtime/ma-g5-cutover/references.json').read_text()):
    item=client.get_object(Bucket='ch.so.daten',Key=row['objectkey'])
    h=hashlib.sha256();count=0
    with item['Body'] as stream:
        for chunk in iter(lambda: stream.read(65536),b''):
            count+=len(chunk);h.update(chunk)
            assert count<=row['bytesize']
    assert count==row['bytesize'] and h.hexdigest()==row['sha256']
    data.append([row['objectkey'],count,h.hexdigest(),item.get('ContentType'),item.get('Metadata'),item.get('ETag')])
print(json.dumps(data,sort_keys=True))
"""

def objects(c, path):
    p=step(c,['--profile','setup','run','--rm','--no-deps','--entrypoint','python3','management-setup','-c',OBJECT_PROBE],path)
    return json.loads(p)

def foundation(c):
    statement="""SELECT database,name,engine,total_rows
    FROM system.tables
    WHERE database NOT IN ('system','information_schema','INFORMATION_SCHEMA','di_data','di_public_sql')
    ORDER BY database,name FORMAT JSONCompact"""
    request=urllib.request.Request('http://127.0.0.1:'+str(int(c.values['CLICKHOUSE_HTTP_PORT']))+'/',
        data=statement.encode(),headers={'X-ClickHouse-User':'default','X-ClickHouse-Key':c.values['CLICKHOUSE_DEFAULT_PASSWORD']})
    with urllib.request.urlopen(request,timeout=15) as response:
        clickhouse=json.loads(response.read(1048577))['data']
    superset={}
    for name in ('ab_user','dashboards','dbs','slices','tables'):
        superset[name]=sql(c,row_hash_sql('SELECT * FROM public.'+name),'superset')
    return {'clickhouseTables':clickhouse,'superset':superset}


def check_local(c):
    pointer=json.loads(ACTIVE.read_text())
    marker=json.loads((c.runtime/'setup-complete.json').read_text())
    if (c.project!='dateninfrastruktur' or c.values.get('DI_TEST_FIXTURE')!='false'
        or pointer['project']!=c.project or pointer['env']!=str(c.env_file)
        or pointer['instance']!=c.values['INSTANCE_ID'] or marker['instance']!=pointer['instance']
        or marker['volumes']!=volume_bindings(c) or c.values.get('DI_STORAGE_BUCKET')!='ch.so.daten'
        or c.values.get('DI_STORAGE_ENDPOINT')!='http://garage:3900'):
        raise RuntimeError('Local cutover ownership proof does not match the retained instance')
    previous=c.runtime/'ma-g1-cutover'
    if not all((previous/name).is_file() for name in ('review-receipt.json','runtime-verified.json','final-storage.log')):
        raise RuntimeError('Verified local G1 storage cutover evidence missing')
    if sql(c,'SELECT fingerprint FROM di_ops.contract_fingerprint;')!=json.loads((UPGRADE/'ma-g1-to-ma-g2.json').read_text())['fromFingerprint']:
        raise RuntimeError('Live management DB is not the known unmodified G1 predecessor')
    if sql(c,'SELECT count(*) FROM di_management.authorityassignment WHERE revokedat IS NOT NULL;')!='0':
        raise RuntimeError('Unattributed historical authority revocation needs explicit reconciliation')
    return physical(c)

def local_backup(c, path):
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL
    env={k:os.environ[k] for k in ('PATH','HOME','DOCKER_CONFIG','DOCKER_CONTEXT','DOCKER_HOST') if k in os.environ}
    env.update(c.values)
    with os.fdopen(os.open(path,flags,0o600),'wb') as out:
        p=subprocess.run(c.base+['exec','-T','postgres','pg_dump','-U','postgres','--format=custom','--dbname='+DB],
                         env=env,cwd=ROOT,stdout=out,stderr=subprocess.PIPE)
        out.flush();os.fsync(out.fileno())
    with path.open('rb') as stream:
        if p.returncode or stream.read(5)!=b'PGDMP':
            raise RuntimeError('Private pre-upgrade DB checkpoint failed; database unchanged')

def build(c, root, run_id):
    suffix='mag5-'+run_id.lower()
    updates={k:'dateninfrastruktur-'+component+':'+suffix for k,component in
             (('ADMIN_IMAGE','admin'),('SODATA_IMAGE','sodata'),('TOOL_IMAGE','tools'),('POSTGRES_IMAGE','postgres'),('SUPERSET_IMAGE','superset'))}
    build_file=c.runtime/'ma-g5-build.env'
    write_private(build_file,''.join(k+'='+encode_env(v)+'\n' for k,v in {**c.values,**updates}.items()))
    staged=ComposeContext(build_file)
    tag='dateninfrastruktur-jenkins:'+suffix
    def jenkins():
        p=subprocess.run([str(JENKINS/'bin/build-image.sh'),str(root/'jenkins-context')],cwd=JENKINS,
                         env={**os.environ,'IMAGE_NAME':tag},capture_output=True,text=True)
        write_private(root/'jenkins-build.log',c.redact(p.stdout+p.stderr))
        if p.returncode:raise RuntimeError('Local candidate Jenkins build failed')
    with ThreadPoolExecutor() as pool:
        worker=pool.submit(jenkins)
        step(staged,['build','postgres','admin','sodata','management-tool-build','superset'],root/'images.log')
        worker.result()
    image_ids={name:subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',value],text=True).strip()
               for name,value in updates.items()}
    return updates,tag,image_ids

def gateway_probe(c,root,mode):
    fixture=root/'g1-probe-fixture.json'
    if not fixture.exists():
        write_private(fixture,(c.runtime/'g1-probe-fixture.json').read_text())
    env={**os.environ,'DI_STORAGE_PROBE_MODE':mode,'PLAYWRIGHT_SKIP_BROWSER_GC':'1',
         'DI_COMPOSE_GATEWAY':'http://localhost:'+c.values['GATEWAY_PORT'],
         'DI_COMPOSE_ISSUER':'http://localhost:'+c.values['KEYCLOAK_PORT']+'/realms/dateninfrastruktur',
         'DI_COMPOSE_DEMO_PASSWORD':c.values['KEYCLOAK_DEMO_PASSWORD'],'DI_COMPOSE_OIDC_SECRET':c.values['DI_OIDC_CLIENT_SECRET'],
         'DI_COMPOSE_FIXTURE':str(fixture)}
    homes=sorted((pathlib.Path.home()/'.sdkman/candidates/java').glob('25*-tem'))
    if homes:env.update(JAVA_HOME=str(homes[-1]),PATH=str(homes[-1]/'bin')+':'+env['PATH'])
    p=subprocess.run(['./gradlew','integrationTest','--tests','*StorageCutoverProbeIT','--console=plain'],
                     cwd=ADMIN,env=env,capture_output=True,text=True)
    write_private(root/('gateway-'+mode+'.log'),c.redact(p.stdout+p.stderr))
    if p.returncode:raise RuntimeError('Read-only existing-user download comparison failed')
    return json.loads((root/'g1-download-probes.json').read_text())['observations']

QUIET=r'''set -eu
umask 077
tmp=$(mktemp -d)
trap 'rm -f "$tmp"/cookie "$tmp"/auth "$tmp"/json; rmdir "$tmp"' EXIT
cat > "$tmp/auth"
fetch() { curl -fsS --max-time 12 --config "$tmp/auth" -b "$tmp/cookie" -c "$tmp/cookie" "$@"; }
url=http://127.0.0.1:8080/jenkins
case "$1" in
  quietDown|cancelQuietDown)
    crumb=$(fetch "$url/crumbIssuer/api/json" | sed -n 's/.*"crumb":"\([^"]*\)".*/\1/p')
    [ -n "$crumb" ]
    fetch -X POST -H "Jenkins-Crumb: $crumb" "$url/$1" >/dev/null ;;
  inspect)
    fetch -g "$url/api/json?tree=quietingDown,jobs[name,color]" > "$tmp/json"
    cat "$tmp/json"; printf '\n'
    fetch -g "$url/queue/api/json?tree=items[task[name],why]"; printf '\n' ;;
  *) exit 2;;
esac
'''

def jenkins_quiesce(c, root):
    # Old bootstrap login is used only for the owned local Jenkins, via stdin.
    auth='user = '+json.dumps('admin:'+c.values['JENKINS_ADMIN_PASSWORD'])+'\n'
    def old(action):
        return c.command(['exec','-T','jenkins','sh','-ec',QUIET,'cutover',action],input=auth).stdout
    old('quietDown')
    try:
        deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            server,queue=[json.loads(line) for line in old('inspect').splitlines()]
            if not server.get('quietingDown'):
                raise RuntimeError('Unable to verify Jenkins quiet mode')
            if not any(j.get('color','').endswith('_anime') for j in server['jobs']):
                # Pending foreign jobs need explicit operator reconciliation, not cancellation.
                if queue['items']:
                    raise RuntimeError('Pending Jenkins jobs remain; none were cancelled')
                save(root/'jenkins-drained.json',{'quietingDown':True,'building':0,'queued':0})
                return
            time.sleep(3)
        raise RuntimeError('Jenkins builds did not drain; no job was aborted')
    except Exception:
        old('cancelQuietDown')
        raise

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate_id')
    args=parser.parse_args()
    receipt=approval(args.candidate_id)
    c=resolve()
    before_services=check_local(c)
    root=c.runtime/'ma-g5-cutover';root.mkdir(mode=0o700)
    with (root/'owner.lock').open('x') as owner:
        os.chmod(owner.name,0o600);fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
        save(root/'accepted.json',receipt)
        save(root/'before-services.json',before_services)
        candidate,tag,image_ids=build(c,root,args.candidate_id)
        save(root/'candidate-images.json',image_ids)
        if check_local(c)!=before_services:
            raise RuntimeError('Live services changed while the candidate was built')
        sql_rows="SELECT row_to_json(x) FROM (SELECT objectkey,sha256,bytesize FROM di_management.distribution WHERE availability='available' ORDER BY objectkey) x;"
        refs=[json.loads(line) for line in sql(c,sql_rows).splitlines()]
        if not refs or len({x['objectkey'] for x in refs})!=len(refs):
            raise RuntimeError('Known referenced file set could not be bound')
        save(root/'references.json',refs)
        save(root/'storage-before.json',objects(c,root/'storage-before.log'))
        old_access=gateway_probe(c,root,'capture')
        jenkins_quiesce(c,root)
        # Nothing below this line starts a service from the previous schema.
        step(c,['stop','--timeout','60','gateway','jenkins','sodata','admin'],root/'stop.log')
        bound=retention_bound(c)
        before=business(c,bound)
        foundation_before=foundation(c)
        save(root/'foundation-before.json',foundation_before)
        save(root/'before-business.json',before)
        save(root/'retention-bound.json',bound)
        local_backup(c,root/'management-before.dump')
        c=update_context(c,candidate)
        filename='jenkins-retirement-'+str(uuid.uuid4())+'.json'
        print(retire(c,'plan',filename),flush=True)
        print(retire(c,'apply',filename),flush=True)
        step(c,['--profile','setup','run','--rm','--no-deps',
                '--volume',str(ADMIN/'scripts/upgrade_contract.py')+':/opt/admin/scripts/upgrade_contract.py:ro',
                '--volume',str(UPGRADE)+':/opt/admin/db/upgrade:ro',
                '--entrypoint','python3','management-setup','/opt/admin/scripts/upgrade_contract.py'],root/'upgrade.log')
        if business(c,bound)!=before:
            raise RuntimeError('Known source table or historical audit changed during upgrade')
        c,identity=provision(c)
        step(c,['--profile','setup','run','--rm','--no-deps','clickhouse-ingestion-setup'],root/'clickhouse-setup.log')
        step(c,['--profile','setup','run','--rm','--no-deps','management-setup','verify'],root/'contract.log')
        step(c,['--profile','tools','run','--rm','--no-deps','--entrypoint','java','management-operator',
                '-Dloader.main=ch.so.agi.dateninfrastruktur.admin.operator.DeliveryServiceIdentityCommand',
                '-cp','/opt/admin/app.jar','org.springframework.boot.loader.launch.PropertiesLauncher','/runtime/'+identity.name],root/'executor-identity.log')
        c=bind(c,tag);render(c)
        step(c,['up','--no-build','-d','--wait','--wait-timeout','300'],root/'up.log')
        after_services=physical(c);save(root/'after-services.json',after_services)
        if any(before_services[name]['namedVolumes']!=after_services[name]['namedVolumes'] for name in NAMES):
            raise RuntimeError('Persistent named volume binding changed')
        # One new technical principal is expected; the earlier users/assignments and audit prefix remain.
        if business(c,bound)!=before:
            raise RuntimeError('Retained identity, authority, business or audit rows changed')
        now=business(c)
        if now['principal'][0]!=before['principal'][0]+1 or now['identity.user_entity'][0]!=before['identity.user_entity'][0]+1:
            raise RuntimeError('Unexpected number of technical identities provisioned')
        for service in ('admin','sodata','postgres','superset'):
            if after_services[service]['image']!=image_ids[service.upper()+'_IMAGE']:
                raise RuntimeError('Started image does not match candidate: '+service)
        if after_services['jenkins']['image']!=c.values['JENKINS_IMAGE']:
            raise RuntimeError('Started Jenkins image does not match candidate')
        save(root/'after-business.json',now)
        foundation_after=foundation(c)
        if foundation_after!=foundation_before:
            raise RuntimeError('Existing ClickHouse inventory or Superset state changed')
        save(root/'foundation-after.json',foundation_after)
        assert objects(c,root/'storage-after.log')==json.loads((root/'storage-before.json').read_text())
        step(c,['--profile','tools','run','--rm','--no-deps','storage-verify'],root/'storage-policy.log')
        assert gateway_probe(c,root,'verify')==old_access
        jobs=step(c,['exec','-T','jenkins','ls','-1','/var/jenkins_home/jobs'],root/'new-jobs.log').splitlines()
        plan=json.loads((c.runtime/filename).read_text())
        foreign={k for k,v in plan['inventory'].items() if not v['legacyMarker']}
        if set(jobs)!=foreign|{'di-csv-ingest'}:
            raise RuntimeError('New Jenkins job inventory differs')
        save(root/'verified.json',{'review':args.candidate_id,'services':len(after_services),'privateFiles':len(refs),
             'privateBytes':sum(x['bytesize'] for x in refs),'historicalAudit':before['audit'][0],
             'archivedJobs':sum(bool(v['legacyMarker']) for v in plan['inventory'].values()),
             'archivedAssets':len(plan['assets']),'downloadStatuses':{str(status):sum(x['status']==status for x in old_access) for status in (200,401,403)}})
        print('LOCAL_CUTOVER_VERIFIED; private evidence: '+str(root))
if __name__=='__main__':
    main()
