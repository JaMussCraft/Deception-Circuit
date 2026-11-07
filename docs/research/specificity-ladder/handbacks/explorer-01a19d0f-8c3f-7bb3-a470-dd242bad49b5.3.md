# Last message of explorer 01a19d0f-8c3f-7bb3-a470-dd242bad49b5 (2026-11-02T11:44:07-05:00)

The bundle approach works with the inspected paths. I found no source-git-revision lookup on canonical preparation or edge/mask M1. The mask model’s `_commit_hash` check concerns the pinned Hugging Face model revision. Root must independently establish that the candidate commit matches exported source bytes.

Let:

- `W=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`
- `P=/projects/beto/swong2/Alignment/Deception-Circuit`
- `B=W/outputs/_analyses/specificity-ladder/a3-runtime-CANDIDATE/runtime`

Export ordinary immutable files from the candidate commit into `B`:

| Bundle content | Reason |
|---|---|
| Complete `component_analysis/`, `dataset/`, `evaluation/`, `models/`, `tasks/`, `scripts/`, `tests/`; all root Python files | Complete local imports and declared source closure. Include tests because edge `code_hashes()` explicitly hashes `tests/test_a3_edges.py`. |
| All noncode files within those directories | In particular `dataset/names.json`, JSON pools, user-inversion requests, job configuration JSON and both cluster `.env` files. |
| `docs/research/specificity-ladder/a3-edge-operational-ruling.json` | Edge reads this exact bundle-relative location. |
| `docs/research/specificity-ladder/a3-mask-operational-ruling.json` and `a3-mask-pilot-ruling.json` | Mask reads both exact locations and checks the pilot ruling’s parent hash. |

Do not retain source symlinks or import fallbacks into `W`. A2’s existing 207-file manifest demonstrates the pattern but is not an A3 source whitelist. Its dependency count/archive hash must not be reused.

Use these **input mappings**:

| Bundle path or argument | Target |
|---|---|
| `B/data` | Symlink to `W/data`. |
| `B/outputs/_analyses/specificity-ladder/a1-control-77b6487-m07` | Symlink to the same directory under `W`. Keep the containing bundle directories ordinary directories. |
| `--a1-design` | `W/outputs/_analyses/specificity-ladder/ladder-5f450dc/design.json` |
| `--a1-selected` | Adjacent original `selected.json`; its adjacent completion sidecar remains mandatory. |
| `--matched-root` | `W/outputs/_analyses/specificity-ladder/a2-matched-77b6487-m07` |
| `--historical-csv` | `W/docs/research/mechanism-analysis/phase3/a_prime.csv` |

The two input symlinks have a substantive purpose: CLI preparation defaults `a1_repo_root` to `B`, and `_matched_rows` compares **resolved paths** against the matched manifest’s original absolute source paths. Copying identical dataset/control bytes under new bundle paths would fail that comparison. These links preserve original resolution.

The data mapping covers FAR/SDR/SER source, honest and nopressure datasets. The control mapping covers all six user-inversion/user-neutral roots and their scoring/assembly ancestry. Existing absolute A1 references under primary mechanism-analysis locations remain untouched.

Create new canonical design and consumer outputs **outside immutable `B`**, at new roots under `W/outputs/...`. Canonical direction preparation requires `--design D/design.json --work-dir D`; edge/mask can reference that design while using separate output roots matching their reservations. A whole `B/outputs -> W/outputs` alias is unnecessary.

For registries and grader:

- `B/docs/research/directions.json` may link to `W/docs/research/directions.json`; the grader guard separately reads `P/docs/research/directions.json`. Both must retain the original frozen grader entry.
- `B/docs/research/held_out.json` may link to the current `W/docs/research/held_out.json`. Pass explicit `--registry W/docs/research/held_out.json` on preparation and consumer invocations so the original active-worktree registry is explicitly unioned with primary and bundle defaults.
- Both current registries contain zero sets. If future entries use `"path"`, the bundle-default registry resolves those paths against **`B`**, even when its JSON file is a symlink. Referenced ID files must resolve inside `B`; copying those protected ID files into their bundle-relative locations preserves containment. External symlinks would fail closed. The explicit original-worktree registry is independently checked against `W`.
- Keep grader **source immutable inside `B`**. `grader_sha256(root=B)` covers every `evaluation/benchmarks/*.py` plus `evaluation/benchmark_eval.py`; do not link those files to live source.
- The live canonical ledger remains fixed at `P/docs/research/specificity-ladder/ledger.json`. Root mappings/admissions/reservations can remain external immutable operational artifacts.

For mask interpreter/profile binding:

- Launch `B/scripts/jobs/specificity_a3_mask.sh` with `SPECIFICITY_A3_MASK_REPO_ROOT=B`, and later use Slurm `--chdir=B`.
- Set `A3_MASK_PYTHON=/u/swong2/.conda/envs/mgnp/bin/python` consistently for mask preparation and execution through the wrapper.
- `mask_code_hashes()` binds absolute **`B/...` source paths**, both **`B/scripts/cluster/{delta,bridges2}.env`**, resolved `sys.executable`, and the wrapper’s resolved `SPECIFICITY_A3_MASK_LAUNCH_EXECUTABLE`. Moving the bundle or changing launcher convention afterward changes identity.
- The completed root execution bundle may live externally. Mask preparation binds its completed byte reference, canonical design-file hash, candidate commit and numeric profile. It does not replace the source `.env` files.
- Delta’s mask wrapper sets `HF_HOME`, `HF_HUB_CACHE`, and `TRANSFORMERS_CACHE` to `/work/nvme/beto/swong2`; canonical/edge wrappers have different cache initialization details. Preserve the existing locally cached tokenizer/model/MMLU snapshots and their resolved identities rather than relocating them.
- Edge can use `SPECIFICITY_A3_EDGE_REPO_ROOT=B`; canonical wrapper can use `A3_REPO_ROOT=B`. Ensure module resolution starts in `B`, with no inherited `PYTHONPATH` pointing to active source.

These findings establish the path layout only. Current frozen source still needs independent scoped acceptance and all original preparation/admission checks before pilots. No edits, git, jobs, weights or report-write retries occurred.
