#!/usr/bin/env python3
"""Execute targeted current schema checks in an owned PostgreSQL Compose context."""
import argparse
import hashlib
import secrets

from compose_runtime import ROOT, init_context, update_context
from ingestion_test_runtime import cleanup, reserve_ports, sql

ADMIN=ROOT.parent/'dateninfrastruktur-admin'
TEST_PACKAGE='ch.so.agi.dateninfrastruktur.admin.'


def setup_command(c, action='setup', check=True):
    result=c.command(['--profile','setup','run','--rm','--no-deps','--entrypoint','python3','management-setup',
        '/opt/admin/scripts/setup_explicit.py',action],check=False)
    with (c.runtime/'schema-contract.log').open('a') as log:
        log.write(c.redact(result.stdout+result.stderr))
    if check and result.returncode:
        raise RuntimeError(f'Management setup failed; private evidence {c.runtime}/schema-contract.log')
    return result


def java(c, name, check=True):
    args=['--profile','test','run','--rm','--no-deps','--entrypoint','java','test-fixture',
          '-cp','/opt/compose-test/classes:/opt/compose-test/lib/*',TEST_PACKAGE+name]
    return c.command(args,check=check)


def state(c):
    return sql(c,"""
      SELECT di_ops.physical_fingerprint(),
       (SELECT string_agg(revision||':'||xmin::text,',' ORDER BY revision) FROM di_ops.schema_revision),
       (SELECT fingerprint||':'||xmin::text FROM di_ops.contract_fingerprint),
       (SELECT last_value FROM di_management.t_ili2db_seq);
    """)


def fresh(c):
    outcome=setup_command(c)
    assert 'Current empty management schema installed' in outcome.stdout
    assert sql(c,'SELECT revision FROM di_ops.schema_revision')=='management-20261106'
    assert sql(c,"SELECT to_regclass('di_ops.legacy_origin') IS NULL")=='t'
    assert sql(c,"SELECT NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='di_migrator')")=='t'
    assert sql(c,'SELECT count(*) FROM di_management.principal')=='0'
    assert sql(c,'SELECT count(*) FROM audit.row_change')=='0'
    assert 'Current management baseline verified read-only' in setup_command(c,'verify').stdout
    return 7


def setup_repetition(c):
    setup_command(c)
    before=state(c)
    second=setup_command(c)
    assert 'Current management baseline verified read-only' in second.stdout
    assert 'Current empty management schema installed' not in second.stdout and before==state(c)
    assert setup_command(c,'verify').returncode==0
    return 3


def partial(c):
    sql(c,'CREATE FUNCTION public.unrelated() RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$;')
    result=setup_command(c,check=False)
    assert result.returncode and 'nonempty or partial' in result.stderr
    assert sql(c,'SELECT public.unrelated()')=='1'
    assert sql(c,"SELECT to_regnamespace('di_management') IS NULL")=='t'
    assert sql(c,"SELECT NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='di_writer')")=='t'
    return 4


def security(c):
    setup_command(c)
    seeded=java(c,'SubmissionAuthorizationIT').stdout
    assert 'PASS G28 ' in seeded and 'PASS G27/G29 ' in seeded
    marker=sql(c,'SELECT di_ops.contract_fingerprint()')
    assert sql(c,"SELECT NOT has_table_privilege('di_audit_owner','di_management.csvdeliveryconfiguration','SELECT')")=='t'
    assert sql(c,"SELECT count(*) FROM audit.row_change WHERE table_name='csvdeliveryconfiguration'")!='0'
    for mutation,restore in (
        ('ALTER TABLE di_management.dataset ADD COLUMN mapping_counterexample bigint',
         'ALTER TABLE di_management.dataset DROP COLUMN mapping_counterexample'),
        ('ALTER TABLE di_management.dataset DISABLE TRIGGER di_audit_log',
         'ALTER TABLE di_management.dataset ENABLE TRIGGER di_audit_log'),
        ('GRANT SELECT ON audit.row_change TO di_public','REVOKE SELECT ON audit.row_change FROM di_public'),
        ("UPDATE di_management.t_ili2db_attrname SET sqlname='unbound' WHERE sqlname='commandid'",
         "UPDATE di_management.t_ili2db_attrname SET sqlname='commandid' WHERE sqlname='unbound'"),
    ):
        sql(c,mutation)
        try:
            assert sql(c,'SELECT di_ops.contract_fingerprint()')==marker
            assert setup_command(c,'verify',check=False).returncode!=0
            assert java(c,'SchemaRuntimeProbe',check=False).returncode!=0
        finally:
            sql(c,restore)
        assert setup_command(c,'verify').returncode==0
    identity_guard(c)
    return 23


