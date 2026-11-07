"""CPU-only edge estimand tests; no pretrained weights or scientific rows."""

import copy

import pytest
import torch
from transformers import LlamaConfig, LlamaForCausalLM

from component_analysis import a3_edges as edges
from component_analysis.a3_native import native_forward, ResidualPatch, _native_norm


@pytest.fixture
def case():
    torch.manual_seed(91)
    model = (
        LlamaForCausalLM(
            LlamaConfig(
                hidden_size=16,
                intermediate_size=24,
                num_hidden_layers=2,
                num_attention_heads=4,
                num_key_value_heads=2,
                vocab_size=29,
                attn_implementation="eager",
            )
        )
        .eval()
        .requires_grad_(False)
    )

    def batch(ids, condition):
        return dict(
            input_ids=torch.tensor(ids),
            attention_mask=torch.tensor([[1, 1, 1, 1], [1, 1, 1, 0]]),
            readout=torch.tensor([3, 2]),
            positions={"last": torch.tensor([3, 2]), "key": torch.tensor([1, 1])},
            position_cells={x["key"]: x for x in geometry()["position_cells"]},
            condition=condition,
            stream="clean",
            instance_ids=["a", "b"],
            opposite_token=torch.tensor([7, 8]),
            honest_token=torch.tensor([3, 4]),
        )

    recipient = batch([[1, 5, 6, 7], [2, 8, 9, 0]], "D")
    donor = batch([[1, 6, 6, 7], [2, 9, 9, 0]], "H")
    maps = {
        "rows": [
            dict(
                supported=True,
                instance_id=i,
                stream="clean",
                recipient_condition="D",
                donor_condition="H",
                recipient_positions=list(range(n)),
                donor_positions=list(range(n)),
            )
            for i, n in [("a", 4), ("b", 3)]
        ]
    }
    return model, recipient, donor, maps


def edge(sender=("head", 0, 0), receiver=("mlp_in", 0, 0), position="last"):
    return dict(
        sender=sender,
        receiver=receiver,
        position=position,
        position_spec=next(
            x for x in geometry()["position_cells"] if x["key"] == position
        ),
    )


def geometry():
    return dict(
        num_hidden_layers=2,
        num_attention_heads=4,
        num_key_value_heads=2,
        position_cells=[
            dict(
                key="last",
                semantic_bin="assistant_readout",
                receiver_kinds=["q", "mlp_in", "readout"],
            ),
            dict(key="key", semantic_bin="question", receiver_kinds=["k", "v"]),
        ],
    )


def test_grid_is_frozen_causal_and_gqa_deduplicated():
    grid = edges.edge_grid(
        {"edge_nodes": [("head", 0, 0), ("head", 0, 1), ("head", 1, 0), ("mlp", 0, 0)]},
        geometry(),
    )
    keys = [(tuple(e["sender"]), tuple(e["receiver"]), e["position"]) for e in grid]
    assert len(keys) == len(set(keys))
    assert (("head", 0, 0), ("mlp_in", 0, 0), "last") in keys
    assert (("mlp", 0, 0), ("q", 0, 0), "last") not in keys
    assert (("head", 0, 0), ("k", 1, 0), "key") in keys
    assert not any(r == ("k", 0, 1) for s, r, p in keys)
    assert all("semantic_bin" not in e for e in grid)
    assert grid == edges.edge_grid(
        {
            "edge_nodes": list(
                reversed(
                    [("head", 0, 0), ("head", 0, 1), ("head", 1, 0), ("mlp", 0, 0)]
                )
            )
        },
        geometry(),
    )


