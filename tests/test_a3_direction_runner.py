"""Bounded A3 direction execution on CPU; no weights or downloads."""

from dataclasses import replace
import numpy as np
import pytest
import torch
from component_analysis import hooks
from component_analysis.specificity_ladder import LadderBatch
from component_analysis.a3_directions import prepare_image_direction
from component_analysis import a3_direction_runner as runner

SITE = ("head", 0, 0)


def batch(stream="clean", width=5):
    tokens = torch.tensor([[1, 2, 3, 0, 0], [3, 4, 5, 6, 7]])[:, :width]
    if stream == "corrupt":
        tokens = tokens + 2
    mask = torch.tensor([[1, 1, 1, 0, 0], [1, 1, 1, 1, 1]])[:, :width]
    return LadderBatch(
        ["a", "b"],
        "D",
        stream,
        tokens,
        mask,
        torch.tensor([2, width - 1]),
        torch.tensor([1, 1]),
        torch.tensor([2, 2]),
        torch.tensor([1, 1]),
        [
            dict(split="validation", source_hash="source", source_id=i)
            for i in ["a", "b"]
        ],
        "far_v2",
    )


def identity(tile=1, width=5):
    ident = dict(
        injected=True,
        diagnostic_only=True,
        panel="validation",
        analysis_task="far_v2",
        split="validation",
        numeric_profile=dict(
            padded_width=width,
            physical_batch_size=2 * tile,
            axis_tile_size=tile,
            dtype="torch.float32",
            backend="fake",
            model="tiny",
            model_revision="random",
            source_sha256="a" * 64,
        ),
    )
    return ident


@pytest.fixture
def fake(monkeypatch):
    calls = []
    monkeypatch.setattr(hooks, "all_component_keys", lambda m: [SITE])
    monkeypatch.setattr(hooks, "attention_implementation", lambda m: "fake")
    monkeypatch.setattr(
        hooks, "device_and_dtype", lambda m: (torch.device("cpu"), torch.float32)
    )
    monkeypatch.setattr(
        hooks,
        "o_proj_weight",
        lambda m, layer: torch.cat((torch.eye(2), torch.eye(2)), dim=1),
    )
    monkeypatch.setattr(hooks, "geometry", lambda m: dict(n_heads=2, head_dim=2))

    def capture(model, ids, mask, *, components, positions, replacements=None):
        assert not torch.is_grad_enabled()
        z = torch.stack((ids.float(), ids.float() * 2), -1)
        outputs = {k: z.clone() for k in components}
        for k, r in (replacements or {}).items():
            outputs[k] = torch.where(r.positions[:, :, None], r.value, outputs[k])
        idx = torch.arange(len(ids))
        out = outputs[SITE][idx, positions]
        logits = torch.stack((out[:, 0] * 0, out[:, 0], out[:, 1], out[:, 0] * 0.1), -1)
        calls.append((ids.clone(), replacements))
        return hooks.Capture(logits, outputs, logits[:, None, :], positions)

    monkeypatch.setattr(hooks, "capture_forward", capture)
    monkeypatch.setattr(hooks, "readout_logits", lambda m, r: r.float())
    return calls


def axis():
    return prepare_image_direction(
        torch.eye(2),
        torch.tensor([1.0, 0.0]),
        torch.tensor([[1.0, 2.0], [2.0, 4.0]]),
        id_weights=torch.tensor([0.5, 0.5]),
    )


def cache(fake, ident=None):
    ident = ident or identity()
    chunks = []
    runner.capture_readouts(
        object(),
        [batch(), batch("corrupt")],
        sites=[SITE],
        sink=chunks.append,
        identity=ident,
    )
    index = {}
    for c in chunks:
        for row in c["rows"]:
            index[
                (
                    c["profile_id"],
                    row["task"],
                    row["condition"],
                    row["stream"],
                    row["instance_id"],
                )
            ] = row
    return index, chunks


def cell(op="interchange", ax="x"):
    return dict(
        site=SITE, axis=ax, operation=op, seed=42, family="learned", axis_index=0
    )


def test_cache_readouts_equal_existing_hooks(fake):
    index, chunks = cache(fake)
    assert len(index) == 4 and len(chunks) == 2
    assert chunks[0]["rows"][0]["heads"][0]["value"].tolist() == [3.0, 6.0]
    assert all(v["heads"][0]["value"].device.type == "cpu" for v in index.values())
    assert chunks[0]["projections"][0]["value"].shape == (2, 2)


