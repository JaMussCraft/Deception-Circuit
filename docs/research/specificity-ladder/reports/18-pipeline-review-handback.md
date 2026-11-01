# Hand-back 18: A1 staged pipeline independent review

Agent: Codex Sol reviewer. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a1.md`, Task 3. Status: resolved. No remaining code-review blocker to a registered Delta scoring pilot, subject to the orchestrator committing code and reserving its budget.

## What changed

Review only; no production code edits. Report is mirrored to the primary checkout and worktree at `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/18-pipeline-review-handback.md` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/18-pipeline-review-handback.md`.

One pilot blocker found in the reviewed initial wrapper: its dry run printed the supplied scoring command but executed only `--help`, accepting unknown flags and nonexistent revisions. It also bypassed the actual cluster environment activation. This blocker is now closed: the corrected shell exercises real cluster activation and CLI CPU preflight; direct reviewer execution passed. The subsequent base Transformers 4.57.3 tokenizer offline-loading issue is also corrected: that exact version resolves the pinned cached snapshot and loads it by local path to bypass its unrelated online Mistral heuristic. Canonical identity, actual revision, physical load path, normalization reason and tokenizer-config digest are retained in provenance. The final focused tests pass in both interpreters.

No other substantive blocker found by direct inspection of the staged pipeline, constructor/scorer helpers, native loader and fixed A2 consumer. Derive/score/assemble are separate and immutable, fallback assembly reuses scores into a distinct root, partial pilots cannot assemble, and stale source/request/prompt hashes, reordered/duplicate ids and within-task cross-split contamination fail. The native scoring closure shares one loaded model across task/split loops, uses native BF16 scoring and checks every prompt length before the reused scorer's truncating encoder. Original D labels orient both arms' scores while baseline rows inherit H labels. Baseline competence remains diagnostic. Self-contained identical receipts and score files serve the actual A2 validator.

Protected ids are refreshed from primary and worktree registries immediately before the model loader, including original source ids rather than only accepted rows. Derive/assemble do not load a model. Native scoring requires Slurm and CUDA, checks pinned local cache shards, then loads that local snapshot. The primary registry's absolute path means a Bridges-2 deployment needs an authoritative accessible copy; absent files fail closed. This does not block the proposed Delta pilot.

## How verified

Read the binding START, specification, plan including Task 3 integration rulings and scored-data contract, plus the actual implementation and its focused tests. No implementation report narrative was used as evidence.

```bash
bash scripts/jobs/specificity_user_inversion.sh --dry-run --unknown-option --model-revision nonexistent --tokenizer-revision nonexistent --work-dir /tmp/absent-specificity-pipeline-review
```

Observed in the original wrapper: exit 0 and a printed scoring command, demonstrating the preflight gap. No model or scoring output was created.

```bash
/sw/external/python/anaconda3/bin/python3.9 - <<'PY'
import json
from pathlib import Path
root=Path('outputs/_analyses/specificity-ladder/user-control-cpu')
for task in ('far_v2','sdr_v2','ser_v2'):
    for split in ('train','validation','test'):
        directory=root/task/split
        report=json.loads((directory/'derivation_report.json').read_text())
        manifest=json.loads((directory/'derivation_manifest.json').read_text())
        rows=[json.loads(line) for line in (directory/'pairs.jsonl').read_text().splitlines()]
        print(task,split,report['source_count'],len(rows),len(report['rejected']),manifest['tokenizer_revision'])
PY
```

Observed: each task has 200/200/1000 source and derived rows, zero rejections, totaling 4200 rows. All nine manifests name tokenizer revision `0e9e39f249a16976918f6564b8830bc894c89659`. These precommit CPU artifacts are diagnostic derivations, not measured behavioral pools.

Corrected wrapper recheck:

```bash
bash scripts/jobs/specificity_user_inversion.sh --dry-run --tasks far_v2 sdr_v2 ser_v2 --splits test --limit 32 --work-dir outputs/_analyses/specificity-ladder/user-control-cpu --score-dir /tmp/specificity-review-score-plan --commit aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa --model-revision 0e9e39f249a16976918f6564b8830bc894c89659 --tokenizer-revision 0e9e39f249a16976918f6564b8830bc894c89659
```

Observed: exit 0 through default activation into `/u/swong2/.conda/envs/mgnp/bin/python`. CPU preflight reports all three tasks at 32 rows and 128 primary forwards apiece, both authoritative registry hashes, the pinned local snapshot, `model_loaded=false` and `writes=false`. The score root did not exist afterward. The placeholder commit above is a syntax-only CPU preflight value, never a scoring provenance claim.

```bash
DC_PYTHON=/sw/external/python/anaconda3/bin/python3.9 bash scripts/jobs/specificity_user_inversion.sh --dry-run --unknown-option
```

Observed: exit 2, unrecognized argument. The original acceptance gap is closed.

Final compatibility review and direct log inspection:

```bash
tail -n 8 /tmp/a1-pipeline-base-final.log /tmp/a1-pipeline-mgnp-final.log
```

Observed: base final owned tests `18 passed, 2 warnings in 32.19s`; mgnp final owned tests `18 passed in 31.36s`. These logs cover `tests/test_user_inversion_pipeline.py` and `tests/test_user_inversion_job.py`; the reviewer inspected logs rather than rerunning those suites. The added test rejects use of the canonical identifier on mocked Transformers 4.57.3 and requires local-only snapshot resolution plus normalized provenance. The actual wrapper subprocess test exercises the real cached tokenizer in addition to injected scorer tests, including the fixed A2 consumer round trip.

## Execution evidence

- Job id and cluster: local CPU dry-run defect reproduction and artifact inspection only; no Slurm job.
- Exit code or Slurm state: artifact inspection, original defect reproduction and corrected default-activation preflight exited 0; corrected invalid-argument preflight exited 2 as expected.
- Row counts: inspected nine derivation scopes; 4200 observed against 4200 source rows, zero rejections.
- Baseline reproduces: not measured; no model inference was run by this reviewer.
- Provenance file: nine diagnostic `derivation_manifest.json` files under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/user-control-cpu`; no scored run manifest or scoring commit exists for this review.

## What is NOT done

No GPU, API, notebook, git, broad repeated test run or production edit. The worker reports the earlier surrounding 117 focused tests passing in both interpreters. Reviewer directly read final owned-test logs: 18 passing in each interpreter after the dry-run and compatibility corrections. Full score validity and native baseline reproduction remain the bounded pilot's job. No pool-size or specificity verdict follows from CPU derivation.

## Open questions

No remaining review question blocks the bounded Delta pilot. Default: use the committed, supplied full source commit, registered budget reservation and immutable fresh score root; keep the existing CPU artifacts diagnostic. Pilot native repeat agreement, runtime, peak memory and pool behavior remain empirical acceptance checks before full scoring.
