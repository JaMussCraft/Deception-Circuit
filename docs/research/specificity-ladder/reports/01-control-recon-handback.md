# Hand-back 01: Control construction and crossed ablation reconnaissance

Agent: Codex research worker. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/START.md`. Status: resolved (read-only reconnaissance).

## What changed

- Orchestrator-owned report only: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/01-control-recon-handback.md`.
- No implementation, datasets, outputs, or shared memory edited. No staged operations.

### Concrete reuse map

- `/projects/beto/swong2/Alignment/Deception-Circuit/dataset/build_inversion_v2.py`: `inversion_row(d, chosen, condition)`, `derive_task(tokenizer, task, d_rows, h_rows, pool, max_seq_length, condition)`, `score_rows(rows, score_fn)`, `filter_scored(rows, scores)`, and score/assemble staging are the closest existing builder. Existing derivation replaces a clause **in the system turn**; moving it to the user turn requires a new constructor. Preserve source labels, instance ids, pressure ids, and source margins; invalidate stale margins on new prompts. `filter_scored` hardcodes `contingency.MARGIN`, so implement an explicit threshold parameter for 0.7/0.5 without modifying the global constant. Existing assemble calls `bridges2_delivery`, which runs git internally; avoid that helper under this session's no-git worker rule.
- `/projects/beto/swong2/Alignment/Deception-Circuit/dataset/contingency.py`: `stream_words(record, stream)` defines honest/target order per stream; `_deceptive(cond_scores, margin)` requires target argmax and target-minus-honest margin at least the threshold **in both streams**. A positive two-token margin without target full-vocabulary argmax does not pass.
- `/projects/beto/swong2/Alignment/Deception-Circuit/dataset/deception_common.py`: `build_prompt` puts intro, designation, and pressure in `system`, question in `user`, then the assistant stem. `build_prompt_pair` swaps the designated item between streams while preserving the user question; target and distractor reverse under corrupt. `score_prompts(prompts, word_pairs, model, tokenizer, device, ...)` returns margin, choice, and argmax. It uses native model logits; analysis hooks use fp32 final norm/unembedding, so retain same-path scoring controls and record precision conventions.
- `/projects/beto/swong2/Alignment/Deception-Circuit/data/datasets/far_v2`, `/projects/beto/swong2/Alignment/Deception-Circuit/data/datasets/sdr_v2`, `/projects/beto/swong2/Alignment/Deception-Circuit/data/datasets/ser_v2`: existing D directories contain train/validation/test, dataset config, filter report, and provenance. START specifies 200/200/1000. Their `_honest`, `_nopressure`, and `_inversion` sibling directories are distinct conditions. Existing inversion builder is test-only; A2 will need fresh train/validation construction, not a silent reuse of test ids.
- Relevant row columns: `clean_prompt`, `corrupt_prompt`, `neutral_prompt`, `target`, `distractor`, `clean_item_d`, `corrupt_item_d`, `desig`, `desig_inv`, `instance_id`, `pressure_id`, `pressure`, `task`, `designation_polarity`, `item_polarity`, `template_variant`, `condition`, margins, and inversion source metadata. `neutral_prompt` is the **prior-balance** prompt, not the neutral-clause H twin.

### Twin and donor pitfalls

- `/projects/beto/swong2/Alignment/Deception-Circuit/component_analysis/dataloaders.py`: `neutral_twin_dir` resolves the twin from `config['task']`, not from the condition directory suffix; `_neutral_twins_by_id` pairs by instance id, requires matching pressure id and neutral-clause metadata, and checks equal full token lengths, equal readout, and no token differences outside the pressure span in **both** streams. `TWINNED_CONDITIONS` currently allows only deceptive/inversion. A new condition id requires plumbing.
- `/projects/beto/swong2/Alignment/Deception-Circuit/dataset/matched_honest.py`: `assert_clause_aligned_pair(tokenizer, pressure_prompt, honest_prompt, clause, max_seq_length)` also checks BPE boundaries. Moving a system clause into the user turn breaks existing D/I/H prefix-and-suffix alignment. Do not bypass these assertions or claim the original H split is automatically the correct user-turn neutral twin. Construct an explicitly matched user-turn neutral-request twin, and retain the original H as its own ladder condition.
- For user-turn I, place the transparent request inside the actual user role and preserve the assistant readout stem; a system statement reporting what the user wants repeats the original confound. A semantically neutral system clause plus a transparent user request is a reasonable default, with a matched neutral user request for the twin.
- Same-item H donor and item-swap donor are different interventions. The same-id H clean stream preserves recipient item identity; H corrupt swaps it. A random H donor must match answer identity and record donor id/stream/position mapping. Reusing recipient rows as their own H donors tests same-id neutral replacement rather than independent resampling. If H is both recipient and donor, guard the resulting identity patch and include an explicit no-op control.

### Crossed ladder implementation seams

