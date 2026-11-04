#!/usr/bin/env python3
"""Fail-closed validation of independently produced review artifacts."""
import hashlib, json, pathlib, re, subprocess, sys
PHASE_CHECKS={'MA-0':['M00','M01','M02'],'MA-A':['M03','M04','M05','M06'],'MA-B':['M%02d'%i for i in range(7,14)],'MA-C':['M%02d'%i for i in range(14,21)],'MA-D':['M%02d'%i for i in range(21,26)],'MA-E':['M%02d'%i for i in range(26,34)]}
def sha(path): return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def require(ok,message):
    if not ok: raise ValueError(message)
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
        require(c['status']=='PASS' and c['execution']=='EXECUTED','required check skipped or failed')
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
