"""Small CPU data/loss/export seam for the conditional selective-removal pilot.

No outcome selection, model loading, training loop or compute-path decision lives
here. Hashes guard frozen serialization; they do not attest a malicious author.
"""
from __future__ import annotations

import copy
import itertools
import math
from collections import Counter, defaultdict
from dataclasses import dataclass

import torch
import torch.nn.functional as F

from evaluation import selective_diagnostics as sd
from l0 import HardConcreteGate

Head = tuple[int, int]
VIEWS = ('original', 'reversed', 'free_response', 'alternative')
R1_MANIFEST_HASH = '29da71bd7cef5f03bec931e5a4231cb93b3bfb026ce3b00f1ea3367a6aab95a0'
R1_EXPOSURE_HASH = 'b2e4c7630552ae1fc12d62d0b90d21b6d653fe2801ecacedad37f4e367b49e10'
DECLARATIONS = {'original_dataset_outcome_filtered': True, 'new_outcome_screening': False,
                'uses_matched_honest_survivor_list': False}


def _heads(heads):
    result = [list(h) for h in heads]
    if (not result or any(len(h) != 2 or any(type(i) is not int or i < 0 for i in h) for h in result)
            or len({tuple(h) for h in result}) != len(result)):
        raise ValueError('candidate heads must be unique nonnegative integer pairs')
    return sorted(result)


def _exposure(stage1, tokenizer):
    if stage1['manifest_hash'] != sd.manifest_hash(stage1):
        raise ValueError('Stage 1 manifest hash mismatch')
    clusters = {c['cluster_id']: c for c in stage1['clusters']}
    endpoints = [r[k] for r in stage1['rows'] for k in ('recipient', 'donor') if r.get(k)]
    endpoints += [r['prompt'] for r in stage1['donor_reference_rows']]
    scenarios = {}
    for p in endpoints:
        c = clusters[p['cluster_id']]
        if p['stream'] not in ('clean', 'corrupt'):
            raise ValueError('unknown exposed stream')
        if p['source_id'] != c['source_id']:
            raise ValueError('exposure source mismatch')
        expected = sd._endpoint(c, p['policy'], p['stream'], p['view'])
        if any(p[k] != v for k, v in expected.items()):
            raise ValueError('Stage 1 endpoint does not match its cluster')
        if tokenizer.encode(p['text'], add_special_tokens=False) != p['input_ids']:
            raise ValueError('Stage 1 tokenization mismatch')
        scenario = copy.deepcopy(c['scenario'])
        scenario['honest_item'] = c['labels']['H' if p['stream'] == 'clean' else 'D']['text']
        scenarios[sd.content_hash(scenario)] = scenario
    return [scenarios[k] for k in sorted(scenarios)], copy.deepcopy(endpoints)


def _split_hashes(clusters, donors):
    return {'representative_mapping_hash': sd.content_hash({c['cluster_id']: c['source_id'] for c in clusters}),
            'donor_mapping_hash': sd.content_hash(donors),
            'allview_clean_endpoint_hash': sd.content_hash({c['cluster_id']: {
                v: {p: c['prompts'][v][p]['clean']['text_hash'] for p in ('D', 'H')}
                for v in VIEWS} for c in clusters}), 'clusters_hash': sd.content_hash(clusters)}


def _coverage(clusters):
    counts = Counter(tuple(c['stratum']) for c in clusters)
    return {'|'.join(map(str, k)): counts[k] for k in itertools.product(
        ('identity', 'inversion'), (1, 2), ('audit', 'lab'))}