- `/projects/beto/swong2/Alignment/Deception-Circuit/component_analysis/knockout.py`: `knock_out_groups(model, batches, groups, scheme=..., plan=..., segmentations=..., mean_bank=...)` accepts groups as `(label, [('head', layer, index), ('mlp', layer, 0), ...])`. `KnockoutPlan` already supports interchange/mean/zero, item_swap/neutral_twin, and position restrictions. It jointly patches group members and retains per-id clean, knockout, and twin margins. Accuracy there is **binary target-vs-distractor**, not full-vocabulary argmax.
- Its `collect_mean_bank(model, batches, keys)` pools clean and corrupt activations over all unpadded positions with fp32 accumulation. Existing `run(ctx)` collects the current condition's bank. The required mean-over-H cell must explicitly pass H batches and record that provenance; ordinary `--knockout-scheme mean` alone does not implement START's crossed design.
- `/projects/beto/swong2/Alignment/Deception-Circuit/component_analysis/hooks.py`: `capture_forward`, `Replacement`, `readout_logits`, and `target_minus_distractor` are reusable for donor resampling and unrelated-task adaptation. Prefer this native analysis route for mixed head/MLP deciding sets. `/projects/beto/swong2/Alignment/Deception-Circuit/evaluation/ablation.py` is the gated-model route with a different mean-bank key schema; do not pass its bank directly to component-analysis knockouts.
- `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/mechanism-analysis/phase1/p1c_readings.json` names FAR/SER `greedy_k20`; SDR is `single_k20` with reading B and is descriptive, not a successful deciding set. Exact component lists are in that file and in task-specific group files under `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/mechanism-analysis/phase1/groups` (D and HF variants). Reuse lists directly rather than transcribing them.
- That groups directory also holds task-specific `*_heldout_D_sample.json`, `*_heldout_I_sample.json`, and option-B/R19 id lists. Use a fresh paired n=100/seed=1 draw from the new I pool excluding original selection ids, then evaluate D/H/F on those same surviving ids. Frozen held-out registry restrictions still apply; START's mechanism-analysis held-out sample is the authorized meaning.
- `/projects/beto/swong2/Alignment/Deception-Circuit/tasks/ioi.py`, `/projects/beto/swong2/Alignment/Deception-Circuit/tasks/gp.py`, and `/projects/beto/swong2/Alignment/Deception-Circuit/tasks/gt.py` provide unrelated tasks, but component-analysis loaders cover only mechanism tasks. Add a small Task-to-Batch adapter or a native-hook scorer. Keep the MMLU floor separate from EVAL 5 and inspect frozen-set registry before sampling.

## How verified

```
/u/swong2/.local/bin/codex-usage --pause-at 80
```

Observed: status ok; weekly used 3%, remaining 97%, should_pause false; reset 2026-11-06T16:07:41+00:00, checked 2026-11-01T19:10:39.772579+00:00.

```
sed -n '274,365p' component_analysis/dataloaders.py
sed -n '609,835p' component_analysis/knockout.py
sed -n '369,431p' dataset/deception_common.py
sed -n '789,824p' dataset/deception_common.py
```

Observed by source inspection in the primary checkout: strict same-span twin pairing; pooled own-task mean semantics; system/user separation; native-logit scoring. Also read the inversion builder, deciding-set JSON, existing test interfaces, START, shared guidance, relevant memory, and synthesis review D's M8 proposal. No behavioral claims are newly measured.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- No model, GPU/API, notebook, test, dataset construction, or ablation job run. Pool sizes in START remain inherited claims, not newly measured.
- Minimal proposed files, all under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`: `dataset/build_user_inversion_v2.py`, `component_analysis/specificity_ladder.py`, `tests/test_user_inversion_v2.py`, and `tests/test_specificity_ladder.py`; small condition-registration/dataloader changes only if using the generic task CLI.
- Meaningful tests: role placement and no hidden inversion instruction; labels and item-swap consistency; threshold boundary plus argmax-other rejection in either stream; deterministic score provenance and fallback reuse; own user-turn twin alignment; missing/duplicate ids rejected; H-bank source selection; same-item donor identity and nonidentity-H resampling; joint group subtraction; binary-versus-argmax metric distinction; tiny-model no-op and actual patch effects. Do not execute notebooks.

## Open questions

- **Required by START, no new approval needed:** user-turn transparent I; at least 300 FAR/SER ids; 0.7 then 0.5 then response-turn fallback; crossed four ablation types by two sets; D/H/F/unrelated ladder plus fixed-small-n MMLU; pre-registered 50%/25%/5-point rule. Record exactly which threshold and control arm supplied the final pool.
- **Routine design to settle before implementation:** user-turn neutral twin layout and token/position correspondence; explicit independent H resampling versus same-id H replacement; treatment of changed user-turn lengths. Default: aligned same-scaffold I/I-neutral twin, explicit donor identities, no assertion bypasses.
- **Scientific definition missing:** no established answer-mover exclusion list was found. The old L24 mover hypothesis was refuted in `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/mechanism-analysis/synthesis.md` (B-selector second clause). The quartet L17H24–27 and literature candidates L15H8/L15H11 are hypotheses, not a validated list; subtracting L24 as “known movers” is unjustified. Default: pre-register a selection-only mover criterion or clearly label a fixed candidate list, and publish full set plus actual intersection removed. This needs a lead scientific ruling, not user permission for routine coding.
- **Scientific metric to freeze:** define D and I effect denominators from their own neutral-request twins, retain raw signed gaps and denominator diagnostics, and report collateral accuracy separately. Existing knockout binary accuracy cannot silently serve as a full-vocabulary task-accuracy claim. Default: preserve both full-vocabulary argmax and binary margin metrics, with the gate's accuracy definition explicit.
- **Sampling choices not fixed by START:** unrelated task and n, MMLU n/subset, resampling seed count, and whether SDR's descriptive set receives a separate label. Default: one unrelated task, fixed reproducible small samples, report SDR as descriptive, and check `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/held_out.json` before any scoring.
