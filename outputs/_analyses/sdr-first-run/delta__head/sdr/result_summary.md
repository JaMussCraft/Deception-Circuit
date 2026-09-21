# SDR nls0.3, head-granularity delta: the first full component-analysis run

Cell: `outputs/_analyses/sdr-first-run/delta__head/sdr/`
Circuit: `delta = sdr \ honest_c` at `--compose-granularity head` — 17 attention
heads and one MLP block (`head_table.json`, `meta.circuit.counts`).
Reference circuit: the honest twin, as the `reference.honest` column.
Task: SDR, the 1000-instance test split (`head_table.json`, `meta.task`).
Model: the files record it as `llama-8b-instruct` (`attention/patterns.json`,
`model`); the job log records a `LlamaForCausalLM` on `cuda:0` in
`torch.bfloat16` under SDPA, read through nnsight per ADR-0001. No version
string is written into the outputs.
Written by ticket 12. Every number below names the file it comes from, or is
marked derived where the analysis records no such number.

Style: there is no Markdown evaluation summary in this repository to copy, so
this follows the shape of the two nearest things — ticket 09's "Slurm read-back"
and ticket 10's roles table in
`Alignment/.scratch/component-analysis/issues/`.

## 1. Executive summary

1. **The pipeline runs end to end, in five short jobs, and reproduces every
   earlier verification job exactly.** Every head-table value this run shares with the outputs of
   record is **byte-identical**: 315 of 315 attention and DLA values against
   `ca06-paired2`, 72 of 72 knockout values against `ca07-knockout`, and 216 of
   216 path-patching values against `ca09-path-patching`. The nine unshared
   entries are the MLP block's attention columns, which are empty on both
   sides. Those three cells live in the sibling worktree
   `Deception-Circuit/.claude/worktrees/component-analysis/outputs/_analyses/`,
   not under this one. Byte-identity is the evidence; the same card is the
   inference from it. Every job of this run was an A40, and tickets 06, 07 and
   09 record theirs as A40s.
2. **The proposed roles are 0 binder, 0 selector, 1 mover, 0 suppressor and 17
   unknown** (`roles/roles.json`, `counts`). The mover is the layer-31 MLP
   block. This is ticket 10's roles of record, re-derived from this run's own
   analyses rather than from a merged cell.
3. **The circuit is top-heavy and thin.** Knocking out L17H25 alone costs
   `+0.4465` logits. Against the knockout analysis's own clean run of `+1.6132`
   (`knockout/knockout.json`, `clean_run`) that is 27.7 percent; against the
   clean-minus-corrupt gap of `3.2585` that the patching metric normalizes by
   (`path_patching/agnostic.json`, `gap`) it is 13.7 percent. **Both
   denominators are stated because each appears elsewhere in this document**,
   and the rest of the text uses the gap. With the layer-31 MLP the two carry
   23.1 percent of the gap, and all eighteen single knockouts sum to `+1.3218`.
4. **Direct paths carry little of the gap.** The eighteen Components' direct
   effects on the Readout sum to `-0.1456` of the gap under the item-swap
   Corruption and `-0.1208` under the Honest-Instruction Counterfactual, and in
   both cases three or four Components carry all of it
   (`path_patching/agnostic.json`, `path_patching/agnostic_honest_instruction.json`,
   `direct_effect_on_readout`).
5. **The completeness sweep says the rest of the gap is outside the circuit.**
   Seven non-circuit Components clear a direct effect of 0.05, the largest of
   all 1057 being `mlp.30.0` at `+0.1275` — larger in magnitude than the
   circuit's own layer-31 MLP at `-0.1137`, **and of the opposite sign**, so
   the two push the Readout in opposite directions rather than one being a
   bigger version of the other
   (`../../../sdr-first-run-sweep/delta__head/sdr/path_patching/sweep.json`).
6. **The pre-registered hypothesis is not supported in its binding or its
   selection clause, and is partly supported in its mover clause.** On the
   mid-layer Q-versus-V question, which the spec calls the direct test, the
   evidence **inside the spec's 12-to-15 band is indeterminate**: Q and V are
   level there and tiny, the strongest Q cell being `+0.0057` and the strongest
   V cell `-0.0060`. What the honest-instruction grid does show is that every
   above-noise Q cell into a mid head is **positive**, meaning those queries
   carry the pressure side rather than the honest instruction, and that the one
   large honest-instruction path into a value input, `head.8.15 -> v.9.3` at
   `+0.0155` carrying the Pressure Clause, sits in the **7-to-9 binding band**,
   not the mid band. `docs/component-roles.md` says in as many words that the
   strongest-single-receiver reading does not test Q-dominance. Section 5 gives
   the reading with its caveats.

## 2. How it was run

Five Slurm jobs, all `gpuA40x4`, one A40 each — four analysis jobs and the
family knockout, which needs the roles the other four make possible. Every one
was rehearsed with `--dry-run` on the login node first and submitted from the
worktree root with `--time` on the `sbatch` command line:

| job | what it ran | node | elapsed |
|---|---|---|---|
| 22240028 | `attention_patterns,dla,knockout` | gpub100 | 10:32 |
| 22240066 | `path_patching`, item-swap, Segment pass | gpub048 | 19:03 |
| 22240067 | `path_patching`, honest-instruction, Segment pass | gpub100 | 14:16 |
| 22240068 | `path_patching` + `--path-completeness-sweep`, 64 instances | gpub042 | 41:44 |
| 22281702 | `knockout --knockout-families` | gpub058 | 2:16 |

All five are `COMPLETED` in `sacct`.

The common binding on every job:

    --circuit sdr=outputs/llama-8b-instruct_sdr/nls0.3_noedge_260819-083414 \
    --circuit honest_c=outputs/llama-8b-instruct_sdr/nls0.3_honest_noedge_260819-083525 \
    --reference honest=outputs/llama-8b-instruct_sdr/nls0.3_honest_noedge_260819-083525 \
    --expr 'delta=sdr \ honest_c' --compose-granularity head \
    --task-from outputs/llama-8b-instruct_sdr/nls0.3_noedge_260819-083414

**The sample is the default one every block C and D job used**: 100 instances,
seed 0, balanced as far as each stratum allows — 52 identity and 48 inversion,
50/50 item polarity, 50/50 template variant, over eight strata
(`sample.json`, `marginals`). That is why the numbers here are comparable to
the verification jobs row by row. **71 of the 100 have an Honest-Instruction
Counterfactual** under the clean-stream criterion; the other 29 are named in
`dla/dla.json` (`unpaired_instance_ids`).

**Flags chosen, and why.**

- `--attention-conditions pressure,honest_instruction,honest_twin` and
  `--dla-conditions pressure,honest_instruction,honest_twin`, so both paired
  honest-instruction conditions ran (tickets 04 and 06).
- `--dla-split designation`, so the DLA is also broken out by designation
  polarity.
- `--path-counterfactual both`, run as two jobs (see below), with the Segment
  pass at **`--path-position-threshold 0.01`**. The code default is 0.05, which
  on this circuit selects exactly one cell; ticket 09's verification ran at
  0.0035, where cell selection changes between cards. 0.01 is the roles path
  floor, twice ticket 09's measured cross-card noise of about 0.005. **The
  researcher has not reset the default; this run states its choice rather than
  implying one.**
- The completeness sweep ran on its own job at ticket 09's settings: 64
  instances, `--path-sweep-threshold 0.05`.

**Two structural notes about the run, both of which shaped the layout.**

1. **The two counterfactuals ran as separate jobs.** A single job with
   `--path-counterfactual both` was submitted first, at a 55-minute limit, and
   the scheduler estimated its start for the following day; it was cancelled
   before it ran and resubmitted as two 25-minute jobs, which started the same
   afternoon. (Ticket 09 measured the combined pass at about 38 minutes on an
   A40; no combined job of this run exists to cite.) The two write different columns and different files
   (`agnostic.json` versus `agnostic_honest_instruction.json`), so nothing is
   lost by splitting them.