def build_pilot_manifest(records_by_split: dict, honest_pool: dict, tokenizer, *,
                         stage1_manifest: dict, candidate_heads: list[Head], source_metadata: dict) -> dict:
    """Reserve raw splits, actual exposure, then preflight/dedup/rotate locally.

    A same-path successor requires explicit root lineage metadata AND the same
    exposure hash. Root must additionally verify unchanged rows/donors/tokens
    against r1 before approving that metadata; this helper never invents approval.
    """
    records = copy.deepcopy(records_by_split)
    metadata = copy.deepcopy(source_metadata)
    stage_hash = stage1_manifest['manifest_hash']
    lineage = metadata.get('stage1_lineage')
    if stage_hash != R1_MANIFEST_HASH and not (
            lineage and lineage.get('original_manifest_hash') == R1_MANIFEST_HASH
            and lineage.get('approved_manifest_hash') == stage_hash and lineage.get('root_decision')
            and lineage.get('inputs_unchanged_from_r1') is True):
        raise ValueError('unapproved Stage 1 lineage')
    scenarios, endpoints = _exposure(stage1_manifest, tokenizer)
    exposed = {sd.content_hash(s) for s in scenarios}
    if sd.content_hash(sorted(exposed)) != R1_EXPOSURE_HASH:
        raise ValueError('frozen Stage 1 exposed scenario set mismatch')
    raw = {s: {sd.content_hash(sd._scenario(r)) for r in records[s]}
           for s in ('train', 'validation', 'test')}
    m = {'version': 1, 'stage1_manifest_hash': stage_hash,
         'stage1_original_manifest_hash': R1_MANIFEST_HASH,
         'exposed_scenarios': scenarios, 'exposed_scenario_set_hash': sd.content_hash(sorted(exposed)),
         'stage1_endpoints': endpoints, 'stage1_endpoints_hash': sd.content_hash(endpoints),
         'candidate_heads': _heads(candidate_heads), 'source_metadata': metadata,
         'source_metadata_hash': sd.content_hash(metadata), 'source_records': records,
         'source_records_hash': sd.content_hash(records), 'matched_honest_pool': copy.deepcopy(honest_pool),
         'matched_honest_pool_hash': sd.content_hash(honest_pool), 'declarations': dict(DECLARATIONS),
         'raw_scenario_reservations': {s: sorted(raw[s]) for s in raw}, 'splits': {}, 'exclusions': []}
    m['candidate_heads_hash'] = sd.content_hash(m['candidate_heads'])
    for split, higher in (('train', ('test', 'validation')), ('validation', ('test',))):
        forbidden = set().union(*(raw[s] for s in higher))
        kept, grouped = [], defaultdict(list)
        def exclude(r, reason, **extra):
            m['exclusions'].append({'split': split, 'source_id': r.get('instance_id', r.get('source_id')),
                                    'cluster_id': sd.content_hash(sd._scenario(r)) if 'instance_id' in r else r['cluster_id'],
                                    'reason': reason, **extra})
        for r in records[split]:
            key = sd.content_hash(sd._scenario(r))
            if key in forbidden:
                exclude(r, 'raw_split_precedence')
            elif key in exposed:
                exclude(r, 'stage1_exposure')
            else:
                kept.append(r)
                try:
                    c = sd._preflight(r, honest_pool, tokenizer, 512, 96)
                except (ValueError, KeyError, AssertionError) as exc:
                    exclude(r, 'structural_preflight', detail=str(exc))
                    continue
                c['cluster_id'] = key
                grouped[key].append(c)
        clusters, counts = [], Counter()
        for key, members in sorted(grouped.items()):
            c = min(members, key=lambda x: (counts[tuple(x['stratum'])], x['source_id']))
            counts[tuple(c['stratum'])] += 1
            c['member_source_ids'] = sorted(x['source_id'] for x in members)
            clusters.append(c)
            for other in members:
                if other is not c:
                    exclude(other, 'representative_omission', selected_source_id=c['source_id'])
        signatures = Counter(sd._signature(c) for c in clusters)
        for c in clusters:
            if signatures[sd._signature(c)] < 2:
                exclude(c, 'singleton_signature')
        clusters = [c for c in clusters if signatures[sd._signature(c)] >= 2]
        if not clusters:
            raise ValueError('no alignment-compatible clusters in ' + split)
        donors = sd._derangement(clusters)
        m['splits'][split] = {'clusters': clusters, 'donor_map': donors,
                              'retained_records_hash': sd.content_hash(kept),
                              'n_pairs': len(clusters), 'coverage': _coverage(clusters),
                              **_split_hashes(clusters, donors)}
    m['manifest_hash'] = sd.manifest_hash(m)
    validate_pilot_manifest(m)
    return m


def validate_pilot_manifest(manifest: dict) -> None:
    """Check frozen serialization and relational isolation without a tokenizer."""
    try:
        _validate(manifest)
    except (KeyError, TypeError, AssertionError, IndexError) as exc:
        raise ValueError('invalid pilot manifest: ' + str(exc)) from exc


