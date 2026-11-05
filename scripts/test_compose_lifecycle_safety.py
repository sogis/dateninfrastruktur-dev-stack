#!/usr/bin/env python3
"""Lifecycle scope failures must precede configuration changes or Docker mutations."""
import pathlib,tempfile,types,unittest
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

if __name__=="__main__":unittest.main()
