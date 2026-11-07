"""Bounded no-grad A3 direction inference; publication/admission belong to callers.

``sink(payload)`` consumes one CPU chunk synchronously. Readout indices are
callables (or mappings) keyed by (profile_id, task, condition, stream, id).
Every entry is one capture row, including padded tokens, labels and provenance.
No full sequence activation, residual or vocabulary logits escape a chunk.
Cells name site, axis (key in axes), seed/family/axis_index, operation and optional
batch task/condition/stream selectors. Interchange requires explicit donor_maps.
Positive calibration is separate; attach its rows as cell['positive_controls'].
Packed execution requires identity['packed_equivalence'] binding profile_id.
This module never admits a profile, chooses a fallback or publishes completion.
"""

from __future__ import annotations

from dataclasses import replace
from collections import Counter
import hashlib
import json
import math
import re
import numpy as np
import torch

from component_analysis import hooks, specificity_ladder as ladder
from component_analysis.a3_directions import (
    direction_replacement,
    perturbation_diagnostics,
)

PROFILE_FIELDS = {
    "padded_width",
    "physical_batch_size",
    "axis_tile_size",
    "dtype",
    "backend",
    "model",
    "model_revision",
    "source_sha256",
}
OPERATIONS = {"interchange", "zero", "h_mean", "steer_positive", "steer_negative"}


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def profile_identity(identity):
    profile = identity.get("numeric_profile", {})
    _require(PROFILE_FIELDS <= set(profile), "complete numeric_profile required")
    for name in ("padded_width", "physical_batch_size", "axis_tile_size"):
        _require(
            type(profile[name]) is int and profile[name] > 0, "invalid profile geometry"
        )
    for name in PROFILE_FIELDS - {
        "padded_width",
        "physical_batch_size",
        "axis_tile_size",
    }:
        _require(
            isinstance(profile[name], str) and bool(profile[name]),
            "invalid profile identity",
        )
    _require(
        re.fullmatch(r"[0-9a-f]{64}", profile["source_sha256"]) is not None,
        "source_sha256 must be full digest",
    )
    canonical = {k: v for k, v in profile.items() if k != "profile_id"}
    digest = hashlib.sha256(
        json.dumps(
            canonical, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()
    _require(
        "profile_id" not in profile or profile["profile_id"] == digest,
        "changed numeric profile id",
    )
    return digest


def axis_identity(direction):
    """Digest the fp32 numeric axis used by the reviewed replacement algebra."""
    digest = hashlib.sha256()
    for name in ("projection", "v", "pullback", "h_center"):
        value = direction[name].detach().float().cpu().contiguous()
        _require(bool(torch.isfinite(value).all()), "nonfinite numeric axis")
        digest.update(json.dumps([name, list(value.shape), str(value.dtype)]).encode())
        digest.update(value.numpy().tobytes())
    digest.update(
        json.dumps(
            {k: float(direction[k]) for k in ("sigma_fit", "projected_variance")},
            sort_keys=True,
            allow_nan=False,
        ).encode()
    )
    return digest.hexdigest()


def _digest(value):
    def portable(x):
        if isinstance(x, torch.Tensor):
            x = x.detach().cpu().contiguous()
            return dict(
                dtype=str(x.dtype),
                shape=list(x.shape),
                bytes_sha256=hashlib.sha256(
                    x.view(torch.uint8).numpy().tobytes()
                ).hexdigest(),
            )
        if isinstance(x, dict):
            return {str(k): portable(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [portable(v) for v in x]
        return x

    return hashlib.sha256(
        json.dumps(
            portable(value), sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def _geometry(batch, identity, *, measuring=False):
    ladder.validate_batch(batch)
    p = identity["numeric_profile"]
    tile = p["axis_tile_size"]
    _require(
        batch.input_ids.shape[1] == p["padded_width"]
        and len(batch.ids) * tile == p["physical_batch_size"],
        "batch/profile geometry mismatch; no automatic fallback",
    )
    _require(
        batch.input_ids.dtype in (torch.int32, torch.int64)
        and batch.readout.dtype in (torch.int32, torch.int64),
        "integer tokens/readouts required",
    )
    if tile > 1 and not measuring:
        _packing_receipt(identity, batch)
    return tile


def _packing_receipt(identity, batch):
    # Distinct target examples require a separate byte-checked attestation.
    # The exact measured-scope API below remains unchanged and fail-closed.
    if "profile_reuse" in identity:
        _require("packed_equivalence" not in identity, "ambiguous exact/reused packing evidence")
        from component_analysis.a3_direction_runtime import validate_profile_reuse
        return validate_profile_reuse(identity, batch)
    receipt = identity.get("packed_equivalence", {})
    body = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    _require(
        receipt.get("receipt_sha256") == _digest(body),
        "equivalence receipt content hash mismatch",
    )
    scope = receipt.get("scope", {})
    _require(
        receipt.get("kind") == "measured_direction_packing_v2"
        and receipt.get("valid") is True
        and scope.get("profile") == identity["numeric_profile"]
        and receipt.get("scope_sha256") == _digest(scope)
        and scope.get("source_sha256") == identity["numeric_profile"]["source_sha256"],
        "equivalence source/profile mismatch",
    )
    bid = _digest([_recipient_digest(batch, i) for i in range(len(batch.ids))])
    _require(
        bid in scope.get("batches", {}),
        "equivalence tested inputs do not cover requested batch",
    )
    comparisons = receipt.get("comparisons", [])
    _require(
        comparisons
        and receipt.get("dummy_lanes_tested") is True
        and receipt.get("distinct_axes", 0) >= 2
        and receipt.get("nonzero_patches", 0) >= 2,
        "equivalence lacks nonzero axes/dummy coverage",
    )
    expected = []
    expected_axes = {}
    for batch_id, cell_specs in scope.get("batches", {}).items():
        recipients = scope.get("recipients", {}).get(batch_id, [])
        _require(
            recipients
            and len(cell_specs) >= identity["numeric_profile"]["axis_tile_size"],
            "equivalence scope coverage invalid",
        )
        for spec in cell_specs + scope.get("dummy_cells", {}).get(batch_id, []):
            for recipient in recipients:
                key = dict(
                    recipient,
                    **{
                        k: spec[k]
                        for k in ("site", "seed", "family", "axis_index", "operation")
                    },
                )
                kid = _digest(key)
                expected.append(kid)
                expected_axes[kid] = spec["axis_sha256"]
    _require(
        Counter(expected) == Counter(_digest(c["key"]) for c in comparisons),
        "equivalence missing/duplicate comparison coverage",
    )
    nonzero_axes = set()
    for c in comparisons:
        axis = expected_axes[_digest(c["key"])]
        _require(
            c["serial"].get("axis_hash") == axis
            and c["packed"].get("axis_hash") == axis,
            "equivalence axis comparison mismatch",
        )
        if c["serial"].get("head_norm", 0) > 0 and c["packed"].get("head_norm", 0) > 0:
            nonzero_axes.add(axis)
        for field in ("intact_margin", "patched_margin"):
            left, right = c["serial"][field], c["packed"][field]
            _require(
                math.isfinite(left)
                and math.isfinite(right)
                and abs(left - right) <= 1e-5 + 1e-5 * abs(left),
                "equivalence margin disagreement",
            )
        _require(
            all(
                c["serial"][k] == c["packed"][k]
                for k in ("intact_argmax", "patched_argmax")
            ),
            "equivalence argmax disagreement",
        )
        for side in ("serial", "packed"):
            errors = c[side]["replay_errors"]
            _require(
                set(errors) == {"empty", "head_self", "zero_coefficient"}
                and all(math.isfinite(v) and 0 <= v <= 1e-5 for v in errors.values()),
                "equivalence replay controls invalid",
            )
    _require(
        len(nonzero_axes) >= 2, "equivalence requires distinct nonzero axis patches"
    )
    return scope["batches"][bid]


def _cell_scope(batch, cell, axes, index):
    donors = []
    for i in range(len(batch.ids)):
        if cell["operation"] == "interchange":
            _, m = _mapping(cell, batch, i, index, "", tuple(cell["site"]))
            key = (
                m["donor_profile_id"],
                batch.task,
                m["donor_condition"],
                m["donor_stream"],
                m["donor_id"],
            )
            donors.append(
                dict(mapping=m, cached_donor_sha256=_digest(_entry(index, key)))
            )
    return dict(
        site=list(cell["site"]),
        seed=cell["seed"],
        family=cell["family"],
        axis_index=cell["axis_index"],
        operation=cell["operation"],
        axis_sha256=axis_identity(axes[cell["axis"]]),
        donors=donors,
    )


def _runtime(model, identity):
    _, dtype = hooks.device_and_dtype(model)
    _require(
        str(dtype) == identity["numeric_profile"]["dtype"],
        "model dtype/profile mismatch",
    )
    _require(
        hooks.attention_implementation(model) == identity["numeric_profile"]["backend"],
        "model backend/profile mismatch",
    )


def _replicate(batch, tile):
    values = {}
    for name in (
        "input_ids",
        "attention_mask",
        "readout",
        "opposite_token",
        "honest_token",
        "expected_token",
        "choice_tokens",
    ):
        x = getattr(batch, name)
        values[name] = None if x is None else x.repeat((tile,) + (1,) * (x.ndim - 1))
    return replace(batch, ids=batch.ids * tile, records=batch.records * tile, **values)


def _forward(model, batch, sites, replacements=None):
    with torch.no_grad():
        return ladder._capture(model, batch, sites, replacements)


def _scalar_stats(batch, capture, logits):
    return {
        k: v.detach().cpu()
        for k, v in ladder._stats(batch, logits, capture.logits).items()
    }


def _entry(index, key):
    try:
        value = index(key) if callable(index) else index[key]
    except KeyError as exc:
        raise ValueError("missing profile-bound capture: " + str(key)) from exc
    _require(
        tuple(
            value.get(k)
            for k in ("profile_id", "task", "condition", "stream", "instance_id")
        )
        == key,
        "capture profile/source identity mismatch",
    )
    return value


def _head(row, site):
    matches = [v["value"] for v in row["heads"] if tuple(v["site"]) == tuple(site)]
    _require(len(matches) == 1, "missing/duplicate cached site")
    value = torch.as_tensor(matches[0])
    _require(
        value.device.type == "cpu"
        and value.ndim == 1
        and bool(torch.isfinite(value).all()),
        "invalid cached readout",
    )
    return value


def _clause_summary(batch, i, sites, capture, identity):
    unsupported = dict(
        supported=False,
        reason="missing/unsupported frozen own-clause span",
        diagnostic_only=True,
    )
    if not identity.get("capture_clause_summary") or batch.task in ("ioi", "mmlu"):
        return unsupported
    stream = batch.records[i].get("streams", {}).get(batch.stream, {})
    semantic = stream.get("semantic", {})
    positions = semantic.get("sites", {}).get("pressure_request", [])
    if (
        not semantic.get("coverage", {}).get("pressure_request", {}).get("supported")
        or not positions
    ):
        return unsupported
    _require(
        all(
            type(p) is int
            and 0 <= p < batch.input_ids.shape[1]
            and bool(batch.attention_mask[i, p])
            for p in positions
        )
        and len(set(positions)) == len(positions),
        "invalid frozen own-clause span",
    )
    if "prompt" in stream:
        _require(
            semantic.get("prompt_utf8_hex") == stream["prompt"].encode().hex(),
            "changed clause prompt provenance",
        )
    if "tokens" in stream:
        _require(
            stream["tokens"]
            == batch.input_ids[i, : int(batch.attention_mask[i].sum())].tolist(),
            "changed own-clause tokenization",
        )
    heads = [
        dict(
            site=list(site),
            value=capture.outputs[site][i, positions]
            .detach()
            .float()
            .mean(0)
            .cpu()
            .clone(),
        )
        for site in sites
    ]
    return dict(
        supported=True,
        diagnostic_only=True,
        positions=positions,
        heads=heads,
        prompt_utf8_hex=semantic.get("prompt_utf8_hex"),
        semantics="own verified clause mean; never readout substitute",
    )


def _capture_readouts(model, batches, *, sites, sink, identity, measuring=False):
    """Flush one union-site CPU chunk per batch. A sink exception aborts execution.

    Optional own-clause summaries use each stream's frozen semantic record;
    missing spans stay unsupported. Primary values always use native readouts.
    """
    pid = profile_identity(identity)
    _runtime(model, identity)
    sites = [tuple(s) for s in sites]
    _require(
        sites
        and len(set(sites)) == len(sites)
        and all(len(s) == 3 and s[0] == "head" for s in sites),
        "unique head sites required",
    )
    count = chunks = total_bytes = 0
    lane_receipts = []
    seen = set()
    geometry = hooks.geometry(model)
    width = geometry["head_dim"]
    projections = [
        dict(
            site=list(s),
            value=hooks.o_proj_weight(model, s[1])[:, s[2] * width : (s[2] + 1) * width]
            .detach()
            .float()
            .cpu()
            .clone(),
        )
        for s in sites
    ]
    for batch in batches:
        tile = _geometry(batch, identity, measuring=measuring)
        packed = _replicate(batch, tile)
        capture, logits = _forward(model, packed, sites)
        _require(str(logits.dtype) == "torch.float32", "canonical logits must be fp32")
        stats = _scalar_stats(packed, capture, logits)
        n = len(batch.ids)
        for lane in range(1, tile):
            _require(
                torch.allclose(
                    stats["margin"][:n],
                    stats["margin"][lane * n : (lane + 1) * n],
                    atol=1e-5,
                    rtol=1e-5,
                )
                and torch.equal(
                    stats["argmax"][:n], stats["argmax"][lane * n : (lane + 1) * n]
                ),
                "packed intact lanes disagree",
            )
        references=[]; comparisons=[]
        for site in sites:
            for i,rid in enumerate(batch.ids):
                reference=capture.outputs[site][i,int(batch.readout[i])].detach().float().cpu()
                head_hash=_digest(reference)
                references.append(dict(site=list(site),instance_id=rid,readout=int(batch.readout[i]),
                    vector_sha256=head_hash,vector_shape=list(reference.shape),dtype='torch.float32'))
                for lane in range(1,tile):
                    j=lane*n+i;value=capture.outputs[site][j,int(packed.readout[j])].detach().float().cpu()
                    _require(torch.allclose(reference,value,atol=1e-5,rtol=1e-5),'packed intact head lanes disagree')
                    comparisons.append(dict(site=list(site),instance_id=rid,lane=lane,readout=int(packed.readout[j]),
                        reference_sha256=head_hash,lane_sha256=_digest(value),head_allclose=True,
                        max_abs_head_error=float((reference-value).abs().max()),reference_max_abs_head=float(reference.abs().max()),
                        max_abs_margin_error=abs(float(stats['margin'][i]-stats['margin'][j])),
                        reference_margin=float(stats['margin'][i]),argmax_equal=bool(stats['argmax'][i]==stats['argmax'][j])))
        lane_receipt=dict(kind='a3_intact_lane_consistency_v1',valid=True,serial_comparison_performed=False,
            numeric_profile=identity['numeric_profile'],profile_id=pid,source_sha256=identity['numeric_profile']['source_sha256'],
            operation='readout_capture',source_task=batch.task,condition=batch.condition,stream=batch.stream,
            replicated_lanes=tile,physical_batch_size=n*tile,batch_sha256=_digest([_recipient_digest(batch,i) for i in range(n)]),
            readout_map=[dict(instance_id=rid,source_readout=int(batch.readout[i]),
                execution_readouts=[int(packed.readout[lane*n+i]) for lane in range(tile)]) for i,rid in enumerate(batch.ids)],
            head_references=references,comparisons=comparisons)
        lane_receipt['receipt_sha256']=_digest(lane_receipt)
        lane_receipts.append(lane_receipt)
        rows = []
        for i, rid in enumerate(batch.ids):
            key = (pid, batch.task, batch.condition, batch.stream, rid)
            _require(key not in seen, "duplicate profile-bound capture")
            seen.add(key)
            heads = [
                dict(
                    site=list(s),
                    value=capture.outputs[s][i, int(batch.readout[i])]
                    .detach()
                    .cpu()
                    .clone(),
                )
                for s in sites
            ]
            row = dict(
                profile_id=pid,
                task=batch.task,
                condition=batch.condition,
                stream=batch.stream,
                instance_id=rid,
                record=dict(batch.records[i]),
                tokens=batch.input_ids[i].tolist(),
                attention_mask=batch.attention_mask[i].tolist(),
                readout=int(batch.readout[i]),
                opposite_token=int(batch.opposite_token[i]),
                honest_token=int(batch.honest_token[i]),
                expected_token=int(batch.expected_token[i]),
                choice_tokens=None
                if batch.choice_tokens is None
                else batch.choice_tokens[i].tolist(),
                heads=heads,
                stats={k: v[i].item() for k, v in stats.items()},
                clause_summary=_clause_summary(batch, i, sites, capture, identity),
            )
            rows.append(row)
            total_bytes += sum(
                h["value"].numel() * h["value"].element_size()
                for h in heads + row["clause_summary"].get("heads", [])
            )
        del capture, logits, packed, stats
        sink(
            dict(
                kind="a3_readout_chunk",
                identity=identity,
                profile_id=pid,
                rows=rows,
                projections=projections,
                lane_consistency=lane_receipt,
            )
        )
        count += len(rows)
        chunks += 1
    return dict(
        profile_id=pid,
        rows=count,
        chunks=chunks,
        readout_bytes=total_bytes,
        lane_consistency_receipts=lane_receipts,
        complete=False,
    )


def _recipient_digest(batch, i):
    data = dict(
        tokens=batch.input_ids[i].tolist(),
        mask=batch.attention_mask[i].tolist(),
        readout=int(batch.readout[i]),
        record=batch.records[i],
        task=batch.task,
        condition=batch.condition,
        stream=batch.stream,
        instance_id=batch.ids[i],
        expected_token=int(batch.expected_token[i]),
        opposite_token=int(batch.opposite_token[i]),
        honest_token=int(batch.honest_token[i]),
        choice_tokens=None
        if batch.choice_tokens is None
        else batch.choice_tokens[i].tolist(),
    )
    return hashlib.sha256(
        json.dumps(
            data, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def _snapshot(batch):
    _require(len(batch.ids) == 1, "positive snapshot requires singleton")
    return dict(
        task=batch.task,
        condition=batch.condition,
        instance_id=batch.ids[0],
        stream=batch.stream,
        tokens=batch.input_ids[0].tolist(),
        attention_mask=batch.attention_mask[0].tolist(),
        readout=int(batch.readout[0]),
        record=batch.records[0],
        opposite_token=int(batch.opposite_token[0]),
        honest_token=int(batch.honest_token[0]),
        expected_token=int(batch.expected_token[0]),
    )


def run_positive_controls(model, batches, *, donor_batches, donor_maps, identity):
    """Bind the reviewed single-pass full-vocabulary all-sender measurement."""
    pid = profile_identity(identity)
    _runtime(model, identity)
    batches = list(batches)
    donor_batches = list(donor_batches)
    keys = [tuple(k) for k in hooks.all_component_keys(model)]
    donors = {
        (b.condition, b.ids[0], b.stream): b
        for batch in donor_batches
        for b in ladder._rows(batch)
    }
    mappings = {
        (m["recipient_condition"], m["recipient_id"], m["recipient_stream"]): m
        for m in donor_maps
    }
    _require(len(mappings) == len(donor_maps), "duplicate positive donor maps")
    output = []
    for batch in batches:
        _geometry(batch, identity, measuring=True)
        for i, recipient in enumerate(ladder._rows(batch)):
            m = mappings[(recipient.condition, recipient.ids[0], recipient.stream)]
            donor = donors[(m["donor_condition"], m["donor_id"], m["donor_stream"])]
            _require(
                m.get("supported") is True
                and m["recipient_positions"] == recipient.readout.tolist()
                and m["donor_positions"] == donor.readout.tolist(),
                "positive requires explicit own-readout map",
            )
            for name in ("source_hash", "source_id", "split"):
                if donor.records[0].get(name) is not None:
                    _require(
                        m.get("donor_" + name) == donor.records[0][name],
                        "positive donor provenance mismatch",
                    )
            reviewed = ladder.positive_control(
                model, [recipient], donor_batches=[donor], donor_maps=[m]
            )[0]
            width = max(recipient.input_ids.shape[1], donor.input_ids.shape[1])
            measured = dict(
                max_abs_logit_error=reviewed["max_abs_logit_error"],
                valid=reviewed["valid"],
                atol=1e-5,
                rtol=1e-5,
                measured_by="specificity_ladder.positive_control",
                full_vocabulary=True,
                calibration_recipient=_snapshot(
                    ladder._pad_calibration_batch(recipient, width)
                ),
                calibration_donor=_snapshot(
                    ladder._pad_calibration_batch(donor, width)
                ),
                padded_width=width,
                physical_batch_size=1,
            )
            _require(
                reviewed["valid"] is True
                and reviewed["sender_keys"] == [list(k) for k in keys]
                and math.isclose(
                    reviewed["max_abs_logit_error"],
                    measured["max_abs_logit_error"],
                    abs_tol=1e-5,
                    rel_tol=1e-5,
                ),
                "positive repeated measurement mismatch",
            )
            row = dict(
                task=batch.task,
                condition=batch.condition,
                instance_id=recipient.ids[0],
                stream=batch.stream,
                kind="measured_all_sender_positive_v2",
                valid=True,
                profile_id=pid,
                numeric_profile=identity["numeric_profile"],
                recipient_sha256=_recipient_digest(batch, i),
                recipient=_snapshot(recipient),
                donor=_snapshot(donor),
                donor_provenance=m,
                sender_keys=[list(k) for k in keys],
                measurement=measured,
                reviewed=reviewed,
            )
            row["control_id"] = _digest(row)
            output.append(row)
    return dict(
        kind="a3_positive_controls", identity=identity, profile_id=pid, rows=output
    )


def _positive_reference(cell, batch, i, pid, identity, model):
    matches = [
        r
        for r in cell.get("positive_controls", [])
        if (r.get("task"), r.get("condition"), r.get("instance_id"), r.get("stream"))
        == (batch.task, batch.condition, batch.ids[i], batch.stream)
    ]
    if not matches:
        _require(
            identity.get("injected") is True
            and identity.get("diagnostic_only") is True,
            "production requires separate positive controls before candidate scoring",
        )
        return None
    _require(len(matches) == 1, "duplicate positive control")
    row = matches[0]
    body = {k: v for k, v in row.items() if k != "control_id"}
    _require(
        row.get("control_id") == _digest(body)
        and row.get("kind") == "measured_all_sender_positive_v2",
        "positive backing measurement content hash mismatch",
    )
    expected_keys = [list(k) for k in hooks.all_component_keys(model)]
    _require(
        row.get("valid") is True
        and row.get("profile_id") == pid
        and row.get("numeric_profile") == identity["numeric_profile"]
        and row.get("recipient_sha256") == _recipient_digest(batch, i)
        and row.get("sender_keys") == expected_keys,
        "positive failed/source/profile/sender coverage mismatch",
    )
    recipient = list(ladder._rows(batch))[i]
    _require(
        row.get("recipient") == _snapshot(recipient),
        "positive recipient provenance mismatch",
    )
    donor = row.get("donor", {})
    m = row.get("donor_provenance", {})
    measured = row.get("measurement", {})
    _require(
        m.get("supported") is True
        and m.get("recipient_id") == batch.ids[i]
        and m.get("recipient_condition") == batch.condition
        and m.get("recipient_stream") == batch.stream
        and m.get("recipient_positions") == [int(batch.readout[i])]
        and all(m.get("donor_" + k) == donor.get(k) for k in ("condition", "stream"))
        and m.get("donor_id") == donor.get("instance_id")
        and m.get("donor_positions") == [donor.get("readout")],
        "positive donor/readout provenance mismatch",
    )
    for name in ("source_hash", "source_id", "split"):
        if donor.get("record", {}).get(name) is not None:
            _require(
                m.get("donor_" + name) == donor["record"][name],
                "positive donor source mismatch",
            )
    width = max(len(row["recipient"]["tokens"]), len(donor.get("tokens", [])))
    for original, field in (
        (row["recipient"], "calibration_recipient"),
        (donor, "calibration_donor"),
    ):
        padded = dict(
            original,
            tokens=original["tokens"] + [0] * (width - len(original["tokens"])),
            attention_mask=original["attention_mask"]
            + [0] * (width - len(original["attention_mask"])),
        )
        _require(
            measured.get(field) == padded,
            "positive separate calibration padding geometry mismatch",
        )
    error = measured.get("max_abs_logit_error", float("inf"))
    _require(
        measured.get("valid") is True
        and measured.get("full_vocabulary") is True
        and measured.get("measured_by") == "specificity_ladder.positive_control"
        and measured.get("atol") == 1e-5
        and measured.get("rtol") == 1e-5
        and isinstance(error, (int, float))
        and math.isfinite(error)
        and error >= 0
        and measured.get("padded_width") == width
        and measured.get("physical_batch_size") == 1,
        "positive measured full-vocabulary recovery invalid",
    )
    reviewed = row.get("reviewed", {})
    _require(
        reviewed.get("valid") is True
        and reviewed.get("sender_keys") == expected_keys
        and reviewed.get("donor_provenance") == m
        and all(
            reviewed.get(k) == row.get(k) for k in ("task", "instance_id", "stream")
        )
        and math.isclose(
            reviewed.get("max_abs_logit_error", float("inf")),
            error,
            abs_tol=1e-5,
            rel_tol=1e-5,
        ),
        "positive reviewed calibration backing invalid",
    )
    return {
        k: row[k] for k in ("control_id", "profile_id", "recipient_sha256", "valid")
    }


def _mapping(cell, batch, i, index, pid, site):
    rid = batch.ids[i]
    maps = [
        m
        for m in cell.get("donor_maps", [])
        if (
            m.get("recipient_condition"),
            m.get("recipient_id"),
            m.get("recipient_stream"),
        )
        == (batch.condition, rid, batch.stream)
    ]
    _require(len(maps) == 1, "exactly one explicit donor readout map required")
    m = maps[0]
    _require(
        m.get("supported") is True
        and m.get("recipient_positions") == [int(batch.readout[i])],
        "unsupported/mismatched recipient readout map",
    )
    donor_pid = m.get("donor_profile_id")
    _require(
        isinstance(donor_pid, str) and donor_pid, "explicit donor profile required"
    )
    key = (
        donor_pid,
        batch.task,
        m["donor_condition"],
        m["donor_stream"],
        m["donor_id"],
    )
    donor = _entry(index, key)
    _require(
        m.get("donor_positions") == [donor["readout"]],
        "map must gather donor own readout",
    )
    _require(
        m.get("donor_source_hash") == donor["record"].get("source_hash")
        and bool(m.get("donor_source_hash")),
        "donor source hash mismatch",
    )
    _require(
        m["donor_id"] == rid
        and m["donor_condition"] == batch.condition
        and m["donor_stream"] != batch.stream,
        "primary donor must be same-id same-condition opposite stream",
    )
    if batch.task == "ioi":
        _require(
            batch.stream == "clean" and m["donor_stream"] == "corrupt",
            "IOI requires frozen corrupt donor",
        )
    return _head(donor, site), dict(m)


def _score_direction_cells(
    model, batches, *, cells, capture_index, axes, sink, identity, measuring=False
):
    """Score fixed axis tiles, including dummy lanes, and flush raw scalar rows.

    Recipient cache replay is checked against fresh same-geometry captures.
    Scientific cells require backing positive_controls from run_positive_controls.
    Missing controls are diagnostic rows only under an explicit injected identity;
    failed or stale backing measurements always block before candidate forwards.
    """
    pid = profile_identity(identity)
    _runtime(model, identity)
    count = chunks = 0
    max_error = 0.0
    for batch in batches:
        tile = _geometry(batch, identity, measuring=measuring)
        selected = [
            c
            for c in cells
            if all(
                c.get(k, getattr(batch, k)) == getattr(batch, k)
                for k in ("task", "condition", "stream")
            )
        ]
        _require(
            all(c.get("operation") in OPERATIONS for c in selected),
            "unknown directional operation",
        )
        _require(
            batch.task != "mmlu"
            or all(c["operation"] != "interchange" for c in selected),
            "MMLU has no native donor interchange",
        )
        if tile > 1 and not measuring:
            covered = _packing_receipt(identity, batch)
            actual = [_cell_scope(batch, c, axes, capture_index) for c in selected]
            _require(
                actual == covered,
                "equivalence tested maps/axes/coverage do not match execution",
            )
        width = hooks.geometry(model)["head_dim"]
        axis_hashes = {}
        for cell in selected:
            site = tuple(cell["site"])
            digest = axis_identity(axes[cell["axis"]])
            _require(
                cell.get("axis_hash", digest) == digest,
                "axis hash differs from actual numeric axis",
            )
            axis_hashes[id(cell)] = digest
            projection = (
                hooks.o_proj_weight(model, site[1])[
                    :, site[2] * width : (site[2] + 1) * width
                ]
                .detach()
                .float()
                .cpu()
            )
            fitted = axes[cell["axis"]]["projection"]
            _require(
                fitted.device.type == "cpu" and torch.equal(fitted.float(), projection),
                "axis projection differs from actual named head",
            )
        cell_keys = [
            (tuple(c["site"]), c["seed"], c["family"], c["axis_index"], c["operation"])
            for c in selected
        ]
        _require(
            len(set(cell_keys)) == len(cell_keys), "duplicate directional raw row keys"
        )
        positive_refs = {
            id(c): [
                _positive_reference(c, batch, i, pid, identity, model)
                for i in range(len(batch.ids))
            ]
            for c in selected
        }
        for start in range(0, len(selected), tile):
            group = selected[start : start + tile]
            sites = sorted({tuple(c["site"]) for c in group})
            _require(
                all(s[0] == "head" for s in sites), "direction cells require head sites"
            )
            packed = _replicate(batch, tile)
            n = len(batch.ids)
            cap, base = _forward(model, packed, sites)
            stats = _scalar_stats(packed, cap, base)
            z = {s: cap.outputs[s].detach().cpu().clone() for s in sites}
            for i, rid in enumerate(batch.ids):
                cached = _entry(
                    capture_index, (pid, batch.task, batch.condition, batch.stream, rid)
                )
                _require(
                    cached["tokens"] == batch.input_ids[i].tolist()
                    and cached["attention_mask"] == batch.attention_mask[i].tolist()
                    and cached["readout"] == int(batch.readout[i])
                    and cached["record"] == batch.records[i],
                    "recipient cache source/geometry mismatch",
                )
                for label in ("opposite_token", "honest_token", "expected_token"):
                    _require(
                        cached[label] == int(getattr(batch, label)[i]),
                        "cached label mismatch",
                    )
                _require(
                    cached.get("choice_tokens")
                    == (
                        None
                        if batch.choice_tokens is None
                        else batch.choice_tokens[i].tolist()
                    ),
                    "cached choice label mismatch",
                )
                for s in sites:
                    _require(
                        torch.equal(_head(cached, s), z[s][i, int(batch.readout[i])]),
                        "recipient cache readout changed",
                    )
                _require(
                    abs(cached["stats"]["margin"] - float(stats["margin"][i])) <= 1e-5
                    and cached["stats"]["argmax"] == int(stats["argmax"][i]),
                    "cached intact score mismatch",
                )
            for lane in range(1, tile):
                _require(
                    torch.allclose(
                        stats["margin"][:n],
                        stats["margin"][lane * n : (lane + 1) * n],
                        atol=1e-5,
                        rtol=1e-5,
                    )
                    and torch.equal(
                        stats["argmax"][:n], stats["argmax"][lane * n : (lane + 1) * n]
                    ),
                    "packed intact lanes disagree",
                )
            mask = torch.zeros_like(
                packed.attention_mask, dtype=torch.bool, device="cpu"
            )
            mask[torch.arange(n * tile), packed.readout.cpu()] = True
            device, dtype = hooks.device_and_dtype(model)
            _require(
                str(dtype) == identity["numeric_profile"]["dtype"],
                "model dtype/profile mismatch",
            )
            # Keep only CPU captures and per-row statistics while subsequent forwards run.
            del cap, base
            replay_errors = {}
            for name in ("empty", "head_self", "zero_coefficient"):
                replacements = (
                    {}
                    if name == "empty"
                    else {
                        s: hooks.Replacement(
                            v.to(device=device, dtype=dtype), mask.to(device)
                        )
                        for s, v in z.items()
                    }
                )
                if name == "zero_coefficient":
                    # Exercise the actual reviewed direction path with donor == recipient.
                    replacements = {}
                    for s, v in z.items():
                        c = next(c for c in group if tuple(c["site"]) == s)
                        replay = direction_replacement(
                            v, v, axes[c["axis"]], mode="interchange", positions=mask
                        )
                        replacements[s] = hooks.Replacement(
                            replay.to(device=device, dtype=dtype), mask.to(device)
                        )
                rc, rl = _forward(model, packed, sites, replacements)
                rs = _scalar_stats(packed, rc, rl)
                error = float((stats["margin"] - rs["margin"]).abs().max())
                _require(
                    torch.allclose(stats["margin"], rs["margin"], atol=1e-5, rtol=1e-5)
                    and torch.equal(stats["argmax"], rs["argmax"]),
                    "assay invalid: same-shape replay failed",
                )
                replay_errors[name] = error
                del rc, rl, rs, replacements
            max_error = max(max_error, *replay_errors.values())
            replacements = {s: v.clone() for s, v in z.items()}
            diagnostics = []
            donor_maps = []
            for lane, c in enumerate(group):
                site = tuple(c["site"])
                direction = axes[c["axis"]]
                original = z[site][lane * n : (lane + 1) * n]
                donor = original.clone()
                maps = []
                for i in range(n):
                    if c["operation"] == "interchange":
                        value, mapping = _mapping(c, batch, i, capture_index, pid, site)
                        donor[i, int(batch.readout[i])] = value.to(donor.dtype)
                        maps.append(mapping)
                    else:
                        maps.append(None)
                mode = c["operation"]
                if mode == "zero":
                    donor.zero_()
                    mode = "interchange"
                if mode == "h_mean":
                    mode = "remove"
                patched = direction_replacement(
                    original, donor, direction, mode=mode, positions=batch.readout.cpu()
                )
                diagnostics.append(
                    perturbation_diagnostics(
                        original, patched, direction, positions=batch.readout.cpu()
                    )
                )
                replacements[site][lane * n : (lane + 1) * n] = patched
                donor_maps.append(maps)
            replacement_objects = {
                s: hooks.Replacement(v.to(device=device, dtype=dtype), mask.to(device))
                for s, v in replacements.items()
            }
            pc, pl = _forward(model, packed, sites, replacement_objects)
            patched_stats = _scalar_stats(packed, pc, pl)
            rows = []
            for lane, c in enumerate(group):
                for i, rid in enumerate(batch.ids):
                    j = lane * n + i
                    calibration = positive_refs[id(c)][i]
                    valid = bool(calibration and calibration.get("valid") is True)
                    row = dict(
                        panel=identity.get("panel"),
                        analysis_task=identity.get("analysis_task", batch.task),
                        source_task=batch.task,
                        split=identity.get("split"),
                        seed=c["seed"],
                        site=list(c["site"]),
                        family=c["family"],
                        axis_index=c["axis_index"],
                        operation=c["operation"],
                        instance_id=rid,
                        condition=batch.condition,
                        stream=batch.stream,
                        profile_id=pid,
                        numeric_profile=identity["numeric_profile"],
                        source_provenance=dict(batch.records[i]),
                        axis_hash=axis_hashes[id(c)],
                        opposite_token=int(batch.opposite_token[i]),
                        honest_token=int(batch.honest_token[i]),
                        expected_token=int(batch.expected_token[i]),
                        donor_mapping=donor_maps[lane][i],
                        head_norm=float(diagnostics[lane]["head_norm"][i]),
                        residual_norm=float(diagnostics[lane]["residual_norm"][i]),
                        fit_projected_variance=diagnostics[lane][
                            "fit_projected_variance"
                        ],
                        replay_errors=dict(replay_errors),
                        epsilon=max(1e-6, 10 * max_error),
                        replay_valid=True,
                        positive_control=calibration,
                        supported=True,
                        gate_valid=valid,
                        invalid_reason=None
                        if valid
                        else "missing/invalid separate all-sender positive calibration",
                    )
                    for k in stats:
                        row["intact_" + k] = stats[k][j].item()
                        row["patched_" + k] = patched_stats[k][j].item()
                    rows.append(row)
            del (
                pc,
                pl,
                patched_stats,
                z,
                replacements,
                replacement_objects,
                stats,
                packed,
            )
            sink(
                dict(
                    kind="a3_direction_rows",
                    identity=identity,
                    profile_id=pid,
                    rows=rows,
                )
            )
            count += len(rows)
            chunks += 1
    return dict(
        profile_id=pid,
        rows=count,
        chunks=chunks,
        max_replay_margin_error=max_error,
        epsilon=max(1e-6, 10 * max_error),
        epsilon_scope="caller must max across complete task/seed panel",
        complete=False,
    )


def capture_readouts(model, batches, *, sites, sink, identity):
    return _capture_readouts(model, batches, sites=sites, sink=sink, identity=identity)


def score_direction_cells(
    model, batches, *, cells, capture_index, axes, sink, identity
):
    return _score_direction_cells(
        model,
        batches,
        cells=cells,
        capture_index=capture_index,
        axes=axes,
        sink=sink,
        identity=identity,
    )


def measure_packing_equivalence(
    model, batches, *, cells, capture_index, axes, identity
):
    """Measure exact requested scope; no receipt authorizes another cohort/axis/map.

    Runs all requested nonzero patches serial and packed, then a one-axis final
    tile to exercise dummy lanes even when the main panel divides exactly.
    Captures and controls are ephemeral, and no scientific rows are published.
    """
    profile_identity(identity)
    _runtime(model, identity)
    batches = list(batches)
    tile = identity["numeric_profile"]["axis_tile_size"]
    _require(
        tile > 1 and batches and cells, "equivalence requires packed execution scope"
    )
    distinct = {axis_identity(axes[c["axis"]]) for c in cells}
    _require(len(distinct) >= 2, "equivalence requires distinct numeric axes")
    scope = dict(
        profile=dict(identity["numeric_profile"]),
        source_sha256=identity["numeric_profile"]["source_sha256"],
        batches={},
        recipients={},
        dummy_cells={},
    )
    for b in batches:
        chosen = [
            c
            for c in cells
            if all(
                c.get(k, getattr(b, k)) == getattr(b, k)
                for k in ("task", "condition", "stream")
            )
        ]
        bid = _digest([_recipient_digest(b, i) for i in range(len(b.ids))])
        _require(
            len(chosen) >= tile,
            "equivalence must exercise a complete physical axis tile",
        )
        if b.task != "mmlu":
            _require(
                any(c["operation"] == "interchange" for c in chosen),
                "equivalence requires actual mapped donor patches",
            )
        scope["batches"][bid] = [_cell_scope(b, c, axes, capture_index) for c in chosen]
        scope["recipients"][bid] = [
            dict(
                source_task=b.task,
                condition=b.condition,
                stream=b.stream,
                instance_id=rid,
            )
            for rid in b.ids
        ]
        first = cells[0]
        matches = all(
            first.get(k, getattr(b, k)) == getattr(b, k)
            for k in ("task", "condition", "stream")
        )
        scope["dummy_cells"][bid] = (
            [_cell_scope(b, first, axes, capture_index)] if matches else []
        )
    results = []
    measuring_cells = [
        {k: v for k, v in c.items() if k != "positive_controls"} for c in cells
    ]
    for lanes in (1, tile):
        ident = dict(identity, injected=True, diagnostic_only=True)
        ident.pop("packed_equivalence", None)
        ident["numeric_profile"] = dict(
            identity["numeric_profile"],
            axis_tile_size=lanes,
            physical_batch_size=identity["numeric_profile"]["physical_batch_size"]
            // tile
            * lanes,
        )
        local = {}

        def save(payload):
            for row in payload["rows"]:
                local[
                    (
                        payload["profile_id"],
                        row["task"],
                        row["condition"],
                        row["stream"],
                        row["instance_id"],
                    )
                ] = row

        sites = sorted({tuple(c["site"]) for c in cells})
        _capture_readouts(
            model, batches, sites=sites, sink=save, identity=ident, measuring=True
        )

        def lookup(key):
            if key in local:
                return local[key]
            return capture_index(key) if callable(capture_index) else capture_index[key]

        chunks = []
        _score_direction_cells(
            model,
            batches,
            cells=measuring_cells,
            capture_index=lookup,
            axes=axes,
            sink=chunks.append,
            identity=ident,
            measuring=True,
        )
        # Dedicated final one-axis tile, with remaining lanes untouched.
        dummy = []
        _score_direction_cells(
            model,
            batches,
            cells=measuring_cells[:1],
            capture_index=lookup,
            axes=axes,
            sink=dummy.append,
            identity=ident,
            measuring=True,
        )
        results.append([r for chunk in chunks + dummy for r in chunk["rows"]])
    _require(
        len(results[0]) == len(results[1]) and results[0],
        "equivalence row coverage mismatch",
    )
    comparisons = []
    nonzero = 0
    keyfields = (
        "source_task",
        "condition",
        "stream",
        "instance_id",
        "seed",
        "site",
        "family",
        "axis_index",
        "operation",
    )
    fields = (
        "intact_margin",
        "patched_margin",
        "intact_argmax",
        "patched_argmax",
        "replay_errors",
        "axis_hash",
        "head_norm",
    )
    for serial, packed in zip(*results):
        _require(
            all(serial[k] == packed[k] for k in keyfields),
            "equivalence row order mismatch",
        )
        nonzero += int(serial["head_norm"] > 0 and packed["head_norm"] > 0)
        comparisons.append(
            dict(
                key={k: serial[k] for k in keyfields},
                serial={k: serial[k] for k in fields},
                packed={k: packed[k] for k in fields},
            )
        )
    receipt = dict(
        kind="measured_direction_packing_v2",
        valid=True,
        scope=scope,
        scope_sha256=_digest(scope),
        comparisons=comparisons,
        dummy_lanes_tested=True,
        distinct_axes=len(distinct),
        nonzero_patches=nonzero,
    )
    receipt["receipt_sha256"] = _digest(receipt)
    checked = dict(identity, packed_equivalence=receipt)
    for b in batches:
        _packing_receipt(checked, b)
    return receipt


def direction_point_metrics(rows, *, seed, require_mmlu=True):
    """Single-site/axis validation estimator, without inventing other seeds.

    Rows must be one exact site/family/axis/analysis-task/split/seed. Primary
    interchange supplies mechanisms and IOI; MMLU supplies zero and h_mean.
    Both designation streams are mandatory for every mechanism condition.
    """
    _require(
        type(seed) is int and rows and all(r.get("seed") == seed for r in rows),
        "one seed required",
    )
    dimensions = ("site", "family", "axis_index", "analysis_task", "split", "panel")
    for k in dimensions:
        _require(
            len({json.dumps(r.get(k), sort_keys=True) for r in rows}) == 1,
            "mixed point-metric " + k,
        )
    by = {}
    for r in rows:
        key = (
            r["source_task"],
            r["condition"],
            r["operation"],
            r["instance_id"],
            r["stream"],
        )
        _require(key not in by, "duplicate point-metric row")
        _require(
            all(
                math.isfinite(float(r[k]))
                for k in ("intact_margin", "patched_margin", "epsilon")
            ),
            "nonfinite point outcome",
        )
        _require(
            r["epsilon"] >= 1e-6
            and all(
                r[k] in (True, False, 0, 1)
                for k in ("intact_correct", "patched_correct")
            ),
            "invalid point correctness/epsilon",
        )
        by[key] = r
    _require(
        all(
            r["source_task"] not in ("ioi", "mmlu")
            or r["operation"]
            in ({"interchange"} if r["source_task"] == "ioi" else {"zero", "h_mean"})
            for r in rows
        ),
        "unexpected utility operation",
    )
    mechanism = [r for r in rows if r["source_task"] not in ("ioi", "mmlu")]
    _require(
        len({r["source_task"] for r in mechanism}) == 1, "mixed source mechanism tasks"
    )
    _require(
        mechanism and all(r["operation"] == "interchange" for r in mechanism),
        "primary mechanism interchange required",
    )
    conditions = ("D", "I", "H", "user_neutral", "F")
    _require(
        {r["condition"] for r in mechanism} == set(conditions),
        "missing mechanism condition",
    )
    ids = sorted({r["instance_id"] for r in mechanism})
    paired = {}
    for c in conditions:
        subset = {
            (r["instance_id"], r["stream"]): r for r in mechanism if r["condition"] == c
        }
        _require(
            set(subset) == {(i, s) for i in ids for s in ("clean", "corrupt")},
            "missing paired mechanism stream/id",
        )
        paired[c] = [[subset[(i, s)] for s in ("clean", "corrupt")] for i in ids]
    epsilon = max(r["epsilon"] for r in rows)

    def mean(c, k):
        return np.asarray([[r[k] for r in pair] for pair in paired[c]], dtype=float)

    fractions = {}
    gaps = {}
    stream_gaps = {}
    drops = {}
    denominator_valid = True
    for c, neutral in (("D", "H"), ("I", "user_neutral")):
        sg = (mean(c, "intact_margin") - mean(neutral, "intact_margin")).mean(0)
        ok = bool(np.isfinite(sg).all() and (sg > epsilon).all())
        denominator_valid &= ok
        gap = float(sg.mean())
        drop = float((mean(c, "intact_margin") - mean(c, "patched_margin")).mean())
        stream_gaps[c] = sg.tolist()
        gaps[c] = gap
        drops[c] = drop
        fractions[c] = drop / gap if ok else float("nan")
    shifts = {
        c: float((mean(c, "patched_correct") - mean(c, "intact_correct")).mean())
        for c in conditions
    }
    utility_ids = {}
    mmlu_errors = {}
    for task, operation, name in (
        ("ioi", "interchange", "IOI"),
        ("mmlu", "zero", "MMLU_zero"),
        ("mmlu", "h_mean", "MMLU_h_mean"),
    ):
        selected = [
            r for r in rows if r["source_task"] == task and r["operation"] == operation
        ]
        if not selected:
            continue
        _require(
            all(r["stream"] == "clean" for r in selected)
            and len({r["instance_id"] for r in selected}) == len(selected),
            "utility IDs/streams must be unique",
        )
        utility_ids[name] = sorted(r["instance_id"] for r in selected)
        shifts[name] = float(
            np.mean([r["patched_correct"] - r["intact_correct"] for r in selected])
        )
        if task == "mmlu":
            _require(len(selected) == 32, "MMLU requires 32 frozen prompts")
            mmlu_errors[name] = -32 * shifts[name]
    mmlu_complete = set(mmlu_errors) == {"MMLU_zero", "MMLU_h_mean"}
    if mmlu_complete:
        _require(
            utility_ids["MMLU_zero"] == utility_ids["MMLU_h_mean"],
            "MMLU floor memberships differ",
        )
        floors = {
            op: {
                r["instance_id"]: r["intact_correct"]
                for r in rows
                if r["source_task"] == "mmlu" and r["operation"] == op
            }
            for op in ("zero", "h_mean")
        }
        _require(
            floors["zero"] == floors["h_mean"],
            "MMLU floors require common intact outcomes",
        )
    coverage = all(r.get("gate_valid") is True for r in rows)
    passed = (
        denominator_valid
        and coverage
        and fractions["D"] >= 0.5
        and fractions["I"] < 0.25
        and all(
            k in shifts and abs(shifts[k]) < 0.05 - 1e-12 for k in ("H", "F", "IOI")
        )
        and (mmlu_complete or not require_mmlu)
        and all(x <= 1 for x in mmlu_errors.values())
    )
    return dict(
        seed=seed,
        point_pass=bool(passed),
        denominator_valid=denominator_valid,
        gate_valid=coverage,
        D_fraction=fractions["D"],
        I_fraction=fractions["I"],
        contrast=fractions["D"] - fractions["I"],
        gaps=gaps,
        stream_gaps=stream_gaps,
        drops=drops,
        collateral_shifts=shifts,
        MMLU_additional_errors=mmlu_errors,
        mmlu_complete=mmlu_complete,
        epsilon=epsilon,
    )
