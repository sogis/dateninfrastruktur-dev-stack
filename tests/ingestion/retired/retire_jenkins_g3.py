#!/usr/bin/env python3
"""Stopped-volume worker: archive only exactly marker-bound legacy jobs, retain their bytes."""
import argparse,hashlib,json,os,pathlib,re,stat,uuid,xml.etree.ElementTree as ET

PREFIX='ch.so.agi.jenkins.gretldatenportal.'
ORG=PREFIX+'GretlDatenportalManagedJobProperty'
SEED=PREFIX+'GretlDatenportalManagedSeedJobProperty'
SEED_NAME='gretl-datenportal-seed'
JOB_NAME='di-csv-ingest'
GLOBAL=PREFIX+'GretlDatenportalGlobalConfiguration'
LOCK='org.jenkins.plugins.lockableresources.LockableResourcesManager'
LOCAL_USERS={'admin','seed-user','read-user','agi-user','mfk-user','statistikdienst-user'}
OLD_REALM='hudson.security.HudsonPrivateSecurityRealm'
OLD_LOCK='datenportal-topic-repository'
SAFE=re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z')
JENKINS_VOLUME_ROOT=pathlib.Path('/jenkins-home')
RUNTIME=pathlib.Path('/runtime')

def digest(file):
    h=hashlib.sha256()
    with file.open('rb') as source:
        for chunk in iter(lambda:source.read(65536),b''):h.update(chunk)
    return h.hexdigest()
def regular(path):return not path.is_symlink() and path.is_file()
def marker(name,path):
    if not regular(path) or path.stat().st_size>1048576:return None
    root=ET.parse(path).getroot();properties=root.find('properties')
    if properties is None:return None
    props=[p.get('class',p.tag) for p in properties]
    if root.tag=='project' and name==SEED_NAME and props.count(SEED)==1:return 'seed'
    if root.tag=='flow-definition' and props.count(ORG)==1 and name!=JOB_NAME and SAFE.fullmatch(name):return 'organization'
    return None

def inventory(home):
    root=home/'jobs'
    if root.is_symlink():raise RuntimeError('Jenkins job root must not be a symlink')
    out={}
    for item in sorted(root.iterdir()) if root.is_dir() else []:
        cfg=item/'config.xml'
        if item.is_symlink():raise RuntimeError('Unexpected symlink in stopped Jenkins job root')
        if not item.is_dir():continue
        if not regular(cfg):raise RuntimeError('Unknown job configuration; no retirement')
        try:owned=marker(item.name,cfg)
        except ET.ParseError:owned=None
        out[item.name]={'configSha256':digest(cfg),'legacyMarker':owned}
    return out

def xml(path):
    if not regular(path) or path.stat().st_size>1048576:
        raise RuntimeError('Unverified Jenkins XML asset')
    return ET.parse(path).getroot()

def old_assets(home):
    global_path=home/(GLOBAL+'.xml')
    if not global_path.exists() and not global_path.is_symlink():
        return {}
    previous=xml(global_path)
    realm=xml(home/'config.xml').find('securityRealm')
    if previous.tag!=GLOBAL or previous.findtext('urlName')!='gretl-datenportal' or realm is None or realm.get('class')!=OLD_REALM:
        raise RuntimeError('Previous Jenkins configuration ownership not established')
    paths=[global_path]
    locks=home/(LOCK+'.xml')
    if locks.exists() or locks.is_symlink():
        body=xml(locks)
        resources=body.find('resources')
        if body.tag!=LOCK or resources is None or [x.findtext('name') for x in resources]!=[OLD_LOCK] or len(body.find('remotes') or []) or len(body.find('queuedContexts') or []):
            raise RuntimeError('Lock manager contains unrelated state; scoped retirement required')
        paths.append(locks)
    old_casc=home/'casc_configs/jenkins.yaml'
    if old_casc.exists() or old_casc.is_symlink():
        if (home/'casc_configs').is_symlink() or not regular(old_casc) or old_casc.stat().st_size>1048576:
            raise RuntimeError('Old JCasC path is unverified')
        text=old_casc.read_text()
        if not all(word in text for word in (OLD_LOCK,'gretl-datenportal','securityRealm:','local:')):
            raise RuntimeError('Old JCasC content is unverified')
        paths.append(old_casc)
    user_dir=home/'users'
    if user_dir.is_symlink():
        raise RuntimeError('Unexpected Jenkins user directory link')
    for path in sorted(user_dir.iterdir()) if user_dir.is_dir() else ():
        if not path.is_dir() or path.is_symlink():
            continue
        cfg=path/'config.xml'
        if not regular(cfg):
            continue
        account=xml(cfg)
        if account.findtext('id') in LOCAL_USERS:
            if account.tag!='user' or account.find('properties/'+OLD_REALM+'_-Details') is None:
                raise RuntimeError('Matching Jenkins ID lacks the previous local realm marker')
            paths.append(path)
    cache=home/'gretl-datenportal'
    if cache.exists() or cache.is_symlink():
        if not cache.is_dir() or cache.is_symlink():
            raise RuntimeError('Previous plugin cache is not a directory')
        paths.append(cache)
    workspace=home/'workspace'/SEED_NAME
    if workspace.exists() or workspace.is_symlink():
        if (home/'workspace').is_symlink() or not workspace.is_dir() or workspace.is_symlink() or marker(SEED_NAME,home/'jobs'/SEED_NAME/'config.xml')!='seed':
            raise RuntimeError('Previous seed workspace has no owning job')
        paths.append(workspace)
    return {p.relative_to(home).as_posix():tree_hash(p,home.stat().st_dev) for p in paths}

