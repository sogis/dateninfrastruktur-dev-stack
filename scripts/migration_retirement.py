"""Exact-source retirement with private layer/config archives and bounded recovery.
No source volume is removed. Recovery is an explicit operator action, never startup.
"""
import json,os,pathlib,shutil,subprocess
from consolidation import inspect,private_write,digest
from migration_db import verify_source,private_bytes,snapshot,target_sql
from compose_runtime import ROOT

def docker(args):
    result=subprocess.run(['docker',*args],capture_output=True,text=True)
    if result.returncode:
        private_write(ROOT/'.runtime/retirement-error.json',{'command':args,'stdout':result.stdout,'stderr':result.stderr})
        raise RuntimeError('RETIRE_OPERATION_FAILED: private source retained; diagnostic protected under .runtime')
    return result.stdout.strip()
def exists(cid):
    result=subprocess.run(['docker','inspect',cid],capture_output=True,text=True)
    return result.returncode==0

def quiesce(operation,all_sources=False):
    from migration_coordinator import restart_order
    operation.assert_target_binding();plan=operation.plan
    keep=set() if all_sources else {plan['sources'][name]['id'] for name in ['foundation_pg','management_pg','management_garage']}
    states=plan['source_states']
    # Validate the complete selection before stopping the first resource.
    for state in states:verify_source(state['ref'],plan['scope'])
    modes={s['ref']['id']:inspect(s['ref']['id'])['HostConfig']['NetworkMode'] for s in states}
    order=list(reversed(restart_order(states,modes)))
    if not all_sources and plan.get('source_jenkins_sha256'):
        from migration_prepare import jenkins_jobs
        names=jenkins_jobs(plan['source_jenkins_port'],operation.context.values['JENKINS_ADMIN_PASSWORD'],require_idle=True)
        checkpoint=operation.root/'source-jenkins-final.json';private_write(checkpoint,{'names':names});operation.journal['source_jenkins_final_sha256']=digest(checkpoint);operation.save()
        selected={r['id'] for r in plan['source_refs'] if r.get('service')=='jenkins'}
        for _ in states:
            selected|={s['ref']['id'] for s in states if modes[s['ref']['id']].startswith('container:') and modes[s['ref']['id']].split(':',1)[1] in selected}
        order=[s for s in order if s['ref']['id'] in selected]+[s for s in order if s['ref']['id'] not in selected]
    for state in order:
        ref=state['ref'];cid=verify_source(ref,plan['scope'])
        if cid not in keep and inspect(cid)['State']['Running']:docker(['stop','--time','60',cid])
    print('Only explicitly selected source services quiesced; original states recorded; volumes retained')

def bind_backup(source,root):
    """Small mounted configs/JARs are archived; repository directories are retained."""
    source=pathlib.Path(source);copy_directory=any(source.resolve().is_relative_to(p.resolve()) for p in [ROOT/'.runtime',ROOT/'services',ROOT.parent/'dateninfrastruktur-admin/.runtime'])
    if not source.is_file() and not (source.is_dir() and copy_directory):return {'original':str(source),'retained':True}
    key=__import__('hashlib').sha256(str(source).encode()).hexdigest();archive=root/'binds'/key;stage=root/'recovery-binds'/key
    if source.is_file():private_bytes(archive,source.read_bytes());modes={'.':source.stat().st_mode&0o777};hashes={'.':digest(archive)}
    else:
        if not archive.exists():shutil.copytree(source,archive,symlinks=True)
        modes={'.':source.stat().st_mode&0o777};hashes={}
        for original in [source,*source.rglob('*')]:
            relative=str(original.relative_to(source));copied=archive/relative
            if original.is_symlink():raise RuntimeError('BACKUP_FAILED: unexpected runtime/config symlink')
            modes[relative]=original.stat().st_mode&0o777
            if original.is_file():hashes[relative]=digest(copied);copied.chmod(0o600)
            else:copied.chmod(0o700)
    return {'original':str(source),'archive':str(archive),'stage':str(stage),'modes':modes,'hashes':hashes,'directory':source.is_dir()}

