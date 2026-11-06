#!/usr/bin/env python3
"""Explicit once-only local G2 credential preparation. No DB/data/grant/start action."""
import argparse,fcntl,os,pathlib,secrets,tempfile
from compose_operations import resolve
from compose_runtime import ComposeContext,encode_env

KEYS=('DI_INGESTION_PLUGIN_SECRET','DI_INGESTION_LEASE_SECRET')
def prepare(context,keys=KEYS):
    context.verify_project()
    lock=context.runtime/'ingestion-credentials.lock'
    fd=os.open(lock,os.O_RDWR|os.O_CREAT,0o600)
    with os.fdopen(fd,'r+') as owner:
        fcntl.flock(owner,fcntl.LOCK_EX)
        before=context.env_file.read_bytes();current=ComposeContext(context.env_file);extra=[]
        for key in keys:
            if key in current.values:
                if len(current.values[key])<32:raise RuntimeError('Existing ingestion credential is invalid; no automatic replacement')
            else:extra.append(key+'='+encode_env(secrets.token_hex(32))+'\n')
        if not extra:return False
        if context.env_file.read_bytes()!=before:raise RuntimeError('Private environment changed concurrently; no write')
        suffix=('' if not before or before.endswith(b'\n') else '\n')+''.join(extra)
        raw,path=tempfile.mkstemp(prefix='.ingestion-env-',dir=context.runtime)
        try:
            with os.fdopen(raw,'wb') as out:out.write(before+suffix.encode());out.flush();os.fsync(out.fileno())
            os.chmod(path,0o600)
            if context.env_file.read_bytes()!=before:raise RuntimeError('Private environment changed concurrently; no write')
            os.replace(path,context.env_file)
            directory=os.open(context.runtime,os.O_RDONLY)
            try:os.fsync(directory)
            finally:os.close(directory)
        finally:pathlib.Path(path).unlink(missing_ok=True)
        return True
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--env');parser.add_argument('--project');args=parser.parse_args()
    changed=prepare(resolve(args.env,args.project));print('Explicit ingestion credentials prepared privately; existing values preserved' if changed else 'Existing ingestion credentials retained byte-for-byte')
