"""Bind an operation to its exact target configuration and reviewed executable files."""
import hashlib,pathlib
from compose_runtime import ROOT

def artifact_hashes():
    paths=[ROOT/'compose.yaml',*[ROOT/'scripts'/name for name in ['compose_runtime.py','compose_operations.py','compose_operator.py','consolidation.py']]]
    for pattern in ['scripts/migration*.py','services/apisix/*','services/garage/*','services/postgres/Dockerfile','services/postgres/init/*','services/postgres/compatibility/*','services/migration/*']:
        paths.extend(p for p in ROOT.glob(pattern) if p.is_file())
    admin=ROOT.parent/'dateninfrastruktur-admin'
    paths+=[admin/'Dockerfile',*[admin/'scripts'/name for name in ['management_db.py','database_target.py','audit_setup.py','contract_fingerprint.py','persistence_contract.py','verify_physical_mapping.py']],admin/'scripts/principal_identity_migration.py',admin/'scripts/setup_explicit.py',admin/'scripts/upgrade_contract.py',admin/'db/persistence-contract.properties']
    paths.extend((admin/'db/migrations').glob('*.sql'))
    return {str(p.relative_to(ROOT.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}

def runtime_hashes(context):
    names=['garage.toml','origin.conf','operator.conf','realm-initial.json','apisix.yaml']
    return {name:hashlib.sha256((context.runtime/name).read_bytes()).hexdigest() for name in names}
