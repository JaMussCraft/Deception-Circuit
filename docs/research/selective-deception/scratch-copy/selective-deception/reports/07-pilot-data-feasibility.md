# Stage 2 pilot: structural data feasibility

CPU-only audit, 2026-10-18. **122 train pairs and 126 validation pairs are structurally usable with one representative per semantic cluster and deterministic, nonself instructed-H clean donors.** Every retained pair passes the existing helper’s full token-alignment preflight. Actual clean D/H recipient and donor endpoints have zero exact cross-split overlaps. An eight-stratum balanced pilot is **not** supported: train has no inversion/item-1/lab cluster and only one inversion/item-2/lab cluster. This audit does not silently rebalance, regenerate, freeze training settings, or claim that instructed-H is behaviorally valid.

Source data: primary `Deception-Circuit/data/datasets/sdr/{train,validation,test}` only. Construction/alignment: worktree `evaluation/selective_diagnostics.py` and `dataset/matched_honest.py`; neither was modified. Read-only Arrow loading, cached tokenizer and saved circuit-mask resolution were used. No weights, model forwards, GPUs, jobs, APIs, downloads, notebooks, outcome sidecars, or model-result selection were used. Only this report is written inside the project; temporary audit script/output live under `/tmp/selective_pilot_feasibility*`. Existing source data were historically outcome-selected, so these are exploratory conditional pilot inputs.

## Frozen structural rule and denominators

A cluster is exactly `content_hash({entity: record["entity"], items: sorted([item_1,item_2]), honest_item: record["distractor"]})`, matching `_scenario`. Before instructed-H construction, reserve every cluster found anywhere in original test; then reserve original validation clusters against train, even if that validation record would later fail structural preflight. Never move records between splits. Precedence is test > validation > train.

| Step | Train records / clusters | Validation records / clusters |
|---|---:|---:|
| Original | 200 / 192 | 200 / 183 |
| After higher-priority cluster exclusions | 127 / 122 | 133 / 126 |
| After instructed-H / all-view preflight | 127 / 122 | 133 / 126 |
| One helper-rule representative per cluster | 122 / 122 | 126 / 126 |
| After nonself donor compatibility | **122 / 122** | **126 / 126** |

Train excludes 73 source records: 59 overlapping test only, 8 overlapping validation only, and 6 overlapping both. Validation excludes 67 source records overlapping test. Test remains 1,000 records / 808 clusters. The raw cluster overlaps are 14 train–validation, 62 train–test and 57 validation–test; these count distinct clusters, whereas exclusion totals count source records. Within the remaining split, 5 train and 7 validation extra wrapper records are omitted by the one-representative rule, not by an outcome filter.

Representative rule is exactly the helper’s `build_manifest` loop: iterate grouped clusters in ascending cluster hash; choose `min(members, key=(count_already_selected_in_this_stratum, source_id))`; increment the selected stratum count. The stratum is `[designation_polarity,item_polarity,template_variant]`. All members within a cluster share its fact scenario, so wrapper selection is structural. This audit retains every donor-compatible representative rather than calling the diagnostic’s 64-cluster sample selector.

## Exact identity and prompt overlap

Counts below are distinct exact text strings, not the number of matching record pairs. All three raw split pairs have **zero overlapping instance IDs**, zero same-clean-stream prompt strings and zero same-corrupt-stream prompt strings.

| Raw split pair | Semantic clusters shared | Prompt strings shared across any clean/corrupt roles |
|---|---:|---:|
| train / validation | 14 | 20 |
| train / test | 62 | 86 |
| validation / test | 57 | 66 |

After precedence and representative selection, actual pilot endpoints are clean D recipients, clean instructed-H recipients, and nonself clean instructed-H donors drawn from the same retained split. Donors are a permutation of these H endpoints and add no new source records. Exact clean D/H endpoint overlaps are:

- `train|validation_original_clean_D_H`: **0**.
- `train|validation_all_views_clean_D_H`: **0**.
- `train|test_clean_D_H_original`: **0**.
- `train|test_clean_D_H_all_views`: **0**.
- `validation|test_clean_D_H_original`: **0**.
- `validation|test_clean_D_H_all_views`: **0**.
- `all_remaining_records_train|validation_original_clean_D_H`: **0**.

The all-view checks include original, reversed, free-response and alternative views. The test H texts used in this comparison are literal structural clause replacements on every original test clean prompt; no test H survivor list or outputs are involved. Semantic-cluster overlaps among the retained train, validation and all original test clean scenarios are zero by construction.

A broader audit that also includes historical **corrupt** streams still finds 64 shared derived prompt strings between retained train/validation, and 58 train / 40 validation derived strings matching an original test clean-or-corrupt prompt. Swapping the designated item can invert the fact truth used in `_scenario`, so honest-item clustering does not make every counterfactual stream globally text-disjoint. These counts do not require extra exclusions for a pilot that exclusively uses clean endpoints. Reusing native corrupted streams would require a new explicit overlap policy; do not silently substitute them for the frozen nonself H donor.

## Phrase coverage and alignment

Every original record has a pool entry: 200/200 train, 200/200 validation, 1,000/1,000 test. Missing pressure IDs: none. On the post-precedence records, missing phrases, clause mismatches, label-token failures, designation-label contradictions, clause-boundary token drift, readout shifts, item-swap alignment failures, unsupported historical templates, context overflows and unequal view lengths all occur **zero** times. This conclusion is obtained from `_preflight(record,pool,cached_tokenizer,512,96)` on all 127/133 remaining records. Each instructed pair is also checked by `instructed_counterpart(...,128)`; no truncation occurs.

