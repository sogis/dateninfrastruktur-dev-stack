#!/usr/bin/env python3
"""Read-only smoke of the selected active canonical stack; never seeds or restarts."""
import argparse,json,urllib.request,sys
from compose_operations import resolve

def main():
    p=argparse.ArgumentParser();p.add_argument('--env');p.add_argument('--project');a=p.parse_args();c=resolve(a.env,a.project)
    rows=[json.loads(line) for line in c.command(['ps','--format','json']).stdout.splitlines()]
    expected=set('postgres keycloak garage origin gateway sodata admin jenkins clickhouse superset'.split())
    if len(rows)!=10 or {r['Service'] for r in rows}!=expected or any(r['State']!='running' or r.get('Health')!='healthy' for r in rows):raise RuntimeError('Expected exactly ten healthy services in the selected Compose project')
    query="SELECT datname FROM pg_database WHERE NOT datistemplate AND datname<>'postgres' ORDER BY datname;"
    actual=c.command(['exec','-T','postgres','psql','-X','-q','-At','-U','postgres','-d','postgres','-c',query]).stdout.splitlines()
    if set(actual)!={'keycloak','superset','dateninfrastruktur_management'}:raise RuntimeError('Application database set differs')
    c.command(['--profile','setup','run','--rm','--no-deps','management-setup','verify'])
    for port,path in [(c.values['GATEWAY_PORT'],'/'),(c.values['GATEWAY_PORT'],'/jenkins/login'),(c.values['KEYCLOAK_PORT'],'/realms/dateninfrastruktur/.well-known/openid-configuration'),(c.values['SUPERSET_PORT'],'/health')]:
        with urllib.request.urlopen('http://localhost:'+port+path,timeout=20) as response:
            if response.status!=200:raise RuntimeError('Application readiness request failed')
    print('PASS canonical read-only smoke: ten services, three DBs, unchanged management contract, portal/Keycloak/Jenkins/Superset reachable')
if __name__=='__main__':
    try:main()
    except Exception as error:print(str(error) if isinstance(error,RuntimeError) else 'Read-only smoke failed; selected data unchanged',file=sys.stderr);sys.exit(1)
