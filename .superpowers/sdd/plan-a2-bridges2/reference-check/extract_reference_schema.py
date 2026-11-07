"""Read saved H200 JSON/logs only; no framework/model imports or modifications."""
from pathlib import Path
import hashlib,json,math
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def compact_eval(value,ids):
 rows=value['outputs'];assert [r['instance_id'] for r in rows]==ids and len(set(ids))==len(ids)
 assert all(all(math.isfinite(r[k]) for k in ('logit_target','logit_distractor','logit_difference')) for r in rows)
 assert all(r['logit_difference']==r['logit_target']-r['logit_distractor'] for r in rows)
 assert value['accuracy']==sum(r['logit_difference']>0 for r in rows)/len(rows)
 assert value['logit_diff']==sum(r['logit_difference'] for r in rows)/len(rows)
 return dict(metrics={k:v for k,v in value.items() if k!='outputs'},rows=len(rows),unique_ids=len(set(ids)),exact_receipt_id_order=True,row_fields=sorted({k for r in rows for k in r}),first_row=rows[0],last_row=rows[-1],margin_min=min(r['logit_difference'] for r in rows),margin_max=max(r['logit_difference'] for r in rows),nonpositive_margins=sum(r['logit_difference']<=0 for r in rows),aggregate_accuracy_and_margin_reconciled=True)
references={}
for arm in ('D','I'):
 receipt_path=ROOT/f'outputs/_analyses/specificity-ladder/a2-timing-6bd8bf5-h200/sdr_v2-{arm}-seed42.json';receipt=json.loads(receipt_path.read_text());artifacts={};native={}
 for name,relative in receipt['artifacts'].items():
  p=ROOT/relative;assert sha(p)==receipt['artifact_sha256'][name]
  artifacts[name]=dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p),receipt_sha256_matches=True);native[name]=json.loads(p.read_text())
 result=native['results.json'];history=native['history.json']['node'];active=native['active_nodes.json'];manifest=native['run_manifest.json']
 assert history['epochs']==list(range(1,21)) and [r['epoch'] for r in history['evals']]==[0,10,20]
 assert all(len(history[k])==20 and all(math.isfinite(x) for x in history[k]) for k in ('loss','kl','task','sparsity','lr'))
 masks=active['masks'];assert set(masks)=={'attention_heads','mlp_blocks'} and len(masks['attention_heads'])==32 and len(masks['mlp_blocks'])==32
 assert all(len(row)==32 and set(row)<={0,1} for row in masks['attention_heads'].values()) and set(masks['mlp_blocks'])<={0,1}
 assert sum(map(sum,masks['attention_heads'].values()))==sum(map(len,active['active_heads'].values()))
 assert sum(masks['mlp_blocks'])==len(active['active_mlps'])
 source={p:dict(expected=h,actual=sha(ROOT/p)) for p,h in receipt['source_hashes'].items()};assert all(x['expected']==x['actual'] for x in source.values())
 dataset_checks={p:sha(Path(p))==h for p,h in manifest['dataset_files'].items()};assert all(dataset_checks.values())
 selected={k:dict(count=len(ids),ordered_ids_sha256=hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()) for k,ids in receipt['selected_ids'].items()}
 log_paths=[ROOT/receipt['stdout_stderr_log'],ROOT/receipt['output_dir']/'train.log'];logs={str(p):dict(sha256=sha(p),bytes=p.stat().st_size,timing_lines=[line for line in p.read_text().splitlines() if 'pruning time:' in line or 'Peak GPU memory' in line]) for p in log_paths}
 references[arm]=dict(receipt=dict(path=str(receipt_path),sha256=sha(receipt_path),status=receipt['status'],execution_commit=receipt['execution_commit'],build_source_commit=receipt['source_commit'],purpose=receipt['purpose'],actual_epochs=receipt['actual_epochs'],planned_epochs=receipt['planned_epochs'],seed=receipt['seed'],counts=receipt['counts'],frozen_config_sha256=receipt['frozen_config_sha256'],resolved_config_sha256=receipt['resolved_config_sha256'],timing={k:receipt[k] for k in ('total_seconds','pruning_seconds','peak_memory_gb')},gpu_devices=receipt['gpu_devices']),artifacts=artifacts,source_hashes=source,selected_id_digests=selected,dataset_file_hash_matches=dataset_checks,config=native['config.json'],run_manifest=manifest,results={k:compact_eval(result[k],receipt['selected_ids']['test']) for k in ('baseline','node_eval')},edge_eval=result['edge_eval'],node_granularity=result['node_granularity'],history=dict(keys=list(history),trajectory={k:history[k] for k in ('epochs','loss','kl','task','sparsity','lr')},evals=[compact_eval(e,receipt['selected_ids']['validation']) for e in history['evals']]),mask=dict(keys=list(masks),binary=True,head_shape=[32,32],mlp_shape=[32],active_heads=sum(map(len,active['active_heads'].values())),active_mlps=len(active['active_mlps']),soft_gates_saved=False),native_directory_files=sorted(str(p.relative_to(ROOT/receipt['output_dir'])) for p in (ROOT/receipt['output_dir']).rglob('*') if p.is_file()),logs=logs)
