"""Bounded selective-mask execution. Stage 1 inputs and primitives stay immutable."""
from __future__ import annotations

import copy
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import random
import time

import numpy as np
import torch
import torch.nn.functional as F

from evaluation import selective_diagnostics as sd
from evaluation import selective_mask as sm
from evaluation import selective_runner as sr
from l0 import HardConcreteGate

BASELINE_PATH = 'dual_stream_self_donor_all_gates_open_uncached'
CANDIDATE_HASH = '6c5943656abc881d8ff949f776a3fa9dc11e7161254a2c16738c7306b8624420'
AUDIT = {
    'train': ['f9a895ea5e05720c2e658132118c2da6924885b3f2abd582f002f174dc32a737', '15e75543b365e739b779a06a11c3f6a063208016c078e646fb09a2824a290d09', '36f2a7f9f6a6824650c2423d0a3efc19e7a9625bee3d8a5e75eabe815d400ec2', '1ab6cf1c7538d17f2286964dff89bf3efd23a82de0d39c3ad2c456b118ba441e'],
    'validation': ['8256872e93a4ba4ba34f5c5c45c4f7dda8c2a29903b3b58f8b73ce23a8a667b8', 'fc5f4e989a7eba00a65efe70d24030b46fd5b526b04b0a0961ddb53cbc66d9da', '4e6b8a1359ead8f6720f35baef582bded3e35a0ed6e17c2039673dbde03b031f', '47551a18a8e08fb11b7b1a3ea002ca0cf02af75baee0c54b36674ac47ccd1a41'],
}
AUDIT_KEYS = ('retained_records_hash', 'representative_mapping_hash', 'donor_mapping_hash', 'allview_clean_endpoint_hash')


def select_checkpoint(history: list[dict], baseline: dict) -> dict | None:
    if baseline.get('split') != 'validation' or any(x.get('split') != 'validation' for x in history):
        raise ValueError('checkpoint selection accepts validation only')
    valid = [x for x in history if x['h_correct'] >= baseline['h_correct']
             and x['capable_correct'] >= baseline['capable_correct']
             and x['removed'] > 0 and math.isfinite(x['suppression']) and x['suppression'] < baseline['suppression']]
    return min(valid, key=lambda x: (x['suppression'], x['removed'], x['update'])) if valid else None


def _tensor_digest(value):
    h=hashlib.sha256()
    def visit(x):
        if isinstance(x,torch.Tensor):
            h.update(str((x.dtype,tuple(x.shape))).encode()); h.update(x.detach().cpu().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes())
        elif isinstance(x,np.ndarray):
            h.update(str((x.dtype,x.shape)).encode()); h.update(x.tobytes())
        elif isinstance(x,dict):
            for key in sorted(x,key=str):
                if key!='payload_digest': visit(key); visit(x[key])
        elif isinstance(x,(list,tuple)):
            h.update(str(type(x)).encode())
            for item in x: visit(item)
        else: h.update(repr(x).encode())
    visit(value)
    return h.hexdigest()


def _save_tensor(path, value):
    path = Path(path); temporary = path.with_name(path.name + '.tmp')
    with temporary.open('wb') as f:
        torch.save(dict(value,payload_digest=_tensor_digest(value)), f); f.flush(); os.fsync(f.fileno())
    os.replace(temporary, path)


def _load_tensor(path, fingerprint):
    value = torch.load(path, map_location='cpu', weights_only=False)
    if value.get('payload_digest') != _tensor_digest(value):
        raise ValueError('corrupt completed tensor record')
    if value.get('fingerprint') != fingerprint:
        raise ValueError('tensor fingerprint mismatch')
    value.pop('payload_digest')
    return value


def _load_cache(path, fingerprint):
    value = _load_tensor(path, fingerprint)
    if value['baseline_path'] != BASELINE_PATH:
        raise ValueError('cache baseline path mismatch')
    return value


def _gate_state(model):
    # SwiGLU gate_proj is a base weight, never a HardConcreteGate tensor.
    return {name+'.'+key:tensor for name,module in model.named_modules()
            if isinstance(module,HardConcreteGate) for key,tensor in module.state_dict().items()}


def _checkpoint(path, model, optimizer, cursor, fingerprint):
    # Gate-only state avoids copying 16 GB of frozen weights; snapshot identity binds base.
    state = {n:t.detach().cpu().clone() for n,t in _gate_state(model).items()}
    _save_tensor(path, dict(fingerprint=fingerprint, gates=state,
        optimizer=optimizer.state_dict(), cursor=copy.deepcopy(cursor),
        rng={'python': random.getstate(), 'numpy': np.random.get_state(), 'torch': torch.get_rng_state(),
             'cuda': torch.cuda.get_rng_state_all() if torch.cuda.is_available() else []}))


def _restore(path, model, optimizer, fingerprint):
    value = _load_tensor(path, fingerprint)
    current = _gate_state(model)
    if set(current) != set(value['gates']):
        raise ValueError('checkpoint gate/eligibility configuration mismatch')
    with torch.no_grad():
        for name, tensor in current.items():
            incoming = value['gates'][name]
            if tensor.shape != incoming.shape or tensor.dtype != incoming.dtype:
                raise ValueError('checkpoint gate shape/dtype mismatch')
            if name.endswith('eligibility') and not torch.equal(tensor.cpu(), incoming):
                raise ValueError('checkpoint eligibility mismatch')
            tensor.copy_(incoming)
    optimizer.load_state_dict(value['optimizer'])
    rng = value['rng']; random.setstate(rng['python']); np.random.set_state(rng['numpy'])
    torch.set_rng_state(rng['torch'])
    if rng['cuda']:
        torch.cuda.set_rng_state_all(rng['cuda'])
    return value['cursor']


def _read_manifest(path):
    m = json.loads(Path(path).read_text()); sm.validate_pilot_manifest(m)
    if len(m['candidate_heads']) != 103 or m['candidate_heads_hash'] != CANDIDATE_HASH:
        raise ValueError('frozen 103 candidate heads mismatch')
    for split in AUDIT:
        d = m['splits'][split]
        if d['n_pairs'] != 119 or [d[k] for k in AUDIT_KEYS] != AUDIT[split]:
            raise ValueError('frozen 119-pair data audit mismatch')
    return m