Alignment signatures are helper `_signature`: `(original,reversed,free_response,alternative)` token lengths for H-clean. The helper additionally checks D/H and clean/corrupt lengths agree within every view.

| Length signature | Train clusters | Validation clusters |
|---|---:|---:|
| (113, 113, 90, 95) | 21 | 24 |
| (114, 114, 91, 96) | 63 | 55 |
| (115, 115, 92, 97) | 31 | 40 |
| (116, 116, 93, 98) | 3 | 2 |
| (117, 117, 94, 99) | 4 | 5 |

All five groups have at least two clusters in both splits. Original/readout scoring prompts are 113–117 tokens under the existing 128-token bound; free-response and alternative prompts are shorter. There are zero singleton-length exclusions.

## Strata and deterministic donors

| Designation / item / template | Train original | Train eligible | Validation original | Validation eligible |
|---|---:|---:|---:|---:|
| identity / 1 / audit | 42 | 25 | 49 | 21 |
| identity / 1 / lab | 20 | 14 | 18 | 14 |
| identity / 2 / audit | 39 | 16 | 36 | 24 |
| identity / 2 / lab | 16 | 11 | 15 | 12 |
| inversion / 1 / audit | 37 | 25 | 37 | 25 |
| inversion / 1 / lab | 2 | 0 | 4 | 4 |
| inversion / 2 / audit | 43 | 30 | 37 | 23 |
| inversion / 2 / lab | 1 | 1 | 4 | 3 |

All eight strata exist originally, but both original inversion/item-1/lab training records are removed by precedence: `8f5d830872a1` overlaps both test and validation, while `90130e39ed06` overlaps validation only. The remaining eligible train distribution covers seven strata; validation covers all eight. Audit templates dominate and the rare lab inversion cells are too small for a balanced eight-cell conclusion. Counts are reported as observed; no stratum is resampled or recreated.

For a reproducible donor assignment, sort the final representatives by ascending cluster hash, group them by `_signature`, and call helper `_derangement`: within each group rotate IDs by one (`ids -> ids[1:]+ids[:1]`). For each recipient use that assigned cluster’s H-clean endpoint for both its D and H twin and for every learned/comparator mask. This rotation is outcome-independent. All 122 train / 126 validation donors have different source IDs, different semantic clusters, unequal prompt text, equal token length and identical unpadded all-one attention masks to both twins in all four views. Every eligible cluster is used once as donor within its split. Donor reuse across D/H is intentional; self-H preservation is excluded.

| Donor’s intended honest answer equals recipient… | Train | Validation |
|---|---:|---:|
| D deceptive-label word | 6 | 5 |
| H truthful-label word | 7 | 6 |
| neither label word | 109 | 115 |

These are exact answer-word relationships, not donor predictions: the donor’s intended answer is its own source’s H truth label. The same relationship count applies to both recipient twins. Most donors introduce an unrelated answer word (109/122 train, 115/126 validation), so this remains a content-mismatch interchange stress test with an answer-copying limitation. Intact donor correctness and recipient H-capable counts remain unmeasured; token alignment does not establish either.

## Candidate restriction and feasibility decision

The existing CPU circuit resolver, with unchanged default D/H/F/m bindings, resolves `candidate=(D|H|F)-m` at leaf granularity to **103 heads out of 1,024**, across 15 layers, with zero MLP-hidden/output membership. Head counts by layer: L4: 2, L5: 6, L7: 8, L8: 8, L9: 8, L10: 5, L11: 6, L12: 12, L13: 13, L14: 11, L15: 5, L17: 5, L18: 4, L24: 5, L30: 5. The resolver also represents subordinate head dimensions/attention blocks; the pilot search parameters should still be precisely the 103 eligible per-head logits, not those extra structural entries.

A bounded unbalanced exploratory pilot is structurally implementable on 122/126 independent-cluster D/H pairs, with exact clean-endpoint split isolation and no alignment/donor shortage. A balanced eight-stratum pilot is blocked by the missing training cell; that is a scientific coverage limitation, not a tokenizer issue. No behavioral validity gate is resolved here: root must still assess intact H truth performance/capable strata, intact donor behavior, generation quality and timed resource cost before fitting. This report neither authorizes a launch nor fixes optimization settings or changes the dataset.

## Reproduction identities

- `helper_sha256`: `2c7c3d8f5714d316bedba21a13307956ed722510116143d9bfc61ce06383d127`
- `pool_sha256`: `472d57b17c3b3760afd9ac72ad7e04717c49a4324a7c868f7b90199868ca1ab5`
- `tokenizer_revision`: `0e9e39f249a16976918f6564b8830bc894c89659`
- `tokenizer.json` SHA256: `79e3e522635f3171300913bb421464a87de6222182a0570b9b2ccba2a964b2b4`
- `tokenizer_config.json` SHA256: `177c7b61e616fecb84c17ce0591acb92c6c4d60e9ac5ababfb940ff23bbcd424`
- Original `train` records canonical content hash: `367f085ac8f78a0859c149341c86bdb02a89d94477fcfd7ed4e893a5290038fb`
- Original `validation` records canonical content hash: `9ed20db8b4b4472af5ab5db7809ad1c50ee96c712a1fe7de0a9b62a21501c625`
- Original `test` records canonical content hash: `7e484a467836d6e997e7b524fba58d02f9fb112c15668c03bb24957609b06c2f`
- `train` donor-assignment canonical hash: `bcaa6582aef865e4553cdc94c702c1aa15f9663bb05c78fd1512b4dc4c37878e`
- `train` clean D/H all-view prompt-hash mapping canonical hash: `72b0e27ae7253110724c3862e3a920e75f6843be81b1b9f34f61cbe836ce8db4`
- `validation` donor-assignment canonical hash: `eb6a2ac473d323113ea75b939ae3a755bf429cc8fea07f06c45b6e3029836773`
- `validation` clean D/H all-view prompt-hash mapping canonical hash: `90707d87756e113b802e010cb0d2d075c4aa0319ba9655a231828dfe36a4d886`

