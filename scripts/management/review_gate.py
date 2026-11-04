#!/usr/bin/env python3
"""Fail-closed validation of independently produced review artifacts."""
import hashlib, json, pathlib, re, subprocess, sys
PHASE_CHECKS={'MA-0':['M00','M01','M02'],'MA-A':['M03','M04','M05','M06'],'MA-B':['M%02d'%i for i in range(7,14)],'MA-C':['M%02d'%i for i in range(14,21)],'MA-D':['M%02d'%i for i in range(21,26)],'MA-E':['M%02d'%i for i in range(26,34)]}
PHASE_CHECKS.update({'MA-F0':['F01','F02','F03'],'MA-F1':['F%02d'%i for i in range(4,9)],'MA-F2':['F%02d'%i for i in range(9,14)],'MA-F3':['F14','F15','F16'],'MA-F4':['F17','F18','F19','F20']})
def sha(path): return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def require(ok,message):
    if not ok: raise ValueError(message)
def carried_check(entry,requirement,phase=None):
    # A rejected phase may still contain independently executed, unaffected PASS
    # observations. Carry those observations explicitly, never the old verdict.
    for name in ['report','handoff','runner','evidence']:
        require(sha(entry[name+'_path'])==entry[name+'_sha256'],'carried '+name+' changed')
    prior=json.loads(pathlib.Path(entry['report_path']).read_text())
    handoff=json.loads(pathlib.Path(entry['handoff_path']).read_text())
    runner=json.loads(pathlib.Path(entry['runner_path']).read_text())
    require(prior['phase']==handoff['phase'] and prior['candidate_id']==handoff['candidate_id'] and (phase is None or prior['phase']==phase),'carried phase/candidate binding')
    require(prior['binding']['handoff_sha256']==entry['handoff_sha256'],'carried handoff binding')
    require(prior['binding']['specification_sha256']==handoff['specification']['aggregate_sha256'],'carried spec binding')
    require(prior['binding']['request_sha256']==handoff['request']['sha256'],'carried request binding')
    require(prior['binding']['repositories']==[{k:r[k] for k in ['name','head_sha']} for r in handoff['repositories']],'carried SHA binding')
    require(runner['exit_code']==0 and runner['product_unchanged'] is True and prior['integrity']['product_unchanged'] is True,'carried integrity')
    require(runner['actual_provider_model']=='deepseek/deepseek-flash' and re.fullmatch(r'(?:opencode v)?2\.\d+\.\d+',runner['opencode_version']),'carried model/version')
    require(runner['read_tool_executed'] and runner['shell_tool_executed'],'carried tests lack tools')
    for key in ['actual_provider_model','opencode_version','session_id']:require(prior['reviewer'][key]==runner[key],'carried reviewer binding')
    found=[c for c in prior['checks'] if c['requirement_id']==requirement]
    require(len(found)==1,'carried check missing/duplicate');check=found[0]
    require(check['status']=='PASS' and check['execution']=='EXECUTED' and check['expected_exit']==check['observed_exit']==0,'carried check was not executed successfully')
    require(bool(entry.get('reason')),'carried non-impact reason missing')
    return check

def validate(handoff_path,report_path,runner):
    h=json.loads(pathlib.Path(handoff_path).read_text()); r=json.loads(pathlib.Path(report_path).read_text())
    require(not r.get('example_only',False),'example cannot open gate')
    require(r['phase']==h['phase'] and r['candidate_id']==h['candidate_id'],'wrong phase/candidate')
    b=r['binding']; require(b['handoff_sha256']==sha(handoff_path),'wrong handoff hash')
    require(b['specification_sha256']==h['specification']['aggregate_sha256'],'wrong specification hash')
    require(b['request_sha256']==h['request']['sha256'],'wrong request hash')
    require(b['repositories']==[{k:x[k] for k in ('name','head_sha')} for x in h['repositories']],'wrong repository SHAs')
    require(sha(h['request']['path'])==h['request']['sha256'],'request changed')
    for path,hash_value in h['specification']['files_sha256'].items(): require(sha(path)==hash_value,'spec changed')
    require(sha(h['workspace_agents']['path'])==h['workspace_agents']['sha256'],'workspace agents changed')
    for repo in h['repositories']:
        head=subprocess.check_output(['git','-C',repo['path'],'rev-parse','HEAD'],text=True).strip()
        require(head==repo['head_sha'],'checkout HEAD changed')
        require(subprocess.check_output(['git','-C',repo['path'],'status','--porcelain'],text=True)=='','product checkout changed')
    require(runner['exit_code']==0 and runner['product_unchanged'] is True,'process or integrity failed')
    require(runner['actual_provider_model']=='deepseek/deepseek-flash','wrong actual model')
    require(re.fullmatch(r'(?:opencode v)?2\.\d+\.\d+',runner['opencode_version']) is not None,'not OpenCode2')
    reviewer=r['reviewer']
    for key in ('actual_provider_model','opencode_version','session_id'):require(reviewer[key]==runner[key],'wrong reviewer '+key)
    require(runner['read_tool_executed'] and runner['shell_tool_executed'],'review tools not executed')
    require(r['integrity']['product_unchanged'] is True,'reviewer integrity missing')
    checks=r['checks']; ids=[x['requirement_id'] for x in checks]
    require(sorted(ids)==sorted(PHASE_CHECKS[h['phase']]),'missing/duplicate/foreign mandatory IDs')
    for c in checks:
        require(c['status']=='PASS','required check failed')
        if c['execution']=='CARRIED':
            entry=h.get('test_selection',{}).get('carried_checks',{}).get(c['requirement_id'])
            require(bool(entry),'unlisted carried check');prior=carried_check(entry,c['requirement_id'],h['phase'])
            require(c.get('source_report_sha256')==entry['report_sha256'] and bool(c.get('reason')),'carried reference/reason missing')
            require(c['evidence_path']==entry['evidence_path'],'carried evidence path')
            for key in ['command','cwd','expected_exit','observed_exit']:require(c[key]==prior[key],'carried command/result changed')
        else:require(c['execution']=='EXECUTED','required check skipped')
        require(c['observed_exit']==c['expected_exit']==0,'test exit mismatch')
        for key in ('command','cwd','observation','evidence_path'):require(bool(c.get(key)),'missing check '+key)
        require(pathlib.Path(c['evidence_path']).is_file(),'missing test evidence')
    require(r['counterexample']['executed'] is True,'no executed independent counterexample')
    for key in ('hypothesis','command','expected','observed','evidence_path'):require(bool(r['counterexample'].get(key)),'missing counterexample '+key)
    require(pathlib.Path(r['counterexample']['evidence_path']).is_file(),'missing counterexample evidence')
    require(not r.get('not_executed'),'required evidence not executed')
    require(r['code_review']['goal_reached'] is True,'phase goal not reached')
    require(not any(x.get('severity') in ('BLOCKER','MAJOR') for x in r['findings']),'blocking findings')
    require(r['verdict']=='ABGENOMMEN','independent verdict does not accept')
    return True
if __name__=='__main__':
    try:
        validate(sys.argv[1],sys.argv[2],json.loads(pathlib.Path(sys.argv[3]).read_text()))
        print('ABGENOMMEN: exact candidate and independently executed evidence verified')
    except (KeyError,ValueError,OSError,TypeError,IndexError) as e:
        print('CLOSED: '+str(e),file=sys.stderr);sys.exit(1)