def _safety_slice(clusters):
    groups = {}
    for c in sorted(clusters, key=lambda c: c['cluster_id']):
        groups.setdefault(tuple(c['stratum']), []).append(c['cluster_id'])
    expected = {(d, p, t) for d in ('identity', 'inversion') for p in (1, 2) for t in ('audit', 'lab')}
    if set(groups) != expected or any(len(x) < 2 for x in groups.values()):
        raise ValueError('safety slice requires two clusters in each stratum')
    rng = random.Random(0)
    return sorted(cid for key in sorted(groups) for cid in rng.sample(groups[key], 2))


def _capability_report(clusters, capable, floor=60):
    counts = {}
    for c, flag in zip(clusters, capable.tolist()):
        key = '|'.join(map(str, c['stratum']))
        counts.setdefault(key, {'total': 0, 'capable': 0})
        counts[key]['total'] += 1; counts[key]['capable'] += int(flag)
    represented = [{c['stratum'][i] for c in clusters} for i in (0, 1)]
    covered = [{c['stratum'][i] for c, ok in zip(clusters, capable.tolist()) if ok} for i in (0, 1)]
    n = int(capable.sum())
    return dict(n_total=len(clusters), n_capable=n, by_stratum=counts,
                usable=n >= floor and covered == represented)


def _candidate_logits(model):
    return torch.cat([layer.attn.head_gates.log_alpha[layer.attn.head_gates.eligibility]
                      for layer in model.model.layers if layer.attn.head_gates.eligibility.any()])


def _optimizer(params):
    return torch.optim.AdamW(params, lr=.03, weight_decay=0.)


def _weighted_loss(loss, n_d, window_h, window_capable):
    return (loss.suppression * n_d / window_h + loss.truth_nondegradation * loss.n_h / window_h
            + loss.capable_kl * loss.n_capable / max(window_capable, 1))


def _microbatches(split, size):
    groups = {}
    for i, c in enumerate(split['clusters']):
        p = c['prompts']['original']['D']['clean']
        groups.setdefault((len(p['input_ids']), tuple(p['attention_mask'])), []).append(i)
    return [ids[start:start + size] for key, ids in sorted(groups.items()) for start in range(0, len(ids), size)]


def _joint_logits(model, split, indices, *, self_donor=False):
    if len(indices)!=1: raise ValueError('exactly one unpadded joint D/H pair required')
    clusters = split['clusters']; lookup = {c['cluster_id']: c for c in clusters}
    recipients, donors, attention = [], [], []
    for policy in ('D', 'H'):
        for i in indices:
            c = clusters[i]; p = c['prompts']['original'][policy]['clean']
            donor = lookup[split['donor_map'][c['cluster_id']]]['prompts']['original']['H']['clean']
            if not all(p['attention_mask']) or len(p['input_ids'])!=len(donor['input_ids']):
                raise ValueError('joint pair must be aligned and unpadded')
            recipients.append(p['input_ids']); donors.append(p['input_ids'] if self_donor else donor['input_ids']); attention.append(p['attention_mask'])
    device = next(model.parameters()).device
    logits = model(input_ids=torch.tensor(recipients, device=device),
        corrupted_input_ids=torch.tensor(donors, device=device),
        attention_mask=torch.tensor(attention, device=device), use_cache=False).logits[:, -1].float()
    return logits[:len(indices)], logits[len(indices):]


@contextmanager
def _preserve_gates(model):
    # Existing EvalContext overwrites gates when applying a circuit. Preserve learned
    # logits AND eligibility, and disable eligibility while executing fixed comparators.
    saved = [(g, g.log_alpha.detach().clone(), None if g.eligibility is None else g.eligibility.clone())
             for g in model.modules() if isinstance(g, HardConcreteGate)]
    training = model.training
    try:
        for g, _, _ in saved:
            g.set_eligibility(None)
        model.eval()
        yield
    finally:
        with torch.no_grad():
            for g, alpha, eligible in saved:
                g.log_alpha.copy_(alpha); g.set_eligibility(eligible)
        model.train(training)


def _baseline_logits(model, split):
    from analysis import open_all_gates
    by_policy = {'D': [], 'H': []}
    with _preserve_gates(model), torch.no_grad():
        open_all_gates(model)
        for i in range(len(split['clusters'])):
            d,h = _joint_logits(model,split,[i],self_donor=True)
            if not torch.isfinite(d).all() or not torch.isfinite(h).all():
                raise ValueError('nonfinite intact readout')
            by_policy['D'].append(d.cpu()); by_policy['H'].append(h.cpu())
    return {p: torch.cat(rows) for p, rows in by_policy.items()}


def _labels(split):
    return {p: torch.tensor([c['labels'][p]['token_id'] for c in split['clusters']]) for p in ('D', 'H')}


def _metrics(d, h, base, labels, capable, *, update, removed):
    from evaluation.selective_mask import pilot_loss
    loss = pilot_loss(d, labels['D'][:, None], h, base, labels['H'], capable,
                      torch.empty(0), rho=0.)
    pred = h.argmax(-1); correct = pred == labels['H']
    # Fixed pairs, descriptive paired uncertainty on surrogate differences.
    each = -torch.log1p(-F.softmax(d, -1).gather(1, labels['D'][:, None]).squeeze(1).clamp(max=1-1e-7))
    return dict(split='validation', update=update, removed=removed,
        h_correct=int(correct.sum()), h_total=len(h), capable_correct=int(correct[capable].sum()),
        capable_total=int(capable.sum()), suppression=float(loss.suppression),
        capable_kl=float(loss.capable_kl), truth_nondegradation=float(loss.truth_nondegradation),
        d_label_logits=d.gather(1,torch.stack((labels['D'],labels['H']),dim=1)).tolist(),
        h_label_logits=h.gather(1,torch.stack((labels['D'],labels['H']),dim=1)).tolist(),
        h_argmax_ids=pred.tolist(),d_argmax_ids=d.argmax(-1).tolist(),
        h_truth_probability=F.softmax(h, -1).gather(1, labels['H'][:, None]).squeeze(1).tolist(),
        h_argmax={'D': int((pred == labels['D']).sum()), 'H': int(correct.sum()),
                  'other': int(((pred != labels['D']) & ~correct).sum())},
        d_argmax={'D': int((d.argmax(-1) == labels['D']).sum()), 'H': int((d.argmax(-1) == labels['H']).sum()),
                  'other': int(((d.argmax(-1) != labels['D']) & (d.argmax(-1) != labels['H'])).sum())},
        d_surrogate_per_pair=each.tolist())


