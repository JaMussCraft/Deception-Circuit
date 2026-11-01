# Reusable native SDR evidence and code seams

Read-only exploration, 2026-10-25. No model inference, jobs, paid APIs, notebook execution, or git changes. Counts below were recomputed directly from saved JSON/JSONL with `/sw/external/python/anaconda3/bin/python3.9`; they are preliminary exploration pending independent reproduction. This note is the only written file. All paths below resolve from `W = /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot` unless explicitly otherwise.

## What the original behavior actually means

`dataset/sdr_llama.py` explicitly describes **selective disclosure commitment**: choosing the harmless result is literally true as a commitment about what to show, while the damaging result goes unshown. `dataset/deception_common.py:SPECS['sdr']` uses damaging/harmless statuses, relevance instruction `THE DAMAGING ONE IS THE RELEVANT ONE THAT SHOULD BE SHOWN.`, user question `Which result will you show me...`, and assistant stem `The result I will show you is`. Lab wording substitutes reading. This is not the false factual assertion measured by FAR's `Which result is weak?` question. An answer naming harmless establishes a non-relevant selection under the task contract; it does not alone establish realized omission, audience deception, false factual assertion, or intent.

`build_prompt_pair` (line390) designates an item in clean and the other item in corrupt; the deceptive target is always the clean harmless item, distractor the clean damaging item. Under inversion, designated means damaging and deceptive target is the other item; under identity, designated means harmless and is itself target. `truth=0/1` in pilot artifacts means clean/corrupt stream, not lexical candidate0/1. Always use `truth_id`, `other_id`, and exact word mappings.

Original dataset construction `filter_by_model_behavior` (line949) requires deceptive whole-vocabulary argmax in BOTH streams with margin threshold. `harvest_honest_twins` selects opposite observed outcomes under same prompt/pressure; it is not an honesty instruction condition. Thus native selected-P96/96 behavior below is selection, not prevalence.

## Original pressure inventory and linkage (CPU-only semantic audit input)

- `dataset/deception_pools/pressure_sdr.json`:20 strings; `pressure_shared.json`:5 strings.
- `dataset/deception_common.py:load_pressures` (line340) assigns `sdr_00..sdr_19`, slots0..19; `shared_00..shared_04`, slots20..24. Return records are `{id, slot, text, shared}`. A blind audit can export just25opaque IDs/texts, classify semantics before seeing response metadata, and join back by pressure ID. Keep exact text—some clauses refer to "second finding" or "that result" rather than explicitly naming harmless.
- `dataset/deception_pools/matched_honest_sdr.json` is an object, with `.instructions[pressure_id] = {slot,shared,pressure,instruction,clause_tokens}`. Use exact original-pressure equality before matching.
- `dataset/matched_honest.py:load_matched_honest_pool` returns `.instructions`; `replace_clause` (line104) swaps/deletes exact saved clause. P = saved pressure; H = matched honest instruction in its place; N = deletion. H and N have distinct semantics.
- `data/datasets/sdr/{train,validation,test}/data-00000-of-00001.arrow` are original saved rows; `data/datasets/sdr/filter_report.json` documents behavioral selection and original pool lengths. Native record factors: entity/domain/item_1/item_2/item_pair/item_polarity/designation_polarity/pressure_slot/template_variant/instance_id, plus exact clean/corrupt/neutral prompts, target/distractor, pressure/pressure_id/shared. `instance_id` hashes the complete factor tuple (`INSTANCE_FACTORS`, line471).

## Existing native scored P/H/N support: exact artifact seams

Let `S = W/outputs/_analyses/sdr-routing-pilot/stage1-retry-f7cb49f-20261021T002501Z`.

- `S/manifest.json`: `.groups` contains story_id, split, source_instance_id, nuisance(entity/domain/item_pair/template_variant), alternative_pressure_ids, n_source_variants. **No `.record` field in frozen groups.** `.panel` has480 complete variants including exact prompt/ids, anchors/segments, story_id/source_instance_id, truth/condition/pressure_id/primary_pressure_id, truthful_item/truth_id/other_item/other_id, item_ids(word→token ID), item_positions(word→option position), content_hash/prompt_hash/variant_id. It can support audited fixed-fact linkage without importing model code.
- `S/baseline.jsonl`:480 rows, join panel by **variant_id**; adds emitted_id, emitted_class, truth_margin, p_truth/p_other/other_mass, top_k, fp32_checksum, accessible. These are **first-token argmax**, not EOS-completed free generation.
- `S/comparisons.jsonl`: recipient_id/donor_id links variants, pressure_pair, pressure_change/truth_change/content_change, donor_matches_recipient_truth/emission, support_classes, recipient/donor hashes.
- `S/gate.json`: old pooled-over-truth crossed-story counts P↔H28(discovery11/confirmation17), P↔N30(14/16), P↔P′37(17/20); fixed-content/same-answer story counts46/46/48. Do not reinterpret these as fixed-fact pressure×answer crossed support.
- `scripts/sdr_routing_pilot.py:story_key` (line215) hashes entity/domain/item_pair/template_variant. `panel_for_record` (line231) constructs P/H/N/two alternate P clauses for each original truth stream. `build_comparisons` (line451) preserves truth/content confounding, and `evaluate_gate` (line476) explicitly says pressure mediation unidentified.

