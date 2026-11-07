"""Admin development must preserve Compose ownership and restore the running image."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import admin_development as dev
import compose_operations as ops
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
                'com.docker.compose.project.working_dir': str(runtime.ROOT),
                'com.docker.compose.project.config_files':
                    f'{runtime.ROOT / "compose.yaml"},{runtime.ADMIN_DEV_OVERLAY}',
                'com.docker.compose.service': 'admin',
            }

            def docker(argv, **kwargs):
                if argv[1] == 'ps':
                    return 'fixture-container\n'
                return json.dumps([{'Config': {'Labels': labels}}])

            with patch.object(runtime.subprocess, 'check_output', side_effect=docker):
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
            context = SimpleNamespace(runtime=Path(directory), values={'INSTANCE_ID': 'fixture'}, redact=lambda value: value)
            context.verify_project = Mock(return_value=[{
                'Image': image,
                'Config': {'Image': 'fixture:old', 'Labels': {
                    'com.docker.compose.service': 'admin',
                    'com.docker.compose.project.config_files': str(runtime.ROOT / 'compose.yaml'),
                }},
                'State': {'Running': True, 'Health': {'Status': 'healthy'}},
            }])
            context.command = Mock(side_effect=[RuntimeError('unhealthy'), SimpleNamespace(stdout='fixture failure'), None])
            with patch.object(dev, 'development_overrides', return_value={'DI_ADMIN_DEV_IMAGE': 'fixture:dev'}), \
                    patch.object(dev, 'image_available', return_value=True), \
                    patch.object(dev.subprocess, 'run', return_value=SimpleNamespace(returncode=1)):
                with self.assertRaisesRegex(RuntimeError, 'Previous Admin restored'):
                    dev.switch_admin(context, 'on')
            self.assertFalse((context.runtime / runtime.ADMIN_DEV_MARKER).exists())
            first, logs, rollback = context.command.call_args_list
            self.assertEqual(logs.args[0], ['logs', '--tail', '40', 'admin'])
            self.assertTrue(first.kwargs['admin_dev'])
            self.assertFalse(rollback.kwargs['admin_dev'])
            self.assertEqual(rollback.kwargs['overrides'], {'ADMIN_IMAGE': image})
            self.assertTrue(all(call.args[0][-1] == 'admin' and '--no-deps' in call.args[0]
                                for call in (first, rollback)))

    def test_invalid_service_and_missing_setup_stop_before_compose_changes(self):
        with patch('sys.argv', ['dev.sh', 'dev', 'sodata', 'on']), patch.object(ops, 'resolve') as resolve:
            with self.assertRaises(SystemExit) as result:
                ops.main()
            self.assertEqual(result.exception.code, 2)
            resolve.assert_not_called()
        with tempfile.TemporaryDirectory() as directory:
            context = SimpleNamespace(runtime=Path(directory), values={'DI_STORAGE_BUCKET': 'ch.so.daten'},
                                      command=Mock(), verify_project=Mock())
            with self.assertRaisesRegex(RuntimeError, 'Explicit setup'):
                ops.operate(context, SimpleNamespace(action='dev', services=['admin', 'on']))
            context.command.assert_not_called()
            context.verify_project.assert_not_called()


if __name__ == '__main__':
    unittest.main()
