# Source-only fresh witness batching implementation plan

> For agentic workers: use executing-plans and test-driven-development after root accepts this plan and creates an isolated candidate. No implementation is authorized by this document.

**Goal:** Reduce redundant source ancestry/resolution work within one real guard refresh while retaining every dependency and fresh full-byte obligation.

**Architecture:** Add a private source-only batch scanner in `a3_source_validation.py`, keeping the original authority witness and its immutable expected identities. Compile an immutable index of existing witness rows and complete lexical/target routes, then replay every required row using fresh filesystem observations; avoid rebuilding common parent paths for each root. Continue hashing every original file observation in the initial narrow change. Preserve the existing static provenance scans before/after the byte check and all live protection/grader/authority calls.

**Tech Stack:** Existing Python/pathlib/os/hashlib; no external service or serialized cache.

**Spec:** Root's residual-profile diagnosis scope and immutable f5 source; raw `mask-profile.json`, `edge-profile.json` and function profiles in this directory.

## Global constraints

No cross-refresh digest/stat/TTL reuse. No skipped ancestor, symlink, directory membership, completion marker, original parent, missing-path, grader glob or file-byte checks. No guard-call/cadence reduction, public authority change, ledger/lease/cap change, inventory/scientific coverage change or original direction-runtime/A1 dependency edit. Current default/explicit/new file-backed registry checks and actual grader_registry remain unchanged on every refresh. No prospective cap fit claim.

## Review focus

- Same-byte external aliases at any lexical/target ancestor must fail.
- File replacement or mutation during a batched read must fail, including equal-size data changes.
- Root overlap and directory membership preserve exact original witness rows and ordering.
- Shared-prefix reuse must be confined to a single coherent scan; closing checks must catch changes after a prefix was observed.
- Legitimate unrelated atomic registry updates still revalidate through the existing real current-registry path.

## Minimal ownership and API

Own only the existing source-validation helper and its focused tests, subject to root authorization. Proposed private `_check_source_file_witness(witness, scan_plan)` validates the genuine existing `_FileWitness` type/process and compares a freshly constructed identity tuple to its existing sealed identities. Keep original authority `_make_file_witness` and original authority/workload APIs unchanged. `scan_plan` is an immutable route/index derived under existing mint-envelope stability. Include every original root, witness-row path, and symlink literal/target route in fresh pre/post provenance coverage; roots alone cannot cover symlinks nested inside a directory witness. All original symlink and target metadata rows remain required; it grants no authority and retains no reusable digest evidence. Include its RAM and initialization in existing consumed fields and actual stats traversal. Do not introduce a new general cache abstraction.

## Tasks

- [ ] First write focused equivalence/negative tests. Compare exact original and batch witness rows on regular files, overlapping directories, completion markers, duplicate aliases, chained/relative links and missing dependencies. Retain untouched B1/B2 and existing mutation/reinitialization isolation probes.
- [ ] Implement source-local replay of the original immutable witness rows. Freshly check the complete compiled lexical/target route graph at the existing before/after provenance phases, sharing common prefixes only within each phase. Freshly stat all row identities, enumerate every directory membership and reconstruct exactly the existing root-row ordering. Hash every original file occurrence initially, including the repeated interpreter: this deliberately leaves byte obligations unchanged. Bind every opened regular file with descriptor fstat against the expected identity before and after its full read, plus after-read/closing path and route checks so sharing cannot hide mid-scan replacement or new links. Preserve directory child names, file identity/bytes, symlink literal/target identity and cycle rejection. Do not cache metadata between start and closing provenance phases.
- [ ] Add changed-file, same-size content, parent link, same-byte alias, link-target ancestor, membership, disappearance and mid-scan replacement regressions. Force mutation after a prefix was inspected and after an earlier file was read; closing checks must reject. Assert no digest is reused across refreshes. Keep original raw prepared/in-memory/registry negatives and consumed initialization/peak/projector tests.
- [ ] Run focused dual-interpreter suites and hand back exact candidate hashes/diff. Root freezes and independently reviews before genuine new-source preparation. Reproduce one controlled real-input profile/clean refresh sequence on that freeze, including initialization/retained-RAM accounting and separate-copy mutation negatives. Compare path-call reduction and preserved byte counts; stop if any fresh-binding/protection rejection occurs.

## Limits and decision gate

The evidence supports redundant path work, not a complete cap solution. The edge witness has no duplicate static file bytes; mask only duplicates the interpreter. Thus byte deduplication is not the first proposed change. Current registries/grader work is small and stays untouched. Even successful path batching retains substantial byte/open/close cost plus unchanged guard multiplicity. Root should accept implementation only as this narrow, reviewable experiment; actual residual budget feasibility remains a separate measured decision. A broader I/O-backend redesign or modified authority implementation is outside this plan.
