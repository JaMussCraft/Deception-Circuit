#!/usr/bin/env python
"""Bounded final-only native assessment. prepare/dry-run never load weights.

The root receipt freezes ALL finalists before any donor or recipient output.
A dry-run without a receipt checks only structural data and workload bounds.
"""
from __future__ import annotations
import argparse
from collections import Counter
from contextlib import contextmanager
import fcntl
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import unicodedata

for _key in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_DATASETS_OFFLINE', 'HF_HUB_DISABLE_TELEMETRY'):
    os.environ[_key] = '1'
ROOT = Path(__file__).resolve().parent
POLICY = 'native-right-intersection-terminal-hold-v1'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n')
    tmp.replace(path)


def canonical(text):
    return ' '.join(unicodedata.normalize('NFKC', text).replace('’', "'").casefold().split()).rstrip('.')


def structural_pairs(final, prior):
    """Read only declared structural fields, never response/belief fields."""
    def clean(rows, domains):
        result = []
        for row in rows:
            p = {k: row[k] for k in ('source_id', 'statement', 'correct_option')}
            if p['correct_option'] not in (0, 1):
                raise ValueError('invalid source truth')
            for domain in domains:
                messages = row[domain]
                if [m['role'] for m in messages] != ['system', 'user']:
                    raise ValueError('native two-turn prompt required')
                p[domain] = [{'role': m['role'], 'content': m['content']} for m in messages]
            if len({p[d][-1]['content'] for d in domains}) != 1:
                raise ValueError('domain user prompts differ')
            result.append(p)
        if len(result) != 16 or Counter(p['correct_option'] for p in result) != {0: 8, 1: 8}:
            raise ValueError('require 16 structurally balanced pairs')
        for key in ('source_id', 'statement'):
            ids = [canonical(p[key]) for p in result]
            if len(set(ids)) != 16:
                raise ValueError('duplicate source/semantic claim')
        return result
    recipients, donors = clean(final['pairs'], 'DHR'), clean(prior['pairs'], 'H')
    for key in ('source_id', 'statement'):
        if {canonical(p[key]) for p in recipients} & {canonical(p[key]) for p in donors}:
            raise ValueError('final assessment overlaps exposed development statements')
    return recipients, donors


def donor_mapping(recipients, donors):
    """Use all 16 H donors once, four recipients in each truth-pair cell."""
    order = lambda p: digest(['native-donor-map-v1', p['source_id']])
    pools = {truth: sorted([p for p in donors if p['correct_option'] == truth], key=order) for truth in (0, 1)}
    mapping = {}
    for truth in (0, 1):
        group = sorted([p for p in recipients if p['correct_option'] == truth], key=order)
        for i, row in enumerate(group):
            dt = i // 4
            donor = pools[dt][truth * 4 + i % 4]
            mapping[row['source_id']] = donor['source_id']
    return mapping


def source_identity():
    paths = [ROOT / 'evaluate_native_sparse.py', ROOT / 'scripts/native_sparse.sbatch', ROOT / 'config.py', ROOT / 'pruning.py', ROOT / 'l0.py']
    for directory in ('models', 'evaluation'):
        paths += sorted((ROOT / directory).rglob('*.py'))
    return {str(p.relative_to(ROOT)): file_hash(p) for p in paths}


def checked_file(path, expected):
    path = Path(path).resolve()
    if file_hash(path) != expected:
        raise ValueError('file receipt hash mismatch: ' + str(path))
    return path


