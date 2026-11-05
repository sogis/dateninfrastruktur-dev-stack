#!/usr/bin/env python3
"""Public lifecycle: one explicit Compose context, no legacy runtime or implicit seed."""
import argparse,json,pathlib,sys,os,subprocess
from compose_runtime import ROOT,ComposeContext,init_context,setup_context,read_env,render
from consolidation import private_write
ACTIVE=ROOT/'.runtime/active-compose.json'

def activate(context,plan=None):
    context.verify_project()
    private_write(ACTIVE,{'env':str(context.env_file),'instance':context.values['INSTANCE_ID'],'project':context.project,'migration_plan':str(plan) if plan else None})

def resolve(env=None,project=None,create=False):
    if env:
        path=pathlib.Path(env).resolve()
        if not path.exists():
            if not create or path.name!='runtime.env' or path.parent.parent!=(ROOT/'.runtime').resolve():raise RuntimeError('Explicit environment does not exist; use init with a project runtime.env')
            c=init_context(project or path.parent.name)
            if c.env_file!=path:raise RuntimeError('Project/environment mismatch')
            return c
        c=ComposeContext(path)
    elif project:
        path=ROOT/'.runtime'/project/'runtime.env'
        c=init_context(project) if create else ComposeContext(path)
    elif ACTIVE.exists():
        active=json.loads(ACTIVE.read_text());c=ComposeContext(active['env'])
        if active['instance']!=c.values['INSTANCE_ID'] or active['project']!=c.project:raise RuntimeError('OWNERSHIP_MISMATCH: active Compose binding')
    elif create:c=init_context('dateninfrastruktur-dev-stack')
    else:raise RuntimeError('No active Compose context. Use init/setup for a fresh instance or the explicit migration plan for existing data.')
    if project and project!=c.project:raise RuntimeError('OWNERSHIP_MISMATCH: project/environment differ')
    c.verify_project();return c

def build(c):
    c.command(['build','admin','sodata','management-tool-build','superset']+(['test-tool-build'] if c.values['DI_TEST_FIXTURE']=='true' else []))

def volume_bindings(c):
    return {k:c.values[k] for k in ['POSTGRES_VOLUME','GARAGE_META_VOLUME','GARAGE_DATA_VOLUME','JENKINS_VOLUME','CLICKHOUSE_DATA_VOLUME','CLICKHOUSE_LOG_VOLUME','SUPERSET_VOLUME']}

