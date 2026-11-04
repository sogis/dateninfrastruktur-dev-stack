"""The old APISIX/Jenkins namespace must be restored in dependency order."""
import unittest
from migration_coordinator import restart_order
class NamespaceRecovery(unittest.TestCase):
 def test_exact_selected_parent_before_child(self):
  parent={'ref':{'id':'a'*64,'name':'/old-jenkins'},'running':True};child={'ref':{'id':'b'*64,'name':'/old-downloads'},'running':True}
  modes={'a'*64:'own-network','b'*64:'container:'+'a'*64}
  self.assertEqual(restart_order([child,parent],modes),[parent,child])
 def test_unknown_parent_and_cycle_rejected(self):
  a={'ref':{'id':'a'*64,'name':'/a'},'running':True};b={'ref':{'id':'b'*64,'name':'/b'},'running':True}
  with self.assertRaisesRegex(RuntimeError,'OWNERSHIP_MISMATCH'):restart_order([a],{'a'*64:'container:foreign'})
  with self.assertRaisesRegex(RuntimeError,'cyclic'):restart_order([a,b],{'a'*64:'container:'+'b'*64,'b'*64:'container:'+'a'*64})


class TargetBinding(unittest.TestCase):
 def test_env_and_rendered_drift_rejected_before_docker(self):
  import secrets,json
  from unittest.mock import patch
  from compose_runtime import init_context,write_private
  from consolidation import digest,private_write
  from migration_binding import artifact_hashes,runtime_hashes
  from migration_coordinator import Migration
  c=init_context('maf-f2-binding-'+secrets.token_hex(5),test_fixture=True)
  plan={'operation_id':secrets.token_hex(16),'target_env':str(c.env_file),'target_instance':c.values['INSTANCE_ID'],'target_env_sha256':digest(c.env_file),'target_artifacts':artifact_hashes(),'target_runtime_files':runtime_hashes(c)}
  file=c.runtime/'migration/plan.json';private_write(file,plan)
  with patch('compose_runtime.ComposeContext.command') as mutation:
   Migration(file)
   original=c.env_file.read_text();write_private(c.env_file,original+'POSTGRES_VOLUME="protected-old-source"\n')
   with self.assertRaisesRegex(RuntimeError,'SOURCE_CHANGED'):Migration(file)
   write_private(c.env_file,original);write_private(c.runtime/'origin.conf',(c.runtime/'origin.conf').read_text()+'# unplanned change\n')
   with self.assertRaisesRegex(RuntimeError,'SOURCE_CHANGED'):Migration(file)
   mutation.assert_not_called()
 def test_compose_native_secret_codec(self):
  import secrets
  from compose_runtime import ROOT,encode_env,read_env,write_private
  values={'COMPOSE_PROJECT_NAME':'maf-secret-codec','TEST_SECRET':"quote '\" $dollar \\ path\nline",'TEST_LITERAL':'${UNDEFINED}','TEST_DOLLARS':'$$$$ $$ $','TEST_UNICODE':'Grüezi 🌍','TEST_BACKSLASH':'end\\'}
  file=ROOT/'.runtime'/('env-codec-'+secrets.token_hex(4)+'.env');write_private(file,''.join(k+'='+encode_env(v)+'\n' for k,v in values.items()))
  self.assertEqual(read_env(file),values)
if __name__=='__main__':unittest.main()