def test_unequal_padding_maps_actual_readouts(fake):
    index, chunks = cache(fake)
    rows = []
    c = cell()
    c["donor_maps"] = [
        dict(
            recipient_id=i,
            recipient_condition="D",
            recipient_stream="clean",
            donor_id=i,
            donor_condition="D",
            donor_stream="corrupt",
            recipient_positions=[p],
            donor_positions=[p],
            donor_profile_id=chunks[0]["profile_id"],
            supported=True,
            donor_source_hash="source",
        )
        for i, p in [("a", 2), ("b", 4)]
    ]
    runner.score_direction_cells(
        object(),
        [batch()],
        cells=[c],
        capture_index=index,
        axes={"x": axis()},
        sink=rows.append,
        identity=identity(),
    )
    assert [r["head_norm"] for r in rows[0]["rows"]] == pytest.approx([2.0, 2.0])
    assert rows[0]["rows"][0]["donor_mapping"]["donor_positions"] == [2]


def test_direction_only_changes_named_head_readout(fake):
    index, _ = cache(fake)
    out = []
    runner.score_direction_cells(
        object(),
        [batch()],
        cells=[cell("zero")],
        capture_index=index,
        axes={"x": axis()},
        sink=out.append,
        identity=identity(),
    )
    patched = [r for _, r in fake if r and SITE in r][-1][SITE]
    assert patched.positions.tolist() == [
        [False, False, True, False, False],
        [False, False, False, False, True],
    ]
    assert patched.value[0, 2].tolist() == [0.0, 6.0]
    assert all(r["epsilon"] == 1e-6 for r in out[0]["rows"])


@pytest.mark.parametrize("operation,expected", [("zero", 0.0), ("h_mean", 1.5)])
def test_secondary_zero_and_centered_h_are_subspace_patches(fake, operation, expected):
    index, _ = cache(fake)
    out = []
    runner.score_direction_cells(
        object(),
        [batch()],
        cells=[cell(operation)],
        capture_index=index,
        axes={"x": axis()},
        sink=out.append,
        identity=identity(),
    )
    assert out[0]["rows"][0]["patched_margin"] == pytest.approx(expected - 6)


def test_mmlu_has_no_item_swap(fake):
    with pytest.raises(ValueError, match="MMLU"):
        runner.score_direction_cells(
            object(),
            [replace(batch(), task="mmlu")],
            cells=[cell()],
            capture_index={},
            axes={"x": axis()},
            sink=lambda x: None,
            identity=identity(),
        )


def test_same_shape_controls_compare_same_kernel_path(fake):
    index, _ = cache(fake)
    out = []
    runner.score_direction_cells(
        object(),
        [batch()],
        cells=[cell("zero")],
        capture_index=index,
        axes={"x": axis()},
        sink=out.append,
        identity=identity(),
    )
    assert all(ids.shape == (2, 5) for ids, _ in fake)
    assert set(out[0]["rows"][0]["replay_errors"]) == {
        "empty",
        "head_self",
        "zero_coefficient",
    }


def donor_maps(recipient, donor, donor_profile_id=None):
    return [
        dict(
            recipient_id=rid,
            recipient_condition=recipient.condition,
            recipient_stream=recipient.stream,
            donor_id=donor.ids[i],
            donor_condition=donor.condition,
            donor_stream=donor.stream,
            recipient_positions=[int(recipient.readout[i])],
            donor_positions=[int(donor.readout[i])],
            donor_source_hash=donor.records[i]["source_hash"],
            donor_source_id=donor.records[i]["source_id"],
            donor_split=donor.records[i]["split"],
            donor_profile_id=donor_profile_id,
            supported=True,
        )
        for i, rid in enumerate(recipient.ids)
    ]


def measured_setup(fake, tile=2):
    index, chunks = cache(fake)
    axes = {
        "x": axis(),
        "y": prepare_image_direction(
            torch.eye(2),
            torch.tensor([0.0, 1.0]),
            torch.tensor([[1.0, 2.0], [2.0, 4.0]]),
            id_weights=torch.tensor([0.5, 0.5]),
        ),
    }
    maps = donor_maps(batch(), batch("corrupt"), chunks[0]["profile_id"])
    cells = [
        dict(cell("interchange", "x"), axis_index=0, donor_maps=maps),
        dict(cell("zero", "y"), axis_index=1),
        dict(cell("steer_positive", "x"), axis_index=2),
    ]
    ident = identity(tile)
    ident["packed_equivalence"] = runner.measure_packing_equivalence(
        object(), [batch()], cells=cells, capture_index=index, axes=axes, identity=ident
    )
    packed = []
    runner.capture_readouts(
        object(), [batch()], sites=[SITE], sink=packed.append, identity=ident
    )
    for chunk in packed:
        for row in chunk["rows"]:
            index[
                (
                    chunk["profile_id"],
                    row["task"],
                    row["condition"],
                    row["stream"],
                    row["instance_id"],
                )
            ] = row
    return ident, index, axes, cells


