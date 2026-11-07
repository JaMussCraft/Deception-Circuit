"""Compare raw/canonical/launcher config identities and saved Arrow rows; no model."""
from pathlib import Path
import hashlib,importlib.util,json,tarfile
import pyarrow.ipc as ipc
W=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
runtime=W/'outputs/_analyses/specificity-ladder/a2-runtime-6bd8bf5/runtime'
module_path=runtime/'scripts/twin_training.py';spec=importlib.util.spec_from_file_location('frozen_twin_training_reference',module_path);frozen=importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
config_path=W/'outputs/_analyses/specificity-ladder/a2-timing-h200-config.json';build_path=W/'outputs/_analyses/specificity-ladder/a2-matched-77b6487-m07/build_manifest.json';transfer_path=W/'outputs/_analyses/specificity-ladder/a2-bridges2-20261102/transfer-manifest.json'
config=json.loads(config_path.read_text());resolved=json.loads(config_path.read_text());resolved.setdefault('data_root',str(build_path.resolve().parent));build=json.loads(build_path.read_text());transfer=json.loads(transfer_path.read_text());slots={x['virtual_path']:x for x in transfer['files']}
def slot(p):
 row=slots[str(p)];assert row['sha256']==sha(p) and row['nbytes']==p.stat().st_size
 return row
summary=dict(kind='read_only_H200_deployment_provenance_reconciliation',digest_function_source=dict(path=str(module_path),sha256=sha(module_path),definition='SHA256(json.dumps(value, sort_keys=True, separators=(comma,colon)).encode())'),transfer_manifest=dict(path=str(transfer_path),sha256=sha(transfer_path),file_count=len(transfer['files'])),build=dict(path=str(build_path),raw_file_sha256=sha(build_path),canonical_JSON_sha256=frozen.digest(build),build_hash=build['build_hash'],transfer_row=slot(build_path)),config=dict(path=str(config_path),raw_file_sha256=sha(config_path),canonical_input_JSON_sha256=frozen.digest(config),launcher_added_fields={'data_root':resolved['data_root']},launcher_resolved_canonical_JSON_sha256=frozen.digest(resolved),transfer_row=slot(config_path),raw_config=config),arms={})
for arm in ('D','I'):
 receipt_path=W/f'outputs/_analyses/specificity-ladder/a2-timing-6bd8bf5-h200/sdr_v2-{arm}-seed42.json';receipt=json.loads(receipt_path.read_text());native=json.loads((W/receipt['artifacts']['run_manifest.json']).read_text());native_config=json.loads((W/receipt['artifacts']['config.json']).read_text())
 assert sha(config_path)==receipt['config_file_sha256'] and frozen.digest(resolved)==receipt['frozen_config_sha256']
 assert sha(build_path)==receipt['build_manifest_file_sha256'] and frozen.digest(build)==receipt['build_manifest_sha256'] and build['build_hash']==receipt['build_hash']
 source_checks={rel:sha(runtime/rel)==value for rel,value in receipt['source_hashes'].items()};assert all(source_checks.values())
 legacy_argv=receipt['argv'];assert frozen.digest(frozen.expected_config(legacy_argv))==receipt['resolved_config_sha256']
 command=frozen.build_command(resolved,build,task='sdr_v2',condition=arm,seed=42,timing_epochs=20)
 assert command[2:]==legacy_argv[2:] and frozen.digest(frozen.expected_config(command))==receipt['resolved_config_sha256']
 private_path=build_path.parent/arm/'sdr_v2/dataset_config.json';private=json.loads(private_path.read_text());splits={}
 file_checks={}
 for name,expected in native['dataset_files'].items():
  p=Path(name);assert sha(p)==expected;file_checks[name]=dict(native_H200_sha256_matches=True,transfer_row=slot(p))
 for split,expected_ids in receipt['selected_ids'].items():
  arrow=build_path.parent/arm/'sdr_v2'/split/'data-00000-of-00001.arrow'
  with arrow.open('rb') as stream:rows=ipc.open_stream(stream).read_all().to_pylist()
  assert [row['instance_id'] for row in rows]==expected_ids==private['split_ids'][split]==build['tasks']['sdr_v2']['split_ids'][split]
  for row in rows:
   proof=private['token_proofs'][split][row['instance_id']];assert row['token_proof']==proof
   assert frozen._canonical(row['clean_prompt'])==proof['recipient_prompt_hash'] and frozen._canonical(row['corrupt_prompt'])==proof['reference_prompt_hash']
   assert row['corrupt_prompt']==proof['reference_prompt'] and proof['readout']==proof['token_length']-1
   assert row['target']==row['source_recipient']['target'] and row['distractor']==row['source_recipient']['distractor']
   assert row['label_semantics']['reference_labels_used_for_loss'] is False
  splits[split]=dict(rows=len(rows),ordered_receipt_and_build_and_private_ids_equal=True,ordered_rows_sha256=frozen._canonical(rows),ordered_prompts_labels_proofs_sha256=frozen._canonical([{k:row[k] for k in ('instance_id','clean_prompt','corrupt_prompt','target','distractor','token_proof','label_semantics')} for row in rows]),all_prompt_hashes_readouts_labels_and_proofs_match=True,raw_arrow_matches_original_H200_native_manifest=True,raw_arrow_matches_transfer_manifest=True,full_runtime_token_ID_arrays_stored=False)
 summary['arms'][arm]=dict(receipt_path=str(receipt_path),receipt_sha256=sha(receipt_path),original_native_config_path=str(W/receipt['artifacts']['config.json']),original_native_config_sha256=sha(W/receipt['artifacts']['config.json']),original_native_config=native_config,receipt_frozen_digest_matches_resolved_input=True,receipt_raw_input_file_hashes_match=True,exact_training_args_argv2_equal=True,original_script_path=legacy_argv[1],frozen_script_path=command[1],frozen_script_same_original_train_bytes=sha(Path(command[1]))==receipt['source_hashes']['train.py'],expected_config_digest=frozen.digest(frozen.expected_config(command)),frozen_source_hash_checks=source_checks,dataset_files=file_checks,splits=splits,tokenizer_provenance=private['a1_scoring']['receipt']['tokenizer_loading'])
