#!/usr/bin/env python3
"""Stopped-volume worker: archive only exactly marker-bound legacy jobs, retain their bytes."""
import argparse,hashlib,json,os,pathlib,re,stat,uuid,xml.etree.ElementTree as ET

PREFIX='ch.so.agi.jenkins.gretldatenportal.'
ORG=PREFIX+'GretlDatenportalManagedJobProperty'
SEED=PREFIX+'GretlDatenportalManagedSeedJobProperty'
SEED_NAME='gretl-datenportal-seed'
JOB_NAME='di-csv-ingest'
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

def plan(home,instance,volume):
    current=inventory(home)
    if JOB_NAME in current:raise RuntimeError('New CSV job name is already occupied; no legacy conversion')
    return {'schemaVersion':1,'planId':str(uuid.uuid4()),'instance':instance,'volume':volume,'inventory':current}

def private_directory(path,owner=None):
    if path.is_symlink():raise RuntimeError('Refusing symlink in private retirement path')
    try:
        path.mkdir(mode=0o700)
        if owner:os.chown(path,*owner)
    except FileExistsError:pass
    if not path.is_dir() or stat.S_IMODE(path.stat().st_mode)!=0o700:raise RuntimeError('Private retirement directory required')

def apply(home,p,instance,volume):
    if p.get('schemaVersion')!=1 or p.get('instance')!=instance or p.get('volume')!=volume:raise RuntimeError('Wrong Jenkins retirement binding')
    id=str(uuid.UUID(p['planId']));expected=p['inventory'];current=inventory(home)
    root=home/'data-infrastructure';destination=root/'retired'/('legacy-'+id)/'jobs'
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
    if not any(row['legacyMarker'] for row in expected.values()):return 0
    uid,gid=home.stat().st_uid,home.stat().st_gid
    private_directory(root,(uid,gid));private_directory(root/'retired');private_directory(destination.parent);private_directory(destination)
    moved=0
    for name,row in expected.items():
        if not row['legacyMarker'] or name not in current:continue
        source=home/'jobs'/name;target=destination/name
        if not SAFE.fullmatch(name) or marker(name,source/'config.xml')!=row['legacyMarker'] or digest(source/'config.xml')!=row['configSha256'] or target.exists():raise RuntimeError('Legacy marker/hash changed; no move')
        os.rename(source,target);moved+=1
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
        print('Planned '+str(sum(bool(x['legacyMarker']) for x in data['inventory'].values()))+' marker-bound jobs; no volume write')
    else:
        if not regular(file) or file.stat().st_mode&0o077 or file.stat().st_size>1048576:raise RuntimeError('Private bound retirement plan required')
        print('Archived '+str(apply(JENKINS_VOLUME_ROOT,json.loads(file.read_text()),instance,volume))+' owned jobs; retained complete histories and unrelated jobs')