def _validate(m):
    if m['version'] != 1 or m['manifest_hash'] != sd.manifest_hash(m):
        raise ValueError('pilot manifest hash/version mismatch')
    if m['declarations'] != DECLARATIONS:
        raise ValueError('fixed scientific declarations mismatch')
    for key in ('source_metadata', 'source_records', 'matched_honest_pool', 'candidate_heads', 'stage1_endpoints'):
        if m[key + '_hash'] != sd.content_hash(m[key]):
            raise ValueError(key + ' hash mismatch')
    if m['candidate_heads'] != _heads(m['candidate_heads']):
        raise ValueError('candidate binding mismatch')
    exposed = {sd.content_hash(s) for s in m['exposed_scenarios']}
    if m['exposed_scenario_set_hash'] != sd.content_hash(sorted(exposed)) or m['exposed_scenario_set_hash'] != R1_EXPOSURE_HASH:
        raise ValueError('exposure hash mismatch')
    if m['stage1_original_manifest_hash'] != R1_MANIFEST_HASH:
        raise ValueError('original lineage mismatch')
    if m['stage1_manifest_hash'] != R1_MANIFEST_HASH:
        line = m['source_metadata']['stage1_lineage']
        if not (line['original_manifest_hash'] == R1_MANIFEST_HASH
                and line['approved_manifest_hash'] == m['stage1_manifest_hash']
                and line['root_decision'] and line['inputs_unchanged_from_r1'] is True):
            raise ValueError('successor lineage mismatch')
    reservations = {s: {sd.content_hash(sd._scenario(r)) for r in m['source_records'][s]}
                    for s in ('train', 'validation', 'test')}
    if m['raw_scenario_reservations'] != {s: sorted(v) for s, v in reservations.items()}:
        raise ValueError('raw reservation mismatch')
    endpoint_sets = (set(exposed), {p['text'] for p in m['stage1_endpoints']},
                     {tuple(p['input_ids']) for p in m['stage1_endpoints']})
    for p in m['stage1_endpoints']:
        sd._check_prompt(p, 512)
    previous = endpoint_sets
    for split, higher in (('train', ('test', 'validation')), ('validation', ('test',))):
        data = m['splits'][split]
        clusters, donors = data['clusters'], data['donor_map']
        if any(data[k] != v for k, v in _split_hashes(clusters, donors).items()):
            raise ValueError('frozen cluster/donor hashes mismatch')
        if [c['cluster_id'] for c in clusters] != sorted(c['cluster_id'] for c in clusters):
            raise ValueError('cluster ordering mismatch')
        if donors != sd._derangement(clusters):
            raise ValueError('deterministic donor rotation mismatch')
        ids = {c['cluster_id'] for c in clusters}
        if (len(ids) != len(clusters) or len(ids) != data['n_pairs'] or not ids
                or set(donors) != ids or set(donors.values()) != ids
                or data['coverage'] != _coverage(clusters)):
            raise ValueError('cluster/donor/count mismatch')
        if ids & set().union(*(reservations[s] for s in higher)):
            raise ValueError('raw split intersection')
        source = {r['instance_id']: r for r in m['source_records'][split]}
        if len(source) != len(m['source_records'][split]):
            raise ValueError('duplicate source IDs')
        texts, tokens, by_id = set(), set(), {c['cluster_id']: c for c in clusters}
        for c in clusters:
            r = source[c['source_id']]
            if c['scenario'] != sd._scenario(r) or sd.content_hash(c['scenario']) != c['cluster_id']:
                raise ValueError('scenario/source mismatch')
            if c['labels']['D']['text'] != r['target'] or c['labels']['H']['text'] != r['distractor']:
                raise ValueError('label mismatch')
            if c['labels']['D']['token_id'] == c['labels']['H']['token_id']:
                raise ValueError('label token collision')
            for policy in ('D', 'H'):
                for stream in ('clean', 'corrupt'):
                    original = r[stream + '_prompt']
                    if policy == 'H':
                        entry = m['matched_honest_pool'][r['pressure_id']]
                        marker = ' ' + r['pressure'] + '<|eot_id|>'
                        if entry['pressure'] != r['pressure'] or original.count(marker) != 1:
                            raise ValueError('honest instruction source mismatch')
                        original = original.replace(marker, ' ' + entry['instruction'] + '<|eot_id|>', 1)
                    for view in VIEWS:
                        prompt = c['prompts'][view][policy][stream]
                        sd._check_prompt(prompt, 128 if view in VIEWS[:2] else 416)
                        if prompt['text'] != sd._transform(original, r, view):
                            raise ValueError('literal source/transform mismatch')
            d = by_id[donors[c['cluster_id']]]
            if c['cluster_id'] == d['cluster_id'] or c['source_id'] == d['source_id']:
                raise ValueError('self donor')
            for view in VIEWS:
                donor = d['prompts'][view]['H']['clean']
                for policy in ('D', 'H'):
                    p = c['prompts'][view][policy]['clean']
                    sd._check_prompt(p, 128 if view in VIEWS[:2] else 416)
                    if p['text'] == donor['text'] or p['length'] != donor['length'] or p['attention_mask'] != donor['attention_mask']:
                        raise ValueError('twin/donor alignment mismatch')
                    texts.add(p['text'])
                    tokens.add(tuple(p['input_ids']))
        current = (ids, texts, tokens)
        if any(a & b for a, b in zip(current, previous)) or any(a & b for a, b in zip(current, endpoint_sets)):
            raise ValueError('semantic/text/token intersection or collision')
        previous = current


