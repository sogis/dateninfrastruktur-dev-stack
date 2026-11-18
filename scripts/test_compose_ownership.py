"""The direct-operation preflight must refuse unknown or incomplete instances."""
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import compose_runtime as runtime
from setup_instance import setup


class ComposeOwnershipTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.context = runtime.ComposeContext.__new__(runtime.ComposeContext)
        self.context.project = 'fixture-project'
        self.context.runtime = Path(directory.name)
        self.context.values = dict(INSTANCE_ID='fixture', DI_STORAGE_BUCKET='ch.so.daten')
        self.context.values.update({key: 'fixture_' + logical for key, (logical, _) in runtime.VOLUMES.items()})
        self.context.verify_project = Mock()
        self.names = set(self.context.volume_bindings().values())
        self.label_project = self.context.project

    def docker(self, resource, action, *args):
        if (resource, action) == ('network', 'ls'):
            return ''
        if (resource, action) == ('volume', 'ls'):
            return '\n'.join(json.dumps([name, self.label_project, name.removeprefix('fixture_')])
                             for name in self.names)
        self.fail((resource, action, args))

    def record_setup(self):
        (self.context.runtime / 'setup-complete.json').write_text(json.dumps({
            'instance': self.context.values['INSTANCE_ID'], 'volumes': self.context.volume_bindings(),
        }))

    def test_private_init_keeps_configuration_and_round_trips_multiline_credentials(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runtime, 'docker_output', return_value=''):
            root = Path(directory).resolve()
            (root / 'services').symlink_to(runtime.ROOT / 'services')
            with patch.object(runtime, 'ROOT', root):
                context = runtime.init_context('fixture-private', test_fixture=True)
                self.assertEqual(context.env_file.stat().st_mode & 0o777, 0o600)
                self.assertEqual(context.runtime.stat().st_mode & 0o777, 0o700)
                secret = 'a=b# "quote" \\ $ $$ ${literal}\nCOMPOSE_FILE=inside-the-value'
                content = context.env_file.read_text() + 'EXTRA_SECRET=' + runtime.encode_env(secret) + '\nEMPTY=\nPROJECT_REFERENCE="${COMPOSE_PROJECT_NAME}"\n'
                runtime.write_private(context.env_file, content)
                with patch.dict('os.environ', {'COMPOSE_PROJECT_NAME': 'foreign-project', 'INSTANCE_ID': 'foreign',
                                               'POSTGRES_VOLUME': 'foreign', 'ADMIN_IMAGE': 'foreign'}):
                    current = runtime.init_context('fixture-private', test_fixture=True)
                self.assertEqual(current.env_file.read_text(), content)
                self.assertEqual(current.values['INSTANCE_ID'], context.values['INSTANCE_ID'])
                self.assertEqual(current.values['POSTGRES_VOLUME'], context.values['POSTGRES_VOLUME'])
                self.assertEqual(current.values['ADMIN_IMAGE'], context.values['ADMIN_IMAGE'])
                self.assertEqual(current.values['EXTRA_SECRET'], secret)
                self.assertEqual(current.values['EMPTY'], '')
                self.assertEqual(current.values['PROJECT_REFERENCE'], context.project)
                self.assertNotIn('COMPOSE_FILE', current.values)
                runtime.write_private(context.env_file, content + 'BROKEN="unterminated\n')
                with self.assertRaisesRegex(RuntimeError, '^Invalid private dotenv configuration; details withheld$'):
                    runtime.read_env(context.env_file)

    def test_start_requires_setup_and_unchanged_volume_bindings(self):
        with self.assertRaisesRegex(RuntimeError, 'Explicit setup'):
            self.context.verify_resources(require_setup=True)
        self.record_setup()
        with patch.object(runtime, 'docker_output', side_effect=self.docker):
            self.context.verify_resources(require_setup=True)
            self.names.remove(self.context.values['POSTGRES_VOLUME'])
            with self.assertRaisesRegex(RuntimeError, 'missing: POSTGRES_VOLUME'):
                self.context.verify_resources(require_setup=True)
            self.context.values['POSTGRES_VOLUME'] = 'foreign'
            with self.assertRaisesRegex(RuntimeError, 'mapping changed'):
                self.context.verify_resources(require_setup=True)

    def test_matching_name_alone_does_not_authorize_using_a_volume(self):
        self.label_project = 'foreign'
        with patch.object(runtime, 'docker_output', side_effect=self.docker):
            with self.assertRaisesRegex(RuntimeError, 'OWNERSHIP_MISMATCH.*POSTGRES_VOLUME'):
                self.context.verify_resources()

    def test_retained_setup_does_not_initialize_a_missing_database(self):
        self.record_setup()
        self.context.command = Mock(side_effect=[None, SimpleNamespace(stdout='0\n')])
        with patch.object(runtime, 'docker_output', side_effect=self.docker):
            with self.assertRaisesRegex(RuntimeError, 'Known management database is missing'):
                setup(self.context)
        self.assertEqual(self.context.command.call_count, 2)

    def test_log_filter_refuses_to_emit_logs_from_a_foreign_project(self):
        context = Mock()
        context.verify_project.side_effect = RuntimeError('OWNERSHIP_MISMATCH')
        with patch.object(runtime, 'ComposeContext', return_value=context), \
                patch.object(sys, 'argv', ['compose_runtime.py', 'redact', '--env', 'fixture.env']), \
                patch.object(sys, 'stdin', io.StringIO('foreign log\n')), \
                patch.object(sys, 'stdout', io.StringIO()) as output:
            with self.assertRaisesRegex(RuntimeError, 'OWNERSHIP_MISMATCH'):
                runtime.main()
            self.assertEqual(output.getvalue(), '')

    def test_jenkins_candidate_requires_label_and_returns_immutable_id(self):
        identifier = 'sha256:' + 'a' * 64
        result = SimpleNamespace(returncode=0, stdout=identifier + ' 6.0.0-SNAPSHOT\n')
        with patch.object(runtime.subprocess, 'run', return_value=result):
            self.assertEqual(runtime.jenkins_image_id('fixture:jenkins'), identifier)
            result.stdout = identifier + ' 5.0.0\n'
            with self.assertRaisesRegex(RuntimeError, 'Expected a local Jenkins image'):
                runtime.jenkins_image_id('fixture:jenkins')


if __name__ == '__main__':
    unittest.main()
