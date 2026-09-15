"""
component_analysis/components.py — a circuit's mask object as a set of Components.

A **Component** is the unit of interpretation: one attention head or one MLP
block, identified by (kind, layer, index). Finer gates — attention neurons,
MLP hidden and MLP output dimensions — are collapsed onto their Component.

The coarsening rule, from CONTEXT.md: *a Component is a Circuit Component when
any of its gates is active in the circuit under study.* Gate levels AND
together in the prunable model, so a head whose neuron gates are all closed
contributes nothing no matter what its head gate says, and an MLP block with no
live hidden or output unit writes nothing. Leaf gates therefore decide
membership, and the coarse gate is *recorded* (`head_gate_active`) rather than
consulted. Where a circuit has no leaf gates at all — a run with
attention-neuron pruning switched off saves no `attention_neurons` — the coarse
gate is all there is, and it decides.

That rule is what makes the leaf-granularity delta circuits from the benchmark
knockouts analysable: their head gates are re-derived from neurons by
`evaluation/algebra.py`, and this reads the same relation back out.

Nothing here loads a model. Geometry comes from the mask object
(`evaluation.context.geometry_from_masks`) except for `num_key_value_heads`,
which no mask records and which the caller supplies.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Component:
    """One head or MLP block of a circuit.

    `index` is the head index, and 0 for an MLP block: a layer has one MLP, so
    (kind, layer, index) stays a uniform key across both kinds.

    `kv_group` is the grouped-query-attention group the head reads its K and V
    from — under GQA a "per-head K/V receiver" is really per group, shared by
    `num_heads // num_kv_heads` query heads. It is None for MLP blocks and when
    the caller did not supply `num_kv_heads`.

    `head_gate_active` is the Component's own coarse gate: `attention_heads`
    for a head, `mlp_blocks` for an MLP block. On a hierarchy-valid circuit it
    agrees with `active_neuron_count > 0` for heads; it is recorded separately
    because the two come apart across granularities (a head-granularity delta
    selects on this gate, a leaf-granularity delta on the count).

    `active_neuron_count` is the live leaf gates inside the Component: the
    head's `attention_neurons`, or the MLP block's `mlp_hidden` plus
    `mlp_output`.
    """

    kind: str
    layer: int
    index: int
    kv_group: int | None
    head_gate_active: bool
    active_neuron_count: int

    @property
    def key(self) -> tuple:
        return (self.kind, self.layer, self.index)


# ==============================================================================
# COARSENING
# ==============================================================================

def _vector(entry, layer: int):
    """A per-layer mask vector as an array, or None when the key is absent."""
    if not isinstance(entry, dict):
        return None
    value = entry.get(str(layer))
    return None if value is None else np.asarray(value, dtype=np.uint8)


def _layers(masks: dict) -> list:
    """Every layer index the mask object describes, ascending."""
    seen = set()
    for key in ("attention_heads", "attention_neurons", "mlp_hidden", "mlp_output"):
        entry = masks.get(key)
        if isinstance(entry, dict):
            seen.update(int(k) for k in entry)
    for key in ("layers", "attention_blocks", "mlp_blocks"):
        value = masks.get(key)
        if value is not None:
            seen.update(range(len(np.asarray(value))))
    return sorted(seen)


def _block_gate(masks: dict, key: str, layer: int) -> bool:
    """A coarse block gate, defaulting to open where the circuit has no such gate."""
    value = masks.get(key)
    if value is None:
        return True
    return bool(np.asarray(value)[layer])


def head_components(masks: dict, layer: int, *, num_heads: int, head_dim: int,
                    num_kv_heads: int | None = None) -> list:
    """The head Components this circuit has in one layer."""
    heads = _vector(masks.get("attention_heads"), layer)
    neurons = _vector(masks.get("attention_neurons"), layer)
    if heads is None and neurons is None:
        return []

    if num_kv_heads and num_heads % num_kv_heads:
        raise ValueError(
            f"{num_heads} query heads do not divide into {num_kv_heads} KV "
            f"heads, so no head has a well-defined KV group.")
    per_group = (num_heads // num_kv_heads) if num_kv_heads else None
    live_layer = (_block_gate(masks, "layers", layer)
                  and _block_gate(masks, "attention_blocks", layer))

    out = []
    for index in range(num_heads):
        if neurons is not None:
            count = int(neurons[index * head_dim:(index + 1) * head_dim].sum())
            active = count > 0
        else:
            # No leaf gates were pruned, so the head gate is the finest
            # statement the circuit makes about this head.
            count = 0
            active = bool(heads[index])
        if not (active and live_layer):
            continue
        out.append(Component(
            kind="head", layer=layer, index=index,
            kv_group=(index // per_group) if per_group else None,
            head_gate_active=True if heads is None else bool(heads[index]),
            active_neuron_count=count))
    return out


def mlp_component(masks: dict, layer: int):
    """The MLP-block Component of one layer, or None when it has no live gate."""
    hidden = _vector(masks.get("mlp_hidden"), layer)
    output = _vector(masks.get("mlp_output"), layer)
    live_layer = (_block_gate(masks, "layers", layer)
                  and _block_gate(masks, "mlp_blocks", layer))

    if hidden is None and output is None:
        # Nothing finer than the block gate exists, so it decides.
        if not live_layer or masks.get("mlp_blocks") is None:
            return None
        return Component(kind="mlp", layer=layer, index=0, kv_group=None,
                         head_gate_active=_block_gate(masks, "mlp_blocks", layer),
                         active_neuron_count=0)

    count = int(sum(int(v.sum()) for v in (hidden, output) if v is not None))
    if not (count > 0 and live_layer):
        return None
    return Component(kind="mlp", layer=layer, index=0, kv_group=None,
                     head_gate_active=_block_gate(masks, "mlp_blocks", layer),
                     active_neuron_count=count)


def circuit_components(masks: dict, *, num_heads: int, head_dim: int,
                       num_kv_heads: int | None = None) -> list:
    """Every Circuit Component of `masks`, ordered by (layer, kind, index).

    Heads come before the MLP block of the same layer, which is the order they
    write to the residual stream in.
    """
    out = []
    for layer in _layers(masks):
        out.extend(head_components(masks, layer, num_heads=num_heads,
                                   head_dim=head_dim, num_kv_heads=num_kv_heads))
        mlp = mlp_component(masks, layer)
        if mlp is not None:
            out.append(mlp)
    return out


def is_component_of(component: Component, masks: dict, *, num_heads: int,
                    head_dim: int) -> bool:
    """Is this Component a Circuit Component of `masks` too?

    The membership test behind the `--reference NAME=RUN_DIR` columns: it asks
    the same "any active leaf gate" question of another circuit, so a
    Component shared with the honest twin is distinguishable from a
    deception-specific one in the same table.
    """
    if component.kind == "head":
        found = head_components(masks, component.layer, num_heads=num_heads,
                                head_dim=head_dim)
        return any(c.index == component.index for c in found)
    return mlp_component(masks, component.layer) is not None


def count_components(components) -> dict:
    """A one-line census of a Component list, for logs and the dry-run report."""
    heads = [c for c in components if c.kind == "head"]
    return {
        "heads": len(heads),
        "mlps": sum(1 for c in components if c.kind == "mlp"),
        "heads_head_gate_active": sum(1 for c in heads if c.head_gate_active),
        "layers": len({c.layer for c in components}),
    }