def test_exact_replay_two_incoming_edges_permutation_and_actual_tensors(case):
    model, batch, donor, maps = case
    selected = [
        edge(),
        edge(("head", 0, 1)),
        edge(receiver=("q", 1, 0)),
        edge(receiver=("k", 1, 0), position="key"),
        edge(receiver=("v", 1, 0), position="key"),
    ]
    out = edges.exact_edge_patch(model, batch, donor, edges=selected, maps=maps)
    permuted = edges.exact_edge_patch(
        model, batch, donor, edges=list(reversed(selected)), maps=maps
    )
    torch.testing.assert_close(
        out["fp32_logits"], permuted["fp32_logits"], atol=0, rtol=0
    )
    sources = sorted({tuple(e["sender"]) for e in selected})
    receivers = sorted({tuple(e["receiver"]) for e in selected})
    intact = native_forward(model, batch, capture_sites=sources + receivers)
    other = native_forward(model, donor, capture_sites=sources)
    for receiver in receivers:
        expected = intact["incoming"][receiver].clone()
        for e in sorted(
            [x for x in selected if x["receiver"] == receiver],
            key=lambda x: tuple(x["sender"]),
        ):
            pos = batch["positions"][e["position"]]
            rows = torch.arange(2)
            sender = e["sender"]
            expected[rows, pos] += (
                other["additive"][sender][rows, pos]
                - intact["additive"][sender][rows, pos]
            )
        torch.testing.assert_close(out["clamps"][receiver], expected)
        layer = model.model.layers[receiver[1]]
        if receiver[0] == "mlp_in":
            effective = _native_norm(layer.post_attention_layernorm, expected)
        else:
            proj = getattr(layer.self_attn, receiver[0] + "_proj")
            start = receiver[2] * 4
            effective = proj(_native_norm(layer.input_layernorm, expected))[
                ..., start : start + 4
            ]
        mask = out["patch_positions"][receiver]
        torch.testing.assert_close(
            out["receiver_outputs"][receiver][mask], effective[mask]
        )
    empty = edges.exact_edge_patch(model, batch, donor, edges=[], maps=maps)
    torch.testing.assert_close(empty["fp32_logits"], intact["fp32_logits"])
    same = edges.exact_edge_patch(
        model,
        batch,
        batch,
        edges=selected,
        maps={"rows": [dict(r, donor_condition="D") for r in maps["rows"]]},
    )
    torch.testing.assert_close(same["fp32_logits"], intact["fp32_logits"])


def test_chain_and_readout_clamp_use_fixed_sources(case):
    model, batch, donor, maps = case
    chain = [edge(), edge(("mlp", 0, 0), ("mlp_in", 1, 0))]
    joint = edges.exact_edge_patch(model, batch, donor, edges=chain, maps=maps)
    downstream = edges.exact_edge_patch(model, batch, donor, edges=chain[1:], maps=maps)
    torch.testing.assert_close(
        joint["clamps"][("mlp_in", 1, 0)],
        downstream["clamps"][("mlp_in", 1, 0)],
        atol=0,
        rtol=0,
    )
    r = edge(("mlp", 0, 0), ("readout", 0, 0))
    both = edges.exact_edge_patch(model, batch, donor, edges=chain + [r], maps=maps)
    only = edges.exact_edge_patch(model, batch, donor, edges=[r], maps=maps)
    torch.testing.assert_close(both["fp32_logits"], only["fp32_logits"], atol=0, rtol=0)


@pytest.mark.parametrize(
    "change",
    [
        "duplicate",
        "future",
        "padding",
        "unsupported",
        "DI",
        "missing",
        "map_duplicate",
        "map_oob",
    ],
)
def test_reject_invalid_edges_and_maps(case, change):
    model, batch, donor, maps = case
    selected = [edge()]
    if change == "duplicate":
        selected *= 2
    if change == "future":
        selected = [edge(("mlp", 1, 0), ("q", 0, 0))]
    if change == "padding":
        batch["positions"]["last"] = torch.tensor([3, 3])
    if change == "unsupported":
        maps["rows"][0]["supported"] = False
    if change == "DI":
        donor["condition"] = "I"
        maps["rows"] = [dict(r, donor_condition="I") for r in maps["rows"]]
    if change == "missing":
        maps["rows"][0]["recipient_positions"] = []
        maps["rows"][0]["donor_positions"] = []
    if change == "map_duplicate":
        maps["rows"][0]["recipient_positions"] = [0, 0, 2, 3]
    if change == "map_oob":
        maps["rows"][0]["donor_positions"] = [0, 1, 2, 4]
    with pytest.raises((ValueError, TypeError)):
        edges.exact_edge_patch(model, batch, donor, edges=selected, maps=maps)


