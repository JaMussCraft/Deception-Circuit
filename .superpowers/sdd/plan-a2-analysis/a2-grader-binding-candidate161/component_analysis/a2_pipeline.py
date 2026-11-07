"""Separate immutable A2 groups/banks around the unchanged frozen A1 assay.

CPU freeze and dry-run never load model weights. GPU stages require independent
orchestrator cost admission; this module never submits jobs or reserves budget.
Native training metrics are retained as limitations, never efficacy filters.
"""

from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace

from component_analysis import a2_mask_comparison as comparison
from component_analysis import ladder_pipeline as a1

TASKS = comparison.TASKS
SEEDS = comparison.SEEDS
require = a1.require
hash_content = a1.design._hash
GROUP_SOURCE = "matched_pressure_twin"
PRIMARY_OPERATIONS = ("item_swap", "zero", "h_mean", "h_twin", "self_replay", "empty")


def publish_artifact(path, payload):
    """Publish complete bytes atomically with no replacement, including races."""
    path = Path(path)
    require(not path.exists(), "output exists: " + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name, dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(
                dict(sha256=hash_content(payload), payload=payload),
                handle,
                sort_keys=True,
                allow_nan=False,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise ValueError("output exists: " + str(path)) from exc
    finally:
        os.unlink(temporary)


def _a1_args(prepared, groups):
    # A1's ancestor commit is distinct from the future A2 execution commit.
    return SimpleNamespace(
        **{
            k: prepared[k]
            for k in (
                "commit",
                "model",
                "model_revision",
                "tokenizer_revision",
                "tasks",
            )
        },
        groups=str(groups),
        registry=[],
    )


def _members(value):
    members = value["members"]
    require(isinstance(members, list), "invalid typed membership")
    keys = []
    for key in members:
        require(
            isinstance(key, list)
            and len(key) == 3
            and key[0] in ("head", "mlp")
            and type(key[1]) is int
            and 0 <= key[1] < 32
            and type(key[2]) is int
            and (0 <= key[2] < 32 if key[0] == "head" else key[2] == 0),
            "invalid typed component",
        )
        keys.append(tuple(key))
    require(keys == sorted(set(keys)), "unsorted/duplicate membership")
    require(
        value.get("membership_sha256") == comparison.digest(members),
        "membership hash mismatch",
    )
    return set(keys)


def validate_comparison(comp):
    require(
        comp.get("schema") == "a2-mask-comparison/1"
        and comp.get("status") == "complete_cpu_audit",
        "complete comparison audit required",
    )
    require(
        comp.get("comparison_sha256")
        == comparison.digest(
            {k: v for k, v in comp.items() if k != "comparison_sha256"}
        ),
        "comparison hash mismatch",
    )
    sources = comp.get("sources", [])
    require(len(sources) == 18, "all18 sources required")
    indexed = {(s["task"], s["condition"], s["seed"]): s for s in sources}
    require(
        len(indexed) == 18
        and set(indexed) == set(itertools.product(TASKS, ("D", "I"), SEEDS)),
        "incomplete/duplicate source domain",
    )
    require(set(comp["tasks"]) == set(TASKS), "comparison task domain")
    for task in TASKS:
        require(
            set(comp["tasks"][task]["seeds"]) == set(map(str, SEEDS)),
            "comparison seed domain",
        )
        for seed in SEEDS:
            d = _members(indexed[task, "D", seed]["members"])
            i = _members(indexed[task, "I", seed]["members"])
            values = dict(D=d, I=i, X=d - i, Y=i - d, B=d & i, U=d | i)
            for name, keys in values.items():
                require(
                    _members(comp["tasks"][task]["seeds"][str(seed)][name]) == keys,
                    "source/group algebra drift",
                )


def freeze_a2_groups(comp, prepared, a1_selected, selection_receipt):
    """Freeze all nine aliases before assessment; never manufacture an A1 selection."""
    validate_comparison(comp)
    require(prepared["tasks"] == list(TASKS), "A2 requires all three frozen tasks")
    path = selection_receipt["selection_artifact"]
    selected = a1.read_selection(_a1_args(prepared, path), prepared)
    require(
        hash_content(selected) == hash_content(a1_selected), "selection payload drift"
    )
    require(
        a1.common.read_json(a1.selection_manifest_path(path)) == selection_receipt,
        "selection sidecar drift",
    )
    groups = {}
    compute = {}
    bank_keys = {}
    for task in TASKS:
        union = set()
        for seed in SEEDS:
            frozen = comp["tasks"][task]["seeds"][str(seed)]["X"]
            name = f"{task}_seed{seed}_DminusI"
            group = dict(
                task=task,
                training_seed=seed,
                members=copy.deepcopy(frozen["members"]),
                membership_sha256=frozen["membership_sha256"],
                source_kind="twin_trained_mask_difference",
                group_source=GROUP_SOURCE,
                granularity="heads-mlp",
                descriptive=False,
                empty=not frozen["members"],
                source_indices=[
                    next(
                        j
                        for j, s in enumerate(comp["sources"])
                        if (s["task"], s["condition"], s["seed"]) == (task, c, seed)
                    )
                    for c in ("D", "I")
                ],
            )
            groups[name] = group
            union.update(map(tuple, group["members"]))
            compute.setdefault(task + ":" + group["membership_sha256"], []).append(name)
        bank_keys[task] = [list(k) for k in sorted(union)]
    result = dict(
        schema="a2-ladder-groups/1",
        group_source=GROUP_SOURCE,
        source_kind="twin_trained_mask_difference",
        groups=groups,
        compute_groups=compute,
        bank_keys=bank_keys,
        tasks=list(TASKS),
        comparison=copy.deepcopy(comp),
        comparison_sha256=comp["comparison_sha256"],
        a1_design_sha256=hash_content(prepared),
        a1_selected_sha256=hash_content(selected),
        selection_receipt=copy.deepcopy(selection_receipt),
        selection_sidecar_sha256=a1.common.file_hash(a1.selection_manifest_path(path)),
        assessment=copy.deepcopy(
            dict(designs=prepared["designs"], utility=prepared["utility"])
        ),
        model_geometry=model_geometry_receipt(prepared),
        model_identity={
            k: prepared[k]
            for k in (
                "model",
                "model_revision",
                "tokenizer_revision",
                "dtype",
                "readout",
            )
        },
        a1_ancestor_commit=prepared["commit"],
        a2_training_execution_commit=comparison.EXECUTION_COMMIT,
        operations=list(PRIMARY_OPERATIONS),
        independent_donor_seeds=[],
        injected=bool(prepared.get("injected") or selected.get("injected")),
        limitations=[
            "Original selection is assessment/exclusion ancestry, not selection evidence for A2 groups.",
            "Native training test metrics are not frozen ladder assessment100 results; no efficacy acceptance filter.",
            "Head containment and mixed specificity are distinct and may coexist.",
        ],
    )
    result["receipt_sha256"] = hash_content(result)
    return result


def validate_receipt(receipt, prepared=None):
    require(
        receipt.get("schema") == "a2-ladder-groups/1"
        and receipt.get("group_source") == GROUP_SOURCE,
        "invalid A2 group receipt",
    )
    require(
        receipt.get("receipt_sha256")
        == hash_content({k: v for k, v in receipt.items() if k != "receipt_sha256"}),
        "A2 receipt hash mismatch",
    )
    validate_comparison(receipt["comparison"])
    require(receipt["tasks"] == list(TASKS), "A2 frozen task scope drift")
    optional = receipt.get("independent_donor_seeds")
    require(optional in ([], [101, 102, 103]), "independent donor seed drift")
    require(
        receipt["operations"]
        == list(PRIMARY_OPERATIONS) + (["independent_resample"] if optional else []),
        "required crossed operation drift",
    )
    names = {f"{task}_seed{seed}_DminusI" for task in TASKS for seed in SEEDS}
    require(set(receipt["groups"]) == names, "all nine seed groups required")
    aliases = {}
    union = {task: set() for task in TASKS}
    for task in TASKS:
        for seed in SEEDS:
            name = f"{task}_seed{seed}_DminusI"
            group = receipt["groups"][name]
            x = receipt["comparison"]["tasks"][task]["seeds"][str(seed)]["X"]
            require(
                _members(group) == _members(x)
                and group["task"] == task
                and group["training_seed"] == seed,
                "frozen seed membership drift",
            )
            require(
                group.get("source_kind") == "twin_trained_mask_difference"
                and group.get("group_source") == GROUP_SOURCE
                and group.get("granularity") == "heads-mlp"
                and group.get("descriptive") is False,
                "A2 group source qualifier drift",
            )
            union[task].update(map(tuple, group["members"]))
            aliases.setdefault(task + ":" + group["membership_sha256"], []).append(name)
    require(receipt["compute_groups"] == aliases, "compute aliases lost or reordered")
    require(
        receipt["bank_keys"]
        == {t: [list(k) for k in sorted(v)] for t, v in union.items()},
        "union bank key drift",
    )
    if prepared is not None:
        selected = a1.read_selection(
            _a1_args(prepared, receipt["selection_receipt"]["selection_artifact"]),
            prepared,
        )
        fresh = freeze_a2_groups(
            receipt["comparison"], prepared, selected, receipt["selection_receipt"]
        )
        for key in (
            "groups",
            "compute_groups",
            "bank_keys",
            "assessment",
            "a1_design_sha256",
            "a1_selected_sha256",
            "selection_sidecar_sha256",
            "model_identity",
            "model_geometry",
            "a1_ancestor_commit",
        ):
            require(
                hash_content(receipt[key]) == hash_content(fresh[key]),
                "stale A2 " + key,
            )


def expected_keys(receipt, limit=0):
    expected = []
    for name in (f"{task}_seed{seed}_DminusI" for task in TASKS for seed in SEEDS):
        group = receipt["groups"][name]
        task = group["task"]
        frozen = receipt["assessment"]["designs"][task]
        for rid in frozen["assessment_ids"][: limit or None]:
            for c in a1.design.CONDITIONS:
                for stream in a1.design.STREAMS:
                    for op in receipt["operations"]:
                        for seed in (
                            receipt["independent_donor_seeds"]
                            if op == "independent_resample"
                            else (None,)
                        ):
                            expected.append((task, rid, c, stream, name, op, seed))
        for utility, ops in [
            ("ioi", ("item_swap", "zero", "h_mean", "self_replay", "empty")),
            ("mmlu", ("zero", "h_mean", "self_replay", "empty")),
        ]:
            for r in receipt["assessment"]["utility"][utility][: limit or None]:
                for op in ops:
                    expected.append(
                        (
                            utility,
                            r["instance_id"],
                            r["condition"],
                            "clean",
                            name,
                            op,
                            None,
                        )
                    )
    return expected


def validate_a2_scope(receipt, rows, *, limit=0, banks=None, bank_path=None):
    validate_receipt(receipt)
    a1.validate_rows(rows, expected_keys(receipt, limit))
    references = (
        {task: bank_reference(banks, bank_path, task) for task in TASKS}
        if banks is not None
        else {}
    )
    for row in rows:
        group = receipt["groups"][row["group"]]
        require(
            row.get("group_members") == group["members"]
            and row.get("a2_group_sha256") == group["membership_sha256"],
            "row seed membership mismatch",
        )
        require(
            row.get("group_source") == GROUP_SOURCE
            and row.get("a2_receipt_sha256") == receipt["receipt_sha256"],
            "row A2 source receipt mismatch",
        )
        if (
            banks is not None
            and row["operation"] == "h_mean"
            and row.get("supported", True)
        ):
            expected = references[group["task"]]
            require(
                row.get("mean_bank_provenance") == expected,
                "stale/foreign A2 bank row reference",
            )


def _prepared_domain(receipt):
    return dict(tasks=receipt["tasks"], **receipt["assessment"])


def validate_finalization(receipt, scored, *, final):
    a1.validate_finalization(scored, final=final)
    if final:
        require(not receipt.get("injected"), "injected groups cannot finalize")
        require(
            all(
                len(f["assessment_ids"]) == 100
                for f in receipt["assessment"]["designs"].values()
            ),
            "final requires exact frozen assessment100",
        )
        require(
            len(receipt["assessment"]["utility"]["ioi"]) == 100
            and len(receipt["assessment"]["utility"]["mmlu"]) == 32,
            "final requires IOI100/MMLU32",
        )


def aggregate_tasks(receipt, summary):
    """No seed averaging/selection: all three primary rules and floors must pass."""
    cells = {}
    for cell in summary["cells"]:
        if cell["operation"] == "item_swap":
            require(cell["group"] not in cells, "duplicate primary group summary")
            require(cell["group"] in receipt["groups"], "unknown primary group summary")
            cells[cell["group"]] = cell
    tasks = {}
    for task in TASKS:
        detail = receipt["comparison"]["tasks"][task]
        per_seed = {}
        for seed in SEEDS:
            name = f"{task}_seed{seed}_DminusI"
            cell = cells.get(name)
            numerical = bool(cell and cell.get("point_pass"))
            complete = bool(cell and cell.get("complete_assay_ready"))
            floors = bool(
                cell and cell.get("assay_readiness", {}).get("MMLU", {}).get("passed")
            )
            nonempty = bool(receipt["groups"][name]["members"])
            supported = bool(
                cell and not cell.get("coverage", {}).get("unsupported", 0)
            )
            interpretable = bool(cell and cell.get("interpretable", numerical))
            empty_failure = bool(
                not nonempty
                and supported
                and interpretable
                and cell.get("empty_group_required_evidence_complete") is True
                and cell.get("D", {}).get("fraction_removed") is not None
                and cell["D"]["fraction_removed"] < 0.5
            )
            assessed = bool(supported and interpretable and (complete or empty_failure))
            assessment_status = (
                "incomplete"
                if cell is None
                else "blocked_uninterpretable"
                if not supported or not interpretable
                else "failed_necessity_empty_group"
                if empty_failure
                else "assessed"
                if complete
                else "blocked_uninterpretable"
            )
            passed = numerical and complete and floors and nonempty and supported
            per_seed[str(seed)] = dict(
                group=name,
                primary_cell=cell,
                primary_point_pass=numerical,
                component_counts=copy.deepcopy(
                    detail["seeds"][str(seed)]["X"]["counts"]
                ),
                head_containment=copy.deepcopy(
                    detail["seeds"][str(seed)]["containment"]["head"]
                ),
                empty_group_required_evidence_complete=bool(
                    cell and cell.get("empty_group_required_evidence_complete")
                ),
                complete_assay_ready=complete,
                both_mmlu_floors_pass=floors,
                nonempty=nonempty,
                specificity_pass=passed,
                strong=bool(passed and cell.get("strong")),
                scientific_assay_ready=complete and supported and interpretable,
                specificity_assessment_complete=assessed,
                assessment_status=assessment_status,
                status="incomplete" if cell is None else cell.get("status"),
            )
        pairs = detail["pairwise"]["mixed"]
        stable = len(pairs) == 3 and all(
            p["ratio"] is not None and p["ratio"] >= 0.5 for p in pairs
        )
        robust = stable and all(v["specificity_pass"] for v in per_seed.values())
        containment = [
            detail["seeds"][str(seed)]["containment"]["head"]["ratio"] for seed in SEEDS
        ]
        ranges = {}
        for condition in ("D", "I"):
            values = [
                v["primary_cell"].get(condition, {}).get("fraction_removed")
                for v in per_seed.values()
                if v["primary_cell"]
            ]
            valid = [x for x in values if x is not None]
            ranges[condition + "_fraction_removed"] = (
                [min(valid), max(valid)] if len(valid) == 3 else None
            )
        tasks[task] = dict(
            per_seed=per_seed,
            seed_ranges=ranges,
            mixed_pairwise_jaccards=copy.deepcopy(pairs),
            mixed_stability_pass=stable,
            complete_primary_coverage=all(
                v["primary_cell"] is not None for v in per_seed.values()
            ),
            robust_task_pass=robust,
            strong=bool(robust and all(v["strong"] for v in per_seed.values())),
            specificity_assessment_complete=all(
                v["specificity_assessment_complete"] for v in per_seed.values()
            ),
            informative_head_containment=all(
                c is not None and c >= 0.9 for c in containment
            ),
            mlp_prediction=copy.deepcopy(detail.get("mlp_prediction", [])),
            native_training_metric_scope="training_test_cohort_not_assessment100",
        )
    return dict(
        tasks=tasks,
        summary=summary,
        limitations=receipt["limitations"],
        membership_comparison=copy.deepcopy(receipt["comparison"]["tasks"]),
        native_training_metrics=[
            dict(
                task=s["task"],
                condition=s["condition"],
                seed=s["seed"],
                scope="native_training_test_cohort_not_ladder_assessment100",
                native_results=copy.deepcopy(s["native_results"]),
            )
            for s in receipt["comparison"]["sources"]
        ],
        collection_complete=all(t["complete_primary_coverage"] for t in tasks.values()),
        scientific_assay_ready=all(
            v["scientific_assay_ready"]
            for t in tasks.values()
            for v in t["per_seed"].values()
        ),
        seed_interpretation="Three trained seeds share frozen assessment IDs; never independent extra observations.",
    )


def numeric_environment():
    """Bind bank arithmetic to library/backend settings, not only dtype labels."""
    import importlib.metadata
    import sys
    import torch

    versions = {
        name: importlib.metadata.version(name)
        for name in ("torch", "transformers", "nnsight", "numpy")
    }
    versions.update(
        python=list(sys.version_info[:3]),
        cuda_runtime=torch.version.cuda,
        matmul_precision=torch.get_float32_matmul_precision(),
        cpu_threads=torch.get_num_threads(),
        cuda_matmul_allow_tf32=bool(torch.backends.cuda.matmul.allow_tf32),
        cudnn_allow_tf32=bool(torch.backends.cudnn.allow_tf32),
        deterministic_algorithms=bool(torch.are_deterministic_algorithms_enabled()),
    )
    return versions


def model_geometry_receipt(prepared):
    """Read pinned model metadata only; no weights or inferred bank dimensions."""
    if prepared.get("injected"):
        config = prepared.get("injected_model_config")
        require(
            isinstance(config, dict), "injected fixture requires model configuration"
        )
        reference = dict(injected=True, config_sha256=hash_content(config))
    else:
        from huggingface_hub import hf_hub_download

        path = Path(
            hf_hub_download(
                prepared["model"],
                "config.json",
                revision=prepared["model_revision"],
                local_files_only=True,
            )
        )
        require(
            path.parent.name == prepared["model_revision"],
            "model config revision mismatch",
        )
        config = a1.common.read_json(path)
        reference = dict(
            injected=False,
            path=str(path.resolve()),
            file_sha256=a1.common.file_hash(path),
            config_sha256=hash_content(config),
            model=prepared["model"],
            model_revision=prepared["model_revision"],
        )
    require(config.get("model_type") == "llama", "unsupported bank model architecture")
    geometry = {
        name: config.get(field)
        for name, field in (
            ("hidden_size", "hidden_size"),
            ("num_heads", "num_attention_heads"),
            ("num_layers", "num_hidden_layers"),
        )
    }
    require(
        all(type(value) is int and value > 0 for value in geometry.values()),
        "invalid model geometry",
    )
    require(
        geometry["hidden_size"] % geometry["num_heads"] == 0,
        "inconsistent model head geometry",
    )
    head_dim = (
        config.get("head_dim") or geometry["hidden_size"] // geometry["num_heads"]
    )
    require(type(head_dim) is int and head_dim > 0, "invalid model head dimension")
    geometry["head_dim"] = head_dim
    return dict(geometry=geometry, source=reference)


def _model_geometry(receipt, prepared):
    frozen = receipt["model_geometry"]
    require(
        frozen == model_geometry_receipt(prepared), "stale frozen model geometry/config"
    )
    return frozen["geometry"]


def _validate_loaded_geometry(receipt, model):
    from component_analysis import hooks

    actual = hooks.geometry(model)
    require(
        all(
            actual.get(k) == value
            for k, value in receipt["model_geometry"]["geometry"].items()
        ),
        "loaded model differs from frozen bank geometry",
    )


def bank_contract(receipt, prepared, task):
    """Exact original-H IDs, source bytes/tokens, pooling and model path."""
    geometry = _model_geometry(receipt, prepared)
    required_shapes = []
    for key in receipt["bank_keys"][task]:
        kind, layer, head = key
        require(
            0 <= layer < geometry["num_layers"]
            and (kind == "mlp" or 0 <= head < geometry["num_heads"]),
            "bank key outside frozen model geometry",
        )
        required_shapes.append(
            dict(
                key=key,
                shape=[
                    geometry["head_dim"] if kind == "head" else geometry["hidden_size"]
                ],
            )
        )
    ids = receipt["assessment"]["designs"][task]["bank_ids"]
    require(ids and len(set(ids)) == len(ids), "empty/duplicate frozen H bank IDs")
    lookup = {r["instance_id"]: r for r in prepared["rows"][task]["H"]}
    require(len(lookup) == len(prepared["rows"][task]["H"]), "duplicate original H row")
    require(set(ids) <= set(lookup), "missing frozen original H bank IDs")
    rows = [lookup[rid] for rid in ids]
    require(
        all(
            r.get("condition") == "H"
            and r.get("source_condition") == "H"
            and r.get("split") in ("train", "validation")
            and r.get("source_hash")
            for r in rows
        ),
        "bank requires original H train+validation",
    )
    require(
        not set(ids) & set(receipt["assessment"]["designs"][task]["assessment_ids"]),
        "assessment in H bank",
    )
    counts = {
        s: sum(len(r["streams"][s]["tokens"]) for r in rows) for s in a1.design.STREAMS
    }
    return dict(
        task=task,
        source_condition="H",
        source_ids=sorted(ids),
        source_id_order=list(ids),
        splits=sorted({r["split"] for r in rows}),
        source_rows_sha256=hash_content(rows),
        stream_token_counts=counts,
        n_tokens=sum(counts.values()),
        n_instances=len(ids),
        numeric_environment=numeric_environment(),
        pooling="both streams; all unpadded tokens; equal token weight; fp32 accumulation",
        model_identity=copy.deepcopy(receipt["model_identity"]),
        tokenizer_identity=prepared.get("tokenizer_identity"),
        tokenization_sha256=hash_content(
            [[r["instance_id"], r["streams"]] for r in rows]
        ),
        source_hashes=copy.deepcopy(prepared["source_hashes"]),
        code_hashes=runtime_hashes(),
        required_keys=copy.deepcopy(receipt["bank_keys"][task]),
        required_shapes=required_shapes,
        model_geometry=copy.deepcopy(receipt["model_geometry"]),
    )


def runtime_hashes():
    result = a1.code_hashes()
    for name in (
        "component_analysis/a2_pipeline.py",
        "component_analysis/a2_mask_comparison.py",
    ):
        result[name] = a1.common.file_hash(a1.REPO / name)
    return result


def collect_banks(args, receipt, prepared, model):
    """Recollect the full union; old partial A1 banks are never relabeled/reused."""
    from component_analysis import specificity_ladder as runner

    _model_geometry(receipt, prepared)
    _validate_loaded_geometry(receipt, model)
    state = a1.start_execution(model)
    banks = {}
    for task in TASKS:
        contract = bank_contract(receipt, prepared, task)
        ids = set(contract["source_ids"])
        rows = [r for r in prepared["rows"][task]["H"] if r["instance_id"] in ids]
        batches = [
            b
            for s in a1.design.STREAMS
            for b in a1.batches(rows, s, batch_size=args.batch_size)
        ]
        bank = runner.collect_h_mean_bank(
            model, batches, [tuple(k) for k in receipt["bank_keys"][task]]
        )
        values = [
            dict(key=list(k), value=v.detach().cpu().float().tolist())
            for k, v in sorted(bank["values"].items())
        ]
        banks[task] = dict(
            values=values, provenance=bank["provenance"], contract=contract
        )
    payload = dict(
        kind="a2_h_banks",
        owner="a2_original_H_union",
        receipt_sha256=receipt["receipt_sha256"],
        banks=banks,
        execution_provenance=a1.finish_execution(state, "bank"),
        injected=bool(args.injected or receipt["injected"]),
    )
    validate_banks(receipt, prepared, payload)
    return payload


def validate_banks(receipt, prepared, payload):
    import math

    require(
        payload.get("kind") == "a2_h_banks"
        and payload.get("receipt_sha256") == receipt["receipt_sha256"],
        "wrong bank artifact/receipt",
    )
    require(set(payload["banks"]) == set(TASKS), "incomplete bank task scope")
    for task, bank in payload["banks"].items():
        expected = bank_contract(receipt, prepared, task)
        require(
            bank.get("contract") == expected,
            "stale bank source/identity/tokenization contract",
        )
        keys = [tuple(v["key"]) for v in bank["values"]]
        require(
            keys == sorted(set(keys))
            and keys == [tuple(k) for k in receipt["bank_keys"][task]],
            "bank missing/foreign/duplicate keys",
        )
        require(
            all(
                isinstance(v["value"], list)
                and len(v["value"]) == shape["shape"][0]
                and all(
                    type(x) in (int, float) and math.isfinite(x) for x in v["value"]
                )
                for v, shape in zip(bank["values"], expected["required_shapes"])
            ),
            "nonfinite/malformed bank vectors or wrong typed shape",
        )
        p = bank["provenance"]
        require(
            p.get("source_condition") == "H"
            and p.get("source_ids") == expected["source_ids"]
            and p.get("splits") == expected["splits"]
            and p.get("n_tokens") == expected["n_tokens"]
            and p.get("provenance"),
            "bank provenance domain/count mismatch",
        )


def bank_reference(payload, path, task):
    require(path is not None and Path(path).is_file(), "bank file reference required")
    require(
        hash_content(a1.read_artifact(path)) == hash_content(payload),
        "bank artifact file/content mismatch",
    )
    return dict(
        owner="a2_original_H_union",
        task=task,
        artifact_reference=str(Path(path).resolve()),
        bank_file_sha256=a1.common.file_hash(path),
        bank_artifact_sha256=hash_content(payload),
        bank_sha256=hash_content(payload["banks"][task]),
        contract_sha256=hash_content(payload["banks"][task]["contract"]),
    )


def _groups_for_compute(receipt, task):
    groups = []
    aliases = {}
    seen = set()
    for seed in SEEDS:
        name = f"{task}_seed{seed}_DminusI"
        group = receipt["groups"][name]
        key = task + ":" + group["membership_sha256"]
        if key in seen:
            continue
        seen.add(key)
        names = receipt["compute_groups"][key]
        first = names[0]
        groups.append((first, receipt["groups"][first]["members"]))
        aliases[first] = names
    return groups, aliases


def score(args, receipt, prepared, banks, bank_path, model):
    """Run canonical crossed interventions, preserving aliases and controls."""
    import torch
    from component_analysis import specificity_ladder as runner
    from component_analysis.ladder_tasks import task_batches

    validate_receipt(receipt, prepared)
    validate_banks(receipt, prepared, banks)
    _validate_loaded_geometry(receipt, model)
    state = a1.start_execution(model)
    bank_execution = banks["execution_provenance"]
    require(
        str(state["dtype"]) == bank_execution["dtype"]
        and str(state["device"]).split(":")[0]
        == bank_execution["device"].split(":")[0],
        "bank/scoring numerical path mismatch",
    )
    current_gpu = (
        torch.cuda.get_device_name(state["cuda_device"])
        if state["cuda_device"] is not None
        else None
    )
    require(
        current_gpu == bank_execution.get("gpu_name"),
        "bank/scoring GPU architecture mismatch",
    )
    rows = []
    controls = []
    references = {task: bank_reference(banks, bank_path, task) for task in TASKS}

    def append(output, aliases):
        for source in output:
            for name in aliases[source["group"]]:
                group = receipt["groups"][name]
                row = dict(
                    source,
                    group=name,
                    group_members=copy.deepcopy(group["members"]),
                    group_source=GROUP_SOURCE,
                    a2_group_sha256=group["membership_sha256"],
                    a2_receipt_sha256=receipt["receipt_sha256"],
                    training_seed=group["training_seed"],
                    compute_alias=source["group"],
                )
                if row["operation"] == "h_mean" and "mean_bank_provenance" in row:
                    require(
                        hash_content(row["mean_bank_provenance"])
                        == hash_content(banks["banks"][group["task"]]["provenance"]),
                        "runner bank provenance mismatch",
                    )
                    row["mean_bank_provenance"] = copy.deepcopy(
                        references[group["task"]]
                    )
                rows.append(row)

    for task in TASKS:
        frozen = prepared["designs"][task]
        ids = frozen["assessment_ids"][: args.limit or None]
        source = prepared["rows"][task]
        groups, aliases = _groups_for_compute(receipt, task)
        raw = banks["banks"][task]
        bank = dict(
            values={
                tuple(v["key"]): torch.tensor(v["value"], dtype=torch.float32)
                for v in raw["values"]
            },
            provenance=raw["provenance"],
        )
        recipients = [
            b
            for c in a1.design.CONDITIONS
            for s in a1.design.STREAMS
            for b in a1.batches(
                [r for r in source[c] if r["instance_id"] in ids],
                s,
                batch_size=args.batch_size,
            )
        ]
        donors = [
            b
            for c in a1.design.CONDITIONS
            for s in a1.design.STREAMS
            for b in a1.batches(source[c], s, batch_size=args.batch_size)
        ]
        maps = [m for m in frozen["donors"] if m["recipient_id"] in ids]
        positive = []
        for m in maps:
            if m["operation"] != "item_swap":
                continue
            r = next(
                r
                for r in source[m["recipient_condition"]]
                if r["instance_id"] == m["recipient_id"]
            )
            positive.append(
                dict(
                    m,
                    supported=True,
                    recipient_positions=[
                        r["streams"][m["recipient_stream"]]["readout"]
                    ],
                    donor_positions=[r["streams"][m["donor_stream"]]["readout"]],
                )
            )
        controls.extend(a1.calibrate(model, recipients, donors, positive, task))
        for op in receipt["operations"]:
            for seed in (
                receipt["independent_donor_seeds"]
                if op == "independent_resample"
                else (None,)
            ):
                subset = [
                    m
                    for m in maps
                    if m["operation"] == op and (seed is None or m["seed"] == seed)
                ]
                append(
                    runner.score_cell(
                        model,
                        recipients,
                        groups=groups,
                        operation=op,
                        donor_batches=donors,
                        donor_maps=subset,
                        mean_bank=bank,
                    ),
                    aliases,
                )
        for utility in ("ioi", "mmlu"):
            utility_rows = prepared["utility"][utility][: args.limit or None]
            recipients = task_batches(utility_rows, batch_size=args.batch_size)
            maps = [
                m
                for m in prepared["utility"][utility + "_maps"]
                if m["recipient_id"] in {r["instance_id"] for r in utility_rows}
            ]
            if utility == "ioi":
                donors = task_batches(prepared["utility"]["ioi"], stream="corrupt")
                lookup = {r["instance_id"]: r for r in utility_rows}
                calibration = [
                    dict(
                        m,
                        recipient_positions=[
                            lookup[m["recipient_id"]]["streams"]["clean"]["readout"]
                        ],
                        donor_positions=[
                            lookup[m["recipient_id"]]["streams"]["corrupt"]["readout"]
                        ],
                        supported=True,
                    )
                    for m in maps
                ]
                ops = ("item_swap", "zero", "h_mean", "self_replay", "empty")
            else:
                donors = task_batches(prepared["utility"]["mmlu"])
                calibration = maps
                ops = ("zero", "h_mean", "self_replay", "empty")
            controls.extend(a1.calibrate(model, recipients, donors, calibration, task))
            for op in ops:
                append(
                    runner.score_cell(
                        model,
                        recipients,
                        groups=groups,
                        operation=op,
                        donor_batches=donors,
                        donor_maps=maps,
                        mean_bank=bank,
                    ),
                    aliases,
                )
    a1.validate_positive_controls(controls, _prepared_domain(receipt), args.limit)
    validate_a2_scope(receipt, rows, limit=args.limit, banks=banks, bank_path=bank_path)
    return dict(
        kind="a2_scored",
        receipt_sha256=receipt["receipt_sha256"],
        bank_artifact_sha256=hash_content(banks),
        rows=rows,
        positive_controls=controls,
        expected=[list(k) for k in expected_keys(receipt, args.limit)],
        pilot=bool(args.limit),
        limit=args.limit,
        injected=bool(args.injected or receipt["injected"] or banks.get("injected")),
        execution_provenance=a1.finish_execution(state, "scoring"),
        counts=dict(
            rows=len(rows),
            expected=len(expected_keys(receipt, args.limit)),
            positive_controls=len(controls),
        ),
    )


def empty_group_evidence(receipt, rows):
    """Require complete supported crossed evidence, allowing empty-patch degeneracy."""
    import math

    by_group = {
        name: [] for name, group in receipt["groups"].items() if not group["members"]
    }
    for row in rows:
        if row["group"] not in by_group or row["operation"] == "independent_resample":
            continue
        if row["operation"] == "h_twin" and row["condition"] == "F":
            continue  # Predeclared unsupported diagnostic, never required evidence.
        by_group[row["group"]].append(row)
    return {
        name: bool(records)
        and all(
            row.get("supported") is True
            and row.get("assay_valid") is True
            and all(
                type(row.get(field)) in (int, float, bool) and math.isfinite(row[field])
                for field in (
                    "intact_margin",
                    "patched_margin",
                    "intact_correct",
                    "patched_correct",
                )
            )
            for row in records
        )
        for name, records in by_group.items()
    }


def summarize(receipt, scored, *, n_boot=2000, final=False):
    from component_analysis.ladder_metrics import summarize_ladder

    require(
        scored["receipt_sha256"] == receipt["receipt_sha256"], "stale scored receipt"
    )
    validate_a2_scope(receipt, scored["rows"], limit=scored["limit"])
    a1.validate_positive_controls(
        scored["positive_controls"], _prepared_domain(receipt), scored["limit"]
    )
    validate_finalization(receipt, scored, final=final)
    if scored["pilot"]:
        return dict(
            status="pilot diagnostics only; no final gate verdict",
            counts=scored.get("counts"),
            final=False,
        )
    summary = summarize_ladder(scored["rows"], bootstrap_seed=1, n_boot=n_boot)
    empty_evidence = empty_group_evidence(receipt, scored["rows"])
    for cell in summary["cells"]:
        if cell["group"] in empty_evidence:
            cell["empty_group_required_evidence_complete"] = empty_evidence[
                cell["group"]
            ]
    result = aggregate_tasks(receipt, summary)
    result.update(
        final=final,
        receipt_sha256=receipt["receipt_sha256"],
        score_sha256=hash_content(scored),
        positive_controls_complete=True,
        source_qualifier="independently trained matched pressure twins; original A1 SDR descriptive-set qualifier does not transfer",
    )
    return result


def _reference(path):
    return dict(path=str(Path(path).resolve()), file_sha256=a1.common.file_hash(path))


def _check_reference(reference):
    require(
        a1.common.file_hash(reference["path"]) == reference["file_sha256"],
        "stale file reference: " + reference["path"],
    )


def _load_context(args):
    prepared = a1.read_artifact(args.design)
    ancestor = _a1_args(prepared, args.selected)
    ancestor.registry = args.registry
    a1.validate_prepared(ancestor, prepared)
    selected = a1.read_selection(ancestor, prepared)
    # Existing validation checks live protected registries, sources, graders,
    # donor plans, selection sidecar and code before any tokenizer/model load.
    return (
        prepared,
        selected,
        a1.common.read_json(a1.selection_manifest_path(args.selected)),
    )


_CATALOGUE_KIND = "a2_specificity_catalogue_binding_v1"
_FOREIGN_FIELDS = frozenset((
    "id", "title", "status", "summary", "claimed_by", "claimed_at", "dir",
    "updated", "status_source", "branch", "worktree", "spec", "resume",
    "worklog", "state", "ledger", "parent_findings", "do_not_touch",
    "archive", "legacy_scratch", "frozen_grader_sha256",
))


def _catalogue_canonical(value):
    # JSON text preserves bool/int/float distinctions that Python equality loses.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _catalogue_digest(value):
    return hashlib.sha256(_catalogue_canonical(value).encode("utf-8")).hexdigest()


def _catalogue_routes():
    # Keep lexical routes: resolving symlinks would erase an original guard site.
    return {str(root / "docs/research/directions.json") for root in (a1.PRIMARY, a1.REPO)}


def _catalogue_provenance(value):
    require(isinstance(value, dict) and set(value) == _catalogue_routes(),
            "grader catalogue route drift")
    require(all(isinstance(v, str) and re.fullmatch("[0-9a-f]{64}", v)
                for v in value.values()), "invalid grader catalogue provenance")


def _catalogue_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate grader catalogue JSON key")
        result[key] = value
    return result


def _catalogue_nonfinite(value):
    raise ValueError("nonfinite grader catalogue JSON: " + value)


def _observe_grader_catalogue():
    # Always retain the original actual source hash and current own-pin checks.
    provenance = a1.grader_registry()
    _catalogue_provenance(provenance)
    routes = {}
    for path in sorted(provenance):
        raw = Path(path).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == provenance[path],
                "grader catalogue same-buffer hash mismatch")
        data = json.loads(raw, object_pairs_hook=_catalogue_pairs,
                          parse_constant=_catalogue_nonfinite)
        require(isinstance(data, dict), "invalid grader catalogue object")
        _catalogue_canonical(data)
        updated = data.get("updated")
        require(isinstance(updated, str) and
                re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", updated),
                "invalid grader catalogue updated date")
        datetime.date.fromisoformat(updated)
        rows = data.get("directions")
        require(isinstance(rows, list) and all(isinstance(r, dict) for r in rows),
                "invalid grader catalogue rows")
        own = [r for r in rows if r.get("id") == "specificity-ladder"]
        require(len(own) == 1 and own[0].get("frozen_grader_sha256") == a1.GRADER,
                "missing/duplicate/stale own grader entry")
        foreign = []
        for row in rows:
            if row.get("id") == "specificity-ladder":
                continue
            require(set(row) <= _FOREIGN_FIELDS, "unknown foreign catalogue field")
            require(isinstance(row.get("id"), str) and row["id"],
                    "invalid foreign catalogue identity")
            declarations = {}
            for key in ("do_not_touch", "archive", "legacy_scratch"):
                if key in row:
                    require(isinstance(row[key], list) and
                            all(isinstance(v, str) for v in row[key]),
                            "invalid foreign catalogue path declaration")
                    if row[key]:
                        declarations[key] = row[key]
            pin = row.get("frozen_grader_sha256")
            require(pin is None or (isinstance(pin, str) and
                    re.fullmatch("[0-9a-f]{64}", pin)),
                    "invalid foreign catalogue grader pin")
            if pin is not None:
                declarations["frozen_grader_sha256"] = pin
            if declarations:
                foreign.append(dict(id=row["id"], declarations=declarations))
        # Sorted list is a multiset: retain duplicate rows and declaration values.
        record = dict(own_entry=own[0],
                      foreign_declarations=sorted(foreign, key=_catalogue_canonical),
                      top={k: v for k, v in data.items() if k not in ("directions", "updated")})
        record["sha256"] = _catalogue_digest(record)
        routes[path] = record
    binding = dict(kind=_CATALOGUE_KIND, routes=routes)
    # Reject nonfinite values anywhere, including nonauthoritative metadata.
    # Capture a separate JSON object, never a mutable decoded-data alias.
    return copy.deepcopy(provenance), json.loads(_catalogue_canonical(binding))


def _validate_grader_catalogue(receipt):
    current_provenance, current = _observe_grader_catalogue()
    _catalogue_provenance(receipt.get("grader_registry"))
    frozen = receipt.get("grader_binding")
    require(isinstance(frozen, dict) and set(frozen) == {"kind", "routes"}
            and frozen.get("kind") == _CATALOGUE_KIND
            and isinstance(frozen.get("routes"), dict)
            and set(frozen["routes"]) == set(current_provenance),
            "missing/invalid A2 grader binding")
    for record in frozen["routes"].values():
        require(isinstance(record, dict) and
                set(record) == {"own_entry", "foreign_declarations", "top", "sha256"}
                and record["sha256"] == _catalogue_digest(
                    {k: v for k, v in record.items() if k != "sha256"}),
                "invalid A2 grader binding digest")
    require(_catalogue_canonical(frozen) == _catalogue_canonical(current),
            "A2 grader catalogue binding drift")
    return copy.deepcopy(receipt["grader_registry"]), copy.deepcopy(frozen)


def _validate_live(args, receipt, prepared):
    validate_receipt(receipt, prepared)
    require(receipt.get("execution_commit") == args.commit, "A2 execution commit drift")
    require(
        receipt.get("runtime_code_hashes") == runtime_hashes(),
        "stale A2 runtime code hashes",
    )
    for reference in receipt["file_references"].values():
        _check_reference(reference)
    records = comparison._read(receipt["file_references"]["source_records"]["path"])[
        "records"
    ]
    fresh = comparison.compare_masks(records)
    require(fresh == receipt["comparison"], "stale all18 training source audit")
    require(
        receipt["registry_hashes"] == a1.registries(args, prepared["rows"])
        and receipt["utility_registry_hashes"]
        == a1.utility_registries(args, prepared["utility"]),
        "protected registry snapshot drift",
    )
    _validate_grader_catalogue(receipt)


def _manifest(args, receipt, payload):
    provenance, binding = _validate_grader_catalogue(receipt)
    return dict(
        kind="a2_" + args.stage,
        execution_commit=args.commit,
        a1_ancestor_commit=receipt["a1_ancestor_commit"],
        training_execution_commit=receipt["a2_training_execution_commit"],
        runtime_code_hashes=runtime_hashes(),
        group_receipt_sha256=receipt["receipt_sha256"],
        comparison_sha256=receipt["comparison_sha256"],
        source_artifacts=receipt["file_references"],
        registry_hashes=receipt["registry_hashes"],
        utility_registry_hashes=receipt["utility_registry_hashes"],
        grader_registry=provenance,
        grader_binding=binding,
        model_identity=receipt["model_identity"],
        execution=payload.get("execution_provenance"),
        payload_sha256=hash_content(payload),
        counts=payload.get("counts"),
        operations=receipt["operations"],
        mapping="unchanged frozen explicit unpadded position maps",
        budget_admission="Orchestrator-owned; this artifact does not authorize GPU admission or reserve resources.",
    )


def _publish_stage(target, filename, payload, manifest):
    def writer(root):
        a1.write_artifact(root / filename, payload)
        a1.common.write_json(root / "run_manifest.json", manifest)

    a1.common.publish(target, writer)


def read_stage(root, filename, stage, args, receipt):
    """Consume only complete stages whose marker binds exact content and runtime."""
    marker = Path(root) / "run_manifest.json"
    require(marker.is_file(), "missing A2 stage completion manifest")
    manifest = a1.common.read_json(marker)
    payload = a1.read_artifact(Path(root) / filename)
    parent = copy.copy(args)
    parent.stage = stage
    require(
        manifest == _manifest(parent, receipt, payload),
        "stale A2 completion manifest link",
    )
    return payload


def parser():
    p = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    p.add_argument(
        "--stage", required=True, choices=("freeze", "bank", "score", "summarize")
    )
    for name in ("design", "selected", "work-dir", "commit"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--comparison")
    p.add_argument("--source-records")
    p.add_argument("--registry", action="append", default=[])
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--final", action="store_true")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument(
        "--independent-donors",
        action="store_true",
        help="Freeze optional fixed donor seeds101/102/103",
    )
    return p


def main(argv=None, model_loader=None):
    args = parser().parse_args(argv)
    require(
        re.fullmatch("[0-9a-f]{40}", args.commit) is not None,
        "full 40-hex execution --commit required",
    )
    require(args.limit >= 0 and args.batch_size > 0, "invalid limit/batch size")
    require(not args.final or args.stage == "summarize", "--final requires summarize")
    require(not args.limit or args.stage == "score", "--limit is score pilot only")
    require(
        not args.independent_donors or args.stage == "freeze",
        "independent donors must be frozen prospectively",
    )
    os.environ.update(
        HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1"
    )
    prepared, selected, sidecar = _load_context(args)
    args.tasks = list(TASKS)
    for field in ("model", "model_revision", "tokenizer_revision"):
        setattr(args, field, prepared[field])
    args.injected = model_loader is not None or bool(prepared.get("injected"))
    root = Path(args.work_dir)
    groups_path = root / "groups.json"
    bank_path = root / "bank" / "banks.json"
    if args.stage == "freeze":
        require(
            args.comparison and args.source_records,
            "freeze requires comparison and all18 source records",
        )
        comp = comparison._read(args.comparison)
        require(
            comparison.compare_masks(comparison._read(args.source_records)["records"])
            == comp,
            "comparison/current sources differ",
        )
        receipt = freeze_a2_groups(comp, prepared, selected, sidecar)
        if not receipt["injected"]:
            require(
                prepared["commit"] == "5f450dc93dac707af649dee8c8ca60888b2831db",
                "unexpected A1 ancestor commit",
            )
        if args.independent_donors:
            receipt["operations"].append("independent_resample")
            receipt["independent_donor_seeds"] = [101, 102, 103]
        provenance, binding = _observe_grader_catalogue()
        receipt.update(
            execution_commit=args.commit,
            runtime_code_hashes=runtime_hashes(),
            file_references={
                name: _reference(path)
                for name, path in dict(
                    design=args.design,
                    selected=args.selected,
                    selection_sidecar=a1.selection_manifest_path(args.selected),
                    comparison=args.comparison,
                    source_records=args.source_records,
                ).items()
            },
            registry_hashes=a1.registries(args, prepared["rows"]),
            utility_registry_hashes=a1.utility_registries(args, prepared["utility"]),
            grader_registry=provenance,
            grader_binding=binding,
        )
        receipt["receipt_sha256"] = hash_content(
            {k: v for k, v in receipt.items() if k != "receipt_sha256"}
        )
        if not args.dry_run:
            publish_artifact(groups_path, receipt)
    else:
        receipt = a1.read_artifact(groups_path)
        _validate_live(args, receipt, prepared)
        if args.stage in ("score", "summarize"):
            banks = read_stage(root / "bank", "banks.json", "bank", args, receipt)
            validate_banks(receipt, prepared, banks)
        if args.stage == "summarize":
            scored = read_stage(root / "score", "score.json", "score", args, receipt)
            require(
                scored["bank_artifact_sha256"] == hash_content(banks),
                "stale scored bank artifact",
            )
            require(
                scored["expected"]
                == [list(k) for k in expected_keys(receipt, scored["limit"])],
                "stale scored expected domain",
            )
            validate_a2_scope(
                receipt,
                scored["rows"],
                limit=scored["limit"],
                banks=banks,
                bank_path=bank_path,
            )
            a1.validate_positive_controls(
                scored["positive_controls"], prepared, scored["limit"]
            )
            validate_finalization(receipt, scored, final=args.final)
            if not args.dry_run:
                summary = summarize(receipt, scored, final=args.final)

                def publish_summary(target):
                    a1.write_artifact(target / "summary.json", summary)
                    a1.common.write_json(
                        target / "run_manifest.json", _manifest(args, receipt, summary)
                    )
                    lines = [
                        "task\tseed\tgroup\theads\tmlps\tprimary_point_pass\tassay_ready\tboth_MMLU_floors_pass\tspecificity_pass\tstrong\tassessment_status"
                    ]
                    for task, v in summary.get("tasks", {}).items():
                        for seed, one in v["per_seed"].items():
                            lines.append(
                                "\t".join(
                                    map(
                                        str,
                                        [
                                            task,
                                            seed,
                                            one["group"],
                                            one["component_counts"]["head"],
                                            one["component_counts"]["mlp"],
                                            one["primary_point_pass"],
                                            one["complete_assay_ready"],
                                            one["both_mmlu_floors_pass"],
                                            one["specificity_pass"],
                                            one["strong"],
                                            one["assessment_status"],
                                        ],
                                    )
                                )
                            )
                    (target / "comparison.tsv").write_text("\n".join(lines) + "\n")

                a1.common.publish(root / "summary", publish_summary)
        elif not args.dry_run:
            # Runtime identity/tokenization checks happen only after CPU source/access
            # validation. Dry-run intentionally has no tokenizer/model dependency.
            tokenizer = a1.common.load_tokenizer(args)
            a1.validate_tokenization(prepared, tokenizer)
            _validate_live(args, receipt, prepared)
            if args.stage == "bank":
                require(not (root / "bank").exists(), "output exists: bank")
                payload = a1.timed_model_stage(
                    args,
                    model_loader or a1.load_model,
                    lambda model: collect_banks(args, receipt, prepared, model),
                    "bank",
                )
                _publish_stage(
                    root / "bank",
                    "banks.json",
                    payload,
                    _manifest(args, receipt, payload),
                )
            else:
                require(not (root / "score").exists(), "output exists: score")
                payload = a1.timed_model_stage(
                    args,
                    model_loader or a1.load_model,
                    lambda model: score(
                        args, receipt, prepared, banks, bank_path, model
                    ),
                    "scoring",
                )
                _publish_stage(
                    root / "score",
                    "score.json",
                    payload,
                    _manifest(args, receipt, payload),
                )
    print(
        args.stage
        + (
            ": validated dry-run; no tokenizer, weights or writes"
            if args.dry_run
            else ": complete"
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
