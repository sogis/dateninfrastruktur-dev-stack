#!/usr/bin/env bash
set -euo pipefail
stack="$(cd "$(dirname "$0")/../.." && pwd)"
workspace="$(dirname "$stack")"
printf 'Architecture: '; uname -m
java -version 2>&1
for name in dateninfrastruktur-dev-stack dateninfrastruktur-admin dateninfrastruktur-sodata dateninfrastruktur-themenrepo dateninfrastruktur-jenkins-dev dateninfrastruktur-jenkins-gretl-plugin; do
  if [[ -d "$workspace/$name/.git" || -f "$workspace/$name/.git" ]]; then
    printf '\nRepository: %s\n' "$name"
    git -C "$workspace/$name" rev-parse HEAD
    git -C "$workspace/$name" status --short
  else
    printf '\nUnavailable optional repository: %s\n' "$name"
  fi
done
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Ports}}'
docker volume ls --format '{{.Name}}'
python3 - "$stack" <<'PY'
import pathlib,sys
sys.path.insert(0,str(pathlib.Path(sys.argv[1])/'scripts/management'))
from importlib.machinery import SourceFileLoader
m=SourceFileLoader('review_runner',str(pathlib.Path(sys.argv[1])/'scripts/management/review-phase.py')).load_module()
b,v=m.binary(); print('OpenCode executable:',b);print('OpenCode version:',v)
PY