def test_local_ig_matches_manual_one_branch_and_readout_live(case):
    model, batch, donor, maps = case
    selected = [
        edge(receiver=("v", 1, 0), position="key"),
        edge(receiver=("mlp_in", 1, 0)),
    ]
    results = edges.attribute_edges(
        model, [dict(batch=batch, neutral=donor, maps=maps)], edges=selected, steps=8
    )
    assert len(results) == 2
    for e, result in zip(selected, results):
        receiver = e["receiver"]
        sender = e["sender"]
        intact = native_forward(model, batch, capture_sites=[receiver, sender])
        neutral = native_forward(model, donor, capture_sites=[receiver, sender])
        baseline = neutral["incoming"][receiver]
        delta = intact["incoming"][receiver] - baseline
        expected = torch.zeros(2)
        for step in range(8):
            point = baseline + (step + 0.5) / 8 * delta
            out = native_forward(
                model,
                batch,
                capture_sites=[receiver],
                patches={receiver: ResidualPatch(point)},
                grad=True,
            )
            rows = torch.arange(2)
            margin = (
                out["fp32_logits"][rows, batch["opposite_token"]]
                - out["fp32_logits"][rows, batch["honest_token"]]
            )
            (grad,) = torch.autograd.grad(margin.sum(), out["leaves"][receiver])
            p = batch["positions"][e["position"]]
            source_delta = intact["additive"][sender] - neutral["additive"][sender]
            expected += (grad[rows, p] * source_delta[rows, p]).sum(-1) / 8
        assert result["score"] == pytest.approx(expected.mean().item(), abs=2e-8)
        assert abs(result["score"]) > 1e-10
    assert all(p.grad is None for p in model.parameters())


def test_ig_weights_and_zero_delta(case):
    model, batch, donor, maps = case
    selected = [edge(receiver=("readout", 0, 0))]
    records = edges.attribute_edges(
        model,
        [
            dict(
                batch=batch,
                neutral=batch,
                maps={"rows": [dict(r, donor_condition="D") for r in maps["rows"]]},
                weights=[0.3, 0.7],
            )
        ],
        edges=selected,
    )
    assert records[0]["score"] == 0
    with pytest.raises(ValueError):
        edges.attribute_edges(
            model,
            [dict(batch=batch, neutral=donor, maps=maps, weights=[1.0, 1.0])],
            edges=selected,
        )


def test_stability_explicit_zero_undefined_and_thresholds():
    a = [dict(edge=edge(("head", 0, h)), score=float(h + 1)) for h in range(20)]
    result = edges.integration_stability(a, a)
    assert (
        result["stable"]
        and result["top16_overlap"] == 1
        and result["normalized_l1"] == 0
    )
    zero = [dict(x, score=0.0) for x in a]
    assert edges.integration_stability(zero, zero)["status"] == "zero_scores"
    assert edges.integration_stability([], [])["status"] == "undefined"
    changed = [dict(x, score=-x["score"]) for x in a]
    assert not edges.integration_stability(a, changed)["stable"]


def test_ragged_bin_sums_mapped_positions_and_rejects_unsupported_alias(case):
    model, batch, donor, maps = case
    selected = [edge(receiver=("v", 1, 0), position="key")]
    batch["positions"]["key"] = [[0, 1], [0, 1, 2]]
    # Each physical token retains its OWN supported donor position.
    maps["rows"][0]["donor_positions"] = [1, 0, 2, 3]
    out = edges.exact_edge_patch(model, batch, donor, edges=selected, maps=maps)
    s, r = selected[0]["sender"], selected[0]["receiver"]
    a = native_forward(model, batch, capture_sites=[s, r])
    b = native_forward(model, donor, capture_sites=[s])
    for row, positions in enumerate(batch["positions"]["key"]):
        m = dict(
            zip(
                maps["rows"][row]["recipient_positions"],
                maps["rows"][row]["donor_positions"],
            )
        )
        for p in positions:
            torch.testing.assert_close(
                out["clamps"][r][row, p],
                a["incoming"][r][row, p]
                + b["additive"][s][row, m[p]]
                - a["additive"][s][row, p],
            )
    record = edges.attribute_edges(
        model, [dict(batch=batch, neutral=donor, maps=maps)], edges=selected
    )[0]
    assert record["token_count"] == 5
    assert record["mean_tokens_per_row"] == 2.5
    batch["positions"]["key"] = [[], [1]]
    with pytest.raises(ValueError, match="unsupported"):
        edges.exact_edge_patch(model, batch, donor, edges=selected, maps=maps)


