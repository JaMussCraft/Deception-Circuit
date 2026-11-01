# Shared-composition task review preparation

2026-10-26. Independent Codex Sol review preparation. This is **not an implementation review or release approval**. Root will supply the frozen diff package, implementation report and exact hash before review begins. No live implementation source, tests, models, notebooks, jobs or git commands were inspected or executed. Only this preparation document was written.

Read root `AGENTS.md`, `.claude/CLAUDE.md`, shared memory index/relevant repository, environment, testing, communication and SDR mechanism notes, and this study's `spec.md`, `plan.md`, `implementation-seams.md`, and `scientific-design-review.md`. The conventional `CLAUDE.md` and `.claude/CLAUDE.md` locations at both target worktree and repository root are absent. The seam note records root startup synchronization already completed. The using-superpowers adapter explicitly exempts dispatched subagents from its general workflow. No agents were spawned.

## Independent immutable-input checks

Read the original Stage1 manifest directly, without importing any new or old runner:

`Deception-Circuit/.claude/worktrees/sdr-routing-pilot/outputs/_analyses/sdr-routing-pilot/stage1-retry-f7cb49f-20261021T002501Z/manifest.json`.

- File SHA256: `8e1c545a74c69311ac276d27f83247710374d258d578ad3659e93dca87cd78c3`.
- Stored internal manifest hash: `36bff9ebb6e4d9d3954ba81ce0f281664d0f887041109c986c5a86fd9cdd3ff0`.
- Input-only selection: `valid`, condition P/N, primary P pressure identity, historical confirmation split. Exactly **24 stories and 96 unique inputs**, each story having P0/P1/N0/N1. Saved lengths equal saved token-ID lengths.
- Eight directed pairs per story: P0↔N0, P1↔N1, P0↔P1, N0↔N1. Exactly **192 unique pairs**. Every original `recipient_id|donor_id` saved `common` map exists and is nonempty; support is **60–79 positions**. Every checked coordinate is inside its saved recipient/donor prefix, and recipient coordinates are unique within each map.
- Main prefix lengths **100–118**, so L224 accommodates cap64. This verifies fit, not permission to change saved IDs/stems.
- First lexicographic discovery story is `1240d0bf2a32959907915952de3b773e05e7a178e54aeccb5e2690f4265d25da`. Its four selected variant suffixes are **0,2,5,7**, with lengths **101–114**, giving eight calibration pairs. Its input IDs are disjoint from all main input IDs.
- Recomputed active-head intersection of the three original D/H/F parent masks equals the manifest's exact **S32** list. All parent mask file hashes match the original manifest. L17H0–3 are all outside their union; K17group0 is a valid prospective geometric comparator.
- Original candidate6 is exactly `(12,6),(13,5),(13,20),(13,21),(14,24),(17,26)`. U5 omits `(17,26)`, H26 is disjoint from U5, and their union equals candidate6. All are contained in S32.
- Count oracle: **96 + 192×20 = 3,936 science rows**; B8 gives **12 baseline + 480 intervention = 492 science batches**. Duplicated clean-only outcomes remain separately planned rows.

These checks used a short stdlib JSON script under `/sw/external/python/anaconda3/bin/python3.9`; no tokenizer/model was loaded. Sandbox startup failed before the first read because bwrap could not create its temporary directory; subsequent commands used narrowly justified approved escalation with `login=false`. Claude service usage counters are not Codex Sol budget evidence.

## Frozen-package review checklist

Review only the exact frozen three-file package against base `4f0278487b0285dd27cbc34d20d88c911dc5562a`, together with implementation report/receipts and root's source hash. Record actual defects with file/line evidence and consequence. Preserve the ratified design; do not add attention tracing, L24, behavioral gates, prompt cleaning, doses, new subsets or broader framework work.

### Inputs, arms and execution sites

- Freeze reuses saved prompt, IDs, lengths, source/story/split/truth/item metadata, forced assistant stem and exact saved common maps. The first lexicographic discovery story is chosen by immutable ID, never by outcomes. Calibration is excluded from main aggregation.
- Exact 20-arm membership and receiver bank origins match the spec. U5 capture uses ordinary `capture_forward` source replacement only; other heads and all MLPs evolve naturally. No old `receiver_inputs`, full-component freeze, donor receiver substitution or direct-edge-bank reuse enters the induced capture.
- B_A receiver values are already in recipient coordinates and are never donor-remapped. Source values alone use saved common donor→recipient maps. Clean and induced receiver masks cover each original recipient prefix, independent of partial source masks.
- Q17H24, pre-RoPE K/V17group6 and pre-o_proj head outputs are distinct sites. Geometry is 32 Q heads / 8 KV groups / head width128; group6 footprint is H24–27, group0 H0–3. H26 output is never described as causing same-layer Q/K/V. QK uses simultaneous Q24 and K6 writes.
- Source-plus-receiver composition preserves distinct-key dictionaries/masks and unchanged hook ordering. Arm11 uses U5-induced QK, arm18 U5-induced quartet, with no source intervention in either rescue arm.

