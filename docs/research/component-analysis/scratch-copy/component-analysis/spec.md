# Component-level analysis of discovered deception circuits

Status: ready-for-agent
Repo: Deception-Circuit (the "Node-Pruning for Circuit Discovery" codebase)
Grilled: 2026-09-13 to 2026-09-15. Glossary terms in `Deception-Circuit/CONTEXT.md`
("Prompt anatomy (component analysis)" section). Decision record:
`Deception-Circuit/docs/adr/0001-component-analysis-on-raw-hf-model.md`.
Tooling research: `Deception-Circuit/docs/research/interp-tooling.md`.

## Problem Statement

Node pruning has produced many candidate deception circuits, and circuit-level
evaluation (faithfulness, knockout necessity, random-circuit nulls, cross-task
matrices, benchmark knockouts) shows that some of them are partially necessary
for deception on external benchmarks. That evidence says the circuits contain
deception-relevant Components without saying which Components those are, where
they sit, what each one reads and writes, or how they compose. Every result so
far treats a circuit as an opaque set of gates. The researcher needs to zoom in:
identify the Components, assign each a Component Role, and recover the
composition structure, with enough rigor that the roles are defensible.

## Solution

A component-analysis package and CLI that takes any circuit expressible in the
existing binding and set-algebra syntax, coarsens it to Components (attention
heads and MLP blocks), and runs five analyses in the full, unmodified model:
attention patterns by Segment, direct logit attribution (DLA) onto the
Target/Distractor pair with differential and suppression columns, a logit lens
at the Readout, per-head interchange knockout, and path patching over two
counterfactuals (the existing item-swap Corruption and a new
Honest-Instruction Counterfactual built from Matched Honest Instructions).
Every analysis writes JSON, and every per-Component number joins one head table
that an agent reads to propose roles and the researcher reads to confirm them.
A single parameterized notebook renders a results directory for human review,
with a flag-gated live section for drill-down on the resident model.

## User Stories

