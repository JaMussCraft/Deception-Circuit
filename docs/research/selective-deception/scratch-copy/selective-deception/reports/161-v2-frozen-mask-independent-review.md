# Independent review of V5 V2 frozen-mask assessment

2026-10-24. **PASS for the bounded descriptive result; no validation defect requiring GPU rerun.** The strongest finding is a causal, task-conditional change in instructed label selection under independent honest-donor head replacement. FAR shows unusually strong D-to-truth correction with largely retained neutral-H capability, across both item and designation polarities. SDR and SER show different suppression–preservation tradeoffs. These results do not establish a deception-specific or strategic-deception mechanism, a minimal circuit, or universal superiority of new30.

## Independent verification

Read reports153/155/156/160, the bound scorer and its completion/control flow, frozen prepared/proposal/receipt records, all6144 saved rows, and detailed audit160. Executed the report160 CPU audit with writes intercepted in memory: every assertion passed and both regenerated report160 and audit160 JSON were **byte-identical** to the existing files. Independently calculated family × item-polarity × designation-polarity cells directly from rows and prepared inputs. No original artifact, source, job, API, or Git state was changed.

The audit rehashed source/input/model-metadata/mask/proposal/receipt bindings and43,106,928 source-dataset bytes; verified every stored prompt, label relation, donor assignment and right-aligned map; and exactly recomputed all48 paired summaries. Coverage is384 recipients =128/family, four prompt conditions D/H/F/HI, four fixed masks, clean stream only:6144 unique expected keys, no filtering or missing rows. Each family contains32 recipients in each of four polarity/designation cells. Old238 fit/selection clusters correspond to225 exact scenarios; recipient and donor IDs/scenarios satisfy the declared exclusions. This proves exact structural exclusions, not semantic deduplication.

Source closure is to the hash-bound source files and receipt commit `9eb2a6a5c8481d99053b78ec2cdc43a3c606cd3c`; this review made no Git provenance inquiry. The driver verifies pretrained snapshot inventory before loading; this CPU review rehashed its bound anchor/metadata rather than rereading all weight shards. The full-vocabulary identity count is1572 =1536 independent-donor all-open assertions +36 masked self-replay assertions. Inspected source requires bitwise equality and aborts on failure before writing complete summary. Complete status and full coverage therefore support their successful execution. Full logits were intentionally not saved, so there is no independent offline recomputation of numerical equality, softmax, or KL. BF16/SDPA, deterministic algorithms, TF32 off, zero optimizer/API calls, and1216.827 driver seconds are consistent with the bound artifacts.

Minor CPU reproduction issue found and resolved by the report160 owner: the original relative-path command failed at `Path(__file__).relative_to(ROOT)`. The owner changed only the script self-path to `Path(__file__).resolve()` and preserved the originals in `transfer-v5/report160-before-path-fix/`. I independently reran the corrected relative-path script with writes intercepted; every assertion passed and the regenerated report and audit JSON again matched the saved files byte-for-byte. Only audit-script selfbinding changed; experiment evidence and scientific results are unchanged. Current audit JSON SHA256: `e653686e1ddcfd08d50ff2e3e2076af2ac7cf782b1ff04de51ec36a54ed0b6db`.

## Confirmed comparisons

All counts below have denominator128. D columns report deceptive-label argmax / truthful-label argmax / other-token argmax. H reports truthful retention, which equals its total truthful count because intact H is128/128 in every family.

|Family|Mask|D deceptive / truth / other|H retained|
|---|---|---:|---:|
|FAR|intact|128 / 0 / 0|128|
|FAR|new23|41 / 87 / 0|127|
|FAR|new30|2 / 126 / 0|126|
|FAR|oldD69|7 / 114 / 7|105|
|SDR|intact|128 / 0 / 0|128|
|SDR|new23|106 / 22 / 0|122|
|SDR|new30|87 / 41 / 0|122|
|SDR|oldD69|24 / 95 / 9|91|
|SER|intact|128 / 0 / 0|128|
|SER|new23|60 / 68 / 0|123|
|SER|new30|36 / 92 / 0|118|
|SER|oldD69|17 / 110 / 1|115|

For both new masks, every loss of D deceptive argmax becomes the construction-defined truthful label. It is therefore accurate to describe these as truthful **label corrections**, not merely nontarget outputs. OldD69 also produces7/9/1 other-token D outputs on FAR/SDR/SER. Those tokens are neither proven coherent refusals nor proven broken language: one-token readout cannot adjudicate either. The user's desired coherent refusal remains a valid behavioral endpoint, but this assay does not measure it.