def tree_hash(root, device):
    h=hashlib.sha256()
    def visit(path):
        mode=path.lstat()
        if mode.st_dev!=device:
            raise RuntimeError('Retirement may not cross a filesystem boundary')
        if stat.S_ISLNK(mode.st_mode):
            kind,value='link',os.readlink(path)
        elif stat.S_ISDIR(mode.st_mode):
            kind,value='directory',None
        elif stat.S_ISREG(mode.st_mode):
            kind,value='file',digest(path)
        else:
            raise RuntimeError('Unexpected non-file Jenkins asset')
        h.update(json.dumps([path.relative_to(root).as_posix(),kind,value,stat.S_IMODE(mode.st_mode)],ensure_ascii=True).encode()+b'\n')
        if kind=='directory':
            for child in sorted(path.iterdir()):visit(child)
    visit(root)
    return h.hexdigest()

def plan(home,instance,volume):
    current=inventory(home)
    if JOB_NAME in current:raise RuntimeError('New CSV job name is already occupied; no legacy conversion')
    return {'schemaVersion':2,'planId':str(uuid.uuid4()),'instance':instance,'volume':volume,'inventory':current,'assets':old_assets(home)}

def private_directory(path,owner=None):
    if path.is_symlink():raise RuntimeError('Refusing symlink in private retirement path')
    try:
        path.mkdir(mode=0o700)
        if owner:os.chown(path,*owner)
    except FileExistsError:pass
    if not path.is_dir() or stat.S_IMODE(path.stat().st_mode)!=0o700:raise RuntimeError('Private retirement directory required')

