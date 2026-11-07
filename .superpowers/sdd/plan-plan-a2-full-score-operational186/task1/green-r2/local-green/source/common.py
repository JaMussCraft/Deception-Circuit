"""Full-score-only guards. Python 3.6 stdlib; no model-provider injection."""
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from decimal import Decimal

L = Path(__file__).resolve().parent
W = '/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder'
S = W + '/outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime'
MAIN = W + '/outputs/_analyses/specificity-ladder/a2-analysis/bridges-h100-G3-v1'
SOURCE = '50e947bb852613e3a270082651f2bd1b7bb0c525'
GPU_NAME = 'NVIDIA H100 80GB HBM3'
REFS = ('packet_manifest', 'snapshot', 'input_manifest', 'model_cache_proof',
        'resource_proof', 'capacity_proof', 'mapping_origin', 'operational_admission',
        'protection_proof', 'image', 'delta_G3_receipt', 'bridges_G3_receipt', 'source_plan')
RESOURCE_KEYS = frozenset(('duration_seconds', 'CPUs', 'RAM_bytes', 'GPU_count',
                           'minimum_entry_seconds', 'finish_margin_seconds', 'child_cap_seconds'))
BASE_KEYS = frozenset(('a1_design a1_selected actual_job_id allowed_partitions attention_backend '
    'bank_gpu_uuid bank_internal_payload_sha256 bank_numeric_environment canonical_ledger commit dtype '
    'expected_account expected_controls expected_qos expected_score_rows experiment_limits '
    'full_scoring_admitted global_limit groups_receipt_sha256 launch_packet_manifest_sha256 '
    'main_root maximum_allocation_capture_age_seconds minimum_gpu_free_bytes minimum_gpu_total_bytes '
    'minimum_registry_paths phase physical_Alignment_root physical_HF_cache placement_sha256 python '
    'registry release_max_age_seconds reservation_id resource_review_accepted resources runtime scope '
    'trigger_max_age_seconds virtual_Alignment_root virtual_HF_cache worktree bank_file '
    'bank_file_sha256 bank_manifest bank_manifest_sha256 groups groups_file_sha256 '
    'evidence_root release_directory').split())
KEYS = BASE_KEYS | frozenset(REFS) | frozenset(k + '_sha256' for k in REFS)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def content(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def read_pinned(path, wanted):
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == wanted and sha(path) == wanted, 'stable pinned object changed')
    return json.loads(raw.decode('utf-8'))


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def inside(path, parent):
    try:
        Path(path).resolve().relative_to(Path(parent).resolve())
        return True
    except ValueError:
        return False


def ref_file(path):
    path = Path(path)
    return path / 'COMPLETE.json' if path.is_dir() else path


