# Code review — ticket 01, worktree, environment and circuit intake

Fixed point: `6b62fbf` (branch base). Reviewed: `6b62fbf...HEAD` on branch
`component-analysis`, three commits:

    1aaacdb  Let circuit intake be reused without building an evaluator Session
    b7eaff3  Coarsen any circuit expression to Components and write the head table
    11dd53a  Prove nnsight reaches every boundary ADR-0001 names, and pin the ones that bite

**How this review was run.** The `mattpocock-skills:code-review` skill spawns
one sub-agent per axis. Both sub-agents ran to completion here but ended
without delivering a report, and neither could be resumed (`No transcript
found for agent ID`). Per the agent brief — "If the code-review skill cannot
spawn its own sub-agents from where you run, do both axes (Standards, Spec)
yourself in one pass and say so in the report" — both axes below are the
author's own pass over the diff. They are therefore not independent of the
author, which is the one thing the ticket's last checkbox asks for; the
orchestrator may want a fresh reviewer on this diff.

Standards sources consulted: `CONTEXT.md` (glossary; its `_Avoid_` terms),
`docs/adr/0001-component-analysis-on-raw-hf-model.md`,
`docs/research/interp-tooling.md`, and the surrounding code as the house-style
statement (`evaluation/circuits.py`, `evaluation/masks.py`,
`evaluation/algebra.py`, `evaluation/suite.py`, `tests/test_end_to_end.py`).
Spec sources: the ticket, `spec.md` (Implementation and Testing Decisions) and
the agent brief.

---

## Standards

### Hard checks (all pass)

| Check | Result |
|---|---|
| nnsight imported outside `component_analysis/hooks.py` | none; enforced by a test that parses the package |
| Prunable wrapper instantiated on the analysis path | none; the smoke script builds a plain `LlamaForCausalLM` |
| Glossary `_Avoid_` terms in new code, tests or docs | none |
| Tests assert at caller-visible seams | yes: written files, returned Components, returned rows |

### Findings, all addressed

1. **Speculative Generality — `resolve_circuit_specs` was dead code.** The
   prefactor added a keyword entry point that nothing called; the CLI went
   through `resolve_circuits(cli)` instead. An untested seam added "for later"
   is exactly the smell. *Fixed:* `component_analysis/intake.py` now resolves
   through the keyword entry point, and
   `test_circuits_resolve_without_an_evaluator_session` calls it directly with
   no argparse namespace, which is what the ticket's prefactor checkbox
   actually asks for.

2. **Speculative Generality — unused `KINDS` constant** in
   `component_analysis/components.py`. *Fixed:* removed.

3. **Mysterious Name — `cells_intake`.** The parameter carried the resolved
   intake, not cells. *Fixed:* renamed to `resolved` throughout
   `analyze_components.py`.

4. **Order-dependent test.** `test_the_intake_layer_does_not_import_nnsight`
   asserted on process-wide `sys.modules`, so it passed or failed on whether
   an earlier test in the session had imported nnsight first — and it did
   fail once the nnsight-gated module was added ahead of it. *Fixed:* the
   probe now runs in a fresh interpreter via `subprocess`, so the assertion is
   about the package rather than about test ordering.

5. **A too-loose skip gate, and a wrong premise in the brief.** The brief says
   nnsight "cannot install" in the login-node base env. It is in fact already
   there at **0.5.12** (for the parent Alignment repo), so
   `pytest.importorskip("nnsight")` did *not* skip in the base env and ran
   0.7.0 assertions against 0.5.12. *Fixed:* `tests/test_nnsight_hooks.py`
   skips unless the installed nnsight is exactly the pinned 0.7.0, with the
   reason stated in the module docstring.

6. **Inconsistent branch in `mlp_component`.** One branch hard-coded
   `head_gate_active=True` where the other read the block gate. Equivalent by
   construction, but two spellings of one idea. *Fixed:* both read
   `_block_gate`.

### Judgement calls left as they are

- **Duplicated Code (minor).** `components._block_gate` overlaps
  `algebra.mlp_blocks_live`. Kept separate: `_block_gate` is generic over the
  three coarse keys, and importing `evaluation.algebra` into `components.py`
  for a three-line helper buys a dependency for nothing.
- **`head_gate_active` on an MLP row** is the `mlp_blocks` gate, not a head
  gate. The column name is fixed by the ticket; the meaning is documented on
  the `Component` dataclass and in the head-table module docstring. Flagged to
  the researcher rather than renamed, because later tickets and any
  already-written downstream code expect the ticket's spelling.

