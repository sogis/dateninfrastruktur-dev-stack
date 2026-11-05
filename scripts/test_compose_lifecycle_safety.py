#!/usr/bin/env python3
"""Lifecycle scope failures must precede configuration changes or Docker mutations."""
import copy,json,pathlib,tempfile,types,unittest
from unittest.mock import Mock,patch
import compose_operations as ops
from migration_retirement import recovery_config

class LifecycleSafety(unittest.TestCase):
    def test_recovery_and_missing_setup_block_before_start(self):
        with tempfile.TemporaryDirectory(prefix='di-lifecycle-') as directory:
            root=pathlib.Path(directory);runtime=root/'.runtime/context';runtime.mkdir(parents=True)
            c=types.SimpleNamespace(runtime=runtime,values={},command=Mock())
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
    def test_recovery_preserves_dynamic_port_literal_env_and_shared_namespace(self):
        with tempfile.TemporaryDirectory(prefix='di-recovery-') as directory:
            root=pathlib.Path(directory);operation=types.SimpleNamespace(root=root,plan={'operation_id':'00000000-0000-4000-8000-000000000001'})
            parent={'Id':'a'*64,'Name':'/original-parent','Config':{'Hostname':'original','Env':['LITERAL=${HOME}#=value'],'Entrypoint':['python'],'Cmd':['-V']},'HostConfig':{'RestartPolicy':{'Name':'no'},'NetworkMode':'bridge','PortBindings':{'8089/tcp':[{'HostIp':'127.0.0.1','HostPort':''}]}},'Mounts':[],'NetworkSettings':{'Networks':{},'Ports':{'8089/tcp':[{'HostIp':'127.0.0.1','HostPort':'30987'}]}}}
            child=copy.deepcopy(parent);child.update(Id='b'*64,Name='/original-child');child['HostConfig'].update(NetworkMode='container:'+parent['Id'],PortBindings={})
            file,_,mapping=recovery_config(operation,[parent,child],{parent['Id']:'fixture:parent',child['Id']:'fixture:child'},{parent['Id']:'linux/arm64',child['Id']:'linux/arm64'},root)
            data=json.loads(file.read_text());p=data['services'][mapping[parent['Id']]];c=data['services'][mapping[child['Id']]]
            self.assertEqual(p['ports'][0]['published'],'30987')
            self.assertEqual(p['environment'],['LITERAL=$${HOME}#=value'])
            self.assertEqual(c['network_mode'],'service:'+mapping[parent['Id']]);self.assertNotIn('hostname',c)
            # Without a preserved dynamic binding, never replace it with a random port.
            parent['NetworkSettings']['Ports']={}
            with self.assertRaisesRegex(RuntimeError,'dynamically assigned'):recovery_config(operation,[parent],{parent['Id']:'fixture:parent'},{parent['Id']:'linux/arm64'},root)
class RollbackStartGuard(unittest.TestCase):
    def test_target_writes_reject_before_start_block_and_valid_rollback_blocks_first(self):
        from migration_coordinator import rollback
        context=types.SimpleNamespace(command=Mock());callback=Mock()
        journal={'database_restored':True,'target_management_baseline':{'known':'baseline'},'status':'CUTOVER'}
        plan={'scope':{},'source_states':[{'ref':{'id':'a'*64,'name':'/source'},'running':False}]}
        with patch('migration_coordinator.snapshot',return_value={'unaccounted':'write'}),self.assertRaisesRegex(RuntimeError,'ROLLBACK_UNSAFE'):rollback(plan,context,journal,callback)
        context.command.assert_not_called();callback.assert_not_called()
        events=[];context.command=Mock(side_effect=lambda *args:events.append('target-stop'))
        with patch('migration_coordinator.snapshot',return_value={'known':'baseline'}),patch('migration_coordinator.verify_source',return_value='a'*64),patch('migration_coordinator.inspect',return_value={'HostConfig':{'NetworkMode':'default'},'State':{'Running':False}}):
            rollback(plan,context,journal,lambda:events.append('start-block'))
        self.assertEqual(events,['start-block','target-stop'])

if __name__=='__main__':unittest.main()
