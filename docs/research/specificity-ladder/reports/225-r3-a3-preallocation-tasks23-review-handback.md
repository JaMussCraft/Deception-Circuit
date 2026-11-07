# A3 Tasks 2–3 final comparability correction review

Status: handed-back

## What changed

Reviewed only the narrow final R225-B scope helper, its receiver/completed-intake calls, cold/warm consistency check and five new seam regressions. No remaining static findings in this correction. R225-A’s earlier native-route source closure is preserved. Root may proceed with source-bound CPU test shards; final source acceptance still requires actual both-environment results.

`_reconcile_prepared_observation_scopes` requires current process scope and cgroup scope availability, then compares each measured phase’s process scope, cgroup applicability and semantic cgroup scope with the current receiver. Different job-specific cgroup paths remain permissible. The loader invokes this before peak comparisons/model entry. Completed intake invokes it against the original receipt’s receiver observations. Measurement validation independently rejects cold/warm scope or applicability disagreement. This closes accepted183-r2 `receiver_observation_contract`’s missing/incomparable-observation requirement without introducing another authority or requiring genuine measurements at this stage.

## How verified

Independently reran the previous counterexample using unchanged AST-extracted preserved-r3/current loader process checks plus the new helper, without runtime imports. Both applicability mismatch directions pass r3 and reject the correction. Matching semantic scopes with different cgroup job paths pass; cold/warm disagreement rejects. The probe completed in approximately one quarter second. Evidence: `.superpowers/sdd/plan-a3/preallocation-task23-review225/r3/comparability-probe.json`.

Runtime SHA is `aea07dbf153824f373be70629dd24edc28dd6566cafa5955f43c69fd1119ec90`; frozen r4 source-pins SHA is `e525683d15bae1106c0d8fb4ad8723ffa31f2591e662ee541aa05b98c9cad0cc`. Native adapter, workload, workload tests and original runtime tests are byte-identical to preserved r3. Prior prepared tests remain a byte prefix. Inspected the new correctly anchored regressions for both receiver mismatches, cold/warm disagreement and both completed-intake mismatches, and the five-case baseline RED wrapper requiring attributable DID NOT RAISE failures against preserved r3. No observer helper patches were introduced for this RED packet.

## Execution evidence

No full/native tests, scheduler/remote calls, model runs or operational measurements were performed. Only the small pure AST probe ran. The root-owned packet expects five attributable r3 RED cases and 223 GREEN cases per interpreter, with no acceptance claim before actual successful completion/source-pin review. The probe is a semantic comparison check, not genuine resource or numerical evidence.

## What is NOT done

No source publication/acceptance, Task4 closure, genuine producer/cold-warm receiver/RAM measurements, BASE equality acceptance, fresh numerical or GPU admission. Those gates remain separate. No source edits, git, RS, jobs, remote operations or extra agents. No author final report was read.

## Open questions

No new decision or static correction is requested. Root should run and inspect the exact frozen both-environment packet, then decide source acceptance only if actual five-case RED and all 223 GREEN cases per environment pass with valid provenance and pins. Root owns Markdown lint under the worker’s no-RS instruction. Review evidence and verdict are in `preallocation-task23-review225/r3/`.
