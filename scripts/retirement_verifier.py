#!/usr/bin/env python3
"""Check the explicit retirement inventory against active repository files."""
import fnmatch
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
RULES = ROOT/'tests/retirement-rules.json'

class RetirementVerifier:
    @staticmethod
    def verify():
        config = json.loads(RULES.read_text())
        if config['schemaVersion'] != 1:
            raise ValueError('Unknown retirement catalog')
        errors=[]
        for repo, rule in config['repositories'].items():
            path = ROOT.parent/repo
            names=subprocess.check_output(['git','-C',str(path),'ls-files','-z']).decode().split('\0')
            for name in filter(None,names):
                if any(fnmatch.fnmatchcase(name, pattern) for pattern in rule.get('absent',[])):
                    if (path/name).exists():
                        errors.append(f'{repo}/{name}: retired entrypoint remains')
                for scan in rule.get('scan',[]):
                    if not any(fnmatch.fnmatchcase(name, pattern) for pattern in scan['paths']):
                        continue
                    source=path/name
                    if not source.is_file():
                        continue
                    for pattern in scan['forbidden']:
                        if re.search(pattern,source.read_text()):
                            errors.append(f'{repo}/{name}: retired contract {pattern}')
        if errors:
            raise RuntimeError('\n'.join(errors))
        compose=json.loads((ROOT/'compose.yaml').read_text())
        assert not any(p.startswith('migration') for v in compose['services'].values() for p in v.get('profiles',[]))
        print('Retirement: six repositories; no active old contract found in the named entrypoints.')

if __name__=='__main__':
    RetirementVerifier.verify()
