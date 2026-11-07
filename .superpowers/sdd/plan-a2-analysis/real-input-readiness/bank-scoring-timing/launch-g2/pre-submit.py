"""Brief read-only gate run by root before GPU submission, after Slurm CPU preflight."""
import os,pathlib,json,time
from common import C,L,sha,packet
packet();p=pathlib.Path(os.environ['A2_TIMING_PREFLIGHT_COMPLETE']);d=json.loads(p.read_text())
assert d['complete'] is True and d['launch_manifest_sha256']==sha(L/'manifest.json')
assert 0<=time.time()-d['completed_epoch']<=900,'refresh CPU protection preflight before GPU submission'
assert d['source']['source_commit']==C['commit'] and d['source']['groups_file_sha256']==C['groups_file_sha256']
assert sha(C['canonical_ledger'])==d['budget']['ledger_sha256'],'root refresh budget/preflight after any ledger change'
print(json.dumps(dict(source_protection_preflight_ready=True,preflight=str(p),preflight_sha256=sha(p),GPU_admission=False,root_live_usage_hardware_reservation_and_submission_still_required=True),indent=2))
