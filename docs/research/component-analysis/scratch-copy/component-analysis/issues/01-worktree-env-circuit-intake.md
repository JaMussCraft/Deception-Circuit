# 01 — Worktree, environment, and circuit intake

**What to build:** A researcher can run the new component-analysis CLI in dry-run mode on the login node against any circuit expression the evaluator accepts, and get back a head table listing every Component (head or MLP block) of that circuit with its head-gate state, active-neuron count, KV group, and membership in each named reference circuit. This is the intake layer every later analysis joins onto, delivered end to end from CLI flag to written table.

Also the groundwork: the implementation worktree exists, the environment has nnsight, and the docs from the grilling are committed so the branch carries them.

**Blocked by:** None — can start immediately.

**Status:** resolved

- [x] The glossary (CONTEXT.md), ADR-0001 and the tooling research doc are committed on the current branch of the circuit repo before the worktree is cut.
- [x] A worktree exists at `.claude/worktrees/component-analysis` on branch `component-analysis`; all subsequent tickets work there.
- [x] nnsight 0.7.0 is installed in the mgnp conda environment; a smoke script traces one forward of the tiny random Llama from the test helpers under nnsight on CPU.
- [x] Prefactor: circuit resolution (bindings plus set-algebra expressions) is callable without constructing the evaluator's Session, and the evaluator still passes its existing tests after the extraction.
- [x] A new analysis package and CLI entry point exist beside the evaluator; `--dry-run` resolves circuits, coarsens to Components by the "any active leaf gate" rule, and writes `head_table.csv` and `head_table.json` under `outputs/_analyses/<suite>/<circuit>/<task>/`.
- [x] Head-table columns: kind, layer, index, kv_group, head_gate_active, active_neuron_count, and one membership column per `--reference NAME=RUN_DIR` binding.
- [x] Test: coarsening of a mask object agrees with the evaluation package's coarsening on the tiny model, including a leaf-only delta circuit.
- [x] Test: CLI-seam dry-run on a throwaway tiny run directory (mirroring the existing end-to-end test) writes the head table and nothing else.
- [x] Verified on the real SDR nls0.3 run and its honest twin: the dry-run head table lists the expected Components and honest-twin membership on the login node with no GPU.
- [x] Subagent code review against the spec completed and findings addressed. (Both axes ran, but by the author under the brief's fallback -- the skill's sub-agents could not deliver, so that pass was not independent. A separate reviewer has since reviewed the same diff; both passes are summarised in Comments.)

## Comments

### What was built

