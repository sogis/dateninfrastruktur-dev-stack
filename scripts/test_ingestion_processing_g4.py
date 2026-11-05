#!/usr/bin/env python3
"""G40–G49 using only new isolated canonical Compose resources and fixture data."""
from concurrent.futures import ThreadPoolExecutor
import csv,io,xml.etree.ElementTree as ET,zipfile
from bind_jenkins_image import bind
from compose_runtime import ComposeContext,init_context,render,update_context
from ingestion_test_runtime import cleanup,reserve_ports,token
from ingestion_g3_harness import JENKINS,verify_run_hygiene
from ingestion_g4_harness import *

def fresh():
    c=init_context('mag-g4-review-'+uuid.uuid4().hex[:10],reserve_ports(),True)
    c=update_context(c,{'TOOL_IMAGE':c.values['TEST_TOOL_IMAGE']})
    print('Isolated G4 evidence: '+str(c.runtime),flush=True)
    return c

def bootstrap(c):
    tag=c.values['JENKINS_IMAGE']
    def build_jenkins():
        env=os.environ.copy();env['IMAGE_NAME']=tag
        shell(c,[str(JENKINS/'bin/build-image.sh'),str(c.runtime/'jenkins-context')],'jenkins-build.log',JENKINS,env)
    def services():
        compose(c,['build','postgres','admin','test-tool-build'],'support-build.log')
        compose(c,['up','-d','--wait','--wait-timeout','240','postgres','garage','clickhouse'],'dependencies.log')
        for name in ('postgres-init','clickhouse-init','clickhouse-ingestion-setup','garage-setup'):
            compose(c,['--profile','setup','run','--rm','--no-deps',name],name+'.log')
        compose(c,['--profile','setup','run','--rm','--no-deps','--entrypoint','python3','management-setup','/opt/admin/scripts/setup_explicit.py','setup'],'setup.log')
        compose(c,['up','-d','--wait','--wait-timeout','420','--no-deps','keycloak'],'keycloak.log')
    with ThreadPoolExecutor() as pool:
        build=pool.submit(build_jenkins);other=pool.submit(services);build.result();other.result()
    c=bind(ComposeContext(c.env_file),tag);render(c)
    return c

def output(row,fmt):
    evidence=row['evidence']['ARTIFACTS_VERIFIED']['artifacts']
    return next(item for item in evidence if item['format']==fmt)

def path_for(target):
    return '/'+target['objectKey']

def current(c,row):
    issue=str(uuid.UUID(row['plan']['issueId']))
    return target_sql(c,'dateninfrastruktur_management',f"SELECT v.t_ili_tid FROM di_management.datasetissue i JOIN di_management.dataversion v ON v.t_id=i.currentversion WHERE i.t_ili_tid='{issue}'::uuid;").strip()

def candidate(row):
    name=row['plan']['clickhouse']['candidateTable'];assert re.fullmatch('v_[0-9a-f]{32}_[0-9a-f]{32}',name);return 'di_data.'+name

def view(row):
    name=row['plan']['clickhouse']['publicationName'];assert re.fullmatch('ds_[0-9a-f]{32}_i_[0-9a-f]{32}_current',name);return 'di_public_sql.'+name

def values(c,table,field,user='di_csv_view_reader'):
    assert field in {'Jahrgang','BFS_Nr','Kennung'}
    return ch(c,user,f'SELECT `{field}` FROM {table} ORDER BY `{field}`')[1].decode().splitlines()

def verify_files(c,row,expected_rows,filename,open_data):
    checkpoint=row['evidence']['SNAPSHOT_VALIDATED'];assert checkpoint['valid'] and checkpoint['rowCount']==expected_rows
    assert row['evidence']['CANDIDATE_VERIFIED']['dataSha256']==checkpoint['dataSha256']
    inp=(TOPICS/'fixtures/csv-g4'/filename).read_bytes()
    archive=row['evidence']['ARTIFACTS_VERIFIED']['archive']
    assert storage(c,archive['inputKey'])==inp and hashlib.sha256(inp).hexdigest()==row['input_sha256']
    report=storage(c,archive['reportKey'])
    assert hashlib.sha256(report).hexdigest()==archive['reportSha256'] and json.loads(report)['snapshot']['rowCount']==expected_rows
    result={}
    for fmt in ('csv','xlsx','parquet'):
        f=output(row,fmt);data=storage(c,f['objectKey']);result[fmt]=data
        assert hashlib.sha256(data).hexdigest()==f['sha256'] and len(data)==f['byteSize']
        status,download=get(c,path_for(f))
        if open_data:assert status==200 and download==data
        else:assert status==401
    return result

