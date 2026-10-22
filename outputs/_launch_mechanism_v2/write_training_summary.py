#!/usr/bin/env python3
"""Ticket-05 training summary: sizes and in-run node evaluation of the v2 circuits.

Reads train_jobs.txt beside this script (one line per submission), each run's
results.json and trained masks, and sacct; writes
    <report_dir>/05-training-summary.json
    <report_dir>/05-training-summary.md
No evaluation is run: this only reads files the training jobs wrote.

usage (from the worktree root):
    python outputs/_launch_mechanism_v2/write_training_summary.py <report_dir>

Sizes come from evaluation.masks.count_masks on the trained masks: a coarse
run's active_nodes.coarse.json (post-processing expands active_nodes.json so
every fine unit of a live head opens, which misstates a coarse circuit's size),
else active_nodes.json. heads = active attention heads; fine units = active
attention neurons + MLP hidden + MLP output, reported only when all three were
pruned (fine runs).

The in-run gate of the coarse SDR wave (accuracy >= 0.90, exact match >= 0.90,
KL <= 0.20 on the run's own test split) is reported, never acted on.
D vs H head gap = (heads_H - heads_D) / heads_D, in percent.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from evaluation.masks import count_masks  # noqa: E402

MAIN = "/projects/beto/swong2/Alignment/Deception-Circuit"
V1_REFERENCES = [
    ("v1 sdr fine D (reference)", "outputs/llama-8b-instruct_sdr/nls0.3_noedge_260819-083414"),
    ("v1 sdr coarse D (reference)", "outputs/llama-8b-instruct_sdr_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742"),
    ("v1 sdr coarse H (orientation)", "outputs/llama-8b-instruct_sdr_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_260922-092743"),
]
QUOTED = {"v1 sdr fine D (reference)": {"heads": 68, "fine_units": 11251},
          "v1 sdr coarse D (reference)": {"heads": 69}}
REF_COARSE_CONFIG = os.path.join(MAIN, "outputs/llama-8b-instruct_sdr_coarse/"
                                 "nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742/config.coarse.json")
EXPECTED_CONFIG_DIFF = {"task", "deception_condition", "deception_margin_loss"}
GATE = {"accuracy": (">=", 0.90), "exact_match": (">=", 0.90), "kl_div": ("<=", 0.20)}
FINE_KINDS = ("attention_neurons", "mlp_hidden", "mlp_output")


def mask_file(run_dir):
    coarse = os.path.join(run_dir, "active_nodes.coarse.json")
    return coarse if os.path.exists(coarse) else os.path.join(run_dir, "active_nodes.json")


def sizes(run_dir):
    with open(mask_file(run_dir)) as f:
        counts = count_masks(json.load(f)["masks"])
    out = {"mask_file": os.path.basename(mask_file(run_dir)),
           "heads": counts["attention_heads"]["active"],
           "attention_blocks": counts.get("attention_blocks", {}).get("active")}
    if all(k in counts for k in FINE_KINDS):
        out["fine_units"] = sum(counts[k]["active"] for k in FINE_KINDS)
    return out


def in_run(run_dir):
    with open(os.path.join(run_dir, "results.json")) as f:
        r = json.load(f)
    ne = r["node_eval"]
    misses = [k for k, (op, t) in GATE.items() if not (ne[k] >= t if op == ">=" else ne[k] <= t)]
    return {"node_eval": {k: ne[k] for k in ("accuracy", "exact_match", "kl_div", "logit_diff") if k in ne},
            "baseline": {k: r["baseline"][k] for k in ("accuracy", "exact_match", "kl_div", "logit_diff")
                         if k in r.get("baseline", {})},
            "node_granularity": r.get("node_granularity"),
            "gate_misses": misses, "gate_holds": not misses}


def _flat(d, prefix=""):
    out = {}
    for k, v in d.items():
        out.update(_flat(v, prefix + k + ".") if isinstance(v, dict) else {prefix + k: v})
    return out


def config_vs_reference(run_dir):
    """Keys of the run's trained config (config.coarse.json, else config.json) that differ from the
    coarse reference's config.coarse.json, beyond the expected task / condition / margin pin."""
    name = "config.coarse.json" if os.path.exists(os.path.join(run_dir, "config.coarse.json")) else "config.json"
    with open(os.path.join(run_dir, name)) as f:
        cfg = _flat(json.load(f))
    with open(REF_COARSE_CONFIG) as f:
        ref = _flat(json.load(f))
    diff = sorted(k for k in set(cfg) | set(ref) if cfg.get(k, "<absent>") != ref.get(k, "<absent>"))
    return {"file": name, "differing_keys": diff,
            "unexpected": [k for k in diff if k not in EXPECTED_CONFIG_DIFF],
            "deception_margin_loss": cfg.get("deception_margin_loss")}


