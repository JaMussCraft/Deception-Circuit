"""CPU-only, hash-bound adapters for frozen whole-query-head removals.

Returned masks describe the circuit TO REMOVE. Consumers must use finest
knockout: MLP leaves in this circuit are zero, hence remain open after removal.
Checkpoint files are hashed as bytes and are never deserialized.
"""
from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from pathlib import Path

import numpy as np
from evaluation.masks import as_arrays, knockout_masks, validate_hierarchy

SCHEMA_VERSION = 1
SELECTION_SHA256 = '3b095b5774e7521080de92a7af94243acd76e4df9725541f8ce61f55ff23f525'
OLD_D_SHA256 = '110a7a87bd2bf5dc9abdffa6d0efed20549b0dd4b2319ebfb0f57cdc8126c536'
GEOMETRY = dict(num_layers=32, num_heads=32, head_dim=128,
                hidden_size=4096, intermediate_size=14336)
RANDOM_SEED = 20261024
MASK_KEYS = {'attention_blocks', 'attention_heads', 'attention_neurons',
             'mlp_hidden', 'mlp_output'}


def file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def binding(path):
    return dict(path=str(Path(path).resolve()), sha256=file_hash(path))


def check_binding(value):
    if file_hash(value['path']) != value['sha256']:
        raise ValueError('source hash mismatch: ' + value['path'])
    return Path(value['path'])


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode('utf-8')).hexdigest()


def validate_heads(heads, geometry=GEOMETRY):
    if not isinstance(heads, list) or any(
        not isinstance(pair, list) or len(pair) != 2
        or any(type(i) is not int for i in pair)
        or not 0 <= pair[0] < geometry['num_layers']
        or not 0 <= pair[1] < geometry['num_heads'] for pair in heads
    ) or len({tuple(p) for p in heads}) != len(heads):
        raise ValueError('invalid or duplicate query heads')
    return sorted(heads)


def layer_matched_random(heads, geometry=GEOMETRY, seed=RANDOM_SEED):
    """One draw from ALL query heads, including any originally selected head."""
    heads = validate_heads(heads, geometry)
    rng = random.Random(seed)
    counts = Counter(layer for layer, _ in heads)
    return sorted([[layer, head] for layer, count in sorted(counts.items())
                   for head in rng.sample(range(geometry['num_heads']), count)])


def heads_to_leaf_masks(heads, geometry=GEOMETRY):
    heads = validate_heads(heads, geometry)
    g = geometry
    if any(type(v) is not int or v <= 0 for v in g.values()) or g['hidden_size'] != g['num_heads'] * g['head_dim']:
        raise ValueError('inconsistent model geometry')
    chosen = set(map(tuple, heads))
    masks = dict(attention_blocks=np.ones(g['num_layers'], dtype=np.uint8),
                 attention_heads={}, attention_neurons={}, mlp_hidden={}, mlp_output={})
    for layer in range(g['num_layers']):
        key = str(layer)
        h = np.array([(layer, head) in chosen for head in range(g['num_heads'])], dtype=np.uint8)
        masks['attention_heads'][key] = h
        masks['attention_neurons'][key] = np.repeat(h, g['head_dim'])
        masks['mlp_hidden'][key] = np.zeros(g['intermediate_size'], dtype=np.uint8)
        masks['mlp_output'][key] = np.zeros(g['hidden_size'], dtype=np.uint8)
    validate_effective_removal(masks, heads, geometry)
    return masks


