# V6 CPU panel preparation

Candidate `panel.candidate.json` contains176 cases:32 distinct SDR scenarios, each D/H/F/I (128 rows), and16 supplementary FAR scenarios, each D/H/F (48 rows). SDR discovery and validation each contain16 scenarios, four per designation-polarity × item-polarity cell. FAR has four scenarios per cell. Only the frozen **clean** recipient stream is used; saved capability evidence retains both-stream results. Each variant reuses its V5-assigned independent validation neutral-H **clean** donor. There are44 unique family/donor IDs. No selected SDR recipient scenario appears among SDR donor scenarios.

The SDR intersection is84 IDs/80 distinct scenarios, cell IDs19/14/25/26 (identity1/identity2/inversion1/inversion2). Selection sorts canonical entity + unordered-item-pair scenario, then source ID; fills discovery first, then validation, skipping previously selected scenarios. All nonselected SDR and FAR IDs are recorded. A shortage raises an error rather than reducing quotas. No fresh outcome can trigger refill. Two scenario keys occur in both families (Aldrix Platform board/chip and humidity/vibration); this is disclosed and does not make FAR an independent replication or an I control.

All rows were previously exposed during V5; these are mechanism development/internal validation partitions, not pristine heldout confirmation. SDR I eligibility comes only from the already-filtered primary directive inversion Arrow dataset, checked by ID against its filter report: kept=true, both choices=b (the builder's I target), matching h scores and both target margins≥0.7. Requested I label comes from the audited Arrow target, checked against frozen D's false-label token; H/F target truth. HI is never substituted. Saved SDR D/H/F margins and I/filter evidence are included in provenance. FAR has no matched capable-I claim.

Sixteen source paths are SHA256 bound: original V5 prepared/proposal/masks, New23/New30 exports, inversion Arrow/config/filter/doc/builder/pool/clause forms, tokenizer/config and model config/generation config. The frozen model identity also retains revision and all original weight-file hashes. Builder SHA6aacfde804edc9603e56c627a88f5b5cfb450133b1315814a518e48d6a89e207 matches inversion config; root independently supplied source commit a0fae76f0f131bd3e125111982ee98b0e0dd5306. No whole-source-worktree cleanliness claim is made. No pickle reader, model inference, network/API call, GPU job or notebook execution is used.

Mask geometry is32 layers×32 query heads, head_dim128. Counts are New23=23, New30=30, OldD69=69, fixed Random30=30. Exact New30−New23 additions are L7H31,L8H10,L13H15,L13H23,L17H27,L19H13,L20H19. All supports are head pairs only. Recipient token lengths are SDR88–106/FAR84–98. All recipient/donor text is locally retokenized and checked; I targets/distractors are single leading-space tokens matching D labels. Runtime receives existing unpadded IDs and must independently compute final nonpad donor/recipient positions.

Interface agreed with runtime: schema_version1, sources path→sha256, geometry, masks new23/new30/oldD69/random30, added_heads, model_name, tokenizer_id, pad_token_id128009, model_identity with snapshot/revision/files, cases. Each case has case_id/scenario_key/family/split/variant, recipient_token_ids/donor_token_ids, requested_target_id/alternate_answer_id/truthful_id, recipient_text/donor_text, source_id/donor_source_id/donor_scenario_key/donor_stream, stratum and provenance. `load_manifest(path, verify_sources=True)` and `validate_manifest(manifest, verify_sources=True)` reject stale source bytes, malformed masks, labels and paired panels.

Exact CPU build command, from the selective-components-v6 worktree:

```bash
OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m component_analysis.selective_v6_manifest \
  --prepared /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/v2-prepared-frozen.json \
  --proposal /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/v2-inputs-proposal.json \
  --masks /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/frozen-masks.json \
  --inversion /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/data/datasets/sdr_v2_inversion/test/data-00000-of-00001.arrow \
  --inversion-doc /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/docs/research/mechanism-analysis/inversion-control.md \
  --output /projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v6/panel.candidate.json
```

The CLI uses exclusive creation and refuses overwrite. Root alone freezes/revises candidate receipts after independent review. Candidate SHA25644aa565297c2d9e435254eafcdb3bee8966e44f6b9182961be34ece0be4fd1be. Focused verification:11 tests in `tests/test_selective_v6_manifest.py`, both mgnp and base Python; tests cover fixed balanced/disjoint selection, deterministic cases, per-variant donor reuse, exact target/truth labels, mask difference, corruption rejection, source hashes and missing/duplicate/incorrect donor source IDs. These are environment-bound integration tests requiring the existing frozen data/tokenizer cache; no claim of portable synthetic fixtures or full-repository-suite verification. Root coordinates integration checks.
