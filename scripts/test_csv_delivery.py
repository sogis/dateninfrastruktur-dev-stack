#!/usr/bin/env python3
"""G50–G59 on the complete canonical Compose topology with real OIDC and GRETL."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import hashlib, json, os, pathlib, select, subprocess, sys, uuid
import xml.etree.ElementTree as ET

from bind_jenkins_image import bind
from compose_database import row_hash_sql, target_sql
from compose_operations import setup
from compose_runtime import ComposeContext, init_context, render, write_private
from delivery_queue_harness import ADMIN, JENKINS, ROOT, compose, shell, subject, verify_run_hygiene, wait_for
from delivery_processing_harness import TOPICS, browser as retry_browser, ch, complete_again, delivery, get, storage, wait_delivery
from ingestion_test_runtime import cleanup, http, reserve_ports, token
from provision_ingestion_oidc import provision

DB = 'dateninfrastruktur_management'
SERVICES = set('postgres keycloak garage origin gateway sodata admin jenkins clickhouse superset'.split())

def query(c, statement, db=DB):
    return target_sql(c, db, statement)

def boot(c):
    tag = c.values['JENKINS_IMAGE']
    def jenkins_build():
        env = {**os.environ, 'IMAGE_NAME': tag}
        shell(c, [str(JENKINS/'bin/build-image.sh'),str(c.runtime/'jenkins-context')],
              'jenkins-build.log', JENKINS, env)
    with ThreadPoolExecutor() as pool:
        image = pool.submit(jenkins_build)
        compose(c, ['build','postgres','admin','sodata','management-tool-build','test-tool-build','superset'], 'images.log')
        image.result()
    c = bind(ComposeContext(c.env_file), tag)
    setup(c)
    c = ComposeContext(c.env_file)
    compose(c, ['up','--no-build','-d','--wait','--wait-timeout','240'], 'normal-start.log')
    return c

def states(c):
    rows = [json.loads(line) for line in c.command(['ps','--format','json']).stdout.splitlines()]
    assert len(rows) == 10 and {r['Service'] for r in rows} == SERVICES
    assert all(r['State'] == 'running' and r['Health'] == 'healthy' for r in rows)
    return {row['Service']:row['ID'] for row in rows}

def inventory(c):
    cfg = json.loads(c.command(['--profile','*','config','--format','json']).stdout)['services']
    assert {n for n,service in cfg.items() if not service.get('profiles')} == SERVICES
    for name in ('postgres','garage','origin','admin','sodata','jenkins'):
        assert not cfg[name].get('ports')
    for service in cfg.values():
        assert not any('.jar' in str(v.get('source','')) for v in service.get('volumes',[]))
    assert set(query(c,"SELECT datname FROM pg_database WHERE datname NOT IN ('postgres','template0','template1');",'postgres').splitlines()) == {'keycloak','superset',DB}
    assert query(c,"SELECT split_part(current_setting('server_version'),'.',1)||':'||postgis_lib_version();") == '16:3.5.2'
    assert query(c,"SELECT di_ops.runtime_contract() AND di_ops.ingestion_contract() AND di_ops.single_storage_contract();") == 't'
    jobs = c.command(['exec','-T','jenkins','ls','-1','/var/jenkins_home/jobs']).stdout.splitlines()
    assert jobs == ['di-csv-ingest']
    assert get(c,'/jenkins/gretl-datenportal/')[0] in (401,403,404)
    for path in ('/catalog/published-catalog.xtf','/catalog/catalog.duckdb','/admin/catalog/reload','/explore/context/example','/ch.so.datenportal/metadata/current.json'):
        assert get(c,path)[0] in (403,404),path
    compose(c,['--profile','tools','run','--rm','--no-deps','storage-verify'],'storage-inventory.log')
    listing=c.command(['exec','-T','garage','/garage','bucket','list']).stdout
    assert 'ch.so.daten' in listing and not any(x in listing for x in ['di-managed-private','ch.so.datenportal','foundation-smoke'])
    program = """from pathlib import Path
