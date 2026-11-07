# Hand-back 307: Conditional A2 resource and deadline judgment

Agent: independent engineering reviewer, gpt-6.1-sol. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-resource-decision307/proposal.json`. Status: resolved; conditional engineering proposal accepted, no actual resource binding.

## What changed

**Verdict: ACCEPT the proposed engineering tuple and deadline fields as a conditional estimate under the already accepted method. No concrete arithmetic or controller-contract blocker identified.** Scope is one H100, four CPUs, 96 GiB, 19,800 seconds; minimum entry 18,000 seconds, child cap 19,000 seconds and finish reserve 300 seconds. This does not guarantee completion or establish operational feasibility, capacity, admission, reservation or GPU permission.

Only `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-resource-decision307-review/arithmetic.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-resource-decision307-review/verdict.json` and `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/307-handback.md` were written. No source, actual bindings, Git, RS, remote, job, test, native import or agent action occurred. Root should lint centrally. Accepted audits249/177 were not rerun or reopened.

The accepted proof and audit support the existing engineering arithmetic:

`13,780.93869288219 × 1.2 + 900 + 555.7060698261485 + 300 = 18,292.8325012848 seconds`.

This leaves approximately 1,507.167499 seconds within 19,800. The single whole-core allowance is retained; no CPU subtraction is made from the observed prefix, and the full 888.394622-second CPU hash stress is not added again. Measured production publication 56.820095 seconds is charged once inside the 900-second combined fixed allowance, leaving 843.179905 seconds explicitly unmeasured. Cold load is charged once. The raw proof identifies these platform measurements and forbids treating them as a GPU runtime theorem; the proposed judgment preserves that qualification.

Deadline arithmetic matches the unchanged component interfaces:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r4/closure/sdd/plan-a2-full-score-operational186/candidate/gpu/common.py:193` takes the minimum initial, current and fixed run end, then subtracts the 300-second finish reserve. With a full 19,800-second allocation, work end is 19,500 seconds; a shortened actual allocation can only reduce it.
- The proposed fields satisfy the original feasibility inequality `300 < 18000 <= 19000 <= 19500` (`common.py:112`). The 18,000-second entry floor covers the entire engineering forecast after removing only finish: 17,992.832501 seconds, with 7.167499 seconds to spare. This is conservative reuse of the forecast, not a new measurement or subtraction of already elapsed work.
- Consequently at most 1,500 seconds of actual elapsed pre-entry time can remain compatible with the floor. Root publication and final consumer guards enforce current remaining time; the 300-second WAITING publication window also shortens to `work_end - entry_floor` (`common.py:473`, root helper `:450`, `:603`). A nominal 300-second release does not override a smaller available window.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r4/closure/sdd/plan-a2-full-score-operational186/candidate/gpu/controller.py:167` clamps the original CLI deadline to the minimum preflight work end, repeated consumed-entry work end and `now + 19000`. At elapsed 0/500/1000/1500 seconds, illustrative permitted child time is 19000/19000/18500/18000 seconds; at 1501 it rejects. The cap never grants 19,000 seconds beyond work end. The fresh floor is checked again immediately before the sole Popen, and consumed permission is not renewed after a failure.
- Native result/audit completion must still precede the minimum run deadline (`controller.py:197`); host supervision retains that minimum without extension (`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/green270-r4/closure/sdd/plan-a2-full-score-operational186/candidate/gpu/host-launch.py:149`). The finish reserve leaves room for the existing post-work path; it is not a guarantee of its latency and is not subtracted twice from the child cap.

Platform/fixed-envelope judgment: retaining the original H100 platform, exact supported mgnp numerical environment, unchanged scientific workload and authentic bank is consistent with the accepted same-platform orientation plus one twenty-percent allowance. Four CPUs and 96 GiB remain a conditional resource choice, not a measured total-workspace theorem; actual identity/free capacity, allocation and storage checks are still mandatory. The accepted CPU proof's analytical host union and measured peak have their existing scope. They do not turn 96 GiB or the 900-second envelope into a universal bound. No additional gate or rerun is introduced by this review.

## How verified

Read the raw accepted COMPLETE proof, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-proof-terminal-review249/audit-result.json`, the new proposal and unchanged common/controller/root/host deadline code directly. Used stdlib Decimal arithmetic and illustrative clamping calculations only; saved results in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-resource-decision307-review/arithmetic.json`. Decimal reconstruction differs from the stored binary-float total by only 0.0000000000025 seconds, with no material effect on margins.

```bash
sha256sum /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/root-proof-50316939-evidence/COMPLETE-PROOF.json /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-resource-decision307/proposal.json
```

Observed proof SHA `56806be4b4f233005f98f338fdc11dd5e46f09e376b0cb7577497494857a519d`, matching accepted audit249, and proposal SHA `a6b12681e76f3d24761349c3b368a1d4189fbc632179b228f2072b7ac4f5ea79`. All proposed actual job, actual capacity and domain-reference bindings remain null.

## Execution evidence

Not applicable: no runs.

## What is NOT done

No full GPU timing measurement, new resource proof, prospective runtime guarantee, Task 4 result acceptance, source publication, actual capacity/resource binding, job, reservation, ledger transition, remote handoff/publication or GPU admission. The queued Task 4 job was not queried, duplicated or retargeted.

The proposal's existing open prerequisites remain unchanged: actual Task 4 whole-packet acceptance/publication; actual capacity/cache/storage/source/input/job/admission bindings; fresh reader-safe reservation and complete successor preserving all charges; genuine request/acquisition/capture/transfer/recheck/publication feasibility within the existing freshness/window limits; and original full-score numerical/environment/support/control/final-result checks. Local CPU and metadata-only cache timings do not establish the unmeasured remote handoff. No automatic retry, extension or cap amendment follows.

## Open questions

No further engineering choice blocks accepting this conditional tuple at the exact proposal hash. Default: root may record that narrow decision while leaving all actual bindings and execution permission unset until the existing prerequisites are satisfied.
