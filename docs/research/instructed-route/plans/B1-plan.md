# B1 plan: close the loop (T1) and key-side versus query-side (T2)

Written 2026-11-01 by the B1 planning agent (Opus), session claude-230e4716; nothing here has run. Rules of record are
the frozen ones in `spec.md`; section 1.4 proposes a pre-run ruling to record there before any job, or to drop.

## 0. Fixed inputs (verified on the login node, 2026-11-01)

- **Sample.** Llama-3.1-8B-Instruct, `far_v2` and `ser_v2` test splits, held-out sample (n = 100, seed 1) fixed by
  `--include-ids docs/research/mechanism-analysis/phase1/groups/{far,ser}_heldout_D_sample.json --n-causal 100` (the far
  file equals the held-out cell's `sample.json`). `docs/research/held_out.json` lists no sets.
- **Streams.** D = the `<t>_v2` clean prompt; T = its Neutral-Clause Twin (`<t>_v2_honest`, same `instance_id`,
  `batch.neutral_twin`). On all 100 held-out ids of both tasks D and T have equal length and differ only at
  `pressure_clause` tokens. The record field `neutral_prompt` is a different control; never use it.
- **Grid and quartet.** `C_t` per task from `docs/research/mechanism-analysis/phase3/ct.json` (far 72, ser 78,
  selection sample); "outside" = every head and MLP block not in `C_t`, embedding excluded. The quartet
  `head.17.24..27` is exactly KV group 6, so one `k.17.6` or `v.17.6` write touches the quartet and nothing else.
- **Metric.** m = logit(Target) − logit(Distractor) at the Readout, fp32 (`hooks.readout_logits`); twin gap G =
  m(D) − m(T) ≥ 1.0. Rule numbers are ratios of means (as `f_D`), with per-instance medians and a 2,000-resample
  bootstrap clustered by `pressure_id` beside them; verdicts use the point estimate, as the frozen rule is worded.
- **What 0.8 is.** E14's signed sum of the completeness sweep's normalized direct effects over the outside senders,
  on the **selection** sample: far 0.803, ser 0.774 (abs 1.68, 1.76; `phase3/completeness.csv`). Top rows: mlp.31
  +0.203 / +0.084, mlp.30 −0.111 / −0.127, L31H0 +0.050 / +0.061. Measured by `path_patching.completeness_sweep`,
  not `dla.py`. The held-out value is unknown until T1's baseline sweep runs.

## 1. T1: is the outside-grid share mediated by the quartet outputs?

### 1.1 Intervention

"Restoring" is meant as in F-sdr-002: under pressure, put the quartet back in its pressure-free state. D and T are run
whole with every Component's output captured (hooks kind `head` = the per-head `o_proj.input` slice). The primary run
**D_q** is the D prompt with `head.17.{24..27}` set to their T values at every position (pre-clause positions are
bit-identical, so this equals post-clause plus Readout); every downstream Component recomputes freely. Descriptive
variants: D_q at the Readout only; D_q post-clause with the Readout excluded; reverse T_q (T prompt, quartet set to D
values), which shows sufficiency.

### 1.2 Readout and rule number

For outside sender s and run X, the sweep's direct effect is normalized by the **D − T gap**:

    e_s(X) = mean_i[ m_i(D) − m_i(D, s's output set to its X value, all else frozen at D) ] / mean_i G_i
    O   = Σ_{s ∉ C_t} e_s(T)      O_q = Σ_{s ∉ C_t} e_s(D_q)      M_q = O_q / O
    Rule: the loop closes when M_q ≥ 0.50; otherwise bypass.

**Trap.** `path_patching.normalized_effect` divides by `streams.gap = clean − corrupt`. With D_q as the corrupt
stream that gap is m(D) − m(D_q), not G, so the code must carry G and normalize every sweep by it.

**Also reported:** total recovery r_q = (mean m(D) − mean m(D_q)) / mean G; the rows for mlp.31, mlp.30 and L31H0;
the positive and negative parts of O and O_q (mlp.30 opposes, so the signed sum moves when a suppressor relaxes); and
the joint swap of all outside senders, since the final RMSNorm makes the sum non-additive.

**Two estimators.**
- (a) The forward sweep (`path_patching.sweep_readout`, one forward per sender per batch) takes `Streams` built from
  the D and X captures, about 640 s per sweep on H100 (05-p3). It is the rule of record for O and O_q.
- (b) The offline fp32 decomposition replaces s's Readout contribution (`dla.component_contributions`) in D's final
  residual by its X contribution, read through the real norm. It computes every arm, controls included, so arms are
  compared on one estimator. Smoke gate G3 requires (a) and (b) to agree.

### 1.3 Matched controls (mediation versus a generic late-layer effect)

Each control is restored from T at the same positions and read with estimator (b).
- **C1, layer-matched.** 5 seeded draws of 4 layer-17 heads outside the quartet and `C_t` (specificity floor).
- **C2, mid-layer.** 5 seeded draws of 4 heads in layers 8 to 16, outside `C_t` and the deciding set.
- **C3, direction-matched push (the generic-amplification probe).** In D, add δ_i·u_i to the `mlp.17` output at the
  Readout, u_i the unit fp32 vector g ⊙ (W_U[target] − W_U[distractor]) (g the final-norm weight: steepest ascent at
  fixed scale), δ_i solved per instance so the fixed-scale layer-17 lens margin moves exactly as under D_q. If the late
  writers amplify whatever answer direction leaves layer 17, C3 removes as much of O as D_q does.
- **S_k reference (descriptive).** Restore `greedy_k20` (`phase1/groups/{far,ser}_heldout_D.json`) post-clause; M_S
  shows whether a bypass leaves the clause readers without passing the quartet.

### 1.4 Proposed pre-run ruling (record in spec.md before submission, or drop)

The frozen verdict stays "closes" or "bypass" from M_q alone. The controls add a qualifier:
- **closes, route-specific.** M_q ≥ 0.50, M_q above every C1 and C2 draw, and M_q − M_C3 ≥ 0.15.
- **closes, generic amplification.** M_q ≥ 0.50 and M_q − M_C3 < 0.15. This is the outcome review-D M7(d) predicts.
- **closes, not specific.** M_q ≥ 0.50, and some C1 or C2 draw reaches M_q.
- **bypass.** M_q < 0.50, reported with M_S and the Readout-only versus post-clause split.

### 1.5 Position-resolved path patching (descriptive; splits M_q)

The quartet is one joint sender, with T as counterfactual. Its value is written only at {Readout} or at {post-clause,
Readout excluded}. Receivers are the inputs of the 20 strongest outside writers by |e_s(T)|: `mlp_in` for MLPs, `q` at
the Readout for heads, and their KV group's `k` and `v` at post-clause positions. Σ path effects against O_q splits
M_q into "quartet to writer directly" and "via intermediates such as the L24 heads". The freeze (L12) applies only
here, not to the rule number.

## 2. T2: is the pressure carried at option-token keys or at the final-token query?

### 2.1 Positions (`component_analysis/segmentation.py`, scheme `mechanism_v2`)

- **Option tokens** = union of `item_{1,2}_question_pair` and `item_{1,2}_question_option`: the user-turn mentions
  ("..., inbound or outbound?") and the response line ("where X is inbound or outbound."), all after the clause. On the
  100 held-out ids of both tasks each is exactly one leading-space token (such as `' inbound'`).
- **Pre-clause mentions** (`item_{1,2}_intro`, `designation_site`) are bit-identical in D and T, so a key-side pressure
  signal cannot sit there; patching them is an exact-zero check, as P2 was. **Final token** = the `readout` Segment
  (last stem token "is"). **Clause** = `pressure_clause`.
- **Pitfalls.** Spans are claimed by priority, so a mention token is never also `question` or `response_line`. FAR's
  stem and question repeat the predicate ("failing"), which is not an option. Match by Segment, never by string
  (leading spaces). K is patched at the `k_proj` output, before RoPE; D and T are position-aligned, so phases match.

### 2.2 Arms

Each arm runs the D prompt with one receiver site set to its T value at a mask, and everything downstream free.

    P = mean m(D) − mean m(T)         r_a = (mean m(D) − mean m(D_a)) / P

- **Rule arms.** Q: `q.17.24..27` ← T at the Readout. K: `k.17.6` ← T at the option tokens. Key-side if
  r_K − r_Q ≥ 0.15, query-side if r_Q − r_K ≥ 0.15, otherwise "indeterminate".
- **Descriptive arms.** V and K+V at the options; Q+K with the interaction r_QK − r_Q − r_K; K at all post-clause
  positions (ceiling of the option restriction); K at the clause span; Q at all post-clause positions; the quartet
  output at the Readout (ceiling r_out); the intro-mention exact-zero check; the reverse direction (T prompt with q,
  or k at the options, set to D values).
- **Controls.** Q at the Readout for 5 draws of 4 non-quartet layer-17 heads. K at the options for each other layer-17
  KV group (0 to 5 and 7; max reported). `k.17.6` at 4 random post-clause tokens that are neither options nor the
  Readout (5 draws), which tests whether the option tokens matter specifically.
- **Power and interaction.** Twin knockout of `head.17.24` alone at the Readout drops the margin by 1.93 (far) and 1.80
  (ser) logits on the selection sample (`phase1/top20.csv`, cell s3). If r_out < 0.15 the reading says "indeterminate,
  ceiling below 0.15". F-sdr-001 found mixed interfaces on SDR, so two large single arms are a live outcome.
- **Sun, precisely.** The arXiv 2605.09314 abstract puts an "option-routing feature" in option-token representations
  and proposes a low-rank fix to the decision heads' key projections; L17H24 as the decision head comes from review-D M7.

### 2.3 Position-resolved path patching (descriptive)

Senders are the phase-3 query feeders of the quartet (`head.14.4`, `head.15.8`, `mlp.13` to `mlp.15`), the strongest
K feeder in `phase3/b_selector.csv`, and layers 0 to 16 as 17 layer-group senders. Receivers are `q.17.24..27` at the
Readout and `k.17.6` at the options. It shows which upstream layers write each signal; phase 3 had only `C_t` senders,
on the selection sample.

## 3. Code: what exists and what must be built

- **Exists, reused as is.** `hooks.capture_forward(..., replacements={key: hooks.Replacement(value, positions=[batch,
  seq] bool)})` writes any `head`, `q`, `k`, `v`, `mlp` or `mlp_in` site at a per-row mask. Also reused:
  `knockout.position_mask`; `path_patching.Streams`, `sweep_readout`, `normalized_effect` and `receiver_inputs`;
  `dla.component_contributions` and `fixed_scale_readout`; `analyze_components.py batch FILE` (one model load,
  `--timings`); the v2 neutral-twin loader.
- **path_patching.py can restrict positions only on the receiver side.** K and V go per Segment, and Q, MLP and
  Readout go at `--query-positions`, via `positioned_effects`. The sender is written at every position, and senders
  and receivers come only from the circuit grid. `run()` always runs the grid before `--path-completeness-sweep`
  (5,500 s against 640 s in 05-p3), and it has no sweep-only mode and no gap other than clean − corrupt.
- **sdr_shared_composition.py cannot be reused for FAR or SER.** It is bound to the SDR native panel: P and N
  variants, semantic maps, parent manifest hash `36bff9eb…`, 8 × 224 batches and 64-token decoding. Only its idiom
  carries over, a bank of `('head', 17, h)` Replacements masked to positions (`pack_bank`, `arm_bank`). The twin is
  token-aligned, so no position map is needed.
- **analyze_components.py writes no `run_manifest.json`.** Only `run_io.make_run_dir` and `evaluation/suite.py` call
  `run_manifest.write_run_manifest`, which records the 40-hex `git_commit`. Ticket 1 adds it.

Interface sketch (names indicative):

    component_analysis/route_closure.py   NAME/SUBDIR "route_closure", one line in registry.ANALYSES
      flags: --route-tests {t1,t2,both} --route-direction {restore,reverse,both} --route-sweep {forward,offline,both}
             --route-control-draws 5 --route-control-seed 20261101 --route-ct FILE --route-deciding-set FILE:NAME --route-pp-top 20
      capture_pair(model, batch) -> PairStreams(d, t, gap, segmentations, ids)
      restore_bank(source, keys, mask) -> {key: Replacement};  run_arm(model, pair, bank, capture_keys) -> ArmResult
      offline_direct_effects(model, pair, arm) -> {sender: [batch]}   # fp32, real norm, normalized by pair.gap
      forward_sweep(model, pair, arm, senders) -> {sender: [batch]}   # Streams with gap overridden to G
      direction_push_bank(model, pair, arm) -> bank                   # C3
    path_patching.receiver_inputs(..., sender_positions=None)          # new kwarg, backward compatible
    knockout.parse_positions: new union form "segments=a+b+c"           # fallback and masks
    scripts/route_closure_readings.py                                   # CPU: JSON -> tables, verdicts, bootstrap

Example (a far batch line reuses the 05-p3 `--expr Ct=...` composition, so the cell equals `ct.json` `C_t`):

    python analyze_components.py batch docs/research/instructed-route/jobs/B1-far.batch --timings outputs/_analyses/instructed-route-b1/timings/far.json
    # <05-p3-far composition> --include-ids docs/research/mechanism-analysis/phase1/groups/far_heldout_D_sample.json --n-causal 100
    #   --analyses route_closure --route-tests both --route-sweep both --output-dir outputs/_analyses/instructed-route-b1/far

## 4. Cost (Bridges-2 GPU-shared, one H100-80, allocation cis260361p, reachable until about 2026-11-09)

Measured on Bridges-2: model load 619 to 767 s; twin completeness sweep 610 to 644 s per task (13,767 forwards,
0.047 s each at batch 8); 05-p3 jobs 6,663 to 9,462 s against 150 to 195 reserved minutes.

| job | contents | closest observed | estimate | reserved |
|---|---|---|---|---|
| B1-smoke | both tasks, 1 batch (8 ids) each, every arm, gates G1-G5 | 02a / 02b smokes 0.40 / 0.35 GPU-h | 0.35 h | 0.5 GPU-h |
| B1-far | 2 forward sweeps (T, D_q), offline arms, T2 arms, path patching | 05-p3 sweep 644 s, load 767 s | 0.75 h | 1.25 GPU-h |
| B1-ser | same | 05-p3 sweep 610 s, load 704 s | 0.75 h | 1.25 GPU-h |
| contingency | one rerun of one task job | same | 0.75 h | 1.25 GPU-h |
| fallback, if triggered | segment knockouts, both tasks, one load | 1C-b held-out job 1,835 s | 0.4 h | 0.75 GPU-h |
| **total** | | | | **5.0 of the 20 B1 GPU-h** |

Capture-all forward timings are extrapolated; the smoke's `--timings` replace them and the task reservations are reset
to observed plus about 50%. Far and ser run as two parallel jobs. Submit after pushing the branch and `b2.sh
sync-code` with `DC_B2_BRANCH=instructed-route scripts/remote/b2.sh submit --time HH:MM:SS --script
scripts/analyze_components.sbatch -- batch <file> --timings <file>`; add `instructed-route-b1*` to
`FETCH_ANALYSIS_GLOBS` for `b2.sh fetch`. **Delta if Bridges-2 is lost:** gpuH200x8 (bimc-delta-gpu or bgrb, fresher
fair-share), same reservations; P3 showed H100 and H200 bit-identical. Avoid A100 for rule runs (bf16 drift noted);
A40 only as a last resort, about 5 times the walltime (about 4 GPU-h per task).

## 5. Tickets

Each ticket is for one Opus implementer working test-first. Tests run on mgnp and on base 3.9. The tiny-Llama tests
need nnsight 0.7.0, which mgnp has on the login node, and they skip on base.

1. **run_manifest in analyze_components** (`write_cell` and each batch output dir call `write_run_manifest`).
   `tests/test_analyze_components_manifest.py`: a non-dry run writes a 40-hex `git_commit` (fingerprint
   monkeypatched); a dry run writes none; a changed argv writes `run_manifest.1.json`.
2. **Sender position masks** (`receiver_inputs(..., sender_positions=None)`). `tests/test_path_patching_sender_positions.py`
   (tiny Llama): an all-True mask is bit-identical to None; all-False gives zero effect; Readout-only and complement
   masks into the Readout match a direct replace-forward.
3. **Segment-union positions in knockout.** `tests/test_knockout_positions_union.py`: the union is the OR of the
   single-Segment masks; an absent Segment is refused by name; the column suffix is stable.
4. **route_closure core and T2.** `tests/test_route_closure_t2.py` (tiny 2-layer GQA model): an empty bank reproduces
   m(D) bit-identically (G1); restoring every `hooks.all_component_keys` key, embedding included, reproduces m(T)
   (G2); a `k.L.g` write touches only that group's 4 heads; option masks equal the 4 Segments and exclude the
   pre-clause mentions; control draws are seeded and disjoint from the quartet and `C_t`.
5. **route_closure T1.** `tests/test_route_closure_t1.py`: the forward sweep normalizes by G, not the arm's gap (case
   built so they differ); offline and forward e_s agree within 1e-3; O excludes `C_t` and the embedding; C3's δ hits
   the target lens change to 1e-4; the joint swap equals a forward with all outside senders replaced.
6. **Readings script.** `tests/test_route_closure_readings.py` (synthetic JSON): the M_q, r_Q and r_K formulas;
   verdicts at 0.4999 / 0.5000 and 0.1499 / 0.1500; the section 1.4 labels; a seeded bootstrap clustered by
   `pressure_id`.
7. **Batch files and dry runs (no GPU).** Generate `docs/research/instructed-route/jobs/B1-{smoke,far,ser}.batch`. Run
   `python analyze_components.py batch <file> --dry-run` on the login node (resolves `C_t`, the 100 ids, the Segments,
   the estimate), then `scripts/remote/b2.sh submit --dry --test-only --time ... -- batch <file>` on the real wrapper.
   A test asserts each cell's Component set equals `ct.json` `C_t`.

**Smoke gates, all required before the task jobs.** G1 and G2 hold on the real model. G3: offline and forward e_s
agree within 0.01 per sender and 0.02 on the summed O. G4: the 8-id held-out O is printed beside 0.80 and 0.77, for
information. G5: the forecast is at most 1.5 GPU-h per task.

## 6. Risks

- **Generic amplification (top risk).** The quartet's Readout write is large, so M_q ≥ 0.5 is likely under the frozen
  rule, and late components dominating direct attribution is normal (Lad 2406.19384; Stolfo 2406.16254). C3 is the
  discriminating control; without the section 1.4 ruling a pass cannot be told from "late writers amplify layer 17".
- **Hydra-style compensation.** The rule number uses free recompute, so self-repair (McGrath 2307.15771) is measured
  and lowers M_q, biasing toward "bypass". A relaxing suppressor (mlp.30) inflates the signed O_q, hence the split
  positive and negative parts. Path patching (1.5, 2.3) is the no-compensation counterpart; L12 applies only there.
- **Mean-ablation pressure injection (L15).** B1 uses no mean or zero ablation anywhere: every intervention, the
  fallback included, is an interchange with the token-aligned twin.
- **Signed-sum fragility.** If held-out O < 0.4 on a task, M_q is a ratio of small numbers; it is flagged with its CI,
  and the rule is unchanged. The selection-sample `C_t` defines "outside", as for the 0.8; a definition, not a leak.

## 7. Fallback: trigger and design

**Trigger.** Switch to the segment fallback when any of these holds: (a) tickets 4 and 5 are not merged, green on both
interpreters, after two review rounds; (b) two smoke jobs fail G1, G2 or G3; (c) the smoke forecasts more than 6 GPU-h
for both task jobs together; (d) the code has not passed the smoke by 2026-11-07 and Delta H200 cannot run it within
the phase. The fallback is reported as "segment-restricted knockout fallback", never as path patching.

**Design.** It uses `knockout.py` with ticket 3, run as `--knockout-scheme interchange --knockout-counterfactual
neutral_twin --knockout-singles off --knockout-groups FILE`.
- **T1.** Groups are the quartet q; W, every head and MLP of layers 18 to 31 not in `C_t`; q ∪ W; and each C1 or C2
  draw ∪ W. Positions are `readout`, with a second invocation for q at `all`. The rule number is M_fb = (KO(q) +
  KO(W) − KO(q ∪ W)) / KO(W), the share of W's effect that is redundant given q, and it closes at ≥ 0.50. This is
  weaker than T1 proper, because W's knockout is a total effect, not the direct share.
- **T2.** Head outputs cannot separate Q from K. The proxy knocks out every Component of layers 0 to 16 at the option
  tokens (`segments=item_1_question_pair+item_2_question_pair+item_1_question_option+item_2_question_option`), against
  the same at `readout`, with the 15-point rule. It patches what those positions carry to every later reader, and the
  reading says so.
- **Cost.** One job, both tasks, one load, about 20 groups × 13 batches per task; 1C-b ran 1,835 s, so 0.75 GPU-h.