Canonical hashes use the helper’s sorted-key, compact UTF-8 JSON convention. Original record hashes preserve Arrow record order. Donor hashes cover the full cluster-ID mapping; prompt mapping hashes cover each selected cluster and each view’s clean D/H text hashes. The offline tokenizer snapshot is `/work/nvme/beto/swong2/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659`. No new dataset/manifest artifact is created.

## Exact source-ID audit trail

Eligible IDs below are in ascending **cluster-hash order**, the ordering used for donor rotation. Recover cluster hashes from the exact `_scenario` definition above; do not infer ordering from source-ID lexicographic order. All exclusions below are structural and pre-outcome.

### train: 122 eligible representatives

```text
7e01c526b34d 1e3f8afaa5d2 351550a8484b 259caf86a700 4651cb3492c9 8ed4858676a6 9692bab8cc92 31c153eb7941
7f9fab983129 39db96199da6 4725d238c7c6 38ef0d153b2f 5616c2f5d635 52b81964d56d 1ca0ce5cca5a 1afcc9e0618d
a59852ab114b 8c0f7e61850b 238006e26036 681eac4b15f5 0c679848ad02 9cb21ebb76b1 adc346657f8f 0613d44dac18
29c2bb4fa5e8 747ddadfa7da 21f662ce7317 26400d89e35c 44cebd6aacd8 74e3a4be5833 a91efd0dc57b 52d4182e74ea
4fbffd14dd85 8e5743ff3dda 067a357e4f0a 063866254a37 612f794af4d9 a36e896e5312 1aafe9378385 69d200c04066
571a1f732c85 9500d83b62e2 8aa2c363dfff 7306a888f799 6c47e0423e06 8cd42ad3bd6a 4032ea710958 9d3dc38c8110
66deb15580a7 1088638df94d 76f40af349b7 67acc02e177b 38444654bcf4 60f6449139ec 17b53c1091cb 291d6b950ad8
5d9a0764b17f 3758ad42149d 2d6232c4c33a 083d3cea3f0c 9e03bec72452 611fe9d99a47 1e737f0ea7c2 0207b5189faa
5cd0f401e6f6 2a410c1cb633 ad6b7858d4a9 13ac927cdc14 1042d273a931 95a6dda272e7 794830daddcc ade4b687b576
7e6212e5444b 4dd46ca1f197 318f2cb01722 0b28d893b9cb 5bac7187752e 38b358376473 0a5a5cda5f98 1fc1a3d9041b
73faeeac3772 8384758d94ed 2ec1d8e626d0 8ada5973fb73 5f33db8bc037 959a5a5336b9 9b196e490f36 339356da8b9d
0d739c4cba45 2b4b33d2c7b8 23a62a3b0b8b 504f02ce9904 87ff2b5e1a60 034dbc08726d 2e28a14c708d 07ead8683c5a
67afcbf9a076 3fc250f5d4b9 136cdb97b7da 14aee37e8d2c 364cd4dac8ed 666985ff4cde 4d12b4509a09 4019ed35dded
7c1fd3c2c8d6 04f6bdcf2e2c 8b01675a3c86 554c69216acc 4ffacc54550d 5aa9be253927 12489881036b 069d7b336593
01c4a8d8143d 4b5c8d9ae5c3 4ef6e8185cad 63f51afb6076 430285f63dfb 1b8ed1b022a3 320433a38428 597fca5f1e49
8bff16ffba57 803d0b2988fb
```

Higher-priority cluster exclusions (`source_id: higher-priority split(s)`):

```text
008dc024e491: test
00da68d72183: validation
01a767e70ac7: test
043ca4fea9b0: test
0702c12acd1a: test,validation
0f2726bc09e8: test
1268ee790209: test
127d4457c4f2: test
12892527e071: test
13ec0b2091a1: test
1c3c9b3a3f6e: test
1c8f885241b2: test
2047263af509: test
236dddc837fa: test
240051ada9da: test
26bba7154c71: test
2b504df2aa68: test
2d613e247084: validation
2d6b2061c5d0: test
2fa3500d06b5: test
329d420e2025: test
347d98ebb72f: test
34b9cbc157e3: test
37b60384b323: validation
38114e987096: test
39232ffdbfb6: test
398bade87f9b: test
3b5dae543b78: test
3d1746fffc3e: test
3d6a7991da73: test
3da306993ba9: test
46313817f4a0: test
468a82c8806f: test
47726fa83267: test
47d63508d5ac: test
493cf20429ec: test
4d8ae54f888c: validation
4da0283ff7c1: test
4fc668ed3a1f: test
52e29ed2d299: test
55e266e9d9e9: test
59c1704284bc: test
5d3a822201eb: test
60c543f9c4c2: test
60cf36ab3bf7: test
613e0001420b: validation
62c1aa5d2374: test,validation
6500f56efdb0: test
67dbe0b2c832: test,validation
6b501913024a: test
720624d1addd: test
76a0878e3d9c: test
770e157c892d: test
78f34ec39de3: test
7dea2e73eff8: test
83023cc624f0: test
830a4814c995: test
87445adc70ea: test
8f5d830872a1: test,validation
90130e39ed06: validation
935ff1c9a3dc: test
9a0ef5f8b03e: validation
9af827ccf55b: test
9b1c28ccb571: test
9b5c98a90e0a: test
9fc41d5f87e2: test
a133f5239a89: test,validation
a31813cb817b: test,validation
a60bbf3ee3c8: test
a6debd37c173: test
a86809a3ffd2: test
ab4059b8ab41: validation
ac45b55ccb50: test
```

