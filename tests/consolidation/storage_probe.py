"""Explicit synthetic mutation probe, fed over stdin to a test-profile tooljob."""
import json,os,pathlib,sys
from urllib.parse import urlsplit
sys.path.insert(0,'/opt/stack-tools/migration')
from storage import client,metadata,FIELDS
from botocore.exceptions import ClientError
root=pathlib.Path('/runtime/migration');config=json.loads((root/'storage.json').read_text());probe=json.loads((root/'storage-probe.json').read_text())
if os.environ.get('DI_COMPOSE_TEST_FIXTURE')!='true' or any(not urlsplit(config[k]['endpoint']).hostname.startswith('maf-f2-') for k in ['source','target']):raise RuntimeError('Only isolated MA-F2 fixtures may run the mutation probe')
source=client(config['source']);target=client(config['target']);bucket='di-managed-private';key=probe['key'];action=probe['action']
def read(c):
    r=c.get_object(Bucket=bucket,Key=key)
    with r['Body'] as body:data=body.read()
    return data,{k:r[k] for k in FIELDS if k in r}
def copy(original,destination):
    data,meta=read(original);destination.put_object(Bucket=bucket,Key=key,Body=data,**meta)
if action=='customize-source':
    body,meta=read(source);meta['Metadata']={**meta.get('Metadata',{}),'di-migration-probe':'current-metadata'};meta['ContentDisposition']='attachment; filename="pilot-v1.csv"';meta['CacheControl']='private, no-store';source.put_object(Bucket=bucket,Key=key,Body=body,**meta)
elif action in ['target-bytes-conflict','target-metadata-conflict']:
    body,meta=read(target)
    if action=='target-bytes-conflict':body=b'explicit synthetic conflict'
    else:meta['Metadata']={**meta.get('Metadata',{}),'di-conflict':'different metadata'}
    target.put_object(Bucket=bucket,Key=key,Body=body,**meta)
elif action=='source-changed':
    body,meta=read(source);meta['Metadata']={**meta.get('Metadata',{}),'di-source-changed':'after checkpoint'};source.put_object(Bucket=bucket,Key=key,Body=body,**meta)
elif action=='restore-target':copy(source,target)
elif action=='restore-source':copy(target,source)
elif action=='permission-boundaries':
    foundation=client(probe['foundation']);origin=client(probe['origin'])
    assert foundation.get_object(Bucket='ch.so.daten',Key='foundation-sentinel.txt')['Body'].read()==b'foundation legacy bytes retained\n'
    assert origin.get_object(Bucket=bucket,Key=key)['Body'].read()==read(target)[0]
    try:foundation.get_object(Bucket=bucket,Key=key);raise AssertionError('Legacy Foundation key can read managed private bytes')
    except ClientError as error:assert error.response['ResponseMetadata']['HTTPStatusCode']==403
    try:origin.put_object(Bucket=bucket,Key='origin-write-probe',Body=b'forbidden');raise AssertionError('Read-only Origin can write')
    except ClientError as error:assert error.response['ResponseMetadata']['HTTPStatusCode']==403
else:raise RuntimeError('Unknown fixture probe')
print('PASS synthetic storage probe: '+action)
