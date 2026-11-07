# A3 Tasks 2–3 correction for independent review 225

Status: handed-back

## What changed

Both review findings are addressed in the isolated candidate and frozen for root CPU validation and scoped re-review. This supersedes the implementation revision described by report 222; prior reports, r1/r2 packets and their root dispatch records remain historical evidence.

**R225-A: actual native aggregate entry.** `run_phase` now verifies scenario source/configuration without loading a model, obtains the original prefit/selected-pilot inventory, materializes deterministic target data if absent, and receives the immutable graph through the unchanged lower transport reader before calling the original tiny-model loader. It then forwards the prepared handle through the actual aggregate helper into `run_pilot`. The original nine prefit or sixty-three selected case IDs/order, saved numerical samples, control assertions and reconciliation remain intact. The original native source/model verification implementation is unchanged.

This explicitly injected numerical harness has no root execution admission. Its test-module-only `_InjectedPreparedPilotTarget` subclass holds immutable data and entry witnesses, checks process/graph scope, and performs final namespace/full witness, original scenario source verification and cheap unchanged identity checks. Production `run_pilot` still requires the exact loader-minted runtime type/context; it rejects this subclass before invoking any numerical/guard entry. Runtime never imports test modules. There is no new provider flag or production authority kind. Root explicitly accepted this narrow seam choice before implementation.

The new actual-entry regression drives `run_phase('prefit-aggregate')` through existing bounded fake-model/source seams. It requires reception before model entry, a non-null prepared handle, no full-target building/publication/readback after model entry, the same nine original saved case references/order, original aggregate control assertions, one lower reader invocation with its two-read/one-parse/freeze recipe, and one final target witness check. The existing direct-helper regression remains unchanged. A separate production-boundary case rejects the test subclass.

**R225-B: deployment and measurement scope.** Software identity no longer asserts an unconditional Lustre filesystem. Actual receiver context observes CPU architecture/model from `/proc/cpuinfo`, allocated cluster/CPU/RAM resources, and each referenced target/preparation path's resolved filesystem, mount point/source and device from `/proc/self/mountinfo`. Missing context fails closed. The original admission's existing `pilot_target_preparation` binding now additionally carries `receiver_deployment`; this is data in the same admission kind, not new authority.

The receiver resource record must match that original binding and independently observed current receiver context before the large read, then match again after reception and the fresh original authority check. The schema requires a byte-bound completed measurement manifest with run/PID/allocation provenance, exact source/code/artifact/software/recipe/deployment identity, source before/after, cold/warm cache scopes, finite wall/user/system CPU observations, process RSS/peak scope and applicable cgroup current/peak/events scope. The unchanged post-reader retained/transient/peak bound comparison remains before the loader. Complete target/pilot/authority tiers remain additive.

Completed intake independently checks original-admission deployment and receipt-origin equality, actual present storage paths/family, original allocation contract CPU/RAM/cluster backing, measurement schema/provenance and recorded process/cgroup peaks. A resource record or measurement manifest still cannot authorize a model.

Fixture evidence is explicit synthetic contract evidence. Its cold scope is labeled `synthetic-fresh-process-contract`, never genuine fresh-process/cold evidence. The fixture actually invokes the lower data-only reader twice and captures elapsed wall/user/system time, process observations and applicable cgroup current/peak/events; a completed fixture manifest binds those observations. Genuine production evidence must declare the non-injected execution class and genuine fresh-process scope. Operational cold/warm measurement remains Task 4. The selected-domain construction, all nine records and 199/32 axes, and the sixty-three invocation classes remain unchanged.

Seventeen focused cases were appended: nine evidence-schema gaps, three originally anchored actual receiver-context mismatches, three originally anchored completed-intake gaps, actual native phase routing and production subclass rejection. The complete previous 142-case test file remains a byte-identical prefix. The 59 parametrizations of all 21 required old regression functions remain, and every old function body is unchanged; only its authentic preparation fixture construction was extended.

Complete prior candidate source is preserved at `S/plan/task23-green-r2-source-snapshot`. Frozen r2 packet/root-dispatch records were not rewritten. `S` denotes `W/.superpowers/sdd`, where `W` is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

Final frozen r3 pins:

| Member | SHA256 |
| --- | --- |
| `S/plan/task23-green-r3/source-pins.json` | `bdae741f0be02fabd68f28b247a7ae8eb07a1a261f00ae3a1703c878c5daf8f6` |
| Candidate runtime | `66c33953dc8c61ed2292744a362d47f69e6cf565732fb3716402657cc80d15c5` |
| Native scenario | `bbf98666e0a8c690ade4b06fe28f7087db2928a0670f83f8590305789f1639aa` |
| Integration fixture helper | `b186ef56543fa984b59801f2f874b84d2b8cc6ee8856354ddc3a764b608738e6` |
| Prepared test file, 159 cases | `6866aa8a578b08b53e25316edfa351502653e8ffa4267bf8ffcacfe6f0705406` |
| Scoped old runtime fixture file | `1e85c6cda40b05711d2334789c3df9722e26931ccc75e6e5193f92a46fe00981` |

## How verified

