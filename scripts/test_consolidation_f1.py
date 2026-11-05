#!/usr/bin/env python3
"""F04–F08 against the canonical Compose definition and synthetic private state."""
import hashlib,json,os,pathlib,secrets,socket,subprocess,sys,urllib.request,urllib.error,urllib.parse,zipfile
from compose_runtime import ComposeContext,ROOT,init_context,setup_context,write_private
SERVICES=set('postgres keycloak garage origin gateway sodata admin jenkins clickhouse superset'.split())
def reserve_ports():
    sockets=[]
    try:
        for _ in range(5):
            s=socket.socket();s.bind(('127.0.0.1',0));sockets.append(s)
        return dict(zip(['GATEWAY_PORT','KEYCLOAK_PORT','SUPERSET_PORT','CLICKHOUSE_HTTP_PORT','CLICKHOUSE_NATIVE_PORT'],[s.getsockname()[1] for s in sockets]))
    finally:
        for s in sockets:s.close()
def sql(c,query,db='dateninfrastruktur_management',service='postgres'):
    return c.command(['exec','-T',service,'psql','-X','-q','-At','-U','postgres','-d',db,'-v','ON_ERROR_STOP=1'],query).stdout.strip()
def http(url,token=None,method='GET',headers=None,data=None):
    h=dict(headers or {})
    if token:h['Authorization']='Bearer '+token
    request=urllib.request.Request(url,data=data,method=method,headers=h)
    try:
        with urllib.request.urlopen(request,timeout=20) as r:return r.status,dict(r.headers),r.read()
    except urllib.error.HTTPError as e:return e.code,dict(e.headers),e.read()
def token(c,user):
    body=urllib.parse.urlencode(dict(grant_type='password',client_id='management-test',username=user,password=c.values['KEYCLOAK_DEMO_PASSWORD'])).encode()
    code,_,data=http('http://localhost:'+c.values['KEYCLOAK_PORT']+'/realms/dateninfrastruktur/protocol/openid-connect/token',method='POST',data=body)
    detail=json.loads(data) if code!=200 else {}
    assert code==200,'real Keycloak token issuance failed: '+user+' HTTP '+str(code)+' '+str(detail.get('error'))+' '+str(detail.get('error_description'))
    return json.loads(data)['access_token']
