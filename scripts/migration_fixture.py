"""Build a real accepted predecessor tool from tracked Git sources, never host JARs."""
import hashlib,io,json,pathlib,subprocess,tarfile
from compose_runtime import ROOT,update_context

def legacy_tool(context):
    lock=json.loads((ROOT/'tests/consolidation/source-fixture.lock.json').read_text());root=context.runtime/'accepted-source';root.mkdir(exist_ok=True);root.chmod(0o700)
    for name,repo,key in [('admin',ROOT.parent/'dateninfrastruktur-admin','admin_commit'),('stack',ROOT,'stack_commit')]:
        archive=subprocess.check_output(['git','-C',str(repo),'archive','--format=tar',lock[key]])
        destination=root/name;destination.mkdir(exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            for member in tar.getmembers():
                path=destination/member.name
                if not path.resolve().is_relative_to(destination.resolve()) or member.issym() or member.islnk():raise RuntimeError('Unsafe predecessor source archive')
                if member.isdir():path.mkdir(parents=True,exist_ok=True)
                elif member.isfile():
                    path.parent.mkdir(parents=True,exist_ok=True);data=tar.extractfile(member).read()
                    if path.exists() and path.read_bytes()!=data:raise RuntimeError('SOURCE_CHANGED: accepted fixture source')
                    path.write_bytes(data);path.chmod(member.mode&0o755)
    expected=json.loads((ROOT.parent/'dateninfrastruktur-admin/db/upgrade-MA-D-to-MA-F.json').read_text())['fromFingerprint']
    if hashlib.sha256((root/'admin/db/persistence-contract.properties').read_bytes()).hexdigest()!=expected:raise RuntimeError('Predecessor fixture fingerprint is not the accepted migration base')
    image='dateninfrastruktur-maf-source-tools:'+context.project
    context=update_context(context,{'MIGRATION_LEGACY_ADMIN_SOURCE':str(root/'admin'),'MIGRATION_LEGACY_STACK_SOURCE':str(root/'stack'),'LEGACY_TOOL_IMAGE':image})
    context.command(['build','legacy-tool-build']);return context,image
