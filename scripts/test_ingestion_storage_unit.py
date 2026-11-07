#!/usr/bin/env python3
"""Storage identity preflight and atomic secret encoding; real policy tested separately."""
import importlib.util,pathlib,tempfile,types,unittest,json,os
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('garage_setup',ROOT/'services/garage/setup-compose.py');module=importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name]=module;spec.loader.exec_module(module)
class StoragePreflightTest(unittest.TestCase):
    def test_unknown_bucket_is_never_adopted_or_modified(self):
        with tempfile.TemporaryDirectory() as td:
            target=module.StorageTarget(pathlib.Path(td),'a'*32)
            def api(name,*args,**kwargs):
                if name=='GetClusterStatus':return {'nodes':[{'id':'node1'}]}
                if name=='GetBucketInfo':return {'id':'unexpected','keys':[]}
                self.fail('Mutation before verified bucket binding: '+name)
            with patch.object(module.StorageTarget,'api',side_effect=api):
                p=module.GarageProvisioner(target)
                with self.assertRaisesRegex(module.StorageError,'explicit reviewed cutover'):p.ensure_private_bucket()
    def test_instance_change_fails_before_bucket_or_key_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td);module.write_secrets_atomically(root/'storage-target.json',json.dumps({'instance':'a'*32,'nodes':['original'],'bucket':'ch.so.daten'}))
            target=module.StorageTarget(root,'a'*32)
            with patch.object(module.StorageTarget,'api',return_value={'nodes':[{'id':'another'}]}) as api:
                with self.assertRaisesRegex(module.StorageError,'binding changed'):module.GarageProvisioner(target)
                self.assertEqual(api.call_count,1)
    def test_private_atomic_writes_and_literal_dotenv_encoding(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'secret';module.write_secrets_atomically(p,'original')
            secret='quote" dollar$ backslash\\ equals= hash#'
            encoded=module.encode(secret)
            self.assertEqual(json.loads(encoded.replace('$$','$')),secret)
            module.write_secrets_atomically(p,encoded);self.assertEqual(p.stat().st_mode&0o777,0o600)
            self.assertEqual([x.name for x in p.parent.iterdir()],['secret'])
    def test_atomic_replacement_uses_runtime_directory_owner(self):
        with tempfile.TemporaryDirectory() as directory:
            target=pathlib.Path(directory)/'runtime.env'
            target.write_text('old')
            owner=target.parent.stat()
            other=types.SimpleNamespace(st_uid=owner.st_uid+1,st_gid=owner.st_gid+1)
            with patch.object(module.os,'fstat',return_value=other), \
                    patch.object(module.os,'fchown') as chown:
                module.write_secrets_atomically(target,'new')
            chown.assert_called_once()
            self.assertEqual(chown.call_args.args[1:],(owner.st_uid,owner.st_gid))
            self.assertEqual(target.read_text(),'new')
            self.assertEqual(target.stat().st_mode&0o777,0o600)
if __name__=='__main__':unittest.main()
