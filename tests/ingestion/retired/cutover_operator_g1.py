"""Temporary G1 operator. Runs only in the canonical explicit tool container.
Removed from active distribution after the reviewed local operation.
"""
import json,os,pathlib,sys,hashlib,re
import boto3
from botocore.config import Config
sys.path[:0]=['/runtime','/opt/stack-tools','/opt/admin/scripts']
from setup_garage import StorageTarget,GarageProvisioner,write_secrets_atomically,encode
from cutover_g1 import PrivateBucketCutover,CutoverError,digest,TARGET,SOURCE,inventory,bind_foundation_fixture,retire_foundation_fixture
from management_db import sql
import tomllib

root=pathlib.Path('/runtime');private=root/'ma-g1-cutover'
if not (private/'host-binding.json').is_file():raise RuntimeError('Explicit verified host binding required')
token=tomllib.loads((root/'garage.toml').read_text())['admin']['admin_token']
target=StorageTarget(root,os.environ['INSTANCE_ID'],admin_token=token)
def client(key):
    return boto3.client('s3',endpoint_url=target.endpoint,region_name=target.region,aws_access_key_id=key['accessKeyId'],aws_secret_access_key=key['secretAccessKey'],config=Config(signature_version='s3v4',s3={'addressing_style':'path'}))
def references():
    rows=json.loads(sql("SELECT coalesce(json_agg(json_build_object('key',objectkey,'size',bytesize,'sha256',sha256)),'[]') FROM di_management.distribution;"))
    result={row['key']:{'size':row['size'],'sha256':row['sha256']} for row in rows}
    if len(result)!=len(rows):raise CutoverError('DUPLICATE_PRIVATE_REFERENCES')
    return result
def read(name):return json.loads((private/name).read_text())
def write(name,value):write_secrets_atomically(private/name,json.dumps(value,indent=2)+'\n')
def engine(keys):return PrivateBucketCutover(target,client(keys['source']),client(keys['old_target']),references,write_secrets_atomically,private,lambda:read('host-binding.json')['binding'])
def plan():
    if (private/'bound-plan.json').exists():raise CutoverError('EXISTING_IMMUTABLE_CUTOVER_PLAN')
    keys={}
    for kind,prefix in [('source','GARAGE_MANAGED'),('old_target','GARAGE_DEFAULT'),('old_origin','GARAGE_ORIGIN')]:
        key=target.api('GetKeyInfo',id=os.environ[prefix+'_ACCESS_KEY'],showSecretKey='true')
        if key['secretAccessKey']!=os.environ[prefix+'_SECRET_KEY']:raise CutoverError('OLD_KEY_SECRET_MISMATCH')
        keys[kind]=key
    proof_path=private/'foundation-fixture-proof.json'
    if proof_path.exists():
        proof=read('foundation-fixture-proof.json')
        if proof['bucket']!='ch.so.dateninfrastruktur.private' or proof['key']!='private-foundation-smoke.txt' or proof['size']!=51:raise CutoverError('UNKNOWN_FOUNDATION_FIXTURE')
        extra=read('foundation-fixture-key.json')
        actual=target.api('GetKeyInfo',id=extra['accessKeyId'],showSecretKey='true')
        if actual['secretAccessKey']!=extra['secretAccessKey']:raise CutoverError('FOUNDATION_KEY_SECRET_CHANGED')
        keys['old_browser']=actual
    bound=engine(keys).plan()
    if proof_path.exists():
        bound['foundation_smoke']=bind_foundation_fixture(target,client(keys['old_target']),keys['old_target']['accessKeyId'],proof)
    allowed={bound['binding']['source_bucket_id'],bound['binding']['target_bucket_id']}
    if 'foundation_smoke' in bound:allowed.add(bound['foundation_smoke']['bucket_id'])
    # An old application key attached to an unknown bucket is never globally deleted.
    for key in keys.values():
        if any(b['id'] not in allowed and any(b['permissions'].values()) for b in key['buckets']):raise CutoverError('OLD_KEY_HAS_FOREIGN_BUCKET_PERMISSIONS')
    write('old-keys.json',keys);write('bound-plan.json',bound)
    print('Bound read-only plan: '+str(len(bound['copy_keys']))+' private referenced objects')