1. As a researcher, I want to point the analysis at any circuit expression the evaluator already accepts (atomic, delta, intersection, union, xor), so that circuits I discover later need no new plumbing.
2. As a researcher, I want mixed-granularity circuits coarsened to Components by the rule "any active leaf gate makes the head a Circuit Component", so that the leaf-level delta circuits I evaluated on benchmarks are analysable.
3. As a researcher, I want the head table to record, per head, the active-neuron count, the head-gate state and the KV group, so that I can see the 14 head-gate-level delta heads inside the 46 leaf-level ones.
4. As a researcher, I want to name reference circuits (such as the honest twin) and have each Component annotated with its membership in them, so that shared and deception-specific Components are distinguishable in one table.
5. As a researcher, I want the analyses to run on SDR first, so that the pipeline is validated on a designation-polarity-balanced task while FAR and SER are identity-only.
6. As a researcher, I want the patching sample stratified on whichever metadata factors have more than one level, with achieved counts written out and no failure on a missing level, so that identity-only tasks still run.
7. As a researcher, I want attention mass per head aggregated by Segment from a configurable query position defaulting to the Readout, so that I can see what each head reads at the moment it matters.
8. As a researcher, I want to split attention profiles by designation polarity, item polarity, both, or none, so that a head implementing the inversion is distinguishable from a pure mover.
9. As a researcher, I want each task to supply a default segmentation from its template pieces and to override or add Segments by regex on the command line, so that STD and future tasks fit without code changes.
10. As a researcher, I want the segmentation actually used written to the output, so that no plot is read against the wrong spans.
11. As a researcher, I want the four Designation Positions (Designation Site, Predicate Token, Other Token, Inverse Predicate Token), the Designation Suffix and the three Item Mentions tracked as separate Segments, so that attention to different mentions of the same word, or to the predicate-like words in the suffix, is never pooled with attention to the Designating Sentence proper.
12. As a researcher, I want DLA of every Circuit Component onto logit(Target) minus logit(Distractor) at the Readout, read through an fp32 final norm and unembedding, so that head rankings are not reordered by bf16 drift.
13. As a researcher, I want a differential DLA column comparing the pressure prompt with its Honest-Instruction Counterfactual, so that heads that flip sign are separated from movers that do not know they are lying.
14. As a researcher, I want a suppression column flagging Components whose DLA favours the Distractor, so that honesty-promoting Components are visible alongside deceptive ones.
15. As a researcher, I want a logit lens at the Readout across layers on both prompt conditions, so that I can see the layer at which the deceptive answer overtakes the honest one.
16. As a researcher, I want per-head knockout in the full model under interchange ablation, with the scheme left as a parameter for mean and zero later, so that Components are ranked by causal contribution the same way the circuit evaluations rank circuits.
17. As a researcher, I want knockout by role family once roles exist, so that small single-head effects in a large circuit do not hide a large family effect.
18. As a researcher, I want path patching with senders equal to every Circuit Component plus the embedding, and receivers equal to every circuit head's Q, K and V inputs, every circuit MLP block's input, and the Readout, so that the composition structure is recovered.
19. As a researcher, I want K and V receivers handled per KV group under grouped-query attention, so that patches are not silently applied to the wrong heads.
20. As a researcher, I want a position-agnostic path-patching pass first and a position-specific pass by Segment only for sender-receiver pairs clearing a threshold, so that the grid stays affordable.
21. As a researcher, I want the threshold to default to five percent of the clean-corrupt gap and to be a flag, so that I can widen or narrow the second pass.
22. As a researcher, I want the patching metric to be the change in logit(Target) minus logit(Distractor) normalized per instance by the clean-minus-corrupt gap, so that cells are comparable across instances and tasks.
23. As a researcher, I want an optional completeness sweep of all heads and MLP blocks as senders into the Readout receiver, so that a strong direct-effect Component the pruning missed becomes visible.
24. As a researcher, I want path patching to run over both counterfactuals through the same code path, so that the pressure-dependent paths among Circuit Components are measured without a second implementation.
25. As a researcher, I want Matched Honest Instructions, one per Pressure Clause per task, drafted by an agent and asserted to the exact token length of the clause they replace, so that pressure and honest prompts align token for token.
26. As a researcher, I want the matched instructions validated by keeping only instances where the model deceives under pressure and answers honestly under the instruction, with per-clause pass rates reported, so that a bad instruction is a data finding rather than a circuit finding.
27. As a researcher, I want a paired honest-instruction column and an unpaired honest-twin column beside every descriptive analysis, clearly labelled paired versus descriptive, so that I never read a population contrast as a causal one.
28. As a researcher, I want descriptive analyses run over the full test set and causal analyses over a fixed-seed sample of one hundred instances whose ids are recorded, so that reruns are reproducible.
29. As a researcher, I want all analyses computed in the full model by default, with an in-circuit mode (complement interchange-ablated) as a check, so that roles describe the behaviour as the model actually runs it.
30. As a researcher, I want one head table, CSV plus JSON, keyed by layer and index, that every analysis adds columns to, so that agent and human reason from the same object.
31. As a researcher, I want a matplotlib PNG for every figure and a JSON twin for everything, so that an agent with no GUI can read every result.
32. As a researcher, I want one parameterized notebook that takes a results directory and renders every analysis view-only with circuitsvis and plotly, so that I can review interactively without recomputation.
33. As a researcher, I want a flag-gated live section in that notebook that loads the model and exposes single-prompt drill-down (raw pattern for one head on one instance, DLA on a hand-typed prompt, one off-grid patch), so that an ambiguous role can be probed in seconds rather than a Slurm round trip.
34. As a researcher, I want the CLI and the notebook to be thin clients of the same library, so that a capability added for one is available to the other.
35. As a researcher, I want a pre-registered role vocabulary (binder, selector, mover, suppressor, unknown; pressure reader reserved) with written assignment criteria, so that role proposals are auditable.
36. As a researcher, I want an agent to propose a role per Component from the head table and my confirmation or override stored in a column the notebook shows, so that the final labels are human-owned.
37. As a researcher, I want outputs under a dedicated analyses directory organized by suite name, circuit, and task, so that composed circuits with no home run directory have a place to live.
38. As a researcher, I want a Slurm submission script matching the evaluator's, so that runs go through the GPU partition the same way.
39. As a researcher, I want a dry-run mode that validates circuits, segmentation, sample stratification and the sender-receiver grid and prints a cost estimate without a GPU, so that a bad configuration fails on the login node.
40. As a researcher, I want nnsight 0.7.0 installed into the mgnp environment, so that training, evaluation and analysis share one environment.
41. As a researcher, I want invariant tests on a tiny random Llama to pass before any GPU run, so that a patching bug cannot masquerade as a finding.
42. As a researcher, I want a subagent code review after each implementation block, so that correctness is checked independently of the author.
43. As an agent, I want every result readable as PNG, JSON, CSV or Markdown, so that I can perform the analyses and propose roles without a browser.

## Implementation Decisions