def validate_config(c):
    require(type(c) is dict and set(c) == KEYS, 'closed full_score config fields')
    def nonnull(value):
        require(value is not None, 'unbound config')
        if isinstance(value, dict):
            for item in value.values(): nonnull(item)
        elif isinstance(value, list):
            for item in value: nonnull(item)
    nonnull(c)
    require(c['phase'] == 'full_score' and c['full_scoring_admitted'] is True, 'full_score-only admission')
    require(c['resource_review_accepted'] is True, 'independent resource review absent')
    require(c['commit'] == SOURCE and c['runtime'] == S and c['worktree'] == W, 'original source50e identity')
    require(c['a1_design'] == W + '/outputs/_analyses/specificity-ladder/ladder-5f450dc/design.json'
            and c['a1_selected'] == W + '/outputs/_analyses/specificity-ladder/ladder-5f450dc/selected.json'
            and c['registry'] == W + '/docs/research/held_out.json', 'original input CLI identities')
    require(c['dtype'] == 'torch.bfloat16' and c['attention_backend'] == 'sdpa', 'original numeric path')
    require(c['expected_score_rows'] == 59652 and c['expected_controls'] == 3396, 'full native domain')
    require(c['experiment_limits'] == {'A1': 25, 'A2': 60, 'A3': 40} and c['global_limit'] == 125, 'unchanged caps')
    require(c['release_max_age_seconds'] == 300 and c['trigger_max_age_seconds'] == 15
            and c['maximum_allocation_capture_age_seconds'] == 15, 'finite freshness contract')
    r = c['resources']
    require(type(r) is dict and set(r) == RESOURCE_KEYS, 'closed reviewed resource tuple')
    require(all(type(x) is int and x > 0 for x in r.values()), 'unbound/nonpositive resource')
    require(r['GPU_count'] == 1, 'exactly one GPU')
    require(r['finish_margin_seconds'] < r['minimum_entry_seconds'] <= r['child_cap_seconds']
            <= r['duration_seconds'] - r['finish_margin_seconds'], 'infeasible reviewed bounds')
    for key, value in c.items():
        if key.endswith('_sha256'):
            require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), 'unbound digest: ' + key)
    for key in REFS + ('main_root', 'bank_file', 'bank_manifest', 'groups', 'evidence_root', 'release_directory',
                       'python', 'physical_Alignment_root', 'virtual_Alignment_root', 'physical_HF_cache', 'virtual_HF_cache'):
        require(isinstance(c[key], str) and Path(c[key]).is_absolute() and '..' not in Path(c[key]).parts, 'absolute path: ' + key)
    for key in ('actual_job_id', 'reservation_id', 'expected_account', 'expected_qos', 'bank_gpu_uuid'):
        require(type(c[key]) is str and c[key] and re.fullmatch('[A-Za-z0-9_.:-]+', c[key]), 'unbound identity: ' + key)
    require(type(c['allowed_partitions']) is list and c['allowed_partitions']
            and all(type(x) is str and x for x in c['allowed_partitions']), 'partitions')
    require(len(c['minimum_registry_paths']) == len(set(c['minimum_registry_paths'])) == 4, 'four complete catalogues')
    require(c['virtual_Alignment_root'] == '/projects/beto/swong2/Alignment'
            and c['virtual_HF_cache'] == '/work/nvme/beto/swong2', 'original namespaces')
    require(not inside(c['evidence_root'], c['main_root']) and not inside(c['evidence_root'], c['runtime']), 'dedicated evidence namespace')
    require(c['minimum_gpu_total_bytes'] >= 80000000000 and c['minimum_gpu_free_bytes'] >= 68719476736, 'reviewed GPU floors')
    return c


CONFIG = Path(os.environ['A2_FULL_SCORE_BOUND_CONFIG']) if os.environ.get('A2_FULL_SCORE_BOUND_CONFIG') else None
C = None
if CONFIG:
    require(not CONFIG.is_symlink(), 'bound config symlink forbidden')
    C = read_pinned(CONFIG, os.environ.get('A2_FULL_SCORE_BOUND_CONFIG_SHA256'))


def full_score_command(c):
    return ['bash', c['runtime'] + '/scripts/jobs/specificity_a2.sh', '--design', c['a1_design'],
            '--selected', c['a1_selected'], '--commit', c['commit'], '--batch-size', '8',
            '--registry', c['registry'], '--stage', 'score', '--work-dir', c['main_root']]


def validate_score_command(c, command):
    require(command == full_score_command(c), 'only one original full-score command; no limit/alternate stage/loader')
    return command


