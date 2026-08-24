"""
evaluation/algebra.py — set algebra over saved node circuits.

Two things live here:

  * a tiny recursive-descent parser for circuit expressions

        expr := term ( '|' term )*                 union, lowest precedence
        term := atom ( ('&' | '\\' | '-') atom )*  intersection / difference
        atom := NAME | '(' expr ')'

    `-` is an alias for `\\`. NAME is `[A-Za-z0-9_]+` and refers to a circuit
    bound on the command line with `--circuit NAME=RUN_DIR`. There is no
    `eval()` anywhere near this.

  * `compose`, which turns such an expression plus its operand mask objects
    into a new mask object.

Membership is never defined on the coarse gates directly — "layer 7 minus
layer 7" is not a meaningful set operation, and doing it at block granularity
would silently discard the within-block selection that makes a circuit a
circuit. Instead there are two granularities, and the plan calls for computing
both and evaluating them as separate cells:

  leaf  membership is the finest gates (attention_neurons / mlp_hidden /
        mlp_output). Set ops apply elementwise; every coarse gate is then
        re-derived bottom-up.

  head  membership is `attention_heads` + `mlp_blocks`. Set ops apply to those;
        the fine gates under each surviving parent are the OR over exactly
        those operands whose parent gate is live at that position.

In both modes the coarse gates are re-derived from the fine ones

    head[l, h]    = any(attention_neurons[l][h*head_dim : (h+1)*head_dim])   (leaf only)
    attn_block[l] = any(head[l, :])
    mlp_block[l]  = any(mlp_hidden[l]) or any(mlp_output[l])
    layer[l]      = attn_block[l] or mlp_block[l]

so `masks.validate_hierarchy` passes by construction.

`embedding` is deliberately *not* a member of the set. Every trained circuit
has `embedding = 1`, so treating it as one would make `A\\B` run its
sufficiency forward on a corrupted embedding stream — measuring the embedding
ablation, not the set difference. It is instead the OR of the operands'
embedding gates. (Real saved circuits from this repo have no `embedding` and
no `layers` key at all; both are handled by absence.)
"""

from __future__ import annotations

import re

import numpy as np

from evaluation.masks import FINEST_KEYS

#: Granularities `compose` understands.
GRANULARITIES = ("leaf", "head")

#: What membership means, per granularity.
MEMBERSHIP_KEYS = {
    "leaf": FINEST_KEYS,
    "head": ("attention_heads", "mlp_blocks"),
}

#: Operator -> slug fragment, used to name a cell directory.
_OP_SLUG = {"|": "or", "&": "and", "\\": "minus"}

_NAME_RE = re.compile(r"[A-Za-z0-9_]+")
_TOKEN_RE = re.compile(r"\s*([A-Za-z0-9_]+|[()|&\\-])")


class ExprError(ValueError):
    """A circuit expression could not be parsed or resolved."""


# ==============================================================================
# PARSING
# ==============================================================================

def _tokenize(text: str):
    text = text.strip()
    tokens, pos = [], 0
    while pos < len(text):
        match = _TOKEN_RE.match(text, pos)
        if not match:
            rest = text[pos:].strip()
            raise ExprError(
                f"cannot parse circuit expression {text!r}: unexpected character "
                f"{rest[0]!r} at position {pos}. Names are [A-Za-z0-9_]+ and the "
                f"operators are | & \\ - ( ).")
        token = match.group(1)
        tokens.append(("-" if token == "-" else token))
        pos = match.end()
    if not tokens:
        raise ExprError("empty circuit expression")
    return tokens


