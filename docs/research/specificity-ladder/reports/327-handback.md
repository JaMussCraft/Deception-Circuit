# Hand-back 327: Task 4 retry-invariant fixture correction

Agent: gpt-6.1-sol, bounded diagnosis/correction. Ticket: Task 4 BASE retry expectation failures from job 23638286. Status: handed-back.

## What changed

Prepared exactly one distinct packet `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-correction327/packet-r5`. Frozen correction321 and all seventeen production components remain unchanged. Only two existing integration-test functions change: whole positive publication and six-variant transfer failure. All thirty-three case parametrizations and every existing assertion remain; the complete native happy path, later mutation audits, exact marker-byte/tamper regression, stage-reached checks and real semantic validators remain.

Diagnosis followed the complete actual BASE log and original guard order, using its two attributable failures as RED before correction. Original `Producer.publish` runs `verify_runtime_pins` before attempting exclusive `publish-once.claim`. After successful score publication, original `verify_existing_bank` must reject the existing score first. After the catalogue transfer attack, original `input_closure` must reject the retained damaged ordinary input first. Neither correct rejection implies renewed permission; expecting only `FileExistsError` mis-specified the invariant.

The correction does not broadly accept exceptions:

- After the first successful full publication/normal audit, controller and producer retries must raise the exact original `score already exists or is symlink` ValueError. Local root/CPU/MAIN/evidence files and actual remote release are fingerprinted by byte count plus streaming SHA across retry. CPU COMPLETE, claim, release, publication, score/manifest and consumed/completion evidence remain unchanged; no pending release appears; original CLI and publication/stage counts remain one and model calls zero.
- After a failed transfer, the original claim must exist. The catalogue retry must produce `ordinary input changed: ` plus the exact attacked catalogue path. The other five variants must raise `FileExistsError` with the exact original claim filename. Retained local partial/CPU/request/WAITING/claim evidence and fake remote bytes remain unchanged, final release/pending/score remain absent, and no extra CLI/model/stage/publication occurs. The existing first-failure stage-reached assertion stays active, distinguishing mutation failure from retry rejection.

All additions live in tests; no receipt is fabricated/repaired for retry, no exception is caught in production, and no first-success condition is removed. A production change that rewrites retained artifacts, publishes/executes twice, repairs damaged evidence or permits reentry would fail the added assertions. Fixture-only MAIN/cwd/HF/source/support construction is untouched.

Files under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-correction327` include reproducible `prepare.py`, actual-RED `diagnosis.json`, exact `fixture.patch`, `correction-manifest.json`, the distinct nine-member packet, a bounded extracted-guard probe and pure/relocated evidence. No other source/state/job/remote/Git/RS/agent action occurred. Root should centrally lint this report.

## How verified

```bash
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-correction327/retry_probe.py
```

Observed exit zero: only extracted original stdlib score-presence and ordinary-input statements reproduce the exact two BASE causes against retained read-only failed-run paths. Original exclusive creation rejects an existing owned probe claim with the precise filename and preserves its bytes. No application import, full producer invocation or native test occurs. Two earlier probe-harness attempts selected the wrong pytest directory set; the final lookup excludes pytest's `current` symlink. Preserved note: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-correction327/evidence/probe-harness-note.json`. These were probe-routing failures, not candidate/native outcomes.

```bash
timeout 25s /sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-correction327/packet-r5/source_checks.py
```

Observed exit zero. The same bounded stdlib checker also exits zero under mgnp. AST/JSON, all thirty-three cases, original assertion/decorator preservation, actual-binding nulls, all seventeen component hashes, original cutover/HF/support constructor flows and real delegating gate checks pass. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-correction327/evidence/source-check-base39.json` and `source-check-mgnp.json`. Shell syntax and the absolute wrapper copied to a spool-style path pass; relocated dry run authenticates exact pins with no native imports (`evidence/relocated-dry-run.json`). Final source-pin recheck passes; frozen321 still matches every original member hash.

Packet pins SHA: `9a5129f6c3fae0455c706a6077ac04047c5062f7abbea0f98018113da1f7e571`. Integration SHA: `b480636a8712de573916a4e9b438a82983156cebf180d36d0ed7429a4648ab03`. The observer bytecode/CLI/env/source selection is unchanged except the absolute wrapper location; only source metadata/proposal/docs and retry assertions change. Actual native GREEN is unrun.

The CPU proposal retains two CPUs, sixteen GiB, 3,600 seconds total and 1,650 seconds per environment. BASE measured 750.79 seconds on the old thirty-three-case packet with thirty-one passes; the positive case completed its native normal publication/audit before the wrong retry expectation, but three later serial mutation audits were not reached. Fingerprint streaming and those three audits are additional reachable work. The 899.21 seconds above that BASE duration is a planning allowance; mgnp's final duration/result remains root-owned and was unfinished when diagnosis began. Two environment bounds total 3,300 seconds plus 300 seconds observer headroom. No successful-path runtime/RAM guarantee, time extension or automatic retry follows; independent review/root must decide a separate diagnostic dispatch.

## Execution evidence

Existing completed BASE phase only; the same job's other environment remains root-owned:

- Job/cluster: 23638286 on Delta, cn096, according to `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task4-deployment324/run-01/run_manifest.json`; two CPUs/sixteen GiB CPU-only context.
- Exit/result: BASE pytest exit 1, two failures; no final dual-environment/Slurm outcome is claimed here.
- Cases: thirty-three observed, thirty-one passes, two failures, zero errors/skips; pytest reports 750.79 seconds. Failures are `test_whole_chain_normal_native_full_publication` and `test_transfer_failure_cannot_cross_score_boundary[catalogue]`, both at the overly specific repeated-publish expectation.
- Baseline comparison: expected thirty-three versus observed thirty-three; no scientific baseline/replication or corrected native success is claimed. Original first positive publication and normal audit assertions execute before its observed failure; later support/control/manifest mutation audits remain unobserved.
- Provenance: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task4-deployment324/run-01/run_manifest.json`, commit `538109e809285b6ddc45d42df8786270a65f7b12`, original source `50e947bb852613e3a270082651f2bd1b7bb0c525`; complete `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-task4-deployment324/run-01/base39.log` and `base39.xml`, pinned in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-whole-packet-correction327/diagnosis.json`. These files were not changed.

## What is NOT done

No corrected native/integration test, full-suite rerun, Task 4 acceptance, final mgnp/job collection, measured successful time/RAM bound, actual binding, source publication, reservation/ledger transition, remote handoff or GPU permission. The running job was neither queried nor modified by this worker. Root collects its terminal evidence separately.

Independent exact-source review and complete focused dual-environment native results still precede Task 4 acceptance. Existing actual source/input/cache/SIF/resource/capacity/ledger/job/admission/owning CPU proof/usage/protection/publication gates remain unchanged; actual bindings and feasibility stay null. No production repair, framework or control bypass is introduced.

## Open questions

No new design choice is requested. Default: root preserves both failed-environment outcomes, independently reviews this single correction and proposed bounded diagnostic request, then decides any separate run. Do not label the corrected native happy/mutation path passing until actual results exist.