def _bank_binding(c, allow_score=False):
    root = Path(c['main_root'])
    require(root.is_dir() and not root.is_symlink(), 'MAIN must be a real directory')
    if not allow_score:
        score = root / 'score'
        require(not score.exists() and not score.is_symlink(), 'score already exists or is symlink')
    for key, expected in [('bank_file', root / 'bank/banks.json'), ('bank_manifest', root / 'bank/run_manifest.json'), ('groups', root / 'groups.json')]:
        path = Path(c[key])
        require(path == expected and path.is_file() and not path.is_symlink()
                and not path.parent.is_symlink() and inside(path, root), 'immutable original path: ' + key)
        require(sha(path) == c['groups_file_sha256' if key == 'groups' else key + '_sha256'], 'stale pinned ' + key)
    artifact = read(c['bank_file'])
    require(set(artifact) == {'payload', 'sha256'}, 'native bank envelope')
    bank = artifact['payload']
    manifest = read(c['bank_manifest'])
    require(artifact['sha256'] == content(bank) == c['bank_internal_payload_sha256'] == manifest['payload_sha256'], 'bank internal payload identity')
    require(bank['kind'] == 'a2_h_banks' and bank.get('injected') is False
            and manifest['kind'] == 'a2_bank' and manifest['execution_commit'] == c['commit'], 'genuine native bank provenance')
    require(manifest['group_receipt_sha256'] == bank['receipt_sha256'] == c['groups_receipt_sha256'], 'bank/G3 receipt identity')
    execution = bank['execution_provenance']
    require(manifest['execution'] == execution and execution['dtype'] == c['dtype']
            and execution['device'].split(':')[0] == 'cuda' and execution['gpu_name'] == GPU_NAME, 'native bank numeric execution')
    require(set(bank['banks']) == {'far_v2', 'sdr_v2', 'ser_v2'}, 'complete bank metadata task scope')
    for task in bank['banks'].values():
        require(task['contract']['numeric_environment'] == c['bank_numeric_environment'], 'bank numeric environment changed')
    return dict(bank_file_sha256=c['bank_file_sha256'], bank_manifest_sha256=c['bank_manifest_sha256'],
                bank_internal_payload_sha256=c['bank_internal_payload_sha256'], bank_gpu_uuid=c['bank_gpu_uuid'],
                bank_execution=execution, numeric_environment=c['bank_numeric_environment'])


def verify_existing_bank(c):
    return _bank_binding(c, allow_score=False)


def validate_gpu_identity(c, probe):
    require(probe['gpu_name'] == GPU_NAME and probe['device'].split(':')[0] == 'cuda'
            and probe['dtype'] == c['dtype'] == 'torch.bfloat16', 'exact bank/scoring GPU numeric identity')
    require(probe['numeric_environment'] == c['bank_numeric_environment'], 'exact bank numeric environment')
    require(probe['total_memory_bytes'] >= c['minimum_gpu_total_bytes']
            and probe['free_memory_bytes'] >= c['minimum_gpu_free_bytes'], 'actual GPU capacity floors')
    require(probe['gpu_uuid'], 'actual GPU UUID absent')
    return dict(bank_gpu_uuid=c['bank_gpu_uuid'], actual_gpu_uuid=probe['gpu_uuid'], probe=probe)


def effective_deadlines(c, initial_end, current_end, fixed_end, now):
    values = [float(initial_end), float(current_end), float(fixed_end), float(now)]
    require(all(math.isfinite(x) for x in values), 'finite actual deadlines')
    run = min(values[:3])
    work = run - c['resources']['finish_margin_seconds']
    return dict(run_deadline=run, work_deadline=work, remaining_work_seconds=work - values[3])


