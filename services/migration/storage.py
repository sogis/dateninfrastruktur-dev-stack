"""Copy only after a complete content/metadata collision preflight. No delete API."""
import datetime,hashlib,json,os,pathlib,tempfile
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
ROOT=pathlib.Path('/runtime/migration')
FIELDS=['ContentType','ContentDisposition','ContentEncoding','ContentLanguage','CacheControl','Expires','Metadata']
def client(config):return boto3.client('s3',endpoint_url=config['endpoint'],aws_access_key_id=config['access_key'],aws_secret_access_key=config['secret_key'],region_name='garage',config=Config(signature_version='s3v4',s3={'addressing_style':'path'},retries={'max_attempts':2}))
def metadata(head):return {k:(head[k].isoformat() if isinstance(head[k],datetime.datetime) else head[k]) for k in FIELDS if k in head}
def object_info(s3,bucket,key):
    try:response=s3.get_object(Bucket=bucket,Key=key)
    except ClientError as e:
        if e.response['ResponseMetadata']['HTTPStatusCode']==404:return None
        raise RuntimeError('S3_READ_FAILED: credentials/details withheld') from None
    h=hashlib.sha256();length=0
    with response['Body'] as body:
        for block in iter(lambda:body.read(1024*1024),b''):h.update(block);length+=len(block)
    if length!=response['ContentLength']:raise RuntimeError('VERIFICATION_FAILED: incomplete S3 stream')
    return {'sha256':h.hexdigest(),'size':length,'metadata':metadata(response)}
def inventory(s3,bucket):
    result={}
    for page in s3.get_paginator('list_objects_v2').paginate(Bucket=bucket):
        for item in page.get('Contents',[]):result[item['Key']]=object_info(s3,bucket,item['Key'])
    return result

def run(mode):
    config=json.loads((ROOT/'storage.json').read_text());source=client(config['source']);target=client(config['target']);bucket=config.get('bucket','di-managed-private')
    if bucket!='di-managed-private':raise RuntimeError('VERIFICATION_FAILED: only the selected managed bucket may be copied')
    manifest=ROOT/'storage-manifest.json'
    if mode=='verify-target':
        if not manifest.exists():raise RuntimeError('VERIFICATION_FAILED: no bound storage manifest')
        original=json.loads(manifest.read_text())
        if any(object_info(target,bucket,key)!=wanted for key,wanted in original.items()):raise RuntimeError('VERIFICATION_FAILED: retained target object content/metadata')
        print('Target storage verified against immutable source manifest: '+str(len(original))+' objects');return
    original=inventory(source,bucket)
    if manifest.exists() and json.loads(manifest.read_text())!=original:raise RuntimeError('SOURCE_CHANGED: managed objects')
    if mode=='source-inventory':
        if not manifest.exists():manifest.write_text(json.dumps(original,sort_keys=True,indent=2));manifest.chmod(0o600)
        print('Source storage checkpoint verified: '+str(len(original))+' objects');return
    # Validate EVERY existing destination before any write. Identical keys are no-ops.
    missing=[]
    for key,wanted in original.items():
        actual=object_info(target,bucket,key)
        if actual is None:missing.append(key)
        elif actual!=wanted:raise RuntimeError('STORAGE_CONFLICT: existing destination content or metadata differs')
    if mode=='inventory':
        manifest.write_text(json.dumps(original,sort_keys=True,indent=2));manifest.chmod(0o600)
    elif mode=='copy':
        if not manifest.exists():raise RuntimeError('VERIFICATION_FAILED: explicit source inventory required')
        for key in missing:
            wanted=original[key]
            if object_info(source,bucket,key)!=wanted:raise RuntimeError('SOURCE_CHANGED: object before copy')
            if object_info(target,bucket,key) is not None:raise RuntimeError('STORAGE_CONFLICT: target appeared during copy')
            with tempfile.TemporaryFile(dir=ROOT) as payload:
                response=source.get_object(Bucket=bucket,Key=key)
                checksum=hashlib.sha256();size=0
                with response['Body'] as body:
                    for block in iter(lambda:body.read(1024*1024),b''):payload.write(block);checksum.update(block);size+=len(block)
                if {'sha256':checksum.hexdigest(),'size':size,'metadata':metadata(response)}!=wanted:raise RuntimeError('SOURCE_CHANGED: object stream during copy')
                payload.seek(0);kwargs=dict(wanted['metadata'])
                if 'Expires' in kwargs:kwargs['Expires']=datetime.datetime.fromisoformat(kwargs['Expires'])
                target.put_object(Bucket=bucket,Key=key,Body=payload,ContentLength=wanted['size'],**kwargs)
            if object_info(target,bucket,key)!=wanted:raise RuntimeError('VERIFICATION_FAILED: copied bytes/metadata')
        if inventory(source,bucket)!=original:raise RuntimeError('SOURCE_CHANGED: objects during copy')
        if any(object_info(target,bucket,key)!=wanted for key,wanted in original.items()):raise RuntimeError('VERIFICATION_FAILED: final object comparison')
    elif mode=='verify':
        if not manifest.exists() or missing:raise RuntimeError('VERIFICATION_FAILED: missing objects or manifest')
    else:raise RuntimeError('Unknown storage migration action')
    print('Storage '+mode+' verified: '+str(len(original))+' objects; '+str(len(missing))+' initially absent; no deletions')
if __name__=='__main__':
    import sys
    try:run(sys.argv[1])
    except Exception as error:
        # SDK exceptions can include URLs/objectnames/authorization context; never print them.
        print(str(error) if type(error) is RuntimeError else 'S3_OPERATION_FAILED: details withheld',file=sys.stderr);sys.exit(1)
