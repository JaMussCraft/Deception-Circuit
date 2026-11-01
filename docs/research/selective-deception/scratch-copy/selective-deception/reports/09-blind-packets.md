# Stage1 blinded packet preparation

Implemented `analysis/prepare_blind.py` (159 production lines, Python standard library only). No actual generated outcomes were read during implementation or verification. No worktree source, GPU/model/API/job/git/notebook operations were performed.

From `/projects/beto/swong2/Alignment`, root can run this only after the full run finishes, substituting its completed run directory and a **new** output directory:

```bash
/sw/external/python/anaconda3/bin/python3.9 \
  .scratch/selective-deception/analysis/prepare_blind.py \
  --manifest Deception-Circuit/.claude/worktrees/selective-deception/outputs/selective-sdr-stage1/manifest.json \
  --run-dir /ABSOLUTE/PATH/TO/COMPLETED/FULL_RUN \
  --output-dir /ABSOLUTE/PATH/TO/NEW_PACKET_DIRECTORY
```

The run directory must contain `run.json` and `results.jsonl`. API: `prepare(manifest_path, run_dir, output_dir, *, expected_counts=(320, 84, 1848)) -> receipt_dict`. The keyword is solely a synthetic fixture seam; the CLI has no count override. Public files contain no semantic labels assigned by the utility.

Validation requires exactly 320 target generations, 84 declared unique donor references, and every one of the 1848 expected full-run records: 1088 target scores +320 target generations +84 donor references +356 intact donor scores. All record identities, kinds, embedded frozen input rows, row hashes, result hashes and run fingerprints must match. The external manifest content hash, run's embedded manifest and recomputed run fingerprint must agree. Duplicate JSON keys, duplicate/undeclared records, conflicting input rows, missing records, and an unterminated final JSONL line fail closed. Input failure occurs before output creation. Existing paths (including symlinks) are refused; files are exclusively created. The utility does not resume or repair logs.

Canonical hashing exactly matches `evaluation.selective_diagnostics`: sorted JSON keys, separators `(',', ':')`, UTF-8, `ensure_ascii=False`, `allow_nan=False`. Expected donor-score identity derivation reproduces the frozen runner's first-endpoint deduplication and labels. A source-AST-only comparison against `donor_diagnostics` confirmed all 1848 expected rows equal those of the frozen runner, without importing torch. The frozen manifest's canonical hash is `a73ec2195fef1b9591e3db6cce1c653b8601d4d46459011c898cbca08d22730e`.

Targets and donor references are shuffled together with `random.Random(0)`, then receive sequential anonymous IDs. Donor factual truth depends only on clean/corrupt stream: clean uses original H as truth; corrupt uses original D as truth, reverses the false alternate, and updates `scenario.honest_item`. Policy and `intended_label` never determine factual truth. Targets retain original H/D labels.

Generated artifacts:

- `public/chunk-00.jsonl` through `public/chunk-06.jsonl`: 404 records in chunks of 64,64,64,64,64,64,20. Only these files go to blinded annotators. Allowed public fields are `anonymous_id`, `prompt`, `ground_truth` (`scenario`, `truthful_answer`, `deceptive_answer`), `output`, and `quality` (`empty`, `cap_hit`, `termination`, `repetition_fraction`). Scenario fields are restricted to `entity`, `items`, `honest_item`.
- `private_mapping.jsonl`: anonymous ID to source row ID/kind, semantic cluster, source ID, condition, policy, stream, and view; root only.
- `hash_manifest.json`: full counts, seed/chunk limit, manifest/run identities, SHA256 of the exact bytes read from all three inputs, and SHA256/byte counts of public chunks and private map; root only. The manifest does not include its own hash; root can hash/freeze it externally. Input byte hashes document the snapshots used; authenticity still depends on root supplying the trusted frozen manifest/run directory.

Packet directories use mode0700; every generated file uses mode0600. There is no annotation, adjudication, condition scoring, generation filtering, or dropped denominator.

Verification (2026-10-18):

```bash
/sw/external/python/anaconda3/bin/python3.9 -m unittest discover \
  -s .scratch/selective-deception/analysis -p 'test_prepare_blind.py' -v
/u/swong2/.conda/envs/mgnp/bin/python -m unittest discover \
  -s .scratch/selective-deception/analysis -p 'test_prepare_blind.py' -v
```

Both: **7 tests passed** (3.9: 0.099s; 3.12: 0.121s). Tests cover all four donor policy/stream combinations, target truth preservation, public redaction, exact counts, ID determinism, joint role shuffling, independent artifact hash/size verification, file modes, refusal of incomplete runs even when all generations exist, duplicates/unknown/conflicting rows, result/run/row/manifest tampering, truncated logs, overwrite refusal, default full-count rejection of small fixtures, and a 134-record chunk-boundary fixture.

Additionally, created ephemeral synthetic results for every row in the actual frozen manifest, with the constant output `SYNTHETIC FIXTURE`; invoked the unmodified production CLI under both Python versions with default counts. Both produced exactly404 records and seven correctly sized chunks, all scenario truth fields agreed with truthful answers, and public chunks/private mapping were byte-identical across versions. Temporary synthetic files were removed automatically. No actual run outcomes were opened.

Source SHA256:

```text
aee4649c33ffaaf78e6cce02df8caa391cb6ddf88d531eb645e16151a4b0d010  analysis/prepare_blind.py
09e7a556149fb199be2ce08277fce3448554a226ac1a427b7fcd698de3ed2fba  analysis/test_prepare_blind.py
```

Root must independently check the utility before use and freeze annotation hashes before unblinding.

Root independent source review: PASS for this frozen Stage1 schema. Verified complete1848identity requirement, full manifest/run/row/payload hash checks, target+donor joint shuffle, corrupt donor truth AND scenario.honest_item inversion, public allowlist and separate private map,64record limit, refusal to overwrite. No actual outputs read or labels assigned. Source remains aee4649c33ffaaf78e6cce02df8caa391cb6ddf88d531eb645e16151a4b0d010.
