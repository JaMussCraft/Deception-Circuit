import os,sys,json,pathlib,hashlib,datetime,time
from types import SimpleNamespace
from transformers import AutoTokenizer
from huggingface_hub import hf_hub_download
from dataset import user_inversion_pipeline as common
from component_analysis import a3_pipeline
start=time.time()
w=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder')
parent_path=w/'outputs/_analyses/specificity-ladder/ladder-5f450dc/design.json'
p=json.loads(parent_path.read_text())['payload']
args=SimpleNamespace(model=p['model'],tokenizer_revision=p['tokenizer_revision'])
snapshot=pathlib.Path(hf_hub_download(args.model,'tokenizer_config.json',revision=args.tokenizer_revision,local_files_only=True)).parent
raw=AutoTokenizer.from_pretrained(str(snapshot),revision=args.tokenizer_revision,local_files_only=True)
canonical=common.load_tokenizer(args)
assert raw.pad_token is None and canonical.pad_token==canonical.eos_token
assert common.tokenizer_identity(canonical,args.tokenizer_revision)==p['tokenizer_identity']
assert a3_pipeline._validated_prepare_tokenizer(canonical,p) is not canonical
checks=[]
for task,conditions in p['rows'].items():
 for condition in ('D','H','F','I','user_neutral'):
  if not conditions.get(condition):continue
  row=conditions[condition][0]
  for stream,s in row['streams'].items():
   actual=canonical.encode(s['prompt'],add_special_tokens=False)
   original=raw.encode(s['prompt'],add_special_tokens=False)
   assert actual==original==s['tokens']
   checks.append(dict(task=task,condition=condition,stream=stream,instance_id=row['instance_id'],token_count=len(actual),prompt_sha256=hashlib.sha256(s['prompt'].encode()).hexdigest()))
try:a3_pipeline._validated_prepare_tokenizer(raw,p)
except ValueError as error:rejected=str(error)
else:raise AssertionError('unmodified raw tokenizer unexpectedly accepted')
assert rejected=='production tokenizer configuration differs from pinned standard'
canonical.padding_side='left' if canonical.padding_side=='right' else 'right'
try:a3_pipeline._validated_prepare_tokenizer(canonical,p)
except ValueError as error:negative=str(error)
else:raise AssertionError('changed padding side unexpectedly accepted')
assert negative==rejected
print(json.dumps(dict(python=sys.executable,model=args.model,revision=args.tokenizer_revision,canonical_identity=p['tokenizer_identity'],snapshot=str(snapshot),loading=common.tokenizer_loading(canonical),raw_pad_token=raw.pad_token,canonical_pad_token=canonical.pad_token,source_prompt_checks=checks,source_prompt_check_count=len(checks),raw_rejection=rejected,negative_rejection=negative,elapsed_seconds=time.time()-start),indent=2))
