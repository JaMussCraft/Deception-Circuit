# Independent prospective cue manifest oracle

2026-10-21. Lead compactions4. Owned audit artifacts only; no production edits, git, models, inference, jobs, ledgers or notebook execution. This is an independent CPU/tokenizer audit, not a scientific result or model release.

Authoritative science: `.scratch/sdr-cue-probe/spec.md`. Parent: worktree `Deception-Circuit/.claude/worktrees/sdr-routing-pilot/.superpowers/sdd/plan-sdr-native-controls/sharding-freeze-final-1eb79892/protocol.json`, source `1eb79892b0c4a428774cf340350d2297d9ec58f7`; parent file SHA256 `1196d1569aa53ee1d37419c52b27d9fec4127f146def6e91e44fe5faf4e52914`, scientific hash `52f3860915bd0843dbcb503d856d034659add37458863dd3c3f5ece75b3bf620`.

`manifest-oracle.py` independently reconstructs expected rows from this parent and the spec's literal grammar. It never imports the new cue renderer or any old renderer, never loads model weights, and reads no response/generation/label files. The only ML object is the cached local AutoTokenizer. Frozen parent main rows are used only to verify a literal prompt bridge after fixture selection; old outcomes never enter selection.

`manifest-audit.json` stores the complete expected scientific core,512 expected main rows,64 selected calibration rows, exact render/token fields and independent hashes. This is an oracle core schema, not a demand that implementation use the same outer payload schema. Implementer declared row schema matches the oracle's execution_rank field and all required literal/token fields. Implementation's fixtures alias contains eight main plus two cal; the oracle stores those lists separately for explicit selection auditing.

## Selection and crossing

Choose first four per template from frozen main execution ranks, then execute combined rank order:

| Rank | Fixture | Template | Pair |
| --- | --- | --- | --- |
| 0 | nc-afa6c76d06448473 | lab | hearing / vision |
| 1 | nc-c5f0b2f5f348543e | lab | roles / users |
| 2 | nc-8121f8603d662dcf | lab | beams / joints |
| 3 | nc-fc55cb97246d1634 | lab | intake / output |
| 4 | nc-7364876512c7d4a8 | audit | bonds / stocks |
| 9 | nc-1c66593d98bda82c | audit | button / switch |
| 11 | nc-c8f3b58353fe5dab | audit | density / hardness |
| 12 | nc-d33131117297333a | audit | blinds / lights |

All512 factor rows are present in exact fixture/form/record_order/question_order/truth/favored/task nesting. Pair IDs are lexical and fixed. The two original additional calibration fixtures remain audit rank32 then lab rank33, disjoint from all original main pairs. Calibration independently ranks each complete64-factor candidate set by SHA256(canonical JSON `["sdr-cue-calibration",20261021,fixture_id,factors]`), tie-break canonical factors, selecting32/fixture. Each selected set must contain both values of all six factors.

## Prospective assertions

The independent oracle checks parent main/fixtures/calibration top-level aliases against payload plus parent scientific/provenance hashes. It reconstructs both template literals, replacing exactly the second reference for named form, preserves `.THE`, fixed neutral wordingA clause/favored mention/norm, manual shell and both old stems. It parses rendered first/other or named predicates to recover actual damaging identity independently of stored truth_name. It verifies report examples remain lexical across every cell, question reversal changes only the interrogative options, both tasks share system text, and named form changes only `and the other ` to `and the {second} {noun} `.

Offline tokenization uses cached local Llama tokenizer with add_special_tokens=False. All512 main plus all128 possible calibration prefixes—not only selected64—must fit224 with64 generation positions. Config and generation-config EOS values must both equal `[128001,128008,128009]`. Both main/cal tokens and leading-space candidate continuation token IDs are stored exactly.

The frozen old prompt bridge uses other form and question_order==record_order:96 main rows must byte-match old native N/A prompts;32 more differ only by the now-fixed lexical quoted answer-example order. This bridge is a construction check, not outcome reuse. Rubric source must match frozen archived brief SHA256 `930f7f081060262f179dc3a4d030e21b15a8b710e629fbead76c6bf7ceda6185`.

## Status

Independent expected oracle: **PASS**. Maximum prefix across main+all calibration candidates is131 tokens; minimum main/selected-cal prefix is110. All prefixes+64 fit fixed224; maximum195. Semantic/factor/selection/tokenization/EOS/rubric/bridge checks pass. This establishes expected bytes only. New provisional implementation freeze is not yet available. No claim about new source/protocol correctness, source hash binding, GPU numerical controls or calibration readiness follows from the expected oracle alone. When the implementer produces a freeze, compare complete row dictionaries/token IDs/ordering, all fixture aliases and scientific/provenance hashes; verify all listed source/import hashes against current bytes and new source files included. Final committed freeze must preserve the complete provisional scientific payload and differ only in the expected provenance commit binding.

