"""Observational compute-node comparison; caches and nodes not controlled."""
import json,pathlib,statistics,os
from job_common import CFG,O,C,sha,write
base=pathlib.Path(CFG['baseline_cpu_root']);result={}
for owner in ('mask','edge'):
    old_path=base/('source-cost-'+owner+'.json');assert sha(old_path)==CFG['baseline_cpu_sha256'][owner]
    old=json.loads(old_path.read_text());new_path=O/'evidence'/('source-cost-'+owner+'.json');new=json.loads(new_path.read_text())
    assert str(old['job_id'])==CFG['baseline_job'] and old['commit']=='f5a5687ec12091f0d148b38b301598e9c7cb98cd' and new['commit']==C
    assert old['model_loaded'] is False and new['model_loaded'] is False
    result[owner]=dict(baseline_path=str(old_path),baseline_sha256=sha(old_path),baseline_job_id=old['job_id'],successor_path=str(new_path),successor_sha256=sha(new_path),successor_job_id=new['job_id'],baseline_cold=old['cold'],successor_cold=new['cold'],baseline_refreshes=old['refreshes'],successor_refreshes=new['refreshes'],baseline_mean_wall=statistics.mean(row['wall_seconds'] for row in old['refreshes']),successor_mean_wall=statistics.mean(row['wall_seconds'] for row in new['refreshes']),baseline_source_stats=old['source_stats_after'],successor_source_stats=new['source_stats_after'],baseline_cpu_model=old['cpu_model'],successor_cpu_model=new['cpu_model'],same_science_validated_in_preparation=True,source_sizes_may_differ=True,cache_controlled=False,causal_speedup_claim=False)
write(O/'evidence/compute-comparison.json',dict(comparison=result,job_id=os.environ['SLURM_JOB_ID'],execution_authorized=False,model_loaded=False,source_only=True))
