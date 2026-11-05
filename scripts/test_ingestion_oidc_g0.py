#!/usr/bin/env python3
"""G02 isolated risk probe, never reconfigure the user's Jenkins or Keycloak."""
import json,os,pathlib,secrets,socket,subprocess,time,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
def port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return str(s.getsockname()[1])
def run():
    project='mag-g0-oidc-'+secrets.token_hex(5)
    runtime=ROOT/'.runtime/ingestion-review/probes'/project;runtime.mkdir(parents=True,mode=0o700)
    values={'G0_RUNTIME':str(runtime),'G0_KC_PORT':port(),'G0_JENKINS_PORT':port(),'G0_VERIFIER_PORT':port(),'G0_DB_PASSWORD':secrets.token_hex(32),'G0_CLIENT_SECRET':secrets.token_hex(32),'G0_USER_PASSWORD':secrets.token_hex(24)}
    values.update(G0_ISSUER='http://localhost:'+values['G0_KC_PORT']+'/realms/g0',G0_JENKINS_URL='http://localhost:'+values['G0_JENKINS_PORT']+'/jenkins/')
    realm={'realm':'g0','enabled':True,'sslRequired':'none','users':[{'id':'11111111-1111-4111-8111-111111111111','username':'g0-supplier','enabled':True,'firstName':'Synthetic','lastName':'Supplier','email':'g0@example.invalid','emailVerified':True,'credentials':[{'type':'password','value':values['G0_USER_PASSWORD'],'temporary':False}]}],'clients':[{'clientId':'jenkins-delivery','enabled':True,'publicClient':False,'secret':values['G0_CLIENT_SECRET'],'standardFlowEnabled':True,'directAccessGrantsEnabled':False,'redirectUris':[values['G0_JENKINS_URL']+'securityRealm/finishLogin'],'webOrigins':[values['G0_JENKINS_URL'].rstrip('/')],'attributes':{'pkce.code.challenge.method':'S256'},'protocolMappers':[{'name':'ingestion audience','protocol':'openid-connect','protocolMapper':'oidc-audience-mapper','config':{'included.custom.audience':'ingestion-api','access.token.claim':'true','id.token.claim':'false'}}]}]}
    (runtime/'realm.json').write_text(json.dumps(realm));(runtime/'realm.json').chmod(0o644)
    (runtime/'jenkins.yaml').write_text('''jenkins:
  numExecutors: 0
  securityRealm:
    oic:
      clientId: jenkins-delivery
      clientSecret: '${G0_CLIENT_SECRET}'
      userNameField: sub
      fullNameFieldName: name
      serverConfiguration:
        manual:
          issuer: '${G0_ISSUER}'
          authorizationServerUrl: '${G0_AUTHORIZATION_URL}'
          tokenServerUrl: http://keycloak:8080/realms/g0/protocol/openid-connect/token
          jwksServerUrl: http://keycloak:8080/realms/g0/protocol/openid-connect/certs
          scopes: openid profile email
      properties:
        - pkce
  authorizationStrategy:
    projectMatrix:
      entries:
        - group:
            name: authenticated
            permissions: ['Overall/Read']
unclassified:
  location:
    url: '${JENKINS_URL}'
  gretlDatenportalJobs:
    seedJobAutoCreate: false
''')
    (runtime/'jenkins.yaml').chmod(0o644)
    values['G0_POSTGRES_IMAGE']=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}','dateninfrastruktur-postgres:dateninfrastruktur'],text=True).strip()
    env={**os.environ,**values}
    base=['docker','compose','--project-name',project,'--file',str(ROOT/'tests/ingestion/oidc-probe.compose.yaml')]
    def redact(text):
        for k,v in values.items():
            if 'PASSWORD' in k or 'SECRET' in k:text=text.replace(v,'[REDACTED]')
        return text
    def cmd(args):
        p=subprocess.run(base+args,env=env,capture_output=True,text=True)
        with (runtime/'commands.log').open('a') as f:f.write(redact(p.stdout+p.stderr))
        if p.returncode:raise RuntimeError('G02 command failed: '+args[0]+'; private evidence '+str(runtime))
    assert not subprocess.check_output(['docker','ps','-aq','--filter','label=com.docker.compose.project='+project]).strip()
    try:
        cmd(['up','-d','--wait','--wait-timeout','120','postgres']);cmd(['up','-d','keycloak'])
        def wait(url):
            for attempt in range(150):
                try:
                    with urllib.request.urlopen(url,timeout=3) as r:
                        if r.status==200:return
                except Exception:pass
                time.sleep(1)
            raise RuntimeError('G02 readiness timeout; '+str(runtime))
        wait(values['G0_ISSUER']+'/.well-known/openid-configuration')
        cmd(['up','-d','jenkins']);wait(values['G0_JENKINS_URL']+'login')
        homes=sorted((pathlib.Path.home()/'.sdkman/candidates/java').glob('25*-tem'))
        if homes:env.update(JAVA_HOME=str(homes[-1]),PATH=str(homes[-1]/'bin')+':'+env['PATH'])
        proc=subprocess.run(['./gradlew','--no-daemon','integrationTest','--tests','*IngestionOidcSpikeIT'],cwd=ROOT.parent/'dateninfrastruktur-admin',env=env,capture_output=True,text=True)
        (runtime/'browser.log').write_text(redact(proc.stdout+proc.stderr))
        if proc.returncode:raise RuntimeError('G02 browser/token test failed; '+str(runtime/'browser.log'))
        import xml.etree.ElementTree as ET
        report=ROOT.parent/'dateninfrastruktur-admin/build/test-results/integrationTest/TEST-ch.so.agi.dateninfrastruktur.admin.IngestionOidcSpikeIT.xml'
        result=ET.parse(report).getroot();assert result.get('tests')=='1' and all(result.get(k)=='0' for k in ['failures','errors','skipped'])
        (runtime/'result.json').write_text(json.dumps({'oidc_plugin':'4.731.v4932b_506e767','checks':['pkce_browser_codeflow','current_user_access_token','verified_issuer_subject','wrong_audience_denied','wrong_subject_denied'],'tokens_emitted':False},indent=2))
        print('PASS G02: real isolated Jenkins→Keycloak PKCE→current-user access token→ADMIN decoder; audience and subject negative; '+str(runtime/'result.json'))
    finally:
        cmd(['logs','--no-color']);
        ids=subprocess.check_output(['docker','ps','-aq','--filter','label=com.docker.compose.project='+project],text=True).split()
        for cid in ids:
            info=json.loads(subprocess.check_output(['docker','inspect',cid]))[0]
            assert info['Config']['Labels']['com.docker.compose.project']==project
            assert info['Config']['Labels']['com.docker.compose.project.config_files']==str(ROOT/'tests/ingestion/oidc-probe.compose.yaml')
        cmd(['down','--volumes','--timeout','30'])
if __name__=='__main__':run()
