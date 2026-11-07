"""Accepted predecessor per-start cache gate; only metadata are byte-hashed.
No model, downloader or full-weight read. Standard-library Python3.6-compatible.
"""
from pathlib import Path
import hashlib,json,time
REFERENCE_SHA="6d4caf626770067c20ce372a197ec402e7242ab745fad8e3b338dead1a071fbf"
FULL_PROOF_SHA="b28e3897ffc3bda9db3ad4bbaf5a38a5c3ed664b301983eae133c08536461fee"
REVISION="0e9e39f249a16976918f6564b8830bc894c89659"
MODEL_REPO="models--meta-llama--Llama-3.1-8B-Instruct"
def file_sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def check_cache(reference_path,full_proof_path,physical_hub,reference_sha256=REFERENCE_SHA,full_proof_sha256=FULL_PROOF_SHA):
 reference=Path(reference_path);full=Path(full_proof_path)
 assert file_sha(reference)==reference_sha256 and file_sha(full)==full_proof_sha256,'immutable cache proof/reference drift'
 original=json.loads(full.read_text());ref=json.loads(reference.read_text());assert original['reference_sha256']==reference_sha256
 cache=Path(ref['remote_cache']);assert cache==Path(physical_hub)/MODEL_REPO,'actual physical HF bind differs'
 assert ref['revision']==REVISION and (cache/'refs/main').read_text().strip()==REVISION,'cached revision changed'
 snapshot=cache/'snapshots'/REVISION;metadata=[];weights=[]
 for row in ref['metadata']:
  path=snapshot/row['name'];assert path.stat().st_size==row['nbytes'];digest=file_sha(path);assert digest==row['sha256'],'cached metadata bytes changed'
  metadata.append(dict(name=row['name'],nbytes=path.stat().st_size,sha256=digest))
 for row in ref['weights']:
  path=snapshot/row['name'];assert path.stat().st_size==row['nbytes'] and path.resolve().name==row['expected_sha256'],'weight size/content-addressed target changed'
  weights.append(dict(name=row['name'],nbytes=path.stat().st_size,resolved_blob_name=path.resolve().name,expected_sha256=row['expected_sha256']))
 return dict(kind='actual_predecessor_per_start_cache_check',revision=REVISION,physical_cache=str(cache),checked_at_unix=time.time(),reference_sha256=reference_sha256,original_full_weight_proof_sha256=full_proof_sha256,metadata=metadata,weights=weights,full_weights_rehashed=False,model_loaded=False)