def parse_expr(text: str) -> tuple:
    """Parse an expression into a tree of `('name', str)` / `(op, left, right)`."""
    tokens = _tokenize(text)
    state = {"i": 0}

    def peek():
        return tokens[state["i"]] if state["i"] < len(tokens) else None

    def take():
        token = peek()
        state["i"] += 1
        return token

    def parse_atom():
        token = take()
        if token is None:
            raise ExprError(
                f"cannot parse circuit expression {text!r}: expression ends after "
                f"an operator — expected a circuit name.")
        if token == "(":
            node = parse_or()
            if peek() != ")":
                raise ExprError(
                    f"cannot parse circuit expression {text!r}: unbalanced '(' — "
                    f"expected ')'.")
            take()
            return node
        if _NAME_RE.fullmatch(token):
            return ("name", token)
        raise ExprError(
            f"cannot parse circuit expression {text!r}: expected a circuit name "
            f"or '(', got {token!r}.")

    def parse_and():
        node = parse_atom()
        while peek() in ("&", "\\", "-"):
            op = take()
            node = ("\\" if op == "-" else op, node, parse_atom())
        return node

    def parse_or():
        node = parse_and()
        while peek() == "|":
            take()
            node = ("|", node, parse_and())
        return node

    tree = parse_or()
    if state["i"] != len(tokens):
        leftover = tokens[state["i"]]
        hint = " — unbalanced ')'" if leftover == ")" else ""
        raise ExprError(
            f"cannot parse circuit expression {text!r}: trailing {leftover!r}{hint}.")
    return tree


def expr_names(tree: tuple) -> list:
    """Circuit names referenced by a tree, in first-appearance order."""
    out = []

    def walk(node):
        if node[0] == "name":
            if node[1] not in out:
                out.append(node[1])
        else:
            walk(node[1])
            walk(node[2])

    walk(tree)
    return out


def validate_names(tree: tuple, available) -> None:
    available = list(available)
    for name in expr_names(tree):
        if name not in available:
            raise ExprError(
                f"unknown circuit {name!r} in expression — bound circuits are "
                f"{available}. Bind one with --circuit {name}=RUN_DIR.")


def format_expr(tree: tuple) -> str:
    """Canonical, fully parenthesised rendering (provenance / error messages)."""
    if tree[0] == "name":
        return tree[1]
    return f"({format_expr(tree[1])} {tree[0]} {format_expr(tree[2])})"


def slug_for(tree: tuple) -> str:
    """Directory-safe cell name: `far`, `far_minus_sdr`, `far_and_sdr_or_ser`.

    Grouping parentheses are *not* encoded — two differently-grouped
    expressions can flatten to the same slug, so the suite dedupes labels and
    `--expr LABEL=EXPR` exists to name a cell explicitly.
    """
    if tree[0] == "name":
        return tree[1]
    return f"{slug_for(tree[1])}_{_OP_SLUG[tree[0]]}_{slug_for(tree[2])}"


def is_atomic(tree: tuple) -> bool:
    return tree[0] == "name"


# ==============================================================================
# SUGAR
# ==============================================================================

def expand_xor(names) -> list:
    """`--xor A,B,C` -> [(label, expr), ...] = A\\B\\C, B\\A\\C, C\\A\\B.

    The exclusive-or family: what each circuit has that none of its siblings do.
    """
    names = list(names)
    if len(names) < 2:
        raise ExprError(f"--xor needs at least two circuit names, got {names}.")
    out = []
    for name in names:
        others = [n for n in names if n != name]
        expr = name + "".join(f"\\{other}" for other in others)
        out.append((slug_for(parse_expr(expr)), expr))
    return out


def expand_all_pairs_delta(names) -> list:
    """Every ordered `X\\Y` over the bound circuits."""
    names = list(names)
    if len(names) < 2:
        raise ExprError(
            f"--all-pairs-delta needs at least two bound circuits, got {names}.")
    out = []
    for left in names:
        for right in names:
            if left == right:
                continue
            expr = f"{left}\\{right}"
            out.append((slug_for(parse_expr(expr)), expr))
    return out


# ==============================================================================
# COMPOSITION
# ==============================================================================

def _bool(value) -> np.ndarray:
    return np.asarray(value, dtype=np.uint8).astype(bool)


def _eval_tree(tree: tuple, get):
    """Evaluate a tree where `get(name)` returns a boolean array."""
    if tree[0] == "name":
        return get(tree[1])
    left = _eval_tree(tree[1], get)
    right = _eval_tree(tree[2], get)
    if tree[0] == "|":
        return left | right
    if tree[0] == "&":
        return left & right
    return left & ~right  # '\\'


def _operand_keys(operands: dict) -> list:
    """The mask keys shared by every operand; raise if they disagree."""
    names = list(operands)
    reference = set(operands[names[0]])
    for name in names[1:]:
        if set(operands[name]) != reference:
            missing = reference.symmetric_difference(set(operands[name]))
            raise ExprError(
                f"circuits {names[0]!r} and {name!r} have different mask "
                f"granularities (differing keys: {sorted(missing)}). Set "
                f"algebra needs circuits trained with the same pruning "
                f"granularities.")
    return sorted(reference)


