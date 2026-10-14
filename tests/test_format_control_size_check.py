"""Format Circuit size rule and training launcher (ticket 03, format-control).

The size rule (spec, "Pairing targets and the size rule"): a gap above 25
percent in head count, or in fine-unit count for fine circuits, between a
Format Circuit and its paired mechanism circuit triggers one retrain at
NLS 0.3 +/- 0.1 in the direction that closes the gap; at most one retune.

Paired sizes used below are the real ones: FAR D 48 heads / 5,436 fine units,
SDR D 68 heads / 11,251 fine units, coarse heads-only SDR D 69 heads.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCH = os.path.join(REPO, "outputs", "_launch_format_control")


def _load_size_check():
    spec = importlib.util.spec_from_file_location(
        "format_control_size_check", os.path.join(LAUNCH, "size_check.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sc = _load_size_check()


# ---------------------------------------------------------------- the boundary

@pytest.mark.parametrize("format_heads, expected", [
    (124, None),   # 24 percent larger than 100: within tolerance
    (125, None),   # exactly 25 percent larger: not "above 25 percent"
    (126, 0.4),    # 26 percent larger: higher NLS, fewer heads
    (76, None),    # 24 percent smaller
    (75, None),    # exactly 25 percent smaller
    (74, 0.2),     # 26 percent smaller: lower NLS, more heads
])
def test_head_gap_fires_only_above_25_percent(format_heads, expected):
    step = sc.retune_step({"heads": 100}, {"heads": format_heads}, 0.3)
    if expected is None:
        assert step is None
    else:
        assert step == pytest.approx(expected)


FAR_D = {"heads": 48, "fine_units": 5436}


@pytest.mark.parametrize("format_units, expected", [
    (6795, None),   # exactly 25 percent above 5,436
    (6796, 0.4),    # just above: higher NLS
    (4077, None),   # exactly 25 percent below
    (4076, 0.2),    # just below: lower NLS
])
def test_fine_unit_gap_fires_for_fine_circuits_even_when_heads_match(format_units, expected):
    step = sc.retune_step(FAR_D, {"heads": 48, "fine_units": format_units}, 0.3)
    if expected is None:
        assert step is None
    else:
        assert step == pytest.approx(expected)


def test_heads_set_the_direction_when_heads_and_fine_units_disagree():
    # 61 heads is 27 percent above 48; 4,000 units is 26 percent below 5,436.
    assert sc.retune_step(FAR_D, {"heads": 61, "fine_units": 4000}, 0.3) == pytest.approx(0.4)


def test_fine_units_set_the_direction_when_only_they_are_out_of_tolerance():
    # 40 heads is 17 percent below 48 (within); 7,000 units is 29 percent above.
    assert sc.retune_step(FAR_D, {"heads": 40, "fine_units": 7000}, 0.3) == pytest.approx(0.4)


def test_coarse_circuits_compare_heads_only():
    # The paired coarse circuit carries no fine-unit count, so a format count
    # (e.g. from an expanded mask with every MLP open) never fires the rule.
    coarse_d = {"heads": 69}
    assert sc.retune_step(coarse_d, {"heads": 70, "fine_units": 590000}, 0.3) is None


# ------------------------------------------------------------- at most one retune

def test_an_already_retuned_run_that_still_misses_is_refused_a_second_step():
    with pytest.raises(sc.RetuneRefused, match="at most one retune"):
        sc.retune_step({"heads": 68}, {"heads": 100}, 0.4, retuned=True)


def test_an_already_retuned_run_within_tolerance_needs_no_step():
    assert sc.retune_step({"heads": 68}, {"heads": 70}, 0.4, retuned=True) is None


# ------------------------------------------------------------------ the CLI seam

N_LAYERS, N_HEADS = 2, 8


def _ones(n, width):
    return [1] * n + [0] * (width - n)


def _fine_masks(heads, an, mh, mo):
    """Masks laid out as active_nodes.json stores them (layer -> 0/1 list)."""
    return {
        "attention_blocks": [1, 1],
        "mlp_blocks": [1, 0],
        "attention_heads": {"0": _ones(heads, N_HEADS), "1": [0] * N_HEADS},
        "attention_neurons": {"0": _ones(an, 1000), "1": [0] * 1000},
        "mlp_hidden": {"0": _ones(mh, 1000), "1": [0] * 1000},
        "mlp_output": {"0": _ones(mo, 1000), "1": [0] * 1000},
    }


def _write_run(path, masks, nls=0.3, node_eval=None, coarse_masks=None):
    os.makedirs(path)
    with open(os.path.join(path, "active_nodes.json"), "w") as f:
        json.dump({"active_heads": {}, "active_mlps": [], "masks": masks}, f)
    if coarse_masks is not None:
        with open(os.path.join(path, "active_nodes.coarse.json"), "w") as f:
            json.dump({"active_heads": {}, "active_mlps": [], "masks": coarse_masks}, f)
    with open(os.path.join(path, "config.json"), "w") as f:
        json.dump({"node_lambda_sparsity": nls}, f)
    node_eval = node_eval or {"accuracy": 0.95, "exact_match": 0.96, "kl_div": 0.08}
    with open(os.path.join(path, "results.json"), "w") as f:
        json.dump({"node_eval": dict(node_eval, outputs=[])}, f)
    return str(path)


def _report(format_run):
    with open(os.path.join(format_run, "size_check.json")) as f:
        return json.load(f)


def test_cli_writes_both_sizes_per_gate_kind_and_the_retune_verdict(tmp_path, capsys):
    paired = _write_run(tmp_path / "D", _fine_masks(heads=4, an=100, mh=100, mo=100))
    fmt = _write_run(tmp_path / "F", _fine_masks(heads=4, an=200, mh=100, mo=100))

    sc.main([paired, fmt])

    r = _report(fmt)
    assert r["paired_counts"] == {"attention_blocks": 2, "mlp_blocks": 1, "heads": 4,
                                  "attention_neurons": 100, "mlp_hidden": 100,
                                  "mlp_output": 100, "fine_units": 300}
    assert r["format_counts"]["fine_units"] == 400       # 33 percent above 300
    assert r["compared"] == ["heads", "fine_units"]
    assert r["verdict"] == "retune"
    assert r["next_nls"] == pytest.approx(0.4)
    out = capsys.readouterr().out
    assert "fine_units" in out and "300" in out and "400" in out and "retune" in out


def _coarse_masks(heads):
    return {"attention_blocks": [1, 0], "attention_heads": {"0": _ones(heads, N_HEADS),
                                                            "1": [0] * N_HEADS}}


def test_cli_reads_the_trained_coarse_masks_not_the_expanded_ones(tmp_path):
    # After post-processing, active_nodes.json is expanded (every fine unit of a
    # live head open); the trained circuit lives in active_nodes.coarse.json.
    paired = _write_run(tmp_path / "D", _fine_masks(4, 1000, 1000, 1000),
                        coarse_masks=_coarse_masks(4))
    fmt = _write_run(tmp_path / "F", _fine_masks(8, 1000, 1000, 1000),
                     coarse_masks=_coarse_masks(6))

    r = sc.main([paired, fmt])

    assert r["paired_source"] == r["format_source"] == "active_nodes.coarse.json"
    assert r["compared"] == ["heads"]
    assert r["format_counts"] == {"attention_blocks": 1, "heads": 6}
    assert r["verdict"] == "retune" and r["next_nls"] == pytest.approx(0.4)   # 6 is 50% above 4


def test_cli_refuses_a_second_retune_on_a_run_already_trained_at_a_stepped_nls(tmp_path):
    paired = _write_run(tmp_path / "D", _fine_masks(4, 100, 100, 100), nls=0.3)
    fmt = _write_run(tmp_path / "F", _fine_masks(8, 100, 100, 100), nls=0.4)

    sc.main([paired, fmt])

    r = _report(fmt)
    assert r["retuned"] is True
    assert r["verdict"] == "refused"
    assert r["next_nls"] is None
    assert "at most one retune" in r["note"]
    assert r["paired_counts"]["heads"] == 4 and r["format_counts"]["heads"] == 8


# ------------------------------------------------ in-run sufficiency (coarse gate)

def test_cli_records_the_in_run_sufficiency_gate_and_flags_a_miss(tmp_path):
    # Coarse-wave gate: acc >= 0.90, exact match >= 0.90, KL <= 0.20. A miss is
    # flagged for the researcher; it never changes the size verdict.
    paired = _write_run(tmp_path / "D", _fine_masks(4, 100, 100, 100))
    fmt = _write_run(tmp_path / "F", _fine_masks(4, 100, 100, 100),
                     node_eval={"accuracy": 0.88, "exact_match": 0.90, "kl_div": 0.21})

    r = sc.main([paired, fmt])

    gate = r["in_run_gate"]
    assert (gate["accuracy"], gate["exact_match"], gate["kl_div"]) == (0.88, 0.90, 0.21)
    assert gate["passes"] is False
    assert gate["misses"] == ["accuracy", "kl_div"]
    assert r["verdict"] == "within_tolerance"


def test_cli_in_run_gate_passes_at_the_thresholds(tmp_path):
    paired = _write_run(tmp_path / "D", _fine_masks(4, 100, 100, 100))
    fmt = _write_run(tmp_path / "F", _fine_masks(4, 100, 100, 100),
                     node_eval={"accuracy": 0.90, "exact_match": 0.90, "kl_div": 0.20})

    gate = sc.main([paired, fmt])["in_run_gate"]

    assert gate["passes"] is True and gate["misses"] == []


# ------------------------------------------------------------ the training launcher

SUBMIT = os.path.join(LAUNCH, "submit_train.sh")

# The paired D runs' settings (their config.json), plus the orchestrator's
# ruling that the hinge margin is pinned to the paired runs' 0.7.
PAIRED_SETTINGS = ["--deception-condition nopressure", "--no-edge-pruning",
                   "--seed 42", "--node-epochs 500", "--lr 0.03", "--batch-size 7",
                   "--max-seq-length 120", "--train-samples 200", "--val-samples 200",
                   "--test-samples 1000", "--deception-margin-loss 0.7"]
COARSE_FLAGS = ["--no-prune-attention-neurons", "--no-prune-mlp-hidden",
                "--no-prune-mlp-output", "--no-prune-mlp-blocks"]


def _dry(*args):
    proc = subprocess.run(["bash", SUBMIT, "--dry", *args], capture_output=True, text=True,
                          timeout=60)
    assert proc.returncode == 0, proc.stderr
    return [line for line in proc.stdout.splitlines() if line.startswith("sbatch ")]


def _sbatch_line(lines, task_dir):
    (line,) = [ln for ln in lines if f"--output-dir outputs/{task_dir}/" in ln]
    return line


def test_dry_run_prints_one_sbatch_line_per_format_circuit_with_the_paired_settings():
    lines = _dry()
    assert len(lines) == 3
    for line in lines:
        assert re.search(r"--account=\S+ --partition=\S+ --time=\S+ ", line)
        for flag in PAIRED_SETTINGS + ["--node-lambda-sparsity 0.3"]:
            assert f" {flag} " in f" {line} ", (flag, line)

    far = _sbatch_line(lines, "llama-8b-instruct_far")
    sdr = _sbatch_line(lines, "llama-8b-instruct_sdr")
    coarse = _sbatch_line(lines, "llama-8b-instruct_sdr_coarse")
    assert " scripts/train_deception.sbatch far " in far
    assert " scripts/train_deception.sbatch sdr " in sdr
    assert " scripts/train_deception.sbatch sdr " in coarse
    assert re.search(r"--output-dir outputs/llama-8b-instruct_far/"
                     r"nls0\.3_nopressure_noedge_\d{6}-\d{6}$", far)
    assert re.search(r"--output-dir outputs/llama-8b-instruct_sdr/"
                     r"nls0\.3_nopressure_noedge_\d{6}-\d{6}$", sdr)
    assert re.search(r"--output-dir outputs/llama-8b-instruct_sdr_coarse/"
                     r"nls0\.3_nopressure_noedge_noan_nomh_nomo_nomb_\d{6}-\d{6}$", coarse)
    for flag in COARSE_FLAGS:
        assert flag in coarse
        assert flag not in far and flag not in sdr


def test_training_never_lands_on_the_40_gb_a100_partitions():
    # Jobs 22879581 / 22879582 hit torch.OutOfMemoryError on gpuA100x8 (39.49 GiB);
    # node pruning needs about 40 GB, so only the 48 GB A40 and 141 GB H200 qualify.
    for line in _dry():
        partitions = re.search(r"--partition=(\S+)", line).group(1).split(",")
        assert partitions and not any(p.startswith("gpuA100") for p in partitions), line
        assert "--export=ALL,PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True" in line


@pytest.mark.parametrize("partition", [
    "gpuA100x4", "gpuA100x8", "gpuA40x4,gpuA100x8", "gpuMI100x8", "gpuA40x4,gpuH200x8,cpu",
    "", ",",
])
def test_launcher_refuses_any_partition_outside_the_a40_h200_allowlist(partition):
    proc = subprocess.run(["bash", SUBMIT, "--dry", "--partition", partition],
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 2
    assert "refusing --partition" in proc.stderr
    assert "sbatch " not in proc.stdout


@pytest.mark.parametrize("partition", ["gpuA40x4", "gpuH200x8", "gpuH200x8,gpuA40x4"])
def test_launcher_accepts_any_subset_of_the_allowlist(partition):
    lines = _dry("--partition", partition)
    assert len(lines) == 3
    assert all(f"--partition={partition} " in line for line in lines)


def test_launcher_rejects_an_unknown_circuit_before_printing_any_line():
    proc = subprocess.run(["bash", SUBMIT, "--dry", "--only", "far bogus"],
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 2
    assert "sbatch " not in proc.stdout


def test_dry_run_of_a_retune_submits_only_the_named_circuit_at_the_stepped_nls():
    lines = _dry("--only", "sdr_coarse", "--nls", "0.4")
    (line,) = lines
    assert " --node-lambda-sparsity 0.4 " in line
    assert re.search(r"llama-8b-instruct_sdr_coarse/nls0\.4_nopressure_noedge_noan_nomh_nomo_nomb_"
                     r"\d{6}-\d{6}$", line)


def _read_or_none(path):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return None


def test_dry_run_records_no_job():
    jobs = os.path.join(LAUNCH, "train_jobs.txt")
    before = _read_or_none(jobs)
    _dry()
    assert _read_or_none(jobs) == before
