#!/usr/bin/env python3
import copy, hashlib, json, pathlib, subprocess, tempfile, unittest, os
from review_gate import validate, sha, PHASE_CHECKS
class ReviewGateContractTest(unittest.TestCase):
    def test_rejects_invalid_evidence(self):
        with tempfile.TemporaryDirectory(prefix='di-gate-') as td:
            p=pathlib.Path(td); repo=p/'repo';repo.mkdir()
            subprocess.run(['git','init','-q',str(repo)],check=True)
            (repo/'source').write_text('fixed candidate')
            subprocess.run(['git','-C',str(repo),'add','source'],check=True)
            subprocess.run(['git','-C',str(repo),'-c','user.name=Gate Test','-c','user.email=gate@example.invalid','commit','-qm','fixture'],check=True)
            phase=os.environ.get('DI_GATE_TEST_PHASE','MA-0')
            head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
            evidence=p/'evidence'; evidence.write_text('executed probe')
            spec=p/'spec';spec.write_text('fixed spec'); request=p/'request';request.write_text('fixed request')
            agents=p/'AGENTS.md';agents.write_text('fixed workspace instructions')
            h={'phase':phase,'candidate_id':'test','specification':{'aggregate_sha256':'fixed','files_sha256':{str(spec):sha(spec)}},'request':{'path':str(request),'sha256':sha(request)},'repositories':[{'name':'repo','path':str(repo),'head_sha':head}],'workspace_agents':{'path':str(agents),'sha256':sha(agents)}}
            hp=p/'handoff.json';hp.write_text(json.dumps(h))
            runner={'exit_code':0,'product_unchanged':True,'actual_provider_model':'deepseek/deepseek-flash','opencode_version':'opencode v2.2.5','session_id':'fresh','read_tool_executed':True,'shell_tool_executed':True}
            r={'phase':phase,'candidate_id':'test','binding':{'handoff_sha256':sha(hp),'specification_sha256':'fixed','request_sha256':sha(request),'repositories':[{'name':'repo','head_sha':head}]},'reviewer':{k:runner[k] for k in ('actual_provider_model','opencode_version','session_id')},'checks':[{'requirement_id':i,'status':'PASS','execution':'EXECUTED','command':'fixture','cwd':td,'expected_exit':0,'observed_exit':0,'observation':'fixture','evidence_path':str(evidence)} for i in PHASE_CHECKS[phase]],'counterexample':{'executed':True,'hypothesis':'fixture','command':'fixture','expected':'fixture','observed':'fixture','evidence_path':str(evidence)},'integrity':{'product_unchanged':True},'code_review':{'goal_reached':True},'findings':[],'verdict':'ABGENOMMEN'}
            rp=p/'review.json'
            def check(obj,ok=False):
                rp.write_text(json.dumps(obj))
                if ok:self.assertTrue(validate(hp,rp,runner))
                else:
                    with self.assertRaises((ValueError,KeyError)):validate(hp,rp,runner)
            check(r,True)
            for mut in [lambda x:x['binding']['repositories'][0].update(head_sha='0'*40),lambda x:x['checks'].pop(),lambda x:x['checks'].append(x['checks'][0]),lambda x:x['checks'][0].update(status='NOT_EXECUTED'),lambda x:x['reviewer'].update(actual_provider_model='opencode/deepseek-v4.1-flash-free'),lambda x:x['counterexample'].update(executed=False),lambda x:x.update(example_only=True),lambda x:x.update(verdict='NICHT_PRUEFBAR')]:
                bad=copy.deepcopy(r);mut(bad);check(bad)
            rp.unlink()
            with self.assertRaises(OSError):validate(hp,rp,runner)
            (repo/'source').write_text('tampered');check(r)
if __name__=='__main__':unittest.main()
