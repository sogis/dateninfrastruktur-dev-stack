#!/usr/bin/env python3
"""Selected real download and GRETL evidence in one owned canonical Compose fixture."""
import hashlib
import json
import secrets
import subprocess
from uuid import uuid4

from compose_runtime import init_context, update_context, write_private
from delivery_processing_harness import ch, complete_again, delivery, seed, stage, submit, wait_delivery
from delivery_queue_harness import compose, owned, wait_for
from ingestion_test_runtime import cleanup, http, reserve_ports, token
from test_csv_delivery import assure_file, browser, hold_worker
from test_delivery_processing import bootstrap, current, values, verify_files, view


def probe_gateway(context):
    """Capture upstream connection metadata without logging request headers or bodies."""
    owned(context)
    path=context.runtime/'apisix.yaml'
    routes=json.loads(path.read_text().split('\n#END',1)[0])
    route=next(row for row in routes['routes'] if row['id']=='download')
    route['plugins']['file-logger']={'path':'/tmp/di-download-probe.log','log_format':{
        'probe':'$http_x_di_scenario_probe','origin':'$upstream_addr','status':'$status'}}
    write_private(path,json.dumps(routes,indent=2)+'\n#END\n')
    path.chmod(0o644)


def origin_address(context):
    container=context.command(['ps','-q','origin']).stdout.strip()
    assert container
    values=json.loads(subprocess.check_output(
        ['docker','inspect','--format','{{json .NetworkSettings.Networks}}',container],text=True))
    assert len(values)==1
    return next(iter(values.values()))['IPAddress']+':8080'


def download(context,path,expected,identity=None,body=None):
    probe=str(uuid4())
    url='http://localhost:'+context.values['GATEWAY_PORT']+path
    status,_,data=http(url,identity,headers={'X-DI-Scenario-Probe':probe})
    assert status==expected,(status,expected)
    assert (data==body) is (expected==200)

    def trace():
        result=context.command(['exec','-T','gateway','cat','/tmp/di-download-probe.log'],check=False)
        return [row for line in result.stdout.splitlines() if line.startswith('{')
                if (row:=json.loads(line)).get('probe')==probe]

    found=wait_for(context,'correlated gateway upstream log',trace,bool,15)
    assert len(found)==1 and int(found[0]['status'])==expected
    if expected==200:
        assert found[0]['origin']==origin_address(context)
    else:
        assert found[0].get('origin') in (None,'','-'),'Denied request reached the file upstream'


def initial_acceptance(context):
    ch(context,'default','REVOKE DROP TABLE ON di_public_sql._tmp_replace_* FROM di_csv_projector')
    try:
        submission=submit(context,'population','population-initial.csv',actual=True)
        committed=wait_delivery(context,submission,'COMMITTED')
        assert committed['published_version_id']==committed['reserved_version_id']
        assert current(context,committed)==committed['published_version_id']
        assert set(committed['evidence'])=={'INPUT_VERIFIED','INCOMING_VALIDATED','SNAPSHOT_VALIDATED',
                                           'CANDIDATE_VERIFIED','ARTIFACTS_VERIFIED'}
        assert committed['plan']['input']['sha256']==committed['input_sha256']
        assert ch(context,'di_csv_projector','EXISTS TABLE '+view(committed))[1].strip()==b'0'
        status,receipt=complete_again(context,committed)
        assert status==202 and receipt['versionId']==committed['published_version_id'] and receipt['state']=='COMMITTED'
        print(f'FLOW ingestion.accepted submission={submission} postgres=COMMITTED clickhouse=absent bound_checkpoints=5',flush=True)
    finally:
        ch(context,'default','GRANT DROP TABLE ON di_public_sql._tmp_replace_* TO di_csv_projector')
    published=wait_delivery(context,submission,'PUBLISHED')
    files=verify_files(context,published,1,'population-initial.csv',True)
    assert values(context,view(published),'Jahrgang')==['2000']
    assert published['published_version_id']==committed['published_version_id']
    status,receipt=complete_again(context,published)
    assert status==200 and receipt['versionId']==published['published_version_id'] and receipt['state']=='PUBLISHED'
    print(f'FLOW ingestion.projected submission={submission} postgres=PUBLISHED verified_exports=csv,xlsx,parquet idempotent=true',flush=True)
    return published,files['csv']


