"""Explicit creation of missing databases; existing roles/data are never reset."""
import os,subprocess
def literal(value):return "'"+value.replace("'","''")+"'"
def sql(db,query,user='postgres',password=None):
    env=os.environ.copy();env.update(PGDATABASE=db,PGUSER=user)
    if password is not None:env['PGPASSWORD']=password
    p=subprocess.run(['psql','-X','-q','-At','-v','ON_ERROR_STOP=1'],input=query,capture_output=True,text=True,env=env)
    if p.returncode:raise RuntimeError('PostgreSQL bootstrap or existing credential validation failed; SQL/credentials withheld')
    return p.stdout.strip()
for role in ['keycloak','superset']:
    password=os.environ[role.upper()+'_DB_PASSWORD']
    if sql('postgres','SELECT count(*) FROM pg_roles WHERE rolname='+literal(role)+';')=='0':
        sql('postgres','CREATE ROLE '+role+' LOGIN PASSWORD '+literal(password)+' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;')
    flags=sql('postgres','SELECT rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls FROM pg_roles WHERE rolname='+literal(role)+';')
    if flags!='f':raise RuntimeError('Unexpected privileged application role')
    if sql('postgres','SELECT count(*) FROM pg_database WHERE datname='+literal(role)+';')=='0':
        sql('postgres','CREATE DATABASE '+role+' TEMPLATE template0;')
        sql(role,'REVOKE ALL ON DATABASE '+role+' FROM PUBLIC; GRANT CONNECT,TEMPORARY ON DATABASE '+role+' TO '+role+'; REVOKE ALL ON SCHEMA public FROM PUBLIC; GRANT USAGE,CREATE ON SCHEMA public TO '+role+';')
    sql(role,'SELECT 1;',role,password)
if sql('postgres',"SELECT count(*) FROM pg_database WHERE datname='dateninfrastruktur_management';")=='0':
    sql('postgres','CREATE DATABASE dateninfrastruktur_management TEMPLATE template0; REVOKE ALL ON DATABASE dateninfrastruktur_management FROM PUBLIC;')
print('Three explicit databases ready; existing credentials/data retained')
