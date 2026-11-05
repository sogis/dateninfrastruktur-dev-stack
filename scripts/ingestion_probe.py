"""Explicit read-only storage probe, shared by isolated regression drivers."""
import os,pathlib,subprocess
from compose_runtime import ROOT,write_private

def probe(c,mode):
    env=dict(os.environ);env.update(DI_STORAGE_PROBE_MODE=mode,PLAYWRIGHT_SKIP_BROWSER_GC='1',DI_COMPOSE_GATEWAY='http://localhost:'+c.values['GATEWAY_PORT'],DI_COMPOSE_ISSUER='http://localhost:'+c.values['KEYCLOAK_PORT']+'/realms/dateninfrastruktur',DI_COMPOSE_DEMO_PASSWORD=c.values['KEYCLOAK_DEMO_PASSWORD'],DI_COMPOSE_OIDC_SECRET=c.values['DI_OIDC_CLIENT_SECRET'],DI_COMPOSE_FIXTURE=str(c.runtime/'g1-probe-fixture.json'))
    homes=sorted((pathlib.Path.home()/'.sdkman/candidates/java').glob('25*-tem'))
    if not env.get('JAVA_HOME') and homes:env['JAVA_HOME']=str(homes[-1]);env['PATH']=str(homes[-1]/'bin')+':'+env['PATH']
    p=subprocess.run(['./gradlew','--no-daemon','integrationTest','--tests','*StorageCutoverProbeIT'],cwd=ROOT.parent/'dateninfrastruktur-admin',env=env,capture_output=True,text=True)
    write_private(c.runtime/'ma-g1-cutover'/('probe-'+mode+'.log'),c.redact(p.stdout+p.stderr))
    if p.returncode:raise RuntimeError('Existing same-token download probe failed; source retained; private probe log')

