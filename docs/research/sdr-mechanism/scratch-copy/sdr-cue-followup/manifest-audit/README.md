# Independent prospective input oracle

Status: **prospective, e14a92 provisional and final 2949214 committed rebind PASS**. See `final-committed-review.md` and `final-committed-rebind.json`. This is CPU-only input/source-binding evidence, not numerical calibration or GPU release.

`independent_oracle.py` imports only Python standard library and `tokenizers`. It never imports the new or old study scripts, transformer model classes, torch, or model weights. It reads the immutable parent protocol, the three original coarse-mask JSON files, and cached tokenizer/config metadata. No labels or outcomes are read.

Run from Alignment:

```bash
/sw/external/python/anaconda3/bin/python3.9 .scratch/sdr-cue-followup/manifest-audit/independent_oracle.py --expected .scratch/sdr-cue-followup/manifest-audit/expectations.json
```

To reproduce the JSON at a distinct audit-owned destination, replace `--expected` with `--write PATH`. Canonical JSON uses sorted keys, compact separators and literal UTF-8; the file adds one newline. Canonical content digest is `fa2a60fc28e9f095e8d2263e8df5ffc6504c9be5de9ffde6be51cfd2f8e1f099`; exact file SHA is recorded in `prospective-results.json`.

The derivation checks:

- Parent exact bytes `e0fc2da612fe08d29a9f913976e6e83341ef91b18405325356b6e49ad7ceeae8` and canonical scientific payload hash.
- Independent literal-shell/grammar rendering, ordering, tokens, offsets, structural roles/spans, answer continuations and cap/padding limits for all 384 main + 96 disjoint calibration-pool inputs.
- All 640 pairs independently reconstructed by input-factor reversal, original pair-ID hash recipe, exact two changed token IDs in the correct role, truth-status slots, preceding identical-token prefixes and identical donor/recipient scope boundaries.
- S32 intersection from D/H/F coarse files, C_S32 recreated with the old deterministic outside-head ranking, and exact parent tuple/hash agreement.
- 3,840 new intervention IDs `parentpair:family:site`, unchanged 384 baseline IDs, and ordered `pb-000000` through `pb-000527` batches. Family/site/task-axis grouping is explicit in every batch.
- Unique assistant header token sequence `[128006,78191,128007,271]`, exact character/token split, independent prefix-retokenization agreement, previous token user EOT `128009`, exhaustive disjoint early/tail/full scopes, and zero padding/generated-site masks. Main assistant boundaries are tokens 101–120; main total prefixes are 111–131 tokens, so cap64 fits L224.
- Every main E pair has identical pre-user token prefix; corresponding system-null position masks are bound for all inputs. All 48 family/site calibration slots are reconstructed from the fixed eight original slots, with exact recipient/donor identity and E-system null positions.

`expectations.json` includes full frozen parent main inputs, independently reconstructed pairs/families/interventions/batches, all 480 boundary/mask maps and 48 calibration identities. Original main rows are copied only after independent rerender/token/metadata agreement. This deliberately preserves every inherited field rather than relying on a production projection.

The new literal calibration ID namespace is not yet specified; exact identities/factors/order are frozen here without inventing calibration IDs. Production comparison will be read-only and use explicit schema projection if new boundary fields differ in name. It must verify actual values and all IDs/order, not merely row counts. Neither prospective PASS nor regenerated JSON claims that the production implementation has passed.

## Provisional production comparison

`compare_manifest.py` compares production JSON directly with the unchanged prospective expectation file. It imports no production code. The explicit position-schema projection changes names only: independent `assistant_token/user_token` become production `b/user_b`; independent `system_null` becomes production `system`. Every index and its hash is checked; all 480 independent B×L row-mask equivalents are verified. Parent main rows remain exactly unchanged, not merely unchanged after dropping fields.

```bash
/sw/external/python/anaconda3/bin/python3.9 .scratch/sdr-cue-followup/manifest-audit/compare_manifest.py
```

The default invocation binds provisional protocol file `e14a92b42310720eb7f6e80491c1320e3eb77ddd939b38b09c7e147250b90654`, science `fd0bf5f1415b4ea951d6396753b64ad7c0061d883eeca28960b55a9bf9423b6e`, spec `b06fc61df13c9c64563d7043fd06502658fc32539cb659639038812b6c1a0cbe` and `UNCOMMITTED` source. That exact artifact passed **1,292,995 recursive comparisons**, including 104 forced/natural calibration rows, three system-E no-op rows, actual rubric/spec bytes, all 63 source bindings and preservation of all 57 inherited source files. Calibration literal IDs were checked using explicit separate namespaces and fixed recipient/donor/slot identity.

`provisional-comparison.json` is the historical receipt for this exact uncommitted snapshot. Production may change for review fixes afterward; the current-source portion of the default command is expected to fail after such edits. Do not overwrite this receipt with a later snapshot. Rebind later manifests with explicit `--protocol`, `--sha`, `--science`, `--spec-sha`, `--code-commit` and a distinct `--output`. Reuse the unchanged input expectation core; do not regenerate it from production.

`checker_selfcheck.py` verifies rejection of eight independently corrupted fields after re-signing outer manifest hashes, including factor, donor, site, order, boundary, rubric and source corruption. These checks are validation of the independent comparator, not production runtime tests.