- **Model path.** Analyses load the unmodified HuggingFace Llama and reach senders and receivers through nnsight 0.7.0 at module boundaries (embedding, per-head output at the o_proj input, q/k/v projections, MLP, unembedding). The prunable wrapper is never instantiated. Eager attention is enabled only for pattern extraction; everything else runs under SDPA. See ADR-0001.
- **One hook module.** All nnsight access lives in one module with small functions (attention profile for a head on a prompt, DLA on a prompt, one path-patch call, one knockout call), so a future nnsight 0.8 migration touches one file. Path patching runs through nnsight like every other analysis; there is no separate hook implementation.
- **Circuit intake.** Reuse the evaluator's `--circuit NAME=RUN_DIR` bindings and `--expr` algebra. Coarsening to Components is a new function whose output is asserted against the evaluation package's own coarsening in tests. Reference circuits for annotation are additional named bindings.
- **Component identity.** A Component is (kind, layer, index) with kind in {head, mlp}. Heads carry their KV group. MLP blocks are single units; MLP hidden and output dimensions are collapsed onto the block.
- **Segmentation.** Each task exposes a default segmentation derived from its template pieces and record metadata: intro, item-1 and item-2 mentions by location, the four Designation Positions, the Designation Suffix, Pressure Clause, user question, assistant stem, Readout. Predicate words are read from each record's `desig` and `desig_inv` fields, never assumed (the pools have changed words over time: the saved FAR run used ready/delayed, the current FAR spec uses weak/strong). CLI accepts named regex overrides over the decoded prompt, merged with defaults. The resolved segmentation per instance is written to output.
- **Counterfactuals.** Two pairs per instance: (clean, item-swap corrupt) from the dataset, and (clean, clean with Pressure Clause replaced by its Matched Honest Instruction). Both align token for token, so position mapping is identity. The item-swap pair keeps the existing single-position alignment assertion. The honest-instruction pair gets a new assertion: equal token count under full-prompt tokenization, every differing position inside the clause span, Readout position identical. Length matching is verified on the full tokenized prompt, not the clause alone, because BPE merges at the clause boundary can differ.
- **Matched Honest Instruction pool.** A new pool file per task beside the pressure pools, keyed by pressure id, each entry length-asserted in the Llama tokenizer. A build step filters the test set to instances passing both the deceptive-under-pressure and honest-under-instruction checks using the existing margin filter, and writes pass rates per clause. The existing fixed-length honest-instruction prompt variant used by the pressure evaluations is left untouched.
- **Sampling.** Descriptive analyses use the full test split. Causal analyses use N=100 instances drawn with a fixed seed, stratified over designation polarity, item polarity and template variant wherever the factor has more than one level; achieved counts and instance ids are written out.
- **Attention patterns.** For each Circuit Component head, query position(s) configurable (default Readout), attention mass summed per Segment, averaged over instances, split by the chosen factor set. Three condition columns: pressure, honest-instruction (paired), honest twin (unpaired, marked descriptive).
- **DLA.** Per-Component contribution at the Readout projected through fp32 final RMSNorm (using the actual scale at that position) and unembedding onto Target minus Distractor. Columns: pressure DLA, honest-instruction DLA, differential, suppression flag. Logit lens is the cumulative residual version across layers.
- **Knockout.** Single-Component interchange ablation in the full model using the item-swap corrupt stream. Interchange is the only scheme built now; the scheme is a parameter so that mean and zero can be added later without changing the interface. Family-level knockout takes a role column as its grouping.
- **Path patching.** Metric is the change in logit(Target) minus logit(Distractor) at the Readout divided by the instance's clean-minus-corrupt gap. Senders: circuit heads, circuit MLP blocks, embedding. Receivers: circuit head Q, K and V (K and V per KV group), circuit MLP inputs, Readout. In the position-agnostic pass every receiver takes the patch at all positions. In the position-specific pass Q and MLP receivers take it at the configured query positions and K and V receivers at the key positions of the chosen Segment. Sender must be strictly upstream, except attention into same-layer MLP. Position-agnostic pass patches the sender at all positions; position-specific pass patches by Segment for pairs above the threshold flag (default 0.05). Optional completeness sweep: all heads and MLPs into the Readout only.
- **In-circuit mode.** A flag that ablates the circuit complement by interchange during any analysis, implemented as nnsight interventions, not the evaluator's hooks.
- **Outputs.** `outputs/_analyses/<suite>/<circuit>/<task>/` with `head_table.csv` and `head_table.json` at the cell root, one subdirectory per analysis holding JSON and PNG, plus `segmentation.json`, `sample.json` and a log. Head table schema: one row per Component; columns namespaced by analysis; a `role_proposed`, `role_confirmed` and `role_notes` triple.
- **Roles.** A docs file defines the vocabulary (binder, selector, mover, suppressor, unknown; pressure reader reserved) and the criteria in terms of head-table columns. Role proposal is a separate agent step that writes `role_proposed`; the human writes `role_confirmed`.
- **Notebook.** One notebook, first cell holds `RESULTS_DIR` and `LIVE=False`. View-only sections read the cell directory. The live section imports the same library, loads the model once, and offers single-instance pattern, single-prompt DLA, and single off-grid patch. The researcher runs the notebook; agents do not execute it.
- **Environment and scheduling.** nnsight 0.7.0 added to the mgnp environment. A Slurm script mirroring the evaluator's submits to the GPU partition. `--dry-run` runs on the login node. Implementation happens in a dedicated git worktree of the circuit repo (`.claude/worktrees/component-analysis`, branch `component-analysis`, cut from the current branch after the glossary, ADR and research docs are committed), because the main worktree receives outputs from other experiments concurrently. Agents may submit Slurm jobs and read their outputs; since 2026-10-13 there is no one-hour cap: multi-hour jobs and the A100 and H200 partitions are allowed when they make a run simpler or faster (rehearse with `--dry-run`, put `--time` on the command line).
- **Pressure readers** are out of scope; the design leaves the head table open to non-circuit candidates so a later pressure-corrupted mask can add them.
- **First run** targets the SDR circuit at nls0.3 with its honest twin as reference circuit; FAR follows once designation polarity is rebalanced.