def _validation(model, split, cache, update, heads, provenance):
    model.eval()
    exported = sm.export_binary_masks(model, heads, provenance=provenance)
    ds, hs = [], []
    with torch.no_grad():
        for i in range(len(split['clusters'])):
            d, h = _joint_logits(model, split, [i]); ds.append(d.cpu()); hs.append(h.cpu())
    result = _metrics(torch.cat(ds), torch.cat(hs), cache['h_logits'], _labels(split), cache['capable'],
                      update=update, removed=len(exported['removed_heads']))
    baseline = torch.tensor(cache['metrics']['d_surrogate_per_pair'])
    delta = baseline - torch.tensor(result['d_surrogate_per_pair'])
    result['paired_suppression_delta'] = float(delta.mean())
    result['paired_suppression_standard_error'] = float(delta.std(unbiased=True) / math.sqrt(len(delta)))
    model.train()
    return result, exported


def _generation_cost(m):
    rows = [r for r in m['rows'] if r['kind'] == 'generation']
    needed = {r['donor']['reference_row_id'] for r in rows if r.get('donor')}
    available = {r['row_id'] for r in m['donor_reference_rows']}
    if needed != available:
        raise ValueError('generation reference closure mismatch')
    frozen={r['row_id'] for r in m.get('frozen_donor_reference_rows',m['donor_reference_rows'])}
    if not needed<=frozen: raise ValueError('frozen generation reference closure mismatch')
    if m.get('pilot_purpose') in ('baseline','validation_safety') and (len(rows)>32 or len(frozen)>16):
        raise ValueError('prefit generation workload cap exceeded')
    return dict(target_completions=len(rows), donor_completions=len(frozen),
                max_new_tokens=(len(rows) + len(frozen)) * 96)


def make_evaluation_manifest(source_manifest: dict, mask_exports: dict, *, purpose: str,
                             frozen_slice: list[str], provenance: dict) -> dict:
    if purpose not in ('validation_safety', 'final_test', 'baseline'):
        raise ValueError('unknown evaluation purpose')
    result = copy.deepcopy(source_manifest)
    result['parent_manifest_hash'] = source_manifest['manifest_hash']
    result['pilot_purpose'] = purpose; result['pilot_provenance'] = copy.deepcopy(provenance)
    result['learned_masks'] = {('learned-' + name + '-' + e['export_hash']): copy.deepcopy(e)
                               for name, e in sorted(mask_exports.items())}
    # Rebuild from intact templates; never relabel fixed core row identity as learned.
    templates = {}
    for row in source_manifest['rows']:
        if row['cluster_id'] in frozen_slice:
            key = (row['kind'], row['cluster_id'], row['view'], row['policy'])
            donor = row.get('donor')
            eligible = donor and donor.get('cluster_id') != row['cluster_id'] and donor.get('policy') == 'H' and donor.get('stream') == 'clean'
            old = templates.get(key, {}).get('donor')
            old_eligible = old and old.get('cluster_id') != row['cluster_id'] and old.get('policy') == 'H' and old.get('stream') == 'clean'
            if key not in templates or (eligible and not old_eligible):
                templates[key] = row
    rows = []
    for template in templates.values():
        conditions = list(result['learned_masks']) if purpose == 'validation_safety' else ['intact'] + list(result['learned_masks'])
        if purpose == 'final_test':
            conditions += ['core', 'd_minus_f', 'random_core_seed0']
        for label in conditions:
            row = copy.deepcopy(template)
            row['condition'] = label; row['mask_label'] = label
            row['identity_sanity_check'] = False
            if label == 'intact':
                row['donor'] = None
            elif row.get('donor') is not None and (row['donor'].get('cluster_id') == row['cluster_id'] or row['donor'].get('policy') != 'H' or row['donor'].get('stream') != 'clean'):
                raise ValueError('derived interventions require fixed nonself clean H donor')
            row['pilot_provenance_hash'] = sd.content_hash(provenance)
            row.pop('row_id', None); row['row_id'] = 'pilot-' + sd.content_hash(row)
            rows.append(row)
    references=[]; reference_ids={}
    for original in source_manifest.get('frozen_donor_reference_rows',source_manifest['donor_reference_rows']):
        ref=copy.deepcopy(original); old_id=ref.pop('row_id'); ref.pop('used_by',None)
        ref['prompt'].pop('reference_row_id',None)
        ref['row_id']='pilot-reference-'+sd.content_hash({'parent':source_manifest['manifest_hash'],'reference':ref})
        reference_ids[old_id]=ref['row_id']; references.append(ref)
    for row in rows:
        if row['kind']=='generation' and row.get('donor'):
            row['donor']['reference_row_id']=reference_ids[row['donor']['reference_row_id']]
            row.pop('row_id'); row['row_id']='pilot-'+sd.content_hash(row)
    result['rows'] = rows
    needed = {r['donor']['reference_row_id'] for r in rows if r['kind'] == 'generation' and r.get('donor')}
    result['frozen_donor_reference_rows']=references
    result['donor_reference_rows'] = [r for r in references if r['row_id'] in needed]
    result['manifest_hash'] = sd.manifest_hash(result)
    _generation_cost(result)
    return result


def _generation_manifest(m, slice_ids, purpose, provenance, exports=None):
    split = m['splits']['validation']; clusters = split['clusters']
    by_id = {c['cluster_id']: c for c in clusters}
    rows, refs = [], {}
    for cid in slice_ids:
        c = by_id[cid]; donor_c = by_id[split['donor_map'][cid]]
        donor = sd._endpoint(donor_c, 'H', 'clean', 'free_response')
        ref = dict(kind='donor_reference', prompt=copy.deepcopy(donor), decode={'max_new_tokens': 96})
        ref['row_id'] = 'pilot-reference-' + sd.content_hash(ref)
        refs[ref['row_id']] = ref; donor['reference_row_id'] = ref['row_id']
        for policy in ('D', 'H'):
            row = dict(kind='generation', cluster_id=cid, view='free_response', policy=policy,
                condition='nonself', mask_label='intact', labels=c['labels'],
                recipient=sd._endpoint(c, policy, 'clean', 'free_response'), donor=copy.deepcopy(donor),
                identity_sanity_check=False)
            row['row_id'] = sd.content_hash(row); rows.append(row)
    source = dict(rows=rows, donor_reference_rows=list(refs.values()), frozen_donor_reference_rows=list(refs.values()), clusters=clusters,
                  config={'max_new_tokens': 96, 'decode': {'max_new_tokens': 96}}, manifest_hash=m['manifest_hash'])
    return make_evaluation_manifest(source, exports or {}, purpose=purpose, frozen_slice=slice_ids, provenance=provenance)


