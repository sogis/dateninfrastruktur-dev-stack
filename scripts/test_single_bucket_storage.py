#!/usr/bin/env python3
"""G10–G13/G18: real canonical Compose Garage, own synthetic reader/writer state."""
import json,pathlib,secrets,sys
from compose_runtime import ROOT,init_context,ComposeContext,write_private
from ingestion_test_runtime import reserve_ports,cleanup

def run():
    c=init_context('mag-g1-storage-'+secrets.token_hex(5),reserve_ports(),True)
    def command(args):
        p=c.command(args,check=False)
        with (c.runtime/'storage-test.log').open('a') as stream:stream.write(c.redact(p.stdout+p.stderr))
        if p.returncode:raise RuntimeError('G1 storage command failed; private '+str(c.runtime/'storage-test.log'))
        return p.stdout
    try:
        command(['build','postgres','management-tool-build'])
        command(['up','--no-build','-d','--wait','--wait-timeout','120','garage'])
        command(['--profile','setup','run','--rm','--no-deps','garage-setup'])
        c=ComposeContext(c.env_file)
        # A trailing unrelated line used to make setup move all credential lines.
        write_private(c.env_file,c.env_file.read_text()+'# unrelated context position must remain stable\n')
        before={name:(c.runtime/name).read_bytes() for name in ['runtime.env','origin.conf','operator.conf','storage-target.json']}
        command(['--profile','setup','run','--rm','--no-deps','garage-setup'])
        assert all((c.runtime/name).read_bytes()==value for name,value in before.items()),'Setup rotated credentials or references'
        fixture={'writer':{k:c.values['DI_STORAGE_WRITER_'+k] for k in ['ACCESS_KEY','SECRET_KEY']},'reader':{k:c.values['DI_STORAGE_READER_'+k] for k in ['ACCESS_KEY','SECRET_KEY']}}
        write_private(c.runtime/'storage-test.json',json.dumps(fixture))
        write_private(c.runtime/'storage-test.py','''import json,boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from pathlib import Path
x=json.loads(Path('/runtime/storage-test.json').read_text())
def client(kind):
 k=x[kind];return boto3.client('s3',endpoint_url='http://garage:3900',region_name='garage',aws_access_key_id=k['ACCESS_KEY'],aws_secret_access_key=k['SECRET_KEY'],config=Config(signature_version='s3v4',s3={'addressing_style':'path'}))
w=client('writer');r=client('reader');bucket='ch.so.daten';key='downloads/11111111-1111-4111-8111-111111111111/data.csv';body=b'id;value\\n001;synthetic\\n'
w.put_object(Bucket=bucket,Key=key,Body=body,ContentType='text/csv')
assert r.get_object(Bucket=bucket,Key=key)['Body'].read()==body
for label,call in [('reader-write',lambda:r.put_object(Bucket=bucket,Key=key,Body=b'forbidden')),('reader-delete',lambda:r.delete_object(Bucket=bucket,Key=key)),('writer-create-bucket',lambda:w.create_bucket(Bucket='forbidden-g1-new-bucket'))]:
 try:call();raise AssertionError(label+' permitted')
 except ClientError as e:assert e.response['ResponseMetadata']['HTTPStatusCode']==403,label
assert r.get_object(Bucket=bucket,Key=key)['Body'].read()==body
import urllib.request,urllib.error
try:urllib.request.urlopen('http://garage:3900/'+bucket+'/'+key);raise AssertionError('anonymous read permitted')
except urllib.error.HTTPError as e:assert e.code==403
w.delete_object(Bucket=bucket,Key=key)
print('PASS G10/G11/G12/G13/G18: reader GET, writer PUT/GET/DELETE, denied reader mutation, writer bucket creation and anonymous existing-object read; identical setup state')
''')
        print(command(['--profile','setup','run','--rm','--no-deps','--entrypoint','python3','management-setup','/runtime/storage-test.py']),end='')
        print('Private evidence: '+str(c.runtime/'storage-test.log'))
    finally:cleanup(c)
if __name__=='__main__':run()