Additional within-cluster wrappers omitted (`omitted -> selected representative`):

```text
acefe5d25861 -> 4032ea710958
4b8560f3480f -> 083d3cea3f0c
6d96474899bd -> 318f2cb01722
66788c4be85d -> 4ffacc54550d
07524d21c8a2 -> 8bff16ffba57
```

### validation: 126 eligible representatives

```text
5050aabfbbbf 44f6145d9328 75966af09538 847616e6d6a2 8ea4ec7799cd 14f18d69ad14 4d4a3931eaaf 809218076379
7240fa2bedde 6a003c98532f a82b7f224b45 02910e20a60b 83f5b002c7f2 af9150f4fb2e 820ea18e0ca0 8fe84505e024
8e519de1ce1f 6501ec2ee904 2d5368c91da5 1cb6a90c1827 6d79032342f4 17c0820da4f8 4abb2dcbd9b7 3c042b6af430
67832ae5c32a 3a84e1d66c59 9064785a1e46 23a4ff27bcf7 51bbb2b14309 25b52b267972 498cfd75ae83 4e53eab401f8
a7289f6cc90e 02276b8f84f6 a2566b3fdcd0 ae737d018857 aed39c1c35d2 70bba8fadbcf 74e9f458a8cf 021b56727914
65d838bcdc76 4a349ed16a2b 5124a1934b23 411790ee1587 041576f3d530 8c62d99c7c3c 75b409eeb2c2 385c05809edc
1231be3a89a8 57506c1a7865 69beac907449 639b9d755e2d a8ae6279a9d2 98e360917f00 43f44cfe74b8 7a3296204183
121f4602b4f5 b76ef34cd60c b158c8883ab9 244b49ec2155 0fa05df7d6c0 54ea1b8cced5 6adfa51b28a2 6bc81ec87bc9
aa7ef05f108b b38384ecd516 65dcb388c60f 6b3a86d770ef 5b7fe2bd2571 7afa9233d599 b16617af76e4 3f7c7fa524b5
5c020d44d448 351f036f483c 4051486ce73b a29492822947 4fe69bdf5c36 1d357502dd05 179a6a573a78 6312c6da001e
04bbb29b7fb6 732384f74c53 0dc1a85babe5 aef123079ff2 0bc75a092462 aba318cde0e3 68d2ed7211d4 8b3f11bec775
99bde450528b 21405eee9648 8a727ee88161 3a5a32406ef9 77bcf0e12d93 ab3dffd68f4c b35a0545783a 462f0b5e5fc4
6048bc562bd1 135a45bc179d af19fb357555 3a524226a823 12aadde85b4b 04ad4edb52fc 0527abf75303 4cd957f006b1
42c2047e680b 1f5efece0150 1b933e3b428e 892277172528 119ce9ab2888 36c5e48513db 80bb6978b80a 6b1d740ee67d
4445a59ce9de 6330a52d0ba8 3818f2554413 8d19e526a26e 31ad8f2cf7b8 b3bad12cd13c 612e3ec2dd7d 80030b36981b
9e72e6207d91 54a1fa0c4043 6179ac57ab7b 1cfa44ac532a 3a94099ed314 0b9d5f099ed9
```

Higher-priority cluster exclusions (`source_id: higher-priority split(s)`):

```text
03bd69e9420e: test
0a1bcaf22977: test
0aea423d64dc: test
0b29d1224756: test
0b7b6b488c2f: test
0bda68edbc35: test
0e5783076cfc: test
100c645dfe65: test
113e798dd261: test
13456489b92b: test
13ff3fddd929: test
15ce3cb4bd78: test
160f949e5477: test
19c0a1efcc1b: test
1e6c32882ec1: test
2179460ab4c5: test
22759875209d: test
2347bae40841: test
295edf5c6781: test
29a53fd9227d: test
2b93ce3d61bc: test
2eedd7c604d8: test
31dc7eac39b5: test
35f2f5a58552: test
38b1f9de280f: test
3b7ab0c0b393: test
3db5e6461c5c: test
3e377831940b: test
43d6f3c3dcb0: test
44c89496c01d: test
5311c1223377: test
58da31ac7ae0: test
5f09b799e1ac: test
61dabc7d4af9: test
62fca56c7598: test
630f1eba5221: test
65e7c9227791: test
66698494552e: test
686b506aff51: test
6aca04e988e7: test
6ae8531a82d3: test
705ec9a250b6: test
76e2e3bbabad: test
789b065987d1: test
7c97460d94fd: test
801c75309e65: test
824674be5dc0: test
837ca9184572: test
86813061b5e2: test
8a35082e8d94: test
8a39a48aabaf: test
93498d5dba34: test
94fe6c9cafc4: test
9fc0071c8d76: test
a0fb7228bfb7: test
a1950897a3c1: test
a251b73d29ee: test
a5c662997f42: test
ac55830bc1ac: test
ada6351e27d6: test
afd0a7b6a2df: test
b1ac6d86c3d1: test
b49facfdcc72: test
b51bd938341b: test
b542bd447bd9: test
b5b4b2623576: test
b5e72e060eb4: test
```