- **`component_analysis/`** (the package name avoids `analysis.py`, the node-mask
  module already at the repo root; noted here as the ticket asks).
  - `components.py` — mask object to Components. `circuit_components(masks, *,
    num_heads, head_dim, num_kv_heads)` returns `Component(kind, layer, index,
    kv_group, head_gate_active, active_neuron_count)`, ordered by layer with a
    layer's heads before its MLP block. `is_component_of(component, masks, *,
    num_heads, head_dim)` is the reference-membership test.
    `count_components(components)` is the census the dry run prints.
  - `head_table.py` — the shared helper later tickets build on.
  - `intake.py` — `resolve_intake(cli) -> Intake(circuits, tasks, references,
    reference_run_dirs, geometry, model, base_run_dir)`, plus
    `num_key_value_heads(model_name, *, hf_token, override)`,
    `analyses_root(cli, base_run_dir)` and `cell_dir(root, circuit, task)`.
  - `hooks.py` — the single nnsight module. Ticket 01 fills in
    `load_analysis_model(model_name, *, device, hf_token, attn_implementation,
    dtype)` only.
- **`analyze_components.py`** — the CLI, beside `evaluate_circuit.py`.
- **`scripts/smoke_nnsight.py`** — the nnsight smoke test, runnable on its own
  and reused by `tests/test_nnsight_hooks.py`.
- **Prefactor** in `evaluation/circuits.py`: `add_circuit_args(parser)`,
  `add_task_args(parser)` and `resolve_circuit_specs(**kwargs)`.
  `evaluate_circuit.py` now calls the two registration functions instead of
  declaring the flags inline; no existing signature changed.

### Head-table helper API (`component_analysis/head_table.py`)

    KEY_COLUMNS = ("kind", "layer", "index")
    BASE_COLUMNS = KEY_COLUMNS + ("kv_group", "head_gate_active",
                                  "active_neuron_count")
    PROTECTED_COLUMNS = ("role_confirmed",)

    row_key(row_or_component) -> (kind, layer, index)
    rows_from_components(components, extra=None) -> [row]
    columns_of(rows) -> [column]                      # base columns first
    merge_columns(rows, updates, *, namespace=None) -> [row]
    write_head_table(cell_dir, rows, *, meta=None) -> {"csv": path, "json": path}
    load_head_table(cell_dir) -> [row]                # from the JSON twin

`merge_columns` takes `{component key or Component: {column: value}}`, writes
each column as `<namespace>.<column>`, gives every row the column (None where
the analysis said nothing) so rows never go ragged, appends a row for a key
that is not in the table yet (the completeness sweep will need that), and
raises on any attempt to write `role_confirmed` or a key column. It does not
mutate its input. JSON is the typed source of truth; the CSV is a view where
None is blank and a boolean is 0/1.

**Hook module path:** `component_analysis/hooks.py`. A test parses the package
and fails if any other module in it imports nnsight, so the ADR's "one file to
migrate to 0.8" property is enforced rather than hoped for. That test is pure
source parsing, so it lives in `tests/test_component_analysis.py` and runs in
both environments rather than only where nnsight 0.7.0 is.

`load_analysis_model` is **not exercised by any test** — it needs real weights
and a GPU — so its keyword arguments were checked against the installed
nnsight source instead: `dispatch` is consumed by `MetaMixin.__init__` in
0.7.0 (the only other mentions in the package are docstrings), and
`device_map` and `dtype` pass through to `from_pretrained`, `dtype` being
transformers 5.x's spelling of the `torch_dtype` that `models/__init__.py`
still uses for the 4.57 login env. The first ticket that loads a model should
make a successful load its own first assertion.

### Environment

nnsight 0.7.0 installed into `mgnp`. `pip install --dry-run` first: the
"Would install" list named nnsight, accelerate, ipython and their
dependencies, and neither transformers nor torch, so the install went ahead.
Asserted after: transformers 5.13.0, torch 2.11.0+cu128, nnsight 0.7.0.

Two nnsight 0.7.0 behaviours the smoke script pinned, both now tests, because
their error messages point away from the cause:

- Envoy accesses inside a trace resolve lazily against the running forward and
  must be written in **execution order**. Reading `o_proj.input` before
  `q_proj.output` ends the trace with `MissedProviderError: ... q_proj.output
  was not provided`, naming the module that came too late rather than the one
  that came too early.
- Under SDPA, `self_attn.output[1]` is None and `.save()` on it never binds the
  name — an `UnboundLocalError`, not the None transformers documents. Save
  `self_attn.output` and index afterwards.

**Correction to the brief.** The brief's environment table says nnsight
"cannot install" in the login-node base env. It is already installed there, at
**0.5.12**, for the parent Alignment repo. `pytest.importorskip("nnsight")`
therefore does *not* skip in the base env, and the nnsight tests gate on the
version being exactly 0.7.0 instead. Later tickets should do the same.

### Verified on the real SDR nls0.3 run

Login node, no GPU, `--dry-run`, with
`--reference honest=outputs/llama-8b-instruct_sdr/nls0.3_honest_noedge_260819-083525`.
Geometry read off the masks: 32 heads, head_dim 128, 32 layers. KV heads read
from the HF config (8, so 4 query heads per group); no weights downloaded.

| circuit | heads | MLP blocks | layers | heads with head gate open | shared with honest twin |
|---|---|---|---|---|---|
| `sdr` (atomic) | 68 | 3 | 15 | 68 | 53 of 71 |
| `sdr \ honest` at leaf granularity | 68 | 3 | 15 | 68 | 53 of 71 |
| `sdr \ honest` at head granularity | 17 | 1 | 9 | 17 | 0 of 18 |

Head-gate-level versus leaf-level, which is what the ticket asks to be
recorded: every one of the 68 head Components has its head gate open, so
within a single circuit the two levels never disagree — `validate_hierarchy`
forbids a live head with no live neuron. The distinction lives **between**
granularities, and the reference column recovers it inside one table:

- The 18 leaf-delta Components whose `reference.honest` column is false are
  **exactly** the 18 Components of the head-granularity delta (asserted set
  equality, and the head delta is a subset of the leaf delta).
- The leaf-granularity delta equals the atomic SDR circuit Component for
  Component. At nls0.3 every SDR head keeps at least one attention neuron the
  honest twin does not have, so subtracting the twin at leaf granularity
  removes no Component at all. Active neuron counts per head run 6 to 123 of
  128.
- Head-delta layers: 5, 8, 9, 13, 14, 17, 24, 27, 31. KV groups present: 1-6.

### Open questions for the researcher

1. **Analyse `delta__head`, not `delta__leaf`, first.** At nls0.3 the
   leaf-granularity delta is Component-for-Component identical to the whole
   SDR circuit: it removes nothing. The deception-specific cell for the first
   GPU analysis is therefore the head-granularity delta, 18 Components. This
   is a property of the runs, not of this code, but it decides which cell
   ticket 02 onwards should point at.

2. **User story 3's numbers match no SDR run in the worktree.** The story says
   "the 14 head-gate-level delta heads inside the 46 leaf-level ones". Every
   SDR sparsity pair was censused on the login node (heads/MLP blocks):

   | run | atomic | `sdr \\ honest` leaf | `sdr \\ honest` head |
   |---|---|---|---|
   | nls0.1 | 80/5 | 80/5 | 23/2 |
   | nls0.3 | 68/3 | 68/3 | 17/1 |
   | nls0.5 | 71/1 | 71/1 | 18/0 |
   | nls0.6 | 67/1 | 67/1 | 18/0 |
   | nls0.7 | 58/1 | 58/1 | 13/0 |

   The head-gate figure of 14 is close to nls0.7's 13, but **no** SDR leaf
   delta is 46, and the leaf delta never shrinks the Component set at any
   sparsity — the smallest leaf count here is 58. So "46 leaf-level" cannot be
   an SDR leaf delta from these runs; it is either another task, another
   sparsity that is not in the repo, or a different counting rule. Worth
   pinning down before the figure is quoted in a write-up.
3. **An MLP block gate left open over dead fine gates is not a Component here.**
   `evaluation/masks.coarsen_masks` would call that block live because it keeps
   the block gate verbatim; the glossary's "any active gate" rule applied to
   leaf gates says it writes nothing. `validate_hierarchy` permits the state,
   so it is reachable in principle. It does not occur on the SDR run and
   cannot occur in a composed circuit. Asserted as its own test; please
   confirm the reading.
4. **`head_gate_active` on an MLP row** holds the `mlp_blocks` gate. The column
   name comes from the ticket; the meaning is documented in the code.

### Tests

New, counted at `7554839`, this ticket's last commit:
`tests/test_component_analysis.py` (13, library seam),
`tests/test_analyze_components_end_to_end.py` (11, CLI seam),
`tests/test_nnsight_hooks.py` (5, nnsight 0.7.0 only). The 12 / 10 / 6 written
here earlier was stale: `b9ef272` added the prefactor-seam test and `7554839`
moved the one-hook-module guard out of the nnsight file into the library file.

Baseline on `6b62fbf`, both envs: 8 failed. Identical names in both:
`test_benchmarks.py::test_mask_judge_kwargs_and_roles_match_evaluate_py`,
`test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[far|sdr|ser]`,
`test_deception_common.py::test_length_matching_narrows_the_cross_task_median_gap`,
`test_deception_common.py::test_pressure_pools_are_well_formed[ser]`,
`test_deception_common.py::test_three_specs_registered`,
`test_deception_tasks.py::test_hyperparameters_are_identical_across_the_three_mechanisms`.

| env | baseline | final | new failures |
|---|---|---|---|
| login-node base (py3.9, transformers 4.57.3) | 8 failed, 562 passed, 20 skipped | 8 failed, 585 passed, 21 skipped | none (same 8 names) |
| `mgnp` (py3.12, transformers 5.13.0) | 8 failed, 563 passed, 19 skipped | 8 failed, 592 passed, 19 skipped | none (same 8 names) |

The base env's extra skip is `tests/test_nnsight_hooks.py`, which needs
nnsight 0.7.0.

No Slurm jobs were submitted: nothing in this ticket needs a GPU.

### Code review

`mattpocock-skills:code-review` against `6b62fbf`. Both of its sub-agents ran
but ended without delivering a report and could not be resumed, so both axes
were done by the author in one pass, as the brief allows — which means the
review is **not independent of the author**. Report:
`Alignment/.scratch/component-analysis/reports/01-worktree-env-circuit-intake-review.md`.
A fresh reviewer has since gone over the same diff; see **Independent review**
below and `Alignment/.scratch/component-analysis/reports/01-independent-review.md`.

Findings addressed (commit `b9ef272`): `resolve_circuit_specs` was dead code
and the prefactor seam untested, so intake now goes through it and a test
calls it directly; the "no nnsight import" test depended on test ordering and
now probes a fresh interpreter; the nnsight skip gate was too loose for this
cluster (finding 5 above); an unused constant removed; `cells_intake` renamed
to `resolved`; one inconsistent branch in `mlp_component` tidied.

Not addressed, deliberately: the minor overlap between
`components._block_gate` and `algebra.mlp_blocks_live` (keeping them separate
avoids importing `evaluation.algebra` into the pure coarsening module for a
three-line helper), and the `head_gate_active` naming on MLP rows (the ticket
fixes the column name; open question 4).

### Independent review

`Alignment/.scratch/component-analysis/reports/01-independent-review.md` — a
reviewer who wrote neither the code nor the self-review, on `6b62fbf..7554839`
read at tip `b6943b6`. Verdict: no missing requirement and no scope creep.
Every SDR nls0.3 number in these comments reproduced exactly; the coarsening
agreement was extended from the test fixture to all 62 loadable saved runs
across seven task families, with zero disagreements; and `load_analysis_model`
was run end to end on CPU against a locally saved tiny Llama, which this ticket
had left untested.

Five findings. Four are code and are fixed on branch `ca/01-fixes`, cut from
`b6943b6`; the fifth is a glossary decision.

1. **`hf_token` never reached the tokenizer** (`component_analysis/hooks.py`).
   nnsight 0.7.0's `LanguageModel._load` loads the tokenizer from a separate
   `tokenizer_kwargs` that defaults to empty, so a gated repo would load its
   weights and then 401 on the tokenizer. **Fixed** (`b63fba9`), with a test
   that fakes `AutoConfig`, `AutoTokenizer` and `AutoModelForCausalLM` and
   records which kwargs each loader saw. This was the must-fix before block C.
2. **`merge_columns` duplicated a row for a hand-built tuple key**
   (`component_analysis/head_table.py`): a key rebuilt from a CSV read carries
   string `layer` and `index` and missed the row it named. **Fixed**
   (`1deb63f`) by routing every key through `row_key`, with a test.
3. **Three docstrings gave a false reason** for keeping nnsight imports inside
   functions — the base env has nnsight 0.5.12, not no nnsight. **Fixed**
   (`7e3105d`) in `component_analysis/__init__.py`,
   `component_analysis/hooks.py` and `scripts/smoke_nnsight.py`.
   `docs/research/interp-tooling.md` says only that nnsight *0.7.0* does not
   install on Python 3.9, which is true, so it was left alone.
4. **CONTEXT.md's Component entry says "any active gate" where the code
   implements "any active leaf gate"** — open question 3 above. **Not a code
   change**; the glossary wording is being handled on the follow-ups branch.
5. **The coarsening-agreement test's name overclaimed**: its fixture has been
   through `validate_hierarchy`, so it would pass even if membership consulted
   the coarse gates. **Fixed** (`a0c746b`) by renaming it to
   `test_coarsening_matches_the_evaluation_package_on_a_hierarchy_valid_circuit`
   and renaming the discriminating test to
   `test_an_open_head_gate_over_dead_neurons_is_not_a_component`.

Raised but not acted on: no test covers the `KEY_COLUMNS` branch of
`merge_columns`; `analyses_root` assumes a run directory two levels under
`outputs/`, with `--output-dir` as the escape hatch; and renaming
`head_gate_active` later should be a deliberate `SCHEMA_VERSION` bump rather
than a quiet edit. The reviewer could not re-measure the 8-failure baseline or
the `pip install --dry-run` narrative; the baseline was re-derived on `b6943b6`
while fixing these findings and is still the same 8 names in both environments.

Suite on `ca/01-fixes`, judged by failure name against that re-derived baseline:

| env | baseline on `b6943b6` | after the fixes | new failures |
|---|---|---|---|
| login-node base (py3.9, nnsight 0.5.12) | 8 failed, 652 passed, 21 skipped | 8 failed, 653 passed, 21 skipped | none (same 8 names) |
| `mgnp` (py3.12, nnsight 0.7.0) | 8 failed, 658 passed, 19 skipped | 8 failed, 661 passed, 19 skipped | none (same 8 names) |

The three analysis files now hold 14 / 11 / 7 tests. The base env gains only
the head-table test; `tests/test_nnsight_hooks.py` still skips at module level
there, which is what the two new tests in it depend on.

### Shared files touched, for the rebase

- `evaluation/circuits.py` — three new functions, no existing signature
  changed. Additive.
- `evaluate_circuit.py` — 27 lines of inline `add_argument` calls for the
  `circuits` and `tasks` groups replaced by two calls to the shared
  registration. This is the one hunk a sibling branch could conflict on.
- `.gitignore` — one added stanza for `outputs/_analyses/`.

Everything else in the diff is a new file. Analysis outputs were deleted
before committing; no `core.*` files were present.
