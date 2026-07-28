"""
evaluation/masks.py — a node circuit as data: load, count, validate, knock out,
and sample size-matched random circuits.

A *mask object* is exactly what `analysis.extract_node_masks` writes and what
`analysis.apply_node_masks` reads back — the object stored under the "masks" key
of `active_nodes.json`:

    embedding          int 0/1                    (absent when there is no gate)
    layers             [0/1] * n_layers           (absent when full-layer
    attention_blocks   [0/1] * n_layers            pruning was off)
    mlp_blocks         [0/1] * n_layers
    attention_heads    {"<layer>": [0/1] * n_heads}
    attention_neurons  {"<layer>": [0/1] * (n_heads * head_dim)}
    mlp_hidden         {"<layer>": [0/1] * intermediate_size}
    mlp_output         {"<layer>": [0/1] * hidden_size}

Everything here works on plain JSON lists or on numpy arrays; `as_arrays`
converts once so the samplers and the set algebra stay fast.
"""

from __future__ import annotations

import json
import os

import numpy as np

# Bump when the random-circuit sampling algorithm changes in any way that moves
# the drawn circuits; recorded in random_circuits.json so an old run's numbers
# are never silently compared against a new sampler's.
ALGORITHM_VERSION = 1

SCALAR_KEYS = ("embedding",)
BLOCK_KEYS = ("layers", "attention_blocks", "mlp_blocks")
VECTOR_KEYS = ("attention_heads", "attention_neurons", "mlp_hidden", "mlp_output")

# The three granularities the finest-only knockout complements.
FINEST_KEYS = ("attention_neurons", "mlp_hidden", "mlp_output")
# Everything the finest-only knockout holds wide open.
COARSE_KEYS = ("layers", "embedding", "attention_blocks", "mlp_blocks",
               "attention_heads")

ALL_KEYS = SCALAR_KEYS + BLOCK_KEYS + VECTOR_KEYS


# ==============================================================================
# LOADING / CONVERSION
# ==============================================================================

