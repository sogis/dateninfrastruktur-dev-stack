#!/usr/bin/env python3
"""G30–G39 against fresh, owned Jenkins, Keycloak, Admin, PostgreSQL and APISIX."""
from ingestion_g3_harness import (
    ROOT, JENKINS, browser, cleanup, compose, delivery_rows, init_context, json, os,
    probe_image, reserve_ports, revoke_fixture, shell, subject, target_sql,
    update_context, uuid, verify_run_hygiene, wait_for, write_private, run_fixture,
)
from provision_ingestion_oidc import provision
from bind_jenkins_image import bind
from retire_legacy_jenkins_g3 import run as retire

def main():
    c=init_context('mag-g3-review-'+uuid.uuid4().hex[:10],reserve_ports(),True)
    print('Isolated G3 evidence: '+str(c.runtime),flush=True)
    try:
        realm_path=c.runtime/'realm-initial.json';realm=json.loads(realm_path.read_text())
        for user in realm['users']:
            if user['username'] in ('anna','ben'):user.update(firstName='Gleicher',lastName='Anzeigename')
        write_private(realm_path,json.dumps(realm));realm_path.chmod(0o644)
        base='dateninfrastruktur-jenkins:'+c.project
        c=update_context(c,{'TOOL_IMAGE':c.values['TEST_TOOL_IMAGE'],'JENKINS_IMAGE':base,'DI_INGESTION_MAX_UPLOAD_BYTES':'1024'})
        env=os.environ.copy();env['IMAGE_NAME']=base
        shell(c,[str(JENKINS/'bin/build-image.sh'),str(c.runtime/'jenkins-context')],'jenkins-build.log',JENKINS,env)
        c=bind(c,base)
        compose(c,['build','postgres','admin','test-tool-build'],'support-build.log')
        compose(c,['up','-d','--wait','--wait-timeout','120','postgres'],'postgres.log')
        compose(c,['--profile','setup','run','--rm','--no-deps','postgres-init'],'database-roles.log')
        compose(c,['up','-d','--wait','--wait-timeout','420','--no-deps','keycloak'],'keycloak.log')
        compose(c,['--profile','setup','run','--rm','--no-deps','--entrypoint','python3','management-setup','/opt/admin/scripts/setup_explicit.py','setup'],'setup.log')
        c,_=provision(c)
        test_retirement(c)
        executor=subject(c)
        run_fixture(c,executor)
        compose(c,['up','-d','--wait','--wait-timeout','180','--no-deps','admin','jenkins','gateway'],'normal-start.log')
        browser(c,'normal')
        installed=compose(c,['exec','-T','jenkins','sha256sum','/var/jenkins_home/plugins/jenkins-gretl-dateninfrastruktur-plugin.jpi','/var/jenkins_home/plugins/oic-auth.jpi'],'installed-plugin-hashes.log').splitlines()
        assert installed[0].split()[0]==json.loads((c.runtime/'jenkins-context/build-args.json').read_text())['PLUGIN_HPI_SHA256']
        assert installed[1].split()[0]==(c.runtime/'jenkins-context/oidc-plugin.sha256').read_text().split()[0]
        jobs=compose(c,['exec','-T','jenkins','sh','-ec','ls -1 /var/jenkins_home/jobs'],'normal-jobs.log')
        assert sorted(jobs.splitlines())==['di-csv-ingest','unmanaged-check']
        c=bind(c,probe_image(c,base))
        compose(c,['up','-d','--wait','--wait-timeout','180','--no-deps','jenkins'],'probe-start.log')
        browser(c,'upload')
        restart_and_check(c)
        browser(c,'after-restart')
        revoke_fixture(c)
        browser(c,'revoked')
        browser(c,'token-loss')
    except Exception:
        for service in ('postgres','keycloak','admin','jenkins'):
            result=c.command(['logs','--tail','120',service],check=False)
            write_private(c.runtime/('failure-'+service+'.log'),c.redact(result.stdout+result.stderr))
        raise
    finally:
        cleanup(c)