def _execute_generation(manifest, ctx, output, provenance, masks, resume):
    if manifest['manifest_hash'] != sd.manifest_hash(manifest):
        raise ValueError('derived evaluation manifest hash mismatch')
    _generation_cost(manifest)
    if not resume and (Path(output) / 'run.json').exists():
        raise FileExistsError('evaluation exists; explicit --resume required')
    with _preserve_gates(ctx.node_model):
        store = sr.ResultStore(output, manifest, provenance)
        references=manifest.get('frozen_donor_reference_rows',manifest['donor_reference_rows'])
        if references:
            import fcntl
            ref_identity={'baseline_fingerprint':_baseline_fingerprint(provenance),'decode':manifest['config']['decode']}
            donor_rows=sr.donor_diagnostics(manifest,[{'donor':dict(ref['prompt'],reference_row_id=ref['row_id'])} for ref in references])
            ref_manifest=dict(rows=donor_rows,donor_reference_rows=references,clusters=manifest['clusters'],
                config=manifest['config'],parent_manifest_hash=manifest.get('parent_manifest_hash'))
            ref_manifest['manifest_hash']=sd.manifest_hash(ref_manifest)
            directory=Path(provenance['receipt']['donor_reference_dir'])/sd.content_hash({'manifest':ref_manifest['manifest_hash'],'identity':ref_identity})
            directory.mkdir(parents=True,exist_ok=True)
            with (directory/'writer.lock').open('a') as lock:
                try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError as exc: raise ValueError('shared donor reference has an active writer') from exc
                reference_store=sr.ResultStore(directory,ref_manifest,ref_identity)
                from evaluation.benchmark_eval import eos_ids_for
                for row in donor_rows:
                    if row['row_id'] not in reference_store.results:
                        payload=sr.score_row(ctx,row,None)
                        payload['intended_answer_argmax_valid']=payload['argmax_category']==row['intended_label']
                        reference_store.append(row,payload)
                for row in references:
                    if row['row_id'] not in reference_store.results:
                        request={'recipient':row['prompt'],'donor':None,'decode':row['decode']}
                        reference_store.append(row,sr.generate_row(ctx,request,None,None,eos_ids=eos_ids_for(ctx.node_model)))
                for row in sr.donor_diagnostics(manifest)+manifest['donor_reference_rows']:
                    if row['row_id'] not in store.results:
                        payload=dict(reference_store.results[row['row_id']]['payload'],shared_reference_fingerprint=reference_store.fingerprint)
                        store.append(row,payload)
        summary = sr.execute(manifest, store, ctx, masks)
        sr.export_blind(manifest, store, Path(output) / 'blind')
    return summary


def _receipt(path, m, mode):
    record = json.loads(Path(path).read_text())
    if (record.get('version') != 1 or record.get('manifest_hash') != m['manifest_hash']
            or record.get('baseline_path') != BASELINE_PATH or not record.get('root_decision')
            or not record.get('source_revision') or not record.get('donor_reference_dir') or record.get('safety_cluster_ids') != _safety_slice(m['splits']['validation']['clusters'])
            or record.get('policy') != 'report18-v1'):
        raise ValueError('root freeze receipt identity/policy mismatch')
    if mode != 'baseline':
        if (record.get('stage1_behavior') != 'passed' or record.get('capability') != 'passed'
                or record.get('generation_headroom') != 'passed' or not record.get('baseline_fingerprint')
                or not record.get('baseline_cache_sha256') or not record.get('baseline_generation_fingerprint')):
            raise ValueError('root baseline gates have not passed')
    if mode in ('train', 'evaluate') and not record.get('measured_budget', {}).get('passed'):
        raise ValueError('root measured budget missing')
    return record


def _hash_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def _source_files():
    here = Path(__file__).resolve().parents[1]
    paths = [here / 'train_selective_mask.py', here / 'evaluate_selective_deception.py',
             here / 'l0.py', here / 'analysis.py', here / 'config.py',
             here / 'scripts/selective_mask.sbatch']
    for folder in ('evaluation', 'models', 'dataset', 'tasks'):
        paths += list((here / folder).rglob('*.py'))
    source = {str(p.relative_to(here)): _hash_file(p) for p in sorted(paths)}
    return source


def _identity(args, m, receipt):
    from evaluate_selective_deception import cached_snapshot
    snapshot = cached_snapshot(args.model_path)
    if args.model_revision != snapshot.name or receipt.get('model_revision') != snapshot.name:
        raise ValueError('cached model revision differs from root pin')
    # Actual hashes, including weights. CPU dry-run does not call this function.
    files = {p.name: _hash_file(p) for p in sorted(snapshot.iterdir()) if p.is_file()}
    source=_source_files()
    _,mask_identity,resolved=sr.resolve_masks()
    if receipt.get('source_files_hash') != sd.content_hash(source):
        raise ValueError('root receipt source content hash mismatch')
    return dict(manifest_hash=m['manifest_hash'], model={'snapshot': str(snapshot), 'files': files, 'revision':snapshot.name},
        fixed_masks=mask_identity,fixed_bindings=resolved[1],operand_configs=resolved[2],
        source_revision=receipt['source_revision'], source_files=source, source_files_hash=sd.content_hash(source),
        baseline_path=BASELINE_PATH, dtype='bfloat16', device=args.device,
        hardware={'gpu': torch.cuda.get_device_name(0), 'cuda': torch.version.cuda,
                  'capability': list(torch.cuda.get_device_capability(0))},
        packages={'torch': torch.__version__, 'transformers': __import__('transformers').__version__,'numpy':np.__version__,'python':__import__('platform').python_version()},
        receipt={k:v for k,v in receipt.items() if k not in ('final_assessment','final_evaluation_manifest_hash','evaluation_checkpoints')}, settings={k: getattr(args,k) for k in ('rho','seed','epochs','validate_every','joint_pairs','accumulation')},
        optimizer={'name':'AdamW','lr':.03,'weight_decay':0.,'clip_norm':1.,'schedule':'constant','expected_initial_removed':1.},
        policy='report18-v1', deterministic_algorithms=True, cublas_workspace=':4096:8', tf32=False, decode={'max_new_tokens':96,'implementation':'evaluation.gen_engine.generate'})


