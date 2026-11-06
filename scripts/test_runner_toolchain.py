#!/usr/bin/env python3
"""G03: run the installed real CsvValidator, both valid and invalid input."""
import hashlib,json,os,pathlib,secrets,shutil,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
def run():
    project='mag-g0-csv-'+secrets.token_hex(5)
    runtime=ROOT/'.runtime/ingestion-review/probes'/project;runtime.mkdir(parents=True,mode=0o700)
    probe=runtime/'probe';probe.mkdir();(probe/'models').mkdir()
    shutil.copyfile(ROOT/'tests/ingestion/csv-probe.gradle',probe/'build.gradle')
    (probe/'settings.gradle').write_text("rootProject.name='g0-csv-spike'\n")
    model=ROOT.parent/'dateninfrastruktur-themenrepo/statistikdienst/ch.so.bevoelkerung.altersstruktur/SO_Bevoelkerung_Altersstruktur_20261015.ili'
    shutil.copyfile(model,probe/'models'/model.name)
    image=json.loads(subprocess.check_output(['docker','image','inspect','dateninfrastruktur-jenkins:local']))[0]
    lock=json.loads((ROOT.parent/'dateninfrastruktur-jenkins-dev/toolchain-lock.json').read_text())
    assert image['Id']==lock['jenkins_base_image_id'],'G0 binary baseline changed'
    env={**os.environ,'G0_JENKINS_IMAGE':image['Id'],'G0_PROBE_DIR':str(probe),'G0_TOPICS_DIR':str(ROOT.parent/'dateninfrastruktur-themenrepo')}
    base=['docker','compose','--project-name',project,'--file',str(ROOT/'tests/ingestion/csv-probe.compose.yaml')]
    header='Jahrgang;Auslaender;Auslaenderinnen;Schweizer;Schweizerinnen;Total\n'
    results=[]
    cases={'valid':header+'2000;10;20;30;40;100\n','invalid-type':header+'not-a-year;10;20;30;40;100\n','invalid-required':header+'2000;;20;30;40;100\n'}
    try:
        for name,content in cases.items():
            work=runtime/name;work.mkdir();(work/'input.csv').write_text(content)
            current={**env,'G0_WORK_DIR':str(work)}
            proc=subprocess.run(base+['run','--rm','--no-deps','csv-probe'],env=current,capture_output=True,text=True)
            (work/'command.log').write_text(proc.stdout+proc.stderr)
            ok=proc.returncode==0
            if ok!=(name=='valid'):raise RuntimeError(name+' unexpected result; see '+str(work/'command.log'))
            if ok:assert json.loads((work/'validated.json').read_text())['validationOk'] is True
            else:assert 'validation failed' in proc.stdout+proc.stderr,'Failure must be actual model validation'
            results.append({'case':name,'exit':proc.returncode,'validation_succeeded':ok})
    finally:
        subprocess.run(base+['down'],env={**env,'G0_WORK_DIR':str(runtime)},capture_output=True,check=True)
    result={'image_id':image['Id'],'model':model.name,'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'jars':json.loads((runtime/'valid/validated.json').read_text())['jars'],'model_dependencies':['INTERLIS (compiler builtin)'],'results':results}
    assert result['jars']==lock['gretl_jars_sha256'],'Bundled GRETL dependency bytes changed'
    assert result['model_sha256']==lock['model_sha256'],'Pilot model changed'
    (runtime/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':run()
