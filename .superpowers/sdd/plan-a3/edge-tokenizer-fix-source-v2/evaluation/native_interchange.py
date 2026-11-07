"""Bounded native nonself-H head replay (report 61).

Individual unpadded prompts only. Both actual streams follow donor autoregression
at capture; recipient shadow inputs are computational scaffolding. Scientific
references come exclusively from the CPU bank, except the causally untouched
unmatched early prefix. No training/model/generation API is changed.

Identity strings must name caller-verified immutable weight/source and tokenizer
artifacts. A bank can be persisted with torch.save and loaded with
``torch.load(..., weights_only=False)`` from trusted local artifacts. Same-process
parameter version guards additionally reject weight edits; persisted reuse on a
new model instance relies on those verified external identities.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import platform
from pathlib import Path

import torch
import transformers
from transformers.cache_utils import DynamicCache

from l0 import HardConcreteGate
from models.llama_node import _gated_modules, install_ablation_hook

SCHEMA = 'native-head-replay-v1'
POSITION_POLICY = 'right-aligned-intersection-keep-clean-prefix'
TERMINAL_POLICY = 'hold-query-predicting-eos-no-eos-forward'


@dataclass(frozen=True)
class DecodeSpec:
    max_new_tokens: int
    eos_token_ids: tuple = ()

    def __post_init__(self):
        if type(self.max_new_tokens) is not int or self.max_new_tokens < 1:
            raise ValueError('max_new_tokens must be a positive integer')
        if not isinstance(self.eos_token_ids, tuple) or any(type(x) is not int or x < 0 for x in self.eos_token_ids):
            raise ValueError('eos_token_ids must be a tuple of nonnegative integers')
        if len(set(self.eos_token_ids)) != len(self.eos_token_ids):
            raise ValueError('duplicate EOS ids')


@dataclass(frozen=True)
class DonorBank:
    prompt_tokens: tuple
    generated_tokens: tuple
    termination: str
    activations: tuple
    provenance: dict
    bound_model_id: int
    parameter_versions: tuple
    content_digest: str = ''

    @property
    def query_count(self):
        return len(self.prompt_tokens) + len(self.generated_tokens) - 1

    def compute_digest(self):
        h = hashlib.sha256()
        metadata = (self.prompt_tokens, self.generated_tokens, self.termination, self.provenance)
        h.update(json.dumps(metadata, sort_keys=True, separators=(',', ':')).encode())
        for value in self.activations:
            h.update(str((tuple(value.shape), value.dtype)).encode())
            h.update(value.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes())
        return h.hexdigest()


@dataclass(frozen=True)
class ReplayResult:
    generated_tokens: tuple
    termination: str
    prompt_map: tuple
    unmapped_prefix: int
    query_indices: tuple
    terminal_held_steps: int
    last_logits: torch.Tensor


def _prompt(model, ids):
    if (not isinstance(ids, torch.Tensor) or ids.ndim != 2 or ids.shape[0] != 1
            or ids.shape[1] < 1 or ids.dtype != torch.long):
        raise ValueError('only individual unpadded nonempty [1,L] long prompts are supported')
    if (ids < 0).any() or (ids >= model.config.vocab_size).any():
        raise ValueError('prompt token outside vocabulary')
    return ids.to(next(model.parameters()).device)


def _versions(model):
    # Gates are scoped intervention settings, never model weight provenance.
    gate_parameters = {id(g.log_alpha) for g in model.modules() if isinstance(g, HardConcreteGate)}
    return tuple((n, id(p), p._version) for n, p in model.named_parameters() if id(p) not in gate_parameters)


def _identity(model, model_identity, tokenizer_identity):
    if not model_identity or not tokenizer_identity:
        raise ValueError('nonempty immutable model/tokenizer identity is required')
    root = Path(__file__).resolve().parent.parent
    sources = ('evaluation/native_interchange.py', 'models/llama_node.py', 'models/_compat.py', 'l0.py')
    source_hashes = {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in sources}
    return dict(model_identity=model_identity, tokenizer_identity=tokenizer_identity,
                source_hashes=source_hashes,
                model_class=type(model).__module__ + '.' + type(model).__qualname__,
                config=model.config.to_dict(), torch=torch.__version__, transformers=transformers.__version__,
                python=platform.python_version(), backend=model.config._attn_implementation,
                dtype=str(next(model.parameters()).dtype), device_type=next(model.parameters()).device.type,
                deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
                schema=SCHEMA, mapping_policy=POSITION_POLICY, terminal_policy=TERMINAL_POLICY)


def _validate_keep(model, keep):
    layers = model.model.layers
    if any(getattr(b.attn, 'head_gates', None) is None for b in layers):
        raise ValueError('every layer must expose an attn_head site')
    shape = (len(layers), layers[0].attn.num_heads)
    if not isinstance(keep, torch.Tensor) or tuple(keep.shape) != shape:
        raise ValueError(f'keep mask shape must be {shape}')
    if not torch.isfinite(keep).all() or not ((keep == 0) | (keep == 1)).all():
        raise ValueError('keep mask must be exact binary 0/1')


@contextmanager
def _execution(model, keep, hook):
    """Scope exact head keep settings and hard-open every nonhead gate.

    Restore existing hooks/gates, including on errors. The model must already be
    in eval mode; this adapter never silently changes caller training state.
    """
    if any(m.training for m in model.modules()):
        raise ValueError('native replay requires model.eval()')
    _validate_keep(model, keep)
    heads = {id(b.attn.head_gates): keep[i] for i, b in enumerate(model.model.layers)}
    gates = [(g, g.log_alpha.detach().clone()) for g in model.modules() if isinstance(g, HardConcreteGate)]
    hooks = [(m, getattr(m, '_ablation_hook', None)) for m in _gated_modules(model)]
    try:
        with torch.no_grad():
            for gate, _ in gates:
                value = heads.get(id(gate))
                gate.log_alpha.copy_(torch.full_like(gate.log_alpha, 20) if value is None
                                     else torch.where(value.to(gate.log_alpha.device) == 1, 20., -20.))
                expected = torch.ones_like(gate()) if value is None else value.to(gate.log_alpha.device)
                if not torch.equal(gate(), expected):
                    raise ValueError('gate did not implement exact hard keep mask')
            install_ablation_hook(model, hook)
            yield
    finally:
        with torch.no_grad():
            for gate, saved in gates:
                gate.log_alpha.copy_(saved)
        for module, previous in hooks:
            object.__setattr__(module, '_ablation_hook', previous)


def _forward(model, ids, position, cache, shadow_cache):
    return model(input_ids=ids, corrupted_input_ids=ids,
                 attention_mask=torch.ones(1, position + ids.shape[1], dtype=torch.long, device=ids.device),
                 position_ids=torch.arange(position, position + ids.shape[1], device=ids.device).unsqueeze(0),
                 past_key_values=cache, corrupted_past_key_values=shadow_cache, use_cache=True).logits


def capture_donor(model, prompt_ids, decode_spec, *, model_identity, tokenizer_identity):
    """Capture all heads on CPU during the donor's actual greedy autoregression."""
    ids = _prompt(model, prompt_ids)
    keep = torch.ones(len(model.model.layers), model.model.layers[0].attn.num_heads)
    _validate_keep(model, keep)
    provenance = _identity(model, model_identity, tokenizer_identity)
    provenance.update(prompt_attention_mask=[1] * ids.shape[1], prompt_positions=list(range(ids.shape[1])),
                      decode=dict(max_new_tokens=decode_spec.max_new_tokens, eos_token_ids=decode_spec.eos_token_ids,
                                  do_sample=False, use_cache=True))
    parts = [[] for _ in model.model.layers]
    seen = set()
    def collect(module, value, site):
        if site == 'attn_head':
            layer = module.layer_idx
            if layer in seen:
                raise ValueError('duplicate head capture site in explicit forward')
            seen.add(layer)
            parts[layer].append(value[0].detach().to('cpu', copy=True))
        return value
    tokens, termination, position = [], 'cap', 0
    step_ids = ids
    cache, shadow = DynamicCache(), DynamicCache()
    with _execution(model, keep, collect):
        for _ in range(decode_spec.max_new_tokens):
            seen.clear()
            logits = _forward(model, step_ids, position, cache, shadow)
            if seen != set(range(len(parts))):
                raise ValueError('missing head capture site')
            token = int(logits[0, -1].argmax())
            tokens.append(token)
            if token in decode_spec.eos_token_ids:
                termination = 'eos'
                break
            position += step_ids.shape[1]
            step_ids = torch.tensor([[token]], dtype=torch.long, device=ids.device)
    bank = DonorBank(tuple(ids[0].tolist()), tuple(tokens), termination,
                     tuple(torch.cat(p, dim=0) for p in parts), provenance,
                     id(model), _versions(model))
    object.__setattr__(bank, 'content_digest', bank.compute_digest())
    return bank