def _runtime(args, identity):
    from transformers import AutoTokenizer
    from evaluate_selective_deception import build_context
    snapshot = identity['model']['snapshot']
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = 'right'
    masks, mask_identity, resolved = sr.resolve_masks()
    if mask_identity!=identity['fixed_masks'] or resolved[1]!=identity['fixed_bindings'] or resolved[2]!=identity['operand_configs']:
        raise ValueError('fixed circuit artifacts changed during startup')
    return build_context(args, {'model': {'snapshot': snapshot}}, tokenizer, masks, resolved), masks


def _plan(args, m):
    for key in ('epochs','validate_every','joint_pairs','accumulation'):
        if getattr(args,key) is None or getattr(args,key) <= 0:
            raise ValueError('explicit positive training budget required: ' + key)
    if args.joint_pairs != 1:
        raise ValueError('joint_pairs=1 frozen until separate numerical geometry proof')
    if args.epochs > 100 or args.rho not in (0., .001, .01, .1) or args.seed is None:
        raise ValueError('frozen rho/seed/epoch budget required')
    train = m['splits']['train']
    micros = _microbatches(train,args.joint_pairs) if train['clusters'] else [None]*math.ceil(train['n_pairs']/args.joint_pairs)
    n_updates = math.ceil(len(micros)/args.accumulation)*args.epochs
    validations = len([e for e in range(1,args.epochs+1) if e % args.validate_every == 0 or e == args.epochs])
    ids = _safety_slice(m['splits']['validation']['clusters']) if m['splits']['validation']['clusters'] else []
    donors = len({m['splits']['validation']['donor_map'][cid] for cid in ids}) if ids else 16
    return dict(source_files_hash=sd.content_hash(_source_files()),manifest_hash=m['manifest_hash'], train_pairs=train['n_pairs'], validation_pairs=m['splits']['validation']['n_pairs'],
        effective_candidate_count=len(m['candidate_heads']), microbatches_per_epoch=len(micros), updates=n_updates,
        joint_forward_passes=len(micros)*args.epochs, validation_checkpoints=validations,
        validation_joint_passes=119*validations, baseline_readout_joint_passes=238,
        baseline_donor_readout_rows_reused=238, reference_cache_h_rows=238,
        reference_cache_fp32_bytes_expression='238 * model_config.vocab_size * 4 (readout only)',
        max_checkpoints=validations+2, target_completions=32, donor_completions=donors,
        max_new_tokens=(32+donors)*96, all_four_finalists_target_completions=160,
        safety_cluster_ids=ids, schedule='constant lr .03', no_optimizer_in_baseline=True,
        reference_cache_fp32_bytes=(238*json.loads((Path(args.model_path)/'config.json').read_text())['vocab_size']*4 if (Path(args.model_path)/'config.json').is_file() else None),
        training_joint_stream_tokens_per_epoch=sum(4*len(c['prompts']['original']['D']['clean']['input_ids']) for c in train['clusters']),
        baseline_max_new_tokens=(32+donors)*96,shared_generation_donor_score_passes=donors,
        reservation_gpu_hours='one GPU * root supplied walltime; measured receipt required')


def _baseline_fingerprint(identity):
    return sd.content_hash({k:v for k,v in identity.items() if k not in ('receipt','settings','optimizer')})


def _baseline(args, m, identity, ctx):
    fingerprint = _baseline_fingerprint(identity)
    path = args.output_dir / 'reference.pt'
    if path.exists():
        if not args.resume:
            raise FileExistsError('baseline exists; explicit --resume required')
        cache = _load_cache(path, fingerprint)
    else:
        cache = dict(fingerprint=fingerprint, baseline_path=BASELINE_PATH, splits={})
        for name, split in m['splits'].items():
            logits = _baseline_logits(ctx.node_model, split); labels = _labels(split)
            capable = logits['H'].argmax(-1) == labels['H']
            metrics = _metrics(logits['D'],logits['H'],logits['H'],labels,capable,update=0,removed=0)
            cache['splits'][name] = dict(h_logits=logits['H'], capable=capable,
                capability=_capability_report(split['clusters'], capable), metrics=metrics,
                donor_realization={'n':len(capable),'h_correct':int(capable.sum()),
                    'mapping_hash':split['donor_mapping_hash'],'note':'nonself donor is a permutation of these intact H rows'})
        _save_tensor(path,cache)
    generation = _generation_manifest(m, identity['receipt']['safety_cluster_ids'], 'baseline',
                                      {'baseline_fingerprint':fingerprint})
    _execute_generation(generation,ctx,args.output_dir/'generation',identity,{},args.resume)
    sr.atomic_json(args.output_dir/'baseline.json',dict(fingerprint=fingerprint,
        baseline_cache_sha256=_hash_file(path), baseline_generation_manifest_hash=generation['manifest_hash'],
        baseline_generation_fingerprint=sd.content_hash({'manifest':generation['manifest_hash'],'provenance':identity}),
        capability={s:c['capability'] for s,c in cache['splits'].items()},
        generation_headroom='requires frozen blinded annotations; never inferred from scores'))


def _checked_cache(args, identity):
    receipt=identity['receipt']; fp=_baseline_fingerprint(identity)
    if receipt['baseline_fingerprint'] != fp or _hash_file(args.reference_cache) != receipt['baseline_cache_sha256']:
        raise ValueError('baseline cache fingerprint/hash differs from passed receipt')
    cache = _load_cache(args.reference_cache,fp)
    if not all(x['capability']['usable'] for x in cache['splits'].values()):
        raise ValueError('global capable-H control unusable; stop without filtering')
    return cache


