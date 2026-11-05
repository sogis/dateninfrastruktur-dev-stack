"""Synthetic G14/G15 fixture executed only through the canonical tooling service."""
import io,json,os,pathlib,sys,uuid,hashlib,zipfile,copy,urllib.request,urllib.error
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
sys.path[:0]=['/opt/stack-tools','/opt/admin/scripts']
from setup_garage import load_storage_target,write_secrets_atomically
from cutover_g1 import PrivateBucketCutover,CutoverError,object_info,inventory,digest,SOURCE,TARGET,CANARY,CANARY_BYTES
from management_db import sql
if os.environ.get('DI_TEST_FIXTURE')!='true' or not os.environ.get('COMPOSE_PROJECT_NAME','').startswith('mag-g1-'):raise RuntimeError('Owned synthetic G1 fixture required')
root=pathlib.Path('/runtime');target=load_storage_target(root)
fixture=json.loads((root/'fixture.json').read_text())
def client(key,secret,endpoint='http://garage:3900'):
    return boto3.client('s3',endpoint_url=endpoint,region_name='garage',aws_access_key_id=key,aws_secret_access_key=secret,config=Config(signature_version='s3v4',s3={'addressing_style':'path'},retries={'max_attempts':2}))
writer=client(os.environ['DI_STORAGE_WRITER_ACCESS_KEY'],os.environ['DI_STORAGE_WRITER_SECRET_KEY'])
def refs():
    rows=json.loads(sql("SELECT coalesce(json_agg(json_build_object('key',objectkey,'size',bytesize,'sha256',sha256)),'[]') FROM di_management.distribution;"))
    result={r['key']:{'size':r['size'],'sha256':r['sha256']} for r in rows}
    if len(result)!=len(rows):raise RuntimeError('Duplicate registered object keys')
    return result

def payload(file):
    if file['filename'].endswith('.csv'):return ('kind,version,wert\n'+file['kind']+','+file['filename']+',42\n').encode()
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w') as z:
        z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
        z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/workbook.xml','<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Pilot" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Preserved synthetic snapshot</t></is></c><c r="B1"><v>42</v></c></row></sheetData></worksheet>')
    return output.getvalue()

def construct(source_key):
    return PrivateBucketCutover(target,client(source_key['accessKeyId'],source_key['secretAccessKey']),writer,refs,write_secrets_atomically,root,lambda:json.loads((root/'g1-host-binding.json').read_text()))