def make_position_map(recipient_prompt, bank):
    """Map real recipient prompt queries onto a donor suffix, or -1 keep-clean."""
    if (recipient_prompt.ndim != 2 or recipient_prompt.shape[0] != 1 or recipient_prompt.shape[1] < 1):
        raise ValueError('only individual unpadded prompts supported')
    lr, ld = recipient_prompt.shape[1], len(bank.prompt_tokens)
    return tuple(max(-1, ld - lr + p) for p in range(lr))


def _validate_bank(model, bank, spec, model_identity, tokenizer_identity):
    expected = _identity(model, model_identity, tokenizer_identity)
    if any(bank.provenance.get(k) != v for k, v in expected.items()):
        raise ValueError('bank model/tokenizer/runtime identity mismatch')
    if bank.bound_model_id == id(model) and bank.parameter_versions != _versions(model):
        raise ValueError('stale bank: model weights changed after donor capture')
    decode = bank.provenance.get('decode', {})
    cap = decode.get('max_new_tokens')
    eos = tuple(decode.get('eos_token_ids', ()))
    if (bank.termination not in ('eos', 'cap') or not bank.prompt_tokens or not bank.generated_tokens
            or type(cap) is not int or not 1 <= len(bank.generated_tokens) <= cap
            or any(t in eos for t in bank.generated_tokens[:-1])
            or (bank.termination == 'eos' and bank.generated_tokens[-1] not in eos)
            or (bank.termination == 'cap' and (len(bank.generated_tokens) != cap or bank.generated_tokens[-1] in eos))):
        raise ValueError('invalid bank termination/tokens')
    if (bank.provenance.get('prompt_attention_mask') != [1] * len(bank.prompt_tokens)
            or bank.provenance.get('prompt_positions') != list(range(len(bank.prompt_tokens)))):
        raise ValueError('invalid donor prompt mask/positions')
    if any(type(t) is not int or not 0 <= t < model.config.vocab_size
           for t in bank.prompt_tokens + bank.generated_tokens):
        raise ValueError('invalid bank token identity')
    if len(bank.activations) != len(model.model.layers):
        raise ValueError('bank missing layer/site')
    for block, value in zip(model.model.layers, bank.activations):
        shape = (bank.query_count, block.attn.num_heads, block.attn.head_dim)
        if (tuple(value.shape) != shape or value.device.type != 'cpu'
                or str(value.dtype) != bank.provenance['dtype'] or not torch.isfinite(value).all()):
            raise ValueError('invalid bank head site shape/device/values')
    if bank.compute_digest() != bank.content_digest:
        raise ValueError('bank content digest mismatch')
    decode = bank.provenance['decode']
    if tuple(decode['eos_token_ids']) != spec.eos_token_ids:
        raise ValueError('bank decode EOS identity mismatch')
    if bank.termination == 'cap' and spec.max_new_tokens > decode['max_new_tokens']:
        raise ValueError('donor cap does not cover requested recipient queries')