def test_positive_control_keeps_parent_padding(fake):
    b = batch()
    donor = batch("corrupt")
    result = runner.run_positive_controls(
        object(),
        [b],
        donor_batches=[donor],
        donor_maps=donor_maps(b, donor),
        identity=identity(),
    )
    assert all(
        r["measurement"]["padded_width"] == 5
        and r["measurement"]["physical_batch_size"] == 1
        for r in result["rows"]
    )
    assert all(r["measurement"]["max_abs_logit_error"] == 0 for r in result["rows"])
    assert b.input_ids.shape == (2, 5)


def test_axis_packing_equals_serial(fake):
    ident, index, axes, cells = measured_setup(fake, 3)
    results = []
    for current in (identity(), ident):
        out = []
        runner.score_direction_cells(
            object(),
            [batch()],
            cells=cells,
            capture_index=index,
            axes=axes,
            sink=out.append,
            identity=current,
        )
        results.append(
            [
                (r["axis_index"], r["instance_id"], r["patched_margin"])
                for chunk in out
                for r in chunk["rows"]
            ]
        )
    assert results[0] == results[1]
    assert len(ident["packed_equivalence"]["comparisons"]) == 8


def test_capture_failure_leaves_no_complete_shard(fake):
    out = []
    with pytest.raises(ValueError):
        runner.capture_readouts(
            object(),
            [replace(batch(), readout=torch.tensor([3, 4]))],
            sites=[SITE],
            sink=out.append,
            identity=identity(),
        )
    assert out == []


def test_profile_mismatch_rejected(fake):
    ident = identity()
    ident["numeric_profile"]["physical_batch_size"] = 3
    with pytest.raises(ValueError, match="geometry"):
        runner.capture_readouts(
            object(), [batch()], sites=[SITE], sink=lambda x: None, identity=ident
        )


def metric_rows(source, seed=42):
    """Extract an existing genuine three-seed synthetic panel's one seed/axis."""
    j = [42, 1, 123].index(seed)
    rows = []
    base = dict(
        seed=seed,
        site=list(SITE),
        family="learned",
        axis_index=0,
        analysis_task="far_v2",
        split="validation",
        panel="calibration",
        gate_valid=True,
        epsilon=1e-6,
    )
    for c, data in source["conditions"].items():
        for i, rid in enumerate(source["instance_ids"]):
            for s, stream in enumerate(("clean", "corrupt")):
                rows.append(
                    dict(
                        base,
                        source_task="far_v2",
                        condition=c,
                        operation="interchange",
                        instance_id=rid,
                        stream=stream,
                        **{
                            k: float(
                                data[k][j, i, s]
                                if k.startswith("intact")
                                else data[k][0, j, i, s]
                            )
                            for k in (
                                "intact_margin",
                                "patched_margin",
                                "intact_correct",
                                "patched_correct",
                            )
                        },
                    )
                )
    for name, data in source["utilities"].items():
        for i, rid in enumerate(data["prompt_ids"]):
            rows.append(
                dict(
                    base,
                    source_task="ioi" if name == "IOI" else "mmlu",
                    condition=name,
                    operation="interchange"
                    if name == "IOI"
                    else ("zero" if name.endswith("zero") else "h_mean"),
                    instance_id=rid,
                    stream="clean",
                    intact_margin=0.0,
                    patched_margin=0.0,
                    intact_correct=float(data["intact_correct"][j, i]),
                    patched_correct=float(data["patched_correct"][0, j, i]),
                )
            )
    return rows


