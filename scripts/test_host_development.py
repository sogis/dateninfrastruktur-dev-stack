#!/usr/bin/env python3
"""Verify the host and optional GRETL Compose models without starting containers."""
import json
import shutil
import subprocess
from uuid import uuid4

from compose_runtime import ROOT, admin_host_config, docker_env, init_context


def model(context, *overlays, env=None):
    command = context.base.copy()
    for overlay in overlays:
        command.extend(['--file', str(ROOT / overlay)])
    result = subprocess.run([*command, 'config', '--format', 'json'], env=env or docker_env(),
                            cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('Compose rejected the development model')
    return json.loads(result.stdout)


def main():
    if not __debug__:
        raise RuntimeError('Assertions must be enabled')
    context = init_context('mag-host-config-' + uuid4().hex[:12], host_admin=True)
    try:
        normal = model(context)
        host = model(context, 'compose.host-admin.yaml')
        services = host['services']
        assert normal['name'] == host['name'] == context.project
        assert normal['volumes'] == host['volumes']
        assert set(normal['services']) - set(services) == {'admin'}
        assert len(services) == 9
        assert all('build' not in service for service in services.values())
        for peer in ('gateway', 'jenkins'):
            previous = normal['services'][peer]['depends_on']
            assert set(previous) - set(services[peer]['depends_on']) == {'admin'}
            assert services[peer]['extra_hosts'] == ['admin=host-gateway']
        for service, port, target in [('postgres', '15432', 5432), ('origin', '18090', 8080)]:
            binding, = services[service]['ports']
            assert (binding['host_ip'], binding['published'], binding['target']) == ('127.0.0.1', port, target)
        config = admin_host_config(context)
        assert config.stat().st_mode & 0o777 == 0o600
        assert 'di.delivery.origin.url=http://127.0.0.1:18090/downloads/\n' in config.read_text()
        realm = json.loads((context.runtime / 'realm-initial.json').read_text())
        assert [user['username'] for user in realm['users']] == ['anna']
        assert not any(client['directAccessGrantsEnabled'] for client in realm['clients'])
        job_dir = context.runtime / 'job'
        job_dir.mkdir()
        gretl = model(context, 'compose.host-admin.yaml', 'compose.gretl-dev.yaml',
                      env=dict(docker_env(), GRETL_JOB_DIR=str(job_dir)))
        jenkins = gretl['services'].pop('jenkins')
        plain = services.pop('jenkins')
        mounts = jenkins.pop('volumes')
        assert jenkins == {key: value for key, value in plain.items() if key != 'volumes'}
        assert gretl == host
        job_mount, = [m for m in mounts if m['target'] == '/opt/dateninfrastruktur/csv-delivery']
        assert (job_mount['type'], job_mount['source'], job_mount['read_only']) == ('bind', str(job_dir), True)
        assert not job_mount.get('bind', {}).get('create_host_path', False)
        assert [mount for mount in mounts if mount != job_mount] == plain['volumes']
    finally:
        shutil.rmtree(context.runtime)
    print('ASSERTIONS=20 SKIP=0')


if __name__ == '__main__':
    main()
