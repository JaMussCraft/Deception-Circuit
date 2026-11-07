"""One frozen-pilot technical proof on the already-loaded node model.

No generation, labels, API, second model, parameter casts or tolerance tuning.
Both identity forwards use the same dual-stream prefill path and fixed IDs.
"""
import hashlib
import inspect
import json
import os
from pathlib import Path

import numpy as np
import torch
from transformers.cache_utils import DynamicCache

from analysis import (_mask_slots, apply_node_masks, assert_masks_equal,
                      extract_node_masks, open_all_gates)
from evaluation.frozen_head_masks import load_frozen_masks
from evaluation.masks import as_lists, knockout_masks, ones_like


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode('utf-8')).hexdigest()


def _save(path, proof):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temporary = path + '.tmp'
    with open(temporary, 'w') as handle:
        json.dump(proof, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def check_frozen_runtime(ctx):
    """Fail before generation unless actual support and exact logits agree.

    JSON proof is written on success/failure. Gate parameters, final-mode flags,
    and every module's training flag are restored even when validation fails.
    This does not touch Session._current_masks or load another model.
    """
    model = ctx.node_model
    slots = _mask_slots(model)
    saved = [(gate, gate.log_alpha.detach().clone(), gate.final_mode)
             for _, _, gate in slots]
    training = [(module, module.training) for module in model.modules()]
    path = os.path.join(ctx.out_dir, 'frozen_runtime_check.json')
    manifest = ctx.cli.benchmark_frozen_masks
    proof = {'passed': False, 'states': {}, 'purpose': 'technical_support_and_same_path_identity',
             'manifest': {'path': os.path.realpath(manifest), 'sha256': _sha(manifest)},
             'source_sha256': {str(Path(__file__).resolve()): _sha(__file__)},
             'model_class': type(model).__name__, 'torch_version': str(torch.__version__)}
    try:
        masks = load_frozen_masks(manifest)
        expected_names = {'new-allW23', 'new-allW30', 'oldD69', 'random30'}
        if set(masks) != expected_names:
            raise ValueError('technical proof requires the four fixed removals')
        geometry = json.loads(Path(manifest).read_text())['geometry']
        actual_geometry = {'num_layers': model.config.num_hidden_layers,
                           'num_heads': model.config.num_attention_heads,
                           'head_dim': model.config.hidden_size // model.config.num_attention_heads,
                           'hidden_size': model.config.hidden_size,
                           'intermediate_size': model.config.intermediate_size}
        if geometry != actual_geometry:
            raise ValueError('actual model geometry differs from frozen mask manifest')
        families = {'attention_blocks', 'attention_heads', 'attention_neurons', 'mlp_hidden', 'mlp_output'}
        if {name for name, _, _ in slots} != families:
            raise ValueError('actual enabled gate families differ from the frozen pilot')
        full = ones_like(next(iter(masks.values())))
        states = {'full': full, **{name: knockout_masks(mask, 'finest') for name, mask in masks.items()}}
        for name, expected in states.items():
            # apply_node_masks checks actual gate widths/layout. The reverse
            # comparison also rejects absent per-layer gates or extra support.
            apply_node_masks(model, expected)
            live = extract_node_masks(model)
            assert_masks_equal(as_lists(expected), live)
            removed = 0
            for layer in range(geometry['num_layers']):
                key = str(layer)
                neurons = np.asarray(live['attention_neurons'][key]).reshape(
                    geometry['num_heads'], geometry['head_dim'])
                if not np.all((neurons == 0).all(axis=1) | (neurons == 1).all(axis=1)):
                    raise AssertionError('actual removal contains partial query heads')
                removed += int((neurons == 0).all(axis=1).sum())
                if (not all(live['attention_heads'][key]) or not all(live['mlp_hidden'][key])
                        or not all(live['mlp_output'][key]) or live['attention_blocks'][layer] != 1):
                    raise AssertionError('actual nonselected/coarse/MLP support is not open')
            proof['states'][name] = {'removed_query_heads': removed,
                                      'actual_support_sha256': _digest(live),
                                      'exact_mask_roundtrip': True,
                                      'nonselected_and_mlp_open': True}
        clean = [[1, 2, 3, 4]]
        corrupt = [[4, 3, 2, 1]]
        if model.config.vocab_size <= 4:
            raise ValueError('fixed technical token IDs are outside the model vocabulary')
        proof['input'] = {'clean_ids': clean, 'corrupt_ids': corrupt,
                          'sha256': _digest({'clean_ids': clean, 'corrupt_ids': corrupt})}
        device = next(model.parameters()).device
        dtype = next(model.parameters()).dtype
        proof.update(device=str(device), dtype=str(dtype), geometry=actual_geometry)
        proof['model_config_name'] = getattr(model.config, '_name_or_path', '')
        for source in (inspect.getsourcefile(type(model)), inspect.getsourcefile(apply_node_masks)):
            if source:
                proof['source_sha256'][os.path.realpath(source)] = _sha(source)
        use_cache = not ctx.cli.no_kv_cache
        proof['forward_path'] = 'dual-stream cached prefill' if use_cache else 'dual-stream uncached'
        ids = torch.tensor(clean, dtype=torch.long, device=device)
        donor = torch.tensor(corrupt, dtype=torch.long, device=device)
        def last_logits():
            kwargs = dict(input_ids=ids, corrupted_input_ids=donor,
                          attention_mask=torch.ones_like(ids), use_cache=use_cache)
            if use_cache:
                kwargs.update(position_ids=torch.arange(ids.shape[1], device=device).unsqueeze(0),
                              past_key_values=DynamicCache(), corrupted_past_key_values=DynamicCache())
            with torch.no_grad():
                return model(**kwargs).logits[:, -1, :].detach().cpu()
        open_all_gates(model)
        assert_masks_equal(as_lists(full), extract_node_masks(model))
        anchor = last_logits()
        apply_node_masks(model, full)
        assert_masks_equal(as_lists(full), extract_node_masks(model))
        explicit = last_logits()
        finite = bool(torch.isfinite(anchor).all() and torch.isfinite(explicit).all())
        exact = finite and torch.equal(anchor, explicit)
        proof['logit_identity'] = {'exact': exact, 'finite': finite,
             'vocab_size': int(anchor.shape[-1]), 'compared_shape': list(anchor.shape),
             'max_abs_diff': float((anchor.float() - explicit.float()).abs().max()) if finite else None,
             'anchor_sha256': hashlib.sha256(anchor.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest(),
             'explicit_sha256': hashlib.sha256(explicit.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()}
        if not exact or anchor.shape != (1, model.config.vocab_size):
            raise AssertionError('all-open full-vocabulary last-token logits failed exact same-path identity')
        proof['passed'] = True
    except Exception as exc:
        proof['error'] = '%s: %s' % (type(exc).__name__, exc)
        raise
    finally:
        with torch.no_grad():
            for gate, values, final_mode in saved:
                gate.log_alpha.copy_(values)
                gate.final_mode = final_mode
        for module, was_training in training:
            module.training = was_training
        _save(path, proof)
    return proof