Additional within-cluster wrappers omitted (`omitted -> selected representative`):

```text
77b098d45e08 -> 43f44cfe74b8
6f7051701c89 -> 121f4602b4f5
3a96dbf39f38 -> 8a727ee88161
14ebe6d7dabe -> 12aadde85b4b
23b0d8631e1c -> 12aadde85b4b
7297d198c4c3 -> 12aadde85b4b
a9d29c8cb26e -> 54a1fa0c4043
```

## Authoritative correction: actual Stage 1 exposure exclusion

Follow-up on 2026-10-18, before any Stage 2 training freeze. **The original 122-train / 126-validation pools reuse exact prompt texts that Stage 1 actually uses as corrupt donor inputs. Recommended final pools are 121 train / 122 validation pairs after five additional structural cluster exclusions and deterministic donor reassignment.** This section supersedes the earlier implication that all corrupt-stream overlap lies outside the actual Stage 1 exposure scope. The earlier zero-overlap comparisons against *clean test* endpoints remain correct but were insufficient to establish the promised no-Stage-1-input-reuse property. The original report is retained above as an audit trail.

Only frozen input manifest `Deception-Circuit/.claude/worktrees/selective-deception/outputs/selective-sdr-stage1-r1/manifest.json` was read; no result files or outcomes were inspected. Actual exposure here is the union of every `rows[*].recipient`, every non-null `rows[*].donor`, and every `donor_reference_rows[*].prompt`, including D/H, clean/corrupt and every view represented in those rows. Source records or unused cluster prompt variants in the manifest are not counted as actual exposure. This is all planned Stage 1 input exposure in its frozen manifest, independent of which result rows have completed.

The manifest contains 1,408 recipient/intervention rows and 84 donor-reference rows, whose union has **388 distinct exact prompt texts**. Additional intact donor-score calls reuse these donor texts and do not enlarge this set. Manifest canonical hash: `29da71bd7cef5f03bec931e5a4231cb93b3bfb026ce3b00f1ea3367a6aab95a0`; file SHA256: `8232f45a064fb489797fe663dec12ef3c280357f7498ca93e990493109ff689f`.

### Exact intersection and affected sources

| Proposed pool, all four clean D/H views | Distinct exact texts shared with Stage 1 | Affected source IDs / clusters |
|---|---:|---:|
| train: 122 pairs | 2 | 1 |
| validation: 126 pairs | 12 | 4 |

Every match is a proposed clean D/H endpoint equal to a Stage 1 **corrupt donor** endpoint; four validation matches are also Stage 1 donor-reference inputs. There are no matches to Stage 1 recipients. Each exact matching text occurs at one proposed source/policy/view endpoint; Stage 1 may reuse it across several intervention rows. Source/policy/view counts below therefore are unique input texts, not repeated row counts.

| Split | Proposed source | Matching proposed clean views | Stage 1 source | Stage 1 endpoint roles |
|---|---|---|---|---|
| train | `a59852ab114b` | D and H: original | `c1f67165348f` | donor; corrupt |
| validation | `1cb6a90c1827` | D and H: original | `97d8074bf3f9` | donor; corrupt |
| validation | `3c042b6af430` | D and H: free_response, original | `558ec114ed1c` | donor, reference; corrupt |
| validation | `70bba8fadbcf` | D and H: original | `bd57365bb34d` | donor; corrupt |
| validation | `aed39c1c35d2` | D and H: free_response, original | `9719298da642` | donor, reference; corrupt |

Exact matching prompt SHA256 values (the D/H policies and views refer to the proposed clean endpoint; Stage 1 uses the same policy/view from its corrupt stream):

| Split / proposed source | Policy / view | Exact text SHA256 |
|---|---|---|
| train / `a59852ab114b` | D / original | `599ba2dad0ea6bc040afaabebc4009dc661037395e17e8f65ff83064ecad0ffd` |
| train / `a59852ab114b` | H / original | `fb8c61e6db064d239b61c6514b71ded6d595ed0cbe615d64a4a77b9ea751fb15` |
| validation / `1cb6a90c1827` | D / original | `67ca2726ef293c22afcc15f0091ecea3ec27cffe89f57ce85edde832f3038ead` |
| validation / `1cb6a90c1827` | H / original | `0c7a31876fa7efbc8c4ac5f8fe7669c578112549b401f874a641bd59ee41d37d` |
| validation / `3c042b6af430` | D / original | `42cceef7c1ebaf7918deb1b8103172356cc3f64c1095e5073e4b7fb032d5ede1` |
| validation / `3c042b6af430` | H / original | `8ea638b566ebdf2d2f175ea9de4af1b9fb0dd4f592d9ce6e51de957a369fc51c` |
| validation / `3c042b6af430` | D / free_response | `a7e899f2bc3d24b73e4cbb4e2a18bf2f2c847fac07869af1c6134aa9e311b397` |
| validation / `3c042b6af430` | H / free_response | `57481fe038bc51667267b611933816b6b7a26098ea7992eb554b031d14dc7fe5` |
| validation / `aed39c1c35d2` | D / original | `7d4908065841768df0464733ec5b611c78706f1c9caeaaada13a8b40e4c5b81a` |
| validation / `aed39c1c35d2` | H / original | `fec848f7ca5f1cece0100aebb56dbd2e423061b7c6c369ea0f5780d2e7068539` |
| validation / `aed39c1c35d2` | D / free_response | `1c4dc27734902bfa2adc003b05124020d0388baad3b8561552db38dcbd620bdb` |
| validation / `aed39c1c35d2` | H / free_response | `27e63beff062fa664583a3ab36bd903ad81a6f2b121b128f2890c7424d4c052e` |
| validation / `70bba8fadbcf` | D / original | `c15626062a02b230ad25327a0893d68a15d1093f508aec064f2dfd2741d42247` |
| validation / `70bba8fadbcf` | H / original | `c129c5c9da1a1d781da59640c1d1212a12a76efdef64ef65cb99290f14927f7c` |

