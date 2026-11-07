# CPU proof receipt collision successor

Status: handed-back

## What changed

Created distinct `proof-adapter-r5` and `root-proof-dispatch237` under the specificity-ladder worktree's `.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/`. The only host behavior change writes its final activation-source receipt to `source-after-activation.json`; the child's `source-after.json` remains untouched. The worker, schema, native contract, request, input pins and other guard code are byte-identical. Wrapper, test path assertions, inventory and manifest identify r5. The adapter manifest SHA-256 is `f12141b3b301d359dd7cf952ee47445b3bc637c31e9c4020c17da81cf268b26f`; the dispatcher SHA-256 is `9631dbf0c26f3576bda79787d1f1b6b8de89ffd8b19cfced0cf156bf917e5862`.

## How verified

A two-layer test extracts the actual child and host exclusive write calls and executes both with fixture data. The predecessor name reproduced `FileExistsError` in each environment; the successor retains the child's bytes and the separate host receipt. The bounded packet suite ran 35 tests under each supported interpreter: Python 3.9 passed with one 3.12-only generic syntax test skipped, and Python 3.12 passed all 35. Nine dispatcher fixtures passed in each. Full new red and green packet logs are included in the manifest; full dispatcher logs are retained beside its script. Manifest, transfer inventory, unchanged guard files, Bash syntax and host Python 3.6 grammar were checked. Actual Python 3.6 was unavailable locally.

## Execution evidence

The preserved Bridges job 50315944 failed in final guards with `FileExistsError` on `source-after.json`; its child reported normal postguards and exit zero, but the supervisor did not publish a complete proof. This task ran only local fixture tests and did not run a successor job, native proof, model or GPU. The failed job was not promoted or modified.

## What is NOT done

Independent review of the frozen successor and dispatcher, new source transfer, job-bound bindings and any future run remain outstanding. The separate owning-time and release-window question is outside this correction.

## Open questions

The coordinator and independent reviewer must assess the earlier child measurements and timing separately, and review the exact successor before deciding whether any new run is warranted.
