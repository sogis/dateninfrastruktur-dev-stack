#!/usr/bin/env python3
"""Explicit offline retirement using the single owned Compose Jenkins volume."""
import argparse,json,pathlib,subprocess,uuid
from compose_operations import ACTIVE,resolve

def run(context,action,name):
    context.verify_project();volume=context.values['JENKINS_VOLUME']
    info=json.loads(subprocess.check_output(['docker','volume','inspect',volume],text=True))[0]
    labels=info.get('Labels') or {}
    if info['Name']!=volume or labels.get('com.docker.compose.volume')!='jenkins-home':raise RuntimeError('Unverified Jenkins volume ownership')
    attached=subprocess.check_output(['docker','ps','-aq','--filter','volume='+volume],text=True).split()
    if len(attached)!=1:raise RuntimeError('Exactly one identified Jenkins container must own the selected volume')
    container=json.loads(subprocess.check_output(['docker','inspect',attached[0]],text=True))[0]
    owner=container['Config'].get('Labels') or {}
    if owner.get('com.docker.compose.project')!=context.project or owner.get('com.docker.compose.service')!='jenkins' or owner.get('di.instance')!=context.values['INSTANCE_ID'] or not any(m.get('Name')==volume and m.get('Destination')=='/var/jenkins_home' for m in container['Mounts']):
        raise RuntimeError('Jenkins volume is attached to a different container')
    if container['State']['Running']:raise RuntimeError('Stop the identified Jenkins service before planning/applying retirement')
    if labels.get('com.docker.compose.project')!=context.project:
        # The previously consolidated local project may retain its original Compose volume label.
        # This exception is accepted only with the retained migration and active bindings.
        if context.values.get('JENKINS_VOLUME_EXTERNAL')!='true' or not ACTIVE.is_file():raise RuntimeError('Unverified retained Jenkins volume')
        active=json.loads(ACTIVE.read_text());setup=json.loads((context.runtime/'setup-complete.json').read_text())
        if active.get('env')!=str(context.env_file) or active.get('project')!=context.project or active.get('instance')!=context.values['INSTANCE_ID'] or setup.get('instance')!=active['instance'] or setup.get('volumes',{}).get('JENKINS_VOLUME')!=volume or not active.get('migration_plan'):
            raise RuntimeError('Active retained Jenkins volume binding missing')
        plan_path=pathlib.Path(active['migration_plan']).resolve()
        if not plan_path.is_relative_to(ACTIVE.parent.resolve()):raise RuntimeError('Retained migration plan must be private to this workspace')
        plan=json.loads(plan_path.read_text())
        if plan.get('target_project')!=context.project or plan.get('target_instance')!=active['instance'] or volume not in plan.get('retained_volumes',[]):
            raise RuntimeError('Jenkins volume was not included in the bound retained set')
    mount=volume+':/jenkins-home'+(':ro' if action=='plan' else '')
    return context.command(['--profile','setup','run','--rm','--no-deps','--volume',mount,'-e','DI_RETIRE_INSTANCE='+context.values['INSTANCE_ID'],'-e','DI_RETIRE_VOLUME='+volume,'--entrypoint','python3','management-setup','/opt/stack-tools/migration/retire_jenkins_g3.py',action,name]).stdout.strip()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['plan','apply']);p.add_argument('--file');p.add_argument('--env');p.add_argument('--project');a=p.parse_args();c=resolve(a.env,a.project)
    if a.action=='plan':name='jenkins-retirement-'+str(uuid.uuid4())+'.json'
    else:
        if not a.file:raise RuntimeError('Explicit bound plan file required')
        path=pathlib.Path(a.file).resolve()
        if path.parent!=c.runtime:raise RuntimeError('Plan must belong to selected private runtime')
        name=path.name
    print(run(c,a.action,name));print(c.runtime/name)