@pytest.mark.parametrize(
    "scenario", ["pass", "i_boundary", "bad_stream", "mmlu", "collateral", "coverage"]
)
def test_point_metrics_match_reviewed_estimators(scenario):
    from tests.test_a3_statistics import panel
    from component_analysis import a3_statistics as statistics

    p = panel()
    source = p["tasks"]["far_v2"]
    if scenario == "i_boundary":
        source["conditions"]["I"]["patched_margin"][0] -= 0.5
    if scenario == "bad_stream":
        source["conditions"]["D"]["intact_margin"][0, :, 0] = -1
    if scenario == "mmlu":
        source["utilities"]["MMLU_h_mean"]["patched_correct"][0, 0, :2] = 0
    if scenario == "collateral":
        source["conditions"]["H"]["patched_correct"][0, 0, 0, :] = 0
    source["gate_valid"] = np.ones((33, 3), dtype=bool)
    if scenario == "coverage":
        source["gate_valid"][0, 0] = False
    tasks, _, _ = statistics._prepare(p, power=True)
    expected = statistics._evaluate(
        tasks["far_v2"],
        list(range(4)),
        {
            "IOI": source["utilities"]["IOI"]["prompt_ids"],
            "MMLU": source["utilities"]["MMLU_zero"]["prompt_ids"],
        },
    )
    rows = metric_rows(source)
    if scenario == "coverage":
        rows[0]["gate_valid"] = False
    actual = runner.direction_point_metrics(rows, seed=42)
    assert actual["point_pass"] == bool(expected["point_pass"][0, 0])
    assert actual["denominator_valid"] == bool(expected["denominator_valid"][0])
    for c in ("D", "I"):
        assert actual[c + "_fraction"] == pytest.approx(
            expected[c + "_fraction"][0, 0], nan_ok=True
        )


@pytest.mark.parametrize(
    "damage", ["missing", "duplicate", "floor_ids", "floor_intact", "extra_utility"]
)
def test_point_metric_exact_coverage(damage):
    from tests.test_a3_statistics import panel

    rows = metric_rows(panel()["tasks"]["far_v2"])
    if damage == "missing":
        rows.pop(0)
    if damage == "duplicate":
        rows.append(rows[0])
    if damage == "floor_ids":
        rows[-1]["instance_id"] = "new"
    if damage == "floor_intact":
        rows[-1]["intact_correct"] = 0
    if damage == "extra_utility":
        rows.append(dict(rows[-1], operation="steer_positive"))
    with pytest.raises(ValueError):
        runner.direction_point_metrics(rows, seed=42)


def test_numeric_profile_source_hash_is_exact(fake):
    ident = identity()
    ident["numeric_profile"]["source_sha256"] = "wrong"
    with pytest.raises(ValueError, match="source_sha256"):
        runner.capture_readouts(
            object(), [batch()], sites=[SITE], sink=lambda x: None, identity=ident
        )


def test_actual_tiny_llama_capture_and_direction_controls():
    nnsight = pytest.importorskip("nnsight")
    if nnsight.__version__ != "0.7.0":
        pytest.skip("base pinned-NNsight mismatch: " + nnsight.__version__)
    from transformers import LlamaForCausalLM
    from nnsight import NNsight
    from tests.helpers import tiny_config

    torch.manual_seed(920)
    model = NNsight(LlamaForCausalLM(tiny_config(attn_implementation="sdpa")).eval())
    b = batch()
    ident = identity()
    ident["numeric_profile"]["backend"] = "sdpa"
    chunks = []
    runner.capture_readouts(
        model, [b], sites=[SITE], sink=chunks.append, identity=ident
    )
    cap = hooks.capture_forward(
        model, b.input_ids, b.attention_mask, components=[SITE], positions=b.readout
    )
    for i, row in enumerate(chunks[0]["rows"]):
        assert torch.equal(row["heads"][0]["value"], cap.outputs[SITE][i, b.readout[i]])
    projection = chunks[0]["projections"][0]["value"]
    h = torch.stack([r["heads"][0]["value"] for r in chunks[0]["rows"]])
    direction = prepare_image_direction(
        projection,
        projection[:, 0] / projection[:, 0].norm(),
        h,
        id_weights=torch.tensor([0.5, 0.5]),
    )
    index = {
        (
            chunks[0]["profile_id"],
            b.task,
            b.condition,
            b.stream,
            row["instance_id"],
        ): row
        for row in chunks[0]["rows"]
    }
    out = []
    result = runner.score_direction_cells(
        model,
        [b],
        cells=[
            cell("zero"),
            cell("h_mean"),
            cell("steer_positive"),
            cell("steer_negative"),
        ],
        capture_index=index,
        axes={"x": direction},
        sink=out.append,
        identity=ident,
    )
    neighbor = ("head", 0, 1)
    baseline = hooks.capture_forward(
        model,
        b.input_ids,
        b.attention_mask,
        components=[SITE, neighbor],
        positions=b.readout,
    )
    original = baseline.outputs[SITE].detach().cpu()
    replacement = runner.direction_replacement(
        original,
        torch.zeros_like(original),
        direction,
        mode="interchange",
        positions=b.readout,
    )
    positions = torch.arange(b.input_ids.shape[1])[None, :] == b.readout[:, None]
    patched = hooks.capture_forward(
        model,
        b.input_ids,
        b.attention_mask,
        components=[SITE, neighbor],
        positions=b.readout,
        replacements={SITE: hooks.Replacement(replacement, positions)},
    )
    assert torch.equal(patched.outputs[neighbor], baseline.outputs[neighbor])
    assert torch.equal(
        patched.outputs[SITE][~positions], baseline.outputs[SITE][~positions]
    )
    assert result["rows"] == 8 and result["max_replay_margin_error"] < 1e-5
    assert all(r["replay_valid"] for chunk in out for r in chunk["rows"])