record=dict(kind='read_only_h200_reference_schema',references=references,available=['selected target/distractor logits and difference, decoded full-vocabulary argmax per evaluation row','baseline and pruned test aggregates','initialized and trained validation evaluations','all20 epoch mean loss/KL/task/sparsity/LR','final full binary head/MLP masks','timing/memory receipts and source/config/dataset/model/runtime identities'],unavailable=['full-vocabulary logit arrays/probabilities, hidden activations','raw argmax token IDs and per-row KL','legacy tokenized input/attention-mask/readout-position arrays in results','soft gates/gradients/optimizer/RNG checkpoints','H100 forward of the identical saved H200 final mask in the proposed retraining pilot'],schema_source_hashes={p:sha(ROOT/p) for p in ('train.py','pruning.py','dataset/deception_common.py','analysis.py','models/__init__.py','evaluation/sanity.py')},no_model_or_framework_import=True,no_forward=True,no_source_or_input_rewrite=True)
launch=ROOT/'outputs/_analyses/specificity-ladder/a2-timing-h200-config.json'
launch_expected={arm:json.loads((ROOT/f'outputs/_analyses/specificity-ladder/a2-timing-6bd8bf5-h200/sdr_v2-{arm}-seed42.json').read_text())['config_file_sha256'] for arm in ('D','I')}
assert set(launch_expected.values())=={sha(launch)}
build=ROOT/'outputs/_analyses/specificity-ladder/a2-matched-77b6487-m07/build_manifest.json'
assert all(sha(build)==json.loads((ROOT/f'outputs/_analyses/specificity-ladder/a2-timing-6bd8bf5-h200/sdr_v2-{arm}-seed42.json').read_text())['build_manifest_file_sha256'] for arm in ('D','I'))
record['launch_references']=dict(original_outer_config=dict(path=str(launch),sha256=sha(launch),receipt_hashes_match=True,config=json.loads(launch.read_text())),original_build_manifest=dict(path=str(build),sha256=sha(build),receipt_hashes_match=True),current_W_default=dict(path='scripts/jobs/specificity_ladder_a2.json',sha256=sha(ROOT/'scripts/jobs/specificity_ladder_a2.json'),is_not_legacy_outer_config=True),deployment_statement_from_root='Exact accepted6bd application/archive and byte-identical original timing-H200 outer config; no current W executable/default config deployed; original paths preserved by namespace')
(OUT/'reference-schema.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(arms=list(references),native_artifact_hash_matches=10,recorded_source_hashes_match=True,dataset_hashes_match=True,all_row_order_and_aggregate_checks=True,output=str(OUT/'reference-schema.json'))))