def _train(args,m,identity,ctx,cache):
    model=ctx.node_model
    params=sm.configure_candidate_gates(model,m['candidate_heads'])
    optimizer=_optimizer(params); fp=sd.content_hash(identity)
    micros=_microbatches(m['splits']['train'],args.joint_pairs)
    windows=[micros[i:i+args.accumulation] for i in range(0,len(micros),args.accumulation)]
    row_order=[i for group in micros for i in group]
    cursor=dict(epoch=0,window=0,update=0,history=[],row_order=row_order,loss_log=[])
    latest=args.output_dir/'latest.pt'
    if args.resume:
        cursor=_restore(latest,model,optimizer,fp)
        if cursor['row_order'] != row_order:
            raise ValueError('resume row order differs')
    elif latest.exists():
        raise FileExistsError('training exists; explicit --resume required')
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(args.seed)
    if args.resume:
        cursor=_restore(latest,model,optimizer,fp)  # restore RNG after initialization/seeding
    labels=_labels(m['splits']['train']); ref=cache['splits']['train']; device=next(model.parameters()).device
    model.train()
    if not args.resume: _checkpoint(latest,model,optimizer,cursor,fp)
    for epoch in range(cursor['epoch'],args.epochs):
        first=cursor['window'] if epoch==cursor['epoch'] else 0
        for w in range(first,len(windows)):
            batches=windows[w]; all_ids=[i for ids in batches for i in ids]
            n=len(all_ids); ncap=int(ref['capable'][all_ids].sum())
            optimizer.zero_grad(set_to_none=True)
            raw=dict(suppression_sum=0.,truth_sum=0.,kl_sum=0.,n_h=n,n_d=n,n_capable=ncap)
            try:
                for ids in batches:
                    d,h=_joint_logits(model,m['splits']['train'],ids)
                    loss=sm.pilot_loss(d,labels['D'][ids,None].to(device),h,ref['h_logits'][ids].to(device),
                        labels['H'][ids].to(device),ref['capable'][ids].to(device),_candidate_logits(model),rho=0.)
                    objective=_weighted_loss(loss,len(ids),n,ncap)
                    if not torch.isfinite(objective): raise FloatingPointError('nonfinite loss')
                    objective.backward()
                    raw['suppression_sum']+=float(loss.suppression.detach())*len(ids)
                    raw['truth_sum']+=float(loss.truth_nondegradation.detach())*len(ids)
                    raw['kl_sum']+=float(loss.capable_kl.detach())*loss.n_capable
                penalty=args.rho*torch.sigmoid(-_candidate_logits(model)).sum()
                if not torch.isfinite(penalty): raise FloatingPointError('nonfinite penalty')
                penalty.backward()
                if any(p.grad is not None and not torch.isfinite(p.grad).all() for p in params):
                    raise FloatingPointError('nonfinite gradient')
                torch.nn.utils.clip_grad_norm_(params,1.,error_if_nonfinite=True)
                optimizer.step()
            except (FloatingPointError,RuntimeError):
                # Preserve last complete update, not a partly accumulated objective.
                if latest.exists():
                    import shutil
                    shutil.copyfile(latest,args.output_dir/'failed-last-complete.pt')
                sr.atomic_json(args.output_dir/'failure.json',{'epoch':epoch,'window':w,'last_complete_update':cursor['update']})
                raise
            cursor.update(epoch=epoch,window=w+1,update=cursor['update']+1)
            raw['update']=cursor['update']; raw['expected_removed']=float(torch.sigmoid(-_candidate_logits(model)).sum().detach())
            cursor['loss_log'].append(raw)
            _checkpoint(latest,model,optimizer,cursor,fp)
        if (epoch+1)%args.validate_every==0 or epoch+1==args.epochs:
            metrics,exported=_validation(model,m['splits']['validation'],cache['splits']['validation'],cursor['update'],m['candidate_heads'],identity)
            checkpoint=args.output_dir/('validation-%06d.pt'%cursor['update'])
            metrics['checkpoint']=str(checkpoint.resolve()); metrics['export_hash']=exported['export_hash']
            cursor['history'].append(metrics)
            _checkpoint(checkpoint,model,optimizer,cursor,fp)
        cursor.update(epoch=epoch+1,window=0)
        _checkpoint(latest,model,optimizer,cursor,fp)
    selected=select_checkpoint(cursor['history'],cache['splits']['validation']['metrics'])
    sr.atomic_json(args.output_dir/'frontier.json',{'history':cursor['history'],'selected':selected,
        'status':'readout_selected_pending_generation_safety' if selected else 'failed_no_admissible_candidate',
        'automatic_retry':False})
    if selected:
        _restore(selected['checkpoint'],model,optimizer,fp)
        exported=sm.export_binary_masks(model,m['candidate_heads'],provenance=identity)
        if exported['export_hash'] != selected['export_hash']: raise ValueError('selected export mismatch')
        sr.atomic_json(args.output_dir/'selected-mask.json',exported)
        manifest=_generation_manifest(m,identity['receipt']['safety_cluster_ids'],'validation_safety',
            {'checkpoint':selected['checkpoint'],'run_fingerprint':fp}, {'rho'+str(args.rho):exported})
        sr.atomic_json(args.output_dir/'safety-manifest.json',manifest)


