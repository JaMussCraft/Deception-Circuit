# Independent V2 implementation and scientific review

2026-10-24. **PASS for root freeze and bounded H200 calibration.** No implementation blocker found. This is not a claim that GPU identity checks, throughput, or scientific efficacy have passed. Root still binds the exact reviewed candidate and source bytes to a calibration receipt and reserves the actual allocation; no additional user permission is required for that authorized continuation.

Reviewed reports152/153, `analysis/transfer_v5_v2_inputs.py`, `transfer_v5_v2.py`, `.sbatch`, both focused test modules, the prepared candidate, and the actual legacy native replay implementation imported by the scorer. No unrelated private evaluation outcomes were consulted. Only CPU tests, cached tokenizer checking and wrapper dry-run were used; no pretrained model, weights, GPU, API or notebook execution occurred.

## Exact artifact and independent verification

Candidate file SHA256 independently matches `520a72edae7378bb1ee6ebc42f8bd5054087ab664cab8cc4aa1ff4a343662bb8`; payload hash is `fe5e1685f5edeb464bee74bec07ccdcf9e909055354fc2ddfd33ba88cb9bd8a6`. The actual wrapper `bash analysis/transfer_v5_v2.sbatch dry-run` passed all current bound-source checks. The candidate remains NONFINAL until root freeze; the older incomplete-source candidate is not the reviewed artifact.

Independently ran both focused test modules together: **15 passed in mgnp/Python3.12 and 15 passed in base/Python3.9**. Base emitted only the existing TRANSFORMERS_CACHE deprecation warning. These include actual trusted hook/gate restoration on synthetic CPU tensors, receipt rejection, global donor exclusion, proposal hashes, fixed-mask support, complete mocked scoring and full-vocabulary metrics. These tests do not instantiate the pretrained model.

## Input and construct boundary

The old fitting/selection manifest supplies 238 clusters and 225 unique exact entity/unordered-item scenarios. Selection excludes those scenarios and old source IDs before taking test recipients; each family has128 recipients,32 per polarity/designation cell, selected by deterministic clause round-robin and hash order. Outcome fields are dropped through an explicit structural/input allowlist. Exact string scenario matching is correctly described as narrower than semantic entity deduplication.

Donors are validation neutral-clause H rows, independently assigned, with every donor scenario and source ID disjoint from the global recipient set and old fitted scenarios. Reuse is declared; there is no independence claim for repeated donors. Recipient IDs and assignments from proposal152 are preserved. H receives an independent donor rather than its own identical prompt. The deliberate self-replay technical control is separate and cannot inflate H preservation metrics.

D, neutral H, clause-deleted F and explicit honest-instruction HI remain distinct. The input helper takes HI prompts from the source's explicit instruction fields and assigns the truthful H labels. The scorer uses the stored clean targets: D target is the construction-defined deceptive choice; H/F/HI target is the truthful choice. Clean/corrupt counterpart metadata is tokenized and bound, but this experiment scores only clean streams. Do not describe its6144 mask rows as a two-stream effect or as natural-language semantic adjudication.

The pressure datasets remain construction-defined, behaviorally filtered survivors under rule instructions. FAR wording differs from SDR/SER and one-word judges failed SDR/SER purity separation. Neither held-out instance selection nor the new runtime removes those construct limitations.

## Intervention and readout correctness

The driver calls the unchanged trusted native capture/replay API with `DecodeSpec(1, ())`. Inspection confirms exactly one prompt forward plus argmax per call: a next-token tensor is constructed but never forwarded. The resulting `last_logits` are the full vocabulary at the final prompt position. No generation loop beyond that single prefill, optimization, semantic judge or paid API exists in this path.

The same-path intact reference uses native `_execution`/`_forward`, explicit attention masks, position IDs and identical-input shadow caches. Every selected head uses an exact binary keep setting; all nonhead gates are hard-open, and nonselected heads remain open. Replay hooks return nonhead sites unchanged. The context restores gates and previous hooks even on errors, which the synthetic test exercises.

Every primary prompt requires exact full-vocabulary equality between its intact reference and independent-donor all-open replay. The first source-ID recipient per family additionally requires self-replay equality for every D/H/F/HI prompt and all23/30/69 masks. A failed equality aborts before a complete summary; no tolerance widening is implemented. Independent donor banks are provenance-checked, have one generated metadata token, contain prompt-query activations only, and are content-hashed during replay.

The right-aligned intersection policy is implemented consistently in preparation and actual replay. An unmapped early prefix retains identical-input shadow activations; a longer donor contributes only its right suffix. The final query and same-family readout suffix align, but record/clause positions need not. The implementation correctly avoids claims of neutral deletion, semantic position correspondence, or equivalence to benchmark EVAL5 tiling.

**Reporting qualification:** neutral H is the strongest matched-length control against D. F and HI often use different position maps/coverage because prompt lengths differ, so D-versus-F/HI contrasts also include this positional-policy change. Report them separately and retain map coverage in interpretation; no extra experiment or donor rematching is needed for this bounded transfer assessment.

Metrics use full-vocabulary argmax and float32 full-vocabulary log-softmax, including `KL(P_intact || P_mask)`. A nonlabel argmax is neither the truthful nor deceptive label. Truth retention/loss/gain is paired to the same instance/condition intact row. Small row records preserve probabilities, margins, IDs, strata and coverage for subsequent fixed descriptive analysis; summary convenience fields need not be mistaken for the entire metric set. No full logits matrix is persisted.

## Execution and accounting boundary

The wrapper fixes offline settings, removes the listed API secrets and does not submit jobs. `evaluate` requires a single-H200 Slurm context, matching prepared bytes/payload, matching fixed conditions and output directory, an explicit positive reservation up to7200 seconds, fixed calibration/assessment sizes, no automatic retry and an exclusive output directory. Actual model snapshot hashes are checked before weight loading; runtime records the source/hardware/software path. Current V5 l0/config and legacy helper inventory are distinctly bound rather than represented as identical code.

Runtime time checks and Slurm's explicit wall limit are complementary. Root must reserve the actual requested walltime in the shared40-hour selective ledger and issue a matching receipt; the driver is not a shared-ledger auditor and cannot by itself certify remaining allocation. The reported17.65-hour historical headroom precedes any pending0.5-hour sandbagging calibration reservation. A proposed0.25-hour V2 calibration is not charged until actually reserved. No budget from the other V2 trained-circuit effort is involved.

Incomplete or failed runs may leave durable partial rows and an execution receipt but no complete summary; they must remain incomplete, without a reduced denominator or efficacy claim. Full assessment completeness is6144 primary rows plus1536 reference prefills,229 unique donor captures,12 self captures and36 self replays:7957 one-prefill forwards and1572 exact identity comparisons. Calibration fixes two recipients per family,96 rows and60 comparisons, at most174 prefills. These counts are not time estimates. Calibration may establish runtime feasibility and numerical identity, never select masks or remove efficacy failures. The assessment includes the same predetermined calibration IDs; it is not an independent replication of those six cases.

Root can now freeze this artifact, perform the already proposed bounded calibration, and decide the feasible assessment reservation from measured runtime. No broad new infrastructure, experiment expansion, or user permission gate is recommended.

Additional independent cached-tokenizer audit completed: all3072 stored clean/corrupt prompt streams exactly match proposal152 recipient prompts and donor assignments; their token IDs reproduce exactly, every leading-space target/truth/deceptive label is one token, every concatenated prompt-plus-label boundary reproduces the stored prompt IDs plus that label token, and each D versus H/F/HI target equals its intended deceptive versus truthful token. This audit loaded tokenizer metadata only, not model weights.