def download_and_negative(context,open_row,open_body):
    restricted=wait_delivery(context,submit(context,'municipality','municipality-initial.csv'),'PUBLISHED')
    path,body=assure_file(context,restricted)
    open_path,_=assure_file(context,open_row)
    identity=token(context,'anna')
    download(context,open_path,200,body=open_body)
    download(context,path,403,identity,body=body)
    browser(context,'grant-read',('municipality',))
    download(context,path,200,identity,body=body)
    browser(context,'revoke-read',('municipality',))
    download(context,path,403,identity,body=body)
    compose(context,['stop','admin'],'architecture-authz-outage.log')
    try:
        download(context,open_path,503,body=open_body)
    finally:
        compose(context,['up','--no-build','--no-deps','-d','--wait','--wait-timeout','180','admin'],
                'architecture-authz-restored.log')
    download(context,open_path,200,body=open_body)
    print('FLOW download.bytes open=200 granted=200 revoked=403 outage=503 denied_origin=0',flush=True)

    compose(context,['stop','garage'],'architecture-missing-artifact.log')
    try:
        missing=wait_delivery(context,submit(context,'population','population-replace.csv'),'FAILED_RETRYABLE')
        assert 'CANDIDATE_VERIFIED' in missing['evidence'] and 'ARTIFACTS_VERIFIED' not in missing['evidence']
        assert missing['published_version_id'] is None and current(context,open_row)==open_row['published_version_id']
    finally:
        compose(context,['up','--no-build','--no-deps','-d','--wait','--wait-timeout','180','garage'],
                'architecture-artifact-storage-restored.log')
    download(context,open_path,200,body=open_body)

    with hold_worker(context,'complete') as blocked:
        denied=submit(context,'municipality','municipality-initial.csv')
        wait_for(context,'verified worker waiting before finalization',blocked,lambda count:count>=1)
        staged=delivery(context,denied)
        assert staged['status']=='READY_TO_COMMIT' and 'ARTIFACTS_VERIFIED' in staged['evidence']
        browser(context,'revoke-submit',('municipality',))
    rejected=wait_delivery(context,denied,'REJECTED_AUTHORIZATION')
    assert rejected['published_version_id'] is None
    assert current(context,restricted)==restricted['published_version_id']
    assert assure_file(context,restricted)==(path,body)
    print(f'FLOW ingestion.denied missing={missing["id"]} revoked={denied} missing_artifact=true revoked_before_commit=true valid_version_preserved=true',flush=True)


def main():
    context=init_context('mag-g5-architecture-'+secrets.token_hex(5),reserve_ports(),True)
    print('Isolated architecture evidence: '+str(context.runtime),flush=True)
    try:
        context=update_context(context,{'TOOL_IMAGE':context.values['TEST_TOOL_IMAGE']})
        context=bootstrap(context)
        context=seed(context)
        probe_gateway(context)
        stage(context)
        published,body=initial_acceptance(context)
        download_and_negative(context,published,body)
        jenkins=context.command(['ps','-q','jenkins']).stdout.strip()
        image=subprocess.check_output(['docker','inspect','--format','{{.Image}}',jenkins],text=True).strip()
        toolchain=context.command(['exec','-T','jenkins','cat','/opt/dateninfrastruktur/runner-provenance.json']).stdout
        print('FLOW toolchain jenkins_image='+image+' provenance_sha256='+hashlib.sha256(toolchain.encode()).hexdigest(),flush=True)
    finally:
        cleanup(context)
    assert not context.command(['ps','-aq']).stdout.strip()
    assert not subprocess.check_output(['docker','volume','ls','-q','--filter',
        'label=com.docker.compose.project='+context.project],text=True).strip()
    print('FLOW cleanup owned_containers=0 owned_volumes=0')
    print('ASSERTIONS=6 SKIP=0')


if __name__=='__main__':
    main()
