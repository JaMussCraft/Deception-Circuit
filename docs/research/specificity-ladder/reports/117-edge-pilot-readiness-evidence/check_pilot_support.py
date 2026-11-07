import json,pathlib,sys,hashlib
W=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');B=W/'outputs/_analyses/specificity-ladder/a3-edge-runtime-87fceb28b3b4/runtime';O=W/'outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4';E=W/'docs/research/specificity-ladder/reports/117-edge-pilot-readiness-evidence';sys.path.insert(0,str(B))
receipt=json.loads((O/'evidence/publication-receipt.json').read_text());raw=(O/'canonical/design.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==receipt['canonical_design_sha256'];d=json.loads(raw)['payload'];del raw
raw=(O/'edge/prepared/payload.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==receipt['prepared_reference']['files']['payload.json']['sha256'];p=json.loads(raw);del raw
from component_analysis import a3_edge_pipeline as edge
result={}
for task,g in p['graphs'].items():
 result[task]={}
 for condition in ('D','I'):
  pairs=[]
  for rid in d['tasks'][task]['selection_ids'][:8]:
   for stream in ('clean','corrupt'):
    pair=edge.source_pair(d,task,'validation',rid,condition,stream,purpose='attribution');supported,missing=edge.supported_edges(pair,g['edges'])
    pairs.append(dict(instance_id=rid,stream=stream,supported=len(supported),missing=len(missing),missing_bins=sorted({e['position'] for e in missing})))
  result[task][condition]=dict(pairs=pairs,pair_count=len(pairs),any_missing=any(x['missing'] for x in pairs),missing_edge_occurrences=sum(x['missing'] for x in pairs))
output=dict(kind='model_free_original_pilot_source_support',source_commit='87fceb28b3b46f4a406c0280db785697a0bbd3fc',tasks=result,any_missing=any(c['any_missing'] for t in result.values() for c in t.values()),weights_loaded=False,execution_authorized=False)
(E/'pilot-source-support.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({'any_missing':output['any_missing'],'summary':{t:{c:{k:v for k,v in x.items() if k!='pairs'} for c,x in rs.items()} for t,rs in result.items()}},indent=2))
