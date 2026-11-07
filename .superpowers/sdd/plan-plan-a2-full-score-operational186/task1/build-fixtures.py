"""One-time fixture extraction. Does not mutate/admit authentic artifacts."""
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder')
R5 = W / '.superpowers/sdd/plan-a2-bridges-assay/h100-g3-20261103/h100-timing-launch-r5'
MAIN = W / 'outputs/_analyses/specificity-ladder/a2-analysis/bridges-h100-G3-v1'
def write(name, x):
    (HERE / 'fixtures' / name).write_text(json.dumps(x, sort_keys=True, indent=2) + '\n')
def content(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

old = json.loads((R5 / 'config.template.json').read_text())
wrapped = json.loads((MAIN / 'bank/banks.json').read_text())
bank = copy.deepcopy(wrapped['payload'])
# All real bank task contract/provenance fields remain. Only value vectors are
# removed; this is explicitly a metadata/controller fixture, never native proof.
for item in bank['banks'].values():
    item['values'] = []
digest = content(bank)
write('banks.json', {'payload': bank, 'sha256': digest})
manifest = json.loads((MAIN / 'bank/run_manifest.json').read_text())
manifest['payload_sha256'] = digest
write('run_manifest.json', manifest)
write('historical-config.template.json', old)
retain = ['worktree', 'runtime', 'commit', 'a1_design', 'a1_selected', 'registry', 'main_root',
          'snapshot_sha256', 'source_plan', 'source_plan_sha256', 'python', 'dtype',
          'attention_backend', 'minimum_gpu_total_bytes', 'minimum_gpu_free_bytes',
          'canonical_ledger', 'experiment_limits', 'global_limit', 'expected_account',
          'allowed_partitions', 'expected_qos', 'image_sha256', 'physical_Alignment_root',
          'virtual_Alignment_root', 'physical_HF_cache', 'virtual_HF_cache', 'minimum_registry_paths',
          'maximum_allocation_capture_age_seconds']
c = {key: old[key] for key in retain}
c.update(phase='full_score', full_scoring_admitted=True, actual_job_id='T1-FIXTURE-JOB',
         reservation_id='T1-FIXTURE-RESERVATION', expected_score_rows=59652, expected_controls=3396,
         bank_internal_payload_sha256=digest, bank_gpu_uuid='GPU-old-bank-job',
         bank_numeric_environment=bank['banks']['far_v2']['contract']['numeric_environment'],
         release_max_age_seconds=300, trigger_max_age_seconds=15,
         resources={'duration_seconds': 7200, 'CPUs': 2, 'RAM_bytes': 34359738368, 'GPU_count': 1,
                    'minimum_entry_seconds': 600, 'finish_margin_seconds': 120, 'child_cap_seconds': 6600},
         resource_review_accepted=True,
         placement_sha256='1' * 64, groups_receipt_sha256=manifest['group_receipt_sha256'],
         launch_packet_manifest_sha256='3' * 64,
         scope='one original full score CLI; no bank/pilot/summary/retry')
write('config.json', c)
write('provenance.json', {
    'fixture_only': True, 'native_validation_authority': False,
    'reduction': 'Complete task contracts/provenance retained; all bank values replaced with empty lists. Controller metadata tests only.',
    'numeric_versions_observed_not_spoofed': c['bank_numeric_environment'],
    'sources': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                [R5 / 'config.template.json', MAIN / 'bank/banks.json', MAIN / 'bank/run_manifest.json']},
})