def apply():
    keys=read('old-keys.json');bound=read('bound-plan.json')
    print(json.dumps(engine(keys).apply(bound)))
def provision():
    keys=read('old-keys.json');bound=read('bound-plan.json');e=engine(keys)
    if e.journal(bound)['state']!='VERIFIED':raise CutoverError('VERIFIED_COPY_REQUIRED')
    e.preflight(bound)
    # Exact inventoried old keys lose all access to the new private target.
    for key in keys.values():target.api('DenyBucketKey',{'bucketId':bound['binding']['target_bucket_id'],'accessKeyId':key['accessKeyId'],'permissions':{'read':True,'write':True,'owner':True}})
    state=root/'storage-target.json'
    if not state.exists():
        write_secrets_atomically(state,json.dumps({'schema_version':1,'instance':target.instance,'nodes':bound['binding']['nodes'],'bucket':TARGET,'bucket_id':bound['binding']['target_bucket_id'],'keys':{}},indent=2)+'\n')
    provisioner=GarageProvisioner(target);bucket=provisioner.ensure_private_bucket()
    writer=provisioner.ensure_key('writer');reader=provisioner.ensure_key('reader')
    provisioner.reconcile_permissions(bucket,writer,reader);provisioner.verify_storage_policy()
    values={k:v for k,v in os.environ.items() if k.startswith('DI_STORAGE_')}
    values.update(DI_STORAGE_BUCKET=TARGET,DI_STORAGE_ENDPOINT=target.endpoint,DI_STORAGE_REGION=target.region)
    for kind,key in [('WRITER',writer),('READER',reader)]:
        values['DI_STORAGE_'+kind+'_ACCESS_KEY']=key['accessKeyId'];values['DI_STORAGE_'+kind+'_SECRET_KEY']=key['secretAccessKey']
    write('new-storage.json',values)
    old=(root/'garage.toml').read_text()
    cleaned=re.sub(r'(?ms)^\[s3_web\]\s*\n.*?(?=^\[|\Z)','',old)
    expected=tomllib.loads(old);expected.pop('s3_web',None)
    if tomllib.loads(cleaned)!=expected:raise CutoverError('GARAGE_CONFIG_REMOVAL_NOT_EXACT')
    write_secrets_atomically(root/'garage.toml',cleaned)
    print('Dedicated storage identities bound and verified; old target keys revoked')
def finish():
    bound=read('bound-plan.json');keys=read('old-keys.json');values=read('new-storage.json')
    e=engine(keys);e.destination=client({'accessKeyId':values['DI_STORAGE_WRITER_ACCESS_KEY'],'secretAccessKey':values['DI_STORAGE_WRITER_SECRET_KEY']})
    def verify():
        receipt=read('runtime-verified.json')
        return sql('SELECT di_ops.single_storage_contract();')=='t' and receipt['plan_sha256']==digest(bound) and receipt['host_binding_sha256']==digest(read('host-binding.json')['binding']) and receipt['probe_sha256']==hashlib.sha256((root/'g1-download-probes.json').read_bytes()).hexdigest()
    if e.journal(bound)['state']=='VERIFIED':e.confirm_switch(bound,verify)
    print(json.dumps(e.retire_source(bound,verify)))
    if 'foundation_smoke' in bound:
        retire_foundation_fixture(target,client(keys['old_target']),bound['foundation_smoke'])
    for key in {v['accessKeyId']:v for v in keys.values()}.values():
        try:current=target.api('GetKeyInfo',id=key['accessKeyId'],showSecretKey='true')
        except Exception as error:
            if getattr(error,'status',None)==404:continue
            raise
        if current['secretAccessKey']!=key['secretAccessKey']:raise CutoverError('OLD_KEY_IDENTITY_CHANGED')
        if any(any(b['permissions'].values()) for b in current['buckets']):raise CutoverError('OLD_KEY_REMAINS_AUTHORIZED')
        target.api('DeleteKey',id=key['accessKeyId'])
    print('Old application storage keys retired')
{'plan':plan,'apply':apply,'provision':provision,'finish':finish}[sys.argv[1]]()