def setup(c):
    # An existing management database is verified by the explicit tool, never
    # passed through initial role creation, ClickHouse seeding or model import.
    if c.values.get('DI_STORAGE_BUCKET')!='ch.so.daten':raise RuntimeError('Explicit reviewed MA-G storage cutover required; normal setup never migrates existing storage')
    c.command(['up','--no-build','-d','--wait','--wait-timeout','240','postgres'])
    q="SELECT count(*) FROM pg_database WHERE datname='dateninfrastruktur_management';"
    count=c.command(['exec','-T','postgres','psql','-X','-q','-At','-U','postgres','-d','postgres','-c',q]).stdout.strip()
    fresh=count=='0' and not (c.runtime/'setup-complete.json').exists()
    if (c.runtime/'setup-complete.json').exists():
        if count!='1':raise RuntimeError('Known management database is missing; retained setup must not create an empty replacement')
        c.command(['--profile','setup','run','--rm','--no-deps','management-setup','verify'])
    elif count=='0':setup_context(c)
    else:c.command(['--profile','setup','run','--rm','--no-deps','management-setup'])
    if not fresh:
        c.command(['up','--no-build','-d','--wait','--wait-timeout','120','garage'])
        c.command(['--profile','setup','run','--rm','--no-deps','garage-setup'])
        c.values=read_env(c.env_file);render(c)
    private_write(c.runtime/'setup-complete.json',{'instance':c.values['INSTANCE_ID'],'mode':'explicit-setup','volumes':volume_bindings(c)})

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['init','build','setup','up','stop','down','restart','status','logs'])
    p.add_argument('--env');p.add_argument('--project');p.add_argument('--skip-build',action='store_true');p.add_argument('--build-only',action='store_true')
    p.add_argument('--follow',action='store_true');p.add_argument('--tail',type=int,default=100);p.add_argument('services',nargs='*');a=p.parse_args()
    if a.services and a.action!='logs':p.error('Service selection is supported only for logs')
    if a.build_only and a.action!='up':p.error('--build-only requires up')
    if a.action in ['init','setup','up','restart'] and (ROOT/'.runtime/active-recovery.json').exists():raise RuntimeError('An explicit rollback is active; target startup requires source/target reconciliation')
    c=resolve(a.env,a.project,a.action=='init')
    if a.action in ['setup','up','restart'] and c.values.get('DI_STORAGE_BUCKET')!='ch.so.daten':raise RuntimeError('Explicit reviewed MA-G storage cutover required; no legacy startup fallback')
    if a.action in ['init','setup','up','restart'] and (c.runtime/'rollback-active.json').exists():raise RuntimeError('An explicit rollback is active for this target; startup is blocked')
    if a.action=='init':
        if not a.env and not a.project and not ACTIVE.exists():activate(c)
        print('Private Compose configuration retained: '+c.project);return
    marker=c.runtime/'setup-complete.json'
    if a.action in ['setup','up','restart'] and marker.exists():
        expected=json.loads(marker.read_text()).get('volumes')
        if expected and expected!=volume_bindings(c):raise RuntimeError('OWNERSHIP_MISMATCH: persistent volume mapping changed; explicit migration required')
    if (a.action=='restart' or (a.action=='up' and not a.build_only)) and not marker.exists():raise RuntimeError('Explicit setup or verified migration is required; normal start never seeds an empty replacement')
    if a.action=='restart' or (a.action=='up' and not a.build_only):
        if c.values.get('JENKINS_IMAGE')!='sha256:'+c.values.get('DI_JENKINS_IMAGE_SHA256','') or len(c.values.get('DI_JENKINS_IMAGE_SHA256',''))!=64:
            raise RuntimeError('Bind the locally built CSV candidate with scripts/bind_jenkins_image.py before starting the stack')
    if a.action in ['build','setup'] or (a.action=='up' and not a.skip_build):build(c)
    if a.build_only:
        return
    if a.action=='setup':setup(c)
    elif a.action=='up':c.command(['up','--no-build','-d','--wait','--wait-timeout','300'])
    elif a.action=='stop':c.command(['stop','--timeout','60'])
    elif a.action=='down':c.command(['down','--timeout','60'])
    elif a.action=='restart':
        c.command(['stop','--timeout','60']);c.command(['up','--no-build','-d','--wait','--wait-timeout','300'])
    elif a.action=='status':
        rows=[json.loads(line) for line in c.command(['ps','--format','json']).stdout.splitlines()]
        for row in rows:print(row['Service']+' '+row['State']+' '+row.get('Health',''))
        print('Gateway: http://localhost:'+c.values['GATEWAY_PORT']+'/')
        print('Keycloak: http://localhost:'+c.values['KEYCLOAK_PORT']+'/')
        print('Superset: http://localhost:'+c.values['SUPERSET_PORT']+'/')
    elif a.action=='logs':
        # Runtime logs can contain user input; always redact configured secrets.
        args=['logs','--tail',str(a.tail)]+(['--follow'] if a.follow else [])+a.services
        if a.follow:
            env={k:os.environ[k] for k in ['PATH','HOME','DOCKER_HOST','DOCKER_CONTEXT','DOCKER_CONFIG'] if k in os.environ};env.update(c.values)
            process=subprocess.Popen(c.base+args,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            for line in process.stdout:print(c.redact(line),end='',flush=True)
            if process.wait():raise RuntimeError('Compose log stream failed')
        else:print(c.redact(c.command(args).stdout),end='')
if __name__=='__main__':
    try:main()
    except Exception as error:
        print(str(error) if isinstance(error,RuntimeError) else 'Compose operation failed; private configuration retained',file=sys.stderr);sys.exit(1)