def load_circuit_masks(run_dir: str, filename: str = "active_nodes.json") -> dict:
    """Read the saved node masks out of a run directory."""
    path = os.path.join(run_dir, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found — a run directory must contain {filename}.")
    with open(path) as f:
        payload = json.load(f)
    if "masks" not in payload:
        raise ValueError(
            f"{path} has no 'masks' key. It predates commit c714ce6, which "
            f"started saving the finer-gate masks; only active_heads / "
            f"active_mlps are recoverable from it, which is not enough to "
            f"rebuild the node-pruned circuit.")
    return as_arrays(payload["masks"])


def as_arrays(masks: dict) -> dict:
    """Per-layer vectors as np.uint8; scalars as python ints."""
    out = {}
    for key, value in masks.items():
        if isinstance(value, dict):
            out[key] = {k: np.asarray(v, dtype=np.uint8) for k, v in value.items()}
        elif isinstance(value, (list, tuple, np.ndarray)):
            out[key] = np.asarray(value, dtype=np.uint8)
        else:
            out[key] = int(value)
    return out


def as_lists(masks: dict) -> dict:
    """Inverse of `as_arrays` — JSON-serialisable, and what apply_node_masks
    round-trips against `extract_node_masks` output."""
    out = {}
    for key, value in masks.items():
        if isinstance(value, dict):
            out[key] = {k: [int(x) for x in np.asarray(v)] for k, v in value.items()}
        elif isinstance(value, np.ndarray):
            out[key] = [int(x) for x in value]
        elif isinstance(value, (list, tuple)):
            out[key] = [int(x) for x in value]
        else:
            out[key] = int(value)
    return out


def _layer_keys(entry: dict):
    return sorted(entry, key=int)


# ==============================================================================
# COUNTING
# ==============================================================================

def count_masks(masks: dict) -> dict:
    """{granularity: {"active", "total", "per_layer": {layer: active}}}.

    `per_layer` lists only the layers with at least one live unit, so two
    circuits are size-matched exactly when their count dicts are equal.
    """
    out = {}
    for key, value in masks.items():
        if isinstance(value, dict):
            per = {k: int(np.asarray(v).sum()) for k, v in value.items()}
            total = int(sum(np.asarray(v).size for v in value.values()))
            out[key] = {"active": int(sum(per.values())), "total": total,
                        "per_layer": {k: c for k, c in sorted(per.items(), key=lambda kv: int(kv[0])) if c}}
        elif isinstance(value, (np.ndarray, list, tuple)):
            arr = np.asarray(value)
            out[key] = {"active": int(arr.sum()), "total": int(arr.size),
                        "per_layer": {str(i): int(v) for i, v in enumerate(arr) if v}}
        else:
            out[key] = {"active": int(value), "total": 1,
                        "per_layer": ({"-": int(value)} if value else {})}
    return out


def counts_equal(a: dict, b: dict) -> bool:
    """Do two count dicts describe circuits of identical per-layer size?"""
    return count_masks(a) == count_masks(b)


# ==============================================================================
# VALIDATION
# ==============================================================================

def validate_hierarchy(masks: dict, *, num_heads: int, head_dim: int,
                       label: str = "circuit") -> None:
    """Raise ValueError unless the mask object is hierarchically consistent.

    * a closed layer / block has no live children
    * a dead head has no live neurons
    * a live head has at least one live neuron — a head whose neurons are all
      dead is behaviourally identical to a dead head (head and neuron gates AND
      together), so allowing it would silently shrink the effective head count.
    """
    heads = masks.get("attention_heads", {})
    neurons = masks.get("attention_neurons", {})
    hidden = masks.get("mlp_hidden", {})
    output = masks.get("mlp_output", {})
    layers = masks.get("layers")
    attn_blocks = masks.get("attention_blocks")
    mlp_blocks = masks.get("mlp_blocks")

    problems = []
    n_layers = max([len(np.asarray(v)) for v in (layers, attn_blocks, mlp_blocks)
                    if v is not None] or [0])
    for l in range(n_layers):
        key = str(l)
        h = np.asarray(heads.get(key, []))
        nrn = np.asarray(neurons.get(key, []))
        hid = np.asarray(hidden.get(key, []))
        out = np.asarray(output.get(key, []))

        if layers is not None and not layers[l]:
            if h.sum() or nrn.sum() or hid.sum() or out.sum():
                problems.append(f"layer {l} is closed but has live children")
            continue

        if attn_blocks is not None and not attn_blocks[l] and (h.sum() or nrn.sum()):
            problems.append(f"layer {l}: attention block closed but has live heads/neurons")
        if mlp_blocks is not None and not mlp_blocks[l] and (hid.sum() or out.sum()):
            problems.append(f"layer {l}: mlp block closed but has live hidden/output units")

        if h.size and nrn.size:
            by_head = nrn.reshape(num_heads, head_dim).sum(axis=1)
            dead_head_live_neurons = int(((h == 0) & (by_head > 0)).sum())
            live_head_no_neurons = int(((h == 1) & (by_head == 0)).sum())
            if dead_head_live_neurons:
                problems.append(
                    f"layer {l}: {dead_head_live_neurons} dead head(s) with live neurons")
            if live_head_no_neurons:
                problems.append(
                    f"layer {l}: {live_head_no_neurons} live head(s) with no live neurons")

    if problems:
        raise ValueError(f"{label} violates the gate hierarchy:\n  "
                         + "\n  ".join(problems))


# ==============================================================================
# SET ALGEBRA — knockout / empty / full
# ==============================================================================

def _map_masks(masks: dict, fn):
    out = {}
    for key, value in masks.items():
        if isinstance(value, dict):
            out[key] = {k: fn(key, np.asarray(v)) for k, v in value.items()}
        elif isinstance(value, (np.ndarray, list, tuple)):
            out[key] = fn(key, np.asarray(value))
        else:
            out[key] = int(fn(key, np.asarray([value]))[0])
    return out


def knockout_masks(circuit_masks: dict, granularity: str = "finest") -> dict:
    """The circuit's complement — the model with the circuit removed.

    `finest` (default) holds every coarse gate wide open and complements only
    attention_neurons / mlp_hidden / mlp_output. Because head gates and neuron
    gates AND together, complementing the finest granularity alone ablates
    exactly the circuit's fine units and nothing else.

    `all` complements every granularity, which additionally shuts every block
    and head the circuit used — a much larger intervention.
    """
    if granularity not in ("finest", "all"):
        raise ValueError(f"granularity must be 'finest' or 'all', got {granularity!r}")

    if granularity == "all":
        return _map_masks(circuit_masks, lambda k, v: (1 - v).astype(np.uint8))

    def fn(key, v):
        if key in FINEST_KEYS:
            return (1 - v).astype(np.uint8)
        return np.ones_like(v, dtype=np.uint8)

    return _map_masks(circuit_masks, fn)


def assert_complement(circuit_masks: dict, knock_masks: dict,
                      keys=FINEST_KEYS) -> None:
    """`knockout AND circuit == 0` and `knockout OR circuit == 1` at `keys`."""
    for key in keys:
        if key not in circuit_masks:
            continue
        a, b = circuit_masks[key], knock_masks[key]
        entries = ([(f"{key}[{k}]", np.asarray(a[k]), np.asarray(b[k])) for k in a]
                   if isinstance(a, dict) else
                   [(key, np.asarray(a), np.asarray(b))])
        for label, x, y in entries:
            if (x & y).any():
                raise AssertionError(f"{label}: knockout overlaps the circuit")
            if not (x | y).all():
                raise AssertionError(f"{label}: knockout ∪ circuit is not everything")


def zeros_like(masks: dict) -> dict:
    """The empty circuit — every gate closed."""
    return _map_masks(masks, lambda k, v: np.zeros_like(v, dtype=np.uint8))


def ones_like(masks: dict) -> dict:
    """The full model — every gate open."""
    return _map_masks(masks, lambda k, v: np.ones_like(v, dtype=np.uint8))


# ==============================================================================
# RANDOM SIZE-MATCHED CIRCUITS
# ==============================================================================

def check_feasibility(circuit_masks: dict, num_heads: int, head_dim: int) -> dict:
    """Per-layer neuron budget check for the random sampler.

    A random circuit places `n_n` attention neurons inside `n_h` randomly drawn
    heads, so it needs `n_n <= n_h * head_dim`. The discovered circuit satisfies
    this by construction only when its neurons are spread over enough heads; a
    lower-sparsity run can violate it, so this raises early (and --dry-run calls
    it before any model is loaded).
    """
    heads = circuit_masks.get("attention_heads", {})
    neurons = circuit_masks.get("attention_neurons", {})
    report, problems = {}, []
    for key in _layer_keys(heads):
        n_h = int(np.asarray(heads[key]).sum())
        n_n = int(np.asarray(neurons.get(key, [])).sum())
        capacity = n_h * head_dim
        report[key] = {"heads": n_h, "neurons": n_n, "capacity": capacity,
                       "headroom": capacity - n_n}
        if n_n > capacity:
            problems.append(
                f"layer {key}: {n_n} attention neurons do not fit in {n_h} heads "
                f"({n_h} x {head_dim} = {capacity} slots)")
        if n_h == 0 and n_n > 0:
            problems.append(f"layer {key}: {n_n} neurons but no live heads")
    if problems:
        raise ValueError("random circuits are infeasible for this circuit:\n  "
                         + "\n  ".join(problems))
    return report


def _draw_neurons_uniform(rng, drawn_heads, n_neurons, head_dim):
    """Neuron slots for the drawn heads: one per head first, then the rest.

    Seeding every drawn head guarantees the exact neuron count *and* that no
    drawn head ends up empty — an empty head is a dead head, which would quietly
    drop the effective head count below the size match.
    """
    n_h = len(drawn_heads)
    base = drawn_heads.astype(np.int64) * head_dim
    first = base + rng.integers(0, head_dim, size=n_h)
    remaining = n_neurons - n_h
    if remaining <= 0:
        return first
    pool = (base[:, None] + np.arange(head_dim)).ravel()
    leftover = np.setdiff1d(pool, first, assume_unique=False)
    extra = rng.choice(leftover, size=remaining, replace=False)
    return np.concatenate([first, extra])


def _draw_neurons_perhead(rng, drawn_heads, per_head_counts, head_dim):
    """Preserve the discovered circuit's per-head count multiset, shuffled onto
    the drawn heads — a tighter null that also controls concentration."""
    counts = np.asarray(per_head_counts, dtype=np.int64).copy()
    rng.shuffle(counts)
    slots = []
    for head, c in zip(drawn_heads, counts):
        dims = rng.choice(head_dim, size=int(c), replace=False)
        slots.append(int(head) * head_dim + dims)
    return np.concatenate(slots) if slots else np.zeros(0, dtype=np.int64)


def sample_random_masks(circuit_masks: dict, *, num_heads: int, head_dim: int,
                        seed: int, index: int, alloc: str = "uniform") -> dict:
    """One random circuit, size-matched to `circuit_masks` layer by layer.

    Blocks (and full layers) are copied verbatim — they are held fixed by
    design, so the null asks "does *this* allocation of heads and neurons
    matter?" rather than "does this depth profile matter?".

    The RNG stream is derived from (seed, index), so sample k is reproducible
    independent of loop order and `--null-start/--null-count` can shard across
    an sbatch array without changing a single number.
    """
    if alloc not in ("uniform", "perhead"):
        raise ValueError(f"alloc must be 'uniform' or 'perhead', got {alloc!r}")

    rng = np.random.default_rng([seed, index])
    out = {}

    for key in SCALAR_KEYS + BLOCK_KEYS:
        if key in circuit_masks:
            value = circuit_masks[key]
            out[key] = int(value) if np.isscalar(value) else np.asarray(value).copy()

    heads = circuit_masks.get("attention_heads")
    neurons = circuit_masks.get("attention_neurons")
    hidden = circuit_masks.get("mlp_hidden")
    output = circuit_masks.get("mlp_output")

    attn_blocks = circuit_masks.get("attention_blocks")
    mlp_blocks = circuit_masks.get("mlp_blocks")
    layers = circuit_masks.get("layers")

    if heads is not None:
        out["attention_heads"] = {}
        if neurons is not None:
            out["attention_neurons"] = {}
        for key in _layer_keys(heads):
            l = int(key)
            src_h = np.asarray(heads[key])
            new_h = np.zeros_like(src_h, dtype=np.uint8)
            src_n = np.asarray(neurons[key]) if neurons is not None else None
            new_n = np.zeros_like(src_n, dtype=np.uint8) if src_n is not None else None

            block_open = (attn_blocks is None or bool(attn_blocks[l])) and \
                         (layers is None or bool(layers[l]))
            n_h = int(src_h.sum())
            if block_open and n_h:
                drawn = rng.choice(num_heads, size=n_h, replace=False)
                new_h[drawn] = 1
                if new_n is not None:
                    n_n = int(src_n.sum())
                    if n_n > n_h * head_dim:
                        raise ValueError(
                            f"layer {key}: {n_n} attention neurons do not fit in "
                            f"{n_h} heads ({n_h} x {head_dim} slots)")
                    if alloc == "uniform":
                        slots = _draw_neurons_uniform(rng, drawn, n_n, head_dim)
                    else:
                        by_head = src_n.reshape(num_heads, head_dim).sum(axis=1)
                        slots = _draw_neurons_perhead(
                            rng, drawn, by_head[src_h.astype(bool)], head_dim)
                    new_n[slots] = 1

            out["attention_heads"][key] = new_h
            if new_n is not None:
                out["attention_neurons"][key] = new_n

    for name, src in (("mlp_hidden", hidden), ("mlp_output", output)):
        if src is None:
            continue
        out[name] = {}
        for key in _layer_keys(src):
            l = int(key)
            vec = np.asarray(src[key])
            new = np.zeros_like(vec, dtype=np.uint8)
            block_open = (mlp_blocks is None or bool(mlp_blocks[l])) and \
                         (layers is None or bool(layers[l]))
            k = int(vec.sum())
            if block_open and k:
                new[rng.choice(vec.size, size=k, replace=False)] = 1
            out[name][key] = new

    return out


def sample_random_mask_set(circuit_masks: dict, *, num_heads: int, head_dim: int,
                           seed: int, n: int, alloc: str = "uniform",
                           start: int = 0, validate: bool = True) -> list:
    """`n` random circuits for indices start .. start + n - 1."""
    check_feasibility(circuit_masks, num_heads, head_dim)
    samples = []
    for index in range(start, start + n):
        m = sample_random_masks(circuit_masks, num_heads=num_heads,
                                head_dim=head_dim, seed=seed, index=index,
                                alloc=alloc)
        if validate:
            validate_hierarchy(m, num_heads=num_heads, head_dim=head_dim,
                               label=f"random circuit {index}")
        samples.append(m)
    return samples


def save_packed_masks(path: str, masks_list, indices) -> str:
    """Bit-pack a list of mask objects into one npz (only for --save-null-masks;
    the set is exactly regenerable from (seed, n, alloc, algorithm_version))."""
    arrays = {"indices": np.asarray(indices, dtype=np.int64)}
    for i, masks in zip(indices, masks_list):
        for key, value in masks.items():
            if isinstance(value, dict):
                for l, v in value.items():
                    arrays[f"{i}/{key}/{l}"] = np.packbits(np.asarray(v, dtype=np.uint8))
            elif isinstance(value, np.ndarray):
                arrays[f"{i}/{key}"] = np.packbits(value)
            else:
                arrays[f"{i}/{key}"] = np.asarray([value], dtype=np.uint8)
    np.savez_compressed(path, **arrays)
    return path
