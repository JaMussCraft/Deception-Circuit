# Hand-back: Pure ladder design

Agent: Codex worker. Ticket: `docs/research/specificity-ladder/plan-ladder.md`, sample/set/donor task. Status: resolved for pure implementation; empirical freeze intentionally deferred.

## What changed

Files for the orchestrator to commit from the worktree:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/ladder_design.py`: pure balanced assessment design, exact recorded group parser, answer-contribution candidate screen, donor specifications and separate input hashes.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_ladder_design.py`: behavioral tests for sampling, validation, labels, mover thresholds, provenance, donor identity, alignment and optional support.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/28-ladder-design-handback.md`: this report.

The module documents the normalized row and explicit token-layout contract. Conditions are D, H, F, I and user_neutral; streams are clean and corrupt. Token lists are full unpadded sequences. Both role and content boundaries must be explicitly supplied and equal before absolute-position mapping; equal padding is insufficient. Unsupported mappings carry empty position lists and an explanation.

The required `mover_selection_ids` keyword preserves this task's exact artifact order. The separate `selection_ids` argument is the union excluded from assessment. Neither is inferred from old assessment data. The lead approved this interface clarification and owns the plan update.

Same-instance H-derived replacement maps D to original H and I to its own user-neutral twin. H identity and any token-identical replacement carry explicit no-op/degenerate flags and cannot supply a collateral gate. The item-swap donor is the recipient's own condition and opposite designation stream over all unpadded positions. F replacement needs explicit matching boundaries. Optional different-instance donors match words, item identity, template and boundaries; I additionally matches request provenance. Sorted candidates and a stable recipient/stream/seed hash give deterministic independent draws. Missing optional support leaves assessment membership unchanged.

The mover screen consumes already oriented correct-minus-other H DLA arrays with head columns in input order, records clean-mean ranks and joint positive-row counts, keeps every MLP, and reports the actual removed intersection. Empty removal is explicitly a duplicate group. SDR's recorded set remains descriptive; the output makes no validated-copying claim.

## How verified

Working directory for both commands: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_ladder_design.py tests/test_sampling.py -p no:cacheprovider -q
```

Observed: all focused design and existing sampling tests passed.

```bash
OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_ladder_design.py tests/test_sampling.py -p no:cacheprovider -q
```

Observed: all focused design and existing sampling tests passed.

Tests were written first. The initial absent module failed import; later adversarial tests failed on missing source-split, donor-label, request-span and component-key checks. The exact ordered mover-selection keyword and per-recipient donor randomization each had a separate failing test before implementation.

Read-only CPU inspection of the actual primary selection artifacts showed the expected `instance_ids` field, unique IDs and usable provenance metadata for FAR, SDR and SER. The existing phase-one reading artifact supplies exact `rab[task].deciding_numbers.members` lists. No real assessment draw was performed.

The ordinary shell launcher failed before execution because its sandbox could not create its temporary directory. Explicit escalated calls for the authorized worktree operations succeeded.

## Execution evidence

Not applicable: no runs.

## What is NOT done

No empirical design, group selection or donor files were frozen. Scored user-control pools and source/provenance checks remain prerequisites. No DLA inference, model/GPU execution, notebook execution, paid API call, benchmark, scheduler submission, git command or baseline/data-builder edit occurred. The whole repository suite was not run; the assigned validation scope was focused tests in both supported interpreters.

No CLI, adapter/tokenizer, model-screening validator or source-file reader was added. The later CLI must validate original selection provenance and pass the exclusion union plus exact task-specific ordered selection IDs. It must derive explicit token boundaries from actual source layouts and preserve source-file hashes and builder alignment assertions. Missing layouts remain unsupported.

## Open questions

No scientific interface questions remain open for this task. The lead should update the plan signature with mandatory `mover_selection_ids` and arrange the independent implementation review before empirical selection. Default: preserve the explicit contract and keep empirical freezing deferred until the scored pools are ready.
