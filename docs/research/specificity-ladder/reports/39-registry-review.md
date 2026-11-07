# Registry command review

Agent: Codex independent reviewer. Ticket: staged grader registry command. Status: handed-back.

## What changed

Recommendation: suitable to install through the approved apply tool. No blocking findings.

- Review report: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/39-registry-review.md`.
- Required handback copy: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/39-registry-review-handback.md`.
- Reviewed staging: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/grader-registry/ops/36-grader-registry.json`.
- No implementation, live registry, private session, usage, cadence, acknowledgement, or gate file was changed by this review.

The command requires an explicit nonempty session selector and accepts only exactly 64 lowercase hexadecimal characters. It resolves the selected existing session without cwd fallback or an impersonation option. The direction must be claimed or active and its owner tag must equal the selected session tag. A null or absent grader field accepts the initial hash; an identical retry succeeds; replacing an existing different hash fails. Count evidence: `/tmp/rs-freeze-independent-gfnf7i7w/review-evidence.json`.

The existing edit helper acquires the registry lock before loading, validates the current registry, applies only the selected row mutation, validates again, and writes atomically. Other row fields and other rows survive; normal registry and selected-row update dates may advance through that helper. The command does not inspect benchmark artifacts or establish scientific grader correctness; it freezes the supplied metadata hash as authorized by START. Count evidence: `/tmp/rs-freeze-independent-gfnf7i7w/review-evidence.json`.

The exact patch adds only the command and parser entry to the production module, plus five tests. It changes no existing command or hook. Tests cover both accepted statuses, explicit selection despite another same-cwd session, retries, bad hashes, missing or ambiguous selectors, rejected impersonation options, ownership/status conflicts, replacement, unknown directions, invalid registries, intervening edits, and preservation of existing fixture files.

## How verified

The staged package and test harness were copied to `/tmp/rs-freeze-independent-gfnf7i7w`, with templates copied there too. Fixture paths are temporary; token and HTTP readers are guarded by mocks. Tests use the copied package and synthetic session records.

```bash
PYTHONDONTWRITEBYTECODE=1 RESEARCH_SESSION_TEMPLATES=/tmp/rs-freeze-independent-gfnf7i7w/templates OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -B -m pytest -p no:cacheprovider -q /tmp/rs-freeze-independent-gfnf7i7w/tests/test_research_session_registry.py
```

Observed: 22 passed; exit 0. Count evidence: `/tmp/rs-freeze-independent-gfnf7i7w/review-evidence.json`.

```bash
PYTHONDONTWRITEBYTECODE=1 RESEARCH_SESSION_TEMPLATES=/tmp/rs-freeze-independent-gfnf7i7w/templates OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -B -m pytest -p no:cacheprovider -q /tmp/rs-freeze-independent-gfnf7i7w/tests/test_research_session_registry.py
```

Observed: 22 passed and 18 subtests passed; exit 0. Count evidence: `/tmp/rs-freeze-independent-gfnf7i7w/review-evidence.json`.

```bash
PYTHONDONTWRITEBYTECODE=1 /sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/apply_staged.py --staging /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/grader-registry --wave A --only 36 --dry-run
```

Observed: exactly two operations selected; both WOULD APPLY; exit 0. Production delta is 37 added lines, and test delta is 101 added lines. Count evidence: `/tmp/rs-freeze-independent-gfnf7i7w/review-evidence.json`.

An independent Python comparison also computed both live SHA-256 values, asserted equality with both the preimage file and operation guards, and regenerated the exact unified diff from live originals to staged files. All assertions passed, including a final recheck before report creation. The source guard mechanism rejects changed destinations before writing, and resolves sources inside staging. No installation was invoked. Count evidence: `/tmp/rs-freeze-independent-gfnf7i7w/review-evidence.json`.

## Execution evidence

- Local CPU checks only: both pytest commands above exited 0 and collected 22 tests each; the installer dry run exited 0 and selected 2 of 2 expected operations. Count evidence: `/tmp/rs-freeze-independent-gfnf7i7w/review-evidence.json`.
- Registry preimages: production `7c2b29370d405a3c64578b62ba8b11837bf71a0b7b9c75fd2bf90afb7fffc0f6`; tests `13c923e2c8f3cb2bc34293b7e2c79f75506a20309e372a705413c26f1c044072`.
- Scientific job, row counts, baseline reproduction, and scientific run manifest: not applicable; no scientific run was performed or claimed.
- Weekly usage at handback: 12 percent spent, 88 percent remaining, below the 80 percent cap; reset reported as 2026-11-06T16:07:41+00:00. Count evidence: `/tmp/rs-freeze-independent-gfnf7i7w/review-evidence.json`.

## What is NOT done

No installation or live freeze command was executed. No scientific result was assessed. No GPU, API, notebook, git, or subagent work occurred. The author report was not read. Parent confirmed the startup synchronizer had already run through the launcher.

## Open questions

None blocking. Default: the orchestrator installs the reviewed operation manifest using the approved tool, which rechecks destination preimages, then uses the explicit intended session selector for the metadata freeze. A later source change requires a new diff review rather than an unguarded overwrite.