@dataclass
class PilotLoss:
    total: torch.Tensor
    suppression: torch.Tensor
    capable_kl: torch.Tensor
    truth_nondegradation: torch.Tensor
    expected_removed: torch.Tensor
    n_h: int
    n_capable: int


def pilot_loss(d_logits, deceptive_token_ids, h_logits, h_base_logits, truthful_token_ids,
               capable, candidate_logits, *, rho: float, beta_kl: float = 1., beta_label: float = 1.) -> PilotLoss:
    """Separate condition means; callers aggregate KL using n_capable, H using n_h.

    Empty *minibatch* capability returns zero KL. The runner must reject an empty
    global capable set and weight accumulated minibatch terms by global counts.
    """
    d, h, base = d_logits.float(), h_logits.float(), h_base_logits.detach().float()
    if (d.ndim != 2 or h.ndim != 2 or base.shape != h.shape or d.shape[1] != h.shape[1]
            or len(d) == 0 or len(h) == 0 or capable.dtype != torch.bool
            or capable.shape != (len(h),) or truthful_token_ids.shape != (len(h),)
            or deceptive_token_ids.ndim != 2 or deceptive_token_ids.shape[0] != len(d)
            or deceptive_token_ids.shape[1] == 0 or candidate_logits.ndim != 1
            or min(rho, beta_kl, beta_label) < 0):
        raise ValueError('invalid pilot loss inputs')
    deceptive = torch.zeros_like(d, dtype=torch.bool).scatter_(1, deceptive_token_ids, True)
    if deceptive.all(dim=1).any():
        raise ValueError('deceptive alternatives must leave at least one other token')
    suppression = (torch.logsumexp(d, dim=-1) - torch.logsumexp(d.masked_fill(deceptive, -torch.inf), dim=-1)).mean()
    n_capable = int(capable.sum().item())
    kl = (F.kl_div(F.log_softmax(h[capable], dim=-1), F.softmax(base[capable], dim=-1),
                   reduction='sum') / n_capable if n_capable else h.sum() * 0.)
    truth = F.relu(F.cross_entropy(h, truthful_token_ids, reduction='none') -
                   F.cross_entropy(base, truthful_token_ids, reduction='none')).mean()
    removed = torch.sigmoid(-candidate_logits.float()).sum()
    return PilotLoss(suppression + beta_kl * kl + beta_label * truth + rho * removed,
                     suppression, kl, truth, removed, len(h), n_capable)


def _head_gates(model, heads):
    candidates = _heads(heads)
    gates = [layer.attn.head_gates for layer in model.model.layers]
    if any(g is None for g in gates) or any(l >= len(gates) or h >= gates[l].num_gates() for l, h in candidates):
        raise ValueError('candidate head outside configured query-head gates')
    return candidates, gates