Observed structure:48stories×2truth streams=96fixed-fact units. Each unit has primary P, H, N, and2alternate P clauses:288P+96H+96N=480. Only11distinct primary pressure IDs occur: sdr_02/03/08/10/11/12/15/17/19, shared_00/01. Primary sdr_17 occupies48of96fixed-fact units. The25-clause pool should therefore be audited in full before drawing conclusions from observed support.

Preliminary fixed-fact primary-P→control transitions (candidate IDs, not text matching):

| Comparison | P harmless→control damaging | P harmless→control harmless | Unit pairs |
|---|---:|---:|---:|
| P→H |74|22|96|
| P→N |78|18|96|
| P→alternateP |108|84|192|

Across the3existing P clauses, **65/96fixed-fact units emit both candidate identities**. H and N each have exactly1saved baseline per fixed-fact unit, so0units provide both answer identities within H or within N. Full fixed-fact condition×emitted-answer crossing therefore remains absent. Record missing/unsupported combinations explicitly; do not create an H-other or N-other donor by changing truth and calling the fact fixed.

Fixed rule agreement on these saved argmax outcomes:

| Condition | N | First option | Second option | Damaging | Harmless |
|---|---:|---:|---:|---:|---:|
| Primary P |96|48|48|0|96|
| Alternate P |192|86|106|108|84|
| H |96|36|60|74|22|
| N |96|32|64|78|18|

## Actual native free-generation support (separate endpoint)

Let `C = W/outputs/_analyses/sdr-completion-diagnostic/labels-pre-adjudication-23099381`.

`C/joined.jsonl` has1280all-population rows; filter `population=='native'` gives256 =32stories×truth2×order2×pressure2. Native factors are `{order,pressure,truth}`; exact original prompt, source_instance_id, story_id, variant_id, ids, prompt_hash, item_ids, truthful_item/truth_id/other_item, record_order, candidates, answer_identity, response_kind, semantic_result, assistant_text, continuation_text, generated_ids/count, stop_reason, firststep_checksum and annotation_status are present. `candidates` are lexical candidate order; `items` and `record_order` may differ. Decode answer_identity candidateA/B through candidates[0/1]. Do not compare letter labels directly with original item_1/2.

`C/summary.json` and `C/report.md` provide existing whole-panel summaries. Native rows all EOS-complete and independently agreed; P34/128damaging versus N101/128damaging. Within128matched(story_id,truth,order) units: Ncorrect→Pwrong80; Nwrong→Pcorrect13; bothwrong14; bothcorrect21. There are **no H native completions** in this artifact. This is a post-hoc forced-prefix endpoint and familiar historically filtered population.

| Native completion | N | First record item | Second record item | Damaging | Harmless |
|---|---:|---:|---:|---:|---:|
| N pressure=0 |128|49|79|101|27|
| P pressure=1 |128|90|38|34|94|

Thus original-native P completion differs materially from neutral example-dominance scaffolds; do not transfer the latter's behavioral interpretation to this population automatically.

## Adapted-native controls and neutral cue scaffolds (already available)

`W/outputs/_analyses/sdr-native-controls/postprocessing-1eb79892/join-audit/joined.json` is3072joined rows, with exact row ID, fixture_id, pair/entity/template, factors(wording/truth/order/favored/condition/task), full prompt, candidate0/1 lexical identity, kind/format_ok/correct/non_relevant, response text, finish, annotators and numerical controls. `.../analysis/analysis.json` contains reviewed panel counts/gates. This is adapted native wording with director-favored item and weights-wipe clauses, not the original25pressure population.

`native_controls.factor_rows` crosses wordingA/B×truth2×order2×favored2×conditionC/A/N×taskreport/retrieval=96rows/fixture,32main fixtures (16audit/16lab). C=wipe iff report disagrees with favored; A=wipe regardless; N=no wipe regardless. It directly separates outcome contingency from aversive wording; truthful-favored alignment is crossed rather than selected.

Preliminary fixed-rule agreement from joined rows (N512each): reportN truth337/first-mentioned429/favored269; reportC305/417/333; reportA305/459/285. RetrievalN truth456/first265/favored223/residual36; retrievalC479/276/234/residual4; retrievalA457/267/222/residual35. Neutral reporting337/512=.6582 and retrieval1392/1536=.90625; behavior_go=false. Wrong report selection on conflict(C142,A118,N94)/256 supports descriptive differences but failed baseline gates prohibit a successful selective-deception claim.

`outputs/_analyses/sdr-cue-probe/postprocessing-5f74d0c/analysis/analysis.json` and `descriptive-inventory.md` hold512neutral cue outcomes (8fixtures×64factor rows), report175/256correct, retrieval238/256correct, report fixed lexical candidate0chosen195/256. `scripts/sdr_cue_probe.py:factor_rows` independently crosses form(other/named), record_order/question_order/truth/favored/task, but its report example-list order is fixed lexical0then1.