def _layer_ids(operands: dict, key: str) -> list:
    for masks in operands.values():
        entry = masks.get(key)
        if isinstance(entry, dict):
            return sorted(entry, key=int)
    return []


def _n_layers(operands: dict) -> int:
    for masks in operands.values():
        for key in ("attention_blocks", "mlp_blocks", "layers"):
            value = masks.get(key)
            if value is not None and not isinstance(value, dict):
                return int(np.asarray(value).size)
        for key in ("attention_heads", "attention_neurons", "mlp_hidden"):
            entry = masks.get(key)
            if isinstance(entry, dict) and entry:
                return max(int(k) for k in entry) + 1
    return 0


def compose(tree: tuple, operands: dict, *, granularity: str,
            num_heads: int, head_dim: int) -> dict:
    """Apply a circuit expression to a dict of `name -> mask object`.

    Returns a fresh mask object (uint8 arrays) whose coarse gates have been
    re-derived bottom-up, so it satisfies `masks.validate_hierarchy`.

    Only the operands named in `tree` participate; the rest are ignored.
    """
    if granularity not in GRANULARITIES:
        raise ExprError(
            f"compose granularity must be one of {GRANULARITIES}, got {granularity!r}")
    validate_names(tree, operands)
    used = {name: operands[name] for name in expr_names(tree)}
    keys = _operand_keys(used)

    if granularity == "leaf":
        result = _compose_leaf(tree, used, keys, num_heads=num_heads, head_dim=head_dim)
    else:
        result = _compose_head(tree, used, keys, num_heads=num_heads, head_dim=head_dim)

    # `embedding` is not a set member — see the module docstring.
    if "embedding" in keys:
        result["embedding"] = int(any(int(masks["embedding"]) for masks in used.values()))
    return result


def _compose_leaf(tree, used, keys, *, num_heads, head_dim) -> dict:
    result = {}
    for key in FINEST_KEYS:
        if key not in keys:
            continue
        out = {}
        for layer in _layer_ids(used, key):
            out[layer] = _eval_tree(
                tree, lambda name, l=layer, k=key: _bool(used[name][k][l])
            ).astype(np.uint8)
        result[key] = out
    _derive_coarse(result, used, keys, num_heads=num_heads, head_dim=head_dim,
                   derive_heads=True)
    return result


def _compose_head(tree, used, keys, *, num_heads, head_dim) -> dict:
    result = {}

    # --- membership: head gates + mlp-block gates -------------------------
    heads = {}
    if "attention_heads" in keys:
        for layer in _layer_ids(used, "attention_heads"):
            heads[layer] = _eval_tree(
                tree, lambda name, l=layer: _bool(used[name]["attention_heads"][l])
            ).astype(np.uint8)
        result["attention_heads"] = heads

    mlp_blocks = None
    if "mlp_blocks" in keys:
        mlp_blocks = _eval_tree(
            tree, lambda name: _bool(used[name]["mlp_blocks"])).astype(np.uint8)
        result["mlp_blocks"] = mlp_blocks

    # --- fine gates: OR over the operands whose parent is live here -------
    if "attention_neurons" in keys:
        out = {}
        for layer in _layer_ids(used, "attention_neurons"):
            size = int(np.asarray(next(iter(used.values()))["attention_neurons"][layer]).size)
            acc = np.zeros(size, dtype=bool)
            live_head = heads.get(layer)
            for masks in used.values():
                parent = _bool(masks["attention_heads"][layer]) if "attention_heads" in keys \
                    else np.ones(num_heads, dtype=bool)
                gate = np.repeat(parent, head_dim)[:size]
                acc |= gate & _bool(masks["attention_neurons"][layer])
            if live_head is not None:
                acc &= np.repeat(_bool(live_head), head_dim)[:size]
                # A surviving head with no surviving neuron is behaviourally
                # dead (head and neuron gates AND together) and would trip
                # validate_hierarchy, so close it.
                heads[layer] = (_bool(live_head)
                                & acc.reshape(len(live_head), -1).any(axis=1)).astype(np.uint8)
            out[layer] = acc.astype(np.uint8)
        result["attention_neurons"] = out

    for key in ("mlp_hidden", "mlp_output"):
        if key not in keys:
            continue
        out = {}
        for layer in _layer_ids(used, key):
            size = int(np.asarray(next(iter(used.values()))[key][layer]).size)
            acc = np.zeros(size, dtype=bool)
            for masks in used.values():
                if mlp_blocks is not None and not mlp_blocks_live(masks, layer):
                    continue
                acc |= _bool(masks[key][layer])
            if mlp_blocks is not None and not bool(mlp_blocks[int(layer)]):
                acc[:] = False
            out[layer] = acc.astype(np.uint8)
        result[key] = out

    _derive_coarse(result, used, keys, num_heads=num_heads, head_dim=head_dim,
                   derive_heads=False)
    return result


