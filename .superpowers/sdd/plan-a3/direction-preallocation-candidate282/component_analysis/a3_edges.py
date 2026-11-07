"""A3 local incoming-residual IG and simultaneous intact-delta clamps.

No cohort selection, bootstrap draws, model loading, or phase admission occurs
here. ``edge_grid`` accepts ONE frozen task view (``edge_nodes``) and geometry
with HF dimension names plus explicit ``position_cells``. Each cell has unique
``key``, ``semantic_bin`` and ``receiver_kinds``; edges retain that exact spec.
Native tuple sites use query-head Q and deduplicated KV-group K/V indices.

Batches are native-forward dictionaries plus ``condition``, ``stream``, unique
``instance_ids``, ``position_cells`` keyed by cell key, and ``positions`` keyed
by cell key. Positions are integer [batch] or ragged lists of absolute token
indices per row. Each selected cell must be supported and nonempty in EVERY
row; split unsupported rows before calling. Padding/duplicate/borrowed indices
are rejected, never clamped. Distinct token cells may be aggregated into a bin
only by the caller; a multi-token cell sums its token contractions.

``maps={'rows': [...]}`` carries one supported builder record per batch row,
with recipient_id/donor_id, recipient_stream/donor_stream,
recipient_condition, donor_condition and injective
recipient_positions/donor_positions lists. These are source-authorized maps,
not maps inferred here from sequence lengths. Shared instance_id/stream is a
shorthand for twins with identical row identity and stream. Explicit identities
and streams also support the frozen IOI corrupt donor. Same-condition designation donors
and D/H or I/user_neutral twins are allowed; D/I splices are forbidden. Utility
donors must be supplied by their owning adapter; none is synthesized here.

Attribution input items are ``{batch, neutral, maps, weights?}``; margin labels
are batch ``opposite_token`` and ``honest_token``. Optional row weights are
cohort-normalized (sum one over the whole iterable), e.g. caller-owned cluster
multiplicity and paired-stream weights. Without weights all rows weigh equally.
Only one batch/receiver graph is live. Captures are detached; only relevant
sender/receiver caches are retained, and no full-vocabulary graphs escape.

Scores rank the local neutral-to-condition incoming-residual path. They are not
necessity estimates. Exact sets instead use fixed intact/donor sender deltas;
a downstream clamp (including readout) can block upstream selected effects.
Incomplete real graphs cannot promise whole-prompt donor endpoint recovery.
"""

from __future__ import annotations

import copy
import math
from collections import defaultdict

import torch

from component_analysis.a3_native import (
    ResidualPatch,
    causally_upstream,
    native_forward,
    receiver_sites,
)


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _site(value):
    _require(
        isinstance(value, (tuple, list))
        and len(value) == 3
        and isinstance(value[0], str)
        and all(type(x) is int and x >= 0 for x in value[1:]),
        "malformed site",
    )
    return tuple(value)


def _cell(spec):
    _require(
        isinstance(spec, dict)
        and set(spec) == {"key", "semantic_bin", "receiver_kinds"},
        "position cell needs exact frozen metadata",
    )
    _require(
        isinstance(spec["key"], str)
        and bool(spec["key"])
        and spec["semantic_bin"]
        in ("pressure_request", "item_designation", "question", "assistant_readout"),
        "invalid position key/bin",
    )
    kinds = spec["receiver_kinds"]
    _require(
        isinstance(kinds, list)
        and kinds
        and len(set(kinds)) == len(kinds)
        and set(kinds) <= {"q", "k", "v", "mlp_in", "readout"},
        "invalid receiver kinds",
    )
    return spec


def _key(edge):
    _require(
        isinstance(edge, dict)
        and set(edge) == {"sender", "receiver", "position", "position_spec"},
        "malformed edge schema",
    )
    spec = _cell(edge["position_spec"])
    sender, receiver = _site(edge["sender"]), _site(edge["receiver"])
    _require(
        edge["position"] == spec["key"] and receiver[0] in spec["receiver_kinds"],
        "changed position geometry or receiver kind",
    )
    _require(
        causally_upstream(sender, receiver, 0, 0),
        "future-to-past or unsupported residual edge",
    )
    return sender, receiver, edge["position"]


