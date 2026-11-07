# Task3 correction report: native fixture identity

Agent: Sol implementation worker. Status: handed-back for root source review and complete Slurm CPU validation.

## What changed

The cause is an incomplete test fixture. The native-chain test reused the budget-only `budget_fixture` config, which omits `groups_file_sha256`. The unchanged producer requires that field to construct the same source/G3/MAIN identity used by the accepted GPU caller. The actual failure occurs before the original native normalizer is called. The source-only [diagnosis](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-correction286/diagnosis.json) reproduces that missing-key access and records the mandatory field in the frozen GPU contract.

The distinct [corrected fixture](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-correction286/candidate-r4/tests/test_full_score_root_integration.py) reads the real frozen GPU template's source commit, raw G3 hash and MAIN path. It checks the actual G3 raw-file SHA, aligns only the owned synthetic ledger row and matching mapping entry to that MAIN before writing temporary snapshots, and asserts the normalizer returns the exact expected identity. No actual canonical ledger, MAIN output, admission or mapping is written.

Only one copied test file changes. All five parameter routes and seven existing native assertions remain; three identity assertions bring the native assertion count to ten. Production helper, CPU/GPU sources, the other cases, old candidate, previous packets, review evidence and raw failed-job data remain unchanged. See the [correction manifest](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-correction286/correction-manifest.json) and [fixture diff](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-correction286/fixture.patch).

Final packet: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r4`. Packet pins SHA256 `5cb997b946a30b1fccf2eec5c847e1caaee6251bbceb392979927e5f918fdd4e`; original-source pins SHA256 `af997a7cde132dbf5807e4f05e10a47352b5135ca1f3b084963c70047d469155`. The unchanged helper retains SHA256 `522e6c9a87aaa041a2d63fb3218dd3637791ab859182d8619bc0a4ec0956d085`.

## How verified

```bash
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-correction286/diagnose_fixture.py
```

Observed: source-only reproduction of the original missing `groups_file_sha256` key; the actual G3 raw-file hash equals the frozen template's `c309` hash. The probe extracts and executes only the tiny budget fixture's AST in a standard-library namespace. It imports no production or native module and runs no pytest case. Evidence: [diagnosis](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-correction286/diagnosis.json).

```bash
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-correction286/check_corrected_identity.py
/u/swong2/.conda/envs/mgnp/bin/python -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-correction286/check_corrected_identity.py
```

Observed: the isolated corrected identity statements and unchanged production identity expression agree in each supported interpreter. These are standard-library/source-AST checks, not native test results. Evidence: [BASE identity replay](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-correction286/identity-replay-base39.json) and [mgnp identity replay](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-correction286/identity-replay-mgnp.json).

```bash
bash -n /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r4/run_cpu.sh
bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r4/run_cpu.sh --dry-run --output /tmp/a2-task3-r4-unused
```

Observed: shell syntax, source hashes, packet ASTs and ordinary argument dry-run pass. A wrapper copied to a Slurm-spool-style temporary path also resolves the same absolute packet without executing tests. Evidence: [relocated dry-run](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-correction286/relocated-dry-run.json). All original assertions and five routes are retained by AST comparison; production bytes match the prior packet, as recorded in the [correction manifest](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-correction286/correction-manifest.json).

## Execution evidence

- Prior root-owned job: `23632112`, Delta. It failed with exit `1:0`; this remains failed evidence. Raw provenance: [prior run manifest](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-deployment275/run-01/run_manifest.json), original scientific commit `50e947bb852613e3a270082651f2bd1b7bb0c525`.
- Prior baseline reproduces in both normal interpreters: 98 cases, 61 intended failures and 37 passes, with zero errors/skips. Prior GREEN observed 379 cases, 374 passes and five failures, with zero errors/skips. All five failures are the same missing-field seam, before native normalization. See [actual failed result](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-deployment275/run-01/RESULT.json) and [preserved failures](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-failure286/observed-failures.json).
- Correction checks: no worker-submitted job and no local pytest/native run. Source-only replay and wrapper dry-runs exited zero. They do not establish corrected GREEN. The final observer will create its own `run_manifest.json`, actual job environment, identities, logs, XML and result when root runs it.

## What is NOT done

No corrected complete or native GREEN result is claimed. Root reports that independent review `288` accepted fixture-only source readiness and that corrected CPU job `23635594` was submitted and released. The worker has not queried that job or received its result. Root owns complete Slurm CPU validation and acceptance. Production behavior, interfaces and validation checks are unchanged; no broad catch, default hash, relaxed assertion, case removal or scoring/admission change was introduced.

No Git, scheduler, SSH, RS mutation, actual model work or protected scoring occurred. The real source/G3/MAIN and canonical ledger remain read-only. Timing/control acceptance elsewhere does not waive this native gate.

## Open questions

No production/design issue was found at this seam. Root has reported dispatch of the frozen successor; the next step is root result review. The same CPU fixture request is retained, `2 CPUs / 8 GiB / 7 minutes / zero GPUs`. It preserves the complete expected RED98 and GREEN379 counts and the normal supported interpreter observer without `-I`. Resources and gate counts are retained in [resources](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r4/resources.json).

```bash
bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r4/run_cpu.sh --output /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-correction286/root-run-r4-01
```

Root owns submission, independent review, source acceptance and any later publication or model admission. The correction and previous failed packets remain separate and immutable.
