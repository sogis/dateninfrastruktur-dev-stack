#!/usr/bin/env python3
"""G01: MA-G cannot fall through to the historic management specification."""
import importlib.util,json,pathlib,tempfile,unittest
from review_gate import PHASE_CHECKS,phase_paths,sha
p=pathlib.Path(__file__).with_name('review-phase.py')
spec=importlib.util.spec_from_file_location('review_phase',p);runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
class G0ReviewRoutingTest(unittest.TestCase):
    def test_every_g_phase_uses_new_contract_and_runtime(self):
        data=json.loads((runner.STACK/'docs/implementation/storage-and-delivery/contracts/phase-checks.json').read_text())
        for phase,checks in data['phases'].items():
            self.assertEqual(PHASE_CHECKS[phase],checks)
            self.assertEqual(phase_paths(phase),(pathlib.Path('docs/implementation/storage-and-delivery'),'.runtime/ingestion-review'))
        with self.assertRaises(ValueError):phase_paths('MA-G6')
        self.assertEqual(phase_paths('MA-F0')[1],'.runtime/compose-review')
        self.assertEqual(phase_paths('MA-A')[1],'.runtime/management-review')
    def test_json_contracts_and_actual_workspace_are_hashed(self):
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td);(root/'contracts').mkdir();(root/'templates').mkdir()
            agents=root/'AGENTS.md';agents.write_text('active workspace')
            current=root/'templates/AGENTS.workspace.current.md';current.write_bytes(agents.read_bytes())
            for name in ['EXECUTION_PLAN.md','SPEC_STORAGE.md']:(root/name).write_text(name)
            contract=root/'contracts/phase-checks.json';contract.write_text('{}')
            before=runner.specification_files(root,'MA-G0',agents)
            self.assertEqual(before[str(contract)],sha(contract));self.assertEqual(before[str(current)],sha(agents))
            contract.write_text('{"changed":true}')
            self.assertNotEqual(before,runner.specification_files(root,'MA-G0',agents))
            agents.write_text('unversioned instructions')
            with self.assertRaisesRegex(RuntimeError,'differs'):runner.specification_files(root,'MA-G0',agents)
if __name__=='__main__':unittest.main()