def sacct(jid):
    o = subprocess.run(["sacct", "-X", "-n", "-P", "-j", jid, "-o", "State,Elapsed,ElapsedRaw,Partition,NodeList"],
                       capture_output=True, text=True).stdout.strip().splitlines()
    if not o:
        return {}
    state, el, raw, part, node = o[0].split("|")
    return {"state": state.split()[0], "elapsed": el, "elapsed_s": int(raw), "partition": part, "node": node}


def main(report_dir):
    # A cell can have several submissions (the queued backup and an interactive run). The summary uses
    # the latest submission whose run dir holds results.json, else the latest one; all job ids are kept.
    subs = {}
    with open(os.path.join(HERE, "train_jobs.txt")) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                p = line.split()
                subs.setdefault(p[0], []).append(
                    {"run": p[0], "task": p[1], "condition": p[2], "run_dir": p[3], "job_id": p[4],
                     "account": p[5], "submitted_partition": p[6], "time_limit": p[7], "submitted": p[8]})
    jobs = {}
    for name, lst in subs.items():
        done = [j for j in lst if os.path.exists(os.path.join(ROOT, j["run_dir"], "results.json"))]
        jobs[name] = dict((done or lst)[-1])
        jobs[name]["submissions"] = []
        for j in lst:
            sa = sacct(j["job_id"])
            jobs[name]["submissions"].append(
                {"job_id": j["job_id"], "run_dir": j["run_dir"], "partition": j["submitted_partition"],
                 "state": sa.get("state"), "elapsed": sa.get("elapsed"),
                 "dir_exists": os.path.isdir(os.path.join(ROOT, j["run_dir"])),
                 "has_results": os.path.exists(os.path.join(ROOT, j["run_dir"], "results.json"))})
    runs = []
    for name in sorted(jobs, key=lambda n: (n.split("_")[0], "_fine" in n, "_H_" in n)):
        j = jobs[name]
        j.update(sacct(j["job_id"]))
        rd = os.path.join(ROOT, j["run_dir"])
        j["finished"] = os.path.exists(os.path.join(rd, "results.json"))
        j["postprocessed"] = os.path.exists(os.path.join(rd, "active_nodes.coarse.json"))
        if j["finished"]:
            j.update(sizes(rd))
            j.update(in_run(rd))
            j["config_vs_reference"] = config_vs_reference(rd)
        runs.append(j)

    gaps = {}
    for task in sorted({r["task"] for r in runs}):
        for kind in ("coarse", "fine"):
            d = next((r for r in runs if r["run"] == f"{task}_D_{kind}" and "heads" in r), None)
            h = next((r for r in runs if r["run"] == f"{task}_H_{kind}" and "heads" in r), None)
            if d and h:
                gaps[f"{task}_{kind}"] = {"heads_D": d["heads"], "heads_H": h["heads"],
                                          "gap_pct": round(100 * (h["heads"] - d["heads"]) / d["heads"], 1)}

    refs = []
    for label, rel in V1_REFERENCES:
        rd = os.path.join(MAIN, rel)
        ref = {"label": label, "run_dir": rd, **sizes(rd), **in_run(rd)}
        ref["quoted"] = QUOTED.get(label)
        refs.append(ref)

    out = {"ticket": "05-train-v2-circuits-and-hand-back", "scope": "G12: coarse heads-only runs only; fine deferred",
           "gate": {k: f"{op} {t}" for k, (op, t) in GATE.items()}, "gap_definition": "(heads_H - heads_D) / heads_D",
           "runs": runs, "d_vs_h_head_gap": gaps, "v1_references": refs}
    with open(os.path.join(report_dir, "05-training-summary.json"), "w") as f:
        json.dump(out, f, indent=1)

    L = ["# Ticket 05 training summary (generated by outputs/_launch_mechanism_v2/write_training_summary.py)", "",
         "Scope: user ruling G12. Six coarse heads-only runs at NLS 0.3; the six fine runs are deferred.",
         "Sizes come from `evaluation/masks.count_masks` on `active_nodes.coarse.json` (the trained masks).",
         "The in-run gate (accuracy >= 0.90, exact match >= 0.90, KL <= 0.20) is the coarse SDR wave's. "
         "It is a reading only and was not acted on.", "",
         "## v2 runs", "",
         "| run | job | partition | state | elapsed | heads | attn blocks | node acc | node EM | node KL | gate |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in runs:
        if r["finished"]:
            ne = r["node_eval"]
            gate = "holds" if r["gate_holds"] else "miss: " + ", ".join(r["gate_misses"])
            L.append(f"| {r['run']} | {r['job_id']} | {r.get('partition', '')} | {r.get('state', '')} | "
                     f"{r.get('elapsed', '')} | {r['heads']} | {r['attention_blocks']} | {ne['accuracy']:.3f} | "
                     f"{ne['exact_match']:.3f} | {ne['kl_div']:.3f} | {gate} |")
        else:
            L.append(f"| {r['run']} | {r['job_id']} | {r.get('partition', '')} | {r.get('state', '')} | "
                     f"{r.get('elapsed', '')} | not finished | | | | | |")
    L += ["", "Run directories used (worktree root relative):", ""]
    L += [f"- {r['run']}: `{r['run_dir']}`" for r in runs]
    L += ["", "## All submissions per cell", "",
          "The first submission to write results.json won its cell. The others were cancelled, or failed; "
          "a failed run's directory is kept and not used.", "",
          "| cell | job | submitted partition | state | elapsed | run dir | dir exists | results.json |",
          "|---|---|---|---|---|---|---|---|"]
    for r in runs:
        for sub in r["submissions"]:
            used = " (used)" if sub["job_id"] == r["job_id"] else ""
            L.append(f"| {r['run']} | {sub['job_id']}{used} | {sub['partition']} | {sub['state']} | "
                     f"{sub['elapsed']} | `{os.path.basename(sub['run_dir'])}` | "
                     f"{'yes' if sub['dir_exists'] else 'no'} | {'yes' if sub['has_results'] else 'no'} |")
    L += ["", "## Trained config against the coarse reference", "",
          "Each run's `config.coarse.json` is compared key by key with the reference's `config.coarse.json`. "
          "The expected differences are task, deception_condition and deception_margin_loss (0.7 here, null in the "
          "reference).", ""]
    for r in runs:
        if r["finished"]:
            c = r["config_vs_reference"]
            L.append(f"- {r['run']}: differs in {', '.join(c['differing_keys'])}; unexpected: "
                     f"{', '.join(c['unexpected']) or 'none'}; deception_margin_loss {c['deception_margin_loss']}")
    L += ["", "## D vs H head gap per task", "", "Gap = (heads H - heads D) / heads D.", "",
          "| task | heads D | heads H | gap |", "|---|---|---|---|"]
    for k, g in gaps.items():
        L.append(f"| {k} | {g['heads_D']} | {g['heads_H']} | {g['gap_pct']:+.1f}% |")
    L += ["", "## v1 SDR reference sizes (recomputed with count_masks, main checkout)", "",
          "| run | heads | fine units | quoted | node acc | node EM | node KL | gate |", "|---|---|---|---|---|---|---|---|"]
    for r in refs:
        ne = r["node_eval"]
        gate = "holds" if r["gate_holds"] else "miss: " + ", ".join(r["gate_misses"])
        q = r["quoted"]
        qs = ", ".join(f"{k} {v:,}" for k, v in q.items()) if q else "n/a"
        fu = f"{r['fine_units']:,}" if "fine_units" in r else "n/a"
        L.append(f"| {r['label']} | {r['heads']} | {fu} | {qs} | {ne['accuracy']:.3f} | {ne['exact_match']:.3f} | "
                 f"{ne['kl_div']:.3f} | {gate} |")
    L += [""] + [f"- {r['label']}: `{r['run_dir']}` ({r['mask_file']})" for r in refs] + [""]
    with open(os.path.join(report_dir, "05-training-summary.md"), "w") as f:
        f.write("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main(sys.argv[1])
