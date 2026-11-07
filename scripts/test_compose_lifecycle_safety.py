#!/usr/bin/env python3
"""Lifecycle scope failures must precede configuration changes or Docker mutations."""
import json,pathlib,tempfile,types,unittest
from unittest.mock import Mock,patch
import compose_operations as ops

class LifecycleSafety(unittest.TestCase):
    def test_recovery_and_missing_setup_block_before_start(self):
        with tempfile.TemporaryDirectory(prefix='di-lifecycle-') as directory:
            root=pathlib.Path(directory);runtime=root/'.runtime/context';runtime.mkdir(parents=True)
            c=types.SimpleNamespace(runtime=runtime,values={"DI_STORAGE_BUCKET":"ch.so.daten"},command=Mock())
            with patch.object(ops,'ROOT',root),patch.object(ops,'resolve',return_value=c) as resolve,patch.object(ops,'activate') as activate,patch.object(ops,'build') as build:
                (root/'.runtime/active-recovery.json').write_text('{}')
                with patch('sys.argv',['ops','init']),self.assertRaisesRegex(RuntimeError,'rollback is active'):ops.main()
                resolve.assert_not_called();activate.assert_not_called();build.assert_not_called();c.command.assert_not_called()
                (root/'.runtime/active-recovery.json').unlink()
                (runtime/'rollback-active.json').write_text('{}')
                with patch('sys.argv',['ops','init']),self.assertRaisesRegex(RuntimeError,'rollback is active'):ops.main()
                activate.assert_not_called();c.command.assert_not_called()
                (runtime/'rollback-active.json').unlink()
                with patch('sys.argv',['ops','up']),self.assertRaisesRegex(RuntimeError,'Explicit setup'):ops.main()
                build.assert_not_called();c.command.assert_not_called()

    def test_missing_registry_image_stops_before_container_change(self):
        context = types.SimpleNamespace(
            values={'JENKINS_IMAGE': 'sha256:old', 'DI_TEST_FIXTURE': 'false'},
            command=Mock(return_value=types.SimpleNamespace(stdout=json.dumps({
                'services': {'jenkins': {'image': 'ghcr.io/sogis/jenkins:0.2.1'}}
            }))),
            redact=lambda value: value,
        )
        ops.select_images(context, 'registry')
        self.assertEqual(context.command_overrides['JENKINS_IMAGE'], '')
        with patch.object(ops.subprocess, 'run', return_value=types.SimpleNamespace(returncode=1, stderr='denied')):
            with self.assertRaisesRegex(RuntimeError, 'ghcr.io/sogis/jenkins:0.2.1'):
                ops.start(context, 'registry', restart=True)
        context.command.assert_called_once_with(['config', '--format', 'json'])

    def test_start_persists_mode_only_after_success(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = pathlib.Path(directory)
            context = types.SimpleNamespace(runtime=runtime, command=Mock(side_effect=RuntimeError('unhealthy')))
            marker = runtime/'startup-image-mode'
            marker.write_text('registry\n')
            with patch.object(ops, 'prepare_start', return_value='sha256:fixture'), \
                    patch.object(ops.subprocess, 'check_output', return_value='sha256:fixture'):
                with self.assertRaisesRegex(RuntimeError, 'unhealthy'):
                    ops.start(context, 'local')
                self.assertEqual(marker.read_text(), 'registry\n')
                context.command.side_effect = None
                context.command.return_value.stdout = 'fixture-container'
                ops.start(context, 'local')
            self.assertEqual(marker.read_text(), 'local\n')
            start_args = context.command.call_args_list[-2].args[0]
            self.assertIn('--no-build', start_args)
            self.assertIn('never', start_args)

    def test_local_tags_keep_fixtures_separate(self):
        context = types.SimpleNamespace(project='dateninfrastruktur', values={'DI_TEST_FIXTURE': 'false'})
        ops.select_images(context, 'local')
        self.assertEqual(context.command_overrides['ADMIN_IMAGE'], 'dateninfrastruktur-admin:local')
        context.project = 'mag-test-fresh'
        context.values['DI_TEST_FIXTURE'] = 'true'
        ops.select_images(context, 'local')
        self.assertEqual(context.command_overrides['ADMIN_IMAGE'], 'dateninfrastruktur-admin:mag-test-fresh')

if __name__=="__main__":unittest.main()
