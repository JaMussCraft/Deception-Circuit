import json, hashlib, math
from pathlib import Path
from datasets import load_from_disk
R=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder')
B=R/'outputs/_analyses/specificity-ladder'
H=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
FH=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
J=lambda p:json.loads(p.read_text())
L=lambda p:[json.loads(s) for s in p.read_text().splitlines()]
pool=J(R/'dataset/user_inversion_requests_v2.json')
commit='dd9aed69d115e87f8942c4a622f993f5996d7b77'
rev='0e9e39f249a16976918f6564b8830bc894c89659'
result={}; timing=0
for task in ['far_v2','sdr_v2','ser_v2']:
 p=B/'a1-pilot-dd9aed6'/task/'test'; d=B/'a1-derive-dd9aed6'/task/'test'
 m=J(p/'run_manifest.json'); dm=J(d/'derivation_manifest.json'); rows=L(p/'scores.jsonl'); pairs=L(d/'pairs.jsonl'); rep=L(p/'baseline_repeat.jsonl')
 assert m['source_commit']==commit and m['model_revision']==m['tokenizer_revision']==rev
 assert len(rows)==32 and len(rep)==64 and len(pairs)==1000
 assert m['ids']==[r['instance_id'] for r in rows]==[r['instance_id'] for r in pairs[:32]]
 assert len(set(m['ids']))==32
 for fn,h in m['files'].items(): assert FH(p/fn)==h
 assert FH(d/'derivation_manifest.json')==m['derivation_manifest_sha256']
 for fn,h in dm['files'].items(): assert FH(d/fn)==h
 assert H(pool)==m['request_pool_hash']==dm['request_pool_hash']
 assert m['source_hashes']==dm['source_hashes']
 src={}
 for arm,suf in [('D',''),('H','_honest')]:
  ds=load_from_disk(str(R/'data/datasets'/(task+suf)))
  assert H(J(R/'data/datasets'/(task+suf)/'dataset_config.json'))==m['source_hashes'][arm]['config']
  src[arm]={}
  for split in ['train','validation','test']:
   rr=list(ds[split]); assert H(rr)==m['source_hashes'][arm][split]
   src[arm][split]={x['instance_id']:x for x in rr}
 for pair in pairs:
  assert pair['source_row_hashes']=={arm:H(src[arm]['test'][pair['instance_id']]) for arm in ['D','H']}
 def ph(pp):return H([{arm:{s:H(pair[arm][s+'_prompt']) for s in ['clean','corrupt']} for arm in ['inversion','baseline']} for pair in pp])
 assert ph(pairs)==dm['prompt_hash'] and ph(pairs[:32])==m['prompt_hash']
 for row,pair in zip(rows,pairs):
  for arm in ['inversion','baseline']:
   for s in ['clean','corrupt']:
    score=row[arm][s]; assert score['prompt_hash']==H(pair[arm][s+'_prompt'])
    assert math.isfinite(score['margin']) and score['margin']==score['logit_a']-score['logit_b']==score['honest_minus_opposite']==-score['opposite_minus_honest']
    if score['choice']=='a':assert score['argmax']==score['expected_honest_token']
    if score['choice']=='b':assert score['argmax']==score['expected_opposite_token']
 for path,h in m['registry_sha256'].items():
  assert FH(Path(path))==h and J(Path(path))=={'schema':1,'sets':[]}
 snap=Path(m['model_snapshot']); assert snap.name==rev
 assert FH(Path(m['tokenizer_loading']['resolved_snapshot'])/'tokenizer_config.json')==m['tokenizer_loading']['tokenizer_config_sha256']
 idx=J(snap/'model.safetensors.index.json'); assert all((snap/f).is_file() for f in set(idx['weight_map'].values()))
 original=[r['baseline'][s] for r in rows for s in ['clean','corrupt']]
 assert all(all(a[k]==b[k] for k in ['argmax','argmax_id','choice','margin','logit_a','logit_b']) for a,b in zip(original,rep))
 def competent(r):return all(r['baseline'][s]['choice']=='a' and r['baseline'][s]['margin']>=.3 for s in ['clean','corrupt'])
 metrics={'hashes_source_prompt_registry_revision':'all pass','baseline_replay_exact':len(rep),'score_sha256':FH(p/'scores.jsonl'),'repeat_sha256':FH(p/'baseline_repeat.jsonl'),'neutral_both_honest':sum(all(r['baseline'][s]['choice']=='a' for s in ['clean','corrupt']) for r in rows),'neutral_competent':sum(map(competent,rows))}
 for threshold in [.7,.5]:
  kept=[r for r in rows if all(r['inversion'][s]['choice']=='b' and -r['inversion'][s]['margin']>=threshold for s in ['clean','corrupt'])]
  metrics[str(threshold)]={'retained':len(kept),'retained_competent':sum(map(competent,kept))}
 for arm in ['inversion','baseline']:
  metrics[arm]={s:{'honest':sum(r[arm][s]['choice']=='a' for r in rows),'opposite':sum(r[arm][s]['choice']=='b' for r in rows),'other':sum(r[arm][s]['choice'] not in ['a','b'] for r in rows),'mean_honest_minus_opposite':sum(r[arm][s]['margin'] for r in rows)/32} for s in ['clean','corrupt']}
 metrics['seconds']=m['seconds'];timing+=m['seconds'];result[task]=metrics
result['timing']={'pilot_scoring_including_replays_seconds':timing,'fixed_95_minus_scoring_seconds':95-timing,'full_primary_forward_equivalent_seconds':timing*(4200*4)/(96*6),'full_total_with_fixed_seconds':95-timing+timing*(4200*4)/(96*6),'allocated_gib':17407058944/2**30,'reserved_gib':17758683136/2**30}
print(json.dumps(result,indent=2))
Path('/tmp/a1-independent-audit-result.json').write_text(json.dumps(result,indent=2))