def validate_effective_removal(masks, heads, geometry=GEOMETRY):
    """Reject nonhead support, partial heads, wrong shapes, or a stale adapter."""
    g = geometry
    heads = validate_heads(heads, g)
    if set(masks) != MASK_KEYS:
        raise ValueError('unexpected gate layout')
    if np.asarray(masks['attention_blocks']).shape != (g['num_layers'],) or not np.all(np.asarray(masks['attention_blocks']) == 1):
        raise ValueError('attention block geometry/support')
    keys = {str(i) for i in range(g['num_layers'])}
    for name, width in [('attention_heads', g['num_heads']),
                        ('attention_neurons', g['hidden_size']),
                        ('mlp_hidden', g['intermediate_size']),
                        ('mlp_output', g['hidden_size'])]:
        if set(masks[name]) != keys:
            raise ValueError('missing or extra layer')
        for value in masks[name].values():
            a = np.asarray(value)
            if a.shape != (width,) or not np.isin(a, [0, 1]).all():
                raise ValueError('invalid mask geometry/binary support')
    chosen = set(map(tuple, heads))
    ko = knockout_masks(as_arrays(masks), 'finest')
    for layer in range(g['num_layers']):
        key = str(layer)
        expected = np.array([int((layer, h) in chosen) for h in range(g['num_heads'])])
        if not np.array_equal(masks['attention_heads'][key], expected) or not np.array_equal(masks['attention_neurons'][key], np.repeat(expected, g['head_dim'])):
            raise ValueError('whole-head support differs')
        if any(np.asarray(masks[k][key]).any() for k in ('mlp_hidden', 'mlp_output')):
            raise ValueError('nonhead support would remove MLPs')
        if not np.array_equal(ko['attention_neurons'][key], 1 - np.repeat(expected, g['head_dim'])):
            raise ValueError('effective complement differs')
        if not all(np.asarray(ko[k][key]).all() for k in ('mlp_hidden', 'mlp_output', 'attention_heads')):
            raise ValueError('nonselected gates are not open')
    validate_hierarchy(as_arrays(masks), num_heads=g['num_heads'], head_dim=g['head_dim'])


def prepare_frozen_masks(alignment_root, output_path):
    root = Path(alignment_root)
    receipt_path = root / '.scratch/selective-deception/sparse-optimization-v4/comparison/selection-receipt.json'
    receipt_binding = dict(path=str(receipt_path), sha256=SELECTION_SHA256)
    receipt = read_json(check_binding(receipt_binding))
    if not (receipt['finalists_frozen'] and receipt['no_test_based_selection']):
        raise ValueError('finalist receipt is not frozen')
    old_path = root / 'Deception-Circuit/outputs/llama-8b-instruct_sdr_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742/active_nodes.coarse.json'
    old_binding = dict(path=str(old_path), sha256=OLD_D_SHA256)
    old = read_json(check_binding(old_binding))
    # active_mlps intentionally ignored: the old coarse export lists every
    # ungated MLP as active. Only its 69 selected query heads were removed.
    old_heads = validate_heads([[int(l), h] for l, hs in old['active_heads'].items() for h in hs])
    if len(old_heads) != 69:
        raise ValueError('oldD69 support changed')
    conditions = {'oldD69': dict(removed_heads=old_heads, origin=old_binding)}
    sources = [receipt_binding, old_binding]
    for row in receipt['masks']:
        label = row['label']
        head_path = check_binding(row['head_list'])
        heads = validate_heads(read_json(head_path)['removed_heads'])
        if label not in ('new-allW23', 'new-allW30') or len(heads) != int(label.removeprefix('new-allW')):
            raise ValueError('unexpected frozen finalist')
        proposal = row['source_proposal']
        for name in ('checkpoint', 'export', 'manifest', 'run_identity'):
            b = dict(path=proposal[name + '_path'], sha256=proposal[name + '_sha256'])
            check_binding(b)
            sources.append(b)
        export = read_json(proposal['export_path'])
        if heads != export['removed_heads'] or export['export_hash'] != digest({k: v for k, v in export.items() if k != 'export_hash'}):
            raise ValueError('frozen export/head-list binding differs')
        expected_r = {str(l): [int([l, h] in heads) for h in range(32)] for l in range(32)}
        if export['R'] != expected_r or export['K'] != {k: [1-v for v in values] for k, values in expected_r.items()}:
            raise ValueError('frozen export effective support differs')
        sources.append(row['head_list'])
        conditions[label] = dict(removed_heads=heads, origin=row['head_list'])
    if set(conditions) != {'oldD69', 'new-allW23', 'new-allW30'}:
        raise ValueError('missing frozen finalists')
    conditions['random30'] = dict(removed_heads=layer_matched_random(conditions['new-allW30']['removed_heads']),
                                  seed=RANDOM_SEED, algorithm='python.Random.sample-all-query-heads-per-sorted-layer-v1')
    result = dict(schema_version=SCHEMA_VERSION, purpose='frozen_query_head_removal_adapter',
                  geometry=dict(GEOMETRY), knockout_granularity='finest', conditions=conditions,
                  source_bindings=sources, selection_receipt=receipt_binding)
    if str(Path(output_path).resolve()) in {str(Path(b['path']).resolve()) for b in sources}:
        raise ValueError('refusing to overwrite historical mask source')
    Path(output_path).write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    load_frozen_masks(output_path)
    return result