def _calibrate(args,m,identity,ctx,cache):
    from analysis import open_all_gates
    model=ctx.node_model; split=m['splits']['train']; labels=_labels(split)
    # Frozen first cluster in each structural length group, never chosen by outcomes.
    groups={}
    for i,c in enumerate(split['clusters']):
        groups.setdefault(len(c['prompts']['original']['D']['clean']['input_ids']),i)
    representatives=[groups[k] for k in sorted(groups)]
    if len(representatives)>5: raise ValueError('unexpected calibration length groups')
    state={n:p.detach().clone() for n,p in model.named_parameters() if p.requires_grad}
    cpu_rng=torch.get_rng_state(); cuda_rng=torch.cuda.get_rng_state_all() if torch.cuda.is_available() else []
    training=model.training; checks=[]; hooks=[]; elapsed=0.
    try:
        for i in representatives:
            with _preserve_gates(model),torch.no_grad():
                open_all_gates(model)
                ad,ah=_joint_logits(model,split,[i],self_donor=True)
                rd,rh=_joint_logits(model,split,[i],self_donor=True)
            a={'D':ad.cpu(),'H':ah.cpu()}
            with _preserve_gates(model),torch.no_grad():
                open_all_gates(model); bd,bh=_joint_logits(model,split,[i])
            model.train()
            def force_open(module,inputs,out):
                forced=out+(torch.ones_like(out)-out).detach()
                if not torch.equal(forced.detach(),torch.ones_like(out)): raise ValueError('forced-open gate failed')
                return forced
            for layer in model.model.layers:
                gate=layer.attn.head_gates
                if gate.eligibility is not None and gate.eligibility.any():
                    hooks.append(gate.register_forward_hook(force_open))
            torch.cuda.synchronize(); start=time.monotonic()
            cd,ch=_joint_logits(model,split,[i]); device=ch.device
            loss=sm.pilot_loss(cd,labels['D'][[i],None].to(device),ch,a['H'].to(device),
                labels['H'][[i]].to(device),cache['splits']['train']['capable'][[i]].to(device),
                _candidate_logits(model),rho=args.rho)
            loss.total.backward(); torch.cuda.synchronize(); elapsed+=time.monotonic()-start
            for hook in hooks: hook.remove()
            hooks=[]
            pairs={}
            for name,x,y in [('self_vs_nonself_D',a['D'],bd.detach().cpu()),('self_vs_nonself_H',a['H'],bh.detach().cpu()),
                              ('eval_vs_grad_D',bd.detach().cpu(),cd.detach().cpu()),('eval_vs_grad_H',bh.detach().cpu(),ch.detach().cpu()),
                              ('repeat_D',a['D'],rd.cpu()),('repeat_H',a['H'],rh.cpu())]:
                difference=(x-y).abs()
                pairs[name]=dict(max_abs_full_vocab=float(difference.max()),mean_abs_full_vocab=float(difference.mean()),
                    changed_entries=int((difference>0).sum()),
                    max_abs_label_logits=float(difference[:,[labels['D'][i],labels['H'][i]]].max()),
                    finite_logits=bool(torch.isfinite(x).all() and torch.isfinite(y).all()),
                    argmax_flip=bool(x.argmax(-1)!=y.argmax(-1)),
                    d_probability=[float(F.softmax(z.float(),-1)[0,labels['D'][i]]) for z in (x,y)],
                    h_probability=[float(F.softmax(z.float(),-1)[0,labels['H'][i]]) for z in (x,y)])
            finite=bool(torch.isfinite(loss.total) and all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters()))
            candidate_signal=False; isolation=True
            for layer in model.model.layers:
                gate=layer.attn.head_gates
                if gate.log_alpha.grad is not None:
                    isolation=isolation and not bool(gate.log_alpha.grad[~gate.eligibility].any())
                    candidate_signal=candidate_signal or bool(gate.log_alpha.grad[gate.eligibility].any())
            isolation=isolation and all(p.grad is None for p in model.parameters() if not p.requires_grad)
            floors={}
            for name,xd,xh,yd,yh in [('self_to_nonself',a['D'],a['H'],bd.detach().cpu(),bh.detach().cpu()),('eval_to_grad',bd.detach().cpu(),bh.detach().cpu(),cd.detach().cpu(),ch.detach().cpu())]:
                measure=sm.pilot_loss(yd,labels['D'][[i],None],yh,xh,labels['H'][[i]],cache['splits']['train']['capable'][[i]],torch.empty(0),rho=0.)
                prior=sm.pilot_loss(xd,labels['D'][[i],None],xh,xh,labels['H'][[i]],cache['splits']['train']['capable'][[i]],torch.empty(0),rho=0.)
                floors[name]=dict(h_kl=float(measure.capable_kl),h_truth_nondegradation=float(measure.truth_nondegradation),d_surrogate_delta=float(measure.suppression-prior.suppression))
            checks.append(dict(finite_loss_and_gradients=finite,gradient_isolation=isolation,candidate_nonzero_gradient=candidate_signal,loss_floors=floors,cluster_id=split['clusters'][i]['cluster_id'],length=len(split['clusters'][i]['prompts']['original']['D']['clean']['input_ids']),
                comparisons=pairs,capability_flip=bool((a['H'].argmax(-1)==labels['H'][i]) != (ch.detach().cpu().argmax(-1)==labels['H'][i])),
                actual_kl=float(loss.capable_kl.detach()),actual_nondegradation=float(loss.truth_nondegradation.detach())))
            model.zero_grad(set_to_none=True)
    finally:
        for hook in hooks: hook.remove()
        model.zero_grad(set_to_none=True); model.train(training); torch.set_rng_state(cpu_rng)
        if cuda_rng: torch.cuda.set_rng_state_all(cuda_rng)
    if any(not torch.equal(dict(model.named_parameters())[n],p) for n,p in state.items()):
        raise ValueError('calibration changed parameters')
    no_op=None
    if 'validation' in cache['splits']:
        no_op,_=_validation(model,m['splits']['validation'],cache['splits']['validation'],0,m['candidate_heads'],identity)
        baseline=cache['splits']['validation']['metrics']
        no_op['all_h_argmax_preserved']=no_op['h_argmax_ids']==baseline['h_argmax_ids']
        no_op['all_d_argmax_preserved']=no_op['d_argmax_ids']==baseline['d_argmax_ids']
        no_op['max_abs_label_logits']=max(float((torch.tensor(no_op[k])-torch.tensor(baseline[k])).abs().max()) for k in ('d_label_logits','h_label_logits'))
    gate=all(c['finite_loss_and_gradients'] and c['gradient_isolation'] and c['candidate_nonzero_gradient'] and not c['capability_flip'] and all(p['finite_logits'] and not p['argmax_flip'] and p['max_abs_label_logits']<=.02 for p in c['comparisons'].values()) for c in checks)
    model.train(training)
    if no_op is not None: gate=gate and no_op['all_h_argmax_preserved'] and no_op['all_d_argmax_preserved'] and no_op['max_abs_label_logits']<=.02
    sr.atomic_json(args.output_dir/'calibration.json',dict(numerical_checks=checks,optimizer_steps=0,
        fixed_label_logit_tolerance=.02,numerical_gate_passed=gate,validation_no_op=no_op,
        total_forced_open_forward_backward_seconds=elapsed,peak_cuda_bytes=torch.cuda.max_memory_allocated(),
        decision='root review required; no tolerance widening or automatic fit'))