### Direction of the earlier 58 / 40 broader overlaps

The earlier total compared proposed all-view D/H **clean and corrupt** strings with original raw test D clean/corrupt strings. It is not exclusively unused proposed corruption:

| Direction, distinct strings | Train | Validation |
|---|---:|---:|
| Proposed clean → raw test clean | 0 | 0 |
| **Proposed clean → raw test corrupt** | 29 | 20 |
| Unused proposed corrupt → raw test clean | 29 | 20 |
| Unused proposed corrupt → raw test corrupt | 0 | 0 |
| Total distinct union | 58 | 40 |

Thus 29/20 of the 58/40 original counts are in the direction relevant to proposed clean training/validation inputs. Considering structurally constructed D/H test corrupt prompts in all four views expands that potential full-test corrupt overlap to 252 train / 164 validation distinct strings; these are *not* all actual Stage 1 exposures. The frozen Stage 1 manifest limits actual matching exposure to the 2/12 strings and five sources above. Its complete source-record list is not treated as a record of executed prompt exposure.

### Additional exclusion rule, resulting strata and donor reassignment

Keep the original test > validation > train semantic precedence and the original representative selection unchanged. Add one documented outcome-independent rule: if any of a selected cluster’s clean D/H endpoints in original, reversed, free-response or alternative view exactly equals any frozen Stage 1 recipient/donor/reference input text, exclude that entire D/H cluster from the Stage 2 recipient and donor pool. Do not substitute a different wrapper from that cluster. Specifically remove train `a59852ab114b`; remove validation `1cb6a90c1827`, `3c042b6af430`, `70bba8fadbcf`, `aed39c1c35d2`. This follows the promised no-reuse boundary and does not alter the historical semantic cluster definition or screen any outputs.

Then sort the surviving cluster representatives by cluster hash, regroup by the existing four-view length signature, and rerun helper `_derangement` within each split. Use the resulting H-clean donor for both twins and all masks. Removing a source from the recipient/donor permutation prevents its exposure from persisting through donor assignment. Reassign donors before freezing a manifest; do not carry forward the old 122/126 mapping or its hashes.

| Length signature | Train after exposure exclusion | Validation after exposure exclusion |
|---|---:|---:|
| (113, 113, 90, 95) | 21 | 23 |
| (114, 114, 91, 96) | 63 | 52 |
| (115, 115, 92, 97) | 30 | 40 |
| (116, 116, 93, 98) | 3 | 2 |
| (117, 117, 94, 99) | 4 | 5 |

**No singleton cascade occurs:** every group retains at least two clusters. The smallest validation group remains size two. No additional donor-compatibility exclusions or repeated pruning are needed. Final counts are **121 train / 122 validation independent-cluster D/H pairs**. All final recipient endpoints and assigned H donors have zero exact intersection with the Stage 1 input set. Every donor remains nonself, has a different semantic cluster/source and prompt text, and matches both twin lengths/attention masks in all four views. Original clean train–validation/test disjointness is preserved because the new pools are subsets.

| Designation / item / template | Final train | Final validation |
|---|---:|---:|
| identity / 1 / audit | 25 | 21 |
| identity / 1 / lab | 14 | 13 |
| identity / 2 / audit | 16 | 24 |
| identity / 2 / lab | 11 | 11 |
| inversion / 1 / audit | 25 | 25 |
| inversion / 1 / lab | 0 | 4 |
| inversion / 2 / audit | 29 | 22 |
| inversion / 2 / lab | 1 | 2 |

The missing inversion/item-1/lab training cell and single inversion/item-2/lab training example remain. These extra exclusions therefore preserve structural feasibility for an unbalanced exploratory pilot and do not cure the coverage limitation. No behavioral H or donor-validity claim follows from this correction.

| Reassigned H donor answer equals recipient… | Final train | Final validation |
|---|---:|---:|
| D deceptive-label word | 6 | 4 |
| H truthful-label word | 7 | 6 |
| neither label word | 108 | 112 |

- Final `train` cluster-ID donor-mapping canonical hash: `c7945962d03f61a0c6083a9e32a77b4c86f80e0768dcf6842312ab1ef849db12`.
- Final `validation` cluster-ID donor-mapping canonical hash: `0f842229322cc8c41ea759f1d2d0828dddf64653bbdd08f0b3ec083fcdaae1a5`.

Final source-ID lists are exactly the earlier eligible cluster-hash-ordered lists with the five named sources removed; no new source is admitted and ordering of the survivors stays unchanged. Temporary reproduction inputs/output are `/tmp/selective_pilot_stage1_exposure.py` and `/tmp/selective_pilot_stage1_exposure.json`. No dataset, source code, configuration, job, result file or training manifest was created or modified.