def check_topology(c,empty=False):
    cfg=json.loads(c.command(['config','--format','json']).stdout)
    assert {n for n,s in cfg['services'].items() if not s.get('profiles')}==SERVICES
    ps=[json.loads(l) for l in c.command(['ps','--format','json']).stdout.splitlines()]
    assert {s['Service'] for s in ps}==SERVICES and len(ps)==10
    assert all(s['State']=='running' and s.get('Health')=='healthy' for s in ps)
    for n,s in cfg['services'].items():
        assert not s.get('container_name')
        if not s.get('profiles'):assert not s.get('network_mode')
        if n in ['postgres','garage','origin','admin','sodata','jenkins']:assert not s.get('ports')
        assert not any('.jar' in str(v.get('source','')) for v in s.get('volumes',[]))
    assert set(sql(c,"SELECT datname FROM pg_database WHERE datname NOT IN ('postgres','template0','template1');",'postgres').splitlines())=={'keycloak','superset','dateninfrastruktur_management'}
    assert int(sql(c,"SELECT current_setting('server_version_num');"))>=160010
    assert sql(c,'SELECT postgis_lib_version();')=='3.5.2'
    for db in ['template1','keycloak','superset']:assert sql(c,"SELECT count(*) FROM pg_extension WHERE extname='postgis';",db)=='0'
    for user,pw in [('di_public','DI_PUBLIC_PASSWORD'),('di_authz','DI_AUTHZ_PASSWORD'),('di_writer','DI_WRITER_PASSWORD')]:
        # Use the same DB client environment as the tool image; credentials stay out of argv.
        program="import os,subprocess\ne=os.environ.copy();e.update(PGUSER="+repr(user)+",PGPASSWORD=os.environ["+repr(pw)+"])\np=subprocess.run(['psql','-X','-At','-c','SELECT current_user'],env=e,capture_output=True,text=True);assert p.returncode==0 and p.stdout.strip()=="+repr(user)
        c.command(['--profile','setup','run','--rm','--no-deps','--entrypoint','python3','management-setup','-c',program])
    boundary_program="""import os,subprocess
roles=[('keycloak','keycloak','KEYCLOAK_DB_PASSWORD'),('superset','superset','SUPERSET_DB_PASSWORD'),('di_writer','dateninfrastruktur_management','DI_WRITER_PASSWORD'),('di_authz','dateninfrastruktur_management','DI_AUTHZ_PASSWORD'),('di_public','dateninfrastruktur_management','DI_PUBLIC_PASSWORD'),('di_migrator','dateninfrastruktur_management','DI_MIGRATOR_PASSWORD'),('di_audit_reader','dateninfrastruktur_management','DI_AUDIT_READER_PASSWORD')]
for user,database,key in roles:
 e=os.environ.copy();e.update(PGUSER=user,PGPASSWORD=os.environ[key],PGDATABASE=database)
 p=subprocess.run(['psql','-X','-At','-c','SELECT current_user'],env=e,capture_output=True,text=True)
 assert p.returncode==0 and p.stdout.strip()==user,'own database login'
 foreign='dateninfrastruktur_management' if database!='dateninfrastruktur_management' else 'keycloak'
 e['PGDATABASE']=foreign
 p=subprocess.run(['psql','-X','-At','-c','SELECT current_user'],env=e,capture_output=True,text=True)
 assert p.returncode!=0,'foreign application database must deny login'
print('seven application roles: own database positive, foreign existing database denied')
"""
    c.command(['--profile','setup','run','--rm','--no-deps','--entrypoint','python3','postgres-init','-c',boundary_program])
    assert sql(c,"SELECT count(*) FROM pg_roles WHERE rolname IN ('di_writer','di_authz','di_public','keycloak','superset') AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolbypassrls);")=='0'
    assert sql(c,"SELECT has_table_privilege('di_public','di_management.dataset','INSERT') OR has_table_privilege('di_authz','di_management.dataset','UPDATE') OR has_table_privilege('di_writer','audit.row_change','DELETE');")=='f'
    if empty:
        assert sql(c,'SELECT (SELECT count(*) FROM di_management.dataset)+(SELECT count(*) FROM di_management.accessgrant);')=='0'
        status,_,body=http('http://localhost:'+c.values['GATEWAY_PORT']+'/');assert status==200 and b'MA-E Pilot' not in body
    print('PASS F04/F05/F06: exactly ten canonical services, one native PG16.10, three DBs, role boundaries, empty fresh catalog',flush=True)