def verify_types(c,files):
    rows=list(csv.reader(io.StringIO(files['csv'].decode()),delimiter=';'))
    assert len(rows)==2 and rows[1]==['00123','9999999999.9999','2024-02-29','2026-11-05T10:33:44.123Z','true','offen','','=keine Formel\nMehrzeilig "Text"; Blatt']
    with zipfile.ZipFile(io.BytesIO(files['xlsx'])) as archive:
        sheet=ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
        ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        assert sheet.find('.//x:f',ns) is None
        row=sheet.findall('.//x:row',ns)[1];cells={v.attrib['r']:v for v in row}
        assert cells['A2'].findtext('x:is/x:t',namespaces=ns)=='00123'
        assert cells['B2'].findtext('x:v',namespaces=ns)=='9999999999.9999'
        assert cells['C2'].get('s')=='1' and cells['E2'].get('t')=='b' and 'G2' not in cells
        assert cells['D2'].findtext('x:is/x:t',namespaces=ns)=='2026-11-05T10:33:44.123Z'
        assert cells['H2'].findtext('x:is/x:t',namespaces=ns)==rows[1][-1]
    if not files['parquet'].startswith(b'PAR1') or not files['parquet'].endswith(b'PAR1'):raise AssertionError('Invalid Parquet container')
    temporary='/tmp/di-g4-format-'+uuid.uuid4().hex
    src=(ROOT/'tests/ingestion/g4-format-probe.java').read_text()
    c.command(['exec','-T','jenkins','sh','-ec','umask 077; mkdir "$1"; cat > "$1/Probe.java"','fixture',temporary],src)
    try:
        c.command(['exec','-T','jenkins','sh','-ec','base64 -d > "$1/data.parquet"','fixture',temporary],base64.b64encode(files['parquet']).decode())
        out=compose(c,['exec','-T','jenkins','sh','-ec','/opt/java/openjdk17/bin/java -cp /opt/dateninfrastruktur/offline-bundle/jars/duckdb_jdbc-1.5.2.0.jar "$1/Probe.java" "$1/data.parquet"','fixture',temporary],'format-probe.log')
        assert 'PASS G43' in out
    finally:c.command(['exec','-T','jenkins','sh','-ec','rm -f "$1/Probe.java" "$1/data.parquet"; rmdir "$1"','fixture',temporary])
    print('PASS G43 CSV/XLSX/Parquet contents, leading zeros, exact decimal, UTC, formula text, null and MTEXT',flush=True)

def denied_candidate(c,row):
    for account in ('ch_test_reader','superset_reader','di_csv_view_reader'):
        code,_=ch(c,account,'SELECT count() FROM '+candidate(row),None);assert code==403
    for item in row['plan']['outputs']:
        code,_=get(c,path_for(item));assert code in (401,403,404)
    assert ch(c,'di_csv_loader','SELECT count() FROM '+candidate(row))[0]==200

def retry(c,id,label):
    browser(c,{'retryId':id},label)
    return wait_delivery(c,id,'PUBLISHED')

