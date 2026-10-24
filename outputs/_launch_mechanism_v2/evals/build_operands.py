#!/usr/bin/env python3
"""
build_operands.py -- the non-circuit inputs of the v2 coarse evaluation suite (ticket 06). CPU only.

    operands/allmlp_nomb_v2/      the `m` operand of `(E) - m` / `(E) | m`: every MLP unit open, no head,
                                  no attention block. Built by outputs/_launch_format_control/build_allmlp.py
                                  (the submit_headsko.sh recipe) from the far_v2 D run, so its config.json
                                  names a v2 task; an `operand` key says what it is (the evaluator reads only
                                  its whitelisted run keys, so the extra key is inert).
    standins/<t>_v2_nopressure/   config.json only: the <t>_v2 D run's config with deception_condition
                                  nopressure, so `--task-from` binds the <t>_v2_nopressure test set. Never
                                  bound as a circuit (there are no v2 Format Circuits).
    drift_control/sdr_coarse_D_260922-092742/
                                  byte copies of active_nodes.json and config.json of the v1 coarse SDR D run
                                  (main checkout, not on this branch), with sha256 in provenance.json.

usage (from the repository root):
    python outputs/_launch_mechanism_v2/evals/build_operands.py [--main-checkout DIR]
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import mv2_cells as mc  # noqa: E402

REPO = mc.REPO
MAIN_CHECKOUT = mc.MAIN_CHECKOUT

DRIFT_SOURCE = "outputs/llama-8b-instruct_sdr_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742"
DRIFT_FILES = ("active_nodes.json", "config.json")
OPERAND_NOTE = ("all-MLP, no-head operand m of the coarse heads-only cells (E) - m and (E) | m; "
                "not a trained circuit. Built by build_allmlp.py from the far_v2 D run (ticket 06).")
STANDIN_NOTE = ("config-only task source for --task-from (the nopressure test set); not a run and never "
                "bound as a circuit (ticket 06).")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _fc_build_allmlp():
    path = os.path.join(REPO, "outputs", "_launch_format_control", "build_allmlp.py")
    spec = importlib.util.spec_from_file_location("fc_build_allmlp", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build_allmlp


def build_allmlp_v2(repo: str = REPO, out_repo: str = REPO) -> str:
    src = os.path.join(repo, mc.RUNS["far"]["D"])
    out = os.path.join(out_repo, mc.ALLMLP)
    _fc_build_allmlp()(src, out)
    # build_allmlp records an absolute `built_from`; keep it repo-relative so the operand is portable.
    path = os.path.join(out, "active_nodes.json")
    with open(path) as f:
        data = json.load(f)
    data["built_from"] = mc.RUNS["far"]["D"]
    with open(path, "w") as f:
        json.dump(data, f)
    cpath = os.path.join(out, "config.json")
    with open(cpath) as f:
        cfg = json.load(f)
    cfg["operand"] = OPERAND_NOTE
    with open(cpath, "w") as f:
        json.dump(cfg, f, indent=1)
    return out


def build_standins(repo: str = REPO, out_repo: str = REPO) -> dict:
    out = {}
    for t in mc.TASKS:
        with open(os.path.join(repo, mc.RUNS[t]["D"], "config.json")) as f:
            cfg = json.load(f)
        cfg["deception_condition"] = "nopressure"
        cfg["standin"] = STANDIN_NOTE
        cfg["standin_of"] = mc.RUNS[t]["D"]
        d = os.path.join(out_repo, mc.STANDINS[t])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "config.json"), "w") as f:
            json.dump(cfg, f, indent=1)
        out[t] = d
    return out


def copy_drift_run(main_checkout: str = MAIN_CHECKOUT, out_repo: str = REPO) -> str:
    src = os.path.join(main_checkout, DRIFT_SOURCE)
    out = os.path.join(out_repo, mc.DRIFT_D)
    os.makedirs(out, exist_ok=True)
    files = {}
    for name in DRIFT_FILES:
        shutil.copyfile(os.path.join(src, name), os.path.join(out, name))
        files[name] = {"sha256": sha256(os.path.join(out, name))}
        if files[name]["sha256"] != sha256(os.path.join(src, name)):
            raise RuntimeError(f"copy of {name} differs from {src}")
    prov = {"source": DRIFT_SOURCE, "source_checkout": main_checkout, "files": files,
            "note": "byte copy of the v1 coarse SDR D run for the ticket-06 drift control; the run is "
                    "not on branch mechanism-datasets. Only the knockout eval reads it (masks + config)."}
    with open(os.path.join(out, "provenance.json"), "w") as f:
        json.dump(prov, f, indent=1)
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--main-checkout", default=MAIN_CHECKOUT)
    a = p.parse_args(argv)
    print(build_allmlp_v2())
    for d in build_standins().values():
        print(d)
    print(copy_drift_run(a.main_checkout))


if __name__ == "__main__":
    main()