Expected row dictionaries now use the implementer's declared `execution_rank` key. Stable independent hashes: canonical main-row list `21d0fc063e0b35e8cc341611079934ac13744330f7b03b026a0c869b2c790105`; canonical selected calibration-row list `9f7e00a734d216724f661aa85c53fd77920d77e96fefd7258c22db9934e2c7b6`. All six cached JSON files (config, generation config, weight-index metadata, special-token map, tokenizer and tokenizer config) independently match the parent's bound hashes. No weight tensor data was loaded or hashed for this tokenizer audit. Implementation comparison remains pending its provisional freeze.

## Actual provisional freeze comparison — lead compactions5

The implementer supplied actual mgnp-wrapper CPU freeze at `Deception-Circuit/.claude/worktrees/sdr-routing-pilot/.superpowers/sdd/plan-sdr-cue-probe/freeze-provisional/protocol.json`, declared scientific hash `9f13e56da0678f289616aba6eaf853d936c042b82a8b55d53db420279ddd95e8`. Independent `manifest-compare.py` compares this artifact against the previously saved expected oracle, not the implementation renderer. It additionally reconstructs the complete outer scientific payload schema from expected rows and frozen spec/rubric bytes, rehashes the complete exact source/import set and every cached model/tokenizer file, and checks actual mgnp package metadata. File hashing reads weight bytes without loading tensor/model objects. This new comparison receipt appends to `manifest-audit.json`, preserving expected core and prior records. The frozen spec's historical count4 is retained; current lead count5 is audit metadata only.

**Provisional actual-freeze verdict: PASS, no findings.** All512 main and64 calibration **complete row dictionaries, string/token bytes and execution ordering** equal the independent oracle exactly. All ten fixture identities/ranks/order and top-level aliases match. The complete reconstructed expected scientific payload equals the actual payload, including its spec/rubric source bytes, and independently produces science hash `9f13e56da0678f289616aba6eaf853d936c042b82a8b55d53db420279ddd95e8`. All54 source/import hashes match current bytes and all three new-file hashes match the root's locked values. Actual mgnp package identities match provenance. All10 cached model/tokenizer/config files were independently streamed and SHA256-rehashed (16,069,722,669 bytes); they match both this new binding and the immutable parent binding.

Provisional protocol file SHA256 `9c0e9fa96e3b943d7cb934e9a05d207993178bd6f6d0a11f1dcc2d3a8d8e227c`; provenance hash `285fdaee72abc662d3759aa6ad524fd15694284ca1430b0cd1f255657f0392ca`. Provenance deliberately says `UNCOMMITTED`: this is CPU science/source/cache consistency PASS, not final GPU release. Root must commit and rebind; independent final follow-up should prove complete payload equality and only code_commit provenance change, plus committed-source byte equality. No GPU numerical/calibration/behavioral outcome is asserted.

## Final committed rebind audit — lead compactions5

Root supplied new commit `5f74d0c3653a63c411997e0f666a79171076a8d8`; final actual-wrapper CPU freeze destination `.superpowers/sdd/plan-sdr-cue-probe/freeze-final-5f74d0c/protocol.json`. This follow-up preserves the complete expected oracle and provisional PASS history. Final closure requires exact payload/row equality to provisional, unchanged frozen spec/rubric,54-source and cache/software equality, only code_commit provenance change, and read-only evidence that the reviewed new-file bytes belong to the supplied commit. Root/operator separately own final actual-wrapper dry-run and model release.

**Final committed freeze verdict: PASS, no findings.** Artifact `.superpowers/sdd/plan-sdr-cue-probe/freeze-final-5f74d0c/protocol.json` is bound to actual commit `5f74d0c3653a63c411997e0f666a79171076a8d8`. The complete scientific payload is unchanged from provisional and independently equals the oracle-backed reconstruction; all512main/64cal complete row dictionaries, literal/token bytes, ordering and ten fixture aliases match. Only `code_commit` changed in provenance. All54 source/import hashes, three root-locked source hashes, actual mgnp software identities, frozen spec/rubric/parent bindings and all10 cached file hashes match. The cache comparison independently streamed all16,069,722,669bytes again; no model was loaded.

Read-only commit evidence proves the commit changes exactly the three reviewed additive paths and each committed blob equals reviewed/current bytes. Final protocol file SHA256 `a6f968660f2cd072dc1589591d532143440356f49c50fd17c8b9b5166c56e915`; scientific hash `9f13e56da0678f289616aba6eaf853d936c042b82a8b55d53db420279ddd95e8`; final provenance hash `e3e041af1f6c5f0353ce4760676e44e47fbeaa16f372bd2d61b87f1b90d75fdb`. Full final receipt is appended in `manifest-audit.json` under comparisons; prior expected oracle/provisional receipts remain preserved. This closes independent CPU final-source/science/cache provenance verification. Operator actual-wrapper final dry-run and root calibration release are separate; no GPU numerical or behavioral result is asserted. Current lead compactions5; frozen spec's historical4 remains unchanged.
