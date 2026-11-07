# Hand-back 181-r2: native A2 shape corrections

Agent: worker. Status: handed-back. Independent review is required before execution.

## What changed

New successor `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-plan178/full-shape-cpu181-r2`. Manifest SHA-256 `71af5046b4701991fd3d444f1fb70c9e03304a5b2d723363757579877be8fa97`; `shape.py` SHA-256 `b30a79cbaac9d62b7d825dc810e3b57cb1f82591bb4a7b0b736aa7e3b9385fd9`. Original 181 manifest `7e3f46a554fd558bcaf7ea085d7d85ad1b5b697ee023b3ce69aed36a41384503` and every member remain intact.

Utility recipients use explicit batch 8 and donors use the actual omitted `task_batches` argument, with an assertion that the frozen native default is 16. Singleton views retain parent width. The actual frozen `_map_index` filters maps by operation; that native behavior is retained, including utility calls. For every recipient and operation the proof accounts for one intact capture, optional supported donor capture, two control captures per unique compute group and a patched capture per group only when the selected mapping is supported. Output aliases expand row keys, not compute captures.

The successor reconstructs complete output keys and compares them exactly with native `expected_keys`; it independently reconstructs calibration keys and compares with native `positive_keys`. It hashes the full row-key/support/reason mapping and records aggregate support coverage, preserving unsupported rows. Assessment and IOI calibration use the native forced-supported readout-only mappings; MMLU retains its existing readout map. Calibration checks singleton readout positions and uses the greater recipient/donor parent width. The proof checks actual allocation/user/node/resources/working directory and all project module origins. Delta filesystem availability is explicitly labeled Delta, not Bridges.

## How verified

The mgnp `red_native_original.py` fixture applies the original proof's explicit utility donor batch size 8 to actual native `task_batches`/`_rows`; it exited 1 with an assertion failure: observed singleton width 2 versus expected native default-16 width 9. This is a semantic RED for the reviewed batching error; the earlier packet's missing-module log was only a setup failure.

The following ran locally in r2:

```bash
PYTHONDONTWRITEBYTECODE=1 /sw/external/python/anaconda3/bin/python3.9 -m unittest -v test_native_seams test_shape
```

```bash
PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python -m unittest -v test_native_seams test_shape
```

Both exited 0 with 6 tests. Native-seam fixtures cover recipient8/donor16 padding, native operation filtering, unsupported mapping capture counts including a zero-operation mapping, forced-supported calibration and paired width/readout checks. Both interpreters parsed all packet Python files; `bash -n run.sh` passed. Logs are retained in the successor. Tests use tiny synthetic data, no model and no real source data.

## Execution evidence

Local pure tests only: the native batching RED exited 1 with one expected failure, and both GREEN interpreters exited 0 with six tests each. No Slurm job, scientific rows, numerical baseline, model or genuine proof run. The successor manifest pins the proof files and the inherited request; frozen scientific source is commit `50e947bb852613e3a270082651f2bd1b7bb0c525`.

## What is NOT done

No real-data CPU execution, scheduler action, RS writes, git, SSH, model/forward/score, effect reading or source/bank edits. Key-domain equality, exact support digest and resource outcomes are code paths to be independently reviewed and executed, not observed full-data results. No GPU memory, serialized output, runtime or full-score admission bound is established.

## Open questions

Review exact map and calibration handling, group aliases, key-domain construction and allocation checks against the unchanged native source before root's dry-run and CPU request. The packet remains a proposal and must stop on any discrepancy.
