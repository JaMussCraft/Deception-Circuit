# Hand-back 281: Native validation failures, bounded diagnosis

Agent: Sol. Status: resolved read-only diagnosis; no correction implemented. Both validation jobs were still running in the supplied observations.

## What changed

Only this report and the non-native probe below were added. No candidate, test, packet, job, or authority artifact was edited.

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-failure281/diagnosis/digest_probe.py`
- `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/281-handback.md`

Source locations used below:

- Runtime: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-preallocation-candidate183/component_analysis/a3_direction_runtime.py`
- Workload: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-preallocation-candidate183/component_analysis/a3_direction_workload.py`
- Suite: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task23-green-r6-r2-sharded/suite/test_a3_prepared_pilot_target.py`
- Fixture: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-preallocation-candidate183/tests/a3_prepared_integration_cases.py`
- Pipeline: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_direction_pipeline.py`
- Existing cost tests: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_a3_direction_workload.py`

### Cost counterfactual: stale receipt lookup key

Suite lines 717–720 obtain a proof map for the original receipt, then deepcopy the receipt and zero startup and proof-validation seconds, while reusing that map. Runtime lines 3031–3041 key the map by `(workload.digest(receipt), packing_id)`. Workload line 1230 recomputes the whole receipt digest, and lines 1248–1251 retrieve by that digest before checking the proof's numeric-evidence digest. Workload lines 104–106 hash all JSON fields.

Changing either timing field changes the receipt digest even though the nested packing evidence is identical. The failed lookup returns `None`; the error is the combined type/digest requirement at workload line 1250. This is not evidence that `proof.source_digest` differs from `evidence_sha256`. `_PackingProof.source_digest` binds the independently validated numeric evidence, minted at workload lines 1095–1114 after `_packing_evidence` validation at 1146–1148. The receipt digest and evidence digest serve different purposes.

The observed trace establishes that the original native projection at suite line 718 returned, then the counterfactual failed at line 720. Production semantics are appropriate: an original receipt proof table is not indexed for a modified receipt. The fixture constructs an invalid input pair for this API.

Smallest meaningful candidate correction: obtain `baseline_proofs = r._cost_packing_proofs([baseline])` and pass that map to the existing counterfactual `project_cost` call. Retain the original delta assertion at suite lines 721–722 and every envelope/publication assertion. This invokes the existing completed numeric reader and checks the unchanged numeric paths, byte references, mapping, and evidence digest at runtime lines 3034–3040; it neither forges a proof nor changes production authentication. Keep the counterfactual in memory and explicitly describe it as cost algebra, never completed execution evidence or authority. Do not publish or re-sign the changed receipt.

Existing patterns support using maps matched to the current receipt: existing cost-test lines 680–692 construct a map only after receipt reference substitution and rebuild its receipt key for an explicit tamper test while keeping genuine immutable numeric proofs; suite runtime-test lines 1662–1669 pair authenticated receipts with `_cost_packing_proofs(receipts)` for the unchanged full projector. The proposed correction has not been exercised natively.

### Missing preparation: validation exception contract gap

Suite lines 750–775 remove only `origin.target_preparation_reference` from an otherwise production-shaped completed test artifact, then expect `ValueError` or `FileNotFoundError`. Saved observation 02 shows this reaches `_completed_pilot_source`, runtime lines 2748–2751, after the original admission binding has passed. Its `resolved_object` helper at line 2714 directly indexes `origin[name]`, so the intended missing-reference rejection escapes as `KeyError`.

This is an API error-normalization defect, not acceptance of an unauthorized receipt and not the earlier fixture mutation defect. The narrower legacy case can reject earlier because its original admission lacks a binding; it does not establish that missing individual origin references use the expected error contract. The transport reader already normalizes malformed shape failures to `ValueError` at runtime lines 282–283, and neighboring completed-source checks consistently use `require`.

Smallest meaningful candidate correction: add an explicit `require` for a dictionary reference and a usable path before dereferencing it in `resolved_object`, then retain `object_reference(path) == ref` and `read_object(path)` unchanged. For the exact observed failure, a presence/type requirement on `origin.get(name)` suffices; checking the path shape there also prevents an adjacent raw `KeyError` for malformed reference objects. Do not catch every exception around the full authentication function, broaden accepted test exceptions, or skip byte/reference/authority checks. Retain the existing missing-preparation test as the native regression. This recommendation has not been implemented or exercised.

### Slow selected admission case: expensive setup is plausible; phase unresolved

Suite lines 444–447 construct and fully anchor `PreparedCase(selected=True, part='selected')` before appending bytes to the selected marker. Only then do lines 464–465 call the expected-rejection loader. Thus the long case may still be constructing its valid fixture rather than rejecting the damage.

Fixture lines 83–94 trim synthetic selection/utility rows while explicitly retaining task/seed coverage, all assessment/calibration axes and invocation classes. Lines 144–146 build complete selected backing and then the selected-pilot inventory. `_complete_selected_backing` fits actual synthetic arrays at 161–174, writes nested group/shard/key validation evidence at 176–197, then invokes the original freezer at 198–200. Pipeline lines 657–701 read/validate backing, scan validation rows for each fit record, select each task/seed and freeze null axes. Pipeline lines 324–337 construct 199 assessment and 32 calibration axes per selected record; fixture line 200 expects nine selected records. These are bounded constructions, not a wait loop.

Fixture `anchor` lines 244–275 calls preparation, reads the target, and measures the reader twice through `receiver_fixture_evidence` lines 44–47. Runtime preparation lines 426–439 independently validates the pilot, explicitly rebuilds the pilot, builds the remaining target, then independently validates the target. Each `_validate_inventory` independently calls `build_inventory` at workload lines 812–819. Consequently repeated large graph construction, serialization, hashing, decoding and accounting are source-supported explanations for sustained CPU and memory usage.

The padding loops at workload lines 451–457, 481–487 and 601–603 append an element on every iteration toward a finite configured size. Runtime graph accounting at lines 166–179 is cycle-safe. Its fixed-point loops at lines 273–280 deserve awareness because they repeat whole-graph scans, but source does not show a reason for nonconvergence: they update an integer retained-size field until its representation size stabilizes. There is no source evidence here establishing an infinite loop or the current native program counter. Supplied observations of rising CPU and moderate memory are compatible with active work but cannot identify the phase or establish eventual completion.

## How verified

Read the saved observations and cited source using `cat`, `rg`, and numbered `sed` excerpts. No native imports, pytest, scheduler/SSH commands, job inspection, trace injection, git, or agent spawning occurred.

```bash
/sw/external/python/anaconda3/bin/python3.9 /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-failure281/diagnosis/digest_probe.py
```

Observed exit 0. The AST-extracted native `digest` function produced original digest `df2b1d01e4ab65c02af33c7c36c1c3be3db3485e94ff11d83d697083bacccdf3` and counterfactual digest `7f96c19297674b15948a660f12f206d97f02494c3c706057d40d83e517cf3752` for a tiny synthetic dictionary. Evidence stayed equal, original lookup found its marker and counterfactual lookup missed. This establishes only digest/key behavior, never native proof acceptance, cost correctness, or completion. The dictionary marker is not a packing proof.

## Execution evidence

- Native jobs: supplied observations from Delta identify running Bridges jobs 50319105 and 50319108. This agent did not query or run them.
- Native state: in progress, no terminal exit available. Observation 02 records two failed call phases in shard zero; no suite-completion claim is made.
- Case totals: supplied checkpoints report shard zero at 74 of 112 and shard one at 49 of 111; these are historical observations, not current counts.
- Baseline reproduces: unavailable; no native baseline execution performed here.
- Provenance: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-failure281/observed-phase.json` binds the first saved monitor by SHA-256; `observed-phases-02.json` in that directory binds the later saved monitor. No new `run_manifest.json` or commit was produced.
- Local probe: exit 0, one synthetic original/counterfactual pair, no application import. Native acceptance remains not yet verified.

## What is NOT done

No fixes, performance changes, authority rewrites, new native runs, narrowed controls, reduced scope, cancellations, retries or traceback injection. Earlier correction 265 was not reopened. Original complete suites across both environments and final gates remain outstanding. Native resource usage and the slow case's exact phase were not independently inspected.

## Open questions

- Let the orchestrator consolidate terminal outcomes from both existing jobs before choosing a correction; default is preserve current jobs and bounds.
- Does the selected case finish within its existing bound? Source cannot answer timing; default is await existing monitor/terminal evidence without injection or cancellation.
- Does rebuilding the counterfactual proof map preserve the original native delta assertion, and does explicit missing-reference validation satisfy the unchanged rejection test? Default is the narrow candidates above followed by authorized full native validation, with original authority checks and all cases retained.