@pytest.mark.parametrize(
    "damage", ["bare_bool", "source", "argmax", "control", "serial_geometry"]
)
def test_packing_requires_complete_measured_equivalence(fake, damage):
    ident, index, axes, cells = measured_setup(fake)
    receipt = ident["packed_equivalence"]
    if damage == "bare_bool":
        ident["packed_equivalence"] = {
            "valid": True,
            "profile_id": runner.profile_identity(ident),
        }
    elif damage == "source":
        receipt["scope"]["source_sha256"] = "b" * 64
    elif damage == "argmax":
        receipt["comparisons"][0]["packed"]["patched_argmax"] += 1
    elif damage == "control":
        del receipt["comparisons"][0]["packed"]["replay_errors"]["empty"]
    else:
        receipt["scope"]["profile"]["padded_width"] = 6
    before = len(fake)
    with pytest.raises(ValueError, match="equivalence"):
        runner.score_direction_cells(
            object(),
            [batch()],
            cells=cells,
            capture_index=index,
            axes=axes,
            sink=lambda x: None,
            identity=ident,
        )
    assert len(fake) == before


def test_production_requires_positive_controls_before_forward(fake):
    ident = identity()
    ident.pop("injected")
    ident.pop("diagnostic_only")
    with pytest.raises(ValueError, match="positive"):
        runner.score_direction_cells(
            object(),
            [batch()],
            cells=[cell("zero")],
            capture_index={},
            axes={"x": axis()},
            sink=lambda x: None,
            identity=ident,
        )
    assert fake == []


def test_donor_gather_uses_own_profile_width_and_readout(fake):
    recipient = batch()
    donor = batch("corrupt")
    donor = replace(
        donor,
        input_ids=torch.nn.functional.pad(donor.input_ids, (0, 1)),
        attention_mask=torch.nn.functional.pad(donor.attention_mask, (0, 1)),
        readout=torch.tensor([1, 4]),
    )
    chunks = []
    index = {}
    for b, ident in ((recipient, identity()), (donor, identity(width=6))):
        runner.capture_readouts(
            object(), [b], sites=[SITE], sink=chunks.append, identity=ident
        )
        for row in chunks[-1]["rows"]:
            index[
                (
                    chunks[-1]["profile_id"],
                    b.task,
                    b.condition,
                    b.stream,
                    row["instance_id"],
                )
            ] = row
    c = cell()
    c["donor_maps"] = [
        dict(
            recipient_id=rid,
            recipient_condition="D",
            recipient_stream="clean",
            donor_id=rid,
            donor_condition="D",
            donor_stream="corrupt",
            recipient_positions=[int(recipient.readout[i])],
            donor_positions=[int(donor.readout[i])],
            donor_source_hash="source",
            donor_profile_id=chunks[-1]["profile_id"],
            supported=True,
        )
        for i, rid in enumerate(recipient.ids)
    ]
    out = []
    runner.score_direction_cells(
        object(),
        [recipient],
        cells=[c],
        capture_index=index,
        axes={"x": axis()},
        sink=out.append,
        identity=identity(),
    )
    assert [r["head_norm"] for r in out[0]["rows"]] == pytest.approx([1.0, 2.0])


def test_backend_profile_mismatch_blocks_before_capture(fake, monkeypatch):
    monkeypatch.setattr(hooks, "attention_implementation", lambda m: "changed")
    with pytest.raises(ValueError, match="backend"):
        runner.capture_readouts(
            object(), [batch()], sites=[SITE], sink=lambda x: None, identity=identity()
        )
    assert fake == []


def test_own_clause_summary_is_diagnostic_and_never_readout(fake):
    b = batch()
    ident = identity()
    ident["capture_clause_summary"] = True
    records = [
        dict(
            r,
            streams={
                "clean": dict(
                    semantic=dict(
                        sites=dict(pressure_request=[0, 1]),
                        coverage=dict(pressure_request=dict(supported=True)),
                        prompt_utf8_hex="78",
                    )
                )
            },
        )
        for r in b.records
    ]
    b = replace(b, records=records)
    out = []
    runner.capture_readouts(
        object(), [b], sites=[SITE], sink=out.append, identity=ident
    )
    row = out[0]["rows"][0]
    assert row["clause_summary"]["supported"] is True
    assert row["clause_summary"]["heads"][0]["value"].tolist() == [1.5, 3.0]
    assert row["heads"][0]["value"].tolist() == [3.0, 6.0]