class _ReplayHook:
    """Explicit query indices are set by the loop before each model forward."""
    def __init__(self, model, bank):
        self.bank = bank
        self.layers = {id(b.attn): i for i, b in enumerate(model.model.layers)}
        self.indices = None

    def set_indices(self, indices):
        if not indices or any(type(q) is not int or q < -1 or q >= self.bank.query_count for q in indices):
            raise ValueError('invalid donor query index')
        self.indices = indices
        self.seen = set()

    def __call__(self, module, value, site):
        if site != 'attn_head':
            return value  # proven hard-open by _execution
        layer = self.layers.get(id(module))
        if layer is None or layer >= len(self.bank.activations):
            raise ValueError('missing bank layer/site')
        if self.indices is None or tuple(value.shape[:2]) != (1, len(self.indices)):
            raise ValueError('replay index/query shape mismatch')
        if layer in self.seen:
            raise ValueError('duplicate head replay site in explicit forward')
        self.seen.add(layer)
        result = value.clone()
        mapped = [(p, q) for p, q in enumerate(self.indices) if q >= 0]
        if mapped:
            ps, qs = zip(*mapped)
            source = self.bank.activations[layer][list(qs)]
            if tuple(source.shape[1:]) != tuple(value.shape[2:]):
                raise ValueError('bank head shape mismatch')
            result[0, list(ps)] = source.to(device=value.device, dtype=value.dtype)
        # Only the causally untouched early prefix retains identical-token shadow.
        return result


def generate_with_replay(model, prompt_ids, keep_mask, bank, decode_spec, *, model_identity, tokenizer_identity):
    """Greedy cached recipient generation with boundary-aligned donor references."""
    ids = _prompt(model, prompt_ids)
    _validate_keep(model, keep_mask)
    _validate_bank(model, bank, decode_spec, model_identity, tokenizer_identity)
    mapping = make_position_map(ids, bank)
    hook = _ReplayHook(model, bank)
    tokens, queries, held = [], [], 0
    termination, position, step_ids = 'cap', 0, ids
    cache, shadow = DynamicCache(), DynamicCache()
    with _execution(model, keep_mask, hook):
        for t in range(decode_spec.max_new_tokens):
            natural = len(bank.prompt_tokens) - 1 + t
            q = min(natural, bank.query_count - 1)
            if natural > q:
                if bank.termination != 'eos':
                    raise ValueError('query exceeds cap-terminated donor bank')
                held += 1
            hook.set_indices(mapping if t == 0 else (q,))
            logits = _forward(model, step_ids, position, cache, shadow)
            if hook.seen != set(range(len(model.model.layers))):
                raise ValueError('missing head replay site')
            if not torch.isfinite(logits).all():
                raise ValueError('nonfinite recipient logits')
            token = int(logits[0, -1].argmax())
            tokens.append(token)
            queries.append(q)
            if token in decode_spec.eos_token_ids:
                termination = 'eos'
                break
            position += step_ids.shape[1]
            step_ids = torch.tensor([[token]], dtype=torch.long, device=ids.device)
    return ReplayResult(tuple(tokens), termination, mapping, mapping.count(-1), tuple(queries), held,
                        logits[0, -1].detach().to('cpu', copy=True))