def epoch(text):
    return datetime.datetime.strptime(text, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp()


def current_deadlines(c, facts):
    return effective_deadlines(c, float(os.environ['A2_FULL_SCORE_INITIAL_END_EPOCH']), epoch(facts['EndTime']),
                               float(os.environ['A2_FULL_SCORE_FIXED_END_EPOCH']), time.time())


def environment():
    return dict(os.environ, DC_CLUSTER='bridges2', DC_B2_ALLOC='cis260361p', DC_PYTHON=C['python'],
                DC_RUN_MANIFEST_GIT='0', PYTHONPATH=C['runtime'], PYTHONDONTWRITEBYTECODE='1',
                HF_HOME='/ocean/projects/cis260361p/swong2/hf', HF_HUB_CACHE='/work/nvme/beto/swong2',
                TRANSFORMERS_CACHE='/work/nvme/beto/swong2', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                HF_DATASETS_OFFLINE='1', WANDB_MODE='disabled', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                OPENBLAS_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')


def packet():
    validate_config(C)
    require(sha(CONFIG) == os.environ['A2_FULL_SCORE_BOUND_CONFIG_SHA256'], 'bound config changed')
    require(C['packet_manifest_sha256'] == C['launch_packet_manifest_sha256'], 'packet binding')
    for key in REFS:
        require(sha(ref_file(C[key])) == C[key + '_sha256'], 'pinned reference changed: ' + key)
    manifest = read(C['packet_manifest'])
    members = manifest['files']
    require(type(members) is dict and members, 'closed packet inventory')
    observed = set()
    for name, digest in members.items():
        path = Path(name)
        if not path.is_absolute():
            require('..' not in path.parts, 'unsafe packet member')
            path = Path(C['packet_manifest']).parent / path
        require(not path.is_symlink() and sha(path) == digest, 'packet member changed: ' + name)
        observed.add(path.resolve())
    require({(L / name).resolve() for name in ('launch.sh', 'host-launch.py', 'inner.sh', 'common.py',
            'controller.py', 'gpu-probe.py', 'module-probe.py', 'config.template.json')} <= observed,
            'packet must bind every executable/config member')
    return dict(packet_manifest_sha256=C['packet_manifest_sha256'], checked_unix=time.time())


def project_origins():
    result = {}
    for name, module in list(sys.modules.items()):
        path = getattr(module, '__file__', None)
        if path and name.split('.')[0] in ('component_analysis', 'models', 'dataset', 'evaluation', 'scripts', 'config'):
            require(inside(path, C['runtime']), 'project import escaped source: ' + name)
            result[name] = str(Path(path).resolve())
    return result


def source():
    require(sha(C['snapshot']) == C['snapshot_sha256'], 'source snapshot changed')
    snapshot = read(C['snapshot'])
    files, links = snapshot['source_sha256'], snapshot['input_links']
    require(snapshot['source_commit'] == SOURCE and len(files) == 511 and len(links) == 4
            and not snapshot['source_code_symlinks'] and not set(files) & set(links), 'closed511+4 export')
    root = Path(C['runtime'])
    actual_files, actual_links = set(), set()
    for item in root.rglob('*'):
        name = str(item.relative_to(root))
        if item.is_symlink(): actual_links.add(name)
        elif item.is_file(): actual_files.add(name)
    require(actual_files == set(files) and actual_links == set(links), 'source extra/missing file or alias')
    for name, digest in files.items():
        rel = Path(name)
        require(not rel.is_absolute() and '..' not in rel.parts and str(rel) == name, 'unsafe source key')
        require(inside(root / name, root) and not (root / name).is_symlink() and sha(root / name) == digest, 'source changed: ' + name)
    for name, target in links.items():
        rel = Path(name)
        require(not rel.is_absolute() and '..' not in rel.parts and str(rel) == name, 'unsafe source alias')
        path = root / name
        require(path.is_symlink() and os.readlink(str(path)) == target and path.exists()
                and path.resolve() == Path(target).resolve(), 'source alias changed')
    return dict(source_commit=SOURCE, snapshot_sha256=C['snapshot_sha256'], source_count=511,
                literal_links=4, project_module_origins=project_origins())


def input_closure():
    require(sha(C['input_manifest']) == C['input_manifest_sha256'], 'input closure changed')
    proof = read(C['input_manifest'])
    ordinary, aliases = proof['ordinary_sha256'], proof['aliases']
    require(len(ordinary) == 422 and type(aliases) is dict and aliases, 'corrected422 input closure')
    roles = proof['alias_role_proof']
    require(roles['complete'] is True and roles['expected_aliases'] == aliases
            and set(roles['roles']) == set(ordinary) | set(aliases), 'exact input alias/role coverage')
    require(not set(ordinary) & set(aliases), 'input file/alias collision')
    for name, digest in ordinary.items():
        path = Path(name)
        require(path.is_absolute() and not path.is_symlink() and sha(path) == digest, 'ordinary input changed: ' + name)
    for name, target in aliases.items():
        path = Path(name)
        require(path.is_absolute() and path.is_symlink() and os.readlink(str(path)) == target
                and path.exists(), 'literal input alias changed: ' + name)
    return dict(ordinary_count=422, aliases=len(aliases), input_manifest_sha256=C['input_manifest_sha256'])


def reviewed_admission():
    """Additive operational evidence, never a new native scientific authority kind."""
    c = C
    require(c['main_root'] == MAIN, 'actual original MAIN only')
    resource = read(c['resource_proof'])
    capacity = read(c['capacity_proof'])
    admission = read(c['operational_admission'])
    require(resource['complete'] is True and resource['independently_accepted'] is True
            and resource['resources'] == c['resources'] and resource['proof181_accepted'] is True, 'genuine independently reviewed resource/proof181 binding')
    require(set(resource['reviewed_components']) == {'host_memory', 'gpu_memory', 'storage', 'work_ratio', 'cost'}
            and all(value is True for value in resource['reviewed_components'].values()), 'full conservative resource/cost review')
    require(capacity['complete'] is True and capacity['independently_accepted'] is True
            and capacity['resources'] == c['resources'] and capacity['actual_job_id'] == c['actual_job_id'], 'actual reviewed placement/capacity')
    require(admission['accepted'] is True and admission['complete'] is True
            and admission['phase'] == 'full_score' and admission['source_commit'] == SOURCE
            and admission['actual_job_id'] == c['actual_job_id'] and admission['reservation_id'] == c['reservation_id']
            and admission['main_root'] == MAIN and admission['resources'] == c['resources'], 'new root operational admission required')
    for key in ('packet_manifest_sha256', 'groups_file_sha256', 'bank_file_sha256', 'bank_manifest_sha256',
                'input_manifest_sha256', 'model_cache_proof_sha256', 'resource_proof_sha256', 'capacity_proof_sha256'):
        require(admission[key] == c[key], 'admission identity: ' + key)
    require(admission['reader_safe_cutover_complete'] is True and admission['native_successor_complete'] is True, 'completed reader-safe native mapping transition')
    return resource


def cache():
    """Accepted predecessor algorithm: metadata bytes, weight size/blob only."""
    proof = read(C['model_cache_proof'])
    reference = proof['reference']
    original_ref = proof['original_full_proof']
    require(reference['sha256'] == '6d4caf626770067c20ce372a197ec402e7242ab745fad8e3b338dead1a071fbf'
            and original_ref['sha256'] == 'b28e3897ffc3bda9db3ad4bbaf5a38a5c3ed664b301983eae133c08536461fee', 'accepted predecessor cache identities')
    require(sha(reference['path']) == reference['sha256'] and sha(original_ref['path']) == original_ref['sha256'], 'immutable cache proof/reference drift')
    ref, original = read(reference['path']), read(original_ref['path'])
    require(original['reference_sha256'] == reference['sha256'], 'full cache proof link')
    revision = '0e9e39f249a16976918f6564b8830bc894c89659'
    model = 'models--meta-llama--Llama-3.1-8B-Instruct'
    physical = Path(C['physical_HF_cache']) / model
    require(Path(ref['remote_cache']) == physical and ref['revision'] == revision, 'actual physical cache/revision binding')
    # Under the container the SAME physical directory is mounted at /work.
    mounted = Path(C['virtual_HF_cache']) / model
    require((mounted / 'refs/main').read_text().strip() == revision, 'cached ref/main changed')
    snapshot = mounted / 'snapshots' / revision
    metadata, weights = [], []
    for row in ref['metadata']:
        path = snapshot / row['name']
        require(path.stat().st_size == row['nbytes'] and sha(path) == row['sha256'], 'cached metadata bytes changed')
        metadata.append(dict(name=row['name'], nbytes=row['nbytes'], sha256=row['sha256']))
    for row in ref['weights']:
        path = snapshot / row['name']
        require(path.stat().st_size == row['nbytes'] and path.resolve().name == row['expected_sha256'], 'weight length/content-addressed blob changed')
        weights.append(dict(name=row['name'], nbytes=row['nbytes'], resolved_blob_name=path.resolve().name))
    return dict(checked_at_unix=time.time(), revision=revision, physical_cache=str(physical),
                metadata=metadata, weights=weights, full_weights_rehashed=False, model_loaded=False)


def protection():
    proof = read(C['protection_proof'])
    require(proof['complete'] is True and proof['independently_accepted'] is True, 'owning protection closure')
    rows = proof['catalogues']
    require(len(rows) == 4 and {x['virtual_path'] for x in rows} == set(C['minimum_registry_paths']), 'four catalogue closure')
    for row in rows:
        require(sha(row['virtual_path']) == row['sha256'], 'protection catalogue changed')
    require(not proof['nonempty_heldout'] or proof['nonempty_heldout_closure_reviewed'] is True, 'nonempty heldout needs owning independent review')
    return rows


def imports():
    require(Path.cwd().resolve() == Path(C['runtime']).resolve(), 'original source cwd')
    if str(C['runtime']) not in sys.path: sys.path.insert(0, str(C['runtime']))
    from component_analysis import a2_pipeline, a3_direction_runtime
    project_origins()
    return a2_pipeline, a3_direction_runtime


def allocation(**kwargs):
    # Reuse the very same typed-resource parser on host and in the container.
    import importlib.util
    spec = importlib.util.spec_from_file_location('full_score_host_parser', str(L / 'host-launch.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_allocation(C, read(Path(C['evidence_root']) / 'allocation.json'))


def budget(release=None):
    _, ar = imports()
    identity = dict(purpose='A2 original source50e full scoring', source_commit=SOURCE,
                    groups_sha256=C['groups_file_sha256'], main_root=C['main_root'])
    normalized = ar.normalize_ledger(C['mapping_origin'], identity=identity, include_envelope=False,
                                     refresh_deadline=time.time() + 20)
    require(normalized['current_snapshot_sha256'] == sha(C['canonical_ledger']), 'current complete native ledger')
    mapping = ar.read_object(normalized['active_mapping_reference']['path'])
    ledger = read(C['canonical_ledger'])
    require(not ledger.get('legacy_totals') and mapping['ledger_path'] == C['canonical_ledger'], 'native lineage')
    require(ledger['caps']['max_concurrent_gpu_jobs'] == 99
            and Decimal(str(ledger['caps']['reserved_gpu_hours'])) == Decimal('125'), 'unchanged native ledger caps')
    entries = {row['id']: row for row in ledger['reservations']}
    require(sum(row['status'] in ('PENDING', 'RUNNING') and row['gpus'] > 0 for row in entries.values()) <= 99, 'native concurrency cap')
    require(len(entries) == len(ledger['reservations']) and len(mapping['entries']) == len(entries)
            and {r['reservation_id'] for r in mapping['entries']} == set(entries), 'full charge lineage; no omissions')
    exact = {name: Decimal('0') for name in C['experiment_limits']}
    rounded = {name: Decimal('0') for name in C['experiment_limits']}
    for item in mapping['entries']:
        row = entries[item['reservation_id']]
        seconds = Decimal(str(row['gpus'])) * Decimal(str(row['requested_minutes'])) * Decimal('60')
        require(seconds.is_finite() and seconds >= 0, 'immutable finite original charge')
        exact[item['experiment']] += seconds
        rounded[item['experiment']] += Decimal(str(item['original_reserved_gpu_hours']))
    total = sum((Decimal(str(row['reserved_gpu_hours'])) for row in entries.values()), Decimal('0'))
    require(total == Decimal(str(ledger['totals']['reserved_gpu_hours'])) and total <= Decimal('125'), 'native rounded global cap')
    require(sum(exact.values(), Decimal('0')) <= Decimal('450000'), 'exact global GPU seconds cap')
    for phase, limit in C['experiment_limits'].items():
        require(exact[phase] <= Decimal(str(limit)) * 3600 and rounded[phase] <= Decimal(str(limit)), 'exact/rounded phase cap')
    row = entries[C['reservation_id']]
    owned = next(x for x in mapping['entries'] if x['reservation_id'] == row['id'])
    require(owned['experiment'] == 'A2' and row['job_id'] == C['actual_job_id'] and row['cluster'] == 'bridges2'
            and row['account'] == C['expected_account'] and row['partition'] in C['allowed_partitions']
            and row['source_commit'] == SOURCE and row['output_dir'] == MAIN, 'actual A2 row identity')
    require(row['gpus'] == 1 and Decimal(str(row['requested_minutes'])) * 60 == C['resources']['duration_seconds']
            and row['status'] in ('PENDING', 'RUNNING'), 'actual bound duration; no old fixed hour')
    if release:
        require(release['ledger_sha256'] == normalized['current_snapshot_sha256']
                and release['active_mapping_reference'] == normalized['active_mapping_reference'], 'release/native mapping changed')
    return dict(ledger_sha256=normalized['current_snapshot_sha256'], active_mapping_reference=normalized['active_mapping_reference'],
                exact_requested_GPU_seconds_by_phase={k: str(v) for k, v in exact.items()}, no_old_charge_refunded=True)


def validate_release(r):
    require(r['phase'] == 'full_score' and r['full_scoring_admitted'] is True
            and 'bank_and_prefix4_only' not in r and 'pilot_root' not in r, 'new full-only release')
    require(r['actual_job_id'] == C['actual_job_id'] and r['reservation_id'] == C['reservation_id']
            and r['source_commit'] == SOURCE and r['main_root'] == MAIN
            and r['bound_config_sha256'] == sha(CONFIG) and r['resources'] == C['resources'], 'release actual binding')
    for key, value in C.items():
        if key.endswith('_sha256'):
            require(r[key] == value, 'release pinned identity: ' + key)
    require(r['current_usage_pass'] is True and r['delta_fresh_preflight_passed'] is True, 'fresh root owning checks')
    waiting = Path(C['evidence_root']) / 'WAITING-full_score.json'
    require(sha(waiting) == r['waiting_sha256'] and read(waiting)['bound_config_sha256'] == sha(CONFIG), 'exact current WAITING request')
    r['_waiting_path'], r['_waiting_sha256'] = str(waiting), r['waiting_sha256']
    rows = r['catalogues']
    require(len(rows) == 4 and {x['virtual_path'] for x in rows} == set(C['minimum_registry_paths']), 'release complete catalogue closure')
    proof = read_pinned(r['delta_preflight_receipt'], r['delta_preflight_receipt_sha256'])
    require(proof['complete'] is True and proof['phase'] == 'full_score'
            and proof['source_commit'] == SOURCE and proof['actual_GPU_job_id'] == C['actual_job_id']
            and proof['actual_Delta_owning_guards_passed'] is True and proof['stable_Delta_catalogues_before_after'] is True
            and proof['immutable_CPU_proof_not_rewritten'] is True and proof['catalogues'] == rows
            and proof['ledger_sha256'] == r['ledger_sha256'], 'full immutable CPU/current composite binding')
    cpu_ref = proof['actual_CPU_COMPLETE']
    cpu = read_pinned(cpu_ref['path'], cpu_ref['sha256'])
    require(cpu['complete'] is True and cpu['phase'] == 'full_score' and cpu['timely_window'] is True
            and cpu['actual_future_GPU_job_id'] == C['actual_job_id'] and cpu['source_commit'] == SOURCE
            and cpu['groups_file_sha256'] == C['groups_file_sha256'] and cpu['bank_file_sha256'] == C['bank_file_sha256']
            and cpu['bank_manifest_sha256'] == C['bank_manifest_sha256'] and cpu['full_rows'] == 59652
            and cpu['full_controls'] == 3396 and cpu['full_domain_support_audit_complete'] is True
            and cpu['waiting_sha256'] == r['waiting_sha256'] and cpu['bound_gpu_config_sha256'] == sha(CONFIG)
            and cpu['launch_packet_manifest_sha256'] == C['launch_packet_manifest_sha256'], 'fresh full native CPU proof required')
    return proof


def _lease(r):
    now = time.time()
    require(r['phase'] == 'full_score' and r['expires_at'] == r['issued_at'] + 300
            and 0 <= now - r['issued_at'] <= 300 and now < r['expires_at'], 'expired/future/renewed full release')


def gpu_release(phase):
    require(phase == 'full_score', 'only full_score may wait')
    packet(); source(); input_closure(); verify_existing_bank(C); reviewed_admission(); protection(); allocation(); budget()
    root = Path(C['release_directory'])
    target = root / (C['actual_job_id'] + '-full_score.json')
    require(not target.exists() and not target.is_symlink(), 'release predates WAITING')
    waiting = Path(C['evidence_root']) / 'WAITING-full_score.json'
    requested = time.time()
    work_end = current_deadlines(C, allocation()['facts'])['work_deadline']
    publication_end = min(requested + 300, work_end - C['resources']['minimum_entry_seconds'])
    require(publication_end > requested, 'no finite CPU/release publication window')
    write(waiting, dict(phase='full_score', job_id=C['actual_job_id'], requested_at=requested,
                        publication_deadline=publication_end, source_commit=SOURCE, bound_config_sha256=sha(CONFIG),
                        groups_file_sha256=C['groups_file_sha256'], bank_file_sha256=C['bank_file_sha256'],
                        bank_manifest_sha256=C['bank_manifest_sha256'], bank_internal_payload_sha256=C['bank_internal_payload_sha256'],
                        launch_packet_manifest_sha256=C['launch_packet_manifest_sha256'], resources=C['resources']))
    until = time.monotonic() + 300
    while not target.exists():
        left = current_deadlines(C, allocation()['facts'])['remaining_work_seconds']
        require(left >= C['resources']['minimum_entry_seconds'], 'waiting exhausted reviewed entry floor')
        if time.monotonic() >= until or time.time() >= publication_end:
            raise TimeoutError('one finite full_score release window expired')
        time.sleep(min(2, max(0.01, until - time.monotonic())))
    require(not target.is_symlink(), 'release symlink forbidden')
    acquired = target.read_bytes()
    acquired_sha = hashlib.sha256(acquired).hexdigest()
    require(sha(target) == acquired_sha, 'release mutated during acquisition')
    r = json.loads(acquired.decode('utf-8'))
    r['_release_path'], r['_release_sha256'] = str(target), acquired_sha
    require(time.time() < publication_end, 'root release arrived after finite WAITING publication window')
    validate_release(r); _lease(r)
    return r


def _entry_eligibility(r, phase):
    """Observe external allocation first; authenticate immutable bytes last."""
    require(phase == 'full_score' and r['phase'] == phase, 'only full_score may enter')
    observed = allocation(release=r)
    require(not Path(r['_release_path']).is_symlink() and sha(r['_release_path']) == r['_release_sha256'], 'release changed after acquisition')
    require(r['actual_job_id'] == os.environ['SLURM_JOB_ID'] == C['actual_job_id']
            and r['bound_config_sha256'] == sha(CONFIG) and r['source_commit'] == SOURCE
            and r['main_root'] == C['main_root']
            and r['launch_packet_manifest_sha256'] == C['launch_packet_manifest_sha256'], 'final exact entry identity')
    _lease(r)
    if '_waiting_path' in r:
        require(sha(r['_waiting_path']) == r['_waiting_sha256'], 'WAITING changed after owning preflight')
    for row in r['catalogues']:
        require(sha(row['virtual_path']) == row['sha256'], 'catalogue changed at entry')
    # Actual allocation() always supplies this metadata. Retain the capture-age
    # bound after hashing too; test I/O doubles may supply only the actual facts.
    if 'host_capture_unix' in observed:
        require(0 <= time.time() - observed['host_capture_unix'] <= C['maximum_allocation_capture_age_seconds'],
                'allocation aged during final immutable checks')
    deadlines = current_deadlines(C, observed['facts'])
    require(deadlines['remaining_work_seconds'] >= C['resources']['minimum_entry_seconds'], 'fresh final entry floor/deadline')
    _lease(r)
    return deadlines


def entry_release(r, phase):
    require(phase == 'full_score' and r['phase'] == phase, 'only full_score may enter')
    # Whole-bank hashing/decoding must finish before the immutable barrier.
    verify_existing_bank(C)
    before_consume = _entry_eligibility(r, phase)
    write(Path(C['evidence_root']) / 'CONSUMED-full_score.json',
          dict(phase=phase, job_id=C['actual_job_id'], release_sha256=r['_release_sha256'],
               consumed_at=time.time(), one_original_CLI_stage_only=True))
    # Evidence I/O can be slow. Permission stays spent if this second fresh
    # observation fails; never remove CONSUMED, renew, retry or extend a bound.
    after_consume = _entry_eligibility(r, phase)
    r['_entry_work_deadline'] = min(before_consume['work_deadline'], after_consume['work_deadline'])
    require(r['_entry_work_deadline'] - time.time() >= C['resources']['minimum_entry_seconds'],
            'consume/evidence I/O exhausted reviewed entry floor')
    _lease(r)
