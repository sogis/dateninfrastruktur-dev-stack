#!/usr/bin/env python3
"""G16: real fresh target and known, nonempty MA-F→G1 upgrade; no user dumps."""
import hashlib,io,json,os,pathlib,secrets,subprocess,tarfile,sys
from compose_runtime import ROOT,ComposeContext,init_context,update_context,write_private
from test_consolidation_f1 import reserve_ports,cleanup
from migration_db import target_sql,row_hash_sql

SOURCE_ADMIN='b4a8c2726da16373ee9e0fd02ecb715fba482612'
SOURCE_STACK='67ffd5801d40a98a0b5f8bc0706288cb4970bb62'
def archive(repo,commit,destination):
    data=subprocess.check_output(['git','-C',str(repo),'archive',commit])
    destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        if any(pathlib.PurePosixPath(m.name).is_absolute() or '..' in pathlib.PurePosixPath(m.name).parts for m in tar):raise RuntimeError('Unsafe source archive')
        tar.extractall(destination)

def run():
    c=init_context('mag-g1-schema-'+secrets.token_hex(5),reserve_ports(),True)
    def command(args):
        p=c.command(args,check=False)
        with (c.runtime/'schema-test.log').open('a') as out:out.write(c.redact(p.stdout+p.stderr))
        if p.returncode:raise RuntimeError('G1 schema command failed; '+str(c.runtime/'schema-test.log'))
        return p.stdout
    def query(q):return target_sql(c,'dateninfrastruktur_management',q)
    candidate_tool=c.values['TOOL_IMAGE']
    try:
        command(['build','postgres','management-tool-build'])
        if '--fresh-only' in sys.argv:
            command(['up','--no-build','-d','--wait','--wait-timeout','120','postgres'])
            command(['--profile','setup','run','--rm','--no-deps','postgres-init'])
            print(command(['--profile','setup','run','--rm','--no-deps','management-setup']).strip())
            print(command(['--profile','setup','run','--rm','--no-deps','management-setup','verify']).strip())
            assert query('SELECT di_ops.single_storage_contract();')=='t'
            assert query('SELECT count(*) FROM di_management.dataset;')=='0'
            print('PASS G16 fresh current schema with no implicit data/grant seed')
            return
        source=c.runtime/'source';admin=source/'dateninfrastruktur-admin';stack=source/'dateninfrastruktur-dev-stack'
        archive(ROOT.parent/'dateninfrastruktur-admin',SOURCE_ADMIN,admin);archive(ROOT,SOURCE_STACK,stack)
        source_image='dateninfrastruktur-g1-source-tests:'+c.project
        p=subprocess.run(['docker','build','--target','test-tools','--build-context','postgres_tools=docker-image://'+c.values['POSTGRES_IMAGE'],'--build-context','stack_source='+str(stack),'-t',source_image,str(admin)],capture_output=True,text=True)
        write_private(c.runtime/'source-build.log',c.redact(p.stdout+p.stderr));assert p.returncode==0,'Source fixture build failed; private source-build.log'
        c=update_context(c,{'TOOL_IMAGE':source_image,'TEST_TOOL_IMAGE':source_image})
        command(['up','--no-build','-d','--wait','--wait-timeout','120','postgres'])
        command(['--profile','setup','run','--rm','--no-deps','postgres-init'])
        command(['--profile','setup','run','--rm','--no-deps','--entrypoint','python3','management-setup','/opt/admin/scripts/setup_explicit.py','setup'])
        expected=json.loads((ROOT.parent/'dateninfrastruktur-admin/db/upgrade/ma-f-to-ma-g1.json').read_text())['fromFingerprint']
        assert query('SELECT fingerprint FROM di_ops.contract_fingerprint WHERE singleton;')==expected
        command(['--profile','test','run','--rm','--no-deps','test-fixture'])
        assert int(query('SELECT count(*) FROM di_management.distribution;'))>0
        assert int(query('SELECT count(*) FROM audit.row_change;'))>0
        before=query(row_hash_sql('SELECT * FROM audit.row_change'))
        stable={table:query(row_hash_sql('SELECT * FROM di_management.'+table)) for table in ['principal','authorityassignment','accessgrant','accessdecision','dataset','datasetissue','dataversion']}
        distribution=query(row_hash_sql("SELECT t_id,t_ili_tid,objectkey,sha256,bytesize,version,availability FROM di_management.distribution"))
        c=update_context(c,{'TOOL_IMAGE':candidate_tool})
        # Real unknown predecessor must stop before the first DDL, retaining even the unknown fingerprint.
        query("UPDATE di_ops.contract_fingerprint SET fingerprint='"+'0'*64+"' WHERE singleton;")
        p=c.command(['--profile','migration','run','--rm','--no-deps','management-upgrade'],check=False)
        write_private(c.runtime/'unknown-source.log',c.redact(p.stdout+p.stderr));assert p.returncode!=0
        assert query("SELECT count(*) FROM information_schema.columns WHERE table_schema='di_management' AND table_name='distribution' AND column_name='storageprofile';")=='1'
        assert query(row_hash_sql('SELECT * FROM audit.row_change'))==before
        query('UPDATE di_ops.contract_fingerprint SET fingerprint='+"'"+expected+"' WHERE singleton;")
        # Diagnostic transport is identical psql/ON_ERROR_STOP; errors stay only in this synthetic fixture.
        write_private(c.runtime/'upgrade-probe.py',"""import sys,os,pathlib,subprocess
sys.path.insert(0,'/opt/admin/scripts')
import upgrade_contract as u
def execute(query):
 p=subprocess.run(['psql','-X','-q','-At','-v','ON_ERROR_STOP=1'],input=query,capture_output=True,text=True)
 if p.returncode:
  pathlib.Path('/runtime/upgrade-error.txt').write_text(p.stderr)
  pathlib.Path('/runtime/upgrade-error.txt').chmod(0o600)
  raise RuntimeError('Synthetic upgrade failed; private upgrade-error.txt')
 return p.stdout.strip()
u.sql=execute
u.apply()
""")
        print(command(['--profile','migration','run','--rm','--no-deps','--entrypoint','python3','management-upgrade','/runtime/upgrade-probe.py']).strip())
        assert query('SELECT di_ops.single_storage_contract();')=='t'
        assert query(row_hash_sql('SELECT * FROM audit.row_change'))==before
        assert all(query(row_hash_sql('SELECT * FROM di_management.'+table))==value for table,value in stable.items())
        assert query(row_hash_sql("SELECT t_id,t_ili_tid,objectkey,sha256,bytesize,version,availability FROM di_management.distribution"))==distribution
        print(command(['--profile','setup','run','--rm','--no-deps','management-setup','verify']).strip())
        # Repeating the explicit upgrade is read-only and never clears or seeds data.
        print(command(['--profile','migration','run','--rm','--no-deps','management-upgrade']).strip())
        write_private(c.runtime/'roundtrip.py',"""import sys,os,pathlib,tempfile,subprocess
sys.path.insert(0,'/opt/admin/scripts')
from management_db import R,D
jar=next((R/'.runtime/tools/ili2pg').glob('ili2pg-*.jar'))
args=['-jar',str(jar),'--export','--exportTid','--dbhost',os.environ['PGHOST'],'--dbport',os.environ['PGPORT'],'--dbdatabase',os.environ['PGDATABASE'],'--dbusr',os.environ['PGUSER'],'--dbpwd',os.environ['PGPASSWORD'],'--dbschema','di_management','--models','SO_AGI_DataInfrastructure_Catalog_20261105;SO_AGI_DataInfrastructure_Access_20261105','--modeldir',str(R/'models'),'/runtime/upgraded.xtf']
with tempfile.NamedTemporaryFile(mode='w',dir=D,suffix='.args',delete=False) as f:
 f.write('\\n'.join('"'+a.replace('\\\\','\\\\\\\\').replace('"','\\\\"')+'"' for a in args));p=pathlib.Path(f.name)
try:
 result=subprocess.run(['java','@'+str(p)],capture_output=True,text=True)
 if result.returncode:raise RuntimeError('Actual upgraded DB XTF export failed')
finally:p.unlink()
validator=next((R/'.runtime/tools/ilivalidator').glob('ilivalidator-*.jar'))
p=subprocess.run(['java','-jar',str(validator),'--modeldir',str(R/'models'),'--allObjectsAccessible','--forceTypeValidation','/runtime/upgraded.xtf'],capture_output=True,text=True)
pathlib.Path('/runtime/roundtrip-validation.log').write_text(p.stdout+p.stderr)
assert p.returncode==0,'Actual exported XTF violates target models'
print('PASS G16 stock ili2pg export and target-model validation of nonempty upgraded database')
""")
        print(command(['--profile','setup','run','--rm','--no-deps','--entrypoint','python3','management-setup','/runtime/roundtrip.py']).strip())
        fresh=init_context('mag-g1-fresh-'+secrets.token_hex(5),reserve_ports(),True)
        fresh=update_context(fresh,{'TOOL_IMAGE':candidate_tool,'POSTGRES_IMAGE':c.values['POSTGRES_IMAGE']})
        try:
            for args in [['up','--no-build','-d','--wait','--wait-timeout','120','postgres'],['--profile','setup','run','--rm','--no-deps','postgres-init'],['--profile','setup','run','--rm','--no-deps','management-setup'],['--profile','setup','run','--rm','--no-deps','management-setup','verify']]:
                p=fresh.command(args,check=False)
                with (fresh.runtime/'fresh-schema.log').open('a') as out:out.write(fresh.redact(p.stdout+p.stderr))
                assert p.returncode==0,'Fresh target schema failed; '+str(fresh.runtime/'fresh-schema.log')
            assert target_sql(fresh,'dateninfrastruktur_management','SELECT di_ops.single_storage_contract();')=='t'
            assert target_sql(fresh,'dateninfrastruktur_management','SELECT count(*) FROM di_management.dataset;')=='0'
            print('PASS G16 independent fresh target schema, no implicit data/grant seed')
        finally:cleanup(fresh)
        print('PASS G16: nonempty known schema upgraded; unknown source refused; business IDs, private references and historical audit identical')
    finally:cleanup(c)
if __name__=='__main__':run()
