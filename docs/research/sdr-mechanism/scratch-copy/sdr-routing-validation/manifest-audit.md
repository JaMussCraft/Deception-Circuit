# Independent pre-inference manifest semantic/data audit

2026-10-21. **PASS for frozen prompts, data exclusions, factorial selection and maps. No must-fix semantic/data error identified.** One pressure-boundary annotation caution below should be handled before summaries. This is not a code-identity, hook-execution, model-validity or inference approval review: code hashes are known stale while implementation tests are refined. Regenerate/pin the final execution manifest separately.

Audited file: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot/outputs/_analyses/sdr-routing-validation/task1-cpu-review-v1/manifest.json`.

- SHA256 exact file bytes: `2da1046a10e880eaf088a2e83f80458cc552dd52b13f80ecbd1f4d4f2e47e274`.
- Recorded manifest hash: `925b028b64f1f2d37c35bcc4987f3183d60aa92cf60949851e2ebd2cf3fc1ad6`.
- Independent methods: direct JSON/content comparisons; full legacy D/H/N Arrow reads; source-ID resolution; tokenizer.json encoding via local tokenizers library only; factor/donor/map/split arithmetic. No model, GPU, notebook, job or code edits.

## Data and selection

Independently reconstructed the historical sets from all nine legacy D/H/N Arrow sources, old25component `sample.json` files, original pilot manifest and selective-v3SDRsource manifest. Exact equality with recorded historical sets:

| Set | Independently verified count |
|---|---:|
| Old component top-level IDs |239 |
| Expanded component story composites |227 |
| All D/H/Ntrain/validation story composites |609 |
| Combined native excluded composites |827 |
| Remaining native test source rows /stories |394 /318 |

All239IDs resolve without composite ambiguity;139areDtest and100Htest, with86DIDs also in Ntest. Every selected native source avoids the conservative exclusion union. Every fresh fixture avoids all1406stored D/H/Ncomposites. The fresh and native panels therefore implement the accepted exclusion policy; the old139-ID-only source field was not mistaken for complete exposure coverage.

There are96selected groups:64fresh and32native. Fresh has16groups in each templateA/B×exploration/confirmation cell. Record/option order is8/8within each such cell (16/16per template overall), fixed within each fixture. All16fresh factor combinations occur exactly once per group; all8native combinations occur exactly once. Native has16groups/split, with exploration10audit/6lab and confirmation13audit/3lab; template balance was not mandated for that bridge. All1,280variant IDs and prompt hashes are unique; all3,584directed pair IDs are unique.

Fresh lexical counts match manifest:37entities,35item pairs; **zero item-pair split overlap**,13entities appear in both splits. Related item-pair bundles do not cross splits; entity overlap is a declared limitation, not independent lexical generalization. Eight domains are represented (construction13,logistics12,manufacturing10,facilities8,consumerhardware6,enterprise software5,finance5,healthcare5fixtures). These are conditional synthetic fixtures, not a random natural-language sample. Native pressures remain concentrated:21/32sdr_17,4sdr_19,2sdr_02,2sdr_03,1eachsdr_11/sdr_18/shared_01.

## Prompts and factors

Compared every fresh prompt's task, favored, stakes, record, question and assistant-stem literal content with the frozen specification. No mismatches. Task context/favored/stakes precede the factual record. Both reporting and retrieval ask for the damaged unit. Correct-answer item/ID equals independently derived damaged-unit truth in all fresh and native variants; favored item/ID remains distinct metadata.

Fresh truth changes preserve named-record order and exchange damaged/intact predicates only. Each Tdonor differs from recipient only in the record span; Sdonors only in the exact fixed/conditional bonus span; Fdonors only in the favored span. The remaining prompt bytes match after removing the intended changed anchor. Every fresh donor pair flips exactly its declared single factor, holds all others fixed, and stays in the same story/split. Fresh directed counts are512per direction per S/T/Faxis (3,072total).

Native truth was independently parsed from actual designation predicates and named identity rather than target metadata. All retain the generic `THE DAMAGING ONE IS THE RELEVANT ONE THAT SHOULD BE SHOWN.` suffix. Intro and question/option orders reverse coherently while factual-record text and truthful identity remain unchanged. Pdonors are literal clause insertion/deletion, with all remaining prompt bytes equal; stored truth-deleting `neutral_prompt` is not substituted. Native directed counts are128per direction per P/Taxis (512total). Native order0/1each has128variants.

## Tokenization and comparable intervention support

Using the actual local cached tokenizer.json, every one of1,280prompt encodings exactly reproduces the saved token vector. For both item names in every variant, encoding actual `prompt + space + item` equals the saved prompt tokens plus **exactly one saved answer token**; there are no conflicting/non-single-token continuations. Fresh lengths80–98, native100–115, all below192; saved length equals actual token count. This is tokenization-only evidence, not intact-model capability.

For all3,584maps independently checked logical nonpadding bounds, injectivity on recipient and donor positions, exact token equality and matching named-role/offset identity. No failures. Every recipient's common-position set is identical across all its S/T/F(or nativeP/T)donors. Fresh corresponding reporting/retrieval rows have exactly equal primary semantic-role support. Readout maps are exactly recipient-final→donor-final tokens in every pair. Common roles exclude changed stakes/favored/record predicates/task clauses, rather than stretching or copying their indices.

Fresh common support has13–21role-token positions/variant, so it does **not** collapse to only readout. It includes stable record-prefix/item tokens, question named-item tokens and stem/readout; factual-record positions occur after stakes and can structurally receive that context. Native common support has78–81positions, including early intro/suffix positions before pressure as well as later question/stem. Those early native positions cannot encode a later pressure change in a causal decoder; they remain permissible content-transfer positions, not evidence of early pressure representation.

Grid matches frozen recipe: outside senderL13H14 is declared;9common links on3,584pairs=32,256path rows,4readout links on3,072fresh pairs=12,288rows, mandatory ordinary four-sender union on1,280stakes/pressure flips, totaling45,824scientific rows. Receiver replay is all192positions, distinct from sender support. No optional or outcome-selected link is added by the manifest. This audit verifies declarations/maps, not runtime freeze correctness or numerics.

## Pressure-boundary annotation caution

`structurally_inaccessible_before_pressure` often lists all mapped positions for nativeP0recipients, where the clause was deleted and has no actual boundary (e.g.79positions versus33in a correspondingP1row). This is not an intervention-map failure. However an absent boundary must be labeled absent/NA or interpreted using a separately declared source-pressure insertion boundary; **do not report every P0mapped position as causally unable to access pressure**. For explicit causal-order summaries use the actual P1anchor/source-location audit and named roles. This caution was sent to the implementer and lead; it does not require changing prompts, selections or pair counts.

Proceed to final code/manifest binding and the fixed baseline capability/numerical gate after this scoped audit. No headroom, pressure effect, role, intent or transfer efficacy is established by a CPU manifest. Lead compactions1.
