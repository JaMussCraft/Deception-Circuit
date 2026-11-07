# Hand-back twenty-seven: Unicode projection hash repair review

Agent: Codex Sol independent reviewer. Ticket: scoped follow-up to the projection review. Status: resolved; P2 closed.

## What changed

No code was edited by this reviewer. Reviewed the narrow repair in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/scripts/twin_training_projection.py` and its regression in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_twin_training_projection.py`.

The new `build_digest` uses Unicode-preserving serialization matching `dataset/build_twin_training.py` for materializer build hashes. Existing `digest` remains unchanged and continues to validate wrapper receipt hashes. The regression uses an em dash in source metadata, accepts its correctly hashed manifest, and rejects a receipt whose full-manifest hash was incorrectly migrated to the build convention. This closes P2 from the earlier independent review; no residual compatibility finding was identified within this scope.

Orchestrator commit source: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/27-projection-rereview-handback.md`. Primary copy: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/27-projection-rereview-handback.md`.

## How verified

Read the changed hash helpers, the build-hash validation call, the new regression, and the direct red/green logs. No suite rerun was needed for this narrow review.

```
sed -n '22,70p' scripts/twin_training_projection.py
tail -45 tests/test_twin_training_projection.py
cat /tmp/a2-projection-unicode-mgnp.log /tmp/a2-projection-unicode-base.log
tail -22 /tmp/a2-projection-unicode-red.log
```

Observed: the red log has one failing Unicode regression and forty-eight passing existing cases. Both green logs have forty-nine passing cases. The red failure is the previously reported `ValueError: build hash mismatch`; the changed helper matches the materializer serialization.

Live Codex usage check reported eight percent used against the eighty-percent cap.

## Execution evidence

- Job id and cluster: local read-only review commands above; no Slurm job.
- Exit code: zero for the inspection command. The inspected red log reports one failed case; both inspected green logs report all cases passing.
- Row counts: forty-nine passed against forty-nine expected in each green log; no scientific rows were scored.
- Baseline reproduces: red log has forty-eight existing passes against the earlier forty-eight-test baseline; the additional regression increases the green total to forty-nine in both environments.
- Provenance file: no scientific `run_manifest.json` or commit is claimed. Logs are CPU regression evidence, not measured GPU timing. Scientific pilot estimates remain not yet verified by an actual run.

## What is NOT done

No code changes, broad reruns, git, GPU/API use, notebooks, ledger writes or job submission. Earlier projection limitations remain: under-two-hundred cohorts require a supported recorded lead ruling, and timing coverage requires actual comparable receipts. This review does not authorize a pilot or fleet submission.

## Open questions

None for this narrow repair. Default: accept the Unicode compatibility repair and close P2 while retaining the earlier gate limitations.