def test_changed_position_geometry_rejected(case):
    model, batch, donor, maps = case
    batch["position_cells"]["last"] = dict(
        batch["position_cells"]["last"], semantic_bin="question"
    )
    with pytest.raises(ValueError, match="geometry"):
        edges.exact_edge_patch(model, batch, donor, edges=[edge()], maps=maps)
    g = geometry()
    g["position_cells"] *= 2
    with pytest.raises(ValueError, match="duplicate"):
        edges.edge_grid({"edge_nodes": [("head", 0, 0)]}, g)


class LinearCircuit:
    """Complete residual source partition: causal coordinate and dead coordinate.

    This analytic adapter seam tests IG/exact orchestration independently of
    nonlinear Llama. All HF norm/projection Jacobians are tested above on HF.
    """

    def __init__(self):
        from types import SimpleNamespace

        self.config = SimpleNamespace(
            num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=1
        )

    def forward(self, batch, *, capture_sites, patches=None, grad=False):
        inputs = batch["input_ids"].float()
        a = torch.stack([inputs, torch.zeros_like(inputs)], -1)
        dead = torch.stack([torch.zeros_like(inputs), inputs * 3], -1)
        incoming = a + dead
        patch = (patches or {}).get(("readout", 0, 0))
        leaf = (
            (incoming if patch is None else patch.value)
            .detach()
            .clone()
            .requires_grad_(grad)
        )
        value = (
            leaf
            if patch is None or patch.positions is None
            else torch.where(patch.positions[..., None], leaf, incoming)
        )
        score = value[..., 0].sum(-1) * 2
        logits = torch.stack([torch.zeros_like(score), score], -1)
        return dict(
            logits=logits.detach(),
            fp32_logits=logits,
            additive={
                s: v.detach()
                for s, v in [(("head", 0, 0), a), (("head", 0, 1), dead)]
                if s in capture_sites
            },
            incoming={("readout", 0, 0): incoming.detach()},
            outputs={("readout", 0, 0): value.detach()},
            leaves={("readout", 0, 0): leaf},
        )


def test_complete_linear_toy_causal_dead_ig_ranking_and_full_endpoint(monkeypatch):
    model = LinearCircuit()
    monkeypatch.setattr(
        edges, "native_forward", lambda m, b, **kwargs: m.forward(b, **kwargs)
    )
    spec = dict(key="all", semantic_bin="question", receiver_kinds=["readout"])

    def batch(tokens, condition):
        return dict(
            input_ids=torch.tensor([tokens]),
            attention_mask=torch.ones(1, 2, dtype=torch.long),
            condition=condition,
            stream="clean",
            instance_ids=["toy"],
            positions={"all": [[0, 1]]},
            position_cells={"all": spec},
            opposite_token=torch.tensor([1]),
            honest_token=torch.tensor([0]),
        )

    a, b = batch([3, 4], "D"), batch([1, 1], "H")
    maps = {
        "rows": [
            dict(
                supported=True,
                instance_id="toy",
                stream="clean",
                recipient_condition="D",
                donor_condition="H",
                recipient_positions=[0, 1],
                donor_positions=[0, 1],
            )
        ]
    }
    selected = [
        dict(
            sender=("head", 0, h),
            receiver=("readout", 0, 0),
            position="all",
            position_spec=spec,
        )
        for h in range(2)
    ]
    scores = edges.attribute_edges(
        model, [dict(batch=a, neutral=b, maps=maps)], edges=selected
    )
    assert [s["score"] for s in scores] == pytest.approx([10.0, 0.0])
    assert scores[0]["score"] > scores[1]["score"]
    complete = edges.exact_edge_patch(model, a, b, edges=selected, maps=maps)
    torch.testing.assert_close(
        complete["fp32_logits"], model.forward(b, capture_sites=[])["fp32_logits"]
    )
    intact = model.forward(a, capture_sites=[])["fp32_logits"]
    assert (intact - complete["fp32_logits"])[0, 1].item() == sum(
        s["score"] for s in scores
    )


