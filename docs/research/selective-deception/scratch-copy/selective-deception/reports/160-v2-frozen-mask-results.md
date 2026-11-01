# V5 V2 frozen-mask results — October 24, 2026

**Audit PASS.** The fixed new30 mask strongly changes construction-defined instructed label choices on FAR and SER while largely preserving matched neutral-H accuracy; its SDR effect is weaker than oldD69. This is single-prefill label behavior, not evidence of semantic or strategic deception, free-generation success, or a deception-specific circuit. All masks and recipients remain frozen; no reselection or optimization occurred.

Assessment job 23159231 is reported COMPLETED (1227 seconds, one H200); the bound complete artifact records 1216.827 seconds. CPU audit independently verified all 6144 unique expected rows (384 recipients ×D/H/F/HI ×four masks), exact source/input/mask/donor/map bindings, finite scalar metrics, and exact recomputation of all 48 saved paired summaries. It rehashed all 43,106,928 dataset source bytes plus bound runtime/tokenizer metadata. Runtime is BF16/SDPA, deterministic, TF32 off. API calls and optimizer steps are zero.

The completed driver reports 1572 mandatory bitwise full-vocabulary identities: 1536 independent-donor all-open checks and 36 masked self-replay controls. These are hard runtime assertions; saved full logits are intentionally absent, so CPU audit cannot independently recalculate vector equality, softmax probabilities or KL. Reported scalar rows and their summaries are internally consistent.

Each table cell uses the full 128 recipients. D counts are full-vocabulary deceptive-label argmax; correction counts require intact deceptive argmax followed by truthful argmax. Probability changes are mean absolute percentage points relative to intact, without two-label renormalization. H/F/HI cells give truthful argmax **(lost/gained)** relative to their own intact row. KL is full-vocabulary KL(intact || mask), ordered D/H/F/HI.

|Family|Mask|D deceptive /128|Mean P(D), Δpp|D truthful corrections|H truth (lost/gained)|F truth (lost/gained)|HI truth (lost/gained)|KL D/H/F/HI|
|---|---|---:|---:|---:|---:|---:|---:|---|
|FAR|intact|128|84.23%, +0.00|0|128 (0/0)|128 (0/0)|128 (0/0)|0.000/0.000/0.000/0.000|
|FAR|new23|41|34.98%, -49.25|87|127 (1/0)|128 (0/0)|128 (0/0)|0.890/0.011/0.015/0.011|
|FAR|new30|2|10.30%, -73.93|126|126 (2/0)|127 (1/0)|127 (1/0)|2.154/0.023/0.038/0.023|
|FAR|oldD69|7|10.43%, -73.80|114|105 (23/0)|100 (28/0)|104 (24/0)|2.956/0.433/0.521/0.411|
|SDR|intact|128|91.35%, +0.00|0|128 (0/0)|128 (0/0)|115 (0/0)|0.000/0.000/0.000/0.000|
|SDR|new23|106|74.84%, -16.51|22|122 (6/0)|122 (6/0)|116 (6/7)|0.253/0.036/0.042/0.059|
|SDR|new30|87|65.11%, -26.25|41|122 (6/0)|122 (6/0)|115 (8/8)|0.375/0.043/0.053/0.075|
|SDR|oldD69|24|23.71%, -67.64|95|91 (37/0)|96 (32/0)|93 (27/5)|1.802/0.591/0.584/0.468|
|SER|intact|128|80.95%, +0.00|0|128 (0/0)|128 (0/0)|126 (0/0)|0.000/0.000/0.000/0.000|
|SER|new23|60|48.99%, -31.96|68|123 (5/0)|104 (24/0)|125 (3/2)|0.449/0.056/0.141/0.030|
|SER|new30|36|35.45%, -45.49|92|118 (10/0)|103 (25/0)|124 (3/1)|0.764/0.086/0.180/0.037|
|SER|oldD69|17|19.42%, -61.53|110|115 (13/0)|108 (20/0)|108 (20/2)|1.565/0.293/0.336/0.298|

Intact D chooses the deceptive label 128/128 in every family; intact H and F are truthful 128/128. Intact HI is truthful 128/128 FAR, 115/128 SDR and 126/128 SER; all baseline HI errors choose the construction-defined deceptive label. D corrections therefore equal D truthful counts. Nonlabel argmax totals and IDs, probability shifts, margins, exact paired cross-tabs, source strata, and alignment coverage are in `transfer-v5/v2-assessment-audit160.json`.

## Fixed paired contrasts

