#!/usr/bin/env python3
"""G14/G15/G17/G19 on the canonical topology and synthetic PG/S3 state."""
import hashlib,json,pathlib,secrets,subprocess,sys
from ingestion_cutover_g1 import probe
from compose_runtime import ROOT,init_context,ComposeContext,write_private,update_context
from compose_operations import build,setup
from test_consolidation_f1 import reserve_ports,cleanup
from test_consolidation_f4 import browser,check_topology
from migration_db import target_sql,row_hash_sql

def run():
    c=init_context('mag-g1-cutover-'+secrets.token_hex(5),reserve_ports(),True)
    def command(args):
        p=c.command(args,check=False)
        with (c.runtime/'g1-integration.log').open('a') as out:out.write(c.redact(p.stdout+p.stderr))
        if p.returncode:raise RuntimeError('G1 canonical integration failed; '+str(c.runtime/'g1-integration.log'))
        return p.stdout
    try:
        build(c);setup(c);c=ComposeContext(c.env_file)
        prefix='maf-f4-g1-'+secrets.token_hex(4)
        command(['--profile','test','run','--rm','--no-deps','-e','DI_TEST_DATASET_PREFIX='+prefix,'test-fixture'])
        garage=json.loads(subprocess.check_output(['docker','inspect',command(['ps','-q','garage']).strip()]))[0]
        binding={'project':c.project,'instance':c.values['INSTANCE_ID'],'garage_container':garage['Id'],'garage_image':garage['Image'],'mounts':[{k:v for k,v in m.items() if k in ['Type','Name','Destination']} for m in garage['Mounts']]}
        write_private(c.runtime/'g1-host-binding.json',json.dumps(binding,sort_keys=True))
        write_private(c.runtime/'cutover-fixture.py',(ROOT/'tests/ingestion/cutover-fixture.py').read_text())
        variables=['DI_TEST_FIXTURE','COMPOSE_PROJECT_NAME','INSTANCE_ID','DI_STORAGE_BUCKET','DI_STORAGE_ENDPOINT','DI_STORAGE_REGION','DI_STORAGE_WRITER_ACCESS_KEY','DI_STORAGE_WRITER_SECRET_KEY','DI_STORAGE_READER_ACCESS_KEY','DI_STORAGE_READER_SECRET_KEY']
        flags=[item for name in variables for item in ['-e',name]]
        def tool(action):
            return command(['--profile','setup','run','--rm','--no-deps',*flags,'-e','G1_GATEWAY_AUTHORITY=localhost:'+c.values['GATEWAY_PORT'],'--entrypoint','python3','management-setup','/runtime/cutover-fixture.py',action])
        operator='--operator' in sys.argv
        print(tool('prepare-operator' if operator else 'prepare').strip(),flush=True)
        if operator:
            private=c.runtime/'ma-g1-cutover';private.mkdir(mode=0o700)
            write_private(private/'host-binding.json',json.dumps({'binding':binding}))
            write_private(c.runtime/'cutover-operator-g1.py',(ROOT/'services/garage/cutover-operator-g1.py').read_text())
            source=json.loads((c.runtime/'g1-source-key.json').read_text())
            c=update_context(c,{prefix+'_'+field:source[name] for prefix in ['GARAGE_DEFAULT','GARAGE_MANAGED','GARAGE_ORIGIN'] for field,name in [('ACCESS_KEY','accessKeyId'),('SECRET_KEY','secretAccessKey')]})
            def operation(action):
                flags=[v for k in ['INSTANCE_ID',*[k for k in c.values if k.startswith(('GARAGE_DEFAULT_','GARAGE_MANAGED_','GARAGE_ORIGIN_'))]] for v in ['-e',k]]
                return command(['--profile','setup','run','--rm','--no-deps',*flags,'--entrypoint','python3','management-setup','/runtime/cutover-operator-g1.py',action])
            for action in ['plan','apply','provision']:print(operation(action).strip(),flush=True)
        command(['up','--no-build','-d','--wait','--wait-timeout','300'])
        check_topology(c)
        browser(c) # Existing normal PKCE + same-JWT grant/revoke + HEAD/Range/ETag regression.
        if not operator:print(tool('finish').strip(),flush=True)
        (c.runtime/'ma-g1-cutover').mkdir(mode=0o700,exist_ok=True)
        write_private(c.runtime/'g1-probe-fixture.json',(c.runtime/'fixture.json').read_text())
        before_probe=target_sql(c,'dateninfrastruktur_management',row_hash_sql('SELECT * FROM audit.row_change'))
        probe(c,'capture')
        if operator:
            private=c.runtime/'ma-g1-cutover'
            digest=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            write_private(private/'runtime-verified.json',json.dumps({'plan_sha256':digest(json.loads((private/'bound-plan.json').read_text())),'host_binding_sha256':digest(binding),'probe_sha256':hashlib.sha256((c.runtime/'g1-download-probes.json').read_bytes()).hexdigest()}))
            print(operation('finish').strip(),flush=True)
        assert target_sql(c,'dateninfrastruktur_management',row_hash_sql('SELECT * FROM audit.row_change'))==before_probe
        # Real runtime inventories, no metadata-only or missing-object negative controls.
        storage_secrets=[c.values[k] for k in ['DI_STORAGE_WRITER_ACCESS_KEY','DI_STORAGE_WRITER_SECRET_KEY','DI_STORAGE_READER_ACCESS_KEY','DI_STORAGE_READER_SECRET_KEY']]
        rows=[json.loads(line) for line in command(['ps','--format','json']).splitlines()]
        for row in rows:
            if row['Service'] in ['admin','sodata','gateway','jenkins']:
                info=json.loads(subprocess.check_output(['docker','inspect',row['ID']]))[0]
                assert not any(secret in value for secret in storage_secrets for value in info['Config'].get('Env',[])),'Storage credential in web ENV'
        before={name:(c.runtime/name).read_bytes() for name in ['runtime.env','origin.conf','operator.conf','storage-target.json']}
        audit=target_sql(c,'dateninfrastruktur_management',row_hash_sql('SELECT * FROM audit.row_change'))
        setup(c)
        assert all((c.runtime/name).read_bytes()==value for name,value in before.items()),'Public setup rotates storage state'
        assert target_sql(c,'dateninfrastruktur_management',row_hash_sql('SELECT * FROM audit.row_change'))==audit
        before_ids={row['Service']:row['ID'] for row in rows}
        command(['up','--no-build','--force-recreate','-d','--wait','--wait-timeout','180','garage','origin','gateway'])
        after=[json.loads(line) for line in command(['ps','--format','json']).splitlines()]
        assert all(next(row['ID'] for row in after if row['Service']==service)!=before_ids[service] for service in ['garage','origin','gateway'])
        print(command(['--profile','tools','run','--rm','--no-deps','storage-verify']).strip())
        # Check preserved current/historical bytes and still-valid active/revoked tokens without a new grant.
        verify='''import json,urllib.request,urllib.error,hashlib,pathlib
f=json.loads(pathlib.Path('/runtime/fixture.json').read_text());t=json.loads(pathlib.Path('/runtime/f4-tokens.json').read_text())
for x in f['files']:
 h={'Host':'localhost:PORT'}
 if x['kind']=='restricted':h['Authorization']='Bearer '+t['ben']
 with urllib.request.urlopen(urllib.request.Request('http://gateway:9080'+x['path'],headers=h),timeout=15) as r:assert r.status==200 and hashlib.sha256(r.read()).hexdigest()==x['sha256']
 if x['kind']=='restricted':
  h['Authorization']='Bearer '+t['anna']
  try:urllib.request.urlopen(urllib.request.Request('http://gateway:9080'+x['path'],headers=h));raise AssertionError('Revoked token permitted')
  except urllib.error.HTTPError as e:assert e.code==403
print('PASS G13/G17/G18/G19 actual Garage/Origin/Gateway recreation retains bytes, keys and active/revoked rights; no writer credentials in web ENV')
'''.replace('PORT',c.values['GATEWAY_PORT'])
        write_private(c.runtime/'recreate-verify.py',verify)
        print(command(['--profile','setup','run','--rm','--no-deps','--entrypoint','python3','management-setup','/runtime/recreate-verify.py']).strip())
        probe(c,'verify')
        check_topology(c)
    finally:cleanup(c)
if __name__=='__main__':run()