Verified new30 versus oldD69 paired D corrections, in new30-only / oldD69-only / shared order: FAR13/1/113; SDR11/65/30; SER10/28/82. H retention in that order: FAR22/1/104; SDR33/2/89; SER10/7/108. Thus FAR favors new30 on both observed endpoints; SDR strongly trades suppression for preservation; SER trades18 fewer corrections for3 additional H retentions. No family-independent winner follows. FAR mean deceptive probabilities are also nearly tied for new30 and D69 (10.30% versus10.43%), so the aggregate argmax advantage should not be represented as a large probability-level advantage over D69.

The nested new23→new30 contrast adds the seven fixed heads L7H31,L8H10,L13H15,L13H23,L17H27,L19H13,L20H19. Additional / reversed / shared D corrections are39/0/87 FAR,19/0/22 SDR,24/0/68 SER. H new30-only / new23-only / shared retention is0/1/126,2/2/120,0/5/118. Identical SDR H totals conceal two losses and two gains between masks. The seven-head contrast is conditional on the other23 heads already receiving replacement; it neither isolates seven-only sufficiency/necessity nor attributes effects to individual heads.

## FAR default-label check

Separate direct row counts show the FAR advantage spans all four predetermined cells. Each cell has32 recipients; cells use the dataset's stored polarity names.

|Item polarity|Designation polarity|D truth new23|D truth new30|D truth D69|Added corrections23→30|H new30|
|---|---|---:|---:|---:|---:|---:|
|1|identity|21|31|28|10|31|
|1|inversion|22|32|31|10|31|
|2|identity|28|32|30|4|32|
|2|inversion|16|31|25|15|32|

All39 added corrections occur without a previously truthful D answer reversing, and each cell improves. Near-perfect truthful selection when the correct item occupies either position, under both designation polarities, rules out a simple fixed item-position or designation default as a complete explanation of this slice. It does not rule out a general shift from following the wrong-answer instruction to following the record, donor-conditioned routing, lexical effects, or more complex shortcuts. Corrupt twins were not scored, so there is no within-item counterfactual causal claim about swapping the record.

## Controls and mechanism boundary

Neutral H is a meaningful capable control: baseline128/128, independent validation H donor rather than self donation, same donor per recipient across masks/conditions, and matched D/H token lengths and position maps. FAR new30 D correction126/128 with H retention126/128 therefore supports a strong condition-dependent intervention effect beyond blanket loss of label capability. It is not evidence that all honest behavior is preserved.

F/HI qualify rather than erase that result. New30 F accuracy is127/122/103 on FAR/SDR/SER; SER loses25 baseline F truths versus10 H truths, so broad benign-task preservation would be misleading. D69 SER F accuracy108 exceeds new30's103 despite worse H accuracy. New30 HI totals are127/115/124; SDR's unchanged115 total masks8 lost and8 gained, leaving107/115 baseline truths retained. SER HI retains123/126 and gains1, rather than retaining124. Report160's paired loss/gain accounting is correct.

F deletes a clause and HI changes an instruction; their prompt lengths and right-aligned donor maps differ from D/H. They are not position-matched controls for isolating a semantic pressure mechanism. All final queries map to donors; unmapped early prefixes retain clean shadow activations. Independent donor reuse and imperfect semantic position correspondence limit a removal interpretation and statistical independence. Descriptive paired counts are preferable to an unqualified independent-trial significance claim.

The recipients remain behaviorally filtered, construction-defined rule-instructed tasks. FAR wording differs from SDR/SER; prior one-word judgments did not establish SDR/SER semantic purity. Cross-family effect variation cannot distinguish purported psychological mechanisms from instruction/readout/template differences. Neither exact old-training exclusions nor the new intervention controls resolve that construct issue. Six calibration cases recur in assessment, precluding a wholly independent calibration replication claim. No new mask selection, test optimization, WikiText/general-utility evidence, random-mask comparison, free generation, or naturalistic strategic-pressure validation is supplied here.

## Recommended takeaway and disposition

> Frozen sparse head replacement transfers beyond the original fitting scenarios, but its effect depends strongly on the instructed task family. On FAR, new30 changes126/128 deceptive label choices into truthful labels while retaining126/128 neutral-honest answers, with corrections spanning both item and designation polarities. The additional seven heads conditionally improve D-to-truth correction over new23 in all three families. OldD69 suppresses SDR and SER deceptive labels more strongly but usually incurs greater neutral-H collateral. These results identify a causal contribution to instructed answer selection under the specified honest-donor intervention; they do not identify a strategic-deception-specific circuit.

Retain the frozen comparison and report its bounded result. No validation bug justifies GPU rerunning, new donor matching, new selection, or a rescue experiment. The CPU command-path nuisance is now resolved. Publication-level mechanism language should remain at the instructed-answer-selection level; these data alone do not complete the broader strategic-deception mechanism objective.
