"""Actual new-source root mask settings; unchanged numeric/scientific profile."""
import os,json,pathlib
from component_analysis import a3_pipeline,ladder_pipeline as ladder,a3_direction_runtime as authority
from dataset import user_inversion_pipeline as common
w=pathlib.Path(os.environ['W']);o=pathlib.Path(os.environ['O']);c=os.environ['C'];design_path=o/'canonical/design.json'
parent,selected,evidence=a3_pipeline.load_a1_parents(w/'outputs/_analyses/specificity-ladder/ladder-5f450dc/design.json',w/'outputs/_analyses/specificity-ladder/ladder-5f450dc/selected.json')
profile={k:parent[k] for k in ('model','model_revision','tokenizer_revision')}
profile.update(dtype='bfloat16',backend='eager',hardware='H200',chunk_size=4,vocab_size=128256)
original=authority.read_object(w/'outputs/_analyses/specificity-ladder/a3-independent-pilots-74efb4d04819/mask-source-settings')
assert profile==original['numeric_profile']
settings=dict(kind='a3_mask_root_execution_bundle_v1',commit=c,design_file_sha256=common.file_hash(design_path),numeric_profile=profile,padding_policy=original['padding_policy'],execution_authorized=False,purpose='source settings only; no reservation/admission/RS authority')
authority.publish_object(o/'mask-source-settings',settings)
print(json.dumps(dict(commit=c,numeric_profile=profile,execution_authorized=False),indent=2))