def load_frozen_masks(path):
    data = read_json(path)
    if data.get('schema_version') != SCHEMA_VERSION or data.get('geometry') != GEOMETRY or data.get('knockout_granularity') != 'finest':
        raise ValueError('unsupported frozen-mask manifest')
    for b in data['source_bindings']:
        check_binding(b)
    if data['selection_receipt']['sha256'] != SELECTION_SHA256:
        raise ValueError('unexpected selection receipt')
    receipt = read_json(check_binding(data['selection_receipt']))
    mandatory = [data['selection_receipt']]
    for row in receipt['masks']:
        mandatory.append(row['head_list'])
        proposal = row['source_proposal']
        for name in ('checkpoint', 'export', 'manifest', 'run_identity'):
            mandatory.append(dict(path=proposal[name + '_path'], sha256=proposal[name + '_sha256']))
        export = read_json(check_binding(dict(path=proposal['export_path'], sha256=proposal['export_sha256'])))
        heads = read_json(check_binding(row['head_list']))['removed_heads']
        expected_r = {str(l): [int([l, h] in heads) for h in range(32)] for l in range(32)}
        if export['removed_heads'] != heads or export['R'] != expected_r or export['K'] != {k: [1-v for v in values] for k, values in expected_r.items()}:
            raise ValueError('frozen export effective support differs')
        if data['conditions'][row['label']]['origin'] != row['head_list']:
            raise ValueError('frozen head-list origin differs')
    if any(b not in data['source_bindings'] for b in mandatory):
        raise ValueError('missing required frozen source binding')
    expected = {row['label']: read_json(check_binding(row['head_list']))['removed_heads'] for row in receipt['masks']}
    old_origin = data['conditions']['oldD69']['origin']
    if old_origin['sha256'] != OLD_D_SHA256:
        raise ValueError('unexpected old D support')
    old = read_json(check_binding(old_origin))
    expected['oldD69'] = sorted([[int(l), h] for l, hs in old['active_heads'].items() for h in hs])
    if old_origin not in data['source_bindings'] or len(expected['oldD69']) != 69:
        raise ValueError('old D support/binding differs')
    if data['conditions']['random30'].get('seed') != RANDOM_SEED or data['conditions']['random30'].get('algorithm') != 'python.Random.sample-all-query-heads-per-sorted-layer-v1':
        raise ValueError('random control policy differs')
    expected['random30'] = layer_matched_random(expected['new-allW30'])
    if set(data['conditions']) != set(expected):
        raise ValueError('unexpected conditions')
    if any(row['removed_heads'] != expected[label] for label, row in data['conditions'].items()):
        raise ValueError('manifest support differs from frozen selection')
    return {label: heads_to_leaf_masks(heads) for label, heads in expected.items()}


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--alignment-root', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = prepare_frozen_masks(args.alignment_root, args.output)
    print(json.dumps({k: len(v['removed_heads']) for k, v in result['conditions'].items()}, sort_keys=True))


if __name__ == '__main__':
    main()