def negative_plan_and_input(c,known):
    import copy
    base=copy.deepcopy(known['plan'])
    original=(TOPICS/'fixtures/csv-g4/population-initial.csv').read_bytes()
    temporary='/tmp/di-g4-negative-'+uuid.uuid4().hex
    call=['exec','-T','jenkins','sh','-ec']
    c.command(call+['umask 077; mkdir "$1"; mkdir "$1/classes"; /opt/java/openjdk17/bin/javac -cp "/opt/dateninfrastruktur/offline-bundle/jars/*" -d "$1/classes" /opt/dateninfrastruktur/runner-bundle/runner/src/main/java/ch/so/agi/dateninfrastruktur/ingest/*.java','fixture',temporary])
    changes=[
      ('input_swap',lambda p:None,original.replace(b'2000',b'2002'),'INPUT_MISMATCH',False),
      ('target_swap',lambda p:p['clickhouse'].update(candidateTable='v_'+'a'*32+'_'+'b'*32),original,'PLAN_TARGET',False),
      ('object_swap',lambda p:p['outputs'][0].update(objectKey='downloads/'+str(uuid.uuid4())+'/data.csv'),original,'PLAN_TARGET',False),
      ('model_swap',lambda p:p.update(modelSetSha256='a'*64),original,'DEFINITION_BINDING',False),
      ('schema_swap',lambda p:p.update(fullSchemaDigest='b'*64),original,'SCHEMA_BINDING',False),
      ('wrong_header',lambda p:None,original.replace(b'Jahrgang',b'jahrgang'),'HEADER',True),
      ('missing_required',lambda p:None,original.replace(b';10\n',b';\n'),'MANDATORY',True),
      ('bad_utf8',lambda p:None,original.replace(b'2000',b'\xff00'),'UTF8',True),
      ('bad_quote',lambda p:None,original.replace(b'2000',b'"2000'),'QUOTE',True),
    ]
    evidence=[]
    try:
        for name,change,data,code,seal in changes:
            plan=copy.deepcopy(base);change(plan)
            if seal:plan['input'].update(size=len(data),sha256=hashlib.sha256(data).hexdigest())
            d=temporary+'/'+name
            c.command(call+['umask 077; mkdir "$1"; cat > "$1/plan.json"','fixture',d],json.dumps(plan))
            c.command(call+['base64 -d > "$1/input.csv"','fixture',d],base64.b64encode(data).decode())
            out=c.command(call+['if /opt/java/openjdk17/bin/java -cp "$1/classes:/opt/dateninfrastruktur/offline-bundle/jars/*" ch.so.agi.dateninfrastruktur.ingest.RunnerMain prepare "$2" /opt/dateninfrastruktur/runner-bundle >/dev/null 2>&1; then exit 1; fi; cat "$2/validation-error.json"','fixture',temporary,d],check=False)
            assert out.returncode==0 and json.loads(out.stdout)['code']==code,(name,out.returncode)
            evidence.append(name+': '+code)
    finally:
        c.command(call+['case "$1" in /tmp/di-g4-negative-*) find "$1" -depth -delete;; *) exit 1;; esac','fixture',temporary])
    write_private(c.runtime/'negative-plan-checks.log','\n'.join(evidence)+'\n')
    status,_=complete_again(c,known,lambda m:m['outputs']['artifacts'][0].update(objectKey='downloads/'+str(uuid.uuid4())+'/data.csv'))
    assert status==409
    print('PASS G40/G45 runner rejected changed input, model/schema/targets, header/null/UTF-8/quotes; modified completion rejected',flush=True)