def _prepare(args):
    from datasets import load_from_disk
    from transformers import AutoTokenizer
    from evaluation.circuits import resolve_circuit_specs
    stage=json.loads(args.stage1_manifest.read_text()); binding=json.loads(args.candidate_bindings.read_text())
    tokenizer=AutoTokenizer.from_pretrained(args.model_path,local_files_only=True)
    specs,bindings,_,_,_=resolve_circuit_specs(circuit=[k+'='+v for k,v in binding['bindings'].items()],
        expr=['candidate=(D|H|F)-m'],compose_granularity='leaf')
    heads=[[int(l),h] for l,values in specs[0].masks['attention_heads'].items() for h,value in enumerate(values) if value]
    records={s:[dict(r) for r in load_from_disk(str(args.data_dir/s))] for s in ('train','validation','test')}
    metadata=dict(binding['source_metadata'],stage1_manifest_path=str(args.stage1_manifest.resolve()),
                  candidate_bindings=bindings,tokenizer=str(Path(args.model_path).resolve()))
    m=sm.build_pilot_manifest(records,json.loads(args.honest_pool.read_text())['instructions'],tokenizer,
        stage1_manifest=stage,candidate_heads=heads,source_metadata=metadata)
    # Enforce the eight final audit pins before any immutable save.
    if m['candidate_heads_hash']!=CANDIDATE_HASH or any([m['splits'][s][k] for k in AUDIT_KEYS]!=AUDIT[s] for s in AUDIT):
        raise ValueError('prepared inputs differ from frozen audit')
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    with args.manifest.open('x') as f: f.write(sd.canonical_json(m)+'\n')


def _run(args):
    if args.prepare:
        _prepare(args); return 0
    m=_read_manifest(args.manifest); plan=_plan(args,m)
    if args.dry_run:
        print(json.dumps(plan,sort_keys=True)); return 0
    mode='baseline' if args.baseline else 'calibrate' if args.calibrate else 'train' if args.train else 'evaluate'
    receipt=_receipt(args.freeze_record,m,mode)
    if args.device!='cuda' or not torch.cuda.is_available():
        raise ValueError('real model work requires a root-launched CUDA allocation')
    if mode in ('train','calibrate') and 'A100' in torch.cuda.get_device_name(0):
        raise ValueError('8B backward requires A40/H200; A100 training forbidden')
    if mode in ('train','calibrate','evaluate'):
        settings={k:getattr(args,k) for k in ('seed','epochs','validate_every','joint_pairs','accumulation')}
        if receipt.get('training_settings') != settings or args.rho not in receipt.get('allowed_rhos',[]):
            raise ValueError('settings differ from root frozen equal-budget batch')
    if mode=='train' and receipt.get('numerical_calibration')!='passed':
        raise ValueError('root numerical calibration decision missing')
    identity=_identity(args,m,receipt)
    ctx,masks=_runtime(args,identity)
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    if mode=='baseline':
        _baseline(args,m,identity,ctx); return 0
    if mode=='evaluate':
        manifest=json.loads(args.evaluation_manifest.read_text())
        params=sm.configure_candidate_gates(ctx.node_model,m['candidate_heads'])
        cursor=_restore(args.checkpoint,ctx.node_model,_optimizer(params),sd.content_hash(identity))
        expected=sm.export_binary_masks(ctx.node_model,m['candidate_heads'],provenance=identity)
        # Bind immutable derived masks to the selected checkpoint; weights never fit here.
        for name,export in manifest.get('learned_masks',{}).items():
            if export != expected:
                approved=receipt.get('evaluation_checkpoints',{}).get(export['export_hash'])
                provenance=export['provenance']
                if manifest['pilot_purpose']!='final_test' or not approved or provenance['settings']['rho']!=0:
                    raise ValueError('learned mask differs from selected checkpoint export')
                if _baseline_fingerprint(provenance)!=_baseline_fingerprint(identity):
                    raise ValueError('rho0 comparator baseline identity differs')
                if sd.content_hash(provenance)!=approved['fingerprint']:
                    raise ValueError('rho0 comparator provenance differs from root pin')
                other_cursor=_restore(approved['checkpoint'],ctx.node_model,_optimizer(params),approved['fingerprint'])
                other_selected=select_checkpoint(other_cursor['history'],_checked_cache(args,identity)['splits']['validation']['metrics'])
                if not other_selected or Path(other_selected['checkpoint']).resolve()!=Path(approved['checkpoint']).resolve():
                    raise ValueError('rho0 comparator is not selected')
                if sm.export_binary_masks(ctx.node_model,m['candidate_heads'],provenance=provenance)!=export:
                    raise ValueError('rho0 mask differs from selected checkpoint export')
            masks[name]=export['removal_mask']
        if manifest['pilot_purpose']=='final_test' and (receipt.get('final_assessment')!='passed_validation_safety' or receipt.get('final_evaluation_manifest_hash') != manifest['manifest_hash']):
            raise ValueError('final test requires root frozen validation-safety decision')
        selected=select_checkpoint(cursor.get('history',[]),_checked_cache(args,identity)['splits']['validation']['metrics'])
        if not selected or Path(selected['checkpoint']).resolve()!=args.checkpoint.resolve():
            raise ValueError('evaluation checkpoint is not the readout-selected finalist')
        if manifest['pilot_purpose']=='validation_safety':
            expected_manifest=_generation_manifest(m,identity['receipt']['safety_cluster_ids'],'validation_safety',
                {'checkpoint':selected['checkpoint'],'run_fingerprint':sd.content_hash(identity)}, {'rho'+str(args.rho):expected})
            if manifest!=expected_manifest: raise ValueError('safety manifest differs from frozen selected finalist')
        _execute_generation(manifest,ctx,args.output_dir/'evaluation',identity,masks,args.resume); return 0
    cache=_checked_cache(args,identity)
    if mode=='calibrate':
        sm.configure_candidate_gates(ctx.node_model,m['candidate_heads'])
        _calibrate(args,m,identity,ctx,cache)
    else: _train(args,m,identity,ctx,cache)
    return 0


def run_cli(args):
    if args.prepare or args.dry_run:
        return _run(args)
    import fcntl
    args.output_dir.mkdir(parents=True,exist_ok=True)
    with (args.output_dir/'writer.lock').open('a') as lock:
        try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc: raise ValueError('output has an active writer') from exc
        return _run(args)