def test_own_clause_missing_span_stays_unsupported(fake):
    out = []
    ident = identity()
    ident["capture_clause_summary"] = True
    runner.capture_readouts(
        object(), [batch()], sites=[SITE], sink=out.append, identity=ident
    )
    assert out[0]["rows"][0]["clause_summary"]["supported"] is False


def test_positive_controls_are_source_bound_and_references_compact(fake):
    index, _ = cache(fake)
    b = batch()
    donor = batch("corrupt")
    ident = identity()
    ident.pop("injected")
    ident.pop("diagnostic_only")
    controls = runner.run_positive_controls(
        object(),
        [b],
        donor_batches=[donor],
        donor_maps=donor_maps(b, donor),
        identity=ident,
    )
    c = dict(cell("zero"), positive_controls=controls["rows"])
    out = []
    runner.score_direction_cells(
        object(),
        [b],
        cells=[c],
        capture_index=index,
        axes={"x": axis()},
        sink=out.append,
        identity=ident,
    )
    assert all(r["gate_valid"] for r in out[0]["rows"])
    assert set(out[0]["rows"][0]["positive_control"]) == {
        "valid",
        "control_id",
        "profile_id",
        "recipient_sha256",
    }
    controls["rows"][0]["measurement"]["max_abs_logit_error"] = 10.0
    before = len(fake)
    with pytest.raises(ValueError, match="positive"):
        runner.score_direction_cells(
            object(),
            [b],
            cells=[c],
            capture_index=index,
            axes={"x": axis()},
            sink=lambda x: None,
            identity=ident,
        )
    assert len(fake) == before


def test_sink_failure_propagates_without_completion(fake):
    def fail(payload):
        raise RuntimeError("disk full")

    with pytest.raises(RuntimeError, match="disk full"):
        runner.capture_readouts(
            object(), [batch()], sites=[SITE], sink=fail, identity=identity()
        )


def test_changed_cached_labels_block(fake):
    index, _ = cache(fake)
    b = replace(batch(), expected_token=torch.tensor([2, 2]))
    with pytest.raises(ValueError, match="label"):
        runner.score_direction_cells(
            object(),
            [b],
            cells=[cell("zero")],
            capture_index=index,
            axes={"x": axis()},
            sink=lambda x: None,
            identity=identity(),
        )


def test_axis_projection_must_match_actual_named_head(fake, monkeypatch):
    index, _ = cache(fake)
    monkeypatch.setattr(hooks, "o_proj_weight", lambda m, layer: torch.zeros(2, 4))
    with pytest.raises(ValueError, match="projection"):
        runner.score_direction_cells(
            object(),
            [batch()],
            cells=[cell("zero")],
            capture_index=index,
            axes={"x": axis()},
            sink=lambda x: None,
            identity=identity(),
        )


def test_axis_hash_binds_actual_numeric_axis(fake):
    index, _ = cache(fake)
    out = []
    runner.score_direction_cells(
        object(),
        [batch()],
        cells=[cell("zero")],
        capture_index=index,
        axes={"x": axis()},
        sink=out.append,
        identity=identity(),
    )
    digest = out[0]["rows"][0]["axis_hash"]
    assert isinstance(digest, str) and len(digest) == 64
    with pytest.raises(ValueError, match="axis hash"):
        runner.score_direction_cells(
            object(),
            [batch()],
            cells=[dict(cell("zero"), axis_hash="f" * 64)],
            capture_index=index,
            axes={"x": axis()},
            sink=lambda x: None,
            identity=identity(),
        )