def journey(c):
    first_id=submit(c,'population','population-initial.csv',actual=True)
    wait_for(c,'live CSV run with verified input',lambda:delivery(c,first_id),lambda row:row and row['status'] in {'VALIDATING','STAGING'} and 'INPUT_VERIFIED' in (row['evidence'] or {}),75)
    verify_run_hygiene(c,require_binding=True,require_cps=True)
    first=wait_delivery(c,first_id,'PUBLISHED')
    first_files=verify_files(c,first,1,'population-initial.csv',True)
    assert values(c,view(first),'Jahrgang')==['2000']
    assert current(c,first)==first['published_version_id']
    negative_plan_and_input(c,first)
    print('PASS G40/G48 real validator evidence and browser upload; paused/draft submissions denied',flush=True)

    ch(c,'default','REVOKE INSERT ON di_data.v_* FROM di_csv_loader')
    try:
        broken=wait_delivery(c,submit(c,'population','population-replace.csv',label='ch-fault'),'FAILED_RETRYABLE')
        assert broken['published_version_id'] is None and 'CANDIDATE_VERIFIED' not in broken['evidence']
        assert current(c,first)==first['published_version_id'] and values(c,view(first),'Jahrgang')==['2000']
        denied_candidate(c,broken)
    finally:ch(c,'default','GRANT INSERT ON di_data.v_* TO di_csv_loader')

    ch(c,'default','REVOKE DROP TABLE ON di_public_sql._tmp_replace_* FROM di_csv_projector')
    try:
        browser(c,{'retryId':broken['id']},'replacement-retry')
        committed=wait_delivery(c,broken['id'],'COMMITTED')
        assert committed['executions']==2 and committed['published_version_id']==committed['reserved_version_id']
        assert current(c,first)==committed['published_version_id'] and values(c,view(first),'Jahrgang')==['2000']
        status,receipt=complete_again(c,committed)
        assert status==202 and receipt['versionId']==committed['published_version_id'] and receipt['state']=='COMMITTED'
    finally:ch(c,'default','GRANT DROP TABLE ON di_public_sql._tmp_replace_* TO di_csv_projector')
    replaced=wait_delivery(c,broken['id'],'PUBLISHED')
    status,receipt=complete_again(c,replaced)
    assert status==200 and receipt['versionId']==replaced['published_version_id'] and receipt['state']=='PUBLISHED'
    assert values(c,view(replaced),'Jahrgang')==['2001'] and values(c,candidate(first),'Jahrgang','di_csv_loader')==['2000']
    for fmt in ('csv','xlsx','parquet'):
        f=output(first,fmt)
        assert storage(c,f['objectKey'])==first_files[fmt],'Historical object bytes changed'
        response=wait_for(c,'historical download '+fmt,lambda:get(c,path_for(f)),lambda r:r[0] not in (502,503,504),25)
        assert response==(200,first_files[fmt]),f'Historical {fmt} response differs (HTTP {response[0]})'
    print('PASS G41/G44/G47 distinct replace history, private failed candidate and no new download before commit, same acceptance after lost ACK, projector repair',flush=True)

    after_replacement(c,replaced)