def apply(home,p,instance,volume):
    if p.get('schemaVersion')!=2 or p.get('instance')!=instance or p.get('volume')!=volume:raise RuntimeError('Wrong Jenkins retirement binding')
    id=str(uuid.UUID(p['planId']));expected=p['inventory'];current=inventory(home)
    root=home/'data-infrastructure';destination=root/'retired'/('legacy-'+id)/'jobs';assets=destination.parent/'assets'
    for ancestor in (root,root/'retired',destination.parent,destination):
        if ancestor.is_symlink() or (ancestor.exists() and (not ancestor.is_dir() or stat.S_IMODE(ancestor.stat().st_mode)!=0o700)):
            raise RuntimeError('Private non-symlink retirement path required')
    if JOB_NAME in expected or not set(current)<=set(expected):raise RuntimeError('Job inventory changed; no retirement')
    # Preflight the complete planned set before moving any item, including resumed items.
    for name,row in expected.items():
        if not isinstance(name,str) or name in ('.','..') or '/' in name or '\x00' in name:raise RuntimeError('Invalid inventory name')
        target=destination/name
        if target.is_symlink():raise RuntimeError('Unexpected symlink in archive')
        if name in current:
            if current[name]!=row or (destination/name).exists():raise RuntimeError('Job inventory changed; no retirement')
        else:
            archived=destination/name/'config.xml'
            if not row['legacyMarker'] or not regular(archived) or digest(archived)!=row['configSha256'] or marker(name,archived)!=row['legacyMarker']:raise RuntimeError('Missing or changed job inventory; no retirement')
    device=home.stat().st_dev
    expected_assets=p['assets']
    if expected_assets:
        global_source=home/(GLOBAL+'.xml')
        global_archived=assets/(GLOBAL+'.xml')
        old_global=xml(global_source if global_source.exists() else global_archived)
        old_realm=xml(home/'config.xml').find('securityRealm')
        if old_global.tag!=GLOBAL or old_global.findtext('urlName')!='gretl-datenportal' or old_realm is None or old_realm.get('class')!=OLD_REALM:
            raise RuntimeError('Previous Jenkins ownership proof lost')
        if global_source.exists() and all((home/name).exists() for name in expected_assets) and old_assets(home)!=expected_assets:
            raise RuntimeError('Previous Jenkins asset selection changed; no retirement')
    for name,wanted in expected_assets.items():
        parts=pathlib.PurePosixPath(name).parts
        allowed=(name in {GLOBAL+'.xml',LOCK+'.xml','casc_configs/jenkins.yaml','gretl-datenportal','workspace/'+SEED_NAME}
                 or (len(parts)==2 and parts[0]=='users' and SAFE.fullmatch(parts[1])))
        if not allowed or '..' in parts:
            raise RuntimeError('Invalid retirement asset')
        source=home/name;archived=assets/name
        for parent in (source.parent,archived.parent,assets):
            if parent.is_symlink():raise RuntimeError('Unexpected link in retirement asset path')
        source_exists=source.exists() or source.is_symlink()
        archive_exists=archived.exists() or archived.is_symlink()
        selected=source if source_exists else archived
        if source_exists==archive_exists or tree_hash(selected,device)!=wanted:
            raise RuntimeError('Jenkins asset inventory changed; no retirement')
        if parts[0]=='users':
            account=xml(selected/'config.xml')
            if account.tag!='user' or account.findtext('id') not in LOCAL_USERS or account.find('properties/'+OLD_REALM+'_-Details') is None:
                raise RuntimeError('Jenkins asset is not an owned old local account')
    if not any(row['legacyMarker'] for row in expected.values()) and not expected_assets:return 0
    uid,gid=home.stat().st_uid,home.stat().st_gid
    private_directory(root,(uid,gid));private_directory(root/'retired');private_directory(destination.parent);private_directory(destination)
    moved=0
    for name,row in expected.items():
        if not row['legacyMarker'] or name not in current:continue
        source=home/'jobs'/name;target=destination/name
        if not SAFE.fullmatch(name) or marker(name,source/'config.xml')!=row['legacyMarker'] or digest(source/'config.xml')!=row['configSha256'] or target.exists():raise RuntimeError('Legacy marker/hash changed; no move')
        os.rename(source,target);moved+=1
    if expected_assets:
        private_directory(assets)
        for name in expected_assets:
            source=home/name;archived=assets/name
            if archived.parent!=assets:private_directory(archived.parent)
            if source.exists() or source.is_symlink():
                os.rename(source,archived)
            if tree_hash(archived,device)!=expected_assets[name]:
                raise RuntimeError('Archived Jenkins asset changed')
        fd=os.open(assets,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
    for directory in (destination,home/'jobs'):
        fd=os.open(directory,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
    remaining=inventory(home)
    if remaining!={k:v for k,v in expected.items() if not v['legacyMarker']}:raise RuntimeError('Unexpected remaining job inventory')
    return moved

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['plan','apply']);p.add_argument('file');a=p.parse_args()
    file=RUNTIME/pathlib.Path(a.file).name
    if not re.fullmatch(r'jenkins-retirement-[0-9a-f-]{36}\.json',file.name):raise RuntimeError('Explicit private plan name required')
    instance=os.environ['DI_RETIRE_INSTANCE'];volume=os.environ['DI_RETIRE_VOLUME']
    if a.action=='plan':
        data=plan(JENKINS_VOLUME_ROOT,instance,volume);data['planId']=file.name.removeprefix('jenkins-retirement-').removesuffix('.json')
        fd=os.open(file,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as out:json.dump(data,out,indent=2);out.write('\n');out.flush();os.fsync(out.fileno())
        print('Planned '+str(sum(bool(x['legacyMarker']) for x in data['inventory'].values()))+' marker-bound jobs and '+str(len(data['assets']))+' legacy assets; no volume write')
    else:
        if not regular(file) or file.stat().st_mode&0o077 or file.stat().st_size>1048576:raise RuntimeError('Private bound retirement plan required')
        data=json.loads(file.read_text())
        print('Archived '+str(apply(JENKINS_VOLUME_ROOT,data,instance,volume))+' owned jobs; verified '+str(len(data['assets']))+' retired assets; retained complete histories and unrelated jobs')
