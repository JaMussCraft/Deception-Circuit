"""Early read-only cache/container evidence, NOT final source/data admission."""
import os,json,hashlib,sys,importlib.metadata
from pathlib import Path
from huggingface_hub import hf_hub_download
MODEL='meta-llama/Llama-3.1-8B-Instruct';REV='0e9e39f249a16976918f6564b8830bc894c89659';ROOT=Path('/work/nvme/beto/swong2')
assert os.environ.get('HF_HUB_OFFLINE')=='1' and os.environ.get('HF_HUB_CACHE')==str(ROOT) and os.environ.get('TRANSFORMERS_CACHE')==str(ROOT)
files={}
for name in ['config.json','tokenizer_config.json','model.safetensors.index.json']:
 p=Path(hf_hub_download(MODEL,name,revision=REV,local_files_only=True));assert p.parent.name==REV and p.resolve().is_relative_to(ROOT)
 files[name]=dict(path=str(p),resolved=str(p.resolve()),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
assert files['config.json']['sha256']=='29e4c210b0d6ac178b16b2a255a568bdb23b581e50ca1ef6a6d071dd85704e6e'
print(json.dumps(dict(kind='early_Bridges_original_work_cache_probe',python=sys.executable,versions={n:importlib.metadata.version(n) for n in ['torch','transformers','nnsight','numpy']},files=files,HF_HOME=os.environ.get('HF_HOME'),HF_HUB_CACHE=os.environ['HF_HUB_CACHE'],TRANSFORMERS_CACHE=os.environ['TRANSFORMERS_CACHE'],model_loaded=False,source_admitted=False,final_source_choice_pending=True),indent=2))