def edge_grid(design, geometry):
    """Pure frozen graph, ordered by execution layer then deterministic site/key."""
    dims = [
        geometry.get(k)
        for k in ("num_hidden_layers", "num_attention_heads", "num_key_value_heads")
    ]
    _require(all(type(x) is int and x > 0 for x in dims), "invalid geometry")
    layers, heads, groups = dims
    _require(heads % groups == 0, "invalid GQA geometry")
    cells = geometry.get("position_cells")
    _require(
        isinstance(cells, list) and cells, "explicit frozen position cells required"
    )
    for c in cells:
        _cell(c)
    _require(
        len({c["key"] for c in cells}) == len(cells), "duplicate position cell key"
    )
    signatures = [
        (c["semantic_bin"], tuple(sorted(c["receiver_kinds"]))) for c in cells
    ]
    _require(len(set(signatures)) == len(signatures), "aliased semantic position cells")
    nodes = [_site(n) for n in design["edge_nodes"]]
    _require(
        nodes and len(nodes) == len(set(nodes)), "empty/duplicate frozen edge nodes"
    )
    _require(
        all(
            k in ("head", "mlp")
            and layer < layers
            and i < (heads if k == "head" else 1)
            for k, layer, i in nodes
        ),
        "node outside geometry",
    )
    receivers = {("readout", 0, 0)}
    for k, layer, i in nodes:
        if k == "head":
            receivers.update(
                {
                    ("q", layer, i),
                    ("k", layer, i // (heads // groups)),
                    ("v", layer, i // (heads // groups)),
                }
            )
        else:
            receivers.add(("mlp_in", layer, 0))
    result = []
    for sender in sorted(nodes):
        for receiver in sorted(receivers):
            if causally_upstream(sender, receiver, 0, 0):
                for c in sorted(cells, key=lambda x: x["key"]):
                    if receiver[0] in c["receiver_kinds"]:
                        result.append(
                            dict(
                                sender=sender,
                                receiver=receiver,
                                position=c["key"],
                                position_spec=copy.deepcopy(c),
                            )
                        )
    return sorted(
        result,
        key=lambda e: (
            e["sender"][1],
            e["sender"],
            layers if e["receiver"][0] == "readout" else e["receiver"][1],
            e["receiver"],
            e["position"],
        ),
    )


def _positions(batch, key):
    value = batch.get("positions", {}).get(key)
    n = batch["input_ids"].shape[0]
    if isinstance(value, torch.Tensor):
        _require(
            value.dtype in (torch.int32, torch.int64) and value.shape == (n,),
            "positions tensor must be integer [batch]; use ragged lists for spans",
        )
        value = [[p] for p in value.cpu().tolist()]
    _require(
        isinstance(value, list) and len(value) == n, "missing/unsupported position cell"
    )
    result = []
    for row, pos in enumerate(value):
        _require(
            isinstance(pos, list)
            and bool(pos)
            and all(type(p) is int for p in pos)
            and len(set(pos)) == len(pos),
            "unsupported/empty/duplicate position bin",
        )
        _require(
            all(
                0 <= p < batch["input_ids"].shape[1]
                and batch["attention_mask"][row, p] == 1
                for p in pos
            ),
            "invalid position or padding",
        )
        result.append(sorted(pos))
    return result


def _validate(model, batch, donor, selected, maps):
    keys = [_key(e) for e in selected]
    _require(len(set(keys)) == len(keys), "duplicate edge key")
    allowed = set(receiver_sites(model))
    cfg = model.config
    cells, specs = {}, {}
    for e, (s, r, p) in zip(selected, keys):
        _require(
            r in allowed
            and s[0] in ("head", "mlp")
            and s[1] < cfg.num_hidden_layers
            and s[2] < (cfg.num_attention_heads if s[0] == "head" else 1),
            "site outside model geometry",
        )
        spec = e["position_spec"]
        _require(
            batch.get("position_cells", {}).get(p) == spec,
            "changed/missing frozen position geometry",
        )
        _require(p not in specs or specs[p] == spec, "position metadata alias")
        specs[p] = spec
        cells[p] = _positions(batch, p)
    # Distinct cells cannot count a physical token twice for a receiver kind.
    for a in cells:
        for b in cells:
            if a < b and set(specs[a]["receiver_kinds"]) & set(
                specs[b]["receiver_kinds"]
            ):
                _require(
                    not any(set(x) & set(y) for x, y in zip(cells[a], cells[b])),
                    "aliased semantic position cells",
                )
    n = batch["input_ids"].shape[0]
    _require(donor["input_ids"].shape[0] == n, "donor batch size mismatch")
    ids = batch.get("instance_ids")
    _require(
        isinstance(ids, list)
        and len(ids) == n
        and len(set(ids)) == n
        and isinstance(donor.get("instance_ids"), list)
        and len(donor["instance_ids"]) == n
        and len(set(donor["instance_ids"])) == n,
        "row identity mismatch",
    )
    records = maps.get("rows") if isinstance(maps, dict) else None
    _require(
        isinstance(records, list) and len(records) == n,
        "one builder map per row required",
    )
    rc, dc = batch.get("condition"), donor.get("condition")
    _require(
        isinstance(rc, str)
        and isinstance(dc, str)
        and (
            rc == dc
            or frozenset((rc, dc))
            in (frozenset(("D", "H")), frozenset(("I", "user_neutral")))
        ),
        "unsupported cross-condition map; D/I splice forbidden",
    )
    _require(
        batch.get("stream") in ("clean", "corrupt")
        and donor.get("stream") in ("clean", "corrupt"),
        "missing/invalid batch stream",
    )
    mapping = []
    for row, record in enumerate(records):
        _require(
            isinstance(record, dict)
            and record.get("supported") is True
            and record.get("recipient_id", record.get("instance_id")) == ids[row]
            and record.get("donor_id", record.get("instance_id"))
            == donor["instance_ids"][row]
            and record.get("recipient_stream", record.get("stream")) == batch["stream"]
            and record.get("donor_stream", record.get("stream")) == donor["stream"]
            and record.get("recipient_condition") == rc
            and record.get("donor_condition") == dc,
            "unsupported map or row/condition/stream mismatch",
        )
        left, right = record.get("recipient_positions"), record.get("donor_positions")
        _require(
            isinstance(left, list)
            and isinstance(right, list)
            and bool(left)
            and len(left) == len(right)
            and all(type(p) is int for p in left + right)
            and len(set(left)) == len(left)
            and len(set(right)) == len(right),
            "malformed/duplicate builder map",
        )
        _require(
            all(
                0 <= p < batch["input_ids"].shape[1]
                and batch["attention_mask"][row, p] == 1
                for p in left
            )
            and all(
                0 <= p < donor["input_ids"].shape[1]
                and donor["attention_mask"][row, p] == 1
                for p in right
            ),
            "builder map out of bounds or padding",
        )
        m = dict(zip(left, right))
        _require(
            all(set(pos[row]) <= set(m) for pos in cells.values()),
            "selected position absent in supported map",
        )
        mapping.append(m)
    return keys, cells, mapping


def exact_edge_patch(model, batch, donor, *, edges, maps):
    """Simultaneously clamp branches from fixed caches; return actual outputs.

    ``clamps`` are full pre-norm residual values, applied only under each
    ``patch_positions`` mask. ``receiver_outputs`` are the actual native
    post-norm/projection slices (readout = pre-final-norm residual).
    """
    keys, cells, mapping = _validate(model, batch, donor, edges, maps)
    sources = sorted({s for s, _, _ in keys})
    receivers = sorted({r for _, r, _ in keys})
    # Keep the graph-free cache on CPU, not a set of full layer/vocabulary graphs.
    intact = native_forward(model, batch, capture_sites=sources + receivers)
    source = {s: intact["additive"][s].cpu() for s in sources}
    incoming = {r: intact["incoming"][r].cpu() for r in receivers}
    del intact
    other = native_forward(model, donor, capture_sites=sources)
    other_source = {s: other["additive"][s].cpu() for s in sources}
    del other
    grouped = defaultdict(list)
    for s, r, p in sorted(keys):
        grouped[r].append((s, p))
    device = batch["input_ids"].device
    clamps, masks, patches = {}, {}, {}
    for r in receivers:
        value = incoming[r].clone()
        mask = torch.zeros(batch["input_ids"].shape, dtype=torch.bool)
        # Sorted additions use fixed intact/donor tensors, never changed senders.
        for s, cell in grouped[r]:
            for row, positions in enumerate(cells[cell]):
                for p in positions:
                    value[row, p] += (
                        other_source[s][row, mapping[row][p]] - source[s][row, p]
                    )
                    mask[row, p] = True
        clamps[r], masks[r] = value.to(device), mask.to(device)
        patches[r] = ResidualPatch(clamps[r], masks[r])
    out = native_forward(model, batch, capture_sites=receivers, patches=patches)
    return dict(
        logits=out["logits"],
        fp32_logits=out["fp32_logits"].detach(),
        clamps=clamps,
        patch_positions=masks,
        receiver_outputs=out["outputs"],
        estimand="simultaneous intact-delta receiver clamping",
    )


def _margin(out, batch):
    logits = out["fp32_logits"]
    rows = torch.arange(logits.shape[0], device=logits.device)
    labels = []
    for name in ("opposite_token", "honest_token"):
        label = torch.as_tensor(batch.get(name), device=logits.device)
        _require(
            label.dtype in (torch.int32, torch.int64)
            and label.shape == rows.shape
            and bool(((label >= 0) & (label < logits.shape[1])).all()),
            "invalid canonical margin labels",
        )
        labels.append(label)
    _require(
        bool((labels[0] != labels[1]).all()), "canonical margin labels must differ"
    )
    return logits[rows, labels[0]] - logits[rows, labels[1]]


def attribute_edges(model, batches, *, edges, steps=8):
    """Midpoint local-branch IG, signed condition-minus-neutral source delta.

    One receiver alone becomes a leaf; all downstream branches stay live.
    Results preserve caller edge order and contain only scalar detached scores.
    """
    _require(type(steps) is int and steps > 0, "positive integration steps required")
    keys = [_key(e) for e in edges]
    _require(len(set(keys)) == len(keys), "duplicate edge key")
    totals = torch.zeros(len(edges), dtype=torch.float64)
    total_weight, count, explicit = 0.0, 0, None
    tokens = [0] * len(edges)
    grouped = defaultdict(list)
    for index, (s, r, p) in enumerate(keys):
        grouped[r].append((index, s, p))
    for item in batches:
        batch, neutral = item["batch"], item["neutral"]
        _, cells, mapping = _validate(model, batch, neutral, edges, item["maps"])
        n = batch["input_ids"].shape[0]
        for index, (_, _, cell) in enumerate(keys):
            tokens[index] += sum(len(p) for p in cells[cell])
        has_weights = "weights" in item
        _require(
            explicit is None or explicit == has_weights,
            "cannot mix explicit and implicit weights",
        )
        explicit = has_weights
        weights = torch.as_tensor(item.get("weights", [1.0] * n), dtype=torch.float64)
        _require(
            weights.shape == (n,)
            and bool(torch.isfinite(weights).all())
            and bool((weights >= 0).all()),
            "invalid cohort weights",
        )
        total_weight += float(weights.sum())
        count += n
        for r, entries in sorted(grouped.items()):
            sources = sorted({s for _, s, _ in entries})
            a = native_forward(model, batch, capture_sites=sources + [r])
            base = a["incoming"][r].detach().cpu()
            sender = {s: a["additive"][s].detach().cpu() for s in sources}
            del a
            b = native_forward(model, neutral, capture_sites=sources + [r])
            start = base.clone()
            selected = torch.zeros(batch["input_ids"].shape, dtype=torch.bool)
            delta = {s: torch.zeros_like(sender[s]) for s in sources}
            for row, m in enumerate(mapping):
                for p, q in m.items():
                    start[row, p] = b["incoming"][r][row, q].detach().cpu()
                    selected[row, p] = True
                    for s in sources:
                        delta[s][row, p] = (
                            sender[s][row, p] - b["additive"][s][row, q].detach().cpu()
                        )
            del b, sender
            path = base - start
            device = batch["input_ids"].device
            for step in range(steps):
                point = (start + ((step + 0.5) / steps) * path).to(device)
                out = native_forward(
                    model,
                    batch,
                    capture_sites=[r],
                    patches={r: ResidualPatch(point, selected.to(device))},
                    grad=True,
                )
                margin = _margin(out, batch)
                (gradient,) = torch.autograd.grad(margin.sum(), out["leaves"][r])
                gradient = gradient.detach().cpu().float()
                del out, margin
                for index, s, cell in entries:
                    score = torch.tensor(
                        [
                            sum(
                                float(
                                    torch.dot(
                                        gradient[row, p], delta[s][row, p].float()
                                    )
                                )
                                for p in positions
                            )
                            for row, positions in enumerate(cells[cell])
                        ],
                        dtype=torch.float64,
                    )
                    totals[index] += (score * weights).sum() / steps
                del gradient
    _require(count > 0 and total_weight > 0, "empty attribution cohort/zero weights")
    _require(
        not explicit or math.isclose(total_weight, 1.0, rel_tol=1e-6, abs_tol=1e-8),
        "explicit weights must sum to one over cohort",
    )
    return [
        dict(
            edge=copy.deepcopy(e),
            score=float(totals[i] / total_weight),
            row_count=count,
            token_count=tokens[i],
            mean_tokens_per_row=tokens[i] / count,
            token_aggregation="sum within cell; cohort-weighted across rows",
            steps=steps,
            estimand="local incoming-residual IG ranking",
        )
        for i, e in enumerate(edges)
    ]


def integration_stability(eight, sixteen):
    """Frozen diagnostic: top-16 absolute-score overlap and relative score L1.

    L1 denominator is sum(abs(16-node scores)); zero reference/empty cohorts are
    explicitly unreliable. With <16 candidates, overlap uses every candidate.
    Nonfinite aggregate arithmetic raises even when every input score is finite.
    """

    def table(records):
        result = {}
        for r in records:
            k = _key(r["edge"])
            _require(
                k not in result and math.isfinite(r["score"]),
                "duplicate/nonfinite stability scores",
            )
            result[k] = float(r["score"])
        return result

    a, b = table(eight), table(sixteen)
    _require(set(a) == set(b), "stability candidate geometry changed")
    specs = {_key(x["edge"]): x["edge"]["position_spec"] for x in eight}
    _require(
        all(specs[_key(y["edge"])] == y["edge"]["position_spec"] for y in sixteen),
        "stability position geometry changed",
    )
    if not a:
        return dict(
            status="undefined", stable=False, top16_overlap=None, normalized_l1=None
        )
    norm = sum(abs(v) for v in b.values())
    _require(math.isfinite(norm), "nonfinite stability aggregate denominator")
    if norm == 0:
        return dict(
            status="zero_scores", stable=False, top16_overlap=None, normalized_l1=None
        )
    k = min(16, len(a))

    def top(t):
        return set(sorted(t, key=lambda key: (-abs(t[key]), key))[:k])

    overlap = len(top(a) & top(b)) / k
    difference = sum(abs(a[key] - b[key]) for key in a)
    _require(math.isfinite(difference), "nonfinite stability aggregate difference")
    l1 = difference / norm
    _require(math.isfinite(l1), "nonfinite stability aggregate ratio")
    return dict(
        status="defined",
        stable=overlap >= 0.8 and l1 <= 0.10,
        top16_overlap=overlap,
        normalized_l1=l1,
        top_count=k,
    )
