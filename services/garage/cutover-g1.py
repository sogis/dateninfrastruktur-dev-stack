"""One-shot, bound local G1 cutover engine; never imported by normal setup/start.
The host operator must bind the canonical Compose container/volume identities and
supply fresh PG references and a real post-switch runtime verification callback.
"""
import datetime,hashlib,json,pathlib,tempfile,os,fcntl,functools,stat
from botocore.exceptions import ClientError

TARGET='ch.so.daten';SOURCE='di-managed-private'
META=['ContentType','ContentDisposition','ContentEncoding','ContentLanguage','CacheControl','Expires','Metadata']
CANARY='migration-evidence/canary.csv'
CANARY_BYTES=b'synthetic-old-public-canary,42\n'
class CutoverError(RuntimeError):pass
def exclusive(method):
    @functools.wraps(method)
    def execute(self,*args,**kwargs):
        fd=os.open(self.root/'cutover-g1.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'r+') as lock:
            if not stat.S_ISREG(os.fstat(lock.fileno()).st_mode):raise CutoverError('INVALID_CUTOVER_LOCK')
            fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
            return method(self,*args,**kwargs)
    return execute

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def object_info(client,bucket,key):
    try:response=client.get_object(Bucket=bucket,Key=key)
    except ClientError as error:
        if error.response['ResponseMetadata']['HTTPStatusCode']==404:return None
        raise CutoverError('PRIVATE_OBJECT_READ_FAILED') from None
    h=hashlib.sha256();size=0
    with response['Body'] as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block);size+=len(block)
    if size!=response['ContentLength']:raise CutoverError('INCOMPLETE_PRIVATE_OBJECT')
    meta={k:(response[k].isoformat() if isinstance(response[k],datetime.datetime) else response[k]) for k in META if k in response}
    return {'size':size,'sha256':h.hexdigest(),'metadata':meta}
def inventory(client,bucket):
    result={}
    for page in client.get_paginator('list_objects_v2').paginate(Bucket=bucket):
        for item in page.get('Contents',[]):result[item['Key']]=object_info(client,bucket,item['Key'])
    return result

