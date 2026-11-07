# Task 4 correction 282: isolated draft

Status: draft prepared; no publication, replacement validation freeze, or native acceptance.

## Scope and attributable RED

Root's `task-4-correction282-brief.md` authorizes exactly two changes based on native failure observations in `plan-a3/validation-failure281/observed-phases-02.json`. The actual failed cases are `test_prepared_costs_and_envelope_are_charged` and `test_prepared_migrated_intake_and_legacy_rejection[missing-preparation]`. Those observations remain immutable and in progress; no new terminal outcome is asserted here. Jobs are on Bridges, observed by root from Delta.

Two complete source copies live only under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-correction282`:

- `component_analysis/a3_direction_runtime.py`: in `_completed_pilot_source.resolved_object`, require a dictionary reference and a nonempty string/pathlike path before the original byte-reference equality and object read. This converts malformed or missing reference shape to the existing `ValueError` contract. It adds no completed evidence, authority or unrelated reference schema requirement.
- `tests/test_a3_prepared_pilot_target.py`: rebuild `baseline_proofs` using the existing `_cost_packing_proofs([baseline])` and pass that map to the original projector for the explicit in-memory zero-cost counterfactual. Every original assertion is retained. The counterfactual is never published or re-signed.

Input runtime SHA-256: `aea07dbf153824f373be70629dd24edc28dd6566cafa5955f43c69fd1119ec90`.

Draft runtime SHA-256: `1d6c3886a7634641a8a4ad64135adeef34dcdac7ce6b388e8441df1bf2cea116`.

Input exercised suite SHA-256: `e2a7c5622508974fafafe016e9c3d1d55903302f646f05c5f35630570a1f6e86`.

Draft suite SHA-256: `2f89de3edb0ac5d513b98c018c6ab1393179b73d9ee67c64d725a064eaa09fb3`.

## Bounded checks

`pure_probe.py` was written and run against the original source before implementation. It AST-extracts only `resolved_object`, supplies a controlled reference/read boundary, and imports no native code. Nine malformed specimens fail the original boundary requirement with exit one: absent/null/scalar/list references, absent/null/integer/list/empty paths. Existing valid string and `Path` shapes traverse the original equality/read path; conflicting byte references reject. The draft passes the same specimens with exit zero. This is extracted-boundary evidence only: the dependency stubs do not establish actual artifact authentication.

After implementation, both `/sw/external/python/anaconda3/bin/python3.9` and `/u/swong2/.conda/envs/mgnp/bin/python` ran four bounded checks each: original boundary RED, draft boundary GREEN, the earlier non-native digest/lookup probe, and static scope/syntax comparison. Each subprocess had a twenty-five-second timeout. `pure-check-results.json` records all eight commands, exit codes and structured outputs; each expected status matched and stderr was empty.

The digest probe AST-extracts native `digest` only, applies it to a tiny synthetic receipt, and shows that the changed timing fields leave evidence equal but change the receipt lookup key. It neither constructs a packing proof nor calls native `project_cost`. Actual native cost acceptance remains outstanding.

`check_scope.py` compares every top-level AST node in both pairs. Only `_completed_pilot_source` and `test_prepared_costs_and_envelope_are_charged` change. Within the completed-source function, every statement outside `resolved_object` remains equal. The helper's original byte-equality `require` and read/return AST nodes remain equal. All 114 test assertion ASTs retain their order and content; decorators, parametrization/count declarations, imports and other functions remain equal. Both complete copies compile in memory under both interpreters, without application imports or bytecode writes.

`scope-pins.json`, `a3_direction_runtime.diff` and `test_a3_prepared_pilot_target.diff` hold the exact review boundary. Source pin checks ran before copying; final static comparison still reads the original active files and reports the same input hashes. No original file was written.

## Remaining gates and limitations

Root must consolidate both terminal validation outcomes, review this full diff independently and decide whether any further attributable failure belongs in the same correction. This draft alone does not freeze a successor source/packet or authorize a new job. The unchanged complete original case set, both environments, genuine BASE comparison and all source/resource/numerical/GPU gates remain. No performance change, traceback injection, authority rewrite, native import, target construction, job operation, Git or RS action occurred. Root owns lint/number checks and publication.
