from pathlib import Path
import json,hashlib,time,datetime
P=Path('/ocean/projects/cis260361p/swong2/specificity-ladder-20261102');ref=json.loads((P/'deployment/model-cache-reference.json').read_text());cache=Path(ref['remote_cache']);revision=(cache/'refs/main').read_text().strip();assert revision==ref['revision'];snap=cache/'snapshots'/revision
start=time.time();checked=[]
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for data in iter(lambda:f.read(8*1024*1024),b''):h.update(data)
 return h.hexdigest()
for item in ref['metadata']+ref['weights']:
 path=snap/item['name'];actual=sha(path);expected=item.get('sha256') or item['expected_sha256'];assert path.stat().st_size==item['nbytes'] and actual==expected,item['name'];checked.append(dict(name=item['name'],sha256=actual,nbytes=path.stat().st_size));print(json.dumps(checked[-1]),flush=True)
result=dict(kind='a2_bridges2_exact_model_cache_check_v1',revision=revision,reference_sha256=sha(P/'deployment/model-cache-reference.json'),files=checked,elapsed_seconds=time.time()-start,checked_at=datetime.datetime.utcnow().isoformat()+'Z',model_loaded=False)
(P/'deployment/model-cache-check.json').write_text(json.dumps(result,indent=2)+'\n');print('MODEL_CACHE_BYTES_PASS',flush=True)