class PrivateBucketCutover:
    def __init__(self,target,source_client,target_client,load_references,write_private,root,host_binding):
        if target.endpoint!='http://garage:3900' or target.bucket!=TARGET:raise CutoverError('NONLOCAL_STORAGE_TARGET')
        for client in [source_client,target_client]:
            if client.meta.endpoint_url!='http://garage:3900' or client.meta.region_name!='garage':raise CutoverError('NONLOCAL_STORAGE_ENDPOINT')
        self.target=target;self.source=source_client;self.destination=target_client
        self.references=load_references;self.write=write_private;self.root=pathlib.Path(root)
        self.host_binding=host_binding;self.journal_path=self.root/'cutover-g1-journal.json'
    def binding(self):
        t=self.target
        source=t.api('GetBucketInfo',globalAlias=SOURCE);target=t.api('GetBucketInfo',globalAlias=TARGET)
        return {'instance':t.instance,'nodes':sorted(n['id'] for n in t.api('GetClusterStatus')['nodes']),'source_bucket_id':source['id'],'target_bucket_id':target['id'],'host':self.host_binding()}
    def plan(self):
        refs=self.references();source=inventory(self.source,SOURCE);target=inventory(self.destination,TARGET)
        if not refs:raise CutoverError('NO_BOUND_PRIVATE_REFERENCES')
        for key,expected in refs.items():
            if key not in source:raise CutoverError('REFERENCED_PRIVATE_OBJECT_MISSING')
            actual=source[key]
            if expected.get('sha256') and actual['sha256']!=expected['sha256']:raise CutoverError('PRIVATE_REFERENCE_HASH_MISMATCH')
            if expected.get('size') is not None and actual['size']!=expected['size']:raise CutoverError('PRIVATE_REFERENCE_SIZE_MISMATCH')
        extra=set(source)-set(refs)
        if extra:
            if extra!={CANARY} or source[CANARY]['sha256']!=hashlib.sha256(CANARY_BYTES).hexdigest() or source[CANARY]['size']!=len(CANARY_BYTES):raise CutoverError('UNKNOWN_PRIVATE_SOURCE_OBJECTS')
        return {'schema_version':1,'binding':self.binding(),'references_sha256':digest(refs),'source_objects':source,'old_target_objects':target,'copy_keys':sorted(refs),'discard_canary':bool(extra),'operation':'local-development-ch.so.daten-single-purge'}
    def journal(self,plan):
        if self.journal_path.exists():
            journal=json.loads(self.journal_path.read_text())
            if journal['plan_sha256']!=digest(plan):raise CutoverError('CUTOVER_PLAN_CHANGED')
            return journal
        return {'plan_sha256':digest(plan),'state':'PLANNED','copied':[]}
    def save(self,journal):self.write(self.journal_path,json.dumps(journal,indent=2)+'\n')
    def preflight(self,plan):
        if plan.get('schema_version')!=1 or plan.get('operation')!='local-development-ch.so.daten-single-purge':raise CutoverError('UNKNOWN_CUTOVER_CONTRACT')
        refs=self.references()
        if plan['copy_keys']!=sorted(refs):raise CutoverError('INCOMPLETE_PRIVATE_COPY_PLAN')
        extra=set(plan['source_objects'])-set(refs)
        if extra and (extra!={CANARY} or plan['source_objects'][CANARY]['sha256']!=hashlib.sha256(CANARY_BYTES).hexdigest() or plan['source_objects'][CANARY]['size']!=len(CANARY_BYTES)):raise CutoverError('UNKNOWN_PRIVATE_SOURCE_OBJECTS')
        if self.binding()!=plan['binding']:raise CutoverError('CUTOVER_INSTANCE_OR_BUCKET_CHANGED')
        if digest(self.references())!=plan['references_sha256']:raise CutoverError('CUTOVER_PG_REFERENCES_CHANGED')
        if inventory(self.source,SOURCE)!=plan['source_objects']:raise CutoverError('PRIVATE_SOURCE_CHANGED')
    @exclusive
    def apply(self,plan,after_copy=None):
        journal=self.journal(plan)
        if journal['state'] in ['SWITCHED','RETIRED']:raise CutoverError('CUTOVER_ALREADY_SWITCHED_READ_ONLY_VERIFICATION_REQUIRED')
        self.preflight(plan)
        if journal['state'] in ['PLANNED','PURGING']:
            current=inventory(self.destination,TARGET)
            if any(key not in plan['old_target_objects'] or value!=plan['old_target_objects'][key] for key,value in current.items()):raise CutoverError('PURGE_TARGET_CHANGED')
            if journal['state']=='PLANNED' and current!=plan['old_target_objects']:raise CutoverError('PURGE_BASELINE_CHANGED')
            journal['state']='PURGING';self.save(journal)
            self.target.api('UpdateBucket',{'websiteAccess':{'enabled':False}},id=plan['binding']['target_bucket_id'])
            for key,wanted in plan['old_target_objects'].items():
                actual=object_info(self.destination,TARGET,key)
                if actual is not None:
                    if actual!=wanted:raise CutoverError('PURGE_OBJECT_CHANGED')
                    self.destination.delete_object(Bucket=TARGET,Key=key)
            if inventory(self.destination,TARGET):raise CutoverError('PURGE_NOT_EMPTY')
            journal['state']='PURGED';self.save(journal)
        journal['state']='COPYING';self.save(journal)
        for key in plan['copy_keys']:
            expected=plan['source_objects'][key];existing=object_info(self.destination,TARGET,key)
            if existing is not None and existing!=expected:raise CutoverError('TARGET_OBJECT_CONFLICT')
            if existing is None:
                # Re-read and hash the exact bytes being written, bounded through a private spool.
                with tempfile.TemporaryFile(dir=self.root) as spool:
                    response=self.source.get_object(Bucket=SOURCE,Key=key);h=hashlib.sha256();size=0
                    with response['Body'] as stream:
                        for block in iter(lambda:stream.read(1024*1024),b''):spool.write(block);h.update(block);size+=len(block)
                    meta={k:(response[k].isoformat() if isinstance(response[k],datetime.datetime) else response[k]) for k in META if k in response}
                    if {'size':size,'sha256':h.hexdigest(),'metadata':meta}!=expected:raise CutoverError('SOURCE_STREAM_CHANGED')
                    kwargs=dict(meta)
                    if 'Expires' in kwargs:kwargs['Expires']=datetime.datetime.fromisoformat(kwargs['Expires'])
                    spool.seek(0);self.destination.put_object(Bucket=TARGET,Key=key,Body=spool,ContentLength=size,**kwargs)
            if object_info(self.destination,TARGET,key)!=expected:raise CutoverError('COPIED_OBJECT_VERIFICATION_FAILED')
            if key not in journal['copied']:journal['copied'].append(key);self.save(journal)
            if after_copy:after_copy(key)
        if inventory(self.destination,TARGET)!={k:plan['source_objects'][k] for k in plan['copy_keys']}:raise CutoverError('UNEXPECTED_TARGET_OBJECTS')
        self.preflight(plan);journal['state']='VERIFIED';self.save(journal)
        return {'state':'VERIFIED','copied_files':len(journal['copied'])}
    @exclusive
    def confirm_switch(self,plan,verify_schema_and_runtime):
        journal=self.journal(plan)
        if journal['state']!='VERIFIED':raise CutoverError('COPY_NOT_VERIFIED')
        self.preflight(plan)
        if not verify_schema_and_runtime():raise CutoverError('RUNTIME_SWITCH_NOT_VERIFIED')
        if inventory(self.destination,TARGET)!={k:plan['source_objects'][k] for k in plan['copy_keys']}:raise CutoverError('TARGET_CHANGED_BEFORE_SWITCH')
        journal['state']='SWITCHED';self.save(journal)
    @exclusive
    def retire_source(self,plan,verify_schema_and_runtime):
        journal=self.journal(plan)
        if journal['state'] not in ['SWITCHED','RETIRING','RETIRED']:raise CutoverError('SWITCH_NOT_VERIFIED')
        if not verify_schema_and_runtime():raise CutoverError('RUNTIME_SWITCH_NOT_VERIFIED')
        # Current alias/node/host binding and PG references remain mandatory on every resume.
        if digest(self.references())!=plan['references_sha256']:raise CutoverError('RETIRE_BINDING_CHANGED')
        expected_target={k:plan['source_objects'][k] for k in plan['copy_keys']}
        if inventory(self.destination,TARGET)!=expected_target:raise CutoverError('TARGET_CHANGED_BEFORE_RETIRE')
        try:current_binding=self.binding()
        except Exception as error:
            if journal['state'] not in ['RETIRING','RETIRED'] or getattr(error,'status',None)!=404:raise
            # A lost DeleteBucket acknowledgement is not permission to purge again.
            # Both the old alias and exact old bucket ID must be absent.
            try:self.target.api('GetBucketInfo',id=plan['binding']['source_bucket_id'])
            except Exception as missing:
                if getattr(missing,'status',None)!=404:raise
            else:raise CutoverError('SOURCE_ALIAS_LOST_BUT_BUCKET_REMAINS')
            actual=self.target.api('GetBucketInfo',globalAlias=TARGET)
            current_binding={'instance':self.target.instance,'nodes':sorted(n['id'] for n in self.target.api('GetClusterStatus')['nodes']),'source_bucket_id':plan['binding']['source_bucket_id'],'target_bucket_id':actual['id'],'host':self.host_binding()}
            if current_binding!=plan['binding']:raise CutoverError('RETIRE_BINDING_CHANGED')
            recovered=journal['state']=='RETIRING'
            if recovered:journal['state']='RETIRED';self.save(journal)
            return {'state':'RETIRED','preserved_files':len(plan['copy_keys']),'recovered_delete_ack':recovered}
        if current_binding!=plan['binding']:raise CutoverError('RETIRE_BINDING_CHANGED')
        if journal['state']=='RETIRED':raise CutoverError('RETIRED_SOURCE_REAPPEARED')
        remaining=inventory(self.source,SOURCE)
        if any(k not in plan['source_objects'] or v!=plan['source_objects'][k] for k,v in remaining.items()):raise CutoverError('UNKNOWN_REMAINING_SOURCE')
        journal['state']='RETIRING';self.save(journal)
        for key,wanted in remaining.items():
            if object_info(self.source,SOURCE,key)!=wanted:raise CutoverError('SOURCE_CHANGED_BEFORE_DELETE')
            self.source.delete_object(Bucket=SOURCE,Key=key)
        self.target.api('DeleteBucket',id=plan['binding']['source_bucket_id'])
        journal['state']='RETIRED';self.save(journal)
        return {'state':'RETIRED','preserved_files':len(plan['copy_keys'])}
