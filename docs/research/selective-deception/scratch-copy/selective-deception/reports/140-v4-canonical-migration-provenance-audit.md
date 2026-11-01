# Actual canonical migration and annotation bridge audit

October21,2026. **PASS. Report139's migration/provenance requirements are satisfied on the actual artifacts.** This was a read-only structural/hash audit. No private-map JSON was decoded; responses and initial labels were not read semantically. Private bytes were handled only by the already-reviewed opaque digest-slot transformer and hashing, with no nonpublic values emitted. No helper, GPU job or annotation was changed.

Independently verified:

- Original packet manifest still has SHA`1c53b442cbef11f12ace3fb60967a175e31090db2678694b8bba5c92e8f53b7c`. Canonical manifest SHA is`d517fee97c2782622c01eb837919ae7327a50aaa698f53b0a1bf823b8efb855a`.
- All eight public files(factual packet, six chunks and rubric) are byte-identical between original and canonical directories and match their original hashes. Every original label file matches the preconversion original-source record:12files,704declared judgments across two352-view streams.
- Reapplying the reviewed bytes-only transformer to original opaque private bytes exactly reproduces the actual canonical private bytes. It checks352named slots and changes seven. Its non-digest byte identity and inverse-recovery proof match the migration receipt; inverse SHA equals the original private SHA. Both private file hashes match their respective manifests; canonical private permissions are0600.
- Removing only the explicit migration metadata, restoring the original public-digest dictionary and original private-file SHA makes the canonical manifest exactly equal to the original. Converter/source/proof metadata match root's migration authorization and report139hash. Frozen exporter, adapter and classification sources still match the manifests.
- The original assignment record precedes migration authorization(20:26:30.935UTC versus20:26:44.593UTC); the bridge follows at20:27:21.162UTC. All12bridge entries reproduce the original stream/actual-worker/chunk/label bindings exactly and connect them to identical copied chunks and valid canonical sidecars. Sidecars bind unchanged label hashes, canonical view digests and the canonical manifest, with no worker overlap between the threeA and threeB sources.
- The bridge explicitly states that annotators saw **original paths**, that root performed metadata rebinding, and that no new judgments were created. Original A02/A06sidecars remain present and valid against their original manifest/chunk/label bindings; they were not replaced by the canonical sidecars.
- Actual collation binds exactly those12canonical sidecars and original label files. Its content hash/source hash and all public bindings verify. The233agreed-clear and119disputed ID sets are disjoint and cover all352views. Dispute-reason counts agree with recorded reasons. The119-view fresh-adjudication manifest has exactly the disputed IDs, matching canonical view digests and valid file hashes. Final-label freeze remains false and the private-join boundary remains unpassed.

This verifies preservation and provenance, not factual correctness of labels. I did not recompute agreement categories from label contents or inspect model responses. Fresh adjudication, identical-view consistency, complete final assembly and root final-label freeze remain required before private joining.

Reviewed provenance SHA256s:

- Original assignments:`7c5796b12b422af8724c84710df66078d172de37977065a4f59209e74b47a30f`.
- Annotation bridge:`00965ff99a0a19b4afea127d8289a3dc8c14056ebf53756a7f8738a3a76fefcb`.
- Collation:`65c30d058106adb5db6600c97c72f3cf35bd77dd30f2d13bf5694bb6475c645a`.

GPU/runtime/reservation figures remain root's accounting record; this audit did not query Slurm or alter them.
