#!/usr/bin/env python3
"""F11/F13 regression only: Compose credentials, real copy and permission boundaries."""
import hashlib,json,secrets
from compose_runtime import ROOT,init_context,update_context,ComposeContext,write_private,render
from consolidation import private_write
from test_consolidation_f1 import cleanup

def job(c,code):return c.command(['--profile','migration','run','--rm','--no-deps','--entrypoint','python3','migration-storage','-'],code)
def run(source,target):
    source=update_context(source,{'GARAGE_DEFAULT_SECRET_KEY':"Source$Quote'\"Back\\Slash_0123456789",'GARAGE_ORIGIN_ACCESS_KEY':'maf2-origin-'+secrets.token_hex(6),'GARAGE_ORIGIN_SECRET_KEY':"Origin$Quote'\"Back\\Slash_0123456789",'DI_MIGRATION_IMPORT_KEYS':'true'})
    render(source)
    source.command(['build','management-tool-build'])
    target=update_context(target,{'TOOL_IMAGE':source.values['TOOL_IMAGE'],'MIGRATION_SOURCE_NETWORK':source.project+'_default','GARAGE_ORIGIN_ACCESS_KEY':'','GARAGE_ORIGIN_SECRET_KEY':''})
    source.command(['up','--no-build','-d','--wait','--wait-timeout','120','garage'])
    source.command(['--profile','setup','run','--rm','--no-deps','garage-setup']);source=ComposeContext(source.env_file)
    target=update_context(target,{'GARAGE_ORIGIN_ACCESS_KEY':source.values['GARAGE_ORIGIN_ACCESS_KEY'],'GARAGE_ORIGIN_SECRET_KEY':source.values['GARAGE_ORIGIN_SECRET_KEY'],'GARAGE_MANAGED_ACCESS_KEY':source.values['GARAGE_DEFAULT_ACCESS_KEY'],'GARAGE_MANAGED_SECRET_KEY':source.values['GARAGE_DEFAULT_SECRET_KEY'],'DI_MIGRATION_IMPORT_KEYS':'true'})
    render(target)
    target.command(['up','--no-build','-d','--wait','--wait-timeout','120','garage'])
    target.command(['--profile','setup','run','--rm','--no-deps','garage-setup'])
    target.command(['--profile','setup','run','--rm','--no-deps','garage-setup'])
    cfg={'bucket':'di-managed-private','source':{'endpoint':'http://'+source.project+'-garage-1:3900','access_key':source.values['GARAGE_DEFAULT_ACCESS_KEY'],'secret_key':source.values['GARAGE_DEFAULT_SECRET_KEY']},'target':{'endpoint':'http://'+target.project+'-garage-1:3900','access_key':target.values['GARAGE_MANAGED_ACCESS_KEY'],'secret_key':target.values['GARAGE_MANAGED_SECRET_KEY']}}
    private_write(target.runtime/'migration/storage.json',cfg)
    private_write(target.runtime/'migration/probe.json',{'origin':{'endpoint':cfg['target']['endpoint'],'access_key':target.values['GARAGE_ORIGIN_ACCESS_KEY'],'secret_key':target.values['GARAGE_ORIGIN_SECRET_KEY']},'legacy':{'endpoint':cfg['target']['endpoint'],'access_key':target.values['GARAGE_DEFAULT_ACCESS_KEY'],'secret_key':target.values['GARAGE_DEFAULT_SECRET_KEY']}})
    prelude="import json,sys,os\nsys.path.insert(0,'/opt/stack-tools/migration')\nfrom storage import client\nassert os.environ['DI_COMPOSE_TEST_FIXTURE']=='true'\nc=json.load(open('/runtime/migration/storage.json'));p=json.load(open('/runtime/migration/probe.json'))\nassert all(v['endpoint'].startswith('http://maf-f2-garage-') for v in [c['source'],c['target'],*p.values()])\n"
    job(target,prelude+"client(c['source']).put_object(Bucket=c['bucket'],Key='downloads/codec.csv',Body=b'kind,value\\ncodec,42\\n',ContentType='text/csv',Metadata={'purpose':'codec-regression'})\n")
    for mode in ['source-inventory','copy','verify','copy']:
        result=target.command(['--profile','migration','run','--rm','--no-deps','migration-storage',mode]);print(result.stdout.strip(),flush=True)
    permissions="""from botocore.exceptions import ClientError
origin=client(p['origin']);legacy=client(p['legacy']);bucket=c['bucket'];key='downloads/codec.csv'
assert origin.get_object(Bucket=bucket,Key=key)['Body'].read()==b'kind,value\ncodec,42\n'
legacy.put_object(Bucket='ch.so.daten',Key='codec-legacy',Body=b'legacy')
assert legacy.get_object(Bucket='ch.so.daten',Key='codec-legacy')['Body'].read()==b'legacy'
for action in [lambda:origin.put_object(Bucket=bucket,Key=key,Body=b'forbidden'),lambda:legacy.get_object(Bucket=bucket,Key=key)]:
 try:action()
 except ClientError as e:assert e.response['ResponseMetadata']['HTTPStatusCode']==403
 else:raise AssertionError('private permission boundary bypassed')
print('PASS real S3 copy, bytes/metadata, replay, imported origin read positive/write403, legacy read positive/private403')
"""
    # Keep literal backslash-n escapes in the code passed through stdin.
    target.command(['up','--no-build','-d','--wait','--wait-timeout','120','origin'])
    actual=target.command(['--profile','tools','run','--rm','--no-deps','storage-tool','cat','managed:di-managed-private/downloads/codec.csv']).stdout
    assert actual=='kind,value\ncodec,42\n','rclone operator did not receive the same graphic secret'
    job(target,prelude+"import urllib.request\nassert urllib.request.urlopen('http://origin:8080/downloads/codec.csv').read()==b'kind,value\\ncodec,42\\n'\n")
    permissions=permissions.replace("b'kind,value\ncodec,42\n'","b'kind,value\\ncodec,42\\n'")
    print(job(target,prelude+permissions).stdout.strip(),flush=True)
    original=target.values['GARAGE_ORIGIN_SECRET_KEY'];synthetic="quote '\" $dollar \\ path\nline"
    bad=update_context(target,{'GARAGE_ORIGIN_SECRET_KEY':synthetic})
    check="import os,hashlib;assert hashlib.sha256(os.environ['GARAGE_ORIGIN_SECRET_KEY'].encode()).hexdigest()=="+repr(hashlib.sha256(synthetic.encode()).hexdigest())
    bad.command(['--profile','setup','run','--rm','--no-deps','--entrypoint','python3','garage-setup','-c',check])
    rejected=bad.command(['--profile','setup','run','--rm','--no-deps','garage-setup'],check=False)
    assert rejected.returncode!=0 and 'INVALID_GARAGE_CREDENTIAL' in rejected.stdout+rejected.stderr
    target=update_context(bad,{'GARAGE_ORIGIN_SECRET_KEY':original})
    print(job(target,prelude+permissions).stdout.strip(),flush=True)
    print('PASS F11/F13 delta: Compose transports quotes/dollars/backslashes/newlines exactly; invalid control characters rejected before API/key changes; valid graphic secrets work through S3, rclone operator and origin with unchanged boundaries',flush=True)

if __name__=='__main__':
    contexts=[init_context('maf-f2-garage-'+kind+'-'+secrets.token_hex(4),test_fixture=True) for kind in ['source','target']]
    try:run(*contexts)
    finally:
        for c in reversed(contexts):cleanup(ComposeContext(c.env_file))