Local work used bounded static/pure checks only: AST syntax of the five owned files; exact previous 142-case prefix; unchanged original old-test function bodies; unchanged Task 1 transport, generic publisher/reader, authority, allocation, numeric dependency forest and file-witness ASTs; unchanged selected-domain constructor/backing ASTs; exact source/staged-suite pins; shell syntax; and direct/relocated import-free wrapper dry-runs. The AST-extracted schema probe ran in under one second and actually observed the r2 validator accept all nine gap specimens, the r3 validator reject all nine, and capacity 100 pass / 99 reject for obligations 50 + retained 20 + transient 30. This is a pure schema counterexample check, not full task RED or operational evidence.

Each independent interpreter shard must run ten attributable correction RED cases against the preserved r2 runtime and actual native route, then all 218 r3 GREEN cases. The RED baseline uses exact r2 runtime/native source bytes with identical current test assertions and fixture support. Only three AST-allowlisted missing CPU/storage observation helpers are installed for fixture construction; no validator, guard, authority or native routing behavior is patched. This declared setup support prevents missing-helper errors from masquerading as the intended failures.

Expected RED is one actual native phase assertion about model loading before prepared reception, plus nine missing evidence rejections reported as `DID NOT RAISE`; zero errors/skips. Expected GREEN is all 218 cases passing: the original 137, the earlier five correction cases, seventeen review-225 cases and 59 original regression parametrizations. Collection and JUnit assert exact function counts. No source changes may occur while either shard is active.

## Execution evidence

No r3 correction RED/GREEN run has been executed by this worker. Root reported both unstarted r2 GREEN jobs, Delta `23620419` and `23620420`, cancelled with zero runtime before authorizing this correction. Their packet/root dispatch evidence remains untouched. The running independent BASE comparison and Bridges proof job were not modified.

The previously accepted Tasks 2–3 RED execution remains Delta `23618388`: saved normal-completion manifest, supervisor exit zero, 687.481366-second runner wall time, 137/137 cases per interpreter, 55 Task 1 passes plus the intended 52/30 missing-symbol failures, zero errors/skips. The original publisher baseline reproduces 62/62 expected bytes in both interpreters. Provenance is `S/plan/task23-red-r2/red-run-01/run_manifest.json`, baseline commit `538109e809285b6ddc45d42df8786270a65f7b12`, with isolated revisions identified separately by source pins.

Root-only r3 launch template, replacing `ENV` with `base` or `mgnp`:

```bash
P=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task23-green-r3
sbatch --account=beto --partition=cpu --cpus-per-task=2 --mem=32G --time=00:59:00 --output="$P/green-ENV-slurm-%j.log" "$P/cpu.sbatch" --mode GREEN --environment ENV --output "$P/green-ENV-run-01"
```

The same immutable scope can run in independent shards. Each requests two CPUs, 32 GiB and fifty-nine minutes: ten-minute correction RED hard limit, ninety-second publisher oracle limit, forty-five-minute GREEN/preflight limit and approximately two-and-a-half minutes of supervisor margin. Sequential combined proposal is 118 minutes.

Resource evidence remains the original prefit preflight observations of approximately five to six seconds and selected preflights of 264 to 290 seconds. No implementation GREEN has yet supplied timing. Each anchored or production-shaped fixture now adds two real CPU lower-reader observations, and ten RED / seventeen additional GREEN cases add work. The revised walltime is an uncertain buffered bound, not observed performance. The retained 32 GiB is diagnostic headroom from prior completed RED execution, not a proven memory requirement, receiver upper bound or GPU feasibility result. No retry follows a failure or timeout.

## What is NOT done

Compute-node correction RED/GREEN, scoped independent re-review, task acceptance and Task 4 are outstanding. No genuine fresh-process cold/warm measurements, real receiver allocation/resource record, source publication, numerical rerun/aggregate, scheduler action, git, RS, SSH, transfer or model execution was performed by this worker. No existing test was dropped. Frozen native worktree/scientific exports and the unrelated running jobs remain untouched.

The original lower transport reader is unchanged: two entry reads/hash passes, one target parse/freeze and zero receiver target writes. Its explicit final full-witness check is the third read. New deployment/measurement validation reads small evidence objects and performs CPU/mount metadata observations; it adds no target payload scan. CPU fixture measurement passes are separately labeled and do not redefine the runtime receiver recipe.

All genuine source/resource/BASE/numerical/paired-M1/root-allocation gates remain. An explicit synthetic cold scope does not establish cold behavior or production admission. Genuine record creation and source-bound operational timing remain separately reviewed work.

## Open questions

Root owns submission, terminal accounting, exact-output review, scoped review-225 reround and Markdown lint/report-number checks. Return both shard manifests, baseline RED manifests, JUnit and original-validator preflight logs before task acceptance.

Re-review should explicitly inspect comparability of measurement cgroup applicability versus the receiving process. The schema validates declared applicability/scope and the post-reader path checks actual applicable peaks, while a separate explicit equality check between recorded and current applicability is not present. This is disclosed for reviewer judgment; no operational resource evidence or admission is claimed.

No user scientific decision or new spending authorization is requested by this handback. The packet and five owned candidate files are frozen read-only.