---

## Spec

### Ticket checkboxes

| Checkbox | State |
|---|---|
| Glossary, ADR-0001, tooling doc committed before the worktree was cut | verified as `6b62fbf`, ticked |
| Worktree on branch `component-analysis` | verified, ticked |
| nnsight 0.7.0 in mgnp; smoke script traces the tiny Llama on CPU | done; `pip install --dry-run` checked first, transformers 5.13.0 and torch 2.11.0 asserted unchanged after |
| Prefactor: resolution callable without a Session; evaluator tests still pass | done; no new failures by name in either env |
| New package and CLI; `--dry-run` coarsens and writes the head table | done |
| Columns kind, layer, index, kv_group, head_gate_active, active_neuron_count, one per `--reference` | exact; reference columns are `reference.<NAME>` |
| Test: coarsening agrees with the evaluation package, incl. a leaf-only delta | done |
| Test: CLI dry-run writes the head table and nothing else | done |
| Verified on the real SDR nls0.3 run and its honest twin | done, login node, no GPU |

### (a) Missing or partial

Nothing in ticket 01's scope. Two things are deliberately deferred and named
as such in the code: `hooks.py` holds the model loader only (the ticket says
"with the model-loading function only"), and the CLI without `--dry-run` exits
with a message saying the model-loading analyses arrive with later tickets
rather than pretending to run.

### (b) Scope creep

- **`tests/test_nnsight_hooks.py`** is beyond the ticket's two named tests. It
  is kept because the spec asks for "invariant tests on a tiny random Llama to
  pass before any GPU run" (user story 41) and because the agent brief's "one
  nnsight hook module" rule is otherwise unenforced. It costs 6 tests that
  skip outside mgnp.
- **`--data-dir`, `--test-samples`, `--std-variant`, `--hf-token`** on the new
  CLI are not asked for by name. They are the arguments
  `evaluation.context.resolve_train_args` reads off the CLI when resolving a
  task, so task resolution does not work without them.
- **`.gitignore` gains `outputs/_analyses/`**, one additive line, so that the
  cell directories this CLI writes are not committed.

Everything else in the diff maps to a checkbox.

### (c) Implemented but possibly wrong

1. **Is the coarsening-agreement test tautological?** No. It computes the
   expected set from `evaluation.masks.coarsen_masks`, which is the evaluation
   package's own coarsening and shares no code with
   `component_analysis.components`. The two reach the same answer by different
   routes: `coarsen_masks` keeps the discovered head and block gates verbatim,
   while the Component rule reads the leaf gates. They agree because
   `validate_hierarchy` ties the two together for heads.

   Where they genuinely disagree is asserted as its own test: an `mlp_blocks`
   gate left open over dead fine gates is live to `coarsen_masks` and is *not*
   a Component, because gates AND together and that MLP writes nothing. That
   divergence is a deliberate reading of the glossary's "any active gate"
   rule, and the researcher should confirm it. It cannot arise in a composed
   circuit (`_derive_coarse` re-derives `mlp_blocks` from the fine gates) and
   did not arise on the real SDR run.

2. **`--reference` names are kept out of circuit resolution.** A reference
   bound with `--circuit` instead would be evaluated as a circuit of its own,
   because `_expression_list` defaults to one atomic circuit per binding.
   References are resolved separately and a name bound both ways is refused
   with a message saying why. Tested.

3. **Shared-file discipline for the parallel branches.** The diff touches two
   shared files. `evaluation/circuits.py` gains three functions and changes no
   existing signature. `evaluate_circuit.py` loses 27 lines of inline
   `add_argument` calls, replaced by two calls to the shared registration —
   the one hunk a sibling branch could conflict on. Everything else is new
   files.

---

## Summary

Post-review follow-ups, also applied: the ADR "one hook module" guard moved to
`tests/test_component_analysis.py`, since it parses source and needs no
nnsight, so it now runs in both environments; `load_analysis_model`'s keyword
arguments checked against the installed nnsight source (`dispatch` is consumed
by `MetaMixin.__init__` in 0.7.0; `device_map` and `dtype` reach
`from_pretrained`), with the docstring stating that the function is untested
against a real load.

Standards: 6 findings, all addressed; the worst was `resolve_circuit_specs`
shipping as dead code, which also left the ticket's prefactor seam untested.
Spec: 3 scope-creep notes, all justified above, and 1 open question for the
researcher (the open-MLP-block divergence in finding (c)1). No missing
requirement in ticket 01's scope.

The review is not independent of the author; see the note at the top.