def prepare(run_engine=True):
    source_bucket=target.api('CreateBucket',{'globalAlias':SOURCE})
    source_key=target.api('CreateKey',{'name':'g1-synthetic-source','deny':{'createBucket':True}})
    for bucket in [source_bucket['id'],target.api('GetBucketInfo',globalAlias=TARGET)['id']]:
        target.api('AllowBucketKey',{'bucketId':bucket,'accessKeyId':source_key['accessKeyId'],'permissions':{'read':True,'write':True,'owner':False}})
    write_secrets_atomically(root/'g1-source-key.json',json.dumps(source_key))
    old=client(source_key['accessKeyId'],source_key['secretAccessKey'])
    old.put_object(Bucket=TARGET,Key='old-development.txt',Body=b'old disposable synthetic development content',ContentType='text/plain')
    assert old.get_object(Bucket=TARGET,Key='old-development.txt')['Body'].read().startswith(b'old disposable')
    commands=['BEGIN;']
    for key,value in [('di.actor_kind','service'),('di.actor_issuer','urn:di:operator'),('di.actor_subject','managed-delivery'),('di.action','test.seed_existing_private_snapshot'),('di.request_id',str(uuid.uuid4())),('di.command_id',str(uuid.uuid4()))]:commands.append("SELECT set_config('"+key+"','"+value+"',true);")
    (root/'payload').mkdir(exist_ok=True)
    for file in fixture['files']:
        content=payload(file);sha=hashlib.sha256(content).hexdigest();file.update(sha256=sha,size=len(content))
        (root/'payload'/(file['kind']+'-'+file['filename'])).write_bytes(content)
        old.put_object(Bucket=SOURCE,Key=file['key'],Body=content,ContentType='text/csv' if file['filename'].endswith('.csv') else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',CacheControl='no-store',Metadata={'fixture':'owned-g1'})
        # Explicit synthetic source fixture only: the values come from the actual S3 read-back.
        actual=object_info(old,SOURCE,file['key']);assert actual['sha256']==sha and actual['size']==len(content)
        identity=str(uuid.UUID(file['id']))
        commands.append("UPDATE di_management.distribution SET bytesize="+str(len(content))+",sha256='"+sha+"',availability='available' WHERE t_ili_tid='"+identity+"';")
    commands.append('COMMIT;');sql('\n'.join(commands));write_secrets_atomically(root/'fixture.json',json.dumps(fixture,indent=2))
    old.put_object(Bucket=SOURCE,Key=CANARY,Body=CANARY_BYTES,ContentType='text/csv')
    if not run_engine:
        print('Synthetic source prepared for the one-shot operator');return
    engine=construct(source_key)
    old.put_object(Bucket=SOURCE,Key='unknown-own-fixture.txt',Body=b'unknown must remain protected')
    try:engine.plan();raise AssertionError('Unknown source accepted')
    except CutoverError as e:assert str(e)=='UNKNOWN_PRIVATE_SOURCE_OBJECTS'
    assert old.get_object(Bucket=SOURCE,Key='unknown-own-fixture.txt')['Body'].read()==b'unknown must remain protected'
    old.delete_object(Bucket=SOURCE,Key='unknown-own-fixture.txt')
    plan=engine.plan();write_secrets_atomically(root/'g1-bound-plan.json',json.dumps(plan,indent=2))
    wrong=copy.deepcopy(plan);wrong['binding']['target_bucket_id']='f'*64
    try:engine.apply(wrong);raise AssertionError('Wrong bucket binding accepted')
    except CutoverError as e:assert str(e)=='CUTOVER_INSTANCE_OR_BUCKET_CHANGED'
    assert old.get_object(Bucket=TARGET,Key='old-development.txt')['Body'].read().startswith(b'old disposable')
    try:PrivateBucketCutover(target,client('synthetic','synthetic',endpoint='https://example.invalid'),writer,refs,write_secrets_atomically,root,lambda:{});raise AssertionError('Foreign endpoint accepted')
    except CutoverError as e:assert str(e)=='NONLOCAL_STORAGE_ENDPOINT'
    def interrupt(key):raise InterruptedError('own controlled interruption after verified first copy')
    try:engine.apply(plan,after_copy=interrupt);raise AssertionError('Interruption not reached')
    except InterruptedError:pass
    journal=json.loads((root/'cutover-g1-journal.json').read_text());assert journal['state']=='COPYING' and len(journal['copied'])==1
    preserved=object_info(writer,TARGET,journal['copied'][0])
    assert engine.apply(plan)['state']=='VERIFIED'
    assert object_info(writer,TARGET,journal['copied'][0])==preserved
    assert 'old-development.txt' not in inventory(writer,TARGET)
    target.api('DenyBucketKey',{'bucketId':plan['binding']['target_bucket_id'],'accessKeyId':source_key['accessKeyId'],'permissions':{'read':True,'write':True,'owner':True}})
    try:old.get_object(Bucket=TARGET,Key=fixture['files'][0]['key']);raise AssertionError('Old key can read new private object')
    except ClientError as e:assert e.response['ResponseMetadata']['HTTPStatusCode']==403
    assert old.get_object(Bucket=SOURCE,Key=CANARY)['Body'].read()==CANARY_BYTES
    print('PASS G14/G15: real PG references, byte/metadata copy, unknown-source/foreign-endpoint/wrong-bucket rejection, interruption resume without repurge, existing-object old-key denial')

def finish():
    source_key=json.loads((root/'g1-source-key.json').read_text());engine=construct(source_key);plan=json.loads((root/'g1-bound-plan.json').read_text());tokens=json.loads((root/'f4-tokens.json').read_text())
    def verify():
        if sql('SELECT di_ops.single_storage_contract();')!='t':return False
        for file in fixture['files']:
            token=None if file['kind']=='open' else tokens['ben']
            headers={'Host':os.environ['G1_GATEWAY_AUTHORITY']}
            if token:headers['Authorization']='Bearer '+token
            with urllib.request.urlopen(urllib.request.Request('http://gateway:9080'+file['path'],headers=headers),timeout=15) as response:
                if response.status!=200 or hashlib.sha256(response.read()).hexdigest()!=file['sha256'] or response.headers.get('Cache-Control')!='no-store':return False
            if file['kind']=='restricted':
                for token,status in [(None,401),(tokens['anna'],403)]:
                    h={'Host':os.environ['G1_GATEWAY_AUTHORITY']}
                    if token:h['Authorization']='Bearer '+token
                    try:urllib.request.urlopen(urllib.request.Request('http://gateway:9080'+file['path'],headers=h),timeout=15);return False
                    except urllib.error.HTTPError as e:
                        if e.code!=status:return False
        return True
    before=inventory(engine.source,SOURCE)
    try:engine.confirm_switch(plan,lambda:False);raise AssertionError('Unverified runtime accepted')
    except CutoverError as e:assert str(e)=='RUNTIME_SWITCH_NOT_VERIFIED'
    assert inventory(engine.source,SOURCE)==before
    engine.confirm_switch(plan,verify)
    class LostDeleteAcknowledgement:
        def __getattr__(self,name):return getattr(target,name)
        def api(self,name,*args,**kwargs):
            result=target.api(name,*args,**kwargs)
            if name=='DeleteBucket':raise OSError('Owned synthetic lost delete acknowledgement')
            return result
    engine.target=LostDeleteAcknowledgement()
    try:engine.retire_source(plan,verify);raise AssertionError('Lost acknowledgement not reached')
    except OSError:pass
    assert json.loads((root/'cutover-g1-journal.json').read_text())['state']=='RETIRING'
    engine.target=target;result=engine.retire_source(plan,verify)
    assert result['recovered_delete_ack'] is True
    target.api('DeleteKey',id=source_key['accessKeyId'])
    try:engine.apply(plan);raise AssertionError('Completed cutover repeated purge')
    except CutoverError as e:assert str(e)=='CUTOVER_ALREADY_SWITCHED_READ_ONLY_VERIFICATION_REQUIRED'
    assert all(object_info(writer,TARGET,f['key'])['sha256']==f['sha256'] for f in fixture['files'])
    print('PASS G14/G17/G19: actual gateway allow/deny/revoked rights verified before source retirement; old private bucket/key removed, repeated cutover refuses any purge; '+json.dumps(result))

{'prepare':prepare,'prepare-operator':lambda:prepare(False),'finish':finish}[sys.argv[1]]()
