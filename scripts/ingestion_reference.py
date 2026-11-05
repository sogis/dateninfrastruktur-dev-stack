#!/usr/bin/env python3
"""Explicit developer-only stock ili2pg reference; canonical owned Compose resources.
Writes raw generated mapping/metadata/DDL into a private synthetic runtime.
Never used by normal setup, upgrade or application startup.
"""
import json,secrets
from compose_runtime import ROOT,init_context,write_private
from test_consolidation_f1 import reserve_ports

def create():
    c=init_context('mag-g2-reference-'+secrets.token_hex(5),reserve_ports(),True)
    def command(args):
        p=c.command(args,check=False)
        with (c.runtime/'reference.log').open('a') as out:out.write(c.redact(p.stdout+p.stderr))
        if p.returncode:raise RuntimeError('Synthetic reference failed; private '+str(c.runtime/'reference.log'))
        return p.stdout
    write_private(ROOT/'.runtime/g2-reference-current.json',json.dumps({'env':str(c.env_file)}))
    command(['build','postgres','management-tool-build'])
    command(['up','--no-build','-d','--wait','--wait-timeout','120','postgres'])
    command(['--profile','setup','run','--rm','--no-deps','postgres-init'])
    write_private(c.runtime/'reference-import.py',PROGRAM)
    print(command(['--profile','setup','run','--rm','--no-deps','-e','COMPOSE_PROJECT_NAME','--entrypoint','python3','management-setup','/runtime/reference-import.py']).strip())
    print('Owned reference retained for explicit cdbimport/cgen: '+str(c.env_file))

PROGRAM=r'''import sys,json,pathlib,subprocess,tempfile,os
sys.path.insert(0,'/opt/admin/scripts')
from management_db import R,D,sql
if not os.environ['COMPOSE_PROJECT_NAME'].startswith('mag-g2-reference-'):raise RuntimeError('Synthetic developer reference required')
jar=next((R/'.runtime/tools/ili2pg').glob('ili2pg-*.jar'))
args=['-jar',str(jar),'--schemaimport','--dbhost',os.environ['PGHOST'],'--dbport',os.environ['PGPORT'],'--dbdatabase',os.environ['PGDATABASE'],'--dbusr',os.environ['PGUSER'],'--dbpwd',os.environ['PGPASSWORD'],'--dbschema','di_management','--models','SO_AGI_DataInfrastructure_Catalog_20261105;SO_AGI_DataInfrastructure_Access_20261105','--modeldir',str(R/'models'),*json.loads((R/'db/mapping-profile.json').read_text())['options']]
with tempfile.NamedTemporaryFile(mode='w',dir=D,suffix='.args',delete=False) as f:
 f.write('\n'.join(json.dumps(a) for a in args));argfile=pathlib.Path(f.name)
try:
 result=subprocess.run(['java','@'+str(argfile)],capture_output=True,text=True)
 if result.returncode:raise RuntimeError('Stock ili2pg reference import failed; credentials withheld')
finally:argfile.unlink()
def rows(q):return [json.loads(x) for x in sql('SELECT row_to_json(x) FROM ('+q+')x;').splitlines()]
mapping={'classes':rows('SELECT * FROM di_management.t_ili2db_classname ORDER BY iliname'),'attributes':rows('SELECT * FROM di_management.t_ili2db_attrname ORDER BY iliname'),'columns':rows("SELECT table_name,column_name,data_type,is_nullable,column_default FROM information_schema.columns WHERE table_schema='di_management' ORDER BY table_name,ordinal_position"),'meta':rows('SELECT * FROM di_management.t_ili2db_meta_attrs ORDER BY ilielement,attr_name')}
root=pathlib.Path('/runtime')
(root/'reference-mapping.json').write_text(json.dumps(mapping,indent=2)+'\n')
meta={}
for table in ['t_ili2db_model','t_ili2db_classname','t_ili2db_attrname','t_ili2db_meta_attrs','t_ili2db_trafo','t_ili2db_column_prop','t_ili2db_table_prop','t_ili2db_inheritance']:
 records=rows('SELECT * FROM di_management.'+table)
 for record in records:
  if table=='t_ili2db_model':record.pop('importdate',None)
 meta[table]=sorted(records,key=lambda x:json.dumps(x,sort_keys=True))
(root/'reference-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
constraints=rows("SELECT c.relname AS table_name,con.conname,pg_get_constraintdef(con.oid) AS definition FROM pg_constraint con JOIN pg_class c ON c.oid=con.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='di_management' ORDER BY c.relname,con.conname")
(root/'reference-constraints.json').write_text(json.dumps(constraints,indent=2)+'\n')

details=rows("SELECT c.relname AS table_name,a.attname AS column_name,pg_catalog.format_type(a.atttypid,a.atttypmod) AS sql_type,a.attnotnull AS not_null,pg_get_expr(d.adbin,d.adrelid) AS default_expression FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum WHERE n.nspname='di_management' AND c.relkind='r' AND a.attnum>0 AND NOT a.attisdropped ORDER BY c.relname,a.attnum")
(root/'reference-column-details.json').write_text(json.dumps(details,indent=2)+'\n')
indexes=rows("SELECT tablename AS table_name,indexname,indexdef FROM pg_indexes WHERE schemaname='di_management' ORDER BY tablename,indexname")
(root/'reference-indexes.json').write_text(json.dumps(indexes,indent=2)+'\n')

print('Stock ili2pg reference: '+str(len(mapping['classes']))+' classes/associations, '+str(len(mapping['columns']))+' physical columns; deterministic metadata and actual constraints captured')
'''
if __name__=='__main__':create()