def check_export(export, layers, heads, hidden, intermediate):
    payload = {k: v for k, v in export.items() if k != 'export_hash'}
    if digest(payload) != export['export_hash']:
        raise ValueError('invalid binary export hash')
    keys = {str(i) for i in range(layers)}
    if set(export['K']) != keys or set(export['R']) != keys:
        raise ValueError('invalid keep/removal geometry')
    removed = []
    for l in range(layers):
        k, r = export['K'][str(l)], export['R'][str(l)]
        if len(k) != heads or any(v not in (0, 1) for v in k) or r != [1-v for v in k]:
            raise ValueError('keep/removal mismatch')
        removed += [[l, h] for h, v in enumerate(k) if not v]
    mask = export['removal_mask']
    expected = {'attention_heads': export['R'], 'attention_blocks': [0]*layers, 'mlp_blocks': [0]*layers,
                'attention_neurons': {str(l): [v for v in export['R'][str(l)] for _ in range(hidden//heads)] for l in range(layers)},
                'mlp_hidden': {str(l): [0]*intermediate for l in range(layers)},
                'mlp_output': {str(l): [0]*hidden for l in range(layers)}}
    if mask != expected or removed != export['removed_heads']:
        raise ValueError('export is not exact heads-only removal; MLP must remain open')
    return [export['K'][str(l)] for l in range(layers)]


def check_receipt(receipt):
    if (receipt.get('finalists_frozen') is not True or receipt.get('selection_basis') != 'SDR_WikiText_validation_only'
            or receipt.get('version') != 1 or receipt.get('no_test_based_selection') is not True):
        raise ValueError('missing/stale root source and finalist freeze receipt')
    scope = receipt.get('expansion_decision')
    spaces = ['union'] if scope == 'union_only' else ['union', 'all'] if scope == 'all_heads_complete' else []
    expected = {(a, s) for a in ('H', 'W', 'HW') for s in spaces}
    entries = receipt.get('finalists', [])
    if not expected or len(entries) != len(expected) or {(e['arm'], e['space']) for e in entries} != expected:
        raise ValueError('freeze all three/six arm finalists before ANY native output')
    for e in entries:
        if e.get('status') not in ('admissible', 'failed_frontier'):
            raise ValueError('finalist must disclose own-arm frontier status')
        for kind in ('export', 'checkpoint', 'manifest', 'run_identity'):
            checked_file(e[kind + '_path'], e[kind + '_sha256'])
    return entries


def frozen_protocol_identity():
    relative = Path('.scratch/selective-deception/sparse-wikitext-v2')
    directory = next((p/relative for p in (ROOT, *ROOT.parents) if (p/relative/'protocol.json').is_file()), None)
    if directory is None:
        raise ValueError('canonical frozen native/sparse protocol not found')
    protocol, wikitext = read(directory/'protocol.json'), read(directory/'wikitext-manifest.json')
    if wikitext['manifest_hash'] != digest({k:v for k,v in wikitext.items() if k != 'manifest_hash'}):
        raise ValueError('canonical WikiText manifest digest differs')
    return digest(protocol), wikitext['manifest_hash']


def check_finalist_identity(entry, export, manifest, identity, snapshot):
    """Verify gate-only checkpoint equivalence without constructing base weights."""
    import torch
    from evaluation.selective_mask_runner import _load_tensor, CANDIDATE_HASH
    if (manifest.get('manifest_hash') != digest({k:v for k,v in manifest.items() if k != 'manifest_hash'})
            or identity.get('manifest_hash') != manifest.get('manifest_hash')
            or identity != export.get('provenance') or digest(identity) != export.get('provenance_hash')):
        raise ValueError('finalist manifest/provenance identity mismatch')
    amendment, settings = manifest.get('amendment', {}), identity.get('settings', {})
    if (identity.get('policy') != 'amendment-v2' or amendment.get('policy') != 'amendment-v2'
            or identity.get('amendment') != amendment
            or any(amendment.get(k) != entry[e] or settings.get(k) != entry[e]
                   for k,e in (('collateral_arm','arm'), ('candidate_space','space')))
            or not amendment.get('protocol_hash')
            or identity.get('receipt', {}).get('protocol_hash') != amendment['protocol_hash']):
        raise ValueError('finalist arm/space/protocol identity mismatch')
    protocol_hash, wt_hash = frozen_protocol_identity()
    if (amendment['protocol_hash'] != protocol_hash
            or amendment.get('wikitext_manifest_hash') != wt_hash
            or identity.get('wikitext_manifest_hash') != wt_hash):
        raise ValueError('finalist differs from canonical frozen protocol/WikiText identity')
    candidates = manifest.get('candidate_heads')
    if (candidates != export.get('candidate_heads')
            or digest(candidates) != manifest.get('candidate_heads_hash')
            or digest(candidates) != export.get('candidate_heads_hash')
            or len(candidates) != export.get('effective_candidate_count')):
        raise ValueError('finalist candidate identity mismatch')
    original = identity.get('model', {})
    if (Path(original.get('snapshot','')).resolve() != Path(snapshot['path']).resolve()
            or any(original.get('files',{}).get(k) != v for k,v in snapshot['files'].items())
            or identity.get('dtype') != 'bfloat16'):
        raise ValueError('native original weights/tokenizer snapshot differs from training')
    checkpoint = _load_tensor(entry['checkpoint_path'], digest(identity))
    update = checkpoint.get('cursor',{}).get('update')
    if type(update) is not int or update not in range(64,513,64):
        raise ValueError('finalist checkpoint is not a scheduled completed validation update')
    gates = checkpoint['gates']
    expected_candidates = {tuple(x) for x in candidates}
    layers, heads = len(export['K']), len(export['K']['0'])
    if (layers,heads) == (32,32) and any(amendment.get(k) != v or settings.get(k,v) != v for k,v in (('max_updates',512),('checkpoint_every',64),('pairs_per_update',8))):
        raise ValueError('finalist amendment schedule differs from frozen 512/64/8 protocol')
    if entry['space'] == 'union' and (layers,heads) == (32,32) and digest(candidates) != CANDIDATE_HASH:
        raise ValueError('union finalist differs from frozen 103-head candidates')
    if entry['space'] == 'all' and expected_candidates != {(l,h) for l in range(layers) for h in range(heads)}:
        raise ValueError('all-head finalist has incomplete candidates')
    if entry['space'] == 'union' and amendment.get('union_heads', candidates) != candidates:
        raise ValueError('union finalist candidate identity differs')
    for l in range(layers):
        prefix = 'model.layers.%d.attn.head_gates.' % l
        logits, eligibility = gates[prefix+'log_alpha'], gates[prefix+'eligibility']
        eligible = torch.tensor([(l,h) in expected_candidates for h in range(heads)], dtype=torch.bool)
        if (logits.shape != (heads,) or eligibility.dtype != torch.bool
                or not torch.equal(eligibility, eligible) or not torch.isfinite(logits).all()):
            raise ValueError('checkpoint candidate eligibility/shape mismatch')
        soft = (torch.sigmoid(logits) * (gates[prefix+'zeta']-gates[prefix+'gamma']) + gates[prefix+'gamma']).clamp(0,1)
        keep = torch.where(eligible, (soft > .5).float(), torch.ones_like(soft)).int().tolist()
        if (keep != export['K'][str(l)] or logits.tolist() != export['logits'][str(l)]
                or eligibility.tolist() != export['eligibility'][str(l)]):
            raise ValueError('checkpoint deterministic export mismatch')
    for name, value in gates.items():
        if name.endswith('.eligibility') and '.attn.head_gates.' not in name and value.any():
            raise ValueError('checkpoint has eligible non-head gates')


@contextmanager
def writer_lock(path):
    path = Path(path); path.mkdir(parents=True, exist_ok=True)
    with (path/'.writer.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('native output store already has an active writer')
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def configure_runtime():
    import torch
    os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False


def hardware_identity():
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError('native hardware binding requires allocated GPU')
    return {'gpu': torch.cuda.get_device_name(0), 'cuda': torch.version.cuda,
            'capability': list(torch.cuda.get_device_capability(0))}


def prompt_text(messages):
    return '<|begin_of_text|>' + ''.join('<|start_header_id|>' + m['role'] + '<|end_header_id|>\n\n' + m['content'] + '<|eot_id|>' for m in messages) + '<|start_header_id|>assistant<|end_header_id|>\n\n'


def snapshot_identity(path):
    path = Path(path).resolve()
    if not path.is_dir() or not (path/'config.json').is_file() or not list(path.glob('*.safetensors')):
        raise ValueError('model must be an existing local original safetensors snapshot')
    files = {p.name: file_hash(p) for p in sorted(path.iterdir()) if p.is_file() and p.suffix in ('.safetensors', '.json', '.model', '.txt', '.jinja')}
    index = path/'model.safetensors.index.json'
    if index.exists() and not set(read(index)['weight_map'].values()) <= files.keys():
        raise ValueError('missing weight shard')
    return {'path': str(path), 'files': files}


def runtime_identity(backend):
    import torch
    return {'python': platform.python_version(), 'packages': {n: importlib.metadata.version(n) for n in ('torch', 'transformers', 'numpy')},
            'dtype': 'bfloat16', 'backend': backend, 'cuda_build': torch.version.cuda,
            'decode': {'greedy': True, 'max_new_tokens': 256}, 'padding': 'none_per_row',
            'deterministic_algorithms': torch.are_deterministic_algorithms_enabled(),
            'matmul_allow_tf32': torch.backends.cuda.matmul.allow_tf32,
            'cudnn_allow_tf32': torch.backends.cudnn.allow_tf32}


def build_manifest(args, tokenizer=None):
    recipients, donors = structural_pairs(read(args.pairs), read(args.donors))
    mapping = donor_mapping(recipients, donors)
    source = source_identity()
    structural = {'policy': POLICY, 'source': source, 'pairs_sha256': file_hash(args.pairs), 'donors_sha256': file_hash(args.donors),
                  'recipients': recipients, 'donors': donors, 'donor_mapping': mapping,
                  'donor_truth_cells': {'%d,%d' % (r, d): 4 for r in (0, 1) for d in (0, 1)},
                  'donor_judgment': 'pending_later_blind_annotation_against_own_statement; no_outcome_filtering',
                  'scope': 'exploratory_statement_holdout; not_entity_holdout; historical_exposure_unknown'}
    if args.receipt is None:
        return structural
    receipt = read(args.receipt)
    entries = check_receipt(receipt)
    model = snapshot_identity(args.model_path)
    config = read(Path(args.model_path)/'config.json')
    geometry = [config[k] for k in ('num_hidden_layers', 'num_attention_heads', 'hidden_size', 'intermediate_size')]
    finalists = []
    for entry in entries:
        export = read(entry['export_path'])
        if read(entry['run_identity_path']) != export.get('provenance'):
            raise ValueError('finalist run identity differs from exact export provenance')
        check_finalist_identity(entry, export, read(entry['manifest_path']), export['provenance'], model)
        finalists.append(dict(entry, keep_mask=check_export(export, *geometry), export_hash=export['export_hash']))
    if len({e['provenance']['amendment']['protocol_hash'] for e in (read(f['export_path']) for f in entries)}) != 1:
        raise ValueError('finalists use different protocols')
    if tokenizer is None:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True)
    for rows, domains in ((recipients, 'DHR'), (donors, 'H')):
        for row in rows:
            row['prompts'] = {d: {'text': prompt_text(row[d]), 'ids': tokenizer.encode(prompt_text(row[d]), add_special_tokens=False)} for d in domains}
    eos = [tokenizer.eos_token_id, tokenizer.convert_tokens_to_ids('<|eot_id|>')]
    if any(i is None for i in eos):
        raise ValueError('native EOS/eot token unavailable')
    eos = sorted(set(eos))
    if any(not isinstance(i, int) or i < 0 or i == tokenizer.unk_token_id for i in eos):
        raise ValueError('native EOS/eot token unavailable')
    structural.update(root_receipt=receipt, receipt_sha256=file_hash(args.receipt), model=model,
                      tokenizer_identity=digest({'snapshot': model, 'eos': eos, 'template': 'manual_llama3_no_date'}),
                      runtime=runtime_identity(args.backend), finalists=finalists, geometry=geometry,
                      eos_token_ids=eos, target_completions=16*3*(1+len(entries)), donor_completions=16,
                      max_generated_tokens=(16*3*(1+len(entries))+16)*256)
    structural['fingerprint'] = digest(structural)
    return structural


class Store:
    def __init__(self, path, manifest):
        self.path = Path(path)
        self.fp = manifest['fingerprint']
        self.path.mkdir(parents=True, exist_ok=True)
        frozen = self.path/'manifest.json'
        if frozen.exists() and read(frozen) != manifest:
            raise ValueError('store fingerprint mismatch')
        if not frozen.exists():
            atomic(frozen, manifest)

    def get(self, key):
        path = self.path/(key + '.json')
        if not path.exists():
            return None
        value = read(path)
        if value.pop('fingerprint') != self.fp or value.pop('record_hash') != digest(value):
            raise ValueError('stale/corrupt resumed output')
        return value

    def begin(self, key):
        marker = self.path/(key+'.inflight')
        try:
            with marker.open('x') as f:
                f.write(self.fp+'\n')
        except FileExistsError:
            raise ValueError('interrupted generation requires root budget review before retry: '+key)

    def put(self, key, value):
        atomic(self.path/(key+'.json'), dict(value, record_hash=digest(value), fingerprint=self.fp))
        marker = self.path/(key+'.inflight')
        if marker.exists():
            marker.unlink()


def execute(manifest, model, tokenizer, output):
    with writer_lock(output):
        return _execute(manifest, model, tokenizer, output)


def _execute(manifest, model, tokenizer, output):
    import torch
    from evaluation.native_interchange import DecodeSpec, capture_donor, generate_with_replay
    store = Store(output, manifest)
    spec = DecodeSpec(256, tuple(manifest['eos_token_ids']))
    mi, ti = digest({'model': manifest['model'], 'runtime': manifest['runtime'], 'source': manifest['source']}), manifest['tokenizer_identity']
    device = next(model.parameters()).device
    tokens = lambda ids: torch.tensor([ids], dtype=torch.long, device=device)
    recipients = {r['source_id']: r for r in manifest['recipients']}
    by_donor = {d['source_id']: d for d in manifest['donors']}
    masks = [('intact', torch.ones(manifest['geometry'][:2]))] + [(e['space']+'-'+e['arm'], torch.tensor(e['keep_mask'])) for e in manifest['finalists']]
    # One bank active at a time; all recipients/domains/masks reuse its exact bytes.
    for donor_id, donor in sorted(by_donor.items()):
        key = 'donor-' + digest(donor_id)
        bank_path = store.path/(key+'.pt')
        record = store.get(key)
        if record is None:
            store.begin(key)
            bank = capture_donor(model, tokens(donor['prompts']['H']['ids']), spec, model_identity=mi, tokenizer_identity=ti)
            tmp = bank_path.with_suffix('.tmp')
            torch.save(bank, tmp); tmp.replace(bank_path)
            store.put(key, {'donor_id': donor_id, 'generated_tokens': list(bank.generated_tokens), 'termination': bank.termination,
                            'response': tokenizer.decode(bank.generated_tokens, skip_special_tokens=True), 'bank_sha256': file_hash(bank_path),
                            'judgment': 'pending_blind_annotation_against_own_statement'})
        else:
            checked_file(bank_path, record['bank_sha256'])
            bank = torch.load(bank_path, map_location='cpu', weights_only=False)
        for rid in sorted(r for r, d in manifest['donor_mapping'].items() if d == donor_id):
            row = recipients[rid]
            for domain in 'DHR':
                ids = row['prompts'][domain]['ids']
                for name, mask in masks:
                    target_key = 'target-' + digest([rid, domain, name])
                    if store.get(target_key) is not None:
                        continue
                    store.begin(target_key)
                    result = generate_with_replay(model, tokens(ids), mask, bank, spec, model_identity=mi, tokenizer_identity=ti)
                    store.put(target_key, {'source_id': rid, 'donor_id': donor_id, 'domain': domain, 'mask': name, 'frontier_status': next((e['status'] for e in manifest['finalists'] if e['space']+'-'+e['arm'] == name), 'intact'),
                        'generated_tokens': list(result.generated_tokens), 'response': tokenizer.decode(result.generated_tokens, skip_special_tokens=True),
                        'termination': result.termination, 'mapped_prompt_queries': len(ids)-result.unmapped_prefix,
                        'real_prompt_queries': len(ids), 'unmapped_prefix': result.unmapped_prefix,
                        'terminal_held_steps': result.terminal_held_steps, 'query_indices': list(result.query_indices),
                        'prompt_map': list(result.prompt_map), 'donor_judgment': 'pending_later_blind_annotation',
                        'recipient_source_truth': row['correct_option'], 'donor_source_truth': donor['correct_option'],
                        'source_truth_agreement': row['correct_option'] == donor['correct_option'],
                        'encoded_target_truth_value': 1-row['correct_option'] if domain == 'R' else None})
        del bank


def check_run_receipt(authorization, manifest, manifest_sha256):
    if (authorization.get('assessment_authorized') is not True
            or authorization.get('manifest_fingerprint') != manifest['fingerprint']
            or authorization.get('manifest_sha256') != manifest_sha256
            or authorization.get('finalist_receipt_sha256') != manifest['receipt_sha256']):
        raise ValueError('missing/stale root execution receipt')
    estimate, reserved = authorization.get('estimated_gpu_seconds', 0), authorization.get('reserved_gpu_seconds', 0)
    if not isinstance(estimate, (int, float)) or not isinstance(reserved, (int, float)) or not 0 < estimate <= reserved:
        raise ValueError('root execution receipt requires measured estimate within reservation')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    for mode in ('prepare', 'dry-run', 'run'):
        modes.add_argument('--'+mode, action='store_true')
    for field in ('pairs', 'donors', 'output-dir'):
        parser.add_argument('--'+field, type=Path, required=True)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--run-receipt', type=Path, help='root authorization binding exact prepared manifest and measured budget')
    parser.add_argument('--model-path', type=Path)
    parser.add_argument('--backend', choices=('eager', 'sdpa'), default='sdpa')
    args = parser.parse_args(argv)
    if not args.dry_run and (args.receipt is None or args.model_path is None):
        parser.error('prepare/run require root finalist receipt and local model snapshot')
    if args.receipt is not None and args.model_path is None:
        parser.error('receipt verification requires local model snapshot')
    if args.receipt is not None:
        configure_runtime()
    manifest = build_manifest(args)
    if args.dry_run:
        print(json.dumps({'source_sha256': digest(manifest['source']), 'structural_only': args.receipt is None,
                          'recipients': 16, 'donors': 16, 'target_bounds': [192, 336],
                          'fingerprint': manifest.get('fingerprint'), 'weights_loaded': False}, sort_keys=True))
        return
    if args.prepare:
        with writer_lock(args.output_dir):
            Store(args.output_dir, manifest)
        print(manifest['fingerprint'])
        return
    # Require preparation before loading any weights or producing ANY output.
    frozen = args.output_dir/'manifest.json'
    if not frozen.is_file() or read(frozen) != manifest:
        raise ValueError('run requires exact frozen prepared manifest/receipt/runtime/source')
    if args.run_receipt is None:
        raise ValueError('run requires root execution receipt after preparation')
    with writer_lock(args.output_dir):
        authorization = read(args.run_receipt)
        check_run_receipt(authorization, manifest, file_hash(frozen))
        actual_hardware = hardware_identity()
        if authorization.get('hardware') != actual_hardware:
            raise ValueError('root execution receipt hardware differs from measured/calibrated allocation')
        execution_record = dict(authorization, receipt_sha256=file_hash(args.run_receipt))
        execution_path = args.output_dir/'execution-receipt.json'
        if execution_path.exists() and read(execution_path) != execution_record:
            raise ValueError('root execution receipt changed across resume, including hardware/budget')
        atomic(execution_path, execution_record)
        import torch
        if not torch.cuda.is_available():
            raise RuntimeError('real-model run requires allocated GPU; never run weights on login CPU')
        from transformers import AutoTokenizer
        from config import NodePruningConfig
        from models.llama_node import PrunableLlamaForCausalLM
        tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True)
        cfg = NodePruningConfig(prune_attention_heads=True, prune_attention_neurons=False,
                                prune_attention_blocks=False, prune_mlp_hidden=False, prune_mlp_output=False,
                                prune_mlp_blocks=False, prune_full_layers=False, prune_embedding=False)
        model = PrunableLlamaForCausalLM.from_pretrained_with_pruning(str(args.model_path), cfg,
                    torch_dtype=torch.bfloat16, attn_implementation=args.backend, local_files_only=True).to('cuda').eval()
        _execute(manifest, model, tokenizer, args.output_dir)


if __name__ == '__main__':
    main()
