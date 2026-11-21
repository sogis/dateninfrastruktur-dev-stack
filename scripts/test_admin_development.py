"""Admin development must restore the running image."""
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import admin_development as dev
import compose_runtime as runtime


class AdminDevelopmentTest(unittest.TestCase):
    def test_on_saves_healthy_regular_image(self):
        with tempfile.TemporaryDirectory() as directory:
            image = 'sha256:' + 'a' * 64
            context = SimpleNamespace(runtime=Path(directory), project='fixture')
            context.command = Mock(return_value=SimpleNamespace(stdout='fixture-container'))
            source = context.runtime / 'dateninfrastruktur-admin/scripts'
            source.mkdir(parents=True)
            (source / 'dev_reload.py').touch()
            current = SimpleNamespace(returncode=0, stdout=f'{image} true healthy compose.yaml')
            with patch.object(dev, 'ROOT', context.runtime / 'stack'), \
                    patch.object(dev.subprocess, 'run', return_value=current):
                dev.switch_admin(context, 'on')
            self.assertEqual((context.runtime / runtime.ADMIN_DEV_IMAGE_FILE).read_text().strip(), image)
            _, build, replace = context.command.call_args_list
            self.assertEqual(build.args[0], ['build', 'admin'])
            self.assertIn('--wait', replace.args[0])
            self.assertTrue(replace.kwargs['admin_dev'])

    def test_off_restores_regular_image_without_health_status(self):
        for running, flag in (('true', '--wait'), ('false', '--no-start')):
            with self.subTest(running=running), tempfile.TemporaryDirectory() as directory:
                context = SimpleNamespace(runtime=Path(directory))
                context.command = Mock(return_value=SimpleNamespace(stdout='fixture-container'))
                image = 'sha256:' + 'a' * 64
                marker = context.runtime / runtime.ADMIN_DEV_IMAGE_FILE
                marker.write_text(image)
                development = 'sha256:' + 'b' * 64
                current = SimpleNamespace(returncode=0, stdout=f'{development} {running} - compose.yaml')
                with patch.object(dev.subprocess, 'run', return_value=current):
                    dev.switch_admin(context, 'off')
                _, replace = context.command.call_args_list
                self.assertIn(flag, replace.args[0])
                self.assertFalse(replace.kwargs['admin_dev'])
                self.assertEqual(replace.kwargs['overrides'], {'ADMIN_IMAGE': image})
                self.assertFalse(marker.exists())

    def test_off_keeps_saved_image_if_rollback_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            context = SimpleNamespace(runtime=Path(directory), redact=lambda value: value)
            context.command = Mock(side_effect=[
                SimpleNamespace(stdout='fixture-container'), RuntimeError('replacement failed'),
                SimpleNamespace(stdout='', stderr=''), RuntimeError('rollback failed'),
            ])
            image = 'sha256:' + 'a' * 64
            marker = context.runtime / runtime.ADMIN_DEV_IMAGE_FILE
            marker.write_text(image)
            development = 'sha256:' + 'b' * 64
            current = SimpleNamespace(
                returncode=0, stdout=f'{development} false - compose.yaml,{runtime.ADMIN_DEV_OVERLAY}',
            )
            with patch.object(dev.subprocess, 'run', return_value=current), \
                    self.assertRaisesRegex(RuntimeError, 'Restoring the previous Admin failed'):
                dev.switch_admin(context, 'off')
            _, replace, _, rollback = context.command.call_args_list
            self.assertEqual(replace.kwargs['overrides'], {'ADMIN_IMAGE': image})
            self.assertTrue(rollback.kwargs['admin_dev'])
            self.assertEqual(rollback.kwargs['overrides']['DI_ADMIN_DEV_IMAGE'], development)
            self.assertEqual(marker.read_text(), image)

    def test_failed_switch_restores_previous_image_and_removes_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            image = 'sha256:' + 'a' * 64
            context = SimpleNamespace(runtime=Path(directory), project='fixture',
                                      redact=lambda value: value.replace('synthetic-token', '[REDACTED]'))
            context.command = Mock(side_effect=[
                SimpleNamespace(stdout='fixture-container'), None, RuntimeError('unhealthy'),
                SimpleNamespace(stdout='synthetic-token', stderr=''), None,
            ])
            source = context.runtime / 'dateninfrastruktur-admin/scripts'
            source.mkdir(parents=True)
            (source / 'dev_reload.py').touch()
            current = SimpleNamespace(returncode=0, stdout=f'{image} true healthy compose.yaml')
            with patch.object(dev, 'ROOT', context.runtime / 'stack'), \
                    patch.object(dev.subprocess, 'run', return_value=current):
                with self.assertRaisesRegex(RuntimeError, 'Previous Admin restored') as failure:
                    dev.switch_admin(context, 'on')
            self.assertIn('[REDACTED]', str(failure.exception))
            self.assertNotIn('synthetic-token', str(failure.exception))
            self.assertFalse((context.runtime / runtime.ADMIN_DEV_IMAGE_FILE).exists())
            _, _, first, logs, rollback = context.command.call_args_list
            self.assertEqual(logs.args[0], ['logs', '--tail', '40', 'admin'])
            self.assertTrue(first.kwargs['admin_dev'])
            self.assertFalse(rollback.kwargs['admin_dev'])
            self.assertEqual(rollback.kwargs['overrides'], {'ADMIN_IMAGE': image})
            self.assertTrue(all(call.args[0][-1] == 'admin' and '--no-deps' in call.args[0]
                                for call in (first, rollback)))

    def test_regular_admin_development_uses_the_host_user(self):
        context = runtime.ComposeContext.__new__(runtime.ComposeContext)
        context.values = {'DI_TEST_FIXTURE': 'false'}
        context.base = ['docker', 'compose', '--file', str(runtime.ROOT / 'compose.yaml')]
        with patch.object(runtime.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as run:
            context.command(['config', '--quiet'], admin_dev=True)
        env = run.call_args.kwargs['env']
        self.assertEqual(env['DI_TEST_HOST_UID'], str(os.getuid()))
        self.assertEqual(env['DI_TEST_HOST_GID'], str(os.getgid()))

    def test_off_clears_saved_image_after_down(self):
        with tempfile.TemporaryDirectory() as directory:
            context = SimpleNamespace(runtime=Path(directory), command=Mock(return_value=SimpleNamespace(stdout='')))
            marker = context.runtime / runtime.ADMIN_DEV_IMAGE_FILE
            marker.write_text('sha256:' + 'a' * 64)
            dev.switch_admin(context, 'off')
            self.assertFalse(marker.exists())
            context.command.assert_called_once_with(['ps', '-aq', 'admin'])


if __name__ == '__main__':
    unittest.main()
