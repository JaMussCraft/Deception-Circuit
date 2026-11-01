# Original D/H/F cue-circuit runtime and mask audit

2026-10-24. Lead compactions5. This worker owns this note and accompanying read-only audit receipts in this directory. No production edits, git mutations, scheduler checks, models, jobs, APIs or notebook execution. Root owns new source/operational release; other agents own design. Separate v2/G14 work is out of scope.

## Verified worktree and frozen evidence

Actual worktree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot`; HEAD remains `5f74d0c3653a63c411997e0f666a79171076a8d8`; `git status --short` returned empty. No local AGENTS.md, CLAUDE.md or .claude/CLAUDE.md exists inside it. Primary `Deception-Circuit/AGENTS.md` exists and points to the shared Alignment/AGENTS.md; both and shared .claude/CLAUDE.md/memory were read. No local repository CLAUDE.md/.claude/CLAUDE.md exists.

All54 files bound by the final cue protocol's source/import manifest independently hash-match current worktree bytes. Selected immutable artifact bindings also match:

| Artifact, relative to worktree | SHA256 |
| --- | --- |
| `.superpowers/sdd/plan-sdr-cue-probe/freeze-final-5f74d0c/protocol.json` | `a6f968660f2cd072dc1589591d532143440356f49c50fd17c8b9b5166c56e915` |
| `.superpowers/sdd/plan-sdr-native-controls/sharding-freeze-final-1eb79892/protocol.json` | `1196d1569aa53ee1d37419c52b27d9fec4127f146def6e91e44fe5faf4e52914` |
| `outputs/_analyses/sdr-cue-probe/postprocessing-5f74d0c/analysis/analysis.json` | `4507c110a23ee4f57a563367021983d3757596c3f3bcdf3e5a0ecddbbf4d5a5e` |
| `outputs/_analyses/sdr-cue-probe/postprocessing-5f74d0c/join-audit/joined.json` | `fc581ac5901fc4cf559a3da58e3828fd4b073e31be25ddf8c216dbff0dfbd758` |

The last two files were SHA256-checked as immutable evidence, not read to select new conditions. New tokenizer feasibility uses the frozen **input** panel only. No source/artifact drift was found in these bindings; this is not an exhaustive re-audit of every historical output. Runtime environment/cache/hardware must be freshly verified on any later execution; no fresh runtime or queue state is asserted here.

## Exact original masks and semantics

Authoritative selection pointer is primary `Deception-Circuit/outputs/_launch_format_control/suites.json`, key `format-control-sdr-coarse-nls0.3.runs`; suite file SHA256 `26153a60ef6120c50a466204bef8f2443880563f2dda7b5dd8f77ce67e19fd97`. These are original seed42/NLS0.3/no-edge heads-only parents, not seed1/123/intersection variants, fine-neuron masks, newly learned/v2 masks or the later selective-suppression candidates.

All three run directories are under primary `/projects/beto/swong2/Alignment/Deception-Circuit/outputs/llama-8b-instruct_sdr_coarse/`:

| Role | Exact run basename | Heads | SHA256 active_nodes.coarse.json |
| --- | --- | --- | --- |
| D | `nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742` | 69 | `110a7a87bd2bf5dc9abdffa6d0efed20549b0dd4b2319ebfb0f57cdc8126c536` |
| H | `nls0.3_honest_noedge_noan_nomh_nomo_nomb_260922-092743` | 56 | `98abc1f4c97a54b6f70aa53b62c999428c619bb2cfb851c008909c94f5413562` |
| F | `nls0.3_nopressure_noedge_noan_nomh_nomo_nomb_261013-204850` | 68 | `833aceb454d7bba6c1e049c9a0ce95d07369e948193fb64d765b02ac6cf3fa06` |

`runtime-seam-audit.json.original_masks` stores the exact full head lists, absolute paths and independent SHA256 of each coarse mask, expanded active_nodes.json and config.json. Configs verify seed42, task sdr, conditions deceptive/honest/nopressure. F records margin loss0.7; D/H record None, so these are discovered task masks with training differences, not clean psychological modules.

Independently checked coarse active_heads equals expanded attention_heads membership. Every live attention head has all128 neuron leaves open, every excluded head all128 shut. Thus direct intervention keys are precisely `('head',layer,head)` for those sets; replace the full128-wide **o_proj input slice**, not q/k/v, whole o_proj output or a K/V group. Hooks `HEAD_KINDS` and `_traced_forward` at `component_analysis/hooks.py:155,440-447` implement this distinction.

Expanded masks also contain **all32 MLPs /589,824 MLP leaves** (`mlp_hidden`+`mlp_output`). They represent MLP-inclusive sufficiency when used as an intact circuit. Removing their whole expanded membership would erase every MLP. Heads-only ordinary knockout historically used `(expr)-m` at **leaf** granularity, where m is primary `outputs/_launch_format_control/allmlp_nomb`. `evaluation/algebra.py:18-44` defines leaf versus head algebra; head composition references absent mlp_blocks gates and can leak MLPs. `expand_coarse_masks.py:77-118` explains synthetic all-open MLP leaves and why config fine-pruning flags are now True despite noan/nomh/nomo slugs. For the new unmodified-model hook experiment, extracting exact head tuples directly avoids this composition trap; all MLPs remain natural.

Independent full-set arithmetic:

| Set | Heads |
| --- | --- |
| D∪H∪F | 103 |
| D∩H / D∩F / H∩F | 43 /36 /43 |
| D∩H∩F | 32 |
| D only / H only / F only | 22 /2 /21 |
| (D∩H)−F / (D∩F)−H / (H∩F)−D | 11 /4 /11 |
| D−H / D−F / H−D / H−F / F−D / F−H | 26 /33 /13 /13 /32 /25 |
| Outside D∪H∪F, in32×32 head universe | 921 |

All full intersections/exclusives and their actual tuples are in the receipt, not only counts. Root's selected targets are **D69,H56,F68,shared32,D-only22,(D∩H)−F11,D−F33**. Verified `D−F33 = D-only22 ⊔ ((D∩H)−F11)` exactly, with empty intersection. Comparing the union's intervention to either constituent tests interaction/occlusion; union effects need not sum.

For **each of seven targets**, an outside-D∪H∪F comparator can exactly match its head count in every layer without replacement. `runtime-seam-audit.json.selected_seven_targets` records target tuples, per-layer required counts and eligible outside counts. Examples of the largest requirements: F needs11 at L12 with20 eligible outsiders, and10 at L13 with19; D needs8 at L8 with24 eligible and8 at L14 with21. No fallback or unmatched layer is needed. A deterministic hash-ranked draw within each target/layer can be frozen before inference; the designer must fix its tag/seed and store actual tuples. One draw per target is a comparator, **not a null distribution or percentile test**. Comparators may overlap each other; all are outside the original union. Unequal target sizes and strong overlap remain interpretation limits.

## Tokenizer-only answer-example reversal

`example-order-tokenizer-audit.json` records all256 original report input rows, plus counterfactual alignment summaries. Cached local AutoTokenizer only was loaded; no model. All512 original main token vectors reproduce exactly.

For each report prompt, exchange only the two complete quoted permitted answers after `Only respond with`; preserve interrogative options, system/record/truth/favored/norm, manual shell, `.THE`, stem and candidate identity0/1. Across all256 report rows:

- Every reversal changes exactly **two token IDs**, with **zero token-length change**.
- Reversed report prefixes span128–131 tokens; maximum131+64=195≤224.
- In the named subset,128 old report prompts plus128 reversed ones give256 report prompts. Named retrieval has128 prompts and **no answer examples**. Thus root's chosen384 unique baseline panel has256 reports+128 retrievals. Fully crossing example order on retrieval would duplicate128 identical prompt pairs and waste128 slots.
- In original named inputs, all128 truth-flip pairs have equal lengths and exactly two token changes. Record-order flips have equal lengths/six token changes; question flips equal lengths/two changes; favored flips equal lengths/one change.

Example-order and truth donors therefore have aligned prompt lengths/absolute token coordinates in these same-task fixtures. Exchanging a candidate token's identity at its positional slot is intentional for the example donor; do not “align by lexical name” and undo that manipulation. Preserve `truth_name=pair[truth]`, independent of answer-example order. For any broader future donor or cross-task mapping, equal length is insufficient: freeze position role/offset mappings, BOS/headers/readout positions, validity masks and all length/collision checks independently. No input row was excluded using observed responses.

## Three intervention semantics that must not be conflated

Current `scripts/sdr_cue_probe.py:384` sets use_cache=False. `scripts/sdr_native_controls.complete_batch` (`:197-258`) **fully recomputes** each B8L224 forward. No KV cache carries patched activations to the next call.

1. **First-step-only intervention:** patch once at the initial stem readout or prompt; then ordinary decoding. Only emitted first token can carry its influence forward. Calling this a persistent prefill intervention would be wrong under this runtime.
2. **Sustained prompt-prefix transplantation, root-selected:** capture selected donor heads on its natural initial prompt, then at **every** recipient decode step replace exactly the original recipient prompt positions from that frozen capture. Include the complete prefill through the supplied assistant stem if “all prefix” is the selected mask. Never replace padding or positions appended by generation. Reapply even after the first token. Unselected heads and all MLPs compute naturally. Standard causal attention makes initial-prefix activations independent of future appended suffix; same-shape numerical calibration must confirm that cached/self prefix values reproduce the unperturbed path. This is a static counterfactual-prefix transplant, not a continually updated donor-answer stream.
3. **Matched-context donor under recipient continuation:** on every step append the recipient's exact emitted token IDs to the donor prompt, capture the donor's natural heads on that forced common suffix, and transplant under the frozen alignment. This needs an extra donor forward each step (and optional recipient capture), and generated sites may be overwritten if the scope includes them. It tests donor-conditioned states under the recipient's history, not donor's own free rollout. Using the donor's independently generated continuation instead introduces unequal histories/lengths and emitted-answer overwrite. This broader scheme is **not** root's selected prefix-only design.

A fixed donor **stem-readout** vector injected repeatedly at the recipient's moving current readout is yet another treatment: static-vector injection onto generated sites. It is not prompt-prefix mediation and violates the selected “generated positions unpatched” scope.

“Ordinary family effect” should mean a direct joint replacement of all heads in the selected family in the intact model, leaving all other heads/MLPs natural. It contrasts with prior pass1/pass2 path patching/freezing other streams. This is distinct from **zero ablation** (zero those slices), **mean ablation** (replace from a separately frozen natural mean bank), and **interchange** (replace donor values). Historical evaluator definitions are at `evaluation/ablation.py:4-28`; importing its node-gated runner is unnecessary here. A prefix-only transplant cannot be described as full-position global head removal. If any ordinary-zero comparator is proposed, specify whether its mask is all prefix or every current valid token; these measure different interventions.

## Smallest safe implementation seam

`component_analysis/hooks.py:163-173` supplies `Replacement(value,positions)` with Boolean `[batch,seq]` masks; `positions=None` overwrites every physical slot and is unsuitable for the chosen scope. `hooks.capture_forward(model,ids,mask,*,components,positions=None,replacements=None)` at `:490-507` accepts full-family replacements and returns READOUT. Read logits through unchanged `scripts.sdr_routing_pilot.capture_logits(model,capture)` (`:407-412`), which selects logical readouts and uses actual FP32 RMSNorm/unembedding (`hooks.readout_logits :583-622`). Hooks' `positions=` sets readout indices; **Replacement.positions** controls patch scope—do not substitute one for the other.

The existing complete_batch is reusable unchanged for intact baselines, but its `forward` closure exposes **no scientific intervention callback**. Do not monkeypatch imported hooks, supply a fake “control” replacement or label intervention rows calibration. A small new study-specific shared greedy kernel should retain its fixed-slot/logical-append/EOS/checkpoint/control mechanics while accepting an explicit fixed prefix replacement map. Route intact and patched arms through the same new kernel to make same-path controls meaningful. Import existing make_batch/compare_vectors/readout/hook helpers, preserve old source. No new generic experiment framework or all-head grid is needed.

For a recipient batch, build original-prefix validity mask from each frozen prompt length. Pack donor tensors into B8L224×128 coordinates, apply exact frozen same-task positional map and mask only valid prefix positions; dummy slots remain false. Selected families use subsets of one common capture union when possible. Reuse frozen donor capture across arms without changing it; use explicit detached/compact clones so accidental in-place writes cannot mutate the donor bank. Preserve mapping IDs, tensor dtype/shape/hash and selected family/source-mask hashes in provenance. Replacing family heads jointly is a real intervention at each layer: later untouched components adapt naturally.

Same-path numerical receipts should include intact repeat/empty hooks, family-capture-versus-readout-only intact equality, and self-prefix replacement using the **same** mapping/masks/packing used by donors, excluding READOUT_KEY itself. Calibration must cover each distinct arm/kernel/scope, longest prefix and required self/full-component controls. Repeat a patched forward on identical IDs/replacements to test deterministic patched computation; do not compare a real non-self patch to intact logits expecting equality. Empty replacement is a no-op control, not an outside-head scientific comparator. Checking a zero-dose interpolation that never exercises mapping is weaker than actual self-prefix replacement. Use full FP32 vocabulary, finite values, ≤1e−5 maximum error, identical greedy decision and bitwise status; retain actual deviations. Verify frozen prefix self-controls at generated contexts too, so complete-response scope is actually tested.

Keep fresh source commit/hash/payload/parent manifests/mask files, exact tokenizer/config/model/software and full actual GPU identity bound to calibration/main. Reuse cue wrapper's actual Slurm Start/End binding, explicit cwd/env/offline/single-GPU/BF16SDPAeval guards, premodel/headroom/forecast fit checks before and after load, deadline-minus-shutdown once, fixedB8L224/cap64 and atomic partial status receipts (`sdr_cue_probe.py:274-427`). New protocol/runner must have its own row counts and source manifest: old cue verify/run validates the old512-row payload and calls the old primitive, so cannot run new384+intervention science unchanged. All old receipts remain evidence, not transferable calibration for new source.

## Memory and compute accounting

Llama geometry here is32layers×32heads, head width128. A compact BF16 family capture at B8L224 costs `K*8*224*128*2` bytes: D30.19MiB, H24.50MiB, F29.75MiB; union103≈45.06MiB. But current hook outputs slice `.detach()` views from saved **full layer o_proj-input tensors** (`hooks.py:470-482`), retaining underlying storage. All D/H/F span12 layers each: underlying head-layer storage alone is168MiB per capture; union spans15 layers,210MiB. READOUT adds14MiB plus residual/logit/trace buffers; this is not total GPU memory. Clone compact slices before long-lived CPU/donor caching, then release full captures. Full-component self-controls retain many more tensors; calibrate peak allocation/reservation with that actual path. No empirical memory-fit claim is made here.

Prefix cache per row can compact to actual prefix length: `K*prefix_length*128*2` bytes, plus tensor/metadata/packing overhead. Donor-only initial captures can be shared across reciprocal arms/families if computed naturally and subset afterward. Captures from an already intervened donor do not represent the intended natural donor. CPU streaming/transfer bytes and checkpoint costs must enter the forecast if caching is off-device.

For a stream group with `M=ceil(N/8)` physical batches and cap64, intact baseline requires at most `M*(64+2)` forwards under old repeat/empty first-step recipe. Root's384-baseline panel gives48 batches/3168 forwards. Sustained frozen-prefix transplantation requires `M*64` patched generation forwards per arm, plus declared numerical-control forwards and one-time natural donor-capture batches; **not** a donor forward each token. Matched-context dynamic donors require roughly `2*M*64` forwards per arm, before controls. New selected arms/families/outside sets increase N; compute exact batch rounding per frozen treatment grouping, not just row count/8 if groups are separately batched.

Use a weighted forecast with calibrated maxima for intact, donor capture, patched family, largest-family/outside capture and full-component controls, plus actual startup/premodel/cache verification, CPU/GPU transfer, per-active/per-panel checkpoint bounds and explicit shutdown/headroom/margin. A single conservative maximum across all these physical-forward types is safe but pessimistic. Main cap forecasting must use64 tokens for every row even if pilot outputs are short. Old cue baseline calibration measured maximum1.063030364seconds/physical forward on an H200150GB-class identity, but it has no sustained-prefix scientific replacement or new outside-family capture and **cannot release/price the new study by itself**. Reused cue IO48 is conservative only if the new larger row/artifact volume is separately bounded; do not blindly assume its64→512 growth bound covers thousands of new intervention rows. No timing-dependent scientific row changes, automatic retries/shards, threshold rescue or outcome-based support selection.

## Causal interpretation boundary

Target-versus-layer/count-matched outside controls distinguish effects of these discovered sets from one generic matched perturbation, not all possible collateral or a null distribution. Retain ordinary whole-family interventions and reciprocal input-defined donors on every selected contrast, not only prior failed/correct baselines. Include agreeing cue controls, factual retrieval collateral and complete residual/format distributions; a non-commitment is not a correct factual answer and a simple report commitment is not a false factual assertion.

Example-order transplantation tests answer-example-conditioned processing; truth transplantation tests factual-content-conditioned processing. A changed emitted identity can reflect inserted donor content or generic damage. Crossed axis/task controls and direction-specific outcomes are needed before a reference-variable interpretation. Strong shared32 effects, saturated parent effects or failure of additivity do not assign psychological roles to D/H/F, prove deception/intent/pressure or establish completeness. New interventions must remain a separate prospective study; all old failed validation gates remain failed.

## Supplement: exact alignment, calibration and timing proposal

This supplement responds to root/designer/reviewer requirements for the prospective **384 baseline +8960 intervention =9344 scientific completions**. It is a concrete recommendation for their spec freeze, not code, GPU release or changes to the earlier receipts. The root-selected prefix-only scope and14 treatment families (seven targets/seven fixed comparators) are unchanged.

### Absolute truth-token alignment independently verified

`truth-span-tokenizer-audit.json` independently tokenizes all384 new named-form prompts:256 reports with independently crossed example order,128 retrievals. Across192 undirected /384 directed truth pairs, **all role/segment character boundaries and token offset mappings are identical**. The only changed bytes are the two factual predicate spans; both `damaging` and `harmless` are8characters and occupy **one token each** in these contexts. Token-ID mismatches are exactly those two status-token positions, with zero changes outside them and no shifted boundaries. The audit records each pair's exact status spans/indices and checks system, record/norm/favored/clause, user/question and assistant-stem boundaries. Thus same-task truth donors support the intended absolute-slot alignment here; this conclusion is stronger than equal total token length and does not generalize to new wording/tasks.

The receipt also verifies the frozen stress literal ` test` encodes as **[1296]**, a single non-EOS token. No outputs were read or used to choose that continuation. `runtime-seam-audit.json.coherent_C_A_C_B_C_J_feasibility` proves every layer can choose C_A matching D-only22, then C_B matching (D∩H)−F11 excluding C_A, and set C_J=C_A∪C_B matching D−F33. At every layer A-required+B-required=J-required≤eligible outside-original-union. No actual comparator draw is made by this audit; the designer freezes its rank tag/seed/tuples.

### Fixed calibration-only stress:14 B8 batches,5462 model forwards

Recommend14 family-homogeneous B8L224 stress batches, one for each target/comparator. Their112 slots are **calibration-only**, using the two original disjoint calibration fixtures. Within each family use the designer's eight frozen input cases covering E/report±, T/report± and T/retrieval±, both templates, plus its two fixed extra cases. In the proposed slot schedule,0/1 are E/report opposite example directions,2/3 T/report opposite truth directions,4/5 T/retrieval opposite truth directions,6 an additional E/report case and7 an additional T/report case. Freeze all source/recipient/donor IDs and remaining factors before inference. This replaces any inherited expectation of “64 calibration rows”;112 slots and their exact schedule are the new study contract.

Every stress row runs64 forward/decode iterations with token1296 forced after each iteration, **regardless of the model's predicted EOS or candidate**. These are explicitly forced-history numerical/runtime tests, not free completions, main-answer extensions or scientifically scored responses. The natural full-vocabulary prediction is recorded for comparisons but never determines the forced sequence, row eligibility or duration. Main responses still stop naturally at EOS or64-token cap. Prefix131+64≤224; step63 validates a long generated-prefix state.

For each family batch, first make two natural initial-prefix captures: donor D and recipient S. S supplies the self-prefix bank; D supplies the scientific-prefix bank. Then at **each of64 steps** execute:

1. I: intact current recipient context, READOUT only.
2. I-repeat: same I context/path.
3. I-empty: same context with empty replacement dictionary.
4. S-self: replace precisely the selected original-prefix slices with the frozen recipient S bank; all appended positions unpatched.
5. P: replace those same slices with frozen donor D bank.
6. P-repeat: identical P context/bank/mask.

Compare I-repeat/I-empty/S-self against I, and P-repeat against P, over the complete FP32 vocabulary. Every vector must be finite; each comparison requires maximum absolute error≤1e−5 and identical greedy token. Record bitwise equality separately, actual maximum error, IDs/step/signature and argmax; **any failure aborts release**. Predicted EOS does not excuse missing later stress comparisons. This supplies28,672 row-level comparisons across family/task/axis/direction and generated-prefix steps. Assert exact family-slice lists and original-prefix-only masks; all nonpadding aligned prefix positions covered, every generated/padded/dummy position excluded. Same-path prefix self-controls exercise the actual packing/assignment code used by scientific transplants.

At steps0 and63 of each batch additionally run full-component natural capture and full-component self-replacement; compare each with the same step's I. Exclude READOUT_KEY from replacement while capturing READOUT naturally. These four extra passes/batch supply448 further row comparisons and measure peak memory on the full-control path. Use two fixed initial I forwards (initial first batch) as explicit cold/warm warm-up and compare them (eight row comparisons). Hence model forwards are exactly `14*(2+6*64+4)+2 =5462`; required row comparisons total29,128. Every extra forward, forced token, I/O benchmark, CPU packing and calibration artifact write is charged to calibration, excluded from scientific denominators and recorded under a distinct stress status.

### Exact main numerical scope and batching

All384 intact baselines get first-step repeat/empty checks, using the same full-vocabulary finite/tolerance/greedy rules. Every one of8960 scientific intervention completions gets **P/P-repeat at every actual decode step through EOS/cap**; numerical equality is checked before committing its next greedy token. Main empty/self/full-component whole-decode validity is supplied by the exact calibration schedule above, not undefined main “spot checks.” All planned rows remain, with failure/incomplete statuses if a numerical failure aborts. Main receipt must state these scopes explicitly instead of claiming main every-step self-controls.

Use1120 family-homogeneous B8 intervention batches (80/family). For each batch capture its eight natural donor prefixes **once using that family**, clone compact detached slices, release the full capture and decode P/P-repeat using the fixed bank. Discard the bank after that batch. This deliberately avoids a global union cache/platform: extra repeated donor-capture cost is small relative to the repeated decode work, while the actual capture key sets match calibration. Maximum compact scientific bank is D69≈30.2MiB at B8L224; each family's natural head capture may retain168MiB underlying layer storage until released. Self S bank is needed in calibration; main does not need a second long-lived self bank. Record peak allocated/reserved memory for full controls and scientific bank paths separately. No claim about model/trace total memory or hardware fit precedes calibration.

### Cold versus warm forecast, without repeating initialization147k times

Freeze canonical forward signatures from exact capture/replacement key lists, physical B/L/dtype and control path. Measure each signature's first-use latency c_g separately from the maximum later warm latency w_g. The two initial I calls make this explicit for the intact path; donor/S setup makes two captures for each family signature;64-step P/self/repeat schedules give ample warm patch observations. Treat first-use of each actual family/key plan separately rather than assuming one global cold initialization. A fresh main process budgets each main-used first-use latency **once**; do not multiply a first-ever trace/allocator/import cost by every subsequent step. Retain the first-call maxima in receipts as well, so the separation is reviewable.

Main full64-cap forward inventory is exact:

- Plain intact I:48 baseline batches×65 =3120 forwards (64 greedy steps plus first repeat).
- Empty intact:48 first-step forwards.
- For each of14 families f:80 donor captures C_f and80×128=10,240 P/P-repeat forwards.
- Total: `3120+48+14*(80+10240)=147648` physical forwards. No expected-short-answer discount.

A conservative measured warm term is `3120*w_I +48*w_empty +Σ_f(80*w_Cf +10240*w_Pf)`. Include donor packing/cloning/synchronization in the measured C_f transaction or bound it separately80times/family. Add `Σ_g c_g` over the **main-used** signatures once (this safely overcounts the warm work of their first call), fresh wrapper/environment/source/cache/provenance verification time, model load, measured final assembly/serialization, the I/O term below, explicit premodel headroom, shutdown buffer and safety margin. Keep full-control first-use/warm costs in calibration accounting; do not charge them as thousands of main calls if main never uses that path. Calibrate elapsed source/cache verification and model initialization separately from warm forwards. These are observed operational bounds with a stop guard, not a guarantee against arbitrary system slowdown.

The fresh forecast is published before main reservation, then rechecked against actual remaining allocation before/after model load and during bounded checkpoints. Exact new source/software/cache/masks/plan/B8L224 and full actual GPU class/name/capability/memory/count must match. The old H200 timing receipt does not authorize this source or predict its new patch/control paths. Root can review one fitting allocation after fresh calibration; no automatic sharding, retries, panel reduction or source retuning.

### Proposed batch-scaled journal:3510 healthy writes, no per-token disk writes

Root explicitly permits separating **whole-decode numerical checks** from checkpoint cadence. The simplest layout is a single-allocation journal, not a resume platform:

- Before each of1168 total baseline/intervention batches, write one immutable attempt-start record containing exact eight IDs, treatment/donor/mask identities, protocol/source/operation hashes, ordinal, start time and attempt_number1. It durably marks rows attempted before any model work.
- At completion write one immutable terminal batch JSON containing all eight complete outputs/statuses/controls/runtime and bindings. For caught error/stop, write a single active-batch snapshot from RAM and a terminal failed record preserving available tokens and exact incomplete states. No auto retry or resume.
- Use one small combined progress/receipt JSON initially, after every terminal batch and at final closure:1170 writes. It records the committed batch prefix/count, current ordinal, accumulated resource maxima and relevant hashes; it must not duplicate all9344 response rows or a growing full trace.
- Write protocol, operations and forecast once (three files). Assemble canonical generations.json once at clean/handled-error closure by joining the immutable planned manifest with terminal records, active snapshot and attempt records. Include **all9344 planned IDs**, explicit completed/error/attempted-incomplete/unattempted statuses and original order; independent integrity audit verifies each expected ordinal/ID/hash.

Healthy full-cap writes are exactly `1168 attempts+1168 terminals+1170 progress+3 metadata+1 final =3510`. Reserve one additional exception active snapshot; a failed terminal/progress substitutes its scheduled terminal/progress rather than disappearing. If SIGKILL prevents the handler, the current eight rows remain honestly attempted-but-incomplete from the durable attempt file and may lack final token progress. The auditor can reconstruct that state from manifest/journal even if final assembly is absent. Do not invent tokens, report them completed, restart automatically or delete them. Numerical step receipts/token progress can accumulate in RAM and persist in terminal output; disk writing after every token or internal control forward is unnecessary for this no-retry design.

For an exact bounded I/O forecast, pre-freeze three serialization byte ceilings: small metadata/progress/attempt, eight-row terminal/exception snapshot, and large protocol/final generations. Compute worst-case templates with all64 token/readout slots and the frozen maximum permitted text/control-record representation, not average observed answer length. If per-step comparisons are retained in terminal artifacts, include their maximum64-step counts. Record exact ceiling sizes and require actual serialized writes never exceed them; an oversized record stops for review with its existing bytes preserved.

During calibration, perform **eight fresh atomic writes per byte class** (24 explicitly charged synthetic writes) on the actual output filesystem with the same serialization/fsync/rename implementation. Use clearly labeled calibration-only synthetic I/O records, never scientific IDs/answers or an exportable generations file. Record first-use latency separately and max of the other seven, including serialization. These writes must exercise creation of fresh immutable names as well as the chosen atomic replacement behavior; main uses both. If the protocol/final ceiling is too different from terminal to share one class safely, split it explicitly and count the extra eight writes rather than use a guessed multiplier.

Let w_s,w_t,w_l be conservative warm maxima at those measured ceilings and c_s,c_t,c_l first-use costs. A simple bound is `(1168+1170+2)*w_s +(1168+1)*w_t +2*w_l +c_s+c_t+c_l`: the two extra small writes are operations/forecast, the two large writes protocol/final generations, and the extra terminal-size write reserves the exception snapshot. This accounts for3510 healthy writes plus one exception snapshot. Include final in-memory assembly/validation and its serialization once if not already covered in the measured large-write transaction. Freeze the actual layout/counts in spec/source and verify CPU fake-writer counters; no old IO48 multiplier or per-row/cold-I/O extrapolation is needed. If this layout is not adopted, recompute the actual frozen callback counts; do not mix its3510 count with the old per-forward publish policy.

The designer and reviewer should approve this layout/control schedule before implementation. Existing completed-phase checkpoints and receipts remain immutable.

### Full-spec reconciliation (supersedes optional details above)

After reading the designer's actual full spec sections5–6, I find the control scope/counts/timing plan coherent, with no blocking runtime finding. The final proposed spec makes two sensible simplifications/clarifications relative to this supplement's earlier options:

- **No extra two-pass warm-up:** first I/I-repeat within the forced schedule already supply first-use/recurrent intact timings. Freeze **5460 calibration forwards**, not5462. The additional recipient-setup-readout→step0 I comparison costs no new forward and adds112 row comparisons. Therefore the exact scheduled numerical comparison inventory is28,672 per-step +448 full-component +112 setup =**29,232 row comparisons**, assuming each pairwise comparison is recorded individually.
- **Six directly benchmarked I/O classes:** attempt, terminal-eight-row, small progress, metadata maximum, final9344-row assembly and emergency-eight-row snapshot. Eight fresh atomic writes each gives**48 benchmark writes**, all charged to calibration. Main class counts are1168/1168/1170/3/1/1-reserve; healthy3510 plusone emergency reserve. The14 calibration batches separately produce48 healthy journal writes (14+14+16+3+1), plusone emergency reserve. The earlier three-class shared ceilings were optional; six explicit classes are cleaner to audit.
- The full spec applies25% operational margin to the measured compute/I/O subtotal and states initialization/headroom/shutdown separately. Signature-cold costs are charged once, warm recurring costs multiplied by their counts; retaining full N warm plus one cold is an explicit conservative overcount, while (N−1)warm+cold is exact count accounting. The forecast artifact should say which convention it uses and independently list actual physical calls, so conservative time accounting cannot look like extra undeclared forwards.

The new scientific spec, calibration schema/ceiling oracle, actual source and wrapper still require their normal independent reviews before GPU release. This is a design sanity read only; none of the proposed timing maxima, memory peaks or byte ceilings has yet been measured for the new kernel.