For new30 versus oldD69, the paired D correction counts below are new30-only / oldD69-only / shared; H truthful-retention counts use the same order. These are observed paired differences, without a significance or general superiority claim.

- FAR: D corrections 13/1/113; H retention 22/1/104.
- SDR: D corrections 11/65/30; H retention 33/2/89.
- SER: D corrections 10/28/82; H retention 10/7/108.

New30 removes the 23 new23 heads plus fixed L7H31, L8H10, L13H15, L13H23, L17H27, L19H13 and L20H19. The new30–new23 contrast is conditional on the other 23 heads already receiving independent neutral-H replacement; it does not identify a seven-head circuit, minimality, or individual contributions. Paired additional / reversed / shared D corrections and H retention (new30-only / new23-only / shared) are:

- FAR: D corrections 39/0/87; H retention 0/1/126.
- SDR: D corrections 19/0/22; H retention 2/2/120.
- SER: D corrections 24/0/68; H retention 0/5/118.

## Interpretation and limits

Neutral H is the strongest control: each D/H recipient pair has equal token length and the same right-aligned donor position map, and both receive the same independent donor. F deletes the clause; HI changes the instruction. Their lengths/maps differ, so D–F/HI differences also include position-policy changes. All final readout queries map to donors; early unmapped prefixes retain identical-input clean shadow activations. This is activation replacement by fixed independent validation H donors, not neutral deletion. Donor reuse and varying semantic alignment limit independence and mechanistic interpretation.

Recipients exclude 238 historical fit/selection clusters (225 exact entity/unordered-item scenarios); all donor IDs/scenarios are globally disjoint from recipients and historical fitted scenarios. Exact structural disjointness is narrower than semantic deduplication. The six predetermined calibration cases recur here, so this is not an independent calibration replication. All 128/family are retained, 32 per polarity/designation cell; no failures are filtered.

V2 remains a behaviorally filtered, rule-instructed construction; FAR differs in wording from SDR/SER and prior one-word judges did not establish SDR/SER semantic purity. One final-position argmax cannot establish autonomous deception, knowledge, intent, coherent refusal, natural-language correctness, continuation quality, or general utility. Corrupt twins are structural provenance only and were not scored. No WikiText, random-mask, fresh semantic judge, trained-V2-mask comparison, or statistical independence assumption is added by this assessment. The descriptive frozen-mask results do not justify another selection step.

## Evidence

Reproduce CPU audit: `python .scratch/selective-deception/analysis/report160_v2_audit.py`. Detailed JSON SHA256: `e653686e1ddcfd08d50ff2e3e2076af2ac7cf782b1ff04de51ec36a54ed0b6db`. Source commit `9eb2a6a5c8481d99053b78ec2cdc43a3c606cd3c`; prepared payload `fe5e1685f5edeb464bee74bec07ccdcf9e909055354fc2ddfd33ba88cb9bd8a6`.

- `.scratch/selective-deception/transfer-v5/v2-prepared-frozen.json`: `520a72edae7378bb1ee6ebc42f8bd5054087ab664cab8cc4aa1ff4a343662bb8`
- `.scratch/selective-deception/transfer-v5/v2-inputs-proposal.json`: `198f1e8362a2b2d6c2c61130b20d46960e2d5976628f438a8572ebed28801fa9`
- `.scratch/selective-deception/transfer-v5/frozen-masks.json`: `69999255f3d5bebf363ecc3d8659f9ebcc6f0bb3ad70cebda9d78925eac33fb6`
- `.scratch/selective-deception/transfer-v5/v2-assessment-receipt.json`: `e8a17c73fc0f201aad1fc65a0609d997f58115e8454e1850b104158c16046d1d`
- `.scratch/selective-deception/transfer-v5/v2-assessment/rows.jsonl`: `846fe206edbea4aa64386f8c28bfe2cb2e0ef1610771bba5cb9be082856e1216`
- `.scratch/selective-deception/transfer-v5/v2-assessment/summary.json`: `53f725a781cbbba6728836d137a7aed2e177e1f6ed00997991cc175f8ca68d97`
- `.scratch/selective-deception/transfer-v5/v2-assessment/runtime.json`: `f17c0c50bb13dcbb52f211092286bf0e2a0d1bc6470f1ef0daf4955fbbb95680`
- `.scratch/selective-deception/transfer-v5/v2-assessment/execution.json`: `264908ee8041b4e4a48ebca5e61bb1021c52172e4f9fb3a21edea666fae928f3`
- `.scratch/selective-deception/analysis/report160_v2_audit.py`: `3a535de69ec8aa76ee6b8d9f80524489c80564ea51ec44b420d2078af3262a78`