def test_retirement(c):
    compose(c,['up','--no-start','--no-build','--no-deps','jenkins'],'stopped-jenkins-volume.log')
    fixture="""import pathlib,os
root=pathlib.Path('/jenkins-home');jobs=root/'jobs'
if jobs.exists():raise RuntimeError('Expected a new test volume')
def item(name,tag,marker=None):
 directory=jobs/name;directory.mkdir(parents=True)
 properties='<properties><'+marker+'/></properties>' if marker else '<properties/>'
 (directory/'config.xml').write_text('<'+tag+'><description>Synthetic G3 retirement proof</description><disabled>true</disabled>'+properties+'</'+tag+'>')
 (directory/'builds').mkdir();(directory/'builds'/'history').write_text(name)
item('gretl-datenportal-seed','project','ch.so.agi.jenkins.gretldatenportal.GretlDatenportalManagedSeedJobProperty')
item('organisation-fixture','flow-definition','ch.so.agi.jenkins.gretldatenportal.GretlDatenportalManagedJobProperty')
item('unmanaged-check','project')
for path in jobs.rglob('*'):os.chown(path,1000,1000)
os.chown(jobs,1000,1000)
"""
    volume=c.values['JENKINS_VOLUME']+':/jenkins-home'
    tool=['--profile','setup','run','--rm','--no-deps','--volume',volume,'--entrypoint','python3','management-setup','-c']
    compose(c,tool+[fixture],'retirement-fixture.log')
    name='jenkins-retirement-'+str(uuid.uuid4())+'.json'
    assert 'Planned 2' in retire(c,'plan',name)
    change="from pathlib import Path;p=Path('/jenkins-home/jobs/unmanaged-check/config.xml');p.write_bytes(p.read_bytes()+b'\\n')"
    compose(c,tool+[change],'retirement-race.log')
    try:
        retire(c,'apply',name)
    except RuntimeError as error:
        assert 'Job inventory changed' in str(error)
    else:
        raise AssertionError('Changed unmanaged config must fail the whole preflight')
    name='jenkins-retirement-'+str(uuid.uuid4())+'.json'
    assert 'Planned 2' in retire(c,'plan',name)
    assert 'Archived 2' in retire(c,'apply',name)
    assert 'Archived 0' in retire(c,'apply',name)
    verification="""from pathlib import Path
root=Path('/jenkins-home')
assert {p.name for p in (root/'jobs').iterdir()}=={'unmanaged-check'}
assert (root/'jobs/unmanaged-check/builds/history').read_text()=='unmanaged-check'
archived=list((root/'data-infrastructure/retired').glob('legacy-*/jobs/*/builds/history'))
assert sorted(p.read_text() for p in archived)==['gretl-datenportal-seed','organisation-fixture']
"""
    compose(c,tool+[verification],'retirement-verification.log')
    print('PASS G39 scoped offline retirement, drift refusal, restart-safe repeat, preserved job histories and unmanaged job',flush=True)