def recovery_config(operation,objects,images,platforms,root):
    live_file=operation.root/'source-inspect.json';live={}
    if live_file.exists():
        if operation.plan.get('source_inspect_sha256')!=digest(live_file):raise RuntimeError('SOURCE_CHANGED: original resolved port/config snapshot')
        live=json.loads(live_file.read_text())
    by_id={o['Id']:'source'+str(i) for i,o in enumerate(objects)};services={};volumes={};networks={};binds={}
    for obj in objects:
        cid=obj['Id'];config=obj['Config'];host=obj['HostConfig'];service={'image':images[cid],'platform':platforms[cid],'container_name':obj['Name'].lstrip('/'),'environment':config.get('Env',[]),'labels':{'di.recovery':operation.plan['operation_id']},'restart':host['RestartPolicy']['Name'] or 'no'}
        for name,key in [('entrypoint','Entrypoint'),('command','Cmd'),('user','User'),('working_dir','WorkingDir'),('hostname','Hostname')]:
            if config.get(key):service[name]=config[key]
        if service['restart']=='on-failure' and host['RestartPolicy'].get('MaximumRetryCount'):service['restart']+=':'+str(host['RestartPolicy']['MaximumRetryCount'])
        health=config.get('Healthcheck')
        if health:
            service['healthcheck']={'test':health['Test']}
            for source,target in [('Interval','interval'),('Timeout','timeout'),('StartPeriod','start_period'),('StartInterval','start_interval')]:
                if health.get(source):service['healthcheck'][target]=str(health[source])+'ns'
            if health.get('Retries'):service['healthcheck']['retries']=health['Retries']
        mounts=[]
        for mount in obj['Mounts']:
            destination=mount['Destination'];kind=mount['Type']
            if kind=='volume':
                key='volume'+str(len(volumes))
                previous=next((k for k,v in volumes.items() if v['name']==mount['Name']),None);key=previous or key
                volumes[key]={'external':True,'name':mount['Name']};source=key
            elif kind=='bind':
                name=mount['Source']
                if name not in binds:binds[name]=bind_backup(name,root)
                source=binds[name].get('stage',name)
            elif kind=='tmpfs':continue
            else:raise RuntimeError('BACKUP_FAILED: unsupported selected source mount type')
            mounts.append({'type':kind,'source':source,'target':destination,'read_only':not mount['RW']})
        if mounts:service['volumes']=mounts
        if host.get('Tmpfs'):service['tmpfs']=[name+':'+options for name,options in host['Tmpfs'].items()]
        mode=host['NetworkMode']
        if mode.startswith('container:'):
            parent=mode.split(':',1)[1];parents=[o['Id'] for o in objects if o['Id']==parent or o['Name'].lstrip('/')==parent]
            if len(parents)!=1:raise RuntimeError('OWNERSHIP_MISMATCH: unselected namespace parent')
            service['network_mode']='service:'+by_id[parents[0]]
            service.pop('hostname',None)
        else:
            attached={}
            for name,data in obj['NetworkSettings']['Networks'].items():
                key=next((k for k,v in networks.items() if v['name']==name),None) or 'network'+str(len(networks));networks[key]={'external':True,'name':name};attached[key]={'aliases':data.get('Aliases') or []}
            if attached:service['networks']=attached
            elif mode in ['none','host','bridge']:service['network_mode']=mode
            else:raise RuntimeError('BACKUP_FAILED: unknown selected source network mode')
        ports=[]
        for container,bindings in (host.get('PortBindings') or {}).items():
            port,protocol=container.split('/')
            for binding in bindings or []:
                selected=[binding]
                if not binding.get('HostPort') or binding['HostPort']=='0':
                    resolved=live.get(cid,obj).get('NetworkSettings',{}).get('Ports',{}).get(container) or []
                    selected=[b for b in resolved if b.get('HostPort') and (not binding.get('HostIp') or b.get('HostIp')==binding['HostIp'])]
                    if not selected:raise RuntimeError('BACKUP_FAILED: original dynamically assigned source port was not preserved')
                for actual in selected:ports.append({'target':int(port),'published':actual['HostPort'],'host_ip':actual.get('HostIp') or '0.0.0.0','protocol':protocol})
        if ports:
            if 'network_mode' in service and service['network_mode'].startswith('service:'):raise RuntimeError('BACKUP_FAILED: namespace child unexpectedly publishes ports')
            service['ports']=ports
        for name,key in [('extra_hosts','ExtraHosts'),('cap_add','CapAdd'),('cap_drop','CapDrop'),('security_opt','SecurityOpt'),('dns','Dns'),('dns_search','DnsSearch')]:
            if host.get(key):service[name]=host[key]
        if host.get('Privileged'):service['privileged']=True
        if host.get('ReadonlyRootfs'):service['read_only']=True
        if host.get('ShmSize'):service['shm_size']=host['ShmSize']
        for source,target in [('Memory','mem_limit'),('MemoryReservation','mem_reservation'),('PidsLimit','pids_limit')]:
            if host.get(source):service[target]=host[source]
        if host.get('NanoCpus'):service['cpus']=host['NanoCpus']/1000000000
        services[by_id[cid]]=service
    file=root/'recovery.compose.json'
    def literal(value):
        if isinstance(value,str):return value.replace('$','$$')
        if isinstance(value,list):return [literal(v) for v in value]
        if isinstance(value,dict):return {k:literal(v) for k,v in value.items()}
        return value
    private_write(file,literal({'services':services,'volumes':volumes,'networks':networks}))
    return file,list(binds.values()),by_id