## Testing Decisions

- A good test asserts external behaviour at a seam the caller sees: the written head table and JSON, or the numbers a library function returns, never the intermediate tensors or hook wiring.
- **CLI seam (existing).** Mirror `tests/test_end_to_end.py`: build a throwaway run directory for the 2-layer random Llama from `tests/helpers.py`, a synthetic task with two aligned streams, monkeypatch the model loader and tokenizer, run the real analysis CLI, and assert on the head table columns, the per-analysis JSON, the segmentation and sample files, and the dry-run producing no output.
- **Library seam.** Call the analysis functions on the same tiny model and assert invariants: with the circuit set to every head and MLP block in the tiny model, patching every sender at every position into every receiver reproduces the corrupt-run logits and patching none reproduces clean, and DLA over all Components plus the embedding sums to the residual logit difference at the Readout within tolerance (neither invariant holds for a circuit subset, so these tests never use one); attention rows and Segment masses sum to one; coarsening of a mask object agrees with the evaluation package's coarsening; K/V receivers patch exactly the heads of one KV group; the honest-instruction pair passes the new clause-span alignment assertion and fails it when one token outside the clause differs; stratified sampling on an identity-only fixture returns the requested N with recorded counts.
- **Matched instruction build.** Test with the fake word tokenizer and scripted model from `tests/fakes.py`: length assertion, honest-under-instruction filter, per-clause pass-rate report.
- Prior art: `tests/test_evaluation.py` (tiny-model equivalence tests, mask round trips), `tests/test_end_to_end.py` (CLI-level run), `tests/test_deception_common.py` (alignment assertions with fakes).
- Process: tests are written before the implementation of each block; after each block a subagent code review runs against this spec and the repo's standards before the next block starts.

## Out of Scope

- Finding pressure readers, whether by ad-hoc head sweeps or otherwise; that waits for a dataset variant with an honest-instruction Corruption and a mask trained on it.
- Edge pruning repair or extension; path patching supplies composition structure.
- Attention-neuron, MLP-hidden and MLP-output units as Components of their own.
- Sparse autoencoder features, probe-direction projections, cross-mechanism role comparison, and method agreement with other discovery methods.
- Rebalancing designation polarity in FAR and SER datasets.
- Executing the notebook by an agent. (Agents may submit Slurm GPU jobs of any length on A40, A100 or H200 and read their outputs; the one-hour cap was lifted on 2026-10-13.)
- Offline HTML visualizations.

## Further Notes

- FAR and SER test sets are entirely identity polarity, so a FAR head table would describe a "copy the Designation Site item to the Readout" circuit with no inversion step; SDR is balanced and is the first target.
- Pre-registered hypothesis, held loosely: binding heads in layers 7 to 9 read the Designation Positions; mid heads in 12 to 15 select the item with the lie signal entering at their queries; late heads in 17, 22 and 24 move the selected item to the Readout; the honest twin shares binding and moving and differs in selection. The Honest-Instruction Counterfactual patched into Q versus V of the mid heads is the direct test.
- Under transformers 5.13 SDPA, attention weights come back as None; eager attention is required for pattern extraction and costs a batch-by-32-by-seq-by-seq buffer per layer.
- The nnsight 0.7.0 wheel pins nothing on transformers; the nnsight conda env carries transformers 5.8 and is not used.
- All three mechanism tasks append a Designation Suffix after the Designating Sentence (FAR: "Notice which one is strong and which one is weak."; SDR and SER: an upper-case sentence naming the damaging or unfavorable one as the relevant one). The suffix repeats predicate words, so a head may read them there instead of at the Predicate Token; the Designation Suffix Segment exists to tell those apart.
- The one existing edge-pruning run on STD never converged (accuracy 0.000 at epoch 220), which is why composition comes from path patching.