def test_review85_packing_sensitive_nonzero_patches_block(fake, monkeypatch):
    original = hooks.capture_forward

    def faulty(model, ids, mask, **kwargs):
        cap = original(model, ids, mask, **kwargs)
        baseline = torch.stack((ids.float(), ids.float() * 2), -1)
        changed = any(
            not torch.equal(rep.value, baseline)
            for rep in (kwargs.get("replacements") or {}).values()
        )
        if len(ids) > 2 and changed:
            cap.logits = cap.logits * 1.5
            cap.residual = cap.residual * 1.5
        return cap

    monkeypatch.setattr(hooks, "capture_forward", faulty)
    index, chunks = cache(fake)
    maps = donor_maps(batch(), batch("corrupt"), chunks[0]["profile_id"])
    axes = {
        "x": axis(),
        "y": prepare_image_direction(
            torch.eye(2),
            torch.tensor([0.0, 1.0]),
            torch.tensor([[1.0, 2.0], [2.0, 4.0]]),
            id_weights=torch.tensor([0.5, 0.5]),
        ),
    }
    cells = [
        dict(cell("interchange", "x"), axis_index=0, donor_maps=maps),
        dict(cell("zero", "y"), axis_index=1),
        dict(cell("steer_positive", "x"), axis_index=2),
    ]
    with pytest.raises(ValueError, match="equivalence margin disagreement"):
        runner.measure_packing_equivalence(
            object(),
            [batch()],
            cells=cells,
            capture_index=index,
            axes=axes,
            identity=identity(2),
        )


def test_review85_fabricated_positive_control_blocks(fake):
    ident = identity()
    ident.pop("injected")
    ident.pop("diagnostic_only")
    b = batch()
    pid = runner.profile_identity(ident)
    controls = [
        dict(
            task=b.task,
            condition=b.condition,
            instance_id=rid,
            stream=b.stream,
            valid=True,
            profile_id=pid,
            recipient_sha256=runner._recipient_digest(b, i),
            control_id="f" * 64,
        )
        for i, rid in enumerate(b.ids)
    ]
    before = len(fake)
    with pytest.raises(ValueError, match="positive"):
        runner.score_direction_cells(
            object(),
            [b],
            cells=[dict(cell("zero"), positive_controls=controls)],
            capture_index={},
            axes={"x": axis()},
            sink=lambda x: None,
            identity=ident,
        )
    assert len(fake) == before


def test_review85_positive_runtime_checked_before_calibration(fake, monkeypatch):
    monkeypatch.setattr(hooks, "attention_implementation", lambda m: "stale")
    monkeypatch.setattr(
        runner.ladder,
        "positive_control",
        lambda *a, **kw: pytest.fail("must reject before forward"),
    )
    with pytest.raises(ValueError, match="backend"):
        runner.run_positive_controls(
            object(),
            [batch()],
            donor_batches=[batch("corrupt")],
            donor_maps=[],
            identity=identity(),
        )


@pytest.mark.parametrize("damage", ["inputs", "axis", "donor", "maps", "missing_cell"])
def test_measured_equivalence_rejects_unrelated_execution(fake, damage):
    import copy

    ident, index, axes, cells = measured_setup(fake)
    requested = batch()
    if damage == "inputs":
        requested = replace(requested, input_ids=requested.input_ids + 1)
    elif damage == "axis":
        axes = copy.deepcopy(axes)
        axes["x"]["sigma_fit"] += 0.1
    elif damage == "donor":
        key = next(k for k in index if k[3] == "corrupt")
        index[key] = copy.deepcopy(index[key])
        index[key]["heads"][0]["value"] += 1
    elif damage == "maps":
        cells = copy.deepcopy(cells)
        cells[0]["donor_maps"][0]["note"] = "unmeasured change"
    else:
        cells = cells[:-1]
    before = len(fake)
    with pytest.raises(ValueError, match="equivalence"):
        runner.score_direction_cells(
            object(),
            [requested],
            cells=cells,
            capture_index=index,
            axes=axes,
            sink=lambda x: None,
            identity=ident,
        )
    assert len(fake) == before


@pytest.mark.parametrize(
    "damage", ["error", "valid", "sender_keys", "donor", "geometry", "tolerance"]
)
def test_positive_backing_changed_measured_fields_reject_old_digest(fake, damage):
    import copy

    b = batch()
    d = batch("corrupt")
    ident = identity()
    index, _ = cache(fake)
    controls = runner.run_positive_controls(
        object(), [b], donor_batches=[d], donor_maps=donor_maps(b, d), identity=ident
    )["rows"]
    controls = copy.deepcopy(controls)
    r = controls[0]
    if damage == "error":
        r["reviewed"]["max_abs_logit_error"] = 999.0
    elif damage == "valid":
        r["valid"] = False
    elif damage == "sender_keys":
        r["sender_keys"] = []
    elif damage == "donor":
        r["donor"]["tokens"][0] += 1
    elif damage == "geometry":
        r["measurement"]["padded_width"] += 1
    else:
        r["measurement"]["atol"] = 1.0
    before = len(fake)
    with pytest.raises(ValueError, match="positive"):
        runner.score_direction_cells(
            object(),
            [b],
            cells=[dict(cell("zero"), positive_controls=controls)],
            capture_index=index,
            axes={"x": axis()},
            sink=lambda x: None,
            identity=ident,
        )
    assert len(fake) == before


