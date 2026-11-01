"""B3 generation entrypoint (plan B3 sections 1.3, 1.4 and 3.4; ticket T4).

For every (query, variant, control, condition) context of the chosen split it writes `--samples` sampled rows
(`--control-samples` for C1 and C2) at temperature 0.7 and top-p 0.95 plus one greedy row, capped at
`--max-new-tokens`, each seeded per row. The greedy row also carries the Readout record: the six teacher-forced
stem distributions in fp32 and the in-job P1 and P2 margins. Helpers and the full contract are in
`spontaneous/generate.py`; the row schema is `spontaneous/rows.py`.

Outputs in `--out`: `rows.jsonl` (base), `rows_c1.jsonl` and `rows_c2.jsonl` (controls), `summary.json` and
`run_manifest.json` (40-hex `git_commit`). Sampled rows are appended as they are generated and greedy rows after the stem pass; an existing row file
stops the run before the model loads. `--dry-run` loads no model: it tokenizes every prompt with the cached
tokenizer, checks every twin pair, and writes only `dry_run_plan.json` with the counts and a walltime estimate.

    scripts/jobs/run_b3_generate.sh --variant both --split calibration --controls base --out DIR
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import run_manifest  # noqa: E402
from spontaneous import af_prompts  # noqa: E402
from spontaneous import generate as G  # noqa: E402
from spontaneous import proxy as px  # noqa: E402

QUERIES_PATH = ROOT / "data" / "b3" / "af_queries.json"
PROMPT_FILES = [af_prompts.PROMPTS_DIR / n for n in
                ("v_a_system.txt", "v_a_controls.json", "v_b_system.txt", "v_b_controls.json")]


def load_tokenizer():
    return af_prompts.load_cached_tokenizer()


def load_model(model_id):
    from component_analysis import hooks
    return hooks.load_analysis_model(model_id, device="cuda")


def head_commit_from_files(root=ROOT):
    """HEAD's commit read from the git files without a subprocess (Lustre can hang git); None when unreadable."""
    try:
        dotgit = Path(root) / ".git"
        gitdir = dotgit
        if dotgit.is_file():
            gitdir = Path(dotgit.read_text().split("gitdir:", 1)[1].strip())
            if not gitdir.is_absolute():
                gitdir = (Path(root) / gitdir).resolve()
        head = (gitdir / "HEAD").read_text().strip()
        if not head.startswith("ref:"):
            return head if len(head) == 40 else None
        ref = head[4:].strip()
        common = gitdir
        if (gitdir / "commondir").is_file():
            common = (gitdir / (gitdir / "commondir").read_text().strip()).resolve()
        for base in (gitdir, common):
            if (base / ref).is_file():
                return (base / ref).read_text().strip()
        for line in (common / "packed-refs").read_text().splitlines():
            if line.endswith(" " + ref):
                return line.split()[0]
    except (OSError, IndexError):
        return None
    return None


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--variant", choices=sorted(G.VARIANT_FLAGS), required=True)
    p.add_argument("--split", choices=["calibration", "test"], required=True)
    p.add_argument("--controls", default="base", help="comma list of base, c1, c2")
    p.add_argument("--samples", type=int, default=10)
    p.add_argument("--control-samples", type=int, default=None,
                   help="sampled rows per C1 or C2 context; default --samples")
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--max-new-tokens", type=int, default=512)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--max-queries", type=int, default=None)
    a = p.parse_args(argv)
    names = [c.strip() for c in a.controls.split(",") if c.strip()]
    bad = [c for c in names if c not in G.CONTROL_FLAGS]
    if bad or not names or len(set(names)) != len(names):
        p.error("--controls takes a comma list of distinct base, c1, c2; got %r" % a.controls)
    a.control_list = [G.CONTROL_FLAGS[c] for c in names]
    if a.control_samples is None:
        a.control_samples = a.samples
    return a


def load_queries(split, max_queries=None):
    items = json.loads(Path(QUERIES_PATH).read_text(encoding="utf-8"))[split]
    return items[:max_queries] if max_queries else items


def _print_plan(plan, args):
    print("B3 generation plan: split %s, variants %s, controls %s" % (
        args.split, ",".join(G.VARIANT_FLAGS[args.variant]), ",".join(c or "base" for c in args.control_list)))
    for v, s in sorted(plan["prompt_tokens"].items()):
        print("  %s prompt tokens: min %d, mean %.1f, max %d" % (v, s["min"], s["mean"], s["max"]))
    print("  contexts %d, twin pairs checked %d" % (plan["contexts"], plan["twin_pairs_checked"]))
    g = plan["generations"]
    print("  generations %d (sampled %d, greedy %d) in %d batches; by control %s" % (
        g["total"], g["sampled"], g["greedy"], plan["generation_batches"], plan["generations_by_control"]))
    print("  teacher-forced forwards %d" % plan["teacher_forced_forwards"])
    w = plan["walltime_estimate_s"]
    print("  walltime estimate (A100) %.0f s = %.2f h: load %.0f, prefill %.0f, decode %.0f, stems %.0f" % (
        w["total"], w["total"] / 3600, w["load"], w["prefill"], w["decode"], w["teacher_forced"]))


