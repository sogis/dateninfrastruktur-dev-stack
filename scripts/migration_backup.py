"""Private, stopped-source Keycloak data backup plus isolated offline export."""
import hashlib,json,pathlib,shutil,subprocess
from consolidation import inspect,private_write,digest
from migration_db import verify_source

def tree_manifest(root):
    result={}
    for p in sorted(pathlib.Path(root).rglob('*')):
        if p.is_symlink():raise RuntimeError('VERIFICATION_FAILED: unexpected backup symlink')
        if p.is_file():result[str(p.relative_to(root))]=digest(p)
    return result

def backup_keycloak(plan,context):
    ref=plan['sources']['management_keycloak'];cid=verify_source(ref,plan['scope'])
    observed=inspect(cid)['State']
    if observed['Running']:raise RuntimeError('SOURCE_NOT_QUIESCED: cleanly stop the selected Keycloak before backup')
    if observed.get('OOMKilled') or observed.get('Error') or observed.get('ExitCode') not in [0,143]:raise RuntimeError('BACKUP_FAILED: selected Keycloak did not stop cleanly')
    root=context.runtime/'migration';root.mkdir(exist_ok=True);root.chmod(0o700);original=root/'keycloak-original';scratch=root/'keycloak-copy'
    if not original.exists():
        original.mkdir(mode=0o700)
        p=subprocess.run(['docker','cp',cid+':/opt/keycloak/data/.',str(original)],capture_output=True)
        if p.returncode:raise RuntimeError('BACKUP_FAILED: actual Keycloak data directory')
        files=tree_manifest(original)
        if not any(name.endswith('.mv.db') for name in files):raise RuntimeError('BACKUP_FAILED: selected MA source is not the expected H2 source')
        for p in original.rglob('*'):p.chmod(0o700 if p.is_dir() else 0o600)
        private_write(root/'keycloak-original-manifest.json',{'container_id':cid,'image_id':ref['image_id'],'files':files})
    manifest=json.loads((root/'keycloak-original-manifest.json').read_text())
    if manifest['container_id']!=cid or tree_manifest(original)!=manifest['files']:raise RuntimeError('SOURCE_CHANGED: Keycloak backup binding')
    if not scratch.exists():shutil.copytree(original,scratch)
    export=root/'keycloak-export/dateninfrastruktur-realm.json'
    if not export.exists():context.command(['--profile','migration','run','--pull','never','--rm','--no-deps','keycloak-export'])
    if not export.exists():raise RuntimeError('BACKUP_FAILED: offline current realm export missing')
    realms={p.name[:-len('-realm.json')] for p in export.parent.glob('*-realm.json')}
    if not realms.issubset({'master','dateninfrastruktur'}):raise RuntimeError('IDENTITY_CONFLICT: additional MA realms need an explicit mapping')
    if tree_manifest(original)!=manifest['files']:raise RuntimeError('VERIFICATION_FAILED: original H2 backup was modified')
    exports=tree_manifest(export.parent)
    if 'exports' in manifest and manifest['exports']!=exports:raise RuntimeError('SOURCE_CHANGED: exported identity proof')
    if 'exports' not in manifest:
        manifest['exports']=exports;private_write(root/'keycloak-original-manifest.json',manifest)
    for directory in [root/'keycloak-export',scratch]:
        directory.chmod(0o700)
        for p in directory.rglob('*'):p.chmod(0o700 if p.is_dir() else 0o600)
    return export

def verify_keycloak_source(plan,context):
    import tempfile
    ref=plan['sources']['management_keycloak'];cid=verify_source(ref,plan['scope'])
    if inspect(cid)['State']['Running']:raise RuntimeError('SOURCE_CHANGED: selected H2 source was restarted')
    root=context.runtime/'migration';manifest=json.loads((root/'keycloak-original-manifest.json').read_text())
    if tree_manifest(root/'keycloak-original')!=manifest['files'] or tree_manifest(root/'keycloak-export')!=manifest['exports']:raise RuntimeError('SOURCE_CHANGED: archived H2 or exported identity proof')
    with tempfile.TemporaryDirectory(prefix='source-recheck-',dir=root) as td:
        result=subprocess.run(['docker','cp',cid+':/opt/keycloak/data/.',td],capture_output=True)
        if result.returncode or tree_manifest(pathlib.Path(td))!=manifest['files']:raise RuntimeError('SOURCE_CHANGED: original H2 content after backup')
