# Hand-back 239 r2: diagnostic pre-Popen deadline correction

Status: handed-back

## What changed

Created only distinct `.superpowers/sdd/plan-a2-fresh-cpu-timing239-r2/` and this report. Original diagnostic 239, its 546-file manifest/hash, all Task2 production, data-only guards and historical evidence remain unchanged. New manifest SHA256 `c43d084973d38dbb2367b269879f23cc2d42383784f65d9abde937d4232573e6` binds 577 files, including original members and raw review 244 evidence.

Read review 244's verdict, checks and actual-boundary probe. It reproduced final packet authentication advancing a fresh process's clock from 1,000 to 1,250 seconds against a fixed 1,240 deadline, yet reaching Popen. Later child/observer guards rejected; no false operational admission was demonstrated.

The sole runner function changed is `run_stage`. Its recheck now retains a nonincreasing minimum of the original stage bound and current CPU end minus sixty seconds. Parameters and command are serialized from the clamped bound after final metadata authentication, then a fresh clock check rejects at or after that bound immediately before the sole Popen. Later allocation increases cannot renew it. The child, data factor, all original native/G2/G3/domain/support/catalogue guards, measurement schemas and policy are unchanged. New launcher/request paths identify the r2 namespace. `original-to-r2.diff` records the exact raw non-git diff; `narrow-ruling.json` records scope and unchanged-policy evidence.

Prime 480, fresh 240, bootstrap 75, local publication 45, CPU finish 60, proposed kill 15 and total 900 seconds remain unchanged. The fixed hypothetical GPU window remains 300 seconds. `operational_feasible` remains null and remote request/transfer/publication costs remain unmeasured. No new operational scope or authority was added.

## How verified

Wrote seven meaningful actual-boundary regressions before the correction, adapting the independent probe. The uncorrected r2 copy produced five intended case failures and two passes, zero errors. The failures cover costly authentication exhausting fresh/prime bounds, equality at the bound, expired current CPU end-minus-finish, and ignoring a shorter current bound. The already-protected ordinary valid start and late-reaped-zero rejection passed.

Final pure suites pass 26 of 26 in base Python 3.9 and 26 of 26 in mgnp Python 3.12, zero failures/errors. They retain all original nineteen tests and add seven boundary cases. The valid path invokes the actual run-stage boundary and unchanged Task2 observer with external metadata/process seams, starts once, traverses saved-byte/supervisor checks and retains a 1,100-second bound despite later allocation increase. Expired cases reach zero Popen calls; late reaped zero cannot publish the pipeline observation. No actual scientific process or native data is used.

An initial full pure run passed 25 of 26; the relocated-wrapper test caught the copied old absolute launch path. The path was corrected before freezing, with those failed logs/XML retained. AST/shell checks and an actual relocated-wrapper preview then passed, both prospective child commands pointing to r2. Source comparison confirmed only `run_stage` changed among runner functions, while all 546 original members and six Task2 helper/template hashes remain intact.

## Execution evidence

Only tiny local pure tests, source/hash/diff/syntax checks and a dry-run preview executed. Initial new-regression baseline observed seven cases: five expected failures and two passes, zero errors. Final suites observed 26 passes against 26 expected in each interpreter, zero failures/errors. Exact XML/logs and hashes are in `review244-red.*`, `pure-final-base.*`, `pure-final-mgnp.*` and `pure-results.json` within r2. No new Slurm job, native rows, numerical baseline, scientific commit or native run_manifest exists for this correction.

Original source remains `50e947bb852613e3a270082651f2bd1b7bb0c525`; new manifest pins that same source and the original 239 hash `63743b3e980ce194a5cbbc8fe0415aaf486c4f78967250751f025b1b5365180e`. Historical failed proof 50315944 remains partial, with no new admission inferred. No git, RS, SSH, scheduler, transfer, source publication or additional-agent action occurred. This worker owns no unfinished process/job.

## What is NOT done

Independent 244 r2 acceptance, actual Task2 GREEN/source acceptance, real diagnostic job/resource/witness/config bindings and native diagnostic timings have not been established by this worker. No diagnostic launch authority is granted. No Task3 or operational CPU/GPU admission work advanced. The diagnostic keeps its separate nonoperational schema and cannot generate READY, WAITING, a future GPU request, operational CPU_COMPLETE or release.

The architecture and all previous limitations remain: data-only filesystem priming may or may not make the full new-process pipeline fit; local publication measurement cannot establish remote costs or operational feasibility. No guessed remote cost or larger window was introduced. Root retains report lint because RS remained prohibited in worker scope.

## Open questions

Root can send the frozen manifest, raw diff and review evidence to independent 244 r2 review. After that acceptance, actual Task2 GREEN/source acceptance and real bindings, use a separate root-bound config and the exact command `bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-fresh-cpu-timing239-r2/launch.sh --config ROOT_BOUND_ABSOLUTE_CONFIG --config-sha256 ROOT_BOUND_SHA256`. The original proposed actual Delta allocation stays four CPUs, 32 GiB, 15 minutes, no GPU/requeue, bank-matching mgnp and one thread. Set Slurm WorkDir/chdir to the original frozen runtime, as required by the unchanged allocation helper.

Job/placement/current four-catalogue witness and acceptance references remain NULL in the templates. A fresh actual diagnostic job/packet witness must retain original 422 roles and all eleven aliases; do not reuse a historical proof's witness or rewrite catalogue/source bytes. Root alone binds and launches after acceptance. Preserve failures and stop rather than retry, enlarge bounds or infer admission.