def main(argv=None):
    args = parse_args(argv)
    out = Path(args.out)
    tokenizer = load_tokenizer()
    queries = load_queries(args.split, args.max_queries)
    variants = G.VARIANT_FLAGS[args.variant]
    contexts = G.build_contexts(tokenizer, queries, args.split, variants, args.control_list)
    jobs = G.plan_jobs(contexts, args.samples, args.control_samples, args.seed)
    tokens = px.load_proxy_tokens()
    res = px.resolve_tokens(tokens, tokenizer)
    plan = G.dry_run_plan(contexts, jobs, res.stem_paths, batch_size=args.batch_size,
                          max_new_tokens=args.max_new_tokens)
    plan["argv"] = list(sys.argv if argv is None else argv)
    _print_plan(plan, args)

    if args.dry_run:
        out.mkdir(parents=True, exist_ok=True)
        (out / "dry_run_plan.json").write_text(json.dumps(plan, indent=1) + "\n")
        print("dry run: wrote %s; no model loaded" % (out / "dry_run_plan.json"))
        return 0

    files = {c: out / G.row_file_name(c) for c in args.control_list}
    existing = [str(f) for f in files.values() if f.exists()]
    if existing:
        sys.exit("refusing to overwrite existing rows: %s" % ", ".join(existing))
    out.mkdir(parents=True, exist_ok=True)
    tokens_sha = run_manifest.file_sha256(str(px.TOKENS_PATH))
    commit = None
    try:
        mpath = run_manifest.write_run_manifest(
            str(out), script=os.path.abspath(__file__), argv=plan["argv"],
            dataset_files=[str(QUERIES_PATH), str(px.TOKENS_PATH)] + [str(p) for p in PROMPT_FILES],
            model=af_prompts.MODEL_ID, seed=args.seed,
            code_files=[str(ROOT / "spontaneous" / n) for n in ("generate.py", "af_prompts.py", "proxy.py",
                                                                 "rows.py")])
        commit = json.loads(Path(mpath).read_text())["git_commit"]
        if not (isinstance(commit, str) and len(commit) == 40):
            print("WARNING: run manifest has no 40-hex git_commit (%r); summary.json records HEAD from the files"
                  % commit, file=sys.stderr)
    except Exception as exc:  # noqa: BLE001 - provenance must not stop the run
        print("WARNING: run manifest not written: %r" % exc, file=sys.stderr)

    t0 = time.time()
    model = load_model(af_prompts.MODEL_ID)
    from component_analysis import hooks
    from evaluation import gen_engine
    hf = hooks._hf(model)
    gen_engine.assert_rope_is_offset_invariant(hf.config)  # left-padded batches equal their rows run alone
    load_s = time.time() - t0
    vocab = int(hf.config.vocab_size)
    eos = hf.generation_config.eos_token_id
    eos_ids = [int(e) for e in (eos if isinstance(eos, (list, tuple)) else [eos])]
    pad_id = tokenizer.pad_token_id if getattr(tokenizer, "pad_token_id", None) is not None else eos_ids[0]
    r1_basis = "calibrated" if tokens.r1 is not None else "seed"

    first_ids = set()
    greedy_rows = {}
    counts = {}
    handles = {c: open(f, "a", encoding="utf-8") for c, f in files.items()}

    def emit(row):
        G.rw.validate_row(row)
        handles[row["control"]].write(json.dumps(row) + "\n")
        handles[row["control"]].flush()
        key = row["control"] or "base"
        counts[key] = counts.get(key, 0) + 1

    t1 = time.time()
    try:
        # Phase 1: every row. Sampled rows are written at once; greedy rows wait for their Readout record, whose
        # prompt-alone stem must list every first token of the run (rows.py), known only when generation ends.
        for chunk in G.batches(jobs, args.batch_size):
            gens = G.generate_batch(hf, [contexts[j.context].prompt_ids for j in chunk],
                                    [None if j.sample == G.GREEDY else j.seed for j in chunk],
                                    temperature=args.temperature, top_p=args.top_p,
                                    max_new_tokens=args.max_new_tokens, pad_id=pad_id, eos_ids=eos_ids)
            for j, gen in zip(chunk, gens):
                row = G.assemble_row(contexts[j.context], j, gen, tokenizer, vocab, temperature=args.temperature,
                                     top_p=args.top_p)
                if row["first_token_id"] is not None:
                    first_ids.add(row["first_token_id"])
                if j.sample == G.GREEDY:
                    greedy_rows[j.context] = row
                else:
                    emit(row)
        gen_s = time.time() - t1
        # Phase 2: the six teacher-forced stems of every context, batched, then the greedy rows.
        n = len(res.stem_paths)
        per_batch = max(1, args.batch_size // n)
        order = sorted(greedy_rows)
        for group in G.batches(order, per_batch):
            seqs = [contexts[i].prompt_ids + list(p) for i in group for p in res.stem_paths]
            lps = G.teacher_forced_logprobs(model, seqs, batch_size=args.batch_size, pad_id=pad_id)
            for k, i in enumerate(group):
                dense = dict(zip(res.stem_paths, lps[k * n:(k + 1) * n]))
                row = G.attach_readout(greedy_rows.pop(i), G.sparse_stems(dense, res, extra_ids=first_ids),
                                       G.margins(dense, res), r1_basis=r1_basis, tokens_sha256=tokens_sha,
                                       readout_argmax=int(dense[()].argmax()))
                emit(row)
    finally:
        for h in handles.values():
            h.close()

    summary = {"rows": counts, "model_load_s": load_s, "generation_s": gen_s,
               "teacher_forced_s": time.time() - t1 - gen_s, "first_token_ids_seen": len(first_ids),
               "contexts": len(contexts), "plan": plan, "manifest_git_commit": commit,
               "git_commit_from_files": head_commit_from_files(), "describe": hooks.describe(model)}
    (out / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print("wrote %s rows to %s in %.0f s" % (counts, out, time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
