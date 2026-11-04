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
            # Carry only a bound, successful, unchanged observation; never a verdict.
            prior_handoff=p/'prior-handoff.json';prior_handoff.write_bytes(hp.read_bytes())
            prior_report=p/'prior-report.json';old=copy.deepcopy(r);old.update(verdict='NACHARBEIT',findings=[{'severity':'MAJOR','id':'other-contract'}]);prior_report.write_text(json.dumps(old))
            prior_runner=p/'prior-runner.json';prior_runner.write_text(json.dumps(runner))
            entry={'reason':'this contract is unchanged'}
            for name,path in [('handoff',prior_handoff),('report',prior_report),('runner',prior_runner),('evidence',evidence)]:entry[name+'_path']=str(path);entry[name+'_sha256']=sha(path)
            identifier=PHASE_CHECKS[phase][0];delta=copy.deepcopy(h);delta['candidate_id']='delta';delta['test_selection']={'carried_checks':{identifier:entry}}
            dh=p/'delta-handoff.json';dr=copy.deepcopy(r);dr['candidate_id']='delta';dr['checks'][0].update(execution='CARRIED',source_report_sha256=entry['report_sha256'],reason='unchanged contract')
            def delta_check(ok):
                dh.write_text(json.dumps(delta));dr['binding']['handoff_sha256']=sha(dh);rp.write_text(json.dumps(dr))
                if ok:self.assertTrue(validate(dh,rp,runner))
                else:
                    with self.assertRaises((ValueError,KeyError)):validate(dh,rp,runner)
            delta_check(True)
            dr['checks'][0].pop('reason');delta_check(False);dr['checks'][0]['reason']='unchanged contract'
            entry['report_sha256']='0'*64;delta_check(False);entry['report_sha256']=sha(prior_report)
            old['checks'][0]['status']='FAIL';prior_report.write_text(json.dumps(old));entry['report_sha256']=sha(prior_report);dr['checks'][0]['source_report_sha256']=entry['report_sha256'];delta_check(False)
            old['checks'][0]['status']='PASS';prior_report.write_text(json.dumps(old));entry['report_sha256']=sha(prior_report);dr['checks'][0]['source_report_sha256']=entry['report_sha256'];delta_check(True)
            evidence.write_text('changed after binding');delta_check(False);evidence.write_text('executed probe')
            del delta['test_selection']['carried_checks'][identifier];delta_check(False)
            rp.unlink()
            with self.assertRaises(OSError):validate(hp,rp,runner)
            (repo/'source').write_text('tampered');check(r)
if __name__=='__main__':unittest.main()
