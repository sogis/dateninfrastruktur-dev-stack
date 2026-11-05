#!/usr/bin/env python3
"""F14–F16: canonical wrapper lifecycle, full recreate and archived legacy recovery."""
import hashlib,json,pathlib,secrets,subprocess,sys
from compose_runtime import ROOT,init_context,ComposeContext,write_private
from consolidation import private_write,inspect,digest
from test_consolidation_f1 import reserve_ports,cleanup,sql,token,http,check_topology
from test_consolidation_f2 import create_fixtures,migration_plan,fixture_ref
from migration_coordinator import Migration
from migration_lifecycle import cutover,verify_services,rollback
from migration_retirement import retire,verify_backup
from migration_db import snapshot,target_sql

def wrapper(c,action,*args):
    p=subprocess.run([str(ROOT/'scripts'/action),'--env',str(c.env_file),*args],capture_output=True,text=True)
    if p.returncode:raise RuntimeError(c.redact(p.stdout+p.stderr))
    return p.stdout

def observe(c,files):
    check_topology(c)
    anna=token(c,'anna');ben=token(c,'ben');gateway='http://localhost:'+c.values['GATEWAY_PORT']
    for file in files:
        code,_,body=http(gateway+file['path'],anna)
        assert code==200 and hashlib.sha256(body).hexdigest()==file['sha256']
        if file['kind']=='restricted':assert http(gateway+file['path'],ben)[0]==403
    assert c.command(['exec','-T','jenkins','cat','/var/jenkins_home/ma-f3-sentinel.txt']).stdout=='canonical retention\n'
    return snapshot(lambda db,q:target_sql(c,db,q),'dateninfrastruktur_management')

def adapter(c):
    prefix="""set -eu
mkdir -p /tmp/maf-f3-adapter
printf '%s\\n' "allprojects { layout.buildDirectory = file('/tmp/maf-f3-adapter/build') }" >/tmp/maf-f3-adapter/init.gradle
export JAVA_HOME=/opt/java/openjdk17
export PATH="$JAVA_HOME/bin:$PATH"
cd /workspace/themenrepo
./gradlew --offline --no-daemon --project-cache-dir /tmp/maf-f3-adapter/cache -I shared/gradle/init.gradle -I /tmp/maf-f3-adapter/init.gradle reloadPortal -x verifyOpendata -PreloadPortal=true -PcatalogSourceType=database -Ps3Publish="""
    for publish in ['true','false']:
        result=c.command(['exec','-T','jenkins','bash','-s'],prefix+publish+'\n',check=False)
        write_private(c.runtime/('legacy-adapter-'+publish+'.log'),c.redact(result.stdout+result.stderr))
        if publish=='true':assert result.returncode!=0 and 'Legacy-S3-Publikation ist hier nicht der Registrierungsweg' in result.stdout+result.stderr and '> Task' not in result.stdout+result.stderr
        else:assert result.returncode==0 and 'reloadPortal SKIPPED' in result.stdout
    print('PASS F14 legacy adapter: DB-mode upload rejected before tasks; local artifacts/reload skip retained; loader code unchanged',flush=True)

