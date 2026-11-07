# Hand-back 288: Task 3 fixture identity correction review

Agent: independent reviewer, gpt-6.1-sol. Ticket: fixture-only correction286 and sealed GREEN270-r4. Status: resolved for bounded complete CPU validation readiness only.

## What changed

**Verdict: READY for bounded complete CPU validation. No blocking spec or quality finding.** This is not Task 3 acceptance or GPU permission. No r4 native test result is claimed.

Only `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-correction-review288/checks.py`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-correction-review288/checks.json` and `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/288-handback.md` were written. No source, Git, RS, scheduler, remote, authority or real ledger/MAIN writes occurred. Author narrative was not read. Root should lint this handback centrally under the worker RS prohibition.

All five failures in each actual r3 environment occur at `collect_native_closure` while reading the missing `groups_file_sha256`, before original native normalization begins. The reused `budget_fixture` supplies arithmetic fields and `/fixture/MAIN`, not a complete native scoring identity (`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r4/closure/sdd/plan-a2-full-score-operational186/candidate/tests/test_full_score_release.py:161`). Real GPU config/common contracts require the actual group raw-file SHA and original MAIN (`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r4/closure/sdd/plan-a2-full-score-operational186/candidate/gpu/common.py:302`, `:385`, `:415`). The correction supplies those existing contract fields rather than weakening production behavior.

The only candidate change is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r4/closure/sdd/plan-a2-full-score-operational186/candidate/tests/test_full_score_root_integration.py:274`: load the frozen real GPU template, assert source identity and actual raw group SHA, populate the test config, and align the new synthetic ledger row and matching mapping entry output before their snapshots are written. Ledger, mappings, admissions and snapshots are created under the test's `tmp_path`. Actual groups bytes are read for hashing; actual MAIN is only an identity string. No new code writes the real canonical ledger or MAIN. Existing `CANONICAL_LEDGER` routing still targets the fixture file.

The original native module import/origin assertion, original `normalize_ledger` implementation, COMPLETE origin/successor/admission construction, charge checks and all five damage variants remain. The helper's `native_runtime` seam returns the actual imported original module, not a replacement normalizer. All seven existing assertions remain verbatim in AST; three assertions add exact commit, raw hash and normalized identity checks. Exceptions are not broadened and no authority is invented. All other candidate files, including production helper SHA `522e6c9a87aaa041a2d63fb3218dd3637791ab859182d8619bc0a4ec0956d085`, are byte-identical to r3.

## How verified

Read raw JUnit failure text, corrected fixture diff, real GPU template/common identity checks, original native return contract, packet wrapper/runner/resources and preparation/probe source. No native module or test module was imported.

```bash
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-correction-review288/checks.py
```

Observed exit zero in approximately 1.35 seconds. All 552 packet members and 577 original-source references match their pins; supplied packet/original-pin digests match; only the integration fixture changes within the candidate; seven original assertions are preserved with ten total; parametrization is unchanged. Wrapper differs only by r4 packet location. Runner/resources are byte-identical to r3: normal BASE/mgnp interpreters, baseline 98 and complete GREEN 379 per environment, two CPUs/eight GiB/seven minutes, twenty-second baseline and 150-second complete per-environment bounds. Exact interpreter patch identities must still be inspected in the actual run logs. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-correction-review288/checks.json`.

## Execution evidence

Existing failed r3 evidence only; no new native run:

- Job/cluster: root-supplied Delta job 23632112; failed after 209 seconds. This worker did not query the scheduler.
- Exit/state: root reports FAILED; both actual GREEN JUnit files show five failures, 374 passes, zero errors/skips out of 379.
- Baseline reproduces: both actual RED JUnit files contain 61 failures plus 37 passes against the expected 98 cases. GREEN has the same five native-chain variants in both environments, each failing on the missing identity key.
- Provenance: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task3-deployment275/run-01/run_manifest.json`, root-supplied worktree commit `538109e809285b6ddc45d42df8786270a65f7b12`; raw environment RED/GREEN XML files in that directory. This review directly parsed those XML files. Corrected packet provenance is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r4/packet-pins.json`, digest `5cb997b946a30b1fccf2eec5c847e1caaee6251bbceb392979927e5f918fdd4e`, and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r4/original-source-pins.json`, digest `af997a7cde132dbf5807e4f05e10a47352b5135ca1f3b084963c70047d469155`.

## What is NOT done

No complete r4 CPU/native validation, Task 3 acceptance, source publication, real resource/authority binding, transfer or GPU execution. Static equality of test routes preserves the planned 379 count; it does not prove successful runtime collection or normalization. The prior 374 passes cannot substitute for complete r4 results.

Root's next gate is the whole sealed r4 packet on the declared CPU allocation, with attributable historical RED and all 379 GREEN cases in each normal supported environment, no errors/skips, complete provenance and original native-chain success/tamper rejection within bounds. Subsequent full-path operational timing/resource feasibility, actual placement, reader-safe completed reservation/successor transition, source/input/bank/protection closure, native budget normalization, fresh owning CPU proof, per-start cache/usage/allocation checks and once-only remote publication remain separate GPU admission gates.

## Open questions

None blocks bounded complete CPU validation. Default: root may run that validation promptly; preserve r3 failure evidence and keep Task 3 acceptance and GPU permission closed until their respective results are independently reviewed.
