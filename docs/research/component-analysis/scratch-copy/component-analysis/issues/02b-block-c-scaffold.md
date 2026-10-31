# 02b — Block C scaffold: shared forward passes, analysis registration, causal dataloader, Slurm script

**What to build:** The pieces tickets 03, 04, 07 and 08 all need and would otherwise each build from scratch on parallel branches: the shared nnsight forward passes in the hook module (capture, replace, eager attention), an analysis-registration seam in the CLI so each analysis is its own module that writes into its own subdirectory and adds its own head-table columns, a dataloader over the causal sample joined by instance id that yields both counterfactual pairs, the Slurm script mirroring the evaluator's, and the first real GPU load of the model through `load_analysis_model`. No analysis is implemented here; a stub analysis proves the seam.

**Blocked by:** 02 — Segmentation and stratified sample; 05 — Matched Honest Instructions (both merged).

**Blocks:** 03, 04, 07, 08 (their "Blocked by" lines gain this ticket).

**Status:** resolved

- [x] `component_analysis/hooks.py` gains three small functions, the only new nnsight access: `capture_forward(model, input_ids, attention_mask, *, components, positions=None)` runs one forward and returns the Readout logits, the per-Component outputs (head outputs read at the `o_proj` input split per head, MLP block outputs) and the residual stream at the Readout for the given Components; `replace_forward(model, input_ids, attention_mask, *, replacements)` runs one forward with the listed Component outputs replaced by supplied tensors (all positions, or a position mask) and returns the Readout logits; `attention_weights(model, input_ids, attention_mask, *, layer, heads, query_positions)` returns the attention rows for those heads under eager attention and restores SDPA afterwards. Each is a few lines; the ticket 01 gotchas (execution-order Envoy access, `self_attn.output[1]` under SDPA) are respected and documented at the function.
- [x] The interchange primitive is `replace_forward` fed with `capture_forward`'s outputs from the corrupt stream; tickets 07 and 08 compose it, they do not re-implement it.
- [x] `component_analysis/registry.py` (or equivalent): an analysis is a module exposing `NAME`, `SUBDIR`, `add_arguments(parser)`, `estimate(ctx) -> str` for `--dry-run`, and `run(ctx) -> dict of head-table column updates`; `ctx` carries the loaded model and tokenizer, the resolved circuit and Components, the segmentation, the causal sample, the dataloaders, the cell directory and the CLI namespace. `analyze_components.py` gains `--analyses NAME[,NAME]` (default: all registered), runs each in order, calls `merge_columns` with the analysis name as namespace, and rewrites the head table once at the end. Registration is a list in one place so sibling branches add one line each.
- [x] `component_analysis/dataloaders.py`: from `sample.json`'s instance ids (never the split indices; see ticket 02's `join_on`), build batches yielding clean and item-swap-corrupt `input_ids`/`attention_mask`, Target and Distractor token ids, the Readout position, and, when the Matched Honest survivors file exists for the task, the honest-instruction pair from `dataset.matched_honest.load_matched_honest` (clean-stream criterion, ticket 05) with its clause span. Instances in the sample that lack an honest counterpart are reported, not dropped, for the item-swap analyses. A descriptive-mode loader over the full test split exists for tickets 03 and 04.
- [x] `scripts/analyze_components.sbatch` mirrors `scripts/evaluate_circuit.sbatch` (partition, account, module loads, env activation, log path) and passes its arguments through to the CLI; `--dry-run` on the login node prints each registered analysis's estimate.
- [x] Tests (tiny 2-layer Llama from `tests/helpers.py`, library seam): `replace_forward` with no replacements reproduces the clean Readout logits; replacing every Component's output with its corrupt-stream capture reproduces the corrupt-run logits within tolerance (circuit set to every head and MLP block); replacing one head's output changes the Readout logits while a second `capture_forward` under that replacement shows the other heads of the same layer unchanged; `attention_weights` rows sum to one and SDPA is restored after the call; the dataloader joins by id and yields aligned pairs whose only differing positions are the item swap (item-swap pair) or inside the clause span (honest pair).
- [x] Test (CLI seam, monkeypatched loader as in `tests/test_analyze_components_end_to_end.py`): a stub analysis registered only in the test writes its JSON into its subdirectory and its columns appear namespaced in the head table; `--analyses` selects it; `--dry-run` prints its estimate and writes nothing beyond the ticket 01/02 dry-run files.
- [x] Verified on a GPU: one short Slurm job (A40 or A100, minutes) on SDR nls0.3 with the honest twin bound at head granularity delta, running the stub analysis over the causal sample. Its first assertion is a successful `load_analysis_model` call on CUDA with the bfloat16 default. It then checks, and records in the ticket comments, that the mean clean-minus-corrupt Readout logit difference over the 100 sampled instances is positive, that replacing all Components with corrupt captures reproduces the corrupt logits on the real model too, and the wall time per forward pass (for the other tickets' cost estimates).
- [x] Subagent code review against the spec completed and findings addressed.

## Notes for the implementer

- The tiny model in `tests/helpers.py` has GQA; use its config's `num_key_value_heads`, never assume it.
- `--dry-run` must keep working on the login node with no nnsight 0.7.0 (base env): the registry and dataloaders import nothing from `hooks.py` at module level.
- Do not implement any of tickets 03, 04, 07 or 08's outputs, columns or plots. The stub analysis lives under `tests/`.
- Wall-time numbers per forward on the A40/A100 go in the comments; ticket 08 sizes its grid from them.

## Comments

### What was built

Four commits on `ca/02b-block-c-scaffold`, base `2cbcac4`:

    575d612  Give block C one scaffold so four analyses can be built in parallel
    f126890  Say plainly that the causal loaders do not cover STD
    0b02cdc  Give each blocked ticket its own line in the registry
    917474d  Take both code reviews: receivers, the fp32 readout, and two real bugs

- **`component_analysis/hooks.py`** gains the three shared passes, the only new
  nnsight access in the diff.

      capture_forward(model, input_ids, attention_mask, *, components,
                      positions=None, replacements=None) -> Capture
      replace_forward(model, input_ids, attention_mask, *, replacements,
                      positions=None) -> [batch, vocab] at the Readout
      attention_weights(model, input_ids, attention_mask, *, layer, heads,
                        query_positions) -> [batch, heads, queries, seq]

      readout_logits(model, residual) -> fp32 [..., vocab]
      target_minus_distractor(logits, target, distractor) -> fp32 [batch]

      EMBED_KEY  READOUT_KEY  Replacement  Capture  geometry(model)
      all_component_keys(model)  all_receiver_keys(model)
      kv_group_of(model, head)   heads_of_kv_group(model, group)
      device_and_dtype(model)    attention_implementation(model)  describe(model)
      readout_positions(attention_mask, positions=None)

  `Capture` holds the Readout logits, `{key: [batch, seq, dim]}` and the
  residual stream at the Readout as `[batch, num_layers + 1, hidden]` (the
  embedding output, then each layer's; `[:, -1]` is what the final norm sees).
  Both passes are thin wrappers over one internal traced forward, so the
  interchange primitive and the capture feeding it cannot drift apart.

  **Keys**, senders and receivers alike, are `(kind, layer, index)`:

      ("embed", 0, 0)      EMBED_KEY    sender    token embedding output
      ("head", layer, h)                sender    o_proj input, head h's slice
      ("mlp", layer, 0)                 sender    MLP block output
      ("q", layer, h)                   receiver  q_proj output, head h's slice
      ("k", layer, g)                   receiver  k_proj output, KV group g
      ("v", layer, g)                   receiver  v_proj output, KV group g
      ("mlp_in", layer, 0)              receiver  MLP block input
      ("readout", 0, 0)    READOUT_KEY  receiver  the final norm's input

  K and V are **per KV group**, not per head: Llama-3.1-8B has 8 groups of 4
  query heads, so patching "head 7's K" would silently patch heads 4 to 7. A
  group index outside 0..7 is refused by name rather than read as a head.
- **`component_analysis/registry.py`** — `ANALYSES` (the one registration
  list), `registered`, `names`, `parse_names`, `select`, and
  `AnalysisContext`. An analysis is a module exposing `NAME`, `SUBDIR`,
  `add_arguments`, `estimate`, `run`.
- **`component_analysis/dataloaders.py`** — `causal_batches`,
  `descriptive_batches`, `batches_for_task`, `summarize`, `uncovered_reason`,
  and the `Batch` / `HonestPair` / `Batches` types.
- **`analyze_components.py`** — `--analyses`, `--batch-size`, `--device`, each
  registered analysis's own flags, the `run` path (which replaces the old
  "only `--dry-run` is implemented" `SystemExit`), `load_model`,
  `analysis_context`, `selected_analyses`, `print_estimates`.
- **`scripts/analyze_components.sbatch`** — mirrors `evaluate_circuit.sbatch`.
- **`scripts/verify_block_c.py`** + **`scripts/verify_block_c.sbatch`** — the
  GPU scaffold check.
- **`tests/stub_analysis.py`** — the stub that proves the seam and, on a GPU,
  records the three scaffold numbers.
- Tests: `tests/test_component_hooks.py` (13, nnsight 0.7.0 only),
  `tests/test_dataloaders.py` (12, both envs),
  `tests/test_analyze_components_registry.py` (12, both envs).

### The GPU verification

Job **22106585**, `gpuA40x4`, **0:49** elapsed, one A40, on the final tip.
(Job **22105822**, 1:17, ran the same check on `575d612` before the review
fixes; its numbers are in the review report and agree with these. The rerun was
worth its 49 seconds because the fixes rewrote the core traced loop, changed
the dataloader join and moved the metric onto the fp32 readout.) Command:
`sbatch scripts/verify_block_c.sbatch --circuit sdr=<nls0.3 run>
--circuit honest_c=<honest twin> --reference honest=<honest twin>
--expr "delta=sdr \ honest_c" --compose-granularity head --task-from <nls0.3 run>
--output-dir outputs/_analyses/block-c-verify --stub-batches 0`, submitted from
the worktree root after the same command was rehearsed with `--dry-run` on the
login node.

**[0] The first assertion, as the brief requires.** `load_analysis_model`
returned a `LanguageModel` over `LlamaForCausalLM` with its weights on `cuda:0`
in `torch.bfloat16` under SDPA. Ticket 01's loader had never been run on a GPU;
it works, including the bfloat16 default that follows from a non-CPU device.

**[1] Mean clean-minus-corrupt Readout logit difference: +3.2585**, over all
100 sampled instances, positive on **100 of 100**, range [1.4080, 6.2471]. The
metric is logit(Target) − logit(Distractor) read with the *clean* stream's
assignment on both runs, so the gap is the drop the patching metric normalizes
by rather than a difference of two positive numbers, and it is read through
`readout_logits` in fp32 from the residual the final norm sees. Before the fp32
readout existed the same quantity came out as +3.2588 over a range of
[1.5000, 6.1250] — the bfloat16 range is visibly quantized, which is the
ordering problem ADR-0001's fp32 requirement is about.

**[2] Replacing all 1057 senders** (32 layers x 32 heads, 32 MLP blocks, the
embedding) **with the corrupt stream's captures reproduced the corrupt run's
Readout logits exactly**: max absolute logit error **0.00000**, against a
clean-versus-corrupt spread of 4.18750. Bit-exact rather than merely close, and
that is the expected result, not luck: after the overwrites every tensor
feeding the final norm is the same tensor the corrupt run produced, so there is
no arithmetic left to round differently.

**[3] Wall time per forward**, batch 8 x 128 tokens, `cuda:0`, bfloat16, after
one untimed warm-up and with `torch.cuda.synchronize()` around each timer:

| pass | seconds |
|---|---|
| capture, all 1057 senders, SDPA | 0.1845 |
| replace, all 1057 senders, SDPA | 0.1909 |
| attention weights, one layer, eager | 0.1926 |
| per instance (capture) | 0.0231 |

**What that means for ticket 08.** At head granularity the SDR delta has 18
Components, so the position-agnostic grid is 19 senders (18 + the embedding)
by about 53 receivers (17 heads x Q/K/V, 1 MLP input, the Readout), near 1000
cells. One capture per sender plus one replace per cell over the sample's 13
batches is roughly (19 + 1000) x 13 x 0.19 s ~ **42 minutes on an A40**. That
fits the one-hour budget with little room. The lever is the batch: these
timings are at batch 8 of 128 tokens on a 48 GB card, and the eager buffer that
forces a small batch is only paid by ticket 03.

### A number the researcher has not seen: 71 of 100

The login-node dry run on the SDR nls0.3 cell reports that **71 of the 100
sampled instances have an Honest-Instruction Counterfactual** under the
clean-stream criterion, and names the 29 that do not. That is the n of every
paired honest column (ticket 06) on this sample, and it is higher than the
split rate of 629/1000 would suggest because the balanced allocation draws
evenly from strata whose survival rates differ. The unpaired 29 are reported
rather than dropped, so the item-swap analyses still run over all 100.

### Seam notes for tickets 03, 04, 07 and 08

Each of you adds **one module under `component_analysis/` and one line to
`registry.ANALYSES`**. Nothing else in the package should need to change.

- `run(ctx)` returns `{component key: {column: value}}`; the CLI merges it with
  your `NAME` as the namespace and writes the head table **once**, after every
  analysis has run. Do not write the head table yourself.
- `ctx.subdir(SUBDIR)` and `ctx.write_json(SUBDIR, name, payload)` take the
  plain string, so a helper function does not have to pass the module around.
- `ctx.causal_batches()` and `ctx.descriptive_batches()` are memoized per cell:
  two analyses in one cell share one load. `len(batches)` is the **batch**
  count; `batches.n_instances` is the instance count.
- **Ticket 03:** `attention_weights` accepts `query_positions` as `[batch, k]`,
  one set of positions per row, which is what a Segment is. Rows sum to one and
  SDPA is restored in a `finally`, including when the trace raises.
- **Ticket 04:** you need no new hook, and **do not build your own fp32
  readout** — `hooks.readout_logits(model, residual)` is it, and ADR-0001's
  requirement is already met there (the real RMSNorm scale at the position, in
  fp32, then the unembedding). `Capture.outputs[("head", l, h)]` is the
  per-head `o_proj` input, so a head's contribution to the residual stream is
  that slice times the matching columns of `o_proj.weight`, read outside any
  trace and passed to `readout_logits`. `Capture.residual` gives the logit lens
  its per-layer rows at the Readout. `target_minus_distractor` is the
  Target-minus-Distractor difference, with the note about which stream's
  assignment to use.
- **Ticket 07:** a knockout is `replace_forward` with one entry. Your test
  "knocking out nothing reproduces the clean logits" is already an invariant
  here (`test_replacing_nothing_reproduces_the_clean_readout_logits`).
- **Ticket 08: the receivers are built, so you do not touch `hooks.py`.** The
  first review caught that the three passes reached senders only, which would
  have put you in this shared module from a parallel branch. `capture_forward`
  and `replace_forward` now take receiver keys alongside sender keys, through
  the same traced forward: `("q", layer, head)`, `("k", layer, group)`,
  `("v", layer, group)`, `("mlp_in", layer, 0)` and `READOUT_KEY`. A path patch
  is one `replace_forward` with the sender's corrupt capture written into one
  receiver's input and nothing else in that receiver's forward changed.
  `all_receiver_keys(model)` is the full grid, `kv_group_of` and
  `heads_of_kv_group` convert between heads and groups, and the invariant
  "replacing every receiver with its own clean capture changes nothing" is
  already a test. `Replacement(value, positions=mask)` takes a `[batch, seq]`
  boolean mask for the position-specific pass, tested per row.
  `capture_forward` accepts `replacements`, so patch-then-read is one call.
  `EMBED_KEY` is a sender; the "patch everything reproduces corrupt" invariant
  is false without it and `all_component_keys(model)` builds the full set.
- **Never reach through the nnsight wrapper.** `model._model` is nnsight's
  private handle and a test fails if it appears outside `hooks.py`. Use
  `hooks.device_and_dtype`, `hooks.attention_implementation`, `hooks.describe`
  and `hooks.geometry`.
- **Your module is imported on the login node**, at parser-build time:
  `build_parser` calls `registry.registered()` so that every analysis can add
  its own flags. So no nnsight at module scope in your module either. Importing
  `hooks` itself is fine — it imports nnsight inside its functions — but the
  cheap habit is to import it inside `run`. Add your module's name to the
  fresh-interpreter probe in `tests/test_component_analysis.py`, as this ticket
  did for `registry` and `dataloaders`.
- **`ANALYSES` already holds a commented placeholder line for each of you**, in
  run order (03, 04, 07, 08 — descriptive before causal), separated by blank
  lines. Replace your own line; four branches each adding a line to a
  one-element list would conflict on every rebase after the first, and a line
  of your own does not.
- **The honest twin is a second dataset directory, not a flag.** The descriptive
  column tickets 03 and 04 want is
  `dataloaders.descriptive_batches("data/datasets/sdr_honest", tokenizer)`.
  Verified on the login node: `sdr_honest/dataset_config.json` records
  `"task": "sdr"`, so the mechanism gate passes and the split loads, 1000 of
  1000 instances, 125 batches of 8. Label the column descriptive, not paired.

### Open questions for the researcher

1. **The causal loaders cover FAR, SDR and SER only.** STD is segmentable and
   samples fine, but its Corruption swaps the Designating Stipulation rather
   than an item, and its answer words ("accurate" / "inaccurate") are several
   tokens each, so `DeceptionDatasetLlama` drops all 1000. The loaders now
   refuse the task by name with that reason and the dry run prints it; before
   the fix the STD dry run said "100 id(s) dropped because an answer word is
   not a single token", which is true and points at the data rather than at the
   loader. If STD is meant to get causal analyses, it needs its own pair
   builder; say so and it becomes a ticket.
2. **Only SDR has a Matched Honest survivors file**, so FAR and SER report
   "no Honest-Instruction Counterfactual" and run the item-swap pair alone.
   That matches ticket 05, which built the pool for all three tasks but only
   ran the GPU filter on SDR.
3. **`--batch-size` defaults to 8.** Chosen for a 128-token prompt on a 40 GB
   card under bfloat16 and measured there; ticket 03's eager attention is the
   one analysis whose buffer scales with the square of the sequence length.

### Deviations from the ticket's letter, all deliberate

- `replace_forward` and `capture_forward` both take `positions`, the Readout
  index per row (default: the last unpadded position). Both return Readout
  logits, so both need it; the ticket's "all positions, or a position mask"
  rides on `Replacement.positions`, which belongs to the replacement rather
  than to the call.
- `capture_forward` also takes `replacements`. The ticket's own test — a second
  capture *under* a replacement — needs it, and so do tickets 07 and 08.
- `EMBED_KEY` is supported in both passes. The invariant the ticket states is
  false without it, and the spec's sender list already includes the embedding.
- A second sbatch, `scripts/verify_block_c.sbatch`, because the GPU check
  asserts on what a run wrote rather than being a CLI run. Ticket 05 set the
  precedent with `scripts/build_matched_honest.sbatch`.

### Shared files touched, for the rebase

- **`analyze_components.py`** — a new argument group plus each registered
  analysis's own group in `build_parser`; `TaskInstances.__init__` gained a
  `tokenizer` argument; one new block inside `dry_run`'s cell loop; new
  `analysis_context`, `selected_analyses`, `print_estimates`, `load_model` and
  `run`; `main` now dispatches instead of raising. **The `dry_run` hunk is the
  one a sibling branch could conflict on.**
- **`tests/test_analyze_components_end_to_end.py`** — one test renamed
  (`test_without_dry_run_it_says_what_is_not_built_yet` ->
  `test_a_run_with_no_analysis_registered_loads_no_model`), since a run without
  `--dry-run` is now implemented.
- **`tests/test_analyze_components_segmentation.py`** — the fixture writes a
  `dataset_config.json`, which every built dataset has and which the loaders
  read the token budget from.
- **`tests/test_component_analysis.py`** — two module names added to the
  fresh-interpreter nnsight probe.
- **`component_analysis/__init__.py`** — two lines in the layout docstring.

Everything else is a new file. `evaluation/`, `dataset/`, `tasks/`, `models/`
and `component_analysis/{components,head_table,intake,segmentation,sampling,
instances}.py` are untouched.

### Tests

| env | baseline on `2cbcac4` | final on `917474d` | new failures |
|---|---|---|---|
| login-node base (py3.9, nnsight 0.5.12) | 8 failed, 657 passed, 21 skipped | 8 failed, 685 passed, 22 skipped | none (same 8 names) |
| `mgnp` (py3.12, nnsight 0.7.0) | 8 failed, 665 passed, 19 skipped | 8 failed, 711 passed, 19 skipped | none (same 8 names) |

The 8 are ticket 01's list, re-derived on this base and identical by name in
both environments. The base env's extra skip is
`tests/test_component_hooks.py`, skipped at module level because it holds
nnsight 0.7.0 behaviours; its 18 tests are 18 of the 26 that
separate the two final `passed` counts, the rest being
`tests/test_nnsight_hooks.py`. This ticket contributes **46 tests**: 18 hooks,
14 dataloaders, 13 registry, and one in `tests/test_component_analysis.py` that
fails if nnsight's private wrapper handle appears outside `hooks.py`.

Login-node `--dry-run` was run against the real SDR nls0.3 head-granularity
delta (18 Components, 1000 instances, 100 sampled, 71 paired), and against the
FAR nls0.1, SER nls0.1 and STD nls0.1 runs to check the loader gate.

### Code review

`mattpocock-skills:code-review` against `2cbcac4`, both axes as parallel
sub-agents. Both delivered — late, after the first report to the orchestrator,
as happened on ticket 02 — so **this review is independent of the author**.
Report:
`Alignment/.scratch/component-analysis/reports/02b-block-c-scaffold-review.md`,
which lists every finding with its outcome. Summary:

**Fixed** (`917474d`, on the orchestrator's decisions):

1. *Spec:* the dataloader keyed the split by `sampling.record_ids` and the kept
   records by `instance_id`, so a task carrying no `instance_id` matched
   nothing and the loss was reported as "dropped because an answer word is not
   a single token" — a false diagnosis. The retention rule is applied here now,
   by id, and a test keeps it in step with the dataset class.
2. *Spec:* `--dry-run` aborted on a task with no causal sample once a causal
   analysis was registered, losing the head table for every later cell. Only
   that failure is softened, into a printed "not applicable" line;
   `LoaderUnavailable` is its own class so every other failure still stops the
   run. Tested on the tiny non-segmentable task.
3. *Spec:* ticket 08's receivers were unreachable, so it would have had to edit
   `hooks.py` from a parallel branch — exactly what this ticket exists to
   prevent. Receiver keys added to both passes (see the seam notes above), with
   the two invariants the orchestrator specified.
4. *Standards, hard:* nnsight's private `_model` handle was read at four sites
   outside `hooks.py`, so a 0.8 migration would have touched four files
   although none imports nnsight. `device_and_dtype`, `attention_implementation`
   and `describe` replace it, and a test fails if it comes back.
5. *Standards:* no fp32 readout seam existed, so four tickets would each have
   built one. `readout_logits` and `target_minus_distractor` do it once, with
   the real RMSNorm scale at the position; the GPU check now reads its own
   metric through them.
6. *Standards:* `load_analysis_model`'s `attn_implementation` override
   contradicted ADR-0001 and is gone.
7. *Standards:* the stale `hooks.py` docstring saying only the loader lives
   there; `control` in `tests/stub_analysis.py`, which `CONTEXT.md` reserves;
   the ignored-marker `_num_heads`; `object` on every dataclass field; the
   duplicated causal/descriptive loader methods. All taken.

**Considered and kept**, with the reason, in the review report: the data clump
through the `dataloaders` signatures; the duplicated circuit-by-task walk in
`run` and `dry_run`; `Replacement.positions` rather than `where`;
`run(..., model=None)`; the duplicated nnsight version gate in the two test
modules; `len(batches)` being the batch count.

Also from the author's own pass, before the sub-agents delivered: the STD
loader gate (open question 1), and three untested seams — the descriptive
loader reached through the context, the per-instance position mask, and a
single MLP-block replacement.
