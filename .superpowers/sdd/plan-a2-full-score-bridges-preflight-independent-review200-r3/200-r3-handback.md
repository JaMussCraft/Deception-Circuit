# Independent Bridges cgroup diagnostic correction review

Status: held after a HOLD

## What changed

Accepted the exact revised packet for one root-bound diagnostic probe only. It exposes the real host memory controller read-only at the unchanged worker path; no host counter values are copied into the container. Actual corrected visibility remains unproven until that probe runs. [Scoped verdict](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-preflight-independent-review200-r3/verdict.json).

## How verified

Read the accepted predecessor review, exact code delta, actual failure evidence and tiny tests without the author hand-back. Rehashed old/new members, confirmed existing exact-job and output guards remain unchanged, and checked Python compatibility and shell syntax. Failed memory mapping now preserves membership, relevant mount lines and path errors instead of discarding the diagnostic context. The borrowed helper's blocked genuine main is not executed or accepted. [Verdict](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-preflight-independent-review200-r3/verdict.json), [raw host path](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-preflight-independent-review200-r3/host_probe.py), [raw counter reader](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-preflight-independent-review200-r3/cgroup_probe.py).

## Execution evidence

Prior Bridges diagnostic 50309188 failed after 9 seconds: host exit 0 showed actual own-job counters, while container exit 1 reported unavailable memory mount mapping. This explains the revision, not a corrected probe pass. [Raw host evidence](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-preflight-independent-review200-r3/actual-50309188-host-cgroup.json), [raw result](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-preflight-independent-review200-r3/actual-50309188-probe-result.json), [reported accounting scope](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-preflight-independent-review200-r3/verdict.json).

No new Slurm job or remote action occurred in this review. Base observed 9 passing tiny tests against 9 expected; mgnp observed 9 against 9 expected, both exit 0. The separate observation RED records 1 expected mapping-evidence failure against 1 observed; the bind RED is an import error, not semantic verification. No scientific baseline replication is claimed. [Counts](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-preflight-independent-review200-r3/verdict.json), [observation RED](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-preflight-independent-review200-r3/red-observation.log), [test provenance](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-preflight-independent-review200-r3/run_manifest.json).

## What is NOT done

No actual corrected container counter visibility, genuine schema graph, model/GPU permission or adapter acceptance. Future genuine execution must retain real Bridges provenance and the separately reviewed deadline rules; it cannot imitate Delta facts or use copied peaks.

## Open questions

Root must bind and stage the exact packet, ordinary owned evidence namespace, actual allocation and unchanged source/profile/SIF/cache paths before one diagnostic probe. Any missing controller or ambiguous identity remains a failure. Subsequent genuine adapter and resource proof need separate review. Work is now held at root's explicit HOLD; no additional review or operation will start. [Exact root prerequisites](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-preflight-independent-review200-r3/verdict.json).
