"""Offline archive regression; uses only a synthetic Jenkins Home."""
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent/'retired'))
import retire_jenkins_g3 as retire

class ScopedRetirement(unittest.TestCase):
    def test_owned_local_files_archived_and_foreign_state_untouched(self):
        with tempfile.TemporaryDirectory() as root:
            home=pathlib.Path(root)
            def put(name,text):
                f=home/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text)
            put('config.xml',f'<hudson><securityRealm class="{retire.OLD_REALM}"/></hudson>')
            put(retire.GLOBAL+'.xml',f'<{retire.GLOBAL}><urlName>gretl-datenportal</urlName></{retire.GLOBAL}>')
            put(retire.LOCK+'.xml',f'<{retire.LOCK}><resources><resource><name>{retire.OLD_LOCK}</name></resource></resources></{retire.LOCK}>')
            put('casc_configs/jenkins.yaml','securityRealm:\n  local:\n# gretl-datenportal\n'+retire.OLD_LOCK)
            put('jobs/gretl-datenportal-seed/config.xml',f'<project><properties><{retire.SEED}/></properties></project>')
            put('jobs/gretl-datenportal-seed/builds/1/log','historic bytes')
            put('jobs/other/config.xml','<project/>')
            put('workspace/gretl-datenportal-seed/state','retained')
            put('gretl-datenportal/topic-repo/cache','retained')
            for user in ('agi-user','foreign'):
                put('users/'+user+'/config.xml',f'<user><id>{user}</id><properties><{retire.OLD_REALM}_-Details/></properties></user>')
            first=retire.plan(home,'fixture','fixture')
            self.assertEqual(len(first['assets']),6)
            foreign=home/'users/foreign'
            altered={**first,'assets':{**first['assets'],'users/foreign':retire.tree_hash(foreign,home.stat().st_dev)}}
            with self.assertRaisesRegex(RuntimeError,'asset selection changed'):
                retire.apply(home,altered,'fixture','fixture')
            self.assertTrue((home/'jobs/gretl-datenportal-seed').is_dir())
            self.assertEqual(retire.apply(home,first,'fixture','fixture'),1)
            self.assertEqual(retire.apply(home,first,'fixture','fixture'),0)
            archive=home/'data-infrastructure'/'retired'/('legacy-'+first['planId'])
            self.assertEqual((archive/'jobs/gretl-datenportal-seed/builds/1/log').read_text(),'historic bytes')
            self.assertTrue((archive/'assets/users/agi-user/config.xml').is_file())
            self.assertTrue((home/'jobs/other/config.xml').is_file() and (foreign/'config.xml').is_file())

if __name__=='__main__':
    unittest.main()