def identity_guard(c):
    row=sql(c,"SELECT t_id FROM di_management.principal WHERE akind='user' ORDER BY t_id LIMIT 1")
    assert row.isdigit()
    actor='00000000-0000-4000-8000-000000000007'
    original=sql(c,f"SELECT aissuer FROM di_management.principal WHERE t_id={row}")
    context=f"""
        SET LOCAL di.actor_issuer='urn:di:migration';
        SET LOCAL di.actor_kind='service';
        SET LOCAL di.actor_subject='{actor}';
        SET LOCAL di.action='operator.migrate_identity';
        SET LOCAL di.command_id='{actor}';
        SET LOCAL di.request_id='{actor}';
        SET LOCAL di.migration_operation='{actor}';
        SET LOCAL di.migration_target_issuer='http://localhost:18080/realms/dateninfrastruktur';
    """
    command=f"""BEGIN;
       CREATE ROLE di_migrator;
       GRANT USAGE ON SCHEMA di_management TO di_migrator;
       GRANT SELECT, UPDATE ON di_management.principal TO di_migrator;
       SET SESSION AUTHORIZATION di_migrator;
       {context}
       UPDATE di_management.principal SET aissuer='http://localhost:18080/realms/dateninfrastruktur' WHERE t_id={row};
       ROLLBACK;
    """
    result=c.command(['exec','-T','postgres','psql','-X','-q','-At','-U','postgres',
                      '-d','dateninfrastruktur_management','-v','ON_ERROR_STOP=1'],command,check=False)
    assert result.returncode and 'principal external identity immutable' in result.stderr
    assert sql(c,f'SELECT aissuer FROM di_management.principal WHERE t_id={row}')==original
    sql(c,f"BEGIN; {context} UPDATE di_management.principal SET displayname='Allowed fixture edit' WHERE t_id={row}; COMMIT;")
    assert sql(c,f'SELECT displayname FROM di_management.principal WHERE t_id={row}')=='Allowed fixture edit'


def packaged_java(c):
    setup_command(c)
    body=(ADMIN/'db/persistence-contract.properties').read_bytes()
    assert sql(c,'SELECT di_ops.contract_fingerprint()')==hashlib.sha256(body).hexdigest()
    before=state(c)
    assert 'Packaged Java verifier accepted' in java(c,'SchemaRuntimeProbe').stdout
    assert before==state(c)
    marker=hashlib.sha256(body).hexdigest()
    predecessor='a7beb105097f00a64b8351cd0a8aa8b75a44eceb735767e0aa457a39e7f1e3f4'
    sql(c,f"UPDATE di_ops.contract_fingerprint SET fingerprint='{predecessor}' WHERE singleton")
    altered=state(c)
    try:
        assert setup_command(c,'verify',check=False).returncode!=0
        assert setup_command(c,'setup',check=False).returncode!=0
        assert java(c,'SchemaRuntimeProbe',check=False).returncode!=0
        assert state(c)==altered and (ADMIN/'db/persistence-contract.properties').read_bytes()==body
    finally:
        sql(c,f"UPDATE di_ops.contract_fingerprint SET fingerprint='{marker}'")
    assert setup_command(c,'verify').returncode==0
    return 8


def retention_boundary(c):
    setup_command(c)
    assert sql(c,"SELECT string_agg(revision, ',') FROM di_ops.schema_revision")=='management-20261106'
    sql(c,"CREATE TABLE di_ops.legacy_origin (key text PRIMARY KEY); INSERT INTO di_ops.legacy_origin VALUES('synthetic');")
    before=state(c)
    assert setup_command(c,'verify',check=False).returncode!=0
    assert setup_command(c,'setup',check=False).returncode!=0
    assert before==state(c) and sql(c,'SELECT count(*) FROM di_ops.legacy_origin')=='1'
    return 4


CASES={'fresh':fresh,'repeat':setup_repetition,'partial':partial,'security':security,
       'package':packaged_java,'retention':retention_boundary}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case',choices=CASES)
    args=parser.parse_args()
    c=init_context('mag-schema-test-'+secrets.token_hex(5),reserve_ports(),True)
    try:
        c.command(['build','postgres','test-tool-build'])
        c=update_context(c,{'TOOL_IMAGE':c.values['TEST_TOOL_IMAGE']})
        c.command(['up','--no-build','-d','--wait','--wait-timeout','120','postgres'])
        c.command(['--profile','setup','run','--rm','--no-deps','postgres-init'])
        count=CASES[args.case](c)
        print(f'Current schema: {args.case} verified')
        print(f'ASSERTIONS={count} SKIP=0')
    finally:
        cleanup(c)


if __name__=='__main__':
    main()
