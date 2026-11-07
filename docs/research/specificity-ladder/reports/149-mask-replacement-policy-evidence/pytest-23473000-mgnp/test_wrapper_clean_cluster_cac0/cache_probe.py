import json, os
from transformers.utils.hub import cached_file
model='meta-llama/Llama-3.1-8B-Instruct'
revision='0e9e39f249a16976918f6564b8830bc894c89659'
assert os.environ['HF_HOME']==os.environ['DC_HF_HOME']
assert os.environ['HF_HUB_CACHE']==os.environ['DC_HF_HOME']
assert os.environ['DC_CLUSTER']=='delta'
assert all(os.environ[k]=='1' for k in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_DATASETS_OFFLINE'))
assert os.path.isfile(os.environ['SPECIFICITY_A3_MASK_LAUNCH_EXECUTABLE'])
paths={name:cached_file(model,name,revision=revision,local_files_only=True) for name in ('config.json','model.safetensors.index.json')}
from pathlib import Path
index=json.loads(Path(paths['model.safetensors.index.json']).read_text())
assert all((Path(paths['model.safetensors.index.json']).parent/name).is_file() for name in set(index['weight_map'].values()))
print(json.dumps(dict(cache=os.environ['HF_HUB_CACHE'],metadata=paths,weights_loaded=False)))
