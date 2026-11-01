# Clause-choice CPU postprocessing handoff

Preparation only as of 2026-10-26. Do not run the commands below until the lead explicitly releases export after **all 672 terminals** and the independent runtime audit reports a complete PASS. Do not inspect responses or labels during preparation. The frozen runner at commit `4f02784` is immutable.

The released protocol is `.scratch/sdr-clause-choice/freeze-final-4f02784.json`; the one retained run directory is `.scratch/sdr-clause-choice/operator/baseline-final-4f02784-001`. Use the mgnp Python interpreter for the runner's CPU-only `export` and `analyze` commands. No model load or GPU is needed for these commands.

## After explicit release: export and make the blind packet

Run from `/projects/beto/swong2/Alignment` with fresh output paths:

```bash
PY=/u/swong2/.conda/envs/mgnp/bin/python
RUNNER=Deception-Circuit/.claude/worktrees/sdr-routing-pilot/scripts/sdr_clause_choice.py
PROTOCOL=.scratch/sdr-clause-choice/freeze-final-4f02784.json
RUN_DIR=.scratch/sdr-clause-choice/operator/baseline-final-4f02784-001
POST=.scratch/sdr-clause-choice/postprocessing

"$PY" "$RUNNER" export --protocol "$PROTOCOL" --run-dir "$RUN_DIR" --output "$POST/actual-export-4f02784"
"$PY" "$POST/prepare.py" packet --protocol "$PROTOCOL" --views "$POST/actual-export-4f02784/views.json" --output "$POST/blind-packet-4f02784"
```

Give each of two fresh independent raters **only** `blind-packet-4f02784/`. It contains `views.json` (opaque ID, exact question, lexical candidates, complete response, finish, protocol hash and view hash), frozen `rubric.md`, `response.schema.json`, and `README.txt`. Keep `actual-export-4f02784/private-archive.json`, the protocol, run directory, factors, targets, truth, masks, parser proposals and the other rater's labels private. Each rater personally reads every unique view and returns one full-tuple JSON artifact following the schema. A fresh third rater sees only the packet and personally rates exactly the disputed views if full tuples disagree.

## After full annotation resolution: analyze and adapt

The runner checks complete per-view coverage, distinct independent annotators, exact protocol/view hashes, label syntax and full-tuple agreement or adjudication. Use actual annotation paths for `FIRST`, `SECOND`, and optional `THIRD`:

```bash
FIRST=/absolute/path/to/first-rater.json
SECOND=/absolute/path/to/second-rater.json
"$PY" "$RUNNER" analyze --protocol "$PROTOCOL" --run-dir "$RUN_DIR" --first "$FIRST" --second "$SECOND" --output "$POST/actual-runner-analysis-4f02784.json"
```

If there are disputes, have the third rater judge exactly those IDs and rerun the command with `--adjudication /absolute/path/to/third-rater.json`, writing to a **fresh** analysis path. Do not alter the original ratings. The runner's analysis joins each resolved full tuple back to all 640 planned main IDs. Preflight rows remain excluded.

The thin adapter copies planned question and lexical candidates, raw complete text and finish, and the runner's resolved tuple into the independent oracle's input shape. It never judges response meaning. Its `numerical_pass` defaults to `false`. Only the lead may assert `--numerical-pass` after personally verifying a complete independent runtime PASS receipt for this manifest, 84 accepted batches, 672 unique rows, 640 main and 32 preflight, zero errors and zero missing batches:

```bash
"$PY" "$POST/prepare.py" normalize --protocol "$PROTOCOL" --archive "$POST/actual-export-4f02784/private-archive.json" --analysis "$POST/actual-runner-analysis-4f02784.json" --output "$POST/normalized-resolved-main640.json" --numerical-pass --runtime-pass-receipt /absolute/path/to/independent-runtime-pass.json
"$PY" .scratch/sdr-clause-choice/scientific-audit/oracle.py --labels "$POST/normalized-resolved-main640.json" --output .scratch/sdr-clause-choice/scientific-audit/actual-independent.json
```

The adapter writes a sidecar `.receipt.json` with input and output hashes. Without the explicit PASS assertion, omit both numerical arguments; the oracle can still produce descriptive counts while its numerical gate stays false. Preserve the frozen arithmetic oracle and its prospective receipt. Its output is an independent recomputation of the specified baseline gates, not a semantic annotation or GPU audit.

## Preparation check

```bash
/sw/external/python/anaconda3/bin/python3.9 .scratch/sdr-clause-choice/postprocessing/test_prepare.py
```

This uses synthetic rows only and does not read the retained run.
