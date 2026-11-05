#!/usr/bin/env python3
"""One-shot local G1 cutover, gated by the existing independent review runner.
No normal lifecycle command imports this module. Remove after local completion.
"""
import argparse,hashlib,json,os,pathlib,subprocess,sys,fcntl
from compose_runtime import ROOT,ComposeContext,write_private,encode_env,render,read_env
from compose_operations import resolve,build
from migration_db import target_sql
sys.path.insert(0,str(ROOT/'scripts/management'))
from review_gate import validate,sha

def accepted(run):
    run=pathlib.Path(run).resolve()
    if not run.is_relative_to((ROOT/'.runtime/ingestion-review/MA-G1').resolve()):raise RuntimeError('MA-G1 independent review required')
    h=run/'handoff.json';r=run/'output/review.json';runner=run/'runner.json'
    marker=json.loads((run/'ACCEPTED.json').read_text())
    if marker!={'handoff_sha256':sha(h),'report_sha256':sha(r),'runner_sha256':sha(runner)}:raise RuntimeError('Review receipt changed')
    validate(h,r,json.loads(runner.read_text()))
    handoff=json.loads(h.read_text())
    if handoff['phase']!='MA-G1':raise RuntimeError('Wrong reviewed phase')
    for repo in handoff['repositories']:
        source=ROOT.parent/repo['name']
        if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=repo['head_sha'] or subprocess.check_output(['git','-C',str(source),'diff','HEAD','--name-only'],text=True):raise RuntimeError('Current source differs from independent G1 candidate')
    return marker

def host_binding(c):
    c.verify_project();binding={};containers={}
    for service in ['garage','postgres']:
        cid=c.command(['ps','-q',service]).stdout.strip()
        if not cid:raise RuntimeError('Bound '+service+' must be running')
        info=json.loads(subprocess.check_output(['docker','inspect',cid]))[0]
        containers[service]=info['Id']
        mounts=[{k:m[k] for k in ['Type','Name','Destination']} for m in info['Mounts'] if m['Type']=='volume']
        expected=[c.values[name] for name in (['GARAGE_META_VOLUME','GARAGE_DATA_VOLUME'] if service=='garage' else ['POSTGRES_VOLUME'])]
        if sorted(m['Name'] for m in mounts)!=sorted(expected):raise RuntimeError('Bound persistent volume mapping changed')
        binding[service]={'volumes':sorted(mounts,key=lambda m:m['Destination'])}
    return {'binding':{'project':c.project,'instance':c.values['INSTANCE_ID'],**binding},'observed_containers':containers}

def probe(c,mode):
    env=dict(os.environ);env.update(DI_STORAGE_PROBE_MODE=mode,PLAYWRIGHT_SKIP_BROWSER_GC='1',DI_COMPOSE_GATEWAY='http://localhost:'+c.values['GATEWAY_PORT'],DI_COMPOSE_ISSUER='http://localhost:'+c.values['KEYCLOAK_PORT']+'/realms/dateninfrastruktur',DI_COMPOSE_DEMO_PASSWORD=c.values['KEYCLOAK_DEMO_PASSWORD'],DI_COMPOSE_OIDC_SECRET=c.values['DI_OIDC_CLIENT_SECRET'],DI_COMPOSE_FIXTURE=str(c.runtime/'g1-probe-fixture.json'))
    homes=sorted((pathlib.Path.home()/'.sdkman/candidates/java').glob('25*-tem'))
    if not env.get('JAVA_HOME') and homes:env['JAVA_HOME']=str(homes[-1]);env['PATH']=str(homes[-1]/'bin')+':'+env['PATH']
    p=subprocess.run(['./gradlew','--no-daemon','integrationTest','--tests','*StorageCutoverProbeIT'],cwd=ROOT.parent/'dateninfrastruktur-admin',env=env,capture_output=True,text=True)
    write_private(c.runtime/'ma-g1-cutover'/('probe-'+mode+'.log'),c.redact(p.stdout+p.stderr))
    if p.returncode:raise RuntimeError('Existing same-token download probe failed; source retained; private probe log')

