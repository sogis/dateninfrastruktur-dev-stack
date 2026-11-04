#!/usr/bin/env python3
"""Create an immutable isolated candidate, invoke OpenCode2, validate its gate."""
import argparse, datetime, hashlib, json, os, pathlib, re, shutil, subprocess, sys
from review_gate import PHASE_CHECKS, sha, validate
STACK=pathlib.Path(__file__).resolve().parents[2]
PLAN=pathlib.Path('docs/implementation/management-and-access')
WORKSPACE=STACK.parent
MODEL='deepseek/deepseek-flash'
def call(args,**kw): return subprocess.check_output(args,text=True,**kw).strip()
def git(repo,*args):return call(['git','-C',str(repo),*args])
def binary():
    choices=[os.environ.get('DI_OPENCODE',''),str(pathlib.Path.home()/'Library/Application Support/ai.opencode.desktop/cli/2.2.5-arm64/opencode-cli'),shutil.which('opencode')]
    for path in choices:
        if path and pathlib.Path(path).is_file():
            version=call([path,'--version'])
            if re.fullmatch(r'(?:opencode v)?2\.\d+\.\d+',version):return path,version
    raise RuntimeError('NICHT_PRUEFBAR: no installed OpenCode2 CLI; no implicit global upgrade')
def snapshot(repo):
    files=git(repo,'ls-files','-z').split('\0')
    return {f:sha(repo/f) for f in files if f}
def prepare(phase):
    runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    plan=pathlib.Path('docs/implementation/compose-consolidation') if phase.startswith('MA-F') else PLAN
    run=STACK/('.runtime/compose-review' if phase.startswith('MA-F') else '.runtime/management-review')/phase/runid
    run.mkdir(parents=True,exist_ok=False)
    workspace=run/'workspace';workspace.mkdir()
    (run/'output').mkdir()
    repos=[]
    request_text=(STACK/plan/'review'/f'{phase}-request.md').read_text()
    short_names={'dateninfrastruktur-dev-stack':'STACK','dateninfrastruktur-admin':'ADMIN','dateninfrastruktur-sodata':'PUBLIC','dateninfrastruktur-jenkins-dev':'JENKINS','dateninfrastruktur-jenkins-gretl-plugin':'PLUGIN','dateninfrastruktur-themenrepo':'TOPICS'}
    names=['dateninfrastruktur-dev-stack','dateninfrastruktur-admin','dateninfrastruktur-sodata']
    if phase.startswith('MA-F'):names+=['dateninfrastruktur-jenkins-dev','dateninfrastruktur-jenkins-gretl-plugin','dateninfrastruktur-themenrepo']
    for name in names:
        source=WORKSPACE/name
        if git(source,'diff','HEAD','--name-only'):raise RuntimeError('Uncommitted product changes: '+name)
        target=workspace/name
        head=git(source,'rev-parse','HEAD')
        subprocess.run(['git','clone','--quiet','--no-hardlinks','--no-checkout',str(source),str(target)],check=True)
        subprocess.run(['git','-C',str(target),'checkout','--quiet','--detach',head],check=True)
        match=re.search(r'^- '+short_names[name]+r' base:?\s+'+chr(96)+r'([0-9a-f]{40})'+chr(96),request_text,re.M)
        base=match.group(1) if match else None
        if base:
            subprocess.run(['git','-C',str(target),'merge-base','--is-ancestor',base,head],check=True)
        repos.append({'name':name,'path':str(target),'base_sha':base,'head_sha':head,'clean_product_tree':True})
    shutil.copyfile(WORKSPACE/'AGENTS.md',workspace/'AGENTS.md')
    agent=workspace/'.opencode/agents';agent.mkdir(parents=True)
    shutil.copyfile(STACK/'scripts/management/reviewer-agent.md',agent/'management-review.md')
    (workspace/'.gitignore').write_text('.runtime/\n')
    sp=workspace/'dateninfrastruktur-dev-stack'/plan
    specs={str(f):sha(f) for f in sorted(sp.glob('*.md')) if f.name not in ('WORK_QUEUE.md',)}
    if phase.startswith('MA-F'):
        current=sp/'templates/AGENTS.workspace.current.md'
        if sha(current)!=sha(workspace/'AGENTS.md'):raise RuntimeError('Active workspace AGENTS differs from versioned current snapshot')
        specs[str(current)]=sha(current)
    spec_digest=hashlib.sha256(json.dumps(specs,sort_keys=True).encode()).hexdigest()
    request=sp/'review'/f'{phase}-request.md'
    h={'schema_version':1,'phase':phase,'candidate_id':runid,'created_at_utc':runid,
       'specification':{'files_sha256':specs,'aggregate_sha256':spec_digest},
       'request':{'path':str(request),'sha256':sha(request)},'repositories':repos,
       'workspace_agents':{'path':str(workspace/'AGENTS.md'),'sha256':sha(workspace/'AGENTS.md')},
       'reviewer':{'requested':'OpenCode2; DeepSeek Flash1017 via existing DeepSeek account','actual_provider_model':MODEL},
       'test_selection':{'required_checks':PHASE_CHECKS[phase],'execute_checks':PHASE_CHECKS[phase]},
       'isolation':{'workspace':str(workspace),'runtime_directory':str(workspace/'.runtime'),'output_directory':str(run/'output'),'ports':'isolated Compose project, ports, named volumes and private test-only credentials' if phase.startswith('MA-F') else 'random loopback, new PG container per compatibility.py invocation','env_file_path_only':None,'compose_project':None},
       'notes':['No original .env copied. No user service may be changed. Only own labeled resources. No phase beyond this gate.']}
    (run/'handoff.json').write_text(json.dumps(h,indent=2)+'\n')
    return run,h