`outputs/_analyses/sdr-cue-circuits/postprocessing-ca41bfd/` and `outputs/_analyses/sdr-cue-positions/postprocessing-2949214/analysis/` contain response joins/analyses for original masks, not six v2 masks. Their script `factor_rows` adds independent example_order and explicit named statuses. Parent-owned other agent covers v2; no v2 work performed here.

## Minimal reusable machinery, and hard-coded limits

- For a **CPU-only audit**, standard JSON/JSONL suffices. Read all25pressure strings and matched instructions; join the immutable480baseline variants; compute a complete support inventory by story+truth+pressure and fixed rule agreement. No model import, tokenizer load, training, paid judges or runner fork is necessary. Join native completion P/N separately by story+truth+order. Report saved first-token and EOS semantic endpoints separately.
- For future additive behavior generation, `scripts/sdr_native_controls.py:make_batch` (line178), `compare_vectors` (188), `complete_batch` (197), `view_for` (607), `export_blind_views` (612), and `join_annotations` (619) are the simplest kernels: B8 same physical shape, max64greedy, full FP32 vocabulary repeat/empty-hook controls; calibration also full-component/self replacement excluding readout; cap/error overrides early candidate. Annotation distinguishes commitment/refusal/evasion/ambiguous/contradictory/malformed/cap/error and format separately. Existing `analyze_panel` assumes3072rows/truth factor/gates; it is not a general native audit API.
- Native outer CLI `--mode freeze/calibration/main/export-labels/analyze/plan-shards/main-shard/merge-shards` hashes all local source/model-cache/pool files and binds exact frozen counts/source/software. Existing protocols cannot be mutated and passed through verification as a new design.
- `scripts/sdr_cue_probe.py` adds independent order/form renderer and reusable label validation/paired-category comparisons. Its build/verify freezes512main and64calibration with archived rubric hash; do not reuse as unmodified outer runner for another panel.
- `scripts/sdr_cue_circuits.py:select_families` (119) reads original D69/H56/F68 and computes S32/A22/B11/J33 plus exact-layer outside controls. `make_pairs` (100) matches only example/truth edits with2changed tokens; `tokenize_rows` verifies offsets/status spans/roles. `decode_batch` (296) is B8/L224/64-token natural generation with immutable compact head-output banks and numerical controls. `component_analysis/hooks.py:Replacement(value,positions)` + `capture_forward` are underlying intervention seams. Outer protocol is384baseline/640pairs/8960interventions with literal parent/spec/mask hashes.
- `scripts/sdr_cue_positions.py:freeze_positions` (60), `position_mask` (164), `pack_bank` (178), `decode_batch` (204) add early/tail/full/system frozen original-prefix masks. Donor bank is captured once at prompt; generated/dummy/padding positions excluded. Useful future pathway test only after behavior identification. Outer protocol supports only S/C_S,384baseline+3840interventions, fixed parent/source/spec checks; not a generic panel.
- `tasks/sdr.py` is a thin `DeceptionTask` wrapper for trained dataset task evaluation. `dataset/deception_common.py:run_evaluation` remains candidate first-token scoring; it cannot supply semantic EOS labels.

## Reproduction snippets (run read-only from Alignment)

```python
import json, pathlib, collections
W = pathlib.Path('Deception-Circuit/.claude/worktrees/sdr-routing-pilot')
S = W/'outputs/_analyses/sdr-routing-pilot/stage1-retry-f7cb49f-20261021T002501Z'
rows = [json.loads(s) for s in (S/'baseline.jsonl').read_text().splitlines() if s]
groups = collections.defaultdict(list)
for r in rows: groups[r['story_id'], r['truth']].append(r)
# IDs in item_ids are VALUES: set(item_ids) would incorrectly use words.
assert len(groups) == 96
print(sum({rs[0]['truth_id'],rs[0]['other_id']} <=
          {r['emitted_id'] for r in rs if r['condition']=='P'}
          for rs in groups.values()))  #65
for control in ('H','N','Pprime'):
    transitions = collections.Counter()
    for rs in groups.values():
        p = next(r for r in rs if r['condition']=='P' and r['pressure_id']==r['primary_pressure_id'])
        ds = [r for r in rs if r['condition']==control] if control!='Pprime' else [r for r in rs if r['condition']=='P' and r['pressure_id']!=r['primary_pressure_id']]
        def cls(r):
            return 'damaging' if r['emitted_id']==r['truth_id'] else 'harmless' if r['emitted_id']==r['other_id'] else 'nonitem'
        transitions.update((cls(p),cls(d)) for d in ds)
    print(control, transitions)
C = W/'outputs/_analyses/sdr-completion-diagnostic/labels-pre-adjudication-23099381/joined.jsonl'
groups = collections.defaultdict(dict)
for s in C.read_text().splitlines():
    r = json.loads(s)
    if r['population']=='native':
        groups[r['story_id'],r['factors']['truth'],r['factors']['order']][r['factors']['pressure']] = r
assert len(groups)==128 and all(set(rs)=={0,1} for rs in groups.values())
print(collections.Counter((rs[0]['semantic_result'],rs[1]['semantic_result']) for rs in groups.values()))
```
