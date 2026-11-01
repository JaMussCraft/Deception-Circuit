# Independent provisional input-freeze review

2026-10-26. **PASS for provisional scientific inputs. No discrepancies found.** This is not a final source/cache closure review, GPU-release decision, runtime approval or outcome analysis.

Reviewed exact `implementation/protocol-provisional-v2.json`:

- File SHA256: `c320f8d3c7c6e1502cdb8109c5f2126f7581b81de983aa7ad3a8830abecb4c58`.
- Scientific payload hash: `1a29813fea112f713b66a673619afa25687a70527d832323159c92e9c4364412`.
- Provisional manifest hash: `2278cf2c75fdbf99db387c56440f0495e83b8a9ee7d5660f078812924674b0a8`.

The read-only standalone [checker](check_input_freeze.py) completed **2,797 direct-source checks** and wrote [input-freeze-receipt.json](input-freeze-receipt.json). It imports only the independent oracle and standard library, not study code. Canonical hash recomputation uses sorted compact UTF8 JSON with `ensure_ascii=False,allow_nan=False`, matching the existing general serializer. No model, notebook, job, actual outcome or implementation analysis algorithm was read/executed.

## Independently verified

| Item | Result |
|---|---|
| Main selection | Exact24historical-confirmation stories;96unique original primary-P/N/both-truth variant IDs. Input metadata alone defines the panel. |
| Original input fidelity | All original parent fields match for all100main+calibration inputs, including literal prompts, saved token IDs, truth/other IDs and names, anchors, semantic spans, source IDs and historical split. Added stem/query fields equal original anchor text with only shell newlines removed; lexical candidate pair is sorted exact saved names. |
| Main pairs | Exact192within-story directed pairs, eight/story; direction/axis independently derived from conditions/truth values. Four clause and four fact directions remain separate. |
| Common maps | All200main+calibration maps equal exact saved parent maps. Independently rebuilt from named spans/exact token identities with readout precedence and one-to-one collision handling; all recipient/donor coordinates within their respective original prefixes. |
| Arms/families | All20source/bank/receiver definitions and footprints match ratified spec. U5 is exact five pre-L17 heads, H26 is same-layer singleton, U6 equals original candidate6, S32 equals frozen parent shared32 and family hash. |
| GQA | Cached config independently confirms32query heads/8KV groups, hidden4096/32layers/vocab128256. K6/V6 footprints H24–27; Q24/head24 remain single-head; quartet explicit24–27. Mask files independently confirm K0's H0–3 outside D∪H∪F. |
| Scientific schedule | Exactly96baseline+192×20=3,936unique rows,492B8batches, no missing/duplicate rows; each arm-row ID maps to its stated pair/arm. |
| Calibration | Lexicographically first discovery story, four original P/Ninputs, eight directed pairs, disjoint from main.21natural batches give164outcomes (4baseline+160interventions); forced64arms10/18 add16, total180excluded calibration outcomes. |
| Physical geometry | B8/L224/cap64, BF16/SDPA/cacheFalse. Max original prefix118, so cap fits without truncation. Cached config/generation EOS union exactly128001/128008/128009. |
| Semantic binding | Exact full96row input-only semantic artifact and SHA69767203…ee; six strict-defined Pinputs, all others retained with null reasons. N current pressure remains null rather than inheriting a Ptarget. |
| Rubric/spec binding | Both embedded full texts equal current files and match declared SHA. Rubricba22cf76…a3 and spec7675b065…52; strict caps/eight annotation kinds are bound. Historical parent/source/mask hash dictionaries retained exactly. |
| Numerical/bootstrap pins | Payload seed20261026/reps2000/tolerance1e−5; full embedded ratified spec binds exact argmax/full-clean-token identity and stdlibRandom/shared sorted24story draws/linear-percentile rule. Execution of analysis/bootstrap was intentionally not inspected. |

## Prefix masks and induced banks

Bounded source inspection used immutable `implementation/review-source/sdr_shared_composition.py` SHA `e3265dc5800a1ecd7f68d97b32bbf3c183edce180c328385e757e950d3e4026f`, restricted to receiver definitions, input/freeze construction, `pack_bank`, setup/arm composition, decoder and forced-batch scheduling. The analysis functions were not read. Existing `sdr_cue_circuits.prefix_positions` was inspected separately.

Source masks contain exactly mapped recipient coordinates, with donor values read at the corresponding donor coordinates; unmapped values are not written. Receiver masks are all original nonpadding recipient prefix positions. The prefix helper starts with false8×224, then marks real rows up to saved prefix length, leaving dummy/padded/generated coordinates false. Decoder checks each key's mask is a subset of that immutable original prefix and preserves independent per-key masks. The induced bank captures receiver values from a recipient pass with U5source replacement alone; all other components remain free. Rescue uses that recipient-coordinate bank without another donor remap. No old full-freeze direct-edge helper is invoked in this setup.

This source-level check establishes the intended construction, not empirical hook assignment correctness or numerical invariance. Tiny-model, live calibration and final runtime audits remain responsible for those checks. No new attention trace/helper is part of the science payload.

## Final-binding requirement

The provisional provenance explicitly says `code_commit=UNCOMMITTED,provisional=true`. Root reported code-review fixes may change source before commit. After those fixes, root must produce the final committed-source/cache binding and either retain scientific hash **1a29813f…4412** or expose an explicit payload diff for scientific recheck. This review makes no claim that final closure or GPU release has occurred. Changes only to source/provenance should change the manifest hash while retaining the reviewed scientific payload.
