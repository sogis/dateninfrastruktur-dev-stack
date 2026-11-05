#!/usr/bin/env python3
"""Explicit existing application operators through the single Compose context."""
import argparse,pathlib,secrets,sys
from migration_db import private_bytes
from compose_operations import resolve
from compose_runtime import write_private

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['activate','legacy-import']);p.add_argument('--env');p.add_argument('--project');p.add_argument('--apply',action='store_true');p.add_argument('--select');p.add_argument('--report');p.add_argument('--actor-issuer');p.add_argument('--actor-subject');p.add_argument('values',nargs='*');a=p.parse_args()
    c=resolve(a.env,a.project)
    if a.action=='activate':
        if len(a.values)!=3 or a.apply or a.select or a.report or a.actor_issuer or a.actor_subject:p.error('activate needs dataset UUID, expected version, distribution UUID')
        result=c.command(['--profile','tools','run','--rm','--no-deps','management-operator','activate',*a.values])
    else:
        if len(a.values)!=1:p.error('legacy-import needs exactly one explicitly selected local XTF file')
        if a.apply and (not a.select or not a.actor_issuer or not a.actor_subject):p.error('Apply requires explicit selection and technical actor issuer/subject')
        source=pathlib.Path(a.values[0]).resolve()
        if not source.is_file():p.error('Selected import input does not exist')
        relative=pathlib.Path('imports')/(secrets.token_hex(8)+'-'+source.name);target=c.runtime/relative
        report=pathlib.Path(a.report).resolve() if a.report else c.runtime/'imports'/('report-'+secrets.token_hex(8)+'.json')
        if not report.is_relative_to(c.runtime):p.error('Import report must remain in this Compose runtime')
        private_bytes(target,source.read_bytes())
        args=[str(pathlib.Path('/runtime')/relative),'--apply' if a.apply else '--dry-run','--report='+str(pathlib.Path('/runtime')/report.relative_to(c.runtime))]
        if a.select:args+=['--select='+a.select]
        actor=[]
        for field,value in [('DI_OPERATOR_ISSUER',a.actor_issuer),('DI_OPERATOR_SUBJECT',a.actor_subject)]:
            if value:actor+=['-e',field+'='+value]
        result=c.command(['--profile','tools','run','--rm','--no-deps',*actor,'--entrypoint','java','management-operator','-Dloader.main=ch.so.agi.dateninfrastruktur.admin.legacy.LegacyCatalogImportCommand','-cp','/opt/admin/app.jar','org.springframework.boot.loader.launch.PropertiesLauncher',*args])
    print(c.redact(result.stdout),end='')
if __name__=='__main__':
    try:main()
    except Exception as error:print(str(error) if isinstance(error,RuntimeError) else 'Explicit operator failed; inputs retained privately',file=sys.stderr);sys.exit(1)