def backup_layers(operation):
    operation.assert_target_binding();root=operation.root/'retirement';root.mkdir(exist_ok=True);root.chmod(0o700)
    manifest=root/'manifest.json'
    if manifest.exists():return verify_backup(operation)
    refs=operation.plan['source_refs'];objects=[]
    for ref in refs:
        obj=inspect(verify_source(ref,operation.plan['scope']))
        if obj['State']['Running']:raise RuntimeError('SOURCE_NOT_QUIESCED: layer backup requires stopped source')
        objects.append(obj)
    private_write(root/'source-inspect.json',objects)
    images={};archives={};platforms={}
    import hashlib,tarfile
    for obj in objects:
        cid=obj['Id'];verify_source(next(r for r in refs if r['id']==cid),operation.plan['scope'])
        platform=obj.get('ImageManifestDescriptor',{}).get('platform')
        if not platform:
            image=json.loads(docker(['image','inspect',obj['Image']]))[0];platform={'os':image['Os'],'architecture':image['Architecture'],'variant':image.get('Variant')}
        platform='/'.join(platform[k] for k in ['os','architecture','variant'] if platform.get(k));platforms[cid]=platform
        archive=root/(cid+'.rootfs.tar');temporary=root/(cid+'.rootfs.partial')
        docker(['container','export','--output',str(temporary),cid]);temporary.chmod(0o600);os.replace(temporary,archive)
        if cid==operation.plan['sources']['management_keycloak']['id']:
            original=json.loads((operation.root/'keycloak-original-manifest.json').read_text())
            with tarfile.open(archive) as tar:
                files={m.name.lstrip('./'):m for m in tar.getmembers() if m.isfile()}
                for name,expected in original['files'].items():
                    if not name.endswith('.mv.db'):continue
                    member=files.get('opt/keycloak/data/'+name)
                    if member is None or hashlib.sha256(tar.extractfile(member).read()).hexdigest()!=expected:raise RuntimeError('BACKUP_FAILED: exported writable H2 bytes differ from the verified current backup')
        images[cid]='dateninfrastruktur-legacy-backup:'+operation.plan['operation_id'].replace('-','')[:12]+'-'+cid[:12]
        archives[cid]={'path':str(archive),'sha256':digest(archive),'platform':platform,'image':images[cid]}
    recovery,binds,services_by_source=recovery_config(operation,objects,images,platforms,root)
    retained={name:json.loads(docker(['volume','inspect',name]))[0] for name in sorted({m['Name'] for o in objects for m in o['Mounts'] if m['Type']=='volume'})}
    result={'operation_id':operation.plan['operation_id'],'source_ids':sorted(images),'images':images,'services_by_source':services_by_source,'archives':archives,'inspect_path':str(root/'source-inspect.json'),'inspect_sha256':digest(root/'source-inspect.json'),'recovery_file':str(recovery),'recovery_sha256':digest(recovery),'binds':binds,'retained_volumes':retained}
    private_write(manifest,result);operation.journal['retirement_manifest_sha256']=digest(manifest);operation.save();return result