### Banks, scoring and numerical controls

- Every key has B8×L224×128 BF16 finite values and its own B8×L224 Boolean mask, cloned/frozen and checked for mutation. Masks are subsets of original recipient prefixes and false for generated, pad and dummy slots at every step, including forced64. Actual write tests prove untouched coordinates remain untouched.
- No cache, fixed B8/L224 physical geometry, declared SDPA backend, all cached EOS IDs `[128001,128008,128009]`, cap64 including EOS, greedy actual final RMSNorm/unembedding recomputed in FP32. No READOUT replacement masquerading as a control.
- Every arm has an actual same-kernel firststep score/full-vocabulary checksum and argmax, independently matched against decoder step0 checksum and generated first ID. Item margin is supplemental; full-vocabulary tokens remain unconstrained.
- Full-vocabulary repeats, finite checks, empty/self Q/K/V/head controls and setup capture agreement use maximum absolute error ≤1e−5 plus exact argmax, retaining bitwise/max-difference receipts. Each decoded step is repeated as specified. Baseline versus each clean-only generated token sequence and EOS/cap finish must match exactly, not merely firststep scores.
- Tiny/fake-model tests distinguish naturally propagated induced state from old full freezing, verify mixed-source/receiver writes, wrong-site rejection and grouped footprints. Read targeted test receipts in both base and mgnp environments; do not rerun tests before the frozen package arrives.
- Norms use FP32 captured tensors only, last-prefix L2 and prefix RMS over actual prefix-length×128 coordinates, separate Q/K entries, excluding dummy/pad/generated coordinates. No attention trace or extra norm captures.

### Durable acquisition and timing

- Source/protocol/input/model/tokenizer/config/weight/backend/software/geometry binding is sealed before execution, verified fail-closed before accepting/reusing records and unchanged on resume. Dry-run invokes the actual absolute wrapper without model/CUDA work and with offline mgnp behavior.
- Accepted work is atomic at the declared **arm batch** boundary, with durable rows, checksum, identity and journal agreement. Audit crash gaps before and after terminal publication/journal acceptance; an already published valid terminal must be recovered or recognized without silently rerunning accepted outcomes. Failed/incomplete attempt evidence is retained.
- Resume verifies existing accepted contents and reruns only genuinely incomplete fixed arm batches. It rejects tampering, mismatched source/calibration/geometry/protocol, duplicated accepted rows, conflicting terminals and orphaned states that cannot be proven safe. A partial arm remains one incomplete fixed batch, without dropping cap/error rows or selecting favorable outcomes.
- Setup reuse is batch-local and realistic: cold versus warm arm counts, repeated decoding, firststep/control/setup captures, serialization and startup/publication/shutdown are charged appropriately. Calibration naturally exercises all20 arms on eight pairs, plus prospectively fixed forced64 arms10/18.
- Deadline admission uses actual remaining allocation time and measured per-arm costs with reasonable buffer. Whole-panel forecasts are advisory after admission; a worst forced64 isolated cost is not repeatedly multiplied by all work and compared with elapsed allocation. Resumption does not count setup as free or double-charge startup for every arm.
- Wrapper binds actual Slurm start/end and approved cwd, guards shell initialization under errexit, and does not reuse old pilot budget logic. Operator remains sole owner of accounting and dispatch.

### Output and interpretation contracts

- All3,936 science outcomes remain in coverage with separate termination status, generated tokens/text, stem-plus-continuation and provenance; cap/error/refusal/null behavior never controls continuation. Strict primary capped tuple is kind=capped, candidate=null, names_only=false, factual_disclosure=uncertain, retaining full raw text.
- Exports show exact question, both lexical candidate identities and complete assistant response while hiding condition/facts/pressure/arm/source/hypothesis. Deduplication uses the complete blind annotation view. Later two fresh independent Sol raters are an acquisition/analysis requirement, not a prerequisite for software review.
- Arithmetic preserves separate axis/direction signs, equal story weighting and all clean-only terms. Bootstrap is stdlib Random(20261026),2,000 shared 24-story draws, sorted story order and draw hash, linear percentile interpolation. No reciprocal signed pooling without declared orientation, mediated fractions or automatic selector/content/intent labels.

## Pending handoff

Await root's frozen diff package, report and hash. The eventual `task-review.md` will distinguish source review conclusions, test evidence and runtime work still requiring the real pinned model; this preparation establishes no implementation PASS and no GPU release.
