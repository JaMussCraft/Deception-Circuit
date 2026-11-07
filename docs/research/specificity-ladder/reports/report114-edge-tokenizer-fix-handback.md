# Edge tokenizer factory candidate hand-back

Agent: Codex Sol. Status: handed-back. Candidate software only.

## What changed

The isolated candidate `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/edge-tokenizer-fix-source-v2/component_analysis/a3_edge_pipeline.py`
now calls `common.load_tokenizer` with the original model and pinned tokenizer revision,
replacing the raw `AutoTokenizer` factory. The canonical loader supplies EOS padding,
checks the cached revision and retains the existing offline compatibility handling.
The independent strict tokenizer signature guard remains unchanged.

The isolated candidate `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/edge-tokenizer-fix-source-v2/tests/test_a3_edge_pipeline.py`
adds real fast-tokenizer admission coverage and a deliberately changed padding-side
counterexample. The default fixture is local; the recorded pinned runs select the actual
cached model through environment variables. CPU producer replay is replaced at the
prepare boundary, while the tokenizer loader and strict validator remain real.

Source hashes and exact edits are recorded in
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/source-pre.json`,
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/source-post.json` and
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/candidate-diff.txt`.
The scope check found exactly the owned source and test files changed among 509 baseline
files: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/candidate-scope-check.json`.

## How verified

All commands below ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/edge-tokenizer-fix-source-v2` with the recorded single-thread,
o-bytecode, offline environment. Each JSON receipt contains its exact command,
environment, start time, elapsed time, exit code and raw log path.
The pinned test environment selects `meta-llama/Llama-3.1-8B-Instruct` at revision
`0e9e39f249a16976918f6564b8830bc894c89659`.

```bash
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider --basetemp=/tmp/a3-edge-114-red-pinned-mgnp tests/test_a3_edge_pipeline.py -q -k parent_admission
```

Observed: 1 failed, 1 passed; the acceptance regression fails at the strict configuration-signature check.
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/red-pinned-mgnp.log`;
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/red-pinned-mgnp.json`.

```bash
/sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider --basetemp=/tmp/a3-edge-114-red-pinned-base tests/test_a3_edge_pipeline.py -q -k parent_admission
```

Observed: 2 failed; the original raw factory reaches the known Transformers offline model-info heuristic before signature validation. Offline mode blocks the request.
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/red-pinned-base.log`;
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/red-pinned-base.json`.

```bash
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider --basetemp=/tmp/a3-edge-114-green-pinned-mgnp tests/test_a3_edge_pipeline.py -q -k parent_admission
```

Observed: 2 passed, including the changed-padding-side rejection.
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/green-pinned-mgnp.log`;
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/green-pinned-mgnp.json`.

```bash
/sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider --basetemp=/tmp/a3-edge-114-green-pinned-base tests/test_a3_edge_pipeline.py -q -k parent_admission
```

Observed: 2 passed, including the changed-padding-side rejection.
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/green-pinned-base.log`;
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/green-pinned-base.json`.

```bash
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider --basetemp=/tmp/a3-edge-114-green-edge-mgnp tests/test_a3_edge_pipeline.py -q
```

Observed: 40 passed; complete affected edge pipeline test file.
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/green-edge-mgnp.log`;
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/green-edge-mgnp.json`.

```bash
/sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider --basetemp=/tmp/a3-edge-114-green-edge-base tests/test_a3_edge_pipeline.py -q
```

Observed: 40 passed with 3 dependency warnings concerning Transformers cache, TensorFlow ml_dtypes and pandas bottleneck.
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/green-edge-base.log`;
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/green-edge-base.json`.

```bash
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/pinned-tokenizer-check.py
```

Observed: exit 0; 30 sampled original parent prompt-stream token sequences match both raw snapshot and canonical loading; original tokenizer identity matches. Raw no-padding and changed-padding-side tokenizers are rejected.
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/direct-pinned-mgnp.log`;
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/direct-pinned-mgnp.json`.

```bash
/sw/external/python/anaconda3/bin/python3.9 /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/pinned-tokenizer-check.py
```

Observed: exit 0; 30 sampled original parent prompt-stream token sequences match both raw snapshot and canonical loading; original tokenizer identity matches. Raw no-padding and changed-padding-side tokenizers are rejected.
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/direct-pinned-base.log`;
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/direct-pinned-base.json`.

The earlier local synthetic regression also failed at the intended strict guard before
implementation: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/red-mgnp.log`.

## Execution evidence

- Job id and cluster: local CPU subprocesses only; no scheduler job or GPU cluster.
- Exit codes: the recorded red runs exit 1; all green tests and direct pinned checks exit 0. Raw command receipts are listed in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/run_manifest.json`.
- Row counts: each complete affected test file observed 40 passes against expected 40; each pinned pair observed 2 passes against expected 2; each direct source-prompt check observed 30 streams against expected 30. See `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/green-edge-mgnp.log`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/green-edge-base.log`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/green-pinned-mgnp.log`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/green-pinned-base.log`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/direct-pinned-mgnp.log`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/direct-pinned-base.log`.
- Baseline reproduces: the original recorded preparation and the new mgnp red regression both reject with `production tokenizer configuration differs from pinned standard`; the red pair observes 1 failing acceptance test against expected 1. See `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/red-pinned-mgnp.log` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-independent-pilots-74efb4d04819/evidence/edge-tokenizer-diagnosis.json`.
- Provenance file: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/114-edge-tokenizer-evidence/run_manifest.json`, baseline commit `74efb4d0481968a1d0138eb1a79b97f302fd3c3b`. This commit names the baseline only; the candidate is uncommitted and identified by its post-change hashes and diff.

## What is NOT done

The mutable candidate has not been accepted, frozen, prepared as actual edge source,
or published. Full production CPU source replay has not run from it. The tokenizer
checks sample the first row per task and available condition, both streams; they do not
constitute full-corpus preparation. No broader suite was run because the assigned testing
scope is the affected edge pipeline. Base dependency warnings remain recorded above.

No active worktree source, immutable runtime bundle, research-session state, jobs,
GPU work, large weights, paid APIs or notebooks were changed or used. No git command
was run. The report and evidence directory are mirrored into the primary checkout.

## Open questions

Independent review and successor source freezing belong to the orchestrator. Default:
retain this as a candidate and run actual preparation only from a separately reviewed,
frozen successor source. No scientific result or execution admission follows from these
software tests.