def verify_backup(operation):
    path=operation.root/'retirement/manifest.json'
    if not path.exists() or operation.journal.get('retirement_manifest_sha256')!=digest(path):raise RuntimeError('BACKUP_FAILED: missing or changed layer manifest')
    value=json.loads(path.read_text())
    if value['operation_id']!=operation.plan['operation_id'] or value['source_ids']!=sorted(r['id'] for r in operation.plan['source_refs']):raise RuntimeError('OWNERSHIP_MISMATCH: archived source selection')
    for archive in value['archives'].values():
        if digest(archive['path'])!=archive['sha256']:raise RuntimeError('BACKUP_FAILED: exported filesystem checksum mismatch')
    for path_key,hash_key in [('inspect_path','inspect_sha256'),('recovery_file','recovery_sha256')]:
        if digest(value[path_key])!=value[hash_key]:raise RuntimeError('BACKUP_FAILED: archive/config checksum mismatch')
    for bind in value['binds']:
        for relative,sha in bind.get('hashes',{}).items():
            file=pathlib.Path(bind['archive']) if not bind['directory'] else pathlib.Path(bind['archive'])/relative
            if digest(file)!=sha:raise RuntimeError('BACKUP_FAILED: mounted configuration checksum')
    for name,original in value['retained_volumes'].items():
        current=json.loads(docker(['volume','inspect',name]))[0]
        if any(current.get(k)!=original.get(k) for k in ['Name','Driver','CreatedAt','Labels','Options','Mountpoint']):raise RuntimeError('OWNERSHIP_MISMATCH: retained volume identity')
    return value

def retire(operation):
    operation.assert_target_binding()
    if operation.journal['status'] not in ['CUTOVER','RETIRED']:raise RuntimeError('VERIFICATION_FAILED: cutover required before retirement')
    expected={r['id'] for r in operation.plan['source_refs']}
    if set(operation.plan.get('retire_allowlist',[]))!=expected:raise RuntimeError('OWNERSHIP_MISMATCH: retire allowlist must match the complete planned sources')
    backup=verify_backup(operation)
    removed=set(operation.journal.get('retired_source_ids',[]))
    for ref in operation.plan['source_refs']:
        if not exists(ref['id']):
            if not operation.journal.get('retirement_started'):raise RuntimeError('SOURCE_CHANGED: source disappeared before retirement')
            removed.add(ref['id']);continue
        cid=verify_source(ref,operation.plan['scope'])
        if inspect(cid)['State']['Running']:raise RuntimeError('SOURCE_NOT_QUIESCED: never force-remove a running source')
    if operation.journal['status']!='RETIRED':
        from migration_lifecycle import verify_services
        verify_services(operation)
    operation.journal['retirement_started']=True;operation.save()
    for ref in operation.plan['source_refs']:
        if ref['id'] in removed:continue
        cid=verify_source(ref,operation.plan['scope']);docker(['update','--restart=no',cid]);docker(['rm',cid]);removed.add(cid)
        operation.journal['retired_source_ids']=sorted(removed);operation.save()
    verify_backup(operation);operation.save('RETIRED')
    print('Retired only exact archived sources; all original named/anonymous volumes and protected filesystem/config archives retained')

