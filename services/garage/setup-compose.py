"""Explicit single-bucket provisioning. Never purges objects or imports legacy keys."""
import dataclasses,hashlib,json,os,pathlib,re,tempfile,urllib.request,urllib.error,urllib.parse

class StorageError(RuntimeError):pass
class ApiError(StorageError):
    def __init__(self,name,status):self.status=status;super().__init__('Storage API '+name+' failed: '+str(status))

def write_secrets_atomically(path,content):
    path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.parent.chmod(0o700)
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as stream:
            stream.write(content);stream.flush();os.fsync(stream.fileno())
        os.chmod(name,0o600);os.replace(name,path)
        directory=os.open(path.parent,os.O_RDONLY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:
        if os.path.exists(name):os.unlink(name)

def encode(value):return json.dumps(str(value),ensure_ascii=False).replace('$','$$')
@dataclasses.dataclass(frozen=True)
class StorageTarget:
    root:pathlib.Path
    instance:str
    bucket:str='ch.so.daten'
    endpoint:str='http://garage:3900'
    region:str='garage'
    admin_token:str=dataclasses.field(default='',repr=False)
    def api(self,name,body=None,**query):
        suffix='?'+urllib.parse.urlencode(query) if query else ''
        request=urllib.request.Request('http://garage:3903/v2/'+name+suffix,data=None if body is None else json.dumps(body).encode(),headers={'Authorization':'Bearer '+self.admin_token,'Content-Type':'application/json'},method='POST' if body is not None or name in ['DeleteBucket','DeleteKey'] else 'GET')
        try:
            with urllib.request.urlopen(request,timeout=10) as response:
                body=response.read()
                return json.loads(body) if body else None
        except urllib.error.HTTPError as error:raise ApiError(name,error.code) from None
        except (OSError,ValueError):raise StorageError('Storage dependency unavailable; details withheld') from None

def load_storage_target(runtime):
    root=pathlib.Path(runtime)
    for key,expected in [('DI_STORAGE_BUCKET','ch.so.daten'),('DI_STORAGE_ENDPOINT','http://garage:3900'),('DI_STORAGE_REGION','garage')]:
        if os.environ.get(key)!=expected:raise StorageError('Unrecognized explicit storage target: '+key)
    instance=os.environ.get('INSTANCE_ID','')
    if not re.fullmatch('[0-9a-f]{32}',instance):raise StorageError('Missing local instance identity')
    # The pinned bookworm tooling supplies Python 3.11's real TOML parser.
    # Escaped quotes/backslashes are credentials, never ad-hoc split delimiters.
    import tomllib
    token=tomllib.loads((root/'garage.toml').read_text()).get('admin',{}).get('admin_token')
    if not isinstance(token,str) or not token or any(ord(c)<33 or ord(c)>126 for c in token):raise StorageError('Invalid private Garage administration configuration')
    return StorageTarget(root,instance,admin_token=token)

class GarageProvisioner:
    def __init__(self,target):
        self.target=target;self.path=target.root/'storage-target.json'
        self.state=json.loads(self.path.read_text()) if self.path.exists() else None
        nodes=target.api('GetClusterStatus')['nodes']
        self.nodes=sorted(node['id'] for node in nodes)
        if len(self.nodes)!=1:raise StorageError('Expected the bound single-node Garage')
        if self.state and (self.state['instance']!=target.instance or self.state['nodes']!=self.nodes or self.state['bucket']!=target.bucket):raise StorageError('Storage instance binding changed')
    def save(self):write_secrets_atomically(self.path,json.dumps(self.state,indent=2)+'\n')
    def ensure_private_bucket(self):
        t=self.target
        try:bucket=t.api('GetBucketInfo',globalAlias=t.bucket)
        except ApiError as error:
            if error.status!=404:raise
            if self.state:raise StorageError('Previously bound bucket disappeared; refusing empty replacement')
            bucket=t.api('CreateBucket',{'globalAlias':t.bucket})
            self.state={'schema_version':1,'instance':t.instance,'nodes':self.nodes,'bucket':t.bucket,'bucket_id':bucket['id'],'keys':{}}
            self.save()
        if self.state is None:raise StorageError('Existing bucket requires explicit reviewed cutover; not a fresh setup')
        if bucket['id']!=self.state['bucket_id']:raise StorageError('Storage bucket identity changed')
        expected={item['accessKeyId'] for item in self.state['keys'].values()}
        if any(any(k['permissions'].values()) and k['accessKeyId'] not in expected for k in bucket['keys']):raise StorageError('Unrecognized bucket principal; explicit cutover required')
        t.api('UpdateBucket',{'websiteAccess':{'enabled':False}},id=bucket['id'])
        return bucket
    def ensure_key(self,kind):
        if kind not in ('writer','reader'):raise StorageError('Unknown storage identity')
        t=self.target;reference=self.state['keys'].get(kind)
        prefix='DI_STORAGE_'+kind.upper()
        configured=(os.environ.get(prefix+'_ACCESS_KEY',''),os.environ.get(prefix+'_SECRET_KEY',''))
        if reference:
            key=t.api('GetKeyInfo',id=reference['accessKeyId'],showSecretKey='true')
            if hashlib.sha256(key['secretAccessKey'].encode()).hexdigest()!=reference['secret_sha256']:raise StorageError('Existing storage key secret changed; no rotation')
            if any(value and value!=expected for value,expected in zip(configured,(key['accessKeyId'],key['secretAccessKey']))):raise StorageError('Conflicting configured credential; no rotation')
        else:
            if any(configured):raise StorageError('Unbound credentials require explicit cutover; never import on normal setup')
            # A name alone never proves ownership of an unbound key.
            candidates=[k for k in t.api('ListKeys') if k['name']=='di-storage-'+kind]
            if candidates:raise StorageError('Unbound named storage key requires explicit identity recovery')
            key=t.api('CreateKey',{'name':'di-storage-'+kind,'deny':{'createBucket':True}})
            self.state['keys'][kind]={'accessKeyId':key['accessKeyId'],'secret_sha256':hashlib.sha256(key['secretAccessKey'].encode()).hexdigest()};self.save()
        t.api('UpdateKey',{'deny':{'createBucket':True}},id=key['accessKeyId'])
        return key
    def reconcile_permissions(self,bucket,writer,reader):
        for key,write in [(writer,True),(reader,False)]:
            self.target.api('DenyBucketKey',{'bucketId':bucket['id'],'accessKeyId':key['accessKeyId'],'permissions':{'read':False,'write':not write,'owner':True}})
            self.target.api('AllowBucketKey',{'bucketId':bucket['id'],'accessKeyId':key['accessKeyId'],'permissions':{'read':True,'write':write,'owner':False}})
    def verify_storage_policy(self):
        bucket=self.target.api('GetBucketInfo',globalAlias=self.target.bucket)
        if bucket['id']!=self.state['bucket_id']:raise StorageError('Storage bucket alias binding changed')
        if bucket['websiteAccess']:raise StorageError('Website access must be disabled')
        expected={self.state['keys'][kind]['accessKeyId']:{'read':True,'write':kind=='writer','owner':False} for kind in ['writer','reader']}
        active={k['accessKeyId']:k['permissions'] for k in bucket['keys'] if any(k['permissions'].values())}
        if active!=expected:raise StorageError('Storage permissions differ from exact reader/writer policy')
        for access in expected:
            key=self.target.api('GetKeyInfo',id=access)
            if key['permissions']['createBucket'] or key['expired']:raise StorageError('Storage key has unexpected administrative rights or expiry')
            if any(b['id']!=bucket['id'] and any(b['permissions'].values()) for b in key['buckets']):raise StorageError('Storage key also authorizes another bucket')
        return {'verified':True,'bound_bucket_verified':True,'website_access':False,'reader_read_only':True,'writer_owner':False}
    def render_config(self,key):
        # Key material never becomes shell text, process arguments or web ENV.
        if any('\n' in key[name] or '\r' in key[name] for name in ['accessKeyId','secretAccessKey']):raise StorageError('Invalid credential encoding')
        return '\n'.join(['[storage]','type = s3','provider = Other','env_auth = false','access_key_id = '+key['accessKeyId'],'secret_access_key = '+key['secretAccessKey'],'endpoint = '+self.target.endpoint,'region = '+self.target.region,'force_path_style = true','no_check_bucket = true',''])
    def render_reader_config(self,key):write_secrets_atomically(self.target.root/'origin.conf',self.render_config(key))
    def render_writer_config(self,key):write_secrets_atomically(self.target.root/'operator.conf',self.render_config(key))
    def setup(self):
        bucket=self.ensure_private_bucket();writer=self.ensure_key('writer');reader=self.ensure_key('reader')
        self.reconcile_permissions(bucket,writer,reader);report=self.verify_storage_policy()
        updates={}
        for kind,key in [('WRITER',writer),('READER',reader)]:
            updates['DI_STORAGE_'+kind+'_ACCESS_KEY']=key['accessKeyId'];updates['DI_STORAGE_'+kind+'_SECRET_KEY']=key['secretAccessKey']
        env=self.target.root/'runtime.env'
        lines=[];seen=set()
        for line in env.read_text().splitlines():
            match=re.match(r'^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=',line)
            name=match.group(1) if match else None
            if name in updates:
                seen.add(name)
                # Compose already decoded the value. Preserve its exact valid source
                # encoding and location when unchanged; never parse secret text here.
                if os.environ.get(name)!=updates[name]:line=name+'='+encode(updates[name])
            lines.append(line)
        lines.extend(name+'='+encode(value) for name,value in updates.items() if name not in seen)
        content='\n'.join(lines)+'\n'
        if content!=env.read_text():write_secrets_atomically(env,content)
        self.render_reader_config(reader);self.render_writer_config(writer)
        return report
if __name__=='__main__':
    try:
        import argparse
        parser=argparse.ArgumentParser();parser.add_argument('action',choices=['setup','verify'],nargs='?',default='setup');args=parser.parse_args()
        provisioner=GarageProvisioner(load_storage_target('/runtime'))
        print(json.dumps(provisioner.setup() if args.action=='setup' else provisioner.verify_storage_policy()))
    except Exception as error:
        import sys
        print(str(error) if isinstance(error,StorageError) else 'Storage setup failed; private details withheld',file=sys.stderr);sys.exit(1)
