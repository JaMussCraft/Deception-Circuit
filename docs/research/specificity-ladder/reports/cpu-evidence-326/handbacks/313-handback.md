# Hand-back 313: A2 correction312 source and CPU proposal review

Agent: independent source reviewer, gpt-6.1-sol. Ticket: A2 Task 4 fixture-only correction312. Status: resolved for bounded CPU diagnostic readiness only.

## What changed

**Verdict: SOURCE READY for a separate bounded root CPU validation attempt at these exact packet pins. No concrete source blocker identified.** The two-CPU/16-GiB/3,600-second proposal with 1,650 seconds per interpreter is acceptable as a bounded diagnostic request, not a measured runtime/RAM bound, native acceptance, automatic retry or GPU permission.

Only `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-review312/checks.py`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-review312/checks.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-review312/verdict.json` and `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/313-handback.md` were written. No source, Git, RS, scheduler, remote, model/native import or real ledger/MAIN operation occurred. Root should lint centrally. The verdict rests on failed actual XML/log/result evidence, actual corrective diff and original raw guard/contracts, not an author narrative.

The raw failed run has two distinct attributable causes in each environment: thirteen cases reject at `CPU immutable WAITING copy`, while the full positive case fails on a relative native input path before its full context/support/audit path. `rebind` previously saved the actual marker with sorted keys, then reserialized the earlier insertion-ordered object into the CPU copy. Equal JSON semantics did not preserve authenticated bytes. The correction in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-correction312/packet-r3/candidate/tests/test_full_score_integration.py:110` acquires the stored marker bytes, parses those bytes for request construction, then writes those exact bytes into CPU WAITING. It asserts their request hash and equality before COMPLETE construction; no production guard or hash is weakened, and no tamper is resealed.

`native_modules` now enters original runtime S before import/native reads (`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-correction312/packet-r3/candidate/tests/test_full_score_integration.py:36`). That follows the unchanged owning CPU/host runtime cwd contract and retains relative prepared-input/source references. Source runtime/commit remain fixed. All actual input/groups/bank access is read-only; bank/score/ledger/admission/publication writes remain confined to owned temporary fixture paths. Cwd restoration is managed by pytest's monkeypatch fixture; changing cwd does not relocate these absolute temporary paths into original MAIN.

All original thirty-two cases' assertion multisets and parametrizations are preserved. One new regression (`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-correction312/packet-r3/candidate/tests/test_full_score_integration.py:602`) calls original `capture_cpu` successfully with exact authenticated bytes, then adds semantically harmless whitespace only to the CPU copy and requires original raw-byte rejection. Marker, request and COMPLETE bytes remain unchanged, no resealing occurs and CLI/model/publication calls remain zero. The six transfer-negative routes now also assert that `stage` was reached (`:497`), preventing the unrelated earlier raw-copy rejection from satisfying those tests. Their historical apparent passes are not acceptance of the intended mutation paths.

All seventeen production components remain unchanged, including the root helper/raw guard, real delegating root/admission checks and coherent temporary MAIN routing accepted in review296-r2. Original native normalization/protection, final entry/consumption, original CLI argv, partial/no-retry and native stage/manifest/domain/control/support semantics remain active in the source.

## How verified

```bash
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-review312/checks.py
```

Observed exit zero in approximately 1.51 seconds. All nine own packet members and frozen dependency/source pins match, as do all seventeen production hashes and preserved failed evidence hashes. AST comparison preserves original assertion multiplicity and decorator/parametrization ASTs and counts thirty-three cases. Replayed only the unchanged original raw-copy assertion against all twenty-six preserved actual failed marker/copy sets: exact original bytes pass; prior semantically equal reserialization and whitespace tamper reject. No application/native import, full `capture_cpu`, pytest or integration run occurred in this check. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-review312/checks.json`.

Packet pins SHA: `4300cdabd1b612e228761b7b4ea204a023ff29121c5ddcd265cb211345ab4761`. Test SHA: `fba62e22db8562a3807de1c73670bb549469583097dca50d5d9641c91668adbd`. Actual observer changes only the expected count from thirty-two to thirty-three; explicit normal environments, exact source dependencies, fresh Alignment output/basetemp, isolated discovery, byte/pin checks, no GPU and failure-preserving timeout behavior remain.

Resource assessment: the actual failed environment durations were 300.717001 and 298.393931 seconds, but no full support reconstruction or native audit completed, and thirteen consumer paths stopped before publication. The corrected scope newly reaches one full support reconstruction, four serial audits/five context loads, eight row-key/eight positive-key enumerations and thirteen publication/consumer paths per environment, plus a small raw-copy regression. The additional 1,349 seconds above the roughly 301-second failed baseline is an explicit planning allowance, not measured work. Two times 1,650 plus 300 seconds observer allowance equals the proposed 3,600-second reservation. It is a coherent bounded diagnostic attempt; no prior 193-second local timing or different-workload memory measurement proves these bounds. Retaining sixteen GiB remains unmeasured for the full graphs/buffers/native temporaries. A timeout/OOM is failure evidence, never permission to retry or weaken controls.

## Execution evidence

Existing failed-run inspection only; no new native run:

- Job/cluster: existing 23636443 on Delta, reported by actual `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task4-deployment298/run-01/run_manifest.json` and result provenance.
- Exit/state: both observed interpreter invocations exit 1; overall result is FAIL. No corrected native run is claimed.
- Cases: each actual XML contains thirty-two cases, eighteen passes, fourteen failures, zero errors/skips. Thirteen fail on immutable CPU WAITING bytes and one on original relative-source cwd.
- Baseline comparison: both environments reproduce the same thirteen raw-copy failures and same one cwd failure; this is failure attribution, not a scientific baseline claim or native success.
- Provenance: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task4-deployment298/run-01/run_manifest.json`, root-supplied worktree commit `538109e809285b6ddc45d42df8786270a65f7b12`, original source `50e947bb852613e3a270082651f2bd1b7bb0c525`; `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task4-deployment298/run-01/RESULT.json`, raw logs/XML, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-correction312/evidence/diagnosis.json` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-correction312/correction-manifest.json`. Failed evidence was read and hash-checked, not modified.

## What is NOT done

No corrected native/integration execution, complete thirty-three-case acceptance, actual resource/time/RAM measurement, source publication, job, reservation, ledger transition, remote handoff or GPU action. Root must inspect both normal supported environment identities, thirty-three unique expected case results including stage reach and the raw-copy regression, full positive native audits, logs/XML/provenance and observed resources before Task 4 acceptance. No accepted component suite needs duplicating while production bytes remain unchanged.

Actual full-path handoff feasibility, source/input/cache/SIF/namespace proofs, independent real resource/capacity decision and bindings, reader-safe reservation/successor/native budget lineage, actual full-only job/admission, fresh owning CPU proof/current catalogue transfer, usage/protection/allocation/deadline checks and once-only remote release remain separate operational/GPU gates. Actual bindings and feasibility remain null.

## Open questions

None blocks root's separately authorized bounded diagnostic dispatch of the exact corrected packet. Default: retain all failed evidence, run only the new corrected integration scope under the reviewed limits and diagnose any first newly exposed failure without bypasses or automatic retries.
