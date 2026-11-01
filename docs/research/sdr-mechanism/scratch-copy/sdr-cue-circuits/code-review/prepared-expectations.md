# Independent review preparation

Authoritative spec SHA256: `1eb6fbf88860d8474ca0bba14178edc8a235c985062a055c69a737e9bc987be3`. Read task brief, complete spec, design review and runtime seam. No mutable implementation, production tests or worker report were inspected. No source verdict is issued. Root owns git; this reviewer owns only review artifacts.

`independent_expectations.py` is a five-row synthetic oracle, deliberately independent of production imports and the separate exhaustive prompt/mask oracle. `preparation-results.json` records its CPU execution. Two different input cases intentionally share one semantic triple, checking aggregation rather than assuming each treatment has a unique category triple.

## Semantic and analysis expectations

- Exactly 729 triple cells and 81 recipient-to-patch cells exist even when almost all are zero. Triple order is intact recipient, intact donor, patch. Multiplicity is retained after view deduplication.
- Synthetic donor/recipient strata have counts same=1, different=2, residual=2, summing to five primary rows. Any unresolved donor or recipient puts the row in residual; a residual patch does not redefine its baseline stratum.
- Pair anchors stay fixed across intact/A/B/J and comparator arms. E recipient/donor truth anchors coincide; E example anchors differ. T truth anchors differ; T example anchors coincide. Residual identities always contribute zero, including when both recipient and patch are unresolved. Individual residual indicators remain explicit.
- The E counterexample moves from commitment0 to donor-example1 while the natural donor emits0. It supports rejection of universal emitted-answer copying for that case; it does not change row eligibility or identify an abstract representation.
- Indicator components intact=1,A=0,B=0,J=1 give target interaction2; intact=1,C_A=1,C_B=0,C_J=0 give comparator interaction0. Their difference is2. Values outside [-1,1] are valid interaction values. An all-zero identity inventory stays zero; an unchanged residual gives zero delta.
- Equal-weight fixture means must precede overall aggregation. Synthetic fixture deltas [1,1] and [-1] yield0, whereas pooled rows give1/3. Empty fixed strata should have explicit zero counts and a defined unavailable mean, never fabricated successful effects.
- Natural unordered contrasts stay separate from directed transplant pairs. Reporting T averages the two example orders before its matched retrieval comparison. No retrieval E analysis, output-selected denominator, donor-recipient normalization, significance gate or new uncertainty method.

## Runtime, timing and persistence expectations

- Calibration exactly5460 model forwards and29232 row-level numerical comparisons. Main cap bound147648 forwards; baseline first-step comparison rows768, and maximal patched P-repeat comparison rows573440. First use is identified by component/replacement key lists, B/L/dtype and hook mode rather than row IDs or tensor values.
- Cold100/warm2 with10 calls yields118 exact or120 under declared conservative overcount. Multiplying cold by10 is invalid. Missing recurrence timing must fail closed. Explicit25% margin includes all measured compute/I/O terms; startup and shutdown/headroom remain auditable separate terms.
- Main healthy journal writes3510 plus one emergency reserve; calibration healthy journal48 is distinct from48 filesystem benchmark writes. Attempt/terminal/progress/metadata/final/emergency counts must be verified by fake writers, including a caught stop. A crash after durable attempt but before terminal leaves all eight rows attempted-incomplete; progress cannot certify completion. Joining the full plan restores unattempted rows too.
- Inspect controls on generated-prefix steps and EOS-finished physical slots, original-prefix-only masks, compact immutable donor banks and assignment assertions for unselected coordinates. Full-component self controls cover all current valid positions, exclude READOUT replacement, and execute after P-repeat before forced append at0/63.

## Finite serialized-byte-bound adversaries

A finite field schema requires exact key sets and bounds for every nested list/string/number, including source paths, hardware names, timings, hashes, IDs, diagnostic messages, controls and reconstruction metadata. A representative payload or an observed calibration maximum cannot establish a ceiling. Freeze constructor hashes and six separate class ceilings.

Check actual canonical UTF-8 bytes, not character counts: non-ASCII multibyte text, quote/backslash/control escaping, negative signs, maximum integer widths and scientific float notation can exceed naive templates. Reject NaN/Infinity, Boolean candidate identities and unconstrained arbitrary extra keys. Raw/display text needs a proven tokenizer-decoding upper bound including64 tokens and any included stem/normalization; byte-token vocabulary length alone may not bound decoder cleanup or inserted separators without verification. Every control receipt must include its maximum64-step cardinality and full diagnostic schema. Final9344-row assembly includes every permitted row/provenance/status variant, not simply9344 times an average completed row. Protocol can dominate the metadata class.

At exactly ceiling bytes a write should pass; one byte over must stop before publication while preserving durable attempts and a bounded error record. Error handling itself must fit its frozen emergency/terminal bounds. Check actual fsync/atomic fresh-name behavior, all48 benchmark writes and first/recurrent timing separation. Calibration-only fake maxima must never be exported as scientific answers.

## Pending actual review

Await root's locked source/report/diff package, with implementation helper names and source hashes. Actual review will independently assess spec compliance and code quality in `task-1-review.md`, run focused CPU checks in both supported environments, and distinguish CPU evidence from unrun GPU numerical validity. No current readiness, implementation success or GPU-release claim follows from this preparation.