def seed(c,database_service='postgres'):
    c.command(['--profile','test','run','--pull','never','--rm','--no-deps','test-fixture'])
    fixture=json.loads((c.runtime/'fixture.json').read_text());payload=c.runtime/'payload';payload.mkdir(exist_ok=True)
    conf=(c.runtime/'origin.conf').read_text().replace(c.values['GARAGE_ORIGIN_ACCESS_KEY'],c.values['GARAGE_DEFAULT_ACCESS_KEY']).replace(c.values['GARAGE_ORIGIN_SECRET_KEY'],c.values['GARAGE_DEFAULT_SECRET_KEY'])
    write_private(c.runtime/'operator.conf',conf)
    for f in fixture['files']:
        path=payload/(f['kind']+'-'+f['filename'])
        if path.suffix=='.csv':path.write_text('kind,version,wert\n'+f['kind']+','+f['filename']+',42\n',encoding='utf-8')
        else:
            with zipfile.ZipFile(path,'w') as z:
                z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
                z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
                z.writestr('xl/workbook.xml','<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Pilot" sheetId="1" r:id="rId1"/></sheets></workbook>')
                z.writestr('xl/_rels/workbook.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
                z.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>'+f['kind']+' '+f['filename']+'</t></is></c><c r="B1"><v>42</v></c></row></sheetData></worksheet>')
        f['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();f['size']=path.stat().st_size
        c.command(['--profile','tools','run','--pull','never','--rm','--no-deps','storage-tool','copyto','/runtime/payload/'+path.name,'managed:di-managed-private/'+f['key'],'--immutable','--retries','1'])
        revision=sql(c,"SELECT row_version FROM di_management.dataset WHERE t_ili_tid='"+f['dataset']+"';",service=database_service)
        c.command(['--profile','tools','run','--pull','never','--rm','--no-deps','management-operator','activate',f['dataset'],revision,f['id']])
        assert sql(c,"SELECT sha256||'|'||bytesize||'|'||availability FROM di_management.distribution WHERE t_ili_tid='"+f['id']+"';",service=database_service)==f['sha256']+'|'+str(f['size'])+'|available'
    write_private(c.runtime/'fixture.json',json.dumps(fixture,indent=2))
def journey(c):
    fixture=json.loads((c.runtime/'fixture.json').read_text());gateway='http://localhost:'+c.values['GATEWAY_PORT'];anna=token(c,'anna');ben=token(c,'ben')
    for f in fixture['files']:
        code,h,body=http(gateway+f['path'])
        assert code==(200 if f['kind']=='open' else 401),(f['kind'],code)
        if code==200:assert hashlib.sha256(body).hexdigest()==f['sha256'] and h.get('Cache-Control')=='no-store'
        if f['kind']=='restricted':assert http(gateway+f['path'],ben)[0]==403
    env=os.environ.copy();env.update(PLAYWRIGHT_SKIP_BROWSER_GC='1',DI_COMPOSE_GATEWAY=gateway,DI_COMPOSE_DEMO_PASSWORD=c.values['KEYCLOAK_DEMO_PASSWORD'],DI_COMPOSE_FIXTURE=str(c.runtime/'fixture.json'))
    if not env.get('JAVA_HOME'):
        homes=sorted((pathlib.Path.home()/'.sdkman/candidates/java').glob('25*-tem'))
        if homes:env['JAVA_HOME']=str(homes[-1]);env['PATH']=str(homes[-1]/'bin')+':'+env['PATH']
    p=subprocess.run(['./gradlew','--no-daemon','integrationTest','--tests','*ComposeJourneyIT'],cwd=ROOT.parent/'dateninfrastruktur-admin',env=env,capture_output=True,text=True)
    write_private(c.runtime/'browser.log',c.redact(p.stdout+p.stderr));assert p.returncode==0,'Browser journey failed; private browser.log'
    import xml.etree.ElementTree as ET
    report=ET.parse(ROOT.parent/'dateninfrastruktur-admin/build/test-results/integrationTest/TEST-ch.so.agi.dateninfrastruktur.admin.ComposeJourneyIT.xml').getroot()
    assert int(report.get('tests','0'))==1 and all(int(report.get(k,'0'))==0 for k in ['failures','errors','skipped'])
    for f in fixture['files']:
        code,_,body=http(gateway+f['path'],anna);assert code==200 and hashlib.sha256(body).hexdigest()==f['sha256']
    assert http(gateway+'/internal/authorization/check',anna)[0]==403
    assert http(gateway+'/ch.so.daten/current.json')[0]==403
    assert http(gateway+'/jenkins/login')[0]==200
    # Inspect redirect without following it; it must point to the existing Jenkins plugin form.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):return None
    try:urllib.request.build_opener(NoRedirect).open(gateway+'/anlieferung',timeout=10);raise AssertionError('redirect expected')
    except urllib.error.HTTPError as e:assert e.code==302 and '/jenkins/' in e.headers['Location']
    adapter="""set -eu
mkdir -p /tmp/maf-adapter
printf '%s\\n' "allprojects { layout.buildDirectory = file('/tmp/maf-adapter/build') }" >/tmp/maf-adapter/init.gradle
export JAVA_HOME=/opt/java/openjdk17
export PATH="$JAVA_HOME/bin:$PATH"
cd /workspace/themenrepo
./gradlew --offline --no-daemon --project-cache-dir /tmp/maf-adapter/cache -I shared/gradle/init.gradle -I /tmp/maf-adapter/init.gradle reloadPortal -x verifyOpendata -Ps3Publish=false -PreloadPortal=true -PcatalogSourceType=database
"""
    result=c.command(['exec','-T','jenkins','bash','-s'],adapter)
    assert 'reloadPortal SKIPPED' in result.stdout and 'reloadPortal=false' in result.stdout
    script="""from superset.app import create_app
app=create_app()
with app.app_context():
 from superset import db
 from superset.models.core import Database
 from sqlalchemy import text
 d=db.session.query(Database).filter_by(database_name='clickhouse_foundation').one()
 with d.get_sqla_engine() as engine:
  with engine.connect() as connection:
   assert connection.execute(text('SELECT count(*) FROM foundation.smoke_metrics')).scalar()==3
 print('existing encrypted Superset connection reads ClickHouse')
"""
    c.command(['exec','-T','superset','python','-'],script)
    print('PASS F07/F08: real OIDC/browser request→approval→private bytes, historical versions, Jenkins/anlieferung and encrypted Superset→ClickHouse',flush=True)
def cleanup(c):
    c.verify_project()
    ids=subprocess.check_output(['docker','volume','ls','-q','--filter','label=com.docker.compose.project='+c.project],text=True).split()
    expected={c.project+'-fixture-pg'}|{c.values[k] for k in ['POSTGRES_VOLUME','GARAGE_META_VOLUME','GARAGE_DATA_VOLUME','JENKINS_VOLUME','CLICKHOUSE_DATA_VOLUME','CLICKHOUSE_LOG_VOLUME','SUPERSET_VOLUME']}
    for name in ids:
        v=json.loads(subprocess.check_output(['docker','volume','inspect',name],text=True))[0]
        assert name in expected and v['Labels']['com.docker.compose.project']==c.project
    expected_objects={name:json.loads(subprocess.check_output(['docker','volume','inspect',name],text=True))[0] for name in ids}
    c.command(['--profile','*','down'])
    for name in ids:
        current=json.loads(subprocess.check_output(['docker','volume','inspect',name],text=True))[0]
        assert current==expected_objects[name] and current['Labels']['com.docker.compose.project']==c.project
        subprocess.run(['docker','volume','rm',name],check=True,capture_output=True)
if __name__=='__main__':
    resume='--resume' in sys.argv
    c=ComposeContext(json.loads((ROOT/'.runtime/maf-f1-current.json').read_text())['env']) if resume else init_context('maf-f1-'+secrets.token_hex(5),reserve_ports(),test_fixture=True)
    write_private(ROOT/'.runtime/maf-f1-current.json',json.dumps({'env':str(c.env_file),'project':c.project}))
    try:
        if not resume:
            c.command(['build','admin','sodata','management-tool-build','test-tool-build','superset']);setup_context(c);c=ComposeContext(c.env_file)
            c.command(['up','-d','--wait','--wait-timeout','300'])
        check_topology(c,empty=not (c.runtime/'fixture.json').exists())
        if not (c.runtime/'fixture.json').exists():seed(c)
        journey(c)
        print('PASS MA-F1 F04–F08',flush=True)
    except Exception as e:
        print(c.redact(str(e)),file=sys.stderr);raise SystemExit(1)
    finally:
        if '--keep-runtime' not in sys.argv:cleanup(c)