def restart_and_check(c):
    ids=json.loads((c.runtime/'g3-browser.json').read_text())
    first,second,waiting=(ids[x] for x in ('first','second','waiting'))
    def queued():
        rows=delivery_rows(c,ids)
        if len(rows)!=3 or rows[waiting]['status']!='READY' or any(rows[x]['status']!='QUEUED' for x in (first,second)):return None
        assert all(x['executions']==0 and x['input_sha256']==ids['inputSha256'] and x['input_size']==ids['inputSize'] for x in rows.values())
        actual=target_sql(c,'dateninfrastruktur_management',f"SELECT submission_id||'|'||id||'|'||queue_id FROM di_ingest.dispatch WHERE submission_id IN ('{uuid.UUID(first)}','{uuid.UUID(second)}') AND state='QUEUED' ORDER BY submission_id;").splitlines()
        return actual if len(actual)==2 and all(x.split('|')[2].isdigit() for x in actual) else None
    queue_before=wait_for(c,'two durable queue acknowledgements and one waiting slot',queued,bool)
    verify_run_hygiene(c,require_binding=False,require_cps=True)
    compose(c,['stop','admin'],'admin-interruption.log')
    compose(c,['exec','-T','jenkins','sh','-ec','touch /var/jenkins_home/data-infrastructure/probe-run'],'probe-enable.log')
    compose(c,['restart','--no-deps','jenkins'],'restart.log')
    compose(c,['up','-d','--wait','--wait-timeout','180','--no-deps','jenkins'],'restart-health.log')
    def ended_without_admin():
        p=c.command(['exec','-T','jenkins','sh','-ec','find /var/jenkins_home/jobs/di-csv-ingest/builds -name build.xml -type f -exec grep -l "<result>FAILURE</result>" {} +'],check=False)
        return len(p.stdout.splitlines())
    wait_for(c,'two completed Jenkins attempts during the Admin outage',ended_without_admin,lambda n:n>=2,100)
    assert all(v['executions']==0 for v in delivery_rows(c,ids).values())
    compose(c,['up','-d','--wait','--wait-timeout','180','--no-deps','admin'],'admin-recovered.log')
    wait_for(c,'live run with allocated workspace and verified input',
             lambda:target_sql(c,'dateninfrastruktur_management',"SELECT count(*) FROM di_ingest.execution e JOIN di_ingest.execution_checkpoint cp ON cp.execution_id=e.id AND cp.checkpoint='INPUT_VERIFIED' WHERE e.state='ACTIVE';"),
             lambda count:int(count)>0,55)
    verify_run_hygiene(c,require_binding=True,require_cps=True)
    def complete():
        rows=delivery_rows(c,ids)
        return rows if len(rows)==3 and all(x['status']=='FAILED_RETRYABLE' for x in rows.values()) else None
    rows=wait_for(c,'all three intentional probe failures',complete,bool,220)
    assert all(x['executions']==1 for x in rows.values())
    for record in queue_before:
        submission,dispatch,queue=record.split('|')
        assert target_sql(c,'dateninfrastruktur_management',f"SELECT id||'|'||queue_id FROM di_ingest.dispatch WHERE submission_id='{uuid.UUID(submission)}';").strip()==dispatch+'|'+queue
    raw=compose(c,['exec','-T','jenkins','sh','-ec','for file in /var/jenkins_home/data-infrastructure/probe-observations/*.json; do cat "$file"; echo; done'],'probe-observations.log')
    observations={v['submission']:v for v in (json.loads(line) for line in raw.splitlines())}
    assert set(observations)=={first,second,waiting}
    a,b,w=(observations[x] for x in (first,second,waiting))
    assert a['dataset']==w['dataset']!=b['dataset']
    assert max(a['started'],b['started'])<min(a['finished'],b['finished']) and a['finished']<=w['started']
    assert all(v['actor']=='di-csv-executor' and v['size']==ids['inputSize'] and v['sha256']==ids['inputSha256'] for v in observations.values())
    assert target_sql(c,'dateninfrastruktur_management','SELECT count(*) FROM di_management.dataversion;').strip()=='0'
    provenance=json.loads(compose(c,['exec','-T','jenkins','cat','/opt/dateninfrastruktur/runner-provenance.json'],'runner-provenance.log'))
    provenance['imageSha256']=c.values['DI_JENKINS_IMAGE_SHA256']
    plans=target_sql(c,'dateninfrastruktur_management',"SELECT plan->'runner' FROM di_ingest.execution ORDER BY id;").splitlines()
    assert len(plans)==3 and all(json.loads(p)==provenance for p in plans)
    print('PASS G35/G36/G38 durable queue IDs and one claim each after restart and Admin outage; only different datasets overlap; technical identity, verified bytes, zero publication',flush=True)
    verify_run_hygiene(c)

if __name__=='__main__':
    main()
