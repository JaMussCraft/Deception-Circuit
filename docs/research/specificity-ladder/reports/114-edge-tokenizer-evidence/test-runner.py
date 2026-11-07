import os,sys,json,time,subprocess,pathlib,datetime
c=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/edge-tokenizer-fix-source-v2')
r=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence')
label,python,selector=sys.argv[1:]
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
if 'pinned' in label:env.update(A3_TEST_TOKENIZER_MODEL='meta-llama/Llama-3.1-8B-Instruct',A3_TEST_TOKENIZER_REVISION='0e9e39f249a16976918f6564b8830bc894c89659')
cmd=[python,'-m','pytest','-p','no:cacheprovider','--basetemp=/tmp/a3-edge-114-'+label,'tests/test_a3_edge_pipeline.py','-q']
if selector:cmd+=['-k',selector]
start=time.time()
with (r/(label+'.log')).open('w') as log:result=subprocess.run(cmd,cwd=c,env=env,stdout=log,stderr=subprocess.STDOUT)
receipt=dict(label=label,command=cmd,cwd=str(c),environment={k:env[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','PYTHONDONTWRITEBYTECODE','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','TOKENIZERS_PARALLELISM')},start_utc=datetime.datetime.fromtimestamp(start,datetime.timezone.utc).isoformat(),elapsed_seconds=time.time()-start,exit_code=result.returncode,log=str(r/(label+'.log')))
(r/(label+'.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt));print((r/(label+'.log')).read_text()[-6500:])