for retired in ('/opt/admin/scripts/upgrade_contract.py','/opt/admin/db/upgrade','/opt/stack-tools/migration','/opt/admin/scripts/managed_runtime.py'):
    assert not Path(retired).exists(), retired
"""
    compose(c,['--profile','setup','run','--rm','--no-deps','--entrypoint','python3','management-setup','-c',program], 'tool-inventory.log')
    gateway = 'http://localhost:'+c.values['GATEWAY_PORT']
    status,_,body = http('http://localhost:'+c.values['SUPERSET_PORT']+'/health')
    assert status==200 and b'OK' in body
    assert ch(c,'superset_reader','SELECT currentUser()')[1].strip() == b'superset_reader'
    assert get(c,'/actuator/health/readiness')[0] in (403,404)
    assert http(gateway+'/datasets')[0] == 200
    states(c)

def browser(c, action, datasets=(), jobs=()):
    command = c.runtime/'g5-browser-command.json'
    write_private(command,json.dumps(dict(action=action,datasets=datasets,jobs=jobs)))
    env={**os.environ,'DI_G3_GATEWAY':'http://localhost:'+c.values['GATEWAY_PORT'],
         'DI_G3_USER_PASSWORD':c.values['KEYCLOAK_DEMO_PASSWORD'],'DI_G5_BROWSER_COMMAND':str(command)}
    homes=sorted((pathlib.Path.home()/'.sdkman/candidates/java').glob('25*-tem'))
    if homes:env.update(JAVA_HOME=str(homes[-1]),PATH=str(homes[-1]/'bin')+':'+env['PATH'])
    number=len(list(c.runtime.glob('g5-browser-*.log')))
    shell(c,['./gradlew','integrationTest','--tests','*CsvPublicationBrowserIT','--console=plain'],
          f'g5-browser-{number:02d}-{action}.log', ADMIN, env)
    report=ET.parse(ADMIN/'build/test-results/integrationTest/TEST-ch.so.agi.dateninfrastruktur.admin.CsvPublicationBrowserIT.xml').getroot()
    assert report.get('tests')=='1' and all(report.get(k)=='0' for k in ['failures','errors','skipped'])
    if action=='submit':
        return [str(uuid.UUID(v)) for v in json.loads((c.runtime/'g5-browser-result.json').read_text())]

def upload(c,*specs):
    jobs=[]
    for dataset, file, *options in specs:
        csv=c.runtime/file
        write_private(csv,(TOPICS/'fixtures/csv-delivery'/file).read_text())
        jobs.append(dict(dataset=dataset,csv=str(csv),**(options[0] if options else {})))
    return browser(c,'submit',jobs=jobs)

@contextmanager
def hold_worker(c, phase):
    """Temporary policy for this owned DB only. Wait before taking any product row lock."""
    assert c.project.startswith('mag-g5-') and c.values['DI_TEST_FIXTURE']=='true'
    assert phase in {'claim','complete'}
    assert query(c,"SELECT relrowsecurity FROM pg_class WHERE oid='di_ops.authorization_guard'::regclass")=='f'
    key='20261106, 415'
    query(c,f"""
    CREATE SCHEMA di_g5_gate;
    GRANT USAGE ON SCHEMA di_g5_gate TO di_writer;
    CREATE FUNCTION di_g5_gate.hold() RETURNS boolean LANGUAGE plpgsql VOLATILE AS $$
    BEGIN
      IF current_setting('di.action',true)='ingestion.{phase}' THEN
        PERFORM pg_advisory_xact_lock({key});
      END IF;
      RETURN true;
    END $$;
    ALTER TABLE di_ops.authorization_guard ENABLE ROW LEVEL SECURITY;
    CREATE POLICY g5_worker_gate ON di_ops.authorization_guard TO di_writer USING (di_g5_gate.hold()) WITH CHECK (true);
    """)
    env={k:os.environ[k] for k in ('PATH','HOME','DOCKER_CONFIG','DOCKER_CONTEXT','DOCKER_HOST') if k in os.environ}
    env.update(c.values)
    process=subprocess.Popen(c.base+['exec','-T','postgres','psql','-XqAt','-U','postgres','-d',DB,'-v','ON_ERROR_STOP=1'],
        cwd=ROOT,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    try:
        process.stdin.write(f"SELECT pg_advisory_lock({key});\nSELECT 'BOUND';\n".encode());process.stdin.flush()
        ready,_,_=select.select([process.stdout],[],[],15)
        assert ready and process.stdout.readline().strip()==b'' and process.stdout.readline().strip()==b'BOUND'
        yield lambda: int(query(c,"SELECT count(*) FROM pg_locks WHERE locktype='advisory' AND classid=20261106 AND objid=415 AND NOT granted;"))
    finally:
        if process.poll() is None:
            try:process.communicate(f"SELECT pg_advisory_unlock({key});\n\\q\n".encode(),timeout=15)
            except subprocess.TimeoutExpired:
                process.kill();process.communicate()
        query(c,"DROP POLICY g5_worker_gate ON di_ops.authorization_guard; ALTER TABLE di_ops.authorization_guard DISABLE ROW LEVEL SECURITY; DROP FUNCTION di_g5_gate.hold(); DROP SCHEMA di_g5_gate;")

def stable(c):
    tables=('principal','authorityassignment','accessgrant','dataset','datasetissue','dataversion','distribution')
    out={name:query(c,row_hash_sql('SELECT * FROM di_management.'+name)) for name in tables}
    out['audit']=query(c,row_hash_sql('SELECT * FROM audit.row_change'))
    out['identity']=query(c,row_hash_sql('SELECT * FROM public.user_entity'),'keycloak')
    return out

def assure_file(c,row):
    artifact=next(f for f in row['evidence']['ARTIFACTS_VERIFIED']['artifacts'] if f['format']=='csv')
    body=storage(c,artifact['objectKey'])
    assert hashlib.sha256(body).hexdigest()==artifact['sha256']
    return "/"+artifact["objectKey"],body

def run(c):
    inventory(c)
    assert query(c,'SELECT (SELECT count(*) FROM di_management.dataset)+(SELECT count(*) FROM di_management.authorityassignment);')=='0'
    print('PASS G50 normal setup, 10 services, PG16/PostGIS, one bucket and fixed job, no business seeds',flush=True)
    c,_=provision(c)
    compose(c,['--profile','test','run','--rm','--no-deps','--entrypoint','java','test-fixture',
               '-cp','/opt/compose-test/classes:/opt/compose-test/lib/*',
               'ch.so.agi.dateninfrastruktur.admin.DeliveryProcessingFixtureCommand',subject(c),'--without-grants'],'g5-fixtures.log')
    browser(c,'no-grants')
    browser(c,'grant-submit',('population','municipality','types'))
    opened_id,restricted_id=upload(c,('population','population-initial.csv'),('municipality','municipality-initial.csv'))
    return exercise(c,opened_id,restricted_id)

def exercise(c,opened_id,restricted_id):
    fixture=json.loads((c.runtime/'g4-fixture.json').read_text())
    opened=wait_delivery(c,opened_id,'PUBLISHED');restricted=wait_delivery(c,restricted_id,'PUBLISHED')
    open_path,open_bytes=assure_file(c,opened)
    restricted_path,restricted_bytes=assure_file(c,restricted)
    assert get(c,open_path)==(200,open_bytes)
    catalog='/datasets/'+fixture['population']['identifier']
    code,body=get(c,catalog)
    assert code==200 and open_path.encode() in body and b'Altersstruktur' in body
    assert get(c,catalog+'/structure-quality-origin')[0]==200
    assert get(c,catalog+'/usage')[0]==200
    assert b'Altersstruktur' in get(c,'/datasets?q=Altersstruktur&size=1')[1]
    assert b'Altersstruktur' not in get(c,'/datasets?q=NoSuchG5Term')[1]
    assert get(c,'/datasets/filter-popover?filter=office')[0]==200
    series='/series/'+fixture['seriesIdentifier']
    code,series_page=get(c,series)
    assert code==200 and b'G5 Ausgabe 2025' in series_page and b'G5 Ausgabe 2026' in series_page
    for suffix,label in (('/issues/2025',b'G5 Ausgabe 2025'),('/issues/current',b'G5 Ausgabe 2026')):
        code,page=get(c,series+suffix)
        assert code==200 and label in page
    first_page=get(c,'/datasets?page=1&size=1&sort=title-asc')[1]
    second_page=get(c,'/datasets?page=2&size=1&sort=title-asc')[1]
    assert b'Seite 1 von' in first_page and b'Seite 2 von' in second_page
    assert first_page!=second_page
    print('PASS G51/G57 manager browser grant; real OIDC upload, GRETL, PG/CH/S3; Sodata detail, search, facets and downloads',flush=True)

    anna=token(c,'anna')
    assert get(c,restricted_path,anna)[0]==403
    browser(c,'grant-read',('municipality',))
    assert get(c,restricted_path,anna)==(200,restricted_bytes)
    browser(c,'revoke-read',('municipality',))
    assert get(c,restricted_path,anna)[0]==403

    with hold_worker(c,'claim') as blocked:
        claim_id,=upload(c,('types','types-initial.csv'))
        wait_for(c,'claim waiting before the authorization row',blocked,lambda n:n>=1)
        assert delivery(c,claim_id)['status']=='QUEUED' and delivery(c,claim_id)['executions']==0
        browser(c,'revoke-submit',('types',))
    denied=wait_delivery(c,claim_id,'REJECTED_AUTHORIZATION')
    assert denied['executions']==0 and denied['published_version_id'] is None
    browser(c,'not-eligible',('types',))

    with hold_worker(c,'complete') as blocked:
        denied_id,=upload(c,('municipality','municipality-initial.csv'))
        wait_for(c,'verified artifacts awaiting actual Commit',blocked,lambda n:n>=1)
        staged=delivery(c,denied_id)
        assert staged['status']=='READY_TO_COMMIT' and 'ARTIFACTS_VERIFIED' in staged['evidence']
        pending,_=assure_file(c,staged)
        browser(c,'revoke-submit',('municipality',))
    denied=wait_delivery(c,denied_id,'REJECTED_AUTHORIZATION')
    assert denied['executions']==1 and denied['published_version_id'] is None
    assert get(c,pending,anna)[0] in (403,404)
    assert storage(c,restricted['evidence']['ARTIFACTS_VERIFIED']['artifacts'][0]['objectKey'])
    print('PASS G52 same-token read grant/revoke, no claim after submit revoke, actual verified Commit rejected after submit revoke',flush=True)

    browser(c,'grant-submit',('municipality',))
    return race_and_finish(c,opened,open_path,open_bytes,catalog)

def race_and_finish(c,opened,open_path,open_bytes,catalog):
    with hold_worker(c,'complete') as blocked:
        first_id,second_id,waiting_id=upload(c,('population','population-replace.csv',{'attack':True}),
                                           ('municipality','municipality-initial.csv'),
                                           ('population','population-initial.csv'))
        wait_for(c,'two live finalizers for distinct datasets',blocked,lambda n:n>=2)
        assert all(delivery(c,id)['status']=='READY_TO_COMMIT' for id in (first_id,second_id))
        waiting=delivery(c,waiting_id)
        assert waiting['status']=='READY' and waiting['executions']==0
    replaced=wait_delivery(c,first_id,'PUBLISHED')
    parallel=wait_delivery(c,second_id,'PUBLISHED')
    same=wait_delivery(c,waiting_id,'PUBLISHED')
    assert all(x['executions']==1 for x in (replaced,parallel,same))
    assert len({x['published_version_id'] for x in (opened,replaced,parallel,same)})==4
    assert complete_again(c,opened)[1]['versionId']==opened['published_version_id']
    assert complete_again(c,same)[1]['versionId']==same['published_version_id']
    assert get(c,open_path)==(200,open_bytes)
    verify_run_hygiene(c)
    print('PASS G53 two simultaneous real workers; same dataset ordered; foreign build/issue and duplicate requests; old callback safe',flush=True)

    ch(c,'default','REVOKE INSERT ON di_data.v_* FROM di_csv_loader')
    try:
        retry_id,=upload(c,('population','population-replace.csv'))
        failed=wait_delivery(c,retry_id,'FAILED_RETRYABLE')
        assert failed['published_version_id'] is None
        assert get(c,open_path)==(200,open_bytes)
    finally:
        ch(c,'default','GRANT INSERT ON di_data.v_* TO di_csv_loader')
    retry_browser(c,{'retryId':retry_id},'g5-retry')
    retried=wait_delivery(c,retry_id,'PUBLISHED')
    assert retried['executions']==2
    print('PASS G51/G53 recoverable real failure, native retry, one business acceptance',flush=True)

    before=stable(c);original=states(c)
    compose(c,['down','--timeout','45'],'recreate-down.log')
    compose(c,['up','--no-build','-d','--wait','--wait-timeout','300'],'recreate-up.log')
    assert all(v!=original[k] for k,v in states(c).items())
    assert stable(c)==before
    assert get(c,open_path)==(200,open_bytes)
    after_id,=upload(c,('population','population-replace.csv'))
    wait_delivery(c,after_id,'PUBLISHED')
    print('PASS G54 full down/up new containers; same identity, grants, versions, audit, old bytes, fresh OIDC and upload',flush=True)

    for service in ('origin','admin','postgres'):
        compose(c,['stop',service],service+'-failure.log')
        try:
            code,body=get(c,open_path)
            assert 500<=code<600 and body!=open_bytes,(service,code)
            if service=='postgres':assert get(c,catalog)[0]==503
        finally:
            compose(c,['up','--no-build','--no-deps','-d','--wait','--wait-timeout','240',service],service+'-recovery.log')
            wait_for(c,'authorized download after '+service+' recovery',lambda:get(c,open_path),lambda r:r==(200,open_bytes))
    print('PASS G55 fail closed on Origin/Admin/PG failures; private ports and no credential leakage',flush=True)
    inventory(c)
    shell(c,[sys.executable,'scripts/retirement_verifier.py'],'retirement.log')
    print('PASS G56 deleted entrypoints, absent retired routes/jobs/buckets, no upgrade code in normal image',flush=True)
    check_operating_guide()

def check_operating_guide():
    guide=(ROOT/'docs/operations.md').read_text()
    assert all(topic in guide for topic in ('./scripts/setup.sh','./scripts/up.sh --skip-build','/anlieferung'))

def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--keep-on-failure',action='store_true',help='Keep only the owned test project for diagnosis')
    options=parser.parse_args()
    c=init_context('mag-g5-review-'+uuid.uuid4().hex[:10],reserve_ports(),True)
    print('Isolated G5 evidence: '+str(c.runtime),flush=True)
    success=False
    try:
        c=boot(c);run(c);success=True
    finally:
        if success or not options.keep_on_failure:cleanup(c)
    assert not c.command(['ps','-aq']).stdout.strip()
    assert not subprocess.check_output(['docker','volume','ls','-q','--filter','label=com.docker.compose.project='+c.project],text=True).strip()
    print('PASS G58 isolated runtime removed; no user target or user credentials used',flush=True)

if __name__=='__main__':
    main()
