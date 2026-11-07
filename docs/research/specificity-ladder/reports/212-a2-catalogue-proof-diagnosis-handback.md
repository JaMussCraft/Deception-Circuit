# Catalogue proof diagnosis212

Status: handed-back

## What changed

Diagnosed the catalogue conflict and wrote a narrow successor correction proposal; no production file changed. The historical input manifest explicitly labels its four catalogue rows historical and requires current snapshots separately. Adapter capture instead requires original size and SHA for all 422 ordinary entries before capturing the four current catalogues. All four exact paths overlap. The primary directions catalogue now differs, so a valid fresh transfer cannot satisfy that historical predicate.

## How verified

Ran a brief read-only reproduction that extracts and executes the actual capture ordinary-input loop for only the four catalogue rows. The historical manifest still matches its config pin. Primary directions is 24,115 bytes against historical 23,245; current SHA is 508092548c76deef7dc3339cec990d1a62cbd455ac0117e8ada215755a591ada versus historical b1cf09a06662438569e7f5f670bc85fe3de5e3d2436f375a64ae308b73694a6d. That row raises the exact guard assertion; the other three currently pass. This is a minimal predicate reproduction, not execution of full capture, native owning guards or the proof. Read existing host bindings, transfer closure, entry/worker call order, native catalogue normalization and accepted reviews 192, 197-r2 and 208-r2.

## Execution evidence

Local Python 3.9 predicate reproduction exited zero after recording the expected assertion. It read four catalogue rows and found one conflicting row. No scheduler job, remote action, model, scoring, graph, full suite or resource proof ran. Scientific counts, cluster terminal state, scientific baseline and run_manifest commit are not applicable to this diagnosis. Exact source pins, the reproduction output and actionable proposal are under W/.superpowers/sdd/plan-a2-catalogue-proof-diagnosis212 in input-pins.json, reproduction.json and proposal.json.

## What is NOT done

No correction is implemented or accepted. Preserve historical config/manifest, all original rows, previous packets and frozen native source. No current catalogue was overwritten and no historical input was re-signed. No resource, GPU or genuine CPU-proof admission follows. Controller review207 remains independent and still awaits root-provided full-suite receipts.

## Open questions

Implement only in a distinct successor: enforce original size/SHA for exactly 418 noncatalogue files; require a separately authenticated current map for the exact four lexical catalogue paths. Extend the existing transfer-attestation witness with those rows and stable actualDelta capture, remote hash and Delta reread equality. The host already authenticates this reference; forward its path/hash to proof_guards and require matching current bytes at every capture. Today that witness is not passed to the worker, so merely excluding four rows would be insufficient.

Retain source and alias closure, every native owning/protection check and worker before/ready/after equality. Keep all four original manifest rows as historical provenance; distinguish their old hashes from current expectations in root route verification and transfer evidence. Use no basename or directory carve-out. Bind witness to the accepted successor packet and actual job, reject missing/tampered witness, and never adopt newly observed hashes. Detailed regression cases and the exact change surface are in proposal.json. Focused dual-environment correction tests and independent successor review are required; prior adapter acceptance explicitly assumed unchanged proof guards.