def execute(phase):
    executable,version=binary()
    run,h=prepare(phase);workspace=pathlib.Path(h['isolation']['workspace']);out=run/'output'
    h['reviewer']['opencode_version']=version
    hp=run/'handoff.json';hp.write_text(json.dumps(h,indent=2)+'\n')
    before={r['name']:snapshot(pathlib.Path(r['path'])) for r in h['repositories']}
    original_before={r['name']:snapshot(WORKSPACE/r['name']) for r in h['repositories']}
    original_status={r['name']:git(WORKSPACE/r['name'],'status','--porcelain') for r in h['repositories']}
    (run/'before.json').write_text(json.dumps(before,indent=2))
    env=os.environ.copy()
    env['PWD']=str(workspace)
    # No keys copied or exported. OpenCode uses its existing credential store.
    # The V2 run command uses PWD for project discovery. subprocess cwd alone
    # leaves inherited PWD pointing at the source repo: an exact reproduced failure.
    agents=json.loads(call([executable,'debug','agents','--standalone'],cwd=workspace,env=env))
    if not any(x.get('id')=='management-review' and x.get('mode')=='primary' for x in agents):
        raise RuntimeError('NICHT_PRUEFBAR: project review agent not discovered')
    prompt=f'''You are the independent reviewer for {phase}. Read {hp} first, then the COMPLETE EXECUTION_PLAN, SPECs, TEST_PLAN, OPENCODE_REVIEW_PROMPT and workspace/repo AGENTS in the isolated workspace. Verify all hashes and exact HEADs yourself. Read source and diffs. The request lists base SHAs. Execute mandatory tests M00-M02 for MA-0 (or your phase's mandatory set) yourself; write stdout/stderr evidence under {out}. Invent and EXECUTE at least one relevant counterexample outside product trees. Never change product code/tests/specs/AGENTS/configuration, and never touch the original workspace or user services. Use the phase request and TEST_PLAN to select tests. MA-F uses the canonical Compose topology, unique test projects/ports/volumes/private paths, and NO original user credentials or dumps. F0 uses only a temporary one-service PG compatibility probe. No docker-run copy of the application topology. Never mutate tracked files through setup/generation. Use the existing management review-result.example.json schema (binding/reviewer/integrity), extended with phase/check IDs from this handoff; the new consolidation template is illustrative. Phase required IDs are {h['test_selection']['required_checks']}. Report any failure; do not repair it. Write review.md AND review.json under {out}, using the versioned templates/review-result.example.json structure without example_only. Full binding: handoff hash {sha(hp)}, specification hash {h['specification']['aggregate_sha256']}, request hash {h['request']['sha256']}; repositories must be a list of name/head_sha exactly from handoff. Model {MODEL}, CLI version exactly {version}. Determine your own session ID from session context if available; otherwise use SESSION_FROM_RUNNER and the orchestrator will substitute only this transport metadata after completion. checks must use execution EXECUTED; include command,cwd,expected_exit,observed_exit,observation and actual evidence_path. Own counterexample must include command/hypothesis/expected/observed/executed/evidence_path. Include code_review.goal_reached and integrity.product_unchanged. No acceptance without real tests and unchanged product. NICHT_PRUEFBAR if requirements cannot be tested, NACHARBEIT for implementation defects. End after writing both files.'''
    with (run/'events.jsonl').open('w') as events,(run/'stderr.log').open('w') as stderr:
        result=subprocess.run([executable,'run','--standalone','--agent','management-review','--model',MODEL,'--format','json',prompt],cwd=workspace,env=env,stdout=events,stderr=stderr)
    after={r['name']:snapshot(pathlib.Path(r['path'])) for r in h['repositories']}
    (run/'after.json').write_text(json.dumps(after,indent=2))
    events=[json.loads(x) for x in (run/'events.jsonl').read_text().splitlines() if x.strip()]
    sessions={x['sessionID'] for x in events if x.get('sessionID')}
    if len(sessions)!=1:raise RuntimeError('Missing/ambiguous fresh session')
    session=sessions.pop()
    export=call([executable,'session','export','--standalone','--sanitize',session],cwd=workspace,env=env)
    (run/'session.json').write_text(export+'\n')
    session_data=json.loads(export)
    actual_models=[]
    def walk(x):
        if isinstance(x,dict):
            if 'providerID' in x and ('id' in x or 'modelID' in x):actual_models.append(x['providerID']+'/'+x.get('modelID',x.get('id')))
            for v in x.values():walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    walk(session_data)
    tools=[x.get('part',{}) for x in events if x.get('type')=='tool_use']
    def executed(name):return any(t.get('tool')==name and t.get('state',{}).get('status')=='completed' for t in tools)
    runner={'exit_code':result.returncode,'product_unchanged':before==after and original_before=={r['name']:snapshot(WORKSPACE/r['name']) for r in h['repositories']} and original_status=={r['name']:git(WORKSPACE/r['name'],'status','--porcelain') for r in h['repositories']},'actual_provider_model':MODEL if actual_models and set(actual_models)=={MODEL} else 'UNVERIFIED','opencode_version':version,'session_id':session,'read_tool_executed':executed('read'),'shell_tool_executed':executed('shell')}
    (run/'runner.json').write_text(json.dumps(runner,indent=2)+'\n')
    report=out/'review.json'
    if report.exists():
        r=json.loads(report.read_text())
        if r.get('reviewer',{}).get('session_id')=='SESSION_FROM_RUNNER':
            # Preserve original report; only fill transport metadata, never verdict/evidence.
            shutil.copyfile(report,out/'review.original.json')
            r['reviewer']['session_id']=session
            report.write_text(json.dumps(r,indent=2)+'\n')
    print('Review artifacts: '+str(run),flush=True)
    validate(hp,report,runner)
    (run/'ACCEPTED.json').write_text(json.dumps({'handoff_sha256':sha(hp),'report_sha256':sha(report),'runner_sha256':sha(run/'runner.json')},indent=2)+'\n')
    print('ABGENOMMEN '+phase+' '+h['candidate_id'])
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=PHASE_CHECKS);args=parser.parse_args()
    try:execute(args.phase)
    except Exception as e:print('AWAITING_INDEPENDENT_REVIEW / CLOSED: '+str(e),file=sys.stderr);sys.exit(1)