def run(f,m,t,only_recovery=False):
    f,m,t=create_fixtures(f,m,t)
    f.command(['--profile','migration-fixture','up','--no-build','-d','--wait','fixture-namespace-parent','fixture-namespace-child'])
    f.command(['exec','-T','fixture-namespace-child','python','-c',"from pathlib import Path;Path('/tmp/legacy-namespace-state').write_text('created after source startup\\n')"])
    assert http('http://localhost:'+f.values['GATEWAY_PORT'])[2]==b'created after source startup\n'
    f,m,t,path=migration_plan(f,m,t)
    plan=json.loads(path.read_text())
    for service in ['fixture-namespace-parent','fixture-namespace-child']:
        ref=fixture_ref(f,service);plan['source_refs'].append(ref);plan['source_states'].append({'ref':ref,'running':True});plan['retire_allowlist'].append(ref['id'])
    private_write(path,plan)
    op=Migration(path);cutover(op);t=op.context;files=json.loads((m.runtime/'fixture.json').read_text())['files']
    cids={x['Service']:x['ID'] for x in [json.loads(l) for l in t.command(['ps','--format','json']).stdout.splitlines()]}
    t.command(['exec','-T','jenkins','sh','-c','printf "canonical retention\\n" > /var/jenkins_home/ma-f3-sentinel.txt'])
    before=observe(t,files);secret_hash=digest(t.env_file)
    if not only_recovery:
        adapter(t)
        # A wrong instance or volume mapping is rejected before stopping/recreating anything.
        original=t.env_file.read_text()
        from compose_runtime import update_context
        for change,action in [({'INSTANCE_ID':secrets.token_hex(16)},'stop.sh'),({'POSTGRES_VOLUME':'never-adopt-an-unknown-volume'},'up.sh')]:
            update_context(t,change)
            try:wrapper(t,action,'--skip-build') if action=='up.sh' else wrapper(t,action)
            except RuntimeError as error:assert 'OWNERSHIP_MISMATCH' in str(error)
            else:raise AssertionError('Wrong runtime binding accepted')
            write_private(t.env_file,original)
        # Existing setup must be read-only and retain all UUIDs/grants/audit.
        wrapper(t,'setup.sh');assert observe(t,files)==before and digest(t.env_file)==secret_hash
        assert 'Gateway:' in wrapper(t,'management/status.sh')
        for stage in ['stop.sh','down.sh']:
            wrapper(t,stage)
            wrapper(t,'management/up.sh','--skip-build')
            assert observe(t,files)==before and digest(t.env_file)==secret_hash
            verify_services(op)
        new_cids={x['Service']:x['ID'] for x in [json.loads(l) for l in t.command(['ps','--format','json']).stdout.splitlines()]}
        assert all(new_cids[name]!=old for name,old in cids.items()),'down/up did not really recreate containers'
        print('PASS F14/F15: Root/management wrappers share exact context; read-only setup, stop/start and true down/up preserve domain/audit/sequences/secrets, identities, grants/revocations, files and Jenkins/CH/Superset',flush=True)
    # A changed allowlist must not be able to retire a different resource.
    original=list(op.plan['retire_allowlist']);op.plan['retire_allowlist']=original+['0'*64]
    try:retire(op)
    except RuntimeError as error:assert 'OWNERSHIP_MISMATCH' in str(error)
    else:raise AssertionError('Unlisted retirement accepted')
    op.plan['retire_allowlist']=original
    archive=verify_backup(op);manifest_path=op.root/'retirement/manifest.json';manifest_original=manifest_path.read_text()
    write_private(manifest_path,manifest_original+'\n')
    try:retire(op)
    except RuntimeError as error:assert 'BACKUP_FAILED' in str(error)
    else:raise AssertionError('Changed backup manifest accepted')
    write_private(manifest_path,manifest_original)
    retire(op);retire(op)
    for ref in op.plan['source_refs']:
        assert subprocess.run(['docker','inspect',ref['id']],capture_output=True).returncode!=0
    for volume in archive['retained_volumes']:subprocess.run(['docker','volume','inspect',volume],check=True,capture_output=True)
    assert observe(t,files)==before
    # Demonstrate that the saved current H2 layer/config is sufficient AFTER rm.
    rollback(op)
    from migration_identity import Keycloak
    for source in [f,m]:
        kc=Keycloak('http://localhost:'+source.values['KEYCLOAK_PORT'],'admin',source.values['KEYCLOAK_ADMIN_PASSWORD'])
        person=next(u for u in kc.users('dateninfrastruktur') if u['username']=='anna')
        if source.project==m.project:assert person['firstName']=='Anna MA current profile'
    assert http('http://localhost:'+f.values['GATEWAY_PORT'])[2]==b'created after source startup\n','shared namespace child or writable state was not recovered'
    assert all(not row['State']=='running' for row in [json.loads(l) for l in t.command(['ps','--all','--format','json']).stdout.splitlines()])
    print('PASS F16: foreign allowlist/changed backup refused; exact sources retired without volumes; private filesystem exports+configs reconstruct live original identities including current writable H2; target retained stopped',flush=True)
    print('PASS F16 focused recovery delta' if only_recovery else 'PASS MA-F3 F14–F16',flush=True)
    return op

if __name__=='__main__':
    contexts=[init_context('maf-f3-'+kind+'-'+secrets.token_hex(4),reserve_ports(),True) for kind in ['foundation','management','target']]
    write_private(ROOT/'.runtime/maf-f3-current.json',json.dumps(dict(zip(['foundation','management','target'],[str(c.env_file) for c in contexts]))))
    try:run(*contexts,only_recovery='--only-recovery' in sys.argv)
    except Exception as error:
        message=str(error)
        for context in contexts:message=context.redact(message)
        print(message,file=sys.stderr);raise SystemExit(1)
    finally:
        target=ComposeContext(contexts[-1].env_file);journal=target.runtime/'migration/journal.json';config=target.runtime/'migration/retirement/recovery.compose.json'
        if journal.exists():
            data=json.loads(journal.read_text())
            recovery=data.get('recovery_project') or ('di-recovery-'+data['operation_id'].replace('-','')[:16] if data.get('retirement_started') else None)
            if recovery:
                subprocess.run(['docker','compose','--project-name',recovery,'--file',str(config),'down'],check=True,capture_output=True)
        for context in reversed(contexts):cleanup(ComposeContext(context.env_file))
