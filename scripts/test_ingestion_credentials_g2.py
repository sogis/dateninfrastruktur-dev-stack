#!/usr/bin/env python3
"""Synthetic private-file regression for explicit G2 preparation, no running services."""
import secrets,stat
from compose_runtime import init_context,ComposeContext,write_private
from prepare_ingestion_g2 import prepare,KEYS
from test_consolidation_f1 import reserve_ports,cleanup

def run():
    context=init_context('mag-g2-credentials-'+secrets.token_hex(5),reserve_ports(),True)
    try:
        source=context.env_file.read_text();source=''.join(line for line in source.splitlines(True) if not any(line.startswith(key+'=') for key in KEYS));write_private(context.env_file,source)
        old=ComposeContext(context.env_file);assert prepare(old);first=context.env_file.read_bytes();assert first.startswith(source.encode());new=ComposeContext(context.env_file)
        assert all(new.values[key]==value for key,value in old.values.items())
        assert len({new.values[key] for key in KEYS})==2 and all(len(new.values[key])>=32 for key in KEYS)
        assert stat.S_IMODE(context.env_file.stat().st_mode)==0o600
        assert not prepare(new) and first==context.env_file.read_bytes()
        invalid=first.decode().replace(new.values[KEYS[0]],'short');write_private(context.env_file,invalid)
        try:prepare(ComposeContext(context.env_file));raise AssertionError('Invalid existing credential silently replaced')
        except RuntimeError:pass
        assert context.env_file.read_text()==invalid
        print('PASS G24 explicit private credential preparation: prior bytes/values preserved, distinct secrets, 0600, repeat unchanged, invalid existing value refused')
    finally:cleanup(context)
if __name__=='__main__':run()
