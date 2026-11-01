# Frozen D/H/F head-membership reference

October21,2026. Reconstructed the original coarse active attention-head supports **directly from each explicitly bound `active_nodes.coarse.json`**, not by inferring F from other sets. No v4 performance, checkpoints, scores, model, GPU or job was accessed; no new mask was selected. Only this note and `sparse-optimization-v4/component-membership-reference.json` were written.

The historical union manifest's `source_metadata.candidate_bindings` names D=`nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742`, H=`nls0.3_honest_noedge_noan_nomh_nomo_nomb_260922-092743`, and F=`nls0.3_nopressure_noedge_noan_nomh_nomo_nomb_261013-204850`, under `Deception-Circuit/outputs/llama-8b-instruct_sdr_coarse/`. Each active-head list exactly matches that file's32×32binary head-mask rows. Historical export provenance names these same operands; its frozen derived core and D-minus-F head supports independently match D∩H=43 and D−F=33.

**D=69, H=56, F=68; D∪H∪F=103exactly.** The sorted union matches both the original restricted manifest's candidate list and the immutable v4 **input** amendment's `union_heads`. Canonical union hash is exactly CANDIDATE_HASH `6c5943656abc881d8ff949f776a3fa9dc11e7161254a2c16738c7306b8624420`.

Exclusive union categories: D-only22, H-only2, F-only21, D∩H outside F11, D∩F outside H4, H∩F outside D11, and D∩H∩F32. These sum to103. The reference retains every head's exact membership and all source/export/receipt byte hashes.

## Historical mask composition

D/H/F columns below are **inclusive overlaps**, so they must not be added together. The masks were read only from frozen historical supports/exports and verified against their original selection receipts and head-list hashes.

| Frozen mask | Heads | In D | In H | In F | Outside discovered F | Outside discovered D/H/F union |
|---|---:|---:|---:|---:|---:|---:|
|oldD69|69|69|43|36|33|0|
|oldW9|9|9|5|6|3|0|
|oldW13|13|11|5|9|4|0|
|oldallW28|28|4|2|2|26|24|

Exclusive mask categories:

- oldD69: D-only22; D/H outside F11; D/F outside H4; D/H/F32.
- oldW9: D-only3; D/F outside H1; D/H/F5.
- oldW13: D-only4; D/F outside H2; D/H/F5; F-only2.
- oldallW28: D-only2; D/H/F2; outside the discovered D/H/F union24.

Layer composition, shown as `layer:head-count`:

| Mask | Layers |
|---|---|
|oldD69|5:6,7:7,8:8,9:6,10:4,11:5,12:6,13:7,14:8,15:3,17:4,24:5|
|oldW9|12:1,13:2,14:2,15:2,17:2|
|oldW13|8:1,12:2,13:3,14:1,15:2,17:4|
|oldallW28|1:1,2:1,4:2,5:1,6:3,7:1,9:3,10:1,11:1,12:3,13:1,14:2,15:1,17:2,22:1,26:1,30:1,31:2|

## Application and limits

After both v4fits pass the complete audit and root freezes finalists, first verify this reference's source hashes, unique integer `[layer,query_head]` pairs and32×32geometry. Then classify the frozen head sets by exact lookup in the stored D/H/F supports. Heads absent from the103union are outside all three discovered supports. Report inclusive overlaps, exclusive categories and per-layer counts; the reference already contains these calculations for the historical masks. Do not use membership to rank, prune, replace or select heads.

“**Outside discovered F**” is the only warranted interpretation of F nonmembership. This coarse sufficient support does not exhaust format machinery, and its boundaries do not establish freedom from format effects or deception specificity. F itself is the learned nopressure-task support, not a complete causal inventory of formatting. D/H/F overlap and sufficiency-support membership likewise do not prove that a head is necessary, uniquely selective or responsible for the future mask's behavioral effect. The oldD69support can be compared under a removal protocol without conflating that intervention with its original sufficiency role.

Reference file SHA256: `26a1fec572fc04a48832b9f2a63fc02ead10a362d277c728ca53f495486247f0`.
Canonical reference hash: `51ef9e1daadd2658de20669e58078277f3bf3c71a9dff845f0cfb9bbe23f2526`.

Verification used stdlib JSON/set arithmetic only: atomic head-list versus mask-row agreement, geometry, original manifest integrity, exact103union/hash, frozen43/33derived supports, historical selection/export/head-list hashes, and historical mask sizes69/9/13/28. No performance-based interpretation was computed.
