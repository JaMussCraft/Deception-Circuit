# Independent review of actual calibrated shard plan

2026-10-21. **PASS. No remaining plan-release blockers.** Reviewed actual fresh calibration23102317 and frozen `operator/sharding-plan-1eb79892/shard-plan.json`, not the earlier timing illustration. Lead context compactions: **4**. Read-only CPU metadata/hash/arithmetic checks only; no source, ledger or git edits, model execution or GPU jobs.

## Exact artifacts and binding

- Source commit: `1eb79892b0c4a428774cf340350d2297d9ec58f7`; all51 frozen source/import files independently hash-match the current files.
- Scientific payload independently canonical-hashes to `52f3860915bd0843dbcb503d856d034659add37458863dd3c3f5ece75b3bf620`; protocol file SHA256 `1196d1569aa53ee1d37419c52b27d9fec4127f146def6e91e44fe5faf4e52914`. Scientific prompts, factors, row order, rubric/gates, B8/L224, EOS and64-token cap remain fixed.
- Plan canonical hash independently recomputed: `1e72decf396e70c532ad676c9f726e94aff045add07bc78871d8104578a71f5a`. Its calibration canonical hash `fca6d274ee685d8465c3b26b26d54624141b61835599ded25e042c10620c1e67` matches the fresh receipt. Receipt file SHA256 is `8ca25e9928dfe8e0b91e3698438e625121f2778ef88668d29ed215afd13f6d07`.
- Calibration, protocol and plan agree on provenance/source/cache/software identities. Hardware is one NVIDIA A100-SXM4-40GB, capability8.0,42,405,855,232bytes. The runtime receipt records the matching software metadata and B8/L224. This binds future main checks; it does not establish a device not yet allocated.

## Numerical coverage and timing

Independently checked exact calibration ID order:64 rows/eight original batches and slots. All256 receipts pass finite/full-vocabulary/identical-greedy/bitwise checks with maximum error0:64 each repeat, empty-hook, full-component baseline and self-replacement. Operator receipt records terminal COMPLETED0:0 and112 actual allocation-seconds. Calibration is excluded from main labels and scientific analysis.

Measured terms are F=.42391343391500413, A=.2233693019952625, P=.304583712015301, startup22.45228822506033, controls7.491382197942585 and I/O14.109010661253706 seconds. Allocation-start/model-load timestamps independently reproduce premodel50.3543221950531seconds within timestamp precision. Thus `H=max(120,ceil(2*premodel))=120`, with margin60 and fixed buffers120/120/90.

Independently evaluated the frozen full64-cap formula, retaining48-fold panel I/O growth. **q34 is the largest fitting integer**: T(34)=3365.2480503334664, plusH+margin=3545.2480503334664≤3600; q35 gives3631.5043825847097>3600. No average response length or semantic outcome enters this calculation. Every stored range forecast independently matches its generation/control/checkpoint counts and formula.

## Complete panel and resource proposal

The plan contains11 contiguous34-batch ranges, then `[374,384)`, for12 shards. Independently flattened all range IDs and verified exact equality to the original3,072 protocol IDs, unique coverage, original order and384 whole eight-slot global batches. There is no gap, overlap or repacking. The final10-batch forecast is1295.0960763036273seconds. Sum of T over all ranges is38312.82462997176seconds before the separate per-allocation H/margin allowances.

The full proposed main reservation is12×3600=**43,200 A100 GPU-seconds (12hours)**. Together with the current40,800-second native-phase reservations, including the retained cancelled monolith and fresh600-second calibration, the prospective phase total would be84,000 reserved GPU-seconds. These are proposals, not asserted submissions or actual consumption; operator alone owns accounting and release receipts.

## Release/registry and scope

The plan hash-binds the canonical absolute registry `operator/sharding-registry-1eb79892`, canonical `operator/sharding-release.json`, and the existing terminal-cancellation/zero-attempt receipt. Independently verified cancellation-receipt byte hash and terminal zero-attempt/no-output fields. At review time the main registry and canonical execution release do not yet exist. The proposal binds the same plan/science/provenance hashes and inventory location; it is not an activated release.

Root activation and runtime execution must still enforce atomic exclusive claims, original slots, predecessor PASS, exact live hardware/software/source bindings, actual remaining-allocation checks and full registry inventory. Any attempted failed shard stops successors and scientific release. Strict complete merge and later blinded labeling remain required. This PASS approves the actual frozen calibrated plan; it is not a GPU submission, automation review, runtime success claim or behavioral gate result. No main responses have been inspected.

**Review-integrity disclosure:** an initial schema-inspection command mistakenly treated the calibration generations list as a dictionary and surfaced calibration response text in tool output. No outcome classification or scientific selection was performed, and no prompt, q, range, bound or plan changed. Root acknowledged the exposure and directed completion of the metadata-only review; this reviewer will not serve as a blinded outcome annotator. Subsequent checks extracted only IDs, numerical controls and timing/provenance metadata. The timing-only partition was independently recomputed from the fresh receipt and equals the already frozen plan.