2. **Separate jobs cannot accumulate into one cell directory.** Every analysis
   run rebuilds the head table from the circuit intake and carries forward only
   `role_confirmed` and the `roles.*` columns (`analyze_components.py`,
   `carry_roles`), so three jobs pointed at one cell would have left only the
   last job's columns. Each job wrote its own suite and this cell was assembled
   afterwards by copying the analysis directories together and merging the
   columns through the roles pass, which is the recipe ticket 10 used:

       cp -r  outputs/_analyses/sdr-first-run-desc/delta__head/sdr   <this cell>
       cp     outputs/_analyses/sdr-first-run-paths/delta__head/sdr/path_patching/*    <this cell>/path_patching/
       cp     outputs/_analyses/sdr-first-run-paths-hi/delta__head/sdr/path_patching/* <this cell>/path_patching/
       python analyze_components.py roles <this cell> \
           --roles-merge-from outputs/_analyses/sdr-first-run-paths/delta__head/sdr \
           --roles-merge-from outputs/_analyses/sdr-first-run-paths-hi/delta__head/sdr

   The three staging cells' `sample.json` and `segmentation.json` are identical
   apart from their `created` timestamps, which is what makes them one cell.
   The completeness sweep stays in its own cell because it ran over a different
   draw and its `path_patching.direct_effect` column would therefore contradict
   this cell's; `merge_cells` refuses such a merge by design.

**Sign conventions** (ADR-0002): positive supports the deceptive answer.
`knockout.logit_diff_drop` and every `dla.*` column read natively. A
path-patching cell is `(patched - clean) / (clean - counterfactual)`, so
**negative** means the path carries the counterfactual; the roles pass reads the
derived `roles.direct_support = -path_patching.direct_effect`. Under the
Honest-Instruction Counterfactual the counterfactual is the honest prompt, so a
negative cell there means the path carries the honest instruction.

## 3. The head table, with the proposed roles

All eighteen Components, from `head_table.csv` and `roles/roles.json`. "Reads"
is the top Segment at the Readout query position under pressure with its mass;
"writes" is `dla.pressure` over the full split; "differential" is
`dla.differential`, paired over the 71; "knockout" is
`knockout.logit_diff_drop` over the 100; "direct" is `roles.direct_support`,
the sign-corrected direct path to the Readout over the 100.

| Component | KV | reads (mass) | writes | differential | knockout | direct | role proposed |
|---|---|---|---|---|---|---|---|
| L5H5 | 1 | question (0.51) | −0.0007 | +0.0003 | +0.0330 | −0.0001 | unknown |
| L5H6 | 1 | question (0.60) | −0.0004 | −0.0003 | +0.0277 | −0.0001 | unknown |
| L5H8 | 2 | unsegmented (0.42) | −0.0000 | +0.0001 | +0.0572 | −0.0001 | unknown |
| L5H9 | 2 | unsegmented (0.52) | −0.0005 | −0.0006 | +0.0415 | −0.0001 | unknown |
| L5H11 | 2 | item_1_question_option (0.35) | −0.0003 | −0.0002 | +0.1503 | −0.0001 | unknown |
| L8H12 | 3 | unsegmented (0.62) | −0.0001 | +0.0004 | +0.0332 | −0.0001 | unknown |
| L8H14 | 3 | unsegmented (0.53) | −0.0001 | +0.0004 | +0.0679 | +0.0001 | unknown |
| L8H15 | 3 | unsegmented (0.44) | −0.0001 | −0.0004 | +0.0320 | +0.0000 | unknown |
| L9H12 | 3 | unsegmented (0.54) | +0.0006 | +0.0005 | +0.0682 | −0.0004 | unknown |
| L13H17 | 4 | question (0.25) | +0.0003 | −0.0003 | −0.0053 | −0.0007 | unknown |
| L14H7 | 1 | question (0.32) | −0.0005 | +0.0008 | **−0.0936** | −0.0004 | unknown |
| L14H21 | 5 | unsegmented (0.44) | −0.0011 | −0.0022 | +0.0203 | −0.0009 | unknown |
| L14H22 | 5 | question (0.29) | −0.0011 | −0.0038 | +0.1122 | −0.0005 | unknown |
| L17H25 | 6 | question (0.27) | **+0.0310** | +0.0347 | **+0.4465** | +0.0192 | unknown (selector lean, query not met) |
| L24H18 | 4 | unsegmented (0.64) | +0.0444 | +0.0703 | +0.0230 | +0.0159 | unknown (mover lean, reads not met) |
| L24H25 | 6 | unsegmented (0.56) | +0.0405 | +0.0849 | +0.0021 | +0.0193 | unknown (mover lean, reads not met) |
| L27H4 | 1 | unsegmented (0.78) | −0.0045 | −0.0032 | −0.0008 | −0.0005 | unknown |
| **L31 MLP** | — | not applicable | **+0.1795** | **+0.3253** | **+0.3065** | **+0.0951** | **mover** |

Thresholds behind those labels, from `roles/roles.json`: z ≥ 2.0, DLA floor
0.01, knockout floor 0.01, path floor 0.01, attention floor 0.20.

**`role_confirmed` is empty, and it is empty by being absent.** Nothing in the
package writes it — `head_table.PROTECTED_COLUMNS` is exactly that one name —
so `head_table.csv` has no such column and `roles/roles.json` records
`role_confirmed: null` for all eighteen Components. The researcher fills it by
adding the column; every later analysis run copies it forward
(`analyze_components.py`, `carry_roles`). No role was confirmed by this run.

**All seventeen unknowns are `unknown/insufficient`; none is
`unknown/disagree`** (`roles/roles.json`, `flavour`). No Component's views
contradict each other, which is worth saying because the vocabulary has a name
for that case and it went unused. **No Component carries a pressure-reader
signature** either, which the pass would have noted had it seen one; the name
stays reserved.

**Why seventeen unknowns.** Three things, all visible in the table.

- **The reads view is unestablished on ten of seventeen heads.** Their top
  Segment at the Readout query is `unsegmented`, which ticket 03 showed is
  almost entirely the `<|begin_of_text|>` attention sink. The criteria refuse to
  promote "we could not see" into a role (`docs/component-roles.md`). That is
  what holds L24H18 and L24H25, which are movers on every other view.
- **`question` counts as a frame, not an item-bearing read.** Of the seven
  heads whose read is established, six top out on `question` and only L5H11
  tops out on an Item Mention (`roles.reads_group` in `head_table.csv`: ten
  `unestablished`, six `frame`, one `item_mention`). A frame read satisfies no
  role's reads clause except the selector's.
- **L17H25 fails one clause by one number.** It reads (question, 0.27), writes
  (+0.0310, z = 22.3), is the most causal single Component (+0.4465, z = 16.0)
  and has a significant direct path (+0.0192, z = 14.1). Only the selector's
  query clause fails: its strongest incoming honest-instruction path is
  `head.14.22 -> q.17.25` at **+0.0068**, below the 0.01 path floor. The floor
  is twice ticket 09's measured cross-card noise of about 0.005; the cell
  itself is above that noise, at 5.3 standard errors, so "inside the noise" —
  the phrase `docs/component-roles.md` uses for this cell — overstates it. What
  is true is that it is below the floor.

**What each condition says about what the circuit writes** (`dla/dla.json`,
`totals`):

| condition | n | model's logit difference | the 18 Components | outside the circuit |
|---|---|---|---|---|
| pressure | 1000 | +1.7454 | +0.2869 | +1.4585 |
| pressure (paired left term) | 71 | +1.5857 | −0.0220 | +1.6073 |
| honest instruction (paired) | 71 | −2.3468 | −0.5287 | −1.8182 |
| differential (paired) | 71 | +3.9325 | +0.5067 | +3.4255 |
| honest twin (unpaired) | 1000 | −2.1120 | −0.3629 | −1.7489 |

The circuit writes **16.4 percent** of the Readout logit difference directly
under pressure. The real-model sum check over all 1057 senders reproduces the
model's own logit difference to a maximum absolute error of 0.0163 against a
mean |logit difference| of 1.5434 (`dla/dla.json`, `sum_check`). That check
ran on **8 instances**, one batch, not on the split.

**The logit lens** (`dla/logit_lens.json`) has the two paired conditions
tracking each other to row 15 and then separating: `pressure_paired` settles
positive at row 18 (layer 17) and reaches +3.56 by row 25, while
`honest_instruction` settles negative at row 15 (layer 14) and reaches −2.37.
A row is not a layer: row 0 is the embedding output. The unpaired honest twin
tracks the paired honest condition throughout (−2.90 at row 25).

**Attention checks.** Every profile is a distribution: the worst
|sum − 1| over all four conditions is 2.7e-3 against a tolerance of 2e-2, no
NaN anywhere, and `max_outside` is exactly 0.0 in every condition, so the 18
Segments partition every prompt (`attention/patterns.json`, `checks`).

## 4. Composition structure

### The position-agnostic grid

19 senders (18 Components plus the embedding) by 41 receivers = **393 cells**
after strict upstream ordering, over the 100-instance sample in 13 batches.
No cell lacks a mean and no instance was excluded by its gap, in either
counterfactual (`path_patching/agnostic.json`,
`path_patching/agnostic_honest_instruction.json`).

The clean-minus-counterfactual gap is **3.2585** for the item swap (positive on
100 of 100) and **3.9325** for the honest instruction (positive on 71 of 71).

Strongest cells, item swap:

| cell | mean | se |
|---|---|---|
| `mlp.31.0 -> readout` | −0.0951 | 0.0161 |
| `head.24.25 -> readout` | −0.0193 | 0.0047 |
| `head.17.25 -> readout` | −0.0192 | 0.0014 |
| `head.17.25 -> mlp_in.31.0` | −0.0161 | 0.0014 |
| `head.24.18 -> readout` | −0.0159 | 0.0037 |
| `head.14.22 -> q.17.25` | −0.0066 | 0.0018 |

Strongest cells, honest instruction:

| cell | mean | se | the same cell under the item swap |
|---|---|---|---|
| `mlp.31.0 -> readout` | −0.0770 | 0.0229 | −0.0951 |
| `head.24.25 -> readout` | −0.0209 | 0.0060 | −0.0193 |
| `head.24.18 -> readout` | −0.0167 | 0.0044 | −0.0159 |
| `head.8.15 -> v.9.3` | **+0.0155** | 0.0023 | −0.0017 |
| `head.17.25 -> readout` | −0.0088 | 0.0007 | −0.0192 |
| `head.17.25 -> mlp_in.31.0` | −0.0073 | 0.0008 | −0.0161 |
| `head.14.22 -> q.17.25` | +0.0068 | 0.0013 | −0.0066 (the predicted flip) |

The structure the grid recovers, read off those cells: **four Components have a
direct edge to the Readout** (the layer-31 MLP and the three late heads
L17H25, L24H18, L24H25), **one head feeds the MLP block**
(`head.17.25 -> mlp_in.31.0`), and **one mid-layer head feeds the query of
L17H25** (`head.14.22 -> q.17.25`, which flips sign between the two
counterfactuals — the flip ADR-0002 predicts for a path that carries the
deceptive content, since the two counterfactuals sit on opposite sides of it).

**In the item-swap grid** the six cells above are exactly those with
|mean| ≥ 0.005, the cross-card noise floor. **In the honest-instruction grid
four more clear it** and are not in the table above:
`head.5.5 -> k.8.3` −0.0064, `head.8.14 -> v.14.1` −0.0060,
`head.13.17 -> q.14.7` +0.0057 and `head.13.17 -> q.14.21` +0.0054. Three of
the four reappear in section 5, which is where they bear on the hypothesis.

### The Segment pass

At `--path-position-threshold 0.01` the item-swap pass selected **5 cells** and
the honest-instruction pass **4** (`path_patching/segments.json`,
`path_patching/segments_honest_instruction.json`, `n_selected`).

**The item-swap Segment pass has nothing to say**, and this is a consequence of
the threshold: all five selected cells are Readout or `mlp_in` receivers, which
take one patch at the query positions rather than a Segment sweep, so no K or V
cell was swept at all. Each of the five `query_positions` entries equals its
position-agnostic cell exactly, which is the expected result for receivers with
nothing downstream that reads another position.

**The honest-instruction pass has one real Segment result**, and it is the
largest non-Readout cell in either grid:

| cell | agnostic | union | union − agnostic | top Segment | sum of Segments |
|---|---|---|---|---|---|
| `head.8.15 -> v.9.3` | +0.01545 | +0.01545 | **0.0** | `pressure_clause` **+0.0116** | +0.0134 |

The remaining Segments of that cell are `question` +0.0029, `unsegmented`
+0.0021, `stem` −0.0017, `readout` −0.0014 and the rest at or below 0.0012.
The union check held exactly, so the Segments do partition the cell's effect;
`sum_of_segments` differs from `union` because a receiver's forward is not
linear in its input, which the file states.

**A caveat on this pass, stated rather than buried.** Ticket 09's verification
ran at 0.0035 and swept nine K and V cells across both counterfactuals; at 0.01
this run sweeps one. The finer pass is in `ca09-path-patching`, is a different
job, and is not reproduced here.

### The completeness sweep

Cell: `outputs/_analyses/sdr-first-run-sweep/delta__head/sdr/`, job 22240068,
1057 senders into the Readout on the item-swap pair, over a **64-instance draw
that is not this cell's 100** (seed 0, 8 per stratum), 8472 forwards.

| rank | Component | direct effect | se | in circuit | flagged |
|---|---|---|---|---|---|
| 1 | `mlp.30.0` | **+0.1275** | 0.0175 | no | yes |
| 2 | `mlp.31.0` | −0.1137 | 0.0188 | **yes** | |
| 3 | `mlp.29.0` | +0.0937 | 0.0225 | no | yes |
| 4 | `head.31.0` | −0.0809 | 0.0035 | no | yes |
| 5 | `head.30.24` | −0.0587 | 0.0034 | no | yes |
| 6 | `head.17.24` | −0.0575 | 0.0032 | no | yes |
| 7 | `head.30.12` | −0.0543 | 0.0064 | no | yes |
| 8 | `head.27.7` | −0.0526 | 0.0052 | no | yes |

**Seven non-circuit Components clear 0.05**, all in layers 17 and 27 to 31, and
two of them are positive, meaning their corrupt-stream output pushes the
Readout *against* the Corruption. `head.17.24` shares KV group 6 of layer 17
with circuit head L17H25. The circuit's own members rank 2 (`mlp.31.0`), 23
(`head.24.18`), 28 (`head.17.25`), 40 (`head.24.25`), 145 (`head.27.4`) and
175 or below for the other thirteen.

On this draw the direct effects of all 1057 Components sum to **−0.90** of the
gap (negatives −1.61, positives +0.71) while the circuit's eighteen sum to
about −0.17. How many Components clear a floor depends strongly on the floor:
7 non-circuit at 0.05, 25 at 0.02, 57 at 0.01, 108 at 0.0035.

## 5. The pre-registered hypothesis

The spec's hypothesis, held loosely: *binding heads in layers 7 to 9 read the
Designation Positions; mid heads in 12 to 15 select the item with the lie
signal entering at their queries; late heads in 17, 22 and 24 move the selected
item to the Readout; the honest twin shares binding and moving and differs in
selection. The Honest-Instruction Counterfactual patched into Q versus V of the
mid heads is the direct test.*

**Binding in layers 7 to 9: not supported, and partly untestable here.** The
circuit has four heads in that band (L8H12, L8H14, L8H15, L9H12). All four top
out on `unsegmented` at the Readout query, at masses 0.44 to 0.62, so none has
an established read of a Designation Position (`head_table.csv`). No Component
in the circuit was proposed as a binder. What those four do have is a knockout
effect of 3.5 to 5.0 standard errors with no DLA above its floor and no direct
effect above its floor — L9H12's direct support is `-0.0004` at z = 2.5, which
is significant but an order of magnitude under the 0.01 path floor — which is
the signature the roles doc calls out as possibly wanting a fifth role.

**The binder criterion's second depends clause is met by two of them, and that
is worth separating from the reads failure.** A binder must feed another
Component at or above the path floor, and `head.8.15 -> v.9.3` (+0.0155) is the
largest non-Readout cell in either grid, layer 8 feeding layer 9; the same
band also holds `head.5.5 -> k.8.3` (−0.0064) just under the floor. So the
binding-band heads do compose forward; what is missing is the read, not the
onward path. The
reads view is unestablished rather than contradicted: the Readout query says
little about a sink head, and establishing it needs an attention run at another
query position.

**Selection in layers 12 to 15 with the lie signal at the queries: not
supported.** The circuit's mid heads are L13H17, L14H7, L14H21 and L14H22. The
Q-versus-V reading under the Honest-Instruction Counterfactual, taken from
`path_patching/agnostic_honest_instruction.json` (K and V are per KV group and
cover query heads outside the circuit, which the file records as
`covers_heads`):

| head | Q: strongest incoming | K: strongest | V: strongest | signed sums Q / K / V |
|---|---|---|---|---|
| L9H12 (kv 3) | `head.5.5` +0.0027 (1.7 se) | `head.5.11` +0.0023 | `head.8.15` **+0.0155** (6.8 se) | +0.004 / +0.003 / +0.014 |
| L13H17 (kv 4) | `head.9.12` +0.0027 | `head.9.12` +0.0025 | `head.8.12` −0.0019 | +0.005 / −0.005 / −0.006 |
| L14H7 (kv 1) | `head.13.17` **+0.0057** (3.9 se) | `head.8.14` −0.0028 | `head.8.14` **−0.0060** (4.3 se) | +0.006 / +0.006 / −0.007 |
| L14H21 (kv 5) | `head.13.17` +0.0054 | `head.5.6` −0.0012 | `head.5.5` −0.0024 | +0.004 / −0.005 / −0.007 |
| L14H22 (kv 5) | `head.13.17` +0.0029 | `head.5.6` −0.0012 | `head.5.5` −0.0024 | +0.001 / −0.005 / −0.007 |
| L17H25 (kv 6) | `head.14.22` **+0.0068** (5.3 se) | `head.14.21` −0.0032 | `head.5.5` −0.0018 | −0.005 / −0.012 / −0.013 |

Read by band, which is ticket 09's reading reproduced on this run's own files:

- **Layer 9**: V dominates by 5.7 times on one cell, `head.8.15 -> v.9.3` at
  +0.0155, and the Segment pass puts +0.0116 of it in the **Pressure Clause**.
- **Layers 13 to 14**: Q and V are level. The strongest Q cell is +0.0057 and
  the strongest V cell −0.0060, with opposite signs. The Q cells into L14H7 and
  L14H21 are **positive**, meaning patching the honest instruction into those
  queries moves the metric away from the honest answer.
- **Layer 17**: the largest single cell is a Q cell, `head.14.22 -> q.17.25`
  at **+0.0068**, against K's largest at −0.0032 — but those two have opposite
  signs, so comparing them by size answers "which receiver carries the most"
  and not "which way". By signed sum the K and V columns (−0.012 and −0.013)
  are more than twice Q's (−0.005), because Q's cells cancel and K's and V's do
  not.

**Two things make every size comparison in that table weaker than it looks.**
Q receivers are per head, while K and V receivers are **per KV group of four
query heads**: `v.9.3` covers heads 12 to 15 of layer 9 with only L9H12 in the
circuit, and `k.17.6` covers heads 24 to 27 of layer 17 with only L17H25 in the
circuit — and layer 17 head 24 is one of the seven the completeness sweep
flagged. A K or V number is therefore not attributable to the circuit head
alone (`agnostic_honest_instruction.json`, `receivers`, `covers_heads` against
`circuit_heads`). And this run's Segment pass ran at a threshold of 0.01, which
swept **one** K or V cell; ticket 09's pass at 0.0035 swept nine, on exactly
this question.

**The verdict on the direct test, stated with the band the spec named:
indeterminate in the mid band on size, and against Q on the sign reading.**
Inside layers 12 to 15 the size comparison is **indeterminate**: Q and V are level,
the strongest Q cell at +0.0057 and the strongest V cell at −0.0060. What does
speak against the hypothesis is the **sign** of the mid-band Q cells rather
than their size: `head.13.17 -> q.14.7` (+0.0057), `head.13.17 -> q.14.21`
(+0.0054) and `head.14.22 -> q.17.25` (+0.0068) are all positive, and under
ADR-0002 a positive cell on the honest pair means that path carries the
pressure side — so patching the honest instruction into those queries moves the
model *away* from the honest answer, which is not "the lie signal entering at
their queries". The one large honest-instruction path into a value input,
`head.8.15 -> v.9.3` at +0.0155, is in the **7-to-9 binding band**, not the mid
band, so it bears on binding rather than on this test. Every cell in the table
is between 1 and 7 standard errors and none exceeds 0.016 of the gap, so this
is a weak result in absolute terms, not a strong refutation — and
`docs/component-roles.md` states that the strongest-single-receiver reading
this table is built on "is not the same as the query dominating the Component's
input".

**Movers late, at 17, 22 and 24: partly supported.** The three strongest direct
edges to the Readout after the layer-31 MLP belong to L17H25, L24H18 and
L24H25, exactly the late band the hypothesis names, and the circuit's most
causal head is L17H25. The hypothesis named layer 22; this circuit contains no
layer-22 head at all. What the hypothesis did not anticipate is that the single
largest mover is not a head: `mlp.31.0` at −0.0951 is five times the strongest
head, and it is the only Component the criteria label.

**"The honest twin shares binding and moving and differs in selection" cannot
be tested from this cell.** The circuit under study is the delta
`sdr \ honest_c`, so by construction **0 of 18 Components are shared with the
honest circuit** (`head_table.csv`, `reference.honest`). Testing that clause
needs the intersection circuit analysed as well, which is a different cell and
a different run.

**One thing the hypothesis did not predict, which the run shows clearly.**
L14H7's knockout *raises* the deceptive margin by 0.0936, 3.3 standard errors,
making it the strongest opponent of deception in the circuit — and it sits in
the band the hypothesis assigns to selection, next to L14H22, the
fourth-strongest helper. It is not labelled a suppressor because its DLA and
its direct effect are both inside their own error, so only one view speaks.

## 6. Caveats

1. **Paired and unpaired columns cover different samples.** `dla.pressure` and
   the pressure attention columns cover the full 1000-instance split;
   `knockout.*` and `path_patching.direct_effect` cover the 100-instance sample;
   `dla.differential`, the paired attention columns and every
   `*_honest_instruction` column cover the **71** instances with a Matched
   Honest survivor. The column names do not say so. No number in this write-up
   subtracts across that boundary. **The sample matters to the headline**: the
   circuit's summed DLA is +0.2869 over the full split but **−0.0220** over the
   paired 71 (`dla/dla.json`, `totals`), so on the very instances where every
   hypothesis-relevant number is computed the circuit writes essentially
   nothing under pressure, and its +0.5067 differential is carried by the
   honest-instruction term.
2. **A family knockout that groups seventeen of eighteen Components answers
   "is this circuit necessary", not "is this role large".** The `unknown`
   family is seventeen Components; its number belongs beside the circuit-level
   knockouts rather than beside the mover's. Section 7 carries the measurement:
   +0.9500 for the seventeen against +0.3065 for the one-member `mover`
   family, and an accuracy of 0.63 against 0.98.
3. **Seven non-circuit Components clear the sweep's 0.05 floor** and
   non-circuit direct paths carry most of the gap on that draw. The circuit is
   not a complete account of the item-swap effect at the Readout.
4. **The cross-card floor is about 0.005 of the gap** on a path-patching cell
   (ticket 09's A40-versus-A100 comparison). Every job here ran on an A40, so
   the comparison with `ca06-paired2`, `ca07-knockout` and `ca09-path-patching`
   is byte-exact; a comparison with ticket 08's A100 grid would not be.
5. **The roles path floor was amended from 0.005 to 0.01 in ticket 10**, for a
   reason external to any result and logged in `docs/component-roles.md`. It is
   what holds L17H25 at `unknown` rather than `selector`, and this run
   reproduces that outcome on its own measurements.
6. **The Segment pass at 0.01 swept one K or V cell**, so the composition-by-
   Segment picture here is thin by construction. The finer pass at 0.0035 is in
   `ca09-path-patching` and is a different job.
7. **The sweep's draw is 64 instances, not this cell's 100**, so its direct
   effects are not this cell's numbers and its cell is kept separate.
8. **The reads view depends on one query position.** Everything about what a
   head reads here is read at the Readout; a sink head's off-sink mass is not
   examined.

## 7. The family knockout

Job 22281702, `gpuA40x4`, `--time=00:10:00`, grouped by the `roles.*` columns
of this cell through `--knockout-roles-from`, written to its own suite because
an analysis run into this cell would overwrite its head table.

Job **22281702**, `gpuA40x4`, node gpub058, **2:16** elapsed, `COMPLETED`,
`--time=00:10:00` on the command line, rehearsed with `--dry-run` on the login
node first. It grouped by the `roles.*` columns of this cell through
`--knockout-roles-from` and wrote to its own suite, because an analysis run into
this cell would have overwritten its head table. Its
`knockout_families.json` and figure were then copied here and its two columns
merged in, so the grouping a figure was built from sits in the table beside it.

The clean run reproduces the one in section 3 exactly: **+1.6132**, standard
error 0.0886, accuracy 1.00 over the same 100 instances, and **all eighteen
single-Component drops in this job are bit-identical to job 22240028's**, so the
family pass is the same code path and the loop changed no number
(`knockout/knockout_families.json`, `knockout/knockout.json`).

| rank | family | Components | mean drop | se | accuracy | sum of its singles |
|---|---|---|---|---|---|---|
| 1 | unknown | 17 | **+0.9500** | 0.1290 | **0.63** | +1.0153 |
| 2 | mover | 1 | +0.3065 | 0.0649 | 0.98 | +0.3065 |

**Three things in that table.**

1. **It is what makes the accuracy column mean anything.** Every single
   knockout left accuracy between 0.98 and 1.00, because a shift of 0.45 in a
   margin of 1.61 flips almost no instance. Knocking out the seventeen unknowns
   together drops it to **0.63**: 37 of 100 instances flip to the honest answer.
2. **Read the `unknown` row as a necessity check, not as a role effect.** A
   family of seventeen of eighteen Components answers "is this circuit
   necessary", which is the circuit-level question, and its number belongs
   beside the circuit-level knockouts rather than beside the mover's +0.31. The
   figure labels each family with its size for that reason.
3. **The joint effect is slightly sub-additive**, +0.9500 against +1.0153
   summed, so at this circuit's size the Components are close to independent.
   The single-member `mover` family is bit-identical to its single knockout, as
   it must be.

No Component was dropped from the grouping: `grouping.n_outside_this_circuit`
is 0, so every row of the head table is in one of the two families.

## 8. Runtime, per analysis per job

For job 22240028 the per-analysis boundaries are the modification times of the
files **in that job's own staging cell**,
`outputs/_analyses/sdr-first-run-desc/delta__head/sdr/`, against the job's start
in `sacct`; the copies in this cell carry the assembly's timestamps instead. The
model load is inside the first figure. Two forward counts are **derived**, not
read from a file: neither `attention/patterns.json` nor `knockout/knockout.json`
records a cost block. For the path-patching jobs the analysis records its own wall time and
forward count in each JSON's `cost` block.

| job | analysis | card | forwards | wall | note |
|---|---|---|---|---|---|
| 22240028 | model load + `attention_patterns` | A40 | 2208 eager (derived: the dry run's count) | 8 min 18 s | job start 13:01:24, `attention/patterns.json` written 13:09:42 |
| 22240028 | `dla` | A40 | — | 1 min 14 s | to `dla/logit_lens_paired.json` at 13:11:01 |
| 22240028 | `knockout` | A40 | 260 (derived: 13 batches x 20) | 50 s | to `knockout/knockout.json` at 13:11:51 |
| 22240028 | whole job | A40 | | **10:32** | |
| 22240066 | path patching, item-swap, agnostic | A40 | 5382 | 1038 s | 0.193 s per forward |
| 22240066 | Segment pass, 5 cells | A40 | 156 | 30 s | |
| 22240066 | whole job | A40 | | **19:03** | |
| 22240067 | path patching, honest-instruction, agnostic | A40 | 5382 | 763 s | 0.142 s per forward, at 71 of 100 occupancy |
| 22240067 | Segment pass, 4 cells | A40 | 364 | 52 s | |
| 22240067 | whole job | A40 | | **14:16** | |
| 22240068 | completeness sweep, 64 instances | A40 | 8472 | 1760 s | one forward per sender per batch |
| 22240068 | whole job | A40 | | **41:44** | includes its own 64-instance agnostic grid |
| 22281702 | family knockout | A40 | 312 (derived: 13 batches x 24) | 2:16 whole job | 2 families of 17 and 1 |

**For budgeting later runs on an A40**: the descriptive trio is about 11
minutes, each position-agnostic patching grid is 13 to 18 minutes at 100
instances, the completeness sweep is about 30 minutes at 64 instances, and the
dry-run estimate at ticket 02b's constant of 0.1848 s per forward (994.6 s for
a grid) **under**-predicts the item-swap grid by 4 percent — it came in at
1038.5 s — and **over**-predicts the honest one by 30 percent, at 762.9 s,
because the honest pass spends all 5382 forwards at 71-of-100 occupancy
(`cost` in both `agnostic*.json`). **Queue time
dominated everything**: the four analysis jobs waited between 12 minutes and
13 hours between `Submit` and `Start` in `sacct` (12m20s, 24m12s, 26m51s and
12h58m51s; the first was submitted about four minutes before the other three),
and the shorter `--time` requests backfilled sooner. Ask for the time the
analysis needs, not the sbatch's four-hour default.

## 9. Next steps

1. **FAR, after designation polarity is rebalanced.** FAR and SER test sets are
   entirely identity polarity, so a FAR head table today would describe a
   "copy the Designation Site item to the Readout" circuit with no inversion
   step (spec, Further Notes). Rebalancing is out of the component-analysis
   spec's scope, and the rerun is the first thing to do once it lands. The
   pipeline needs no change: the same five jobs with FAR's run directories.
2. **Establish the reads view at another query position.** Ten of seventeen
   heads read the attention sink at the Readout. One more attention run per
   query position (`--query-positions`, for instance the designation Segments
   or the Pressure Clause) plus a roles pass that costs a second on the login
   node would say whether those heads read anything the vocabulary names.
3. **Settle L17H25.** A longer honest-instruction pass, a different selector
   clause, or `role_confirmed` by hand.
4. **Decide whether the head-granularity delta is the right object.** It is
   disjoint from the honest circuit by construction, which is what makes the
   hypothesis's honest-twin clause untestable here, and the sweep says most of
   the item-swap effect at the Readout arrives through Components it does not
   contain.

### Open researcher decisions, collected

From ticket 06: whether `attention_patterns.pressure_paired_*` should exist at
all; whether "paired" belongs in the column names; whether the paired columns
should run over the full split rather than the causal sample; the L14H7
disagreement between the twin and the counterfactual; and the two conditions
flags (now settled by ticket 10).

From ticket 09: whether an A100 rerun is wanted for a strict bit-identity check
against ticket 08; the default for `--path-position-threshold`; the Q-versus-V
evidence; and the seven non-circuit Components.

From ticket 10: L17H25's one missing cell; the suppressor carve-out; the twelve
heads with no established read; whether `question` is a frame; that a rerun into
a cell strips merged analysis columns; the position-threshold default; the
71-versus-100 column naming; and whether the vocabulary is missing a fifth role
for the five Components that matter causally and do nothing the four roles
describe.

**New from this run, two items.** First, whether the roles pass should write an
empty `role_confirmed` column rather than leaving the researcher to add one.
`head_table.merge_columns` refuses to write that name at all, which is what
protects a confirmed role from being overwritten, so writing an empty column
would need a deliberate exception rather than a flag. Second: separate Slurm
jobs cannot accumulate into one cell
directory, because every run rebuilds the head table and carries only
`role_confirmed` and `roles.*`. The workaround here was copy-then-merge. If
multi-job cells are to be normal — and with a one-hour job budget they are —
then the CLI should either carry every analysis's columns forward or say
plainly that a cell is one job's output.
