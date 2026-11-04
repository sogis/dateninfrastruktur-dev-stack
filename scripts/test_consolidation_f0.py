#!/usr/bin/env python3
import copy,hashlib,json,pathlib,platform,secrets,subprocess,sys,tempfile,unittest,os
from unittest.mock import Mock,patch
from consolidation import STACK,reference,verify_ownership,with_verified_resource,private_write
class OwnershipTest(unittest.TestCase):
    def test_bad_ids_labels_projects_mounts_rejected_before_mutation(self):
        scope={'workspace':'/owned','foundation_project':'owned-project'}
        actual={'Id':'a'*64,'Name':'/owned-postgres-1','Image':'sha256:fixed','Config':{'Image':'postgres:test','Labels':{'com.docker.compose.project':'owned-project','com.docker.compose.service':'postgres','com.docker.compose.project.working_dir':'/owned/dateninfrastruktur-dev-stack','com.docker.compose.project.config_files':'/owned/dateninfrastruktur-dev-stack/compose.yaml'}},'State':{'Status':'running'},'HostConfig':{'PortBindings':{},'RestartPolicy':{'Name':'no'}},'Mounts':[{'Type':'volume','Name':'owned-volume','Source':'/vol/owned','Destination':'/var/lib/postgresql/data','RW':True}]}
        ref={**reference(actual),'source_kind':'foundation','service':'postgres'}
        self.assertEqual(verify_ownership(ref,scope,actual),'a'*64)
        for change in [lambda x:x.update(id='b'*64),lambda x:x.update(name='/foreign'),lambda x:x['mounts'][0].update(Name='foreign')]:
            bad=copy.deepcopy(ref);change(bad);mutation=Mock()
            with patch('consolidation.inspect',return_value=actual):
                with self.assertRaisesRegex(RuntimeError,'OWNERSHIP_MISMATCH'):with_verified_resource(bad,scope,mutation)
            mutation.assert_not_called()
        for key,value in [('com.docker.compose.project','foreign'),('com.docker.compose.service','foreign'),('com.docker.compose.project.working_dir','/foreign')]:
            bad=copy.deepcopy(actual);bad['Config']['Labels'][key]=value;mutation=Mock()
            with patch('consolidation.inspect',return_value=bad):
                with self.assertRaisesRegex(RuntimeError,'OWNERSHIP_MISMATCH'):with_verified_resource(ref,scope,mutation)
            mutation.assert_not_called()
        with self.assertRaisesRegex(RuntimeError,'full container ID'):verify_ownership({**ref,'id':'named-container'},scope)
    def test_private_output_modes(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'private/plan.json';private_write(p,{'no':'secret'})
            self.assertEqual(p.stat().st_mode&0o777,0o600);self.assertEqual(p.parent.stat().st_mode&0o777,0o700)
def pg_probe():
    root=STACK/'.runtime/consolidation-f0';root.mkdir(parents=True,exist_ok=True);root.chmod(0o700)
    project='maf-f0-'+secrets.token_hex(6);run=root/project;run.mkdir(mode=0o700)
    image='dateninfrastruktur-postgres:maf-f0-'+hashlib.sha256((STACK/'services/postgres/Dockerfile').read_bytes()).hexdigest()[:12]
    env=run/'probe.env';env.write_text('PROBE_PASSWORD='+secrets.token_urlsafe(32)+'\nF0_POSTGRES_IMAGE='+image+'\n');env.chmod(0o600)
    base=['docker','compose','--file',str(STACK/'tests/consolidation/pg-probe.compose.yaml'),'--env-file',str(env),'--project-name',project]
    def call(args,input=None):
        p=subprocess.run(base+args,capture_output=True,text=True,input=input)
        (run/('command-'+str(len(list(run.glob('command-*'))))+'.log')).write_text(p.stdout+p.stderr)
        if p.returncode:raise RuntimeError('Own F02 command failed: '+args[0]+'; see private '+str(run))
        return p.stdout.strip()
    existing=subprocess.check_output(['docker','ps','-aq','--filter','label=com.docker.compose.project='+project],text=True).strip()
    if existing:raise RuntimeError('Refusing an existing test project')
    try:
        call(['build','postgres']);call(['up','-d','--wait','--wait-timeout','120'])
        cid=call(['ps','-q','postgres']);observed=json.loads(subprocess.check_output(['docker','inspect',cid],text=True))[0]
        assert observed['Config']['Labels']['com.docker.compose.project']==project
        info=json.loads(subprocess.check_output(['docker','image','inspect',image],text=True))[0]
        native={'arm64':'arm64','aarch64':'arm64','x86_64':'amd64'}[platform.machine()];assert info['Architecture']==native
        def sql(db,q):return call(['exec','-T','postgres','psql','-X','-U','postgres','-d',db,'-At','-v','ON_ERROR_STOP=1'],q)
        version=int(sql('postgres',"SELECT current_setting('server_version_num');"));assert 160010<=version<170000
        sql('postgres','CREATE DATABASE keycloak TEMPLATE template0; CREATE DATABASE superset TEMPLATE template0; CREATE DATABASE dateninfrastruktur_management TEMPLATE template0;')
        sql('dateninfrastruktur_management','CREATE EXTENSION postgis; CREATE EXTENSION "uuid-ossp";')
        postgis=sql('dateninfrastruktur_management','SELECT postgis_lib_version();');assert postgis=='3.5.2'
        for db in ['template1','keycloak','superset']:assert sql(db,"SELECT count(*) FROM pg_extension WHERE extname IN ('postgis','uuid-ossp');")=='0'
        evidence={'project':project,'image':image,'image_id':info['Id'],'architecture':native,'server_version_num':version,'postgis':postgis,'databases':['keycloak','superset','dateninfrastruktur_management'],'postgis_only_in_management':True}
        private_write(run/'result.json',evidence);print(json.dumps(evidence))
    finally:
        # Check every resource before deleting this fresh, disposable probe volume.
        ids=subprocess.check_output(['docker','ps','-aq','--filter','label=com.docker.compose.project='+project],text=True).split()
        for owned in ids:
            obj=json.loads(subprocess.check_output(['docker','inspect',owned],text=True))[0]
            assert obj['Config']['Labels']['com.docker.compose.project']==project
            assert obj['Config']['Labels']['com.docker.compose.service']=='postgres'
        volumes=subprocess.check_output(['docker','volume','ls','-q','--filter','label=com.docker.compose.project='+project],text=True).split()
        for volume in volumes:
            obj=json.loads(subprocess.check_output(['docker','volume','inspect',volume],text=True))[0]
            assert obj['Labels']['com.docker.compose.project']==project and obj['Labels']['com.docker.compose.volume']=='probe-pgdata'
        call(['down','--volumes'])
if __name__=='__main__':
    result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(OwnershipTest))
    if not result.wasSuccessful():sys.exit(1)
    print('PASS F01: ownership mismatches rejected before mutation; private paths')
    pg_probe();print('PASS F02: native PG16.10/PostGIS3.5.2 with three logical databases')
    subprocess.run([sys.executable,str(STACK/'scripts/management/test_review_gate.py')],check=True,env={**os.environ,'DI_GATE_TEST_PHASE':'MA-F0'})
    print('PASS F03 negative gate regression; independent model/read/shell proof belongs to phase review')
