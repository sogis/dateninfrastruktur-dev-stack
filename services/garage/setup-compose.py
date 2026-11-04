"""Explicit internal Garage setup over admin API; no secrets in process arguments."""
import json,os,pathlib,re,urllib.request,urllib.error
class ApiError(RuntimeError):
    def __init__(self,name,status):
        self.status=status;super().__init__("Garage setup failed: "+name+" status "+str(status))
root=pathlib.Path('/runtime');config=(root/'garage.toml').read_text()
token=re.search(r'^admin_token\s*=\s*"([^"]+)"',config,re.M).group(1)
def api(name,body=None,query=''):
    req=urllib.request.Request('http://garage:3903/v2/'+name+query,data=None if body is None else json.dumps(body).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=10) as response:return json.load(response)
    except urllib.error.HTTPError as error:raise ApiError(name,error.code) from None
env=root/'runtime.env';values={line.split('=',1)[0]:line.split('=',1)[1].strip("'\"") for line in env.read_text().split('\n') if '=' in line and not line.startswith('#')}
try:bucket=api('GetBucketInfo',query='?globalAlias=di-managed-private')
except ApiError as error:
    if error.status!=404:raise
    bucket=api('CreateBucket',{'globalAlias':'di-managed-private'})
def imported_key(access,secret,name):
    try:result=api('GetKeyInfo',query='?id='+access+'&showSecretKey=true')
    except ApiError as error:
        if error.status!=404 or os.environ.get('DI_MIGRATION_IMPORT_KEYS')!='true':raise
        api('ImportKey',{'accessKeyId':access,'secretAccessKey':secret,'name':name})
        result=api('GetKeyInfo',query='?id='+access+'&showSecretKey=true')
    if result['secretAccessKey']!=secret:raise RuntimeError('STORAGE_CONFLICT: existing key has another secret; no rotation')
    return result
if values.get('GARAGE_ORIGIN_ACCESS_KEY'):
    key=imported_key(values['GARAGE_ORIGIN_ACCESS_KEY'],values['GARAGE_ORIGIN_SECRET_KEY'],'dateninfrastruktur-managed-origin')
    if key['secretAccessKey']!=values['GARAGE_ORIGIN_SECRET_KEY']:raise RuntimeError('Existing origin key credential conflict; no rotation')
else:
    key=api('CreateKey',{'name':'dateninfrastruktur-managed-origin','deny':{'createBucket':True}})
    values.update(GARAGE_ORIGIN_ACCESS_KEY=key['accessKeyId'],GARAGE_ORIGIN_SECRET_KEY=key['secretAccessKey'])
    lines=env.read_text().split('\n');names=['GARAGE_ORIGIN_ACCESS_KEY','GARAGE_ORIGIN_SECRET_KEY']
    lines=[line for line in lines if line.partition('=')[0] not in names]+[k+'='+values[k] for k in names]
    env.write_text('\n'.join(lines)+'\n');env.chmod(0o600)
api('UpdateKey',{'deny':{'createBucket':True}},query='?id='+key['accessKeyId'])
api('AllowBucketKey',{'bucketId':bucket['id'],'accessKeyId':key['accessKeyId'],'permissions':{'read':True,'write':False,'owner':False}})
api('DenyBucketKey',{'bucketId':bucket['id'],'accessKeyId':key['accessKeyId'],'permissions':{'read':False,'write':True,'owner':True}})
if values.get('GARAGE_MANAGED_ACCESS_KEY'):
    managed=imported_key(values['GARAGE_MANAGED_ACCESS_KEY'],values['GARAGE_MANAGED_SECRET_KEY'],'dateninfrastruktur-managed-operator')
    api('UpdateKey',{'deny':{'createBucket':True}},query='?id='+managed['accessKeyId'])
    api('AllowBucketKey',{'bucketId':bucket['id'],'accessKeyId':managed['accessKeyId'],'permissions':{'read':True,'write':True,'owner':False}})
    api('DenyBucketKey',{'bucketId':bucket['id'],'accessKeyId':managed['accessKeyId'],'permissions':{'read':False,'write':False,'owner':True}})
if os.environ.get('DI_MIGRATION_IMPORT_KEYS')=='true' and values.get('GARAGE_MANAGED_ACCESS_KEY'):
    api('DenyBucketKey',{'bucketId':bucket['id'],'accessKeyId':values['GARAGE_DEFAULT_ACCESS_KEY'],'permissions':{'read':True,'write':True,'owner':True}})
else:
    api('AllowBucketKey',{'bucketId':bucket['id'],'accessKeyId':values['GARAGE_DEFAULT_ACCESS_KEY'],'permissions':{'read':True,'write':True,'owner':True}})
(root/'origin.conf').write_text('\n'.join(['[managed]','type = s3','provider = Other','env_auth = false','access_key_id = '+values['GARAGE_ORIGIN_ACCESS_KEY'],'secret_access_key = '+values['GARAGE_ORIGIN_SECRET_KEY'],'endpoint = http://garage:3900','region = garage','force_path_style = true','no_check_bucket = true','']))
(root/'origin.conf').chmod(0o600)
print('Private bucket and dedicated read-only origin key configured; credentials withheld')
