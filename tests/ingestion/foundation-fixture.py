"""Real Garage regression for the explicitly owned key-local Foundation fixture."""
import hashlib,os,pathlib,sys
import boto3
from botocore.config import Config
sys.path[:0]=['/runtime','/opt/stack-tools']
from setup_garage import load_storage_target
from cutover_g1 import bind_foundation_fixture,retire_foundation_fixture,CutoverError,inventory
if os.environ.get('DI_TEST_FIXTURE')!='true' or not os.environ['COMPOSE_PROJECT_NAME'].startswith('mag-g1-foundation-'):raise RuntimeError('Synthetic owned project required')
t=load_storage_target('/runtime');alias='ch.so.dateninfrastruktur.private';key=t.api('CreateKey',{'name':'own-foundation-fixture'})
b=t.api('CreateBucket',{'localAlias':{'accessKeyId':key['accessKeyId'],'alias':alias}})
t.api('AllowBucketKey',{'bucketId':b['id'],'accessKeyId':key['accessKeyId'],'permissions':{'read':True,'write':True,'owner':True}})
s=boto3.client('s3',endpoint_url='http://garage:3900',region_name='garage',aws_access_key_id=key['accessKeyId'],aws_secret_access_key=key['secretAccessKey'],config=Config(signature_version='s3v4',s3={'addressing_style':'path'}))
body=b'private-object-id=0123456789abcdef0123456789abcdef\n'
proof={'bucket':alias,'key':'private-foundation-smoke.txt','size':len(body),'sha256':hashlib.sha256(body).hexdigest()}
s.put_object(Bucket=alias,Key=proof['key'],Body=body,ContentType='text/plain')
bound=bind_foundation_fixture(t,s,key['accessKeyId'],proof);assert bound['bucket_id']==b['id']
# A distinct global bucket with the same human-readable alias is never selected.
foreign=t.api('CreateBucket',{'globalAlias':alias})
assert bind_foundation_fixture(t,s,key['accessKeyId'],proof)['bucket_id']==b['id']
s.put_object(Bucket=alias,Key='unknown.txt',Body=b'protected unknown fixture')
try:retire_foundation_fixture(t,s,bound);raise AssertionError('Unknown source deleted')
except CutoverError as e:assert str(e)=='FOUNDATION_FIXTURE_CHANGED'
assert s.get_object(Bucket=alias,Key='unknown.txt')['Body'].read()==b'protected unknown fixture'
s.delete_object(Bucket=alias,Key='unknown.txt')
assert s.get_object(Bucket=alias,Key=proof['key'])['Body'].read()==body
retire_foundation_fixture(t,s,bound);retire_foundation_fixture(t,s,bound)
assert t.api('GetBucketInfo',id=foreign['id'])['globalAliases']==[alias]
# Reassignment after successful retirement is an identity conflict, never permission to purge.
replacement=t.api('CreateBucket',{})
t.api('AddBucketAlias',{'bucketId':replacement['id'],'accessKeyId':key['accessKeyId'],'localAlias':alias})
t.api('AllowBucketKey',{'bucketId':replacement['id'],'accessKeyId':key['accessKeyId'],'permissions':{'read':True,'write':True,'owner':True}})
s.put_object(Bucket=alias,Key='new-owner.txt',Body=b'keep after alias reassignment')
try:retire_foundation_fixture(t,s,bound);raise AssertionError('Reassigned alias accepted')
except CutoverError as e:assert str(e)=='FOUNDATION_ALIAS_REASSIGNED'
assert s.get_object(Bucket=alias,Key='new-owner.txt')['Body'].read()==b'keep after alias reassignment'
print('PASS G14/G19 key-local Foundation identity and actual GET SHA, distinct global bucket untouched, unknown object protected, safe repeated retirement, reassigned alias refused')
