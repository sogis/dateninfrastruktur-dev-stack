#!/usr/bin/env python3
"""Import a bootstrap XTF or export the selected management database."""
import argparse
import base64
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlencode
from urllib.request import urlopen
from uuid import UUID
from xml.etree import ElementTree

from compose_runtime import SETUP_RUN, ComposeContext, write_private


def development_transfer(context, source):
    if context.values.get('DI_LOCAL_DEVELOPMENT') != 'true':
        raise RuntimeError('Create an explicit host development instance before importing the demo')
    realm = json.loads((context.runtime / 'realm-initial.json').read_text())
    anna, = (user for user in realm['users'] if user['username'] == 'anna')
    issuer = 'http://localhost:' + context.values['KEYCLOAK_PORT'] + '/realms/dateninfrastruktur'
    request = urlencode({
        'grant_type': 'client_credentials',
        'client_id': 'gretl-delivery',
        'client_secret': context.values['DI_GRETL_DELIVERY_CLIENT_SECRET'],
    }).encode()
    with urlopen(issuer + '/protocol/openid-connect/token', data=request, timeout=15) as response:
        segment = json.load(response)['access_token'].split('.')[1]
    claims = json.loads(base64.urlsafe_b64decode(segment + '=' * (-len(segment) % 4)))
    if claims['iss'] != issuer or 'management-api' not in claims['aud']:
        raise RuntimeError('Keycloak returned an unexpected GRETL identity')
    subjects = {'anna': str(UUID(anna['id'])), 'gretl': str(UUID(claims['sub']))}
    access = '{http://www.interlis.ch/xtf/2.4/SO_AGI_DataInfrastructure_Access_20261112}'
    root = ElementTree.parse(source).getroot()
    for principal in root.iter(access + 'Principal'):
        subject = principal.find(access + 'subject')
        if subject.text in subjects:
            principal.find(access + 'issuer').text = issuer
            subject.text = subjects.pop(subject.text)
    if subjects:
        raise RuntimeError('Demo XTF is missing the Anna or GRETL principal')
    target = context.runtime / 'development-bootstrap.xtf'
    write_private(target, ElementTree.tostring(root, encoding='unicode'))
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('import', 'export', 'bootstrap-dev'))
    parser.add_argument('file', type=Path)
    parser.add_argument('--env', required=True)
    args = parser.parse_args()
    context = ComposeContext(args.env)
    path = args.file.absolute()
    if path != path.resolve() or not path.is_relative_to(context.runtime):
        raise RuntimeError('Place the XTF file in the selected private runtime')
    if args.action != 'export' and (not path.is_file() or path.stat().st_mode & 0o077):
        raise RuntimeError('Import requires a private regular XTF file')
    action = args.action
    if action == 'bootstrap-dev':
        path = development_transfer(context, path)
        action = 'import'
    inside = '/runtime/' + path.relative_to(context.runtime).as_posix()
    result = context.command([*SETUP_RUN,
                              '--user', f'{os.getuid()}:{os.getgid()}',
                              '-e', 'DI_TOOL_RUNTIME=/tmp/di-management-transfer',
                              'management-setup', action, inside])
    print(context.redact(result.stdout), end='')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, ElementTree.ParseError):
        sys.exit('Invalid or inaccessible private Compose configuration')
    except RuntimeError as error:
        print(error, file=sys.stderr)
        sys.exit(1)