def configure_candidate_gates(model, candidate_heads: list[Head], *, expected_initial_removed: float = 1.) -> list[torch.nn.Parameter]:
    """Only eligible head entries optimize; optimizer must use weight_decay=0.

    All other existing granularities are explicitly hard-open, including in tiny
    models constructed with the historical broad default pruning config.
    Configure the same eligibility before strict checkpoint loading.
    """
    heads, gates = _head_gates(model, candidate_heads)
    if not 0 < expected_initial_removed < len(heads):
        raise ValueError('initial expected removal must be between zero and candidate count')
    for p in model.parameters():
        p.requires_grad_(False)
    for module in model.modules():
        if isinstance(module, HardConcreteGate):
            module.set_eligibility(torch.zeros_like(module.log_alpha, dtype=torch.bool))
    params = []
    initial = math.log((len(heads) - expected_initial_removed) / expected_initial_removed)
    for layer, gate in enumerate(gates):
        eligible = torch.zeros_like(gate.log_alpha, dtype=torch.bool)
        for l, h in heads:
            if l == layer:
                eligible[h] = True
        gate.set_eligibility(eligible)
        if eligible.any():
            gate.log_alpha.data = gate.log_alpha.data.float()
            with torch.no_grad():
                gate.log_alpha[eligible] = initial
            gate.log_alpha.requires_grad_(True)
            params.append(gate.log_alpha)
    return params


def export_binary_masks(model, candidate_heads: list[Head], *, provenance: dict) -> dict:
    """Export actual eval K and head-only R; zero MLP membership for knockout."""
    heads, gates = _head_gates(model, candidate_heads)
    keep, removed, eligibility, logits, ids = {}, {}, {}, {}, []
    for l, gate in enumerate(gates):
        expected = torch.tensor([(l, h) in {tuple(x) for x in heads} for h in range(gate.num_gates())],
                                dtype=torch.bool, device=gate.log_alpha.device)
        if gate.eligibility is None or not torch.equal(gate.eligibility, expected):
            raise ValueError('export candidate eligibility mismatch')
        # Mirror eval forward exactly (including log_alpha == 0), without
        # mutating the model training mode or drawing random gates.
        soft = (torch.sigmoid(gate.log_alpha.detach()) * (gate.zeta - gate.gamma) + gate.gamma).clamp(0, 1)
        k = torch.where(expected, (soft > .5).float(), torch.ones_like(soft)).int().cpu().tolist()
        key = str(l)
        keep[key], removed[key] = k, [1 - x for x in k]
        eligibility[key] = expected.cpu().tolist()
        logits[key] = gate.log_alpha.detach().cpu().tolist()
        ids += [[l, h] for h, value in enumerate(k) if not value]
    mask = {'attention_heads': removed,
            'attention_blocks': [0] * len(gates), 'mlp_blocks': [0] * len(gates),
            'attention_neurons': {str(l): [int(v) for v in torch.tensor(removed[str(l)]).repeat_interleave(
                model.model.layers[l].attn.head_dim).tolist()] for l in range(len(gates))},
            'mlp_hidden': {str(l): [0] * model.config.intermediate_size for l in range(len(gates))},
            'mlp_output': {str(l): [0] * model.config.hidden_size for l in range(len(gates))}}
    result = {'K': keep, 'R': removed, 'removed_heads': ids, 'removal_mask': mask,
              'eligibility': eligibility, 'logits': logits, 'candidate_heads': heads,
              'candidate_heads_hash': sd.content_hash(heads), 'effective_candidate_count': len(heads),
              'provenance': copy.deepcopy(provenance), 'provenance_hash': sd.content_hash(provenance)}
    result['export_hash'] = sd.content_hash(result)
    return result


def amended_objective(loss, *, arm, n_d, total_d, total_h, total_capable,
                      w_kl_sum=None, w_nll_sum=None, w_base_nll_sum=None, w_tokens=None):
    """One microbatch contribution, with update-level observation denominators.

    WikiText sums describe one entire window, so its hinge is applied after the
    token mean. Penalty is added once by the runner, outside accumulation.
    """
    if arm not in ('H', 'W', 'HW') or min(n_d, total_d, total_h) <= 0 or total_capable < 0:
        raise ValueError('invalid amended objective units')
    result = loss.suppression * n_d / total_d
    if arm in ('H', 'HW'):
        ch = (loss.capable_kl * loss.n_capable / max(total_capable, 1)
              + loss.truth_nondegradation * loss.n_h / total_h) / 2
        result = result + ch * (1. if arm == 'H' else .5)
    if w_kl_sum is not None:
        if arm == 'H' or w_tokens is None or w_tokens <= 0:
            raise ValueError('unexpected WikiText contribution')
        cw = (w_kl_sum / w_tokens + F.relu(w_nll_sum / w_tokens - w_base_nll_sum / w_tokens)) / 2
        result = result + cw * (1. if arm == 'W' else .5)
    return result
