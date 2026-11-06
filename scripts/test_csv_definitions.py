#!/usr/bin/env python3
"""Recompile the approved single source with the actual pinned ili2c, without writes to TOPICS."""
import hashlib,json,pathlib,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
TOPICS=ROOT.parent/'dateninfrastruktur-themenrepo'
ADMIN=ROOT.parent/'dateninfrastruktur-admin'
def sha(data):return hashlib.sha256(data).hexdigest()
def run():
    tool=ADMIN/'.runtime/tools/ili2c/ili2c.jar'
    if not tool.is_file():raise RuntimeError('Run explicit ADMIN scripts/interlis_tools.py ensure() before this developer check')
    index=json.loads((TOPICS/'contracts/index.json').read_text())
    for entry in index['definitions']:
        path=(TOPICS/entry['relativePath']).resolve();assert path.is_relative_to(TOPICS)
        assert sha(path.read_bytes())==entry['sha256']
        definition=json.loads(path.read_text())
        for model in definition['modelFiles']:assert sha((TOPICS/model['relativePath']).read_bytes())==model['sha256']
        with tempfile.TemporaryDirectory(prefix='di-g2-compiled-') as directory:
            output=pathlib.Path(directory)/'actual.imd'
            command=['java','-jar',str(tool),'--quiet','--no-auto','--with-predefined','-oIMD16','--out',str(output),*[str(TOPICS/m['relativePath']) for m in definition['modelFiles']]]
            result=subprocess.run(command,capture_output=True,text=True);assert result.returncode==0,result.stderr
            assert sha(output.read_bytes())==definition['compiledModel']['sha256'],'Compiled metadata differs from real pinned compiler'
            assert output.read_bytes()==(TOPICS/definition['compiledModel']['relativePath']).read_bytes()
        print('PASS G20 approved '+definition['definitionKey']+': original model bytes and actual compiler output identical')
if __name__=='__main__':run()
