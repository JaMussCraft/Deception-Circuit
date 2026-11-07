# Hand-back 317: Candidate producer original-input inventory

Agent: Terra inventory worker. Status: handed-back.

## What changed

Created `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/producer-input-inventory317/inventory.json`. It contains 326 proposed `{path, sha256, bytes}` file rows and 17 `{path, literal_target}` alias rows: five export aliases, six MMLU cache links and six model metadata links. Model weights and new canonical outputs are excluded. Original matched data, manifest-listed source files, A1 design/selection/completion, historical source and selection references, root ruling, settings, IOI names, registry targets and bounded model/MMLU metadata are included.

## How verified

Read producer 311 context, closure contract and `common.py`, the matched build manifest, the original A1 parent hash maps, packet 247 input context, the native `a3_pipeline.prepare` and A1 selection/registry readers, and the model-cache reference. Enumerated the bounded matched tree and MMLU cache; checked metadata blob hashes against the original model reference. No native modules were imported. Historical manifest digests are individually marked in `basis_by_path` as unverified when reused with current stat only; root must rehash these before binding. The five export aliases are declarations and require actual binding checks.

One concrete historical/current distinction is recorded: the A1 design's old primary directions-registry digest differs from current bytes. The file row carries the current hash, while the gap preserves both hashes. Native `grader_registry` reads current primary and export registries and checks the frozen grader field; this difference alone does not establish a failure. Root must review the registry semantics and source-bound checks.

## Execution evidence

Not applicable: no runs.

## What is NOT done

This is a partial, unbound inventory and not admission or evidence of native execution. Source310 code is separately bound. The parent JSON reference walk is bounded and heuristic, so all transitive parent, protection, grader, IOI generator, dataset and runtime references are not proved complete. Some rows reuse historical hashes and cannot be used as authenticated current bytes until rehashed. Candidate export aliases, physical mappings, startup/cache behavior, remote bytes and access have not been tested. No jobs, copies, Git, RS, SSH, native imports or tests occurred.

## Open questions

- Root should resolve the historical/current registry distinction and independently compare native freeze reads against this list, then rehash all selected bytes and verify literal aliases in the actual namespace. Default: do not bind or dispatch from this partial list until closure review succeeds.
