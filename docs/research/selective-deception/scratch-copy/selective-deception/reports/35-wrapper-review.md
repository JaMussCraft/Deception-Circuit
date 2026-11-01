# Independent bounded wrapper feasibility review

Verdict: no important actual bug found; no code change requested before the bounded intact-only diagnostic. Review is source-only, not evidence that real-model outputs pass either capability floor.

Reviewed canonical protocol v2, issue05, standalone implementation, focused CPU tests, Slurm wrapper, and the reused exposure, result-store, context, native generation/EOS paths. No jobs, real models, GPU/API/network activity, notebooks, git operations, or source changes performed. Existing worker evidence reports nine focused tests passing in both supported environments and actual CPU preparation; this reviewer did not repeat those checks.

Verified contracts:

- Exactly the frozen 16 validation clusters, two D/H policies, and two fixed views produce 64 generation rows, original 32 first and repaired 32 second, without outcome-dependent selection. All rows are intact, have no donor and no identity/control scoring; 96 tokens each bounds generated tokens at 6144.
- Original prompts are preserved verbatim and retokenized against frozen IDs. Repair is exactly SYSTEM_HEADER + canonical repair_text + two newlines + unchanged remainder. Existing facts, labels, policy and refusal permission remain byte-identical; both views retain the empty assistant start.
- Pilot validation checks scenario/source relations and semantic exposure exclusions including corrupt-stream truth flips; wrapper preparation independently reconstructs actual exposure/endpoints from the frozen Stage1 manifest and compares them with persisted provenance. Slice disjointness with training and all Stage1 semantic exposures is asserted before run.
- Source hashes cover standalone script, Slurm wrapper and reused Python dependencies. Canonical protocol/pilot bytes, Stage1 input, initialization artifacts and model/tokenizer snapshot identity are frozen and revalidated. Runtime fingerprint includes full snapshot file hashes, packages, Python, hardware, tokenizer, settings and policy; ResultStore rejects changed identities before loading a model or reusing results. Exclusive writer lock and explicit resume protect the append store.
- Empty mask mapping produces selected=None, so native generate_row enters all_gates_open; no knockout mask or donor-score path runs. Existing native generate/EOS resolution, cached greedy decoding and EOS/cap handling are reused for both views. All 64 persisted outputs are required before anonymous export.
- Slurm wrapper stops on unavailable conda or failed mgnp activation, fixes thread counts and deterministic CUDA workspace, uses local/offline model dependencies, removes paid-service keys, requests one GPU for 30 minutes and disables requeue. Root must preserve the external budget/launch reservation check; no launch was performed here.

Reviewed SHA256 values:

- wrapper_feasibility.py: b385cfef5132dddd3df59168e6c22268bf76f005d8f131e89b5c7b5f0c8c9272
- wrapper_feasibility.sbatch: 6184ed2c8d313a1609ef842020c56e4274f7a24725f0da8e027ecf9dea7fb666
- protocol-v2-feasibility.json: e5f6d58d6524ecad59338b4fdd6c36ff9e6444e3e50ab0ef06c5b6f986aa68b0

Scope boundary: annotation and wrapper routing remain root decisions after fresh blinded annotation. This review approves no optimizer, training, adaptive prompt search or expanded model execution.