## Final authoritative correction: reserve all actual Stage 1 exposed scenarios

Final narrow strengthening, 2026-10-18, before Stage 2 training freeze. **119 train / 119 validation independent-cluster D/H pairs remain under the required semantic exposure reservation.** These counts and hashes supersede both the original 122/126 pool and the exact-text-only provisional 121/122 pool. Exact text exclusion alone allowed different wrappers of already exposed corrupt facts to survive; the rule below excludes those whole semantic clusters before representative selection and donor assignment. No outcome was consulted, no original report section was erased, and no new dataset or training manifest was written.

### Exact exposure-set definition and operation order

Use the same frozen Stage 1 input manifest and the same actual recipient/donor/reference endpoint union described in the preceding correction. For each endpoint, locate its original selected source cluster and construct `{entity: cluster.scenario.entity, items: sorted(cluster.scenario.items), honest_item: truth}`. Set `truth = cluster.labels.H.text` for a clean endpoint and **`truth = cluster.labels.D.text` for a corrupt endpoint**, because the item-swap reverses the source fact truth. This is independent of whether endpoint policy is D or H: a pressure instruction changes the policy, not which fact is truthful. Key each scenario with helper `content_hash`, exactly as `_scenario` keys proposed source records. References and repeated donor usages add no new scenario if the fact was already reserved.

This reserves **122 distinct exposed scenarios**: 64 represented by actual clean endpoints, 64 by actual corrupt endpoints, with six scenario keys in both sets. It reserves only actual Stage 1 endpoint scenarios, not all unused raw test corrupt variants. The frozen manifest contains 388 distinct exact texts and 388 distinct complete token sequences. Every manifest endpoint’s frozen tokens was rechecked against its text with the same cached tokenizer; all agreed.

- Frozen Stage 1 manifest canonical hash: `29da71bd7cef5f03bec931e5a4231cb93b3bfb026ce3b00f1ea3367a6aab95a0`.
- Frozen Stage 1 manifest file SHA256: `8232f45a064fb489797fe663dec12ef3c280357f7498ca93e990493109ff689f`.
- **Exposed scenario set hash**, helper canonical hash of the sorted list of 122 scenario-key hashes: `b2e4c7630552ae1fc12d62d0b90d21b6d653fe2801ecacedad37f4e367b49e10`.
- Exposed scenarios content hash, helper canonical hash of scenario objects ordered by their scenario-key hashes: `3057c071e7ded1067da5d66e161ee9c577ff938cb0a41fead009cc50beba77be`.

Operation order is mandatory for reproduction: (1) retain the original raw test > validation > train semantic precedence; (2) exclude every remaining record whose source `_scenario` key is in this actual-exposure set, taking the whole cluster; (3) run unchanged structural preflight; (4) choose one representative per surviving cluster using the original ascending-cluster-hash / stratum-count / source-ID helper rule; (5) exclude any singleton length-signature groups; (6) rotate each surviving signature group with helper `_derangement`, sharing its H-clean donor across D/H and all masks; (7) assert zero semantic, exact-text and complete-token-sequence intersections with all actual Stage 1 inputs. Do not first pick representatives and then try a different wrapper to evade exposure exclusion.

### Whole-cluster exclusions and final denominators

| Step | Train | Validation |
|---|---:|---:|
| Records after original semantic precedence | 127 | 133 |
| Additional actual-exposure semantic exclusions, records / clusters | 3 / 3 | 7 / 7 |
| Records remaining before preflight/dedup | 124 | 126 |
| Structural preflight failures | 0 | 0 |
| Extra wrappers omitted by cluster representative rule | 5 | 7 |
| Eligible representatives before donor compatibility | 119 | 119 |
| Singleton/cascade exclusions | 0 | 0 |
| **Final D/H pairs** | **119** | **119** |

Every additional exclusion corresponds to an actually exposed corrupt-stream fact. Compared with the preceding exact-text-only correction, there are **two extra train** and **three extra validation** exclusions. No representative changes to another wrapper in surviving clusters; final source IDs are exactly the original cluster-hash-ordered 122/126 eligible lists with the ten sources below removed. No previously omitted record is admitted.

| Split | Source to exclude | Exposing Stage 1 corrupt source | Beyond exact-text-only rule? |
|---|---|---|---|
| train | `063866254a37` | `7291880419c3` | yes |
| train | `5616c2f5d635` | `0daece526aa9` | yes |
| train | `a59852ab114b` | `c1f67165348f` | no |
| validation | `1cb6a90c1827` | `97d8074bf3f9` | no |
| validation | `3c042b6af430` | `558ec114ed1c` | no |
| validation | `4051486ce73b` | `b74c0dc3566e` | yes |
| validation | `4fe69bdf5c36` | `5e401b48d855` | yes |
| validation | `70bba8fadbcf` | `bd57365bb34d` | no |
| validation | `aed39c1c35d2` | `9719298da642` | no |
| validation | `af19fb357555` | `8c54060ac2e2` | yes |

The exact scenario-key audit trail for these ten exclusions is:

