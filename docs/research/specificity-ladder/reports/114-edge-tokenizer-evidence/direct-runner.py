import pathlib,os,sys,subprocess,json,time,datetime
c=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/edge-tokenizer-fix-source-v2')
r=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence')
label,python=sys.argv[1:]
env=dict(os.environ,PYTHONPATH=str(c),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
cmd=[python,str(r/'pinned-tokenizer-check.py')];start=time.time()
with (r/(label+'.log')).open('w') as log:result=subprocess.run(cmd,cwd=c,env=env,stdout=log,stderr=subprocess.STDOUT)
record=dict(command=cmd,cwd=str(c),environment={k:env[k] for k in ('PYTHONPATH','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','PYTHONDONTWRITEBYTECODE','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','TOKENIZERS_PARALLELISM')},start_utc=datetime.datetime.fromtimestamp(start,datetime.timezone.utc).isoformat(),exit_code=result.returncode,elapsed_seconds=time.time()-start,log=str(r/(label+'.log')))
(r/(label+'.json')).write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record));print((r/(label+'.log')).read_text()[-2000:])
