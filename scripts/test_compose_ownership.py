"""The direct-operation preflight must refuse unknown or incomplete instances."""
import json
from pathlib import Path
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
            return '\n'.join(self.names)
        if (resource, action) == ('volume', 'inspect'):
            return json.dumps([{'Labels': {
                'com.docker.compose.project': self.label_project,
                'com.docker.compose.volume': args[0].removeprefix('fixture_'),
            }}])
        self.fail((resource, action, args))

    def record_setup(self):
        (self.context.runtime / 'setup-complete.json').write_text(json.dumps({
            'instance': self.context.values['INSTANCE_ID'], 'volumes': self.context.volume_bindings(),
        }))

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