def test_single_receiver_matches_existing_two_pass_path_patching(case):
    from nnsight import NNsight
    from component_analysis import hooks, path_patching as path

    model, batch, donor, maps = case
    # Readout is the most direct legacy receiver and uses the same fp32 metric.
    sender = ("head", 0, 0)
    receiver = ("readout", 0, 0)
    selected = [edge(sender, receiver)]
    actual = edges.exact_edge_patch(model, batch, donor, edges=selected, maps=maps)
    wrapped = NNsight(copy.deepcopy(model))
    all_sources = [("embed", 0, 0)] + [
        (k, layer, h)
        for layer in range(2)
        for k, heads in [("head", 4), ("mlp", 1)]
        for h in range(heads)
    ]
    intact = hooks.capture_forward(
        wrapped,
        batch["input_ids"],
        batch["attention_mask"],
        components=all_sources + [receiver],
        positions=batch["readout"],
    )
    other = hooks.capture_forward(
        wrapped,
        donor["input_ids"],
        donor["attention_mask"],
        components=[sender],
        positions=donor["readout"],
    )
    from types import SimpleNamespace

    streams = SimpleNamespace(
        input_ids=batch["input_ids"],
        attention_mask=batch["attention_mask"],
        positions=batch["readout"],
        clean_outputs={s: intact.outputs[s] for s in all_sources},
        corrupt_outputs={sender: other.outputs[sender]},
    )
    captured = path.receiver_inputs(
        wrapped, streams, senders=[sender], receivers=[receiver]
    )
    mask = actual["patch_positions"][receiver]
    torch.testing.assert_close(
        captured.outputs[receiver][mask],
        actual["clamps"][receiver][mask],
        atol=1e-7,
        rtol=1e-5,
    )
    legacy = path.readout_from_receivers(
        wrapped,
        streams,
        {receiver: hooks.Replacement(captured.outputs[receiver], positions=mask)},
    )
    torch.testing.assert_close(actual["fp32_logits"], legacy, atol=1e-6, rtol=1e-5)


def test_position_effects_and_weighted_streaming_are_distinct(case):
    model, batch, donor, maps = case
    spec = dict(key="last", semantic_bin="assistant_readout", receiver_kinds=["v"])
    batch["position_cells"]["last"] = spec
    first = edge(receiver=("v", 1, 0), position="key")
    last = dict(
        sender=first["sender"],
        receiver=first["receiver"],
        position="last",
        position_spec=spec,
    )
    records = edges.attribute_edges(
        model, [dict(batch=batch, neutral=donor, maps=maps)], edges=[first, last]
    )
    assert abs(records[0]["score"] - records[1]["score"]) > 1e-8
    weighted = edges.attribute_edges(
        model,
        [dict(batch=batch, neutral=donor, maps=maps, weights=[0.2, 0.8])],
        edges=[first],
    )
    chunks = []
    for row, weight in enumerate([0.2, 0.8]):

        def one(source):
            out = {
                k: v[row : row + 1] if isinstance(v, torch.Tensor) else v
                for k, v in source.items()
            }
            out["instance_ids"] = [source["instance_ids"][row]]
            out["positions"] = {
                k: v[row : row + 1] for k, v in source["positions"].items()
            }
            return out

        chunks.append(
            dict(
                batch=one(batch),
                neutral=one(donor),
                maps={"rows": [maps["rows"][row]]},
                weights=[weight],
            )
        )
    streamed = edges.attribute_edges(model, iter(chunks), edges=[first])
    assert streamed[0]["score"] == pytest.approx(weighted[0]["score"], abs=1e-7)
    sixteen = edges.attribute_edges(
        model,
        [dict(batch=batch, neutral=donor, maps=maps)],
        edges=[first, last],
        steps=16,
    )
    assert edges.integration_stability(records, sixteen)["stable"]