def test_actual_tiny_llama_multi_axis_packing_and_positive_backing():
    nnsight = pytest.importorskip("nnsight")
    if nnsight.__version__ != "0.7.0":
        pytest.skip("base pinned-NNsight mismatch: " + nnsight.__version__)
    from transformers import LlamaForCausalLM
    from nnsight import NNsight
    from tests.helpers import tiny_config

    torch.manual_seed(921)
    model = NNsight(LlamaForCausalLM(tiny_config(attn_implementation="sdpa")).eval())
    b = batch()
    d = batch("corrupt")
    serial = identity()
    serial["numeric_profile"]["backend"] = "sdpa"
    chunks = []
    runner.capture_readouts(
        model, [b, d], sites=[SITE], sink=chunks.append, identity=serial
    )
    index = {
        (
            chunk["profile_id"],
            row["task"],
            row["condition"],
            row["stream"],
            row["instance_id"],
        ): row
        for chunk in chunks
        for row in chunk["rows"]
    }
    w = chunks[0]["projections"][0]["value"]
    h = torch.stack([row["heads"][0]["value"] for row in chunks[0]["rows"]])
    axes = {
        name: prepare_image_direction(
            w,
            w[:, column] / w[:, column].norm(),
            h,
            id_weights=torch.tensor([0.5, 0.5]),
        )
        for name, column in [("x", 0), ("y", 1)]
    }
    maps = donor_maps(b, d, runner.profile_identity(serial))
    cells = [
        dict(cell("interchange", "x"), axis_index=0, donor_maps=maps),
        dict(cell("zero", "y"), axis_index=1),
        dict(cell("steer_positive", "x"), axis_index=2),
    ]
    packed = identity(2)
    packed["numeric_profile"]["backend"] = "sdpa"
    packed["packed_equivalence"] = runner.measure_packing_equivalence(
        model, [b], cells=cells, capture_index=index, axes=axes, identity=packed
    )
    assert (
        packed["packed_equivalence"]["valid"]
        and packed["packed_equivalence"]["nonzero_patches"] >= 2
    )
    assert len(packed["packed_equivalence"]["comparisons"]) == 8
    controls = runner.run_positive_controls(
        model, [b], donor_batches=[d], donor_maps=maps, identity=packed
    )["rows"]
    assert all(
        r["measurement"]["valid"]
        and r["sender_keys"] == [list(k) for k in hooks.all_component_keys(model)]
        for r in controls
    )
    stored = []
    runner.capture_readouts(
        model, [b], sites=[SITE], sink=stored.append, identity=packed
    )
    for chunk in stored:
        for row in chunk["rows"]:
            index[
                (
                    chunk["profile_id"],
                    row["task"],
                    row["condition"],
                    row["stream"],
                    row["instance_id"],
                )
            ] = row
    out = []
    runner.score_direction_cells(
        model,
        [b],
        cells=[dict(c, positive_controls=controls) for c in cells],
        capture_index=index,
        axes=axes,
        sink=out.append,
        identity=packed,
    )
    assert all(r["gate_valid"] for chunk in out for r in chunk["rows"])


def test_equivalence_rejects_missing_comparison_even_with_new_digest(fake):
    ident, index, axes, cells = measured_setup(fake)
    receipt = ident["packed_equivalence"]
    receipt["comparisons"].pop()
    receipt["receipt_sha256"] = runner._digest(
        {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    )
    with pytest.raises(ValueError, match="equivalence"):
        runner.score_direction_cells(
            object(),
            [batch()],
            cells=cells,
            capture_index=index,
            axes=axes,
            sink=lambda x: None,
            identity=ident,
        )


def test_positive_rehashed_incomplete_sender_coverage_blocks(fake):
    b = batch()
    d = batch("corrupt")
    index, _ = cache(fake)
    rows = runner.run_positive_controls(
        object(),
        [b],
        donor_batches=[d],
        donor_maps=donor_maps(b, d),
        identity=identity(),
    )["rows"]
    rows[0]["sender_keys"] = []
    rows[0]["control_id"] = runner._digest(
        {k: v for k, v in rows[0].items() if k != "control_id"}
    )
    with pytest.raises(ValueError, match="positive"):
        runner.score_direction_cells(
            object(),
            [b],
            cells=[dict(cell("zero"), positive_controls=rows)],
            capture_index=index,
            axes={"x": axis()},
            sink=lambda x: None,
            identity=identity(),
        )