def after_replacement(c,replaced):
    added=wait_delivery(c,submit(c,'population','population-append.csv','append'),'PUBLISHED')
    added_files=verify_files(c,added,2,'population-append.csv',True)
    assert added['plan']['baseVersionId']==replaced['published_version_id']
    assert values(c,view(added),'Jahrgang')==['2001','2002'] and values(c,candidate(replaced),'Jahrgang','di_csv_loader')==['2001']
    assert [r[0] for r in list(csv.reader(io.StringIO(added_files['csv'].decode()),delimiter=';'))[1:]]==['2001','2002']
    for accepted in (replaced,added):
        status,receipt=complete_again(c,accepted)
        assert status==200 and receipt['versionId']==accepted['published_version_id']
    assert current(c,added)==added['published_version_id'] and values(c,view(added),'Jahrgang')==['2001','2002']
    collision=wait_delivery(c,submit(c,'population','population-collision.csv','append'),'REJECTED_VALIDATION')
    assert collision['published_version_id'] is None and current(c,added)==added['published_version_id']
    invalid=wait_delivery(c,submit(c,'population','population-invalid.csv'),'REJECTED_VALIDATION')
    browser(c,{'reportId':invalid['id'],'expectedCode':'INVALID_TYPE'},'safe-invalid-report')
    assert invalid['published_version_id'] is None and values(c,view(added),'Jahrgang')==['2001','2002']
    print('PASS G42 delta and full snapshot, retained old data, cross-version duplicate and bad type rejected',flush=True)

    restricted=wait_delivery(c,submit(c,'municipality','municipality-initial.csv'),'PUBLISHED')
    verify_files(c,restricted,1,'municipality-initial.csv',False)
    assert get(c,path_for(output(restricted,'csv')),token(c,'anna'))[0]==403
    assert values(c,view(restricted),'BFS_Nr')==['2601']
    types=wait_delivery(c,submit(c,'types','types-initial.csv'),'PUBLISHED')
    verify_types(c,verify_files(c,types,1,'types-initial.csv',False))
    print('PASS G44/G49 two existing pilot model schemas and third typed fixture use the same fixed job; submit grant confers no restricted download',flush=True)

    compose(c,['stop','garage'],'garage-fault.log')
    try:
        unavailable=wait_delivery(c,submit(c,'population','population-append.csv',label='s3-fault'),'FAILED_RETRYABLE')
        assert 'CANDIDATE_VERIFIED' in unavailable['evidence'] and 'ARTIFACTS_VERIFIED' not in unavailable['evidence']
        assert current(c,added)==added['published_version_id'] and values(c,view(added),'Jahrgang')==['2001','2002']
    finally:compose(c,['up','-d','--wait','--wait-timeout','180','--no-deps','garage'],'garage-recovered.log')
    assert get(c,path_for(output(added,'csv')))==(200,added_files['csv'])
    attempt=submit(c,'population','population-replace.csv',label='admin-fault')
    active=wait_for(c,'claimed delivery before Admin interruption',lambda:delivery(c,attempt),lambda row:row and 'INPUT_VERIFIED' in (row['evidence'] or {}),70)
    execution=str(uuid.UUID(active['plan']['executionId']))
    run=target_sql(c,'dateninfrastruktur_management',f"SELECT jenkins_run_id FROM di_ingest.execution WHERE id='{execution}'::uuid;").strip()
    assert run.isdigit()
    compose(c,['stop','--timeout','0','admin'],'admin-fault.log')
    try:
        path='/var/jenkins_home/jobs/di-csv-ingest/builds/'+run+'/build.xml'
        def failed():
            return c.command(['exec','-T','jenkins','grep','-q','^  <result>FAILURE</result>',path],check=False).returncode==0
        wait_for(c,'bound Jenkins attempt terminates during Admin outage',failed,bool,115)
        assert delivery(c,attempt)['published_version_id'] is None
        assert current(c,added)==added['published_version_id']
    finally:compose(c,['up','-d','--wait','--wait-timeout','180','--no-deps','admin'],'admin-recovered.log')
    wait_delivery(c,attempt,'FAILED_RETRYABLE')
    assert values(c,view(added),'Jahrgang')==['2001','2002'] and get(c,path_for(output(added,'csv')))==(200,added_files['csv'])
    print('PASS G46 actual ClickHouse, S3 and Admin faults preserve the last valid snapshot and distribution bytes',flush=True)

    archive_restricted(c,restricted)

def archive_restricted(c,restricted,host_classes=False):
    args=['--profile','test','run','--rm','--no-deps']
    if host_classes:args+=['--volume',str(ADMIN/'build/compose-test')+':/opt/compose-test:ro']
    args+=['--entrypoint','java','test-fixture','-cp','/opt/compose-test/classes:/opt/compose-test/lib/*','ch.so.agi.dateninfrastruktur.admin.DeliveryG4FixtureCommand','--archive',restricted['plan']['datasetId']]
    compose(c,args,'archive-fixture.log')
    wait_for(c,'removed derived SQL view after catalog archive',lambda:ch(c,'di_csv_projector','EXISTS TABLE '+view(restricted))[1].strip(),lambda r:r==b'0',45)
    assert values(c,candidate(restricted),'BFS_Nr','di_csv_loader')==['2601']
    out=output(restricted,'csv');assert hashlib.sha256(storage(c,out['objectKey'])).hexdigest()==out['sha256']
    print('PASS G47 archive removes only the derived SQL view; historical candidate and file retained',flush=True)

def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--keep-on-failure',action='store_true',help='Retain only this owned test runtime for developer diagnosis')
    options=parser.parse_args()
    c=fresh();success=False
    try:
        c=bootstrap(c);c=seed(c);stage(c);journey(c);success=True
    except Exception:
        for service in ('postgres','keycloak','admin','jenkins','clickhouse'):
            p=c.command(['logs','--tail','110',service],check=False)
            write_private(c.runtime/('failure-'+service+'.log'),c.redact(p.stdout+p.stderr))
        raise
    finally:
        if success or not options.keep_on_failure:cleanup(c)
if __name__=='__main__':main()