```text
train 063866254a37 58e0325022f2c3f6db305d0ccb3a2933206bbef5c3f767562a6551fc79a7f85f
train 5616c2f5d635 2796eedebafe67d4b430a73c38ef8ee45cdc59ba6ba76006e7435c9643a9abd0
train a59852ab114b 2fd530de1d9514b9947ffc63302d011f2b3ce412fbd8a3a64865f69bdbc44b4d
validation 1cb6a90c1827 339368f3e73439f7b877849998b5b5280225612002101cd6b13b132f08aee6ed
validation 3c042b6af430 3ce093811da7d8b99189fba5b92bfd9a55dc829a883ce496b4e543c9619e98ac
validation 4051486ce73b a29a9351a1fc61d7024d03ceda8169d0807bbdaa4e3c3b87a33b0db77b7d454b
validation 4fe69bdf5c36 a52ce01e520eef7af523245c65bf3fdf305b75818d75d9f2d19a3206217fbff7
validation 70bba8fadbcf 56c53774936549c3f7a74ce54babad6143041bddd7035015cc574a49bda46e61
validation aed39c1c35d2 56aa48e5ad80fff0f5ca827c59bd5c6c1d302bfa20dcac5a8853b32d1584a8ab
validation af19fb357555 c66a89be8f5aef0db075111bfe0238706f542764fd5b2178e720e05d862c94e0
```

### Final coverage, alignment and input isolation

| Designation / item / template | Final train | Final validation |
|---|---:|---:|
| identity / 1 / audit | 25 | 20 |
| identity / 1 / lab | 14 | 13 |
| identity / 2 / audit | 15 | 23 |
| identity / 2 / lab | 11 | 11 |
| inversion / 1 / audit | 24 | 24 |
| inversion / 1 / lab | 0 | 4 |
| inversion / 2 / audit | 29 | 22 |
| inversion / 2 / lab | 1 | 2 |

The original missing inversion/item-1/lab training cell and single inversion/item-2/lab training example persist. This correction protects the exposure boundary; it does not make an eight-cell balanced pilot possible.

| Four-view token-length signature | Final train | Final validation |
|---|---:|---:|
| (113, 113, 90, 95) | 21 | 22 |
| (114, 114, 91, 96) | 62 | 51 |
| (115, 115, 92, 97) | 29 | 40 |
| (116, 116, 93, 98) | 3 | 2 |
| (117, 117, 94, 99) | 4 | 4 |

**No singleton cascade:** all five length groups in both splits retain at least two clusters; the smallest validation group is still size two. Every final H-clean donor is a different source/scenario from its recipient, has unequal prompt text and matches both twins’ lengths and attention masks in all four views. Donors form the reassigned within-split permutation and introduce no extra facts or endpoints. No extra alignment exclusions are needed.

| Final intersection check | Train vs all Stage 1 inputs | Validation vs all Stage 1 inputs | Train vs validation |
|---|---:|---:|---:|
| Semantic scenario keys | 0 | 0 | 0 |
| Exact prompt texts, all four clean D/H views | 0 | 0 | 0 |
| Exact complete prompt token sequences, same views | 0 | 0 | 0 |

Token overlap here means equality of the entire unpadded prompt token sequence, not shared words or common chat headers. The checks include all final recipient views and all assigned donor views against all frozen actual Stage 1 recipient, donor and reference inputs, including corrupt endpoints. Original reservation against every raw test clean scenario remains in place. The absence of matching strings/tokens is additionally checked; it is not inferred from semantic inequality alone.

| Reassigned donor H answer equals recipient… | Final train | Final validation |
|---|---:|---:|
| D deceptive-label word | 6 | 4 |
| H truthful-label word | 8 | 6 |
| neither label word | 105 | 109 |

### Final reproduction hashes

All hashes below use helper canonical JSON hashing. Retained-record hashes preserve original Arrow record order after both reservation rules. Representative hashes cover `{cluster_id: source_id}` after deduplication; donor hashes cover `{recipient_cluster_id: donor_cluster_id}` after the final rotation; endpoint hashes cover each final cluster and each view’s clean D/H text hashes. These replace the preceding provisional hashes.

- `train` retained records: `f9a895ea5e05720c2e658132118c2da6924885b3f2abd582f002f174dc32a737`.
- `train` **dedup/representative mapping**: `15e75543b365e739b779a06a11c3f6a063208016c078e646fb09a2824a290d09`.
- `train` **donor mapping**: `36f2a7f9f6a6824650c2423d0a3efc19e7a9625bee3d8a5e75eabe815d400ec2`.
- `train` all-view clean D/H endpoint mapping: `1ab6cf1c7538d17f2286964dff89bf3efd23a82de0d39c3ad2c456b118ba441e`.
- `validation` retained records: `8256872e93a4ba4ba34f5c5c45c4f7dda8c2a29903b3b58f8b73ce23a8a667b8`.
- `validation` **dedup/representative mapping**: `fc5f4e989a7eba00a65efe70d24030b46fd5b526b04b0a0961ddb53cbc66d9da`.
- `validation` **donor mapping**: `4e6b8a1359ead8f6720f35baef582bded3e35a0ed6e17c2039673dbde03b031f`.
- `validation` all-view clean D/H endpoint mapping: `47551a18a8e08fb11b7b1a3ea002ca0cf02af75baee0c54b36674ac47ccd1a41`.

Final audit code/output: `/tmp/selective_pilot_semantic_exposure.py` and `/tmp/selective_pilot_semantic_exposure.json`. Only this report was modified within the project. Candidate union remains the previously resolved 103 heads; no new model results, validity strata, training hyperparameters or compute estimates were produced. The resulting 119/119 pool is structurally feasible for the same unbalanced exploratory pilot, conditional on the outstanding behavioral control and cost gates.
