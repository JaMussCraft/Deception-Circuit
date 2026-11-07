"""Freeze pure operational implementation, accepted tests and native code only."""
from pathlib import Path
import ast,hashlib,json,os,shutil
P=Path(__file__).resolve().parent;S=P.parents[2]
C=S/'plan-a2-full-score-operational186/candidate'
D=P/'closure/sdd';F=D/'plan-a2-full-score-operational186/candidate'
N=S.parents[1]/'outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526'
# Resolve original native export from the root-supplied worktree, not cwd.
N=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526')
originals={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cp(source,dest):
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(str(source),str(dest));originals[str(source)]=sha(source)
for source in C.rglob('*'):
    if source.is_file() and '__pycache__' not in source.parts and source.suffix in ('.py','.sh','.json'):
        cp(source,F/source.relative_to(C))
for source in (S/'plan-plan-a2-full-score-operational186/task1/fixtures').iterdir():
    if source.is_file():cp(source,D/'plan-plan-a2-full-score-operational186/task1/fixtures'/source.name)
observer=S/'plan-plan-a2-full-score-operational186/task2/green-r4/run_cpu_green.py'
cp(observer,P/'observer/run_cpu_green.py')
for name in ('helper.py','cache_gate.py'):
    source=S/'plan-a2-bridges-assay/h100-g3-20261103/root-model-phase-release-helper/r5-r2'/name
    cp(source,P/'historical-root'/name)
# Native source is a frozen code-only export, with the same four literal input
# aliases. No dataset/model/cache/weight content is copied or imported here.
snapshot=json.loads((N/'snapshot.json').read_text());cp(N/'snapshot.json',P/'native-snapshot.json')
assert len(snapshot['source_sha256'])==511 and len(snapshot['input_links'])==4
for name,digest in snapshot['source_sha256'].items():
    source=Path(snapshot['runtime_root'])/name;assert sha(source)==digest;cp(source,P/'native-source'/name)
for name,target in snapshot['input_links'].items():
    path=P/'native-source'/name;path.parent.mkdir(parents=True,exist_ok=True);path.symlink_to(target)
for source in [S/'plan-a2-full-score-operational186/reference-pins.json',S/'plan-a2-task2-terminal-review258/verdict.json']:
    originals[str(source)]=sha(source)
(P/'original-source-pins.json').write_text(json.dumps(originals,indent=2,sort_keys=True)+'\n')
counts={}
for name in ('test_full_score_release.py','test_full_score_usage.py','test_full_score_cache.py','test_full_score_root_integration.py','test_full_score_root_wait.py'):
    total=0
    for node in ast.parse((F/'tests'/name).read_text()).body:
        if isinstance(node,ast.FunctionDef) and node.name.startswith('test_'):
            n=1
            for d in node.decorator_list:
                if isinstance(d,ast.Call) and isinstance(d.func,ast.Attribute) and d.func.attr=='parametrize':
                    assert isinstance(d.args[1],(ast.List,ast.Tuple));n*=len(d.args[1].elts)
            total+=n
    counts[name]=total
resources=dict(cpus=2,memory='8G',walltime='00:07:00',GPUs=0,full_timeout_seconds=150,baseline_timeout_seconds=20,
    expected_baseline_cases=98,accepted_Task1_Task2_cases=226,new_case_counts=counts,expected_GREEN_cases=226+sum(counts.values()),
    interpreters=[dict(label='base39',python='/sw/external/python/anaconda3/bin/python3.9',pytest='8.3.3',python_minor=[3,9]),
                  dict(label='mgnp',python='/u/swong2/.conda/envs/mgnp/bin/python',pytest='9.1.1',python_minor=[3,12])],
    prior_226_case_seconds=[35.692,34.586],fixture_only=True,actual_resources_or_admission_bound=False)
(P/'resources.json').write_text(json.dumps(resources,indent=2)+'\n')
print(json.dumps(resources))