def recover_retired(operation):
    # This guard runs before stopping the target or creating any recovery service.
    operation.assert_target_binding();expected=operation.journal.get('target_management_baseline')
    if not expected or snapshot(lambda db,q:target_sql(operation.context,db,q),'dateninfrastruktur_management')!=expected:raise RuntimeError('ROLLBACK_UNSAFE: target writes require explicit backup and reconciliation')
    backup=verify_backup(operation)
    for ref in operation.plan['source_refs']:
        if exists(ref['id']):raise RuntimeError('OWNERSHIP_MISMATCH: retired source unexpectedly still exists')
        names=docker(['ps','-aq','--no-trunc','--filter','name=^'+ref['name']+'$'])
        if names:raise RuntimeError('OWNERSHIP_MISMATCH: original source name is now in use')
    # Restore mount access modes only in private recovery staging, never in archives.
    for bind in backup['binds']:
        if bind.get('retained'):continue
        source=pathlib.Path(bind['archive']);stage=pathlib.Path(bind['stage']);stage.parent.mkdir(parents=True,exist_ok=True);stage.parent.chmod(0o700)
        if bind['directory']:
            if stage.exists():shutil.rmtree(stage)
            shutil.copytree(source,stage)
            for relative,mode in bind['modes'].items():(stage/relative).chmod(mode)
        else:shutil.copyfile(source,stage);stage.chmod(bind['modes']['.'])
    for cid,archive in backup['archives'].items():
        wanted={'di.recovery':operation.plan['operation_id'],'di.source-container':cid,'di.filesystem-sha256':archive['sha256']}
        result=subprocess.run(['docker','image','inspect',archive['image']],capture_output=True,text=True)
        if result.returncode:
            args=['image','import','--platform',archive['platform']]
            for key,value in wanted.items():args+=['--change','LABEL '+key+'='+value]
            docker([*args,archive['path'],archive['image']])
        image=json.loads(docker(['image','inspect',archive['image']]))[0]
        if any((image['Config'].get('Labels') or {}).get(k)!=v for k,v in wanted.items()):raise RuntimeError('TARGET_NOT_EMPTY: recovery image tag belongs to another source or archive')
    project='di-recovery-'+operation.plan['operation_id'].replace('-','')[:16]
    operation.journal['recovery_project']=project;operation.journal['recovery_started']=True;operation.save()
    from migration_lifecycle import block_target_start
    block_target_start(operation)
    operation.context.command(['stop','--timeout','60'])
    base=['compose','--project-name',project,'--file',backup['recovery_file']]
    running={s['ref']['id'] for s in operation.plan['source_states'] if s['running']}
    backends=[operation.plan['sources'][name]['id'] for name in ['foundation_pg','management_pg','management_garage']]
    backend_services=[backup['services_by_source'][cid] for cid in backends if cid in running]
    if backend_services:docker([*base,'up','--no-build','-d','--wait','--wait-timeout','180',*backend_services])
    import time
    for cid in backends[:2]:
        if cid not in running:continue
        for attempt in range(60):
            result=subprocess.run(['docker',*base,'exec','-T',backup['services_by_source'][cid],'pg_isready','-U','postgres'],capture_output=True)
            if result.returncode==0:break
            time.sleep(.5)
        else:raise RuntimeError('ROLLBACK_FAILED: archived source database is not ready')
    services=[backup['services_by_source'][cid] for cid in running]
    if services:docker([*base,'up','--no-build','-d','--wait','--wait-timeout','300',*services])
    operation.journal['recovery_project']=project;operation.save('ROLLED_BACK_RECONSTRUCTED')
    print('Original legacy configuration reconstructed from verified filesystem exports/configs/mounts; target retained stopped; no volume deleted')