def run(c,action,review):
    receipt=accepted(review);private=c.runtime/'ma-g1-cutover';private.mkdir(exist_ok=True,mode=0o700)
    current=host_binding(c);binding_file=private/'host-binding.json'
    if binding_file.exists():
        if json.loads(binding_file.read_text())['binding']!=current['binding']:raise RuntimeError('Original instance/volume binding changed')
    else:write_private(binding_file,json.dumps(current,sort_keys=True))
    write_private(private/'review-receipt.json',json.dumps(receipt,sort_keys=True))
    write_private(c.runtime/'cutover-operator-g1.py',(ROOT/'services/garage/cutover-operator-g1.py').read_text())
    def tool(operation):
        fresh=host_binding(c)
        if fresh['binding']!=current['binding']:raise RuntimeError('Host binding changed before '+operation)
        names=['INSTANCE_ID']+[k for k in c.values if k.startswith(('GARAGE_DEFAULT_','GARAGE_MANAGED_','GARAGE_ORIGIN_'))]
        args=['--profile','setup','run','--rm','--no-deps',*[x for name in names for x in ['-e',name]],'--entrypoint','python3','management-setup','/runtime/cutover-operator-g1.py',operation]
        p=c.command(args,check=False)
        with (private/'operator.log').open('a') as out:out.write(c.redact(p.stdout+p.stderr))
        if p.returncode:raise RuntimeError('Bound cutover '+operation+' failed; source retained; private operator.log')
        print(c.redact(p.stdout).strip(),flush=True)
    if action=='plan':
        # Build only; existing containers keep their exact running images.
        build(c)
        query="SELECT coalesce(json_agg(json_build_object('path','/downloads/'||t_ili_tid||'/'||filename,'sha256',sha256,'size',bytesize)),'[]') FROM di_management.distribution;"
        files=json.loads(target_sql(c,'dateninfrastruktur_management',query))
        write_private(c.runtime/'g1-probe-fixture.json',json.dumps({'prefix':'read-only-existing-g1','files':files}))
        probe(c,'capture')
        # Optional Foundation fixture: derive exact expected bytes from the hash-bound
        # historical local source, never from the current bucket's own contents.
        active=json.loads((ROOT/'.runtime/active-compose.json').read_text())
        if active.get('migration_plan') and pathlib.Path(active['env']).resolve()==c.env_file:
            old=json.loads(pathlib.Path(active['migration_plan']).read_text())
            source=ROOT/'.env'
            refs=[r for r in old['secret_refs'] if pathlib.Path(r['path']).resolve()==source.resolve()]
            if len(refs)!=1 or sha(source)!=refs[0]['sha256']:raise RuntimeError('Historical Foundation source binding changed')
            original=read_env(source)
            body=('private-object-id='+original['PRIVATE_TEST_OBJECT_ID']+'\n').encode()
            proof={'bucket':'ch.so.dateninfrastruktur.private','key':'private-foundation-smoke.txt','size':len(body),'sha256':hashlib.sha256(body).hexdigest(),'source_commit':'7de6b6f','source_env_sha256':sha(source)}
            write_private(private/'foundation-fixture-proof.json',json.dumps(proof))
            write_private(private/'foundation-fixture-key.json',json.dumps({'accessKeyId':original['GARAGE_BROWSER_ACCESS_KEY'],'secretAccessKey':original['GARAGE_BROWSER_SECRET_KEY']}))
        tool('plan');return
    if action=='apply':
        if not (private/'bound-plan.json').exists():raise RuntimeError('Read-only bound plan required')
        if not (private/'maintenance.json').exists():
            # Refuse running builds; do not terminate a user execution.
            from migration_prepare import jenkins_jobs
            jenkins_jobs(c.values['GATEWAY_PORT'],c.values['JENKINS_ADMIN_PASSWORD'],require_idle=True)
            probe(c,'verify')
            write_private(private/'maintenance.json',json.dumps({'instance':c.values['INSTANCE_ID'],'review':receipt}))
        c.command(['stop','--timeout','60','jenkins','gateway','admin','sodata','origin'])
        journal=private/'cutover-g1-journal.json'
        if not journal.exists() or json.loads(journal.read_text())['state'] not in ['VERIFIED','SWITCHED','RETIRING','RETIRED']:tool('apply')
        c.command(['--profile','migration','run','--rm','--no-deps','management-upgrade'])
        tool('provision')
        new=json.loads((private/'new-storage.json').read_text())
        values={k:v for k,v in c.values.items() if not k.startswith(('GARAGE_DEFAULT_','GARAGE_MANAGED_','GARAGE_ORIGIN_','DI_MIGRATION_IMPORT_KEYS','DI_PRIVATE_STORAGE_'))}
        values.update(new)
        # Same atomic private writer as the provisioning code, without host Python TOML dependency.
        temporary=c.env_file.with_suffix('.g1-new');write_private(temporary,''.join(k+'='+encode_env(v)+'\n' for k,v in values.items()));os.replace(temporary,c.env_file)
        c=ComposeContext(c.env_file);render(c)
        c.command(['up','--no-build','--force-recreate','-d','--wait','--wait-timeout','300','garage','origin','admin','sodata','gateway','jenkins'])
    probe(c,'verify')
    # Receipt generated only after the real Java/PKCE same-token HTTP probe passed.
    import importlib.util
    spec=importlib.util.spec_from_file_location('g1_digest',ROOT/'services/garage/setup-compose.py');module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    digest=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    module.write_secrets_atomically(private/'runtime-verified.json',json.dumps({'plan_sha256':digest(json.loads((private/'bound-plan.json').read_text())),'host_binding_sha256':digest(current['binding']),'probe_sha256':sha(c.runtime/'g1-download-probes.json')}))
    tool('finish')
    print('Local G1 cutover verified; private evidence retained. Remove one-shot operator from active source before the next phase.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['plan','apply','finish']);p.add_argument('--review',required=True);p.add_argument('--env');a=p.parse_args()
    try:
        c=resolve(a.env);lock=c.runtime/'ma-g1-host.lock'
        with lock.open('a+') as stream:
            lock.chmod(0o600);fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB);run(c,a.action,a.review)
    except Exception as error:print(str(error) if isinstance(error,RuntimeError) else 'One-shot cutover failed closed; private state retained',file=sys.stderr);sys.exit(1)
