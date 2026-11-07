"""Finish authorized steps serially; stop at first actual failure."""
import pathlib,subprocess,sys,json,datetime
root=pathlib.Path(__file__).parent
for step in ('edge','inventories','mask-dry-run','dry-run','validate','benchmark'):
    print('BEGIN '+step,flush=True)
    code=subprocess.call([sys.executable,str(root/'run-step.py'),step])
    if code:raise SystemExit(code)
print('ALL_CPU_PREPARATION_AND_SOURCE_MEASUREMENTS_COMPLETED',flush=True)