def mlp_blocks_live(masks: dict, layer) -> bool:
    """Is this operand's MLP block open at `layer`? (True when there is no gate.)"""
    blocks = masks.get("mlp_blocks")
    if blocks is None:
        return True
    return bool(np.asarray(blocks)[int(layer)])


def _derive_coarse(result: dict, used: dict, keys, *, num_heads, head_dim,
                   derive_heads: bool) -> None:
    """Rebuild every coarse gate from the fine gates, in place."""
    n_layers = _n_layers(used)

    if derive_heads and "attention_heads" in keys:
        heads = {}
        neurons = result.get("attention_neurons", {})
        for layer in _layer_ids(used, "attention_heads"):
            size = int(np.asarray(used[next(iter(used))]["attention_heads"][layer]).size)
            vector = np.asarray(neurons.get(layer, np.zeros(0, dtype=np.uint8)))
            if vector.size:
                by_head = vector.reshape(size, -1).any(axis=1)
            else:
                by_head = np.zeros(size, dtype=bool)
            heads[layer] = by_head.astype(np.uint8)
        result["attention_heads"] = heads

    if "attention_blocks" in keys:
        blocks = np.zeros(n_layers, dtype=np.uint8)
        heads = result.get("attention_heads", {})
        neurons = result.get("attention_neurons", {})
        for l in range(n_layers):
            key = str(l)
            live = bool(np.asarray(heads.get(key, [])).any()) or \
                bool(np.asarray(neurons.get(key, [])).any())
            blocks[l] = 1 if live else 0
        result["attention_blocks"] = blocks

    if "mlp_blocks" in keys:
        blocks = np.zeros(n_layers, dtype=np.uint8)
        for l in range(n_layers):
            key = str(l)
            live = any(bool(np.asarray(result.get(k, {}).get(key, [])).any())
                       for k in ("mlp_hidden", "mlp_output"))
            blocks[l] = 1 if live else 0
        result["mlp_blocks"] = blocks

    if "layers" in keys:
        attn = np.asarray(result.get("attention_blocks", np.zeros(n_layers, dtype=np.uint8)))
        mlp = np.asarray(result.get("mlp_blocks", np.zeros(n_layers, dtype=np.uint8)))
        result["layers"] = ((attn.astype(bool)) | (mlp.astype(bool))).astype(np.uint8)


# ==============================================================================
# EMPTINESS
# ==============================================================================

def live_fine_units(masks: dict) -> int:
    """Total live units across the finest granularities."""
    total = 0
    for key in FINEST_KEYS:
        entry = masks.get(key)
        if isinstance(entry, dict):
            total += int(sum(int(np.asarray(v).sum()) for v in entry.values()))
        elif entry is not None:
            total += int(np.asarray(entry).sum())
    return total


def emptiness_warning(label: str, masks: dict) -> str:
    """A one-line warning when a composed circuit came out (near-)empty, else ''.

    Composed circuits going empty is a *result*, not a crash — `A\\A` is
    legitimately empty, and `far\\sdr\\ser` being nearly so is exactly the
    specificity finding the suite is looking for.
    """
    live = live_fine_units(masks)
    if live == 0:
        return (f"  WARNING: circuit '{label}' is empty (0 live fine units) — "
                f"its sufficiency run is the fully-ablated model.")
    if live < 100:
        return (f"  WARNING: circuit '{label}' has only {live} live fine units.")
    return ""