def test_grid_group_dedup_and_metadata_alias_rejection(case):
    grid = edges.edge_grid(
        {"edge_nodes": [("head", 0, 0), ("head", 1, 0), ("head", 1, 1)]}, geometry()
    )
    incoming = [
        e
        for e in grid
        if e["sender"] == ("head", 0, 0) and e["receiver"] == ("k", 1, 0)
    ]
    assert len(incoming) == 1
    model, batch, donor, maps = case
    alias = dict(key="key_alias", semantic_bin="question", receiver_kinds=["k", "v"])
    batch["position_cells"]["key_alias"] = alias
    batch["positions"]["key_alias"] = batch["positions"]["key"].clone()
    first = edge(receiver=("v", 1, 0), position="key")
    second = dict(first, position="key_alias", position_spec=alias)
    with pytest.raises(ValueError, match="alias"):
        edges.exact_edge_patch(model, batch, donor, edges=[first, second], maps=maps)


def test_geometry_duplicate_semantic_alias_rejected_before_execution():
    g = geometry()
    g["position_cells"].append(dict(g["position_cells"][0], key="last_alias"))
    with pytest.raises(ValueError, match="alias"):
        edges.edge_grid({"edge_nodes": [("head", 0, 0)]}, g)


def test_stability_exact_thresholds_and_nonfinite_rejected():
    a = [dict(edge=edge(("head", 0, h)), score=9.0) for h in range(20)]
    b = [dict(x, score=10.0) for x in a]
    assert edges.integration_stability(a, b)["normalized_l1"] == 0.10
    assert edges.integration_stability(a, b)["stable"]
    a[0]["score"] = 8.99
    assert not edges.integration_stability(a, b)["stable"]
    a[0]["score"] = float("nan")
    with pytest.raises(ValueError, match="nonfinite"):
        edges.integration_stability(a, b)


def test_cross_bin_physical_alias_is_rejected(case):
    model, batch, donor, maps = case
    spec = dict(key="readout_alias", semantic_bin="question", receiver_kinds=["mlp_in"])
    batch["position_cells"]["readout_alias"] = spec
    batch["positions"]["readout_alias"] = batch["positions"]["last"].clone()
    selected = [
        edge(),
        dict(
            sender=("head", 0, 0),
            receiver=("mlp_in", 0, 0),
            position="readout_alias",
            position_spec=spec,
        ),
    ]
    with pytest.raises(ValueError, match="alias"):
        edges.exact_edge_patch(model, batch, donor, edges=selected, maps=maps)


def test_explicit_corrupt_utility_donor_stream_and_identity(case):
    model, batch, donor, maps = case
    batch["condition"] = "IOI"
    donor["condition"] = "IOI"
    donor["stream"] = "corrupt"
    donor["instance_ids"] = ["donor-a", "donor-b"]
    records = []
    for i, r in enumerate(maps["rows"]):
        records.append(
            dict(
                supported=True,
                recipient_id=batch["instance_ids"][i],
                donor_id=donor["instance_ids"][i],
                recipient_condition="IOI",
                donor_condition="IOI",
                recipient_stream="clean",
                donor_stream="corrupt",
                recipient_positions=r["recipient_positions"],
                donor_positions=r["donor_positions"],
            )
        )
    actual = edges.exact_edge_patch(
        model,
        batch,
        donor,
        edges=[edge(receiver=("readout", 0, 0))],
        maps={"rows": records},
    )
    assert torch.isfinite(actual["fp32_logits"]).all()
    records[0]["donor_id"] = "wrong"
    with pytest.raises(ValueError, match="mismatch"):
        edges.exact_edge_patch(
            model, batch, donor, edges=[edge()], maps={"rows": records}
        )


@pytest.mark.parametrize(
    "eight,sixteen,count",
    [(8e306, 1e307, 20), (1e308, -1e308, 1), (1e308, 1e-308, 1)],
)
def test_stability_rejects_nonfinite_aggregate_arithmetic(eight, sixteen, count):
    a = [dict(edge=edge(("head", 0, h)), score=eight) for h in range(count)]
    b = [dict(record, score=sixteen) for record in a]
    with pytest.raises(ValueError, match="nonfinite stability aggregate"):
        edges.integration_stability(a, b)
