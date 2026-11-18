"""Admin development must preserve Compose ownership and restore the running image."""
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import admin_development as dev
import compose_runtime as runtime


class AdminDevelopmentTest(unittest.TestCase):
    def test_overlay_ownership_is_limited_to_admin_in_the_selected_instance(self):
        with tempfile.TemporaryDirectory() as directory:
            context = runtime.ComposeContext.__new__(runtime.ComposeContext)
            context.project = 'mag-dev-fixture'
            context.runtime = Path(directory)
            context.values = {'INSTANCE_ID': 'fixture'}
            labels = {
                'di.instance': 'fixture',
                'com.docker.compose.project': context.project,
                'com.docker.compose.project.working_dir': str(runtime.ROOT),
                'com.docker.compose.project.config_files':
                    f'{runtime.ROOT / "compose.yaml"},{runtime.ADMIN_DEV_OVERLAY}',
                'com.docker.compose.service': 'admin',
            }

            def docker(argv, *args):
                if argv == 'ps':
                    return 'fixture-container\n'
                return json.dumps([{'Config': {'Labels': labels}}])

            with patch.object(runtime, 'docker_output', side_effect=docker):
                with self.assertRaisesRegex(RuntimeError, 'OWNERSHIP_MISMATCH'):
                    context.verify_project()
                (context.runtime / runtime.ADMIN_DEV_MARKER).touch()
                self.assertEqual(len(context.verify_project()), 1)
                for label, other in [('com.docker.compose.service', 'postgres'), ('di.instance', 'foreign')]:
                    original = labels[label]
                    labels[label] = other
                    with self.assertRaisesRegex(RuntimeError, 'OWNERSHIP_MISMATCH'):
                        context.verify_project()
                    labels[label] = original

    def test_failed_switch_restores_previous_image_and_removes_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            image = 'sha256:' + 'a' * 64
            context = SimpleNamespace(runtime=Path(directory), values={'INSTANCE_ID': 'fixture'},
                                      redact=lambda value: value.replace('synthetic-token', '[REDACTED]'))
            context.verify_resources = Mock(return_value=[{
                'Image': image,
                'Config': {'Image': 'fixture:old', 'Labels': {
                    'com.docker.compose.service': 'admin',
                    'com.docker.compose.project.config_files': str(runtime.ROOT / 'compose.yaml'),
                }},
                'State': {'Running': True, 'Health': {'Status': 'healthy'}},
            }])
            context.command = Mock(side_effect=[
                None, RuntimeError('unhealthy'), SimpleNamespace(stdout='synthetic-token', stderr=''), None,
            ])
            source = context.runtime / 'dateninfrastruktur-admin/scripts'
            source.mkdir(parents=True)
            (source / 'dev_reload.py').touch()
            with patch.object(dev, 'ROOT', context.runtime / 'stack'):
                with self.assertRaisesRegex(RuntimeError, 'Previous Admin restored') as failure:
                    dev.switch_admin(context, 'on')
            self.assertIn('[REDACTED]', str(failure.exception))
            self.assertNotIn('synthetic-token', str(failure.exception))
            self.assertFalse((context.runtime / runtime.ADMIN_DEV_MARKER).exists())
            _, first, logs, rollback = context.command.call_args_list
            self.assertEqual(logs.args[0], ['logs', '--tail', '40', 'admin'])
            self.assertTrue(first.kwargs['admin_dev'])
            self.assertFalse(rollback.kwargs['admin_dev'])
            self.assertEqual(rollback.kwargs['overrides'], {'ADMIN_IMAGE': image})
            self.assertTrue(all(call.args[0][-1] == 'admin' and '--no-deps' in call.args[0]
                                for call in (first, rollback)))

    def test_missing_setup_stops_before_compose_changes(self):
        context = Mock()
        context.verify_resources.side_effect = RuntimeError('Explicit setup required')
        with tempfile.TemporaryDirectory() as directory:
            context.runtime = Path(directory)
            with patch('sys.argv', ['admin_development.py', 'on', '--env', 'fixture.env']), \
                    patch.object(dev, 'ComposeContext', return_value=context):
                with self.assertRaisesRegex(RuntimeError, 'Explicit setup'):
                    dev.main()
        context.command.assert_not_called()
        context.verify_resources.assert_called_once_with(require_setup=True)

    def test_regular_admin_development_uses_the_host_user(self):
        context = runtime.ComposeContext.__new__(runtime.ComposeContext)
        context.values = {'DI_TEST_FIXTURE': 'false'}
        context.base = ['docker', 'compose', '--file', str(runtime.ROOT / 'compose.yaml')]
        context.command_overrides = {}
        with patch.object(runtime.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as run:
            context.command(['config', '--quiet'], admin_dev=True)
        env = run.call_args.kwargs['env']
        self.assertEqual(env['DI_TEST_HOST_UID'], str(os.getuid()))
        self.assertEqual(env['DI_TEST_HOST_GID'], str(os.getgid()))

    def test_off_clears_the_bound_marker_after_the_project_was_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            context = SimpleNamespace(runtime=Path(directory), values={'INSTANCE_ID': 'fixture'},
                                      verify_resources=Mock(return_value=[]), command=Mock())
            marker = context.runtime / runtime.ADMIN_DEV_MARKER
            marker.write_text(json.dumps({'instance': 'other', 'image': 'sha256:' + 'a' * 64}))
            with self.assertRaisesRegex(RuntimeError, 'OWNERSHIP_MISMATCH'):
                dev.switch_admin(context, 'off')
            self.assertTrue(marker.exists())
            marker.write_text(json.dumps({'instance': 'fixture', 'image': 'sha256:' + 'a' * 64}))
            dev.switch_admin(context, 'off')
            self.assertFalse(marker.exists())
            context.command.assert_not_called()


if __name__ == '__main__':
    unittest.main()
