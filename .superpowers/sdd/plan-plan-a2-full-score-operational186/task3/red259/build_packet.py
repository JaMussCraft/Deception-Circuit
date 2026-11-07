"""One-off stdlib packaging only; does not execute or import tests."""
from pathlib import Path
import ast, hashlib, json, shutil
P=Path(__file__).resolve().parent
S=P.parents[2]
C=S/'plan-a2-full-score-operational186/candidate'
H=S/'plan-a2-bridges-assay/h100-g3-20261103/root-model-phase-release-helper/r5-r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(source,dest):dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(str(source),str(dest))
names=['test_full_score_release.py','test_full_score_usage.py','test_full_score_cache.py']
originals={}
for n in names:
    source=C/'tests'/n;copy(source,P/'tests'/n);originals[str(source)]=sha(source)
for section,names2 in [('gpu',['common.py']),('cpu',['supervisor.py']),('tests',['test_full_score_cpu.py','test_full_score_controller.py'])]:
    for n in names2:
        source=C/section/n;copy(source,P/'accepted'/section/n);originals[str(source)]=sha(source)
for n in ['config.json','banks.json','run_manifest.json']:
    source=S/'plan-plan-a2-full-score-operational186/task1/fixtures'/n
    copy(source,P/'task1/fixtures'/n);originals[str(source)]=sha(source)
for n in ['helper.py','cache_gate.py']:
    source=H/n;copy(source,P/'historical-root'/n);originals[str(source)]=sha(source)
(P/'absent-root').mkdir(exist_ok=True)
for source in [S/'plan-a2-full-score-operational186/reference-pins.json',S/'plan-a2-task2-terminal-review258/verdict.json',S/'plan-a2-full-score-operational186/task3/source-inventory235.json']:
    originals[str(source)]=sha(source)
count=0
for n in names:
    tree=ast.parse((P/'tests'/n).read_text())
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name.startswith('test_'):
            number=1
            for d in node.decorator_list:
                if isinstance(d,ast.Call) and isinstance(d.func,ast.Attribute) and d.func.attr=='parametrize':
                    assert isinstance(d.args[1],(ast.List,ast.Tuple));number*=len(d.args[1].elts)
            count+=number
(P/'original-source-pins.json').write_text(json.dumps(originals,indent=2,sort_keys=True)+'\n')
(P/'resources.json').write_text(json.dumps(dict(kind='CPU_FIXTURE_RED_ONLY',expected_cases_each=count,
    interpreters=['/u/swong2/.conda/envs/mgnp/bin/python','/sw/external/python/anaconda3/bin/python3.9'],
    cpus=2,memory='4G',walltime='00:06:00',per_invocation_timeout_seconds=70,
    model_loaded=False,native_imports=False,scheduler_submission_by_worker=False,
    production_root_files_absent=True,actual_resource_or_admission_binding=False),indent=2)+'\n')
print('expected cases per invocation:',count)