archive=W/'outputs/_analyses/specificity-ladder/a2-runtime-6bd8bf5/application.tar'
with tarfile.open(archive) as tf:
 name=next(n for n in tf.getnames() if n.endswith('scripts/jobs/specificity_ladder_a2.json'));raw=tf.extractfile(name).read();archived=json.loads(raw)
summary['archived_default_config']=dict(archive_path=str(archive),member=name,raw_file_sha256=hashlib.sha256(raw).hexdigest(),config=archived,diff_from_original_launch={k:dict(archived=archived.get(k),H200_launch=config.get(k)) for k in sorted(set(archived)|set(config)) if archived.get(k)!=config.get(k)})
summary['conclusion']=dict(no_build_metadata_difference=True,no_transferred_original_launch_config_difference=True,no_row_cohort_label_or_hyperparameter_difference=True,actual_legacy_runtime_token_arrays_not_saved=True,tokenization_equivalence='Same exact original Arrow/prompt/label bytes, stored tokenizer identity, frozen loader/tokenization code and admitted same tokenizer snapshot are required; stored prompt token proofs agree, but this read-only check does not invent legacy runtime token arrays or a newly executed H100 input equality observation.',operational_changes=['Authenticated frozen train.py execution path instead of old W/train.py','New private remote physical output root/host/job/time; original virtual data paths preserved'],same_schedule='Actual20 epoch cosine T_max20; planned500 remains provenance only')
(OUT/'provenance-reconciliation.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(dict(build=summary['build'],config={k:v for k,v in summary['config'].items() if k not in ('raw_config','transfer_row')},archive_config_diff=summary['archived_default_config']['diff_from_original_launch'],arms={k:dict(rows={s:x['rows'] for s,x in v['splits'].items()},exact_args=v['exact_training_args_argv2_equal'],source=v['frozen_source_hash_checks']) for k,v in summary['arms'].items()},all_assertions_pass=True),indent=2))
