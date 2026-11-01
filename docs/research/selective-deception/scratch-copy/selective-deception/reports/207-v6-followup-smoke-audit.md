# 207 — V6 followup actual A40 smoke audit

PASS. Job23218961 meets the technical smoke gate. Proceed with the already frozen64-case/640-row main acquisition on one A40 under a new root-bound one-use receipt and10-minute reservation (1/6 GPU-hour), without changing hypotheses, donors, masks, heads or cases. This is a technical verdict; no followup effect has been used for selection or scientific interpretation.

## Raw completeness and binding

Independent read-only Slurm accounting reports23218961 COMPLETED, exit0:0,90seconds, one GPU on gpub020. Node inventory identifies gpub020 as NVIDIA A40. Header records BF16/SDPA, pinned nnsight0.7.0 and the same frozen model identity. The reviewed runner enforces A40 and validates frozen model file hashes before loading; this audit checked model-identity binding and execution evidence without rerunning inference or rehashing all weight shards.

The frozen pack is eb266afc19320bbb31739fa5bdb4251c003f9f903944f6b357c0ea73e9fdfd3c. It reconstructs successfully with the reviewed source and differs from approved candidate002 only by status=frozen. Selection002 hash is2a55b55570b5a6f9610ebe424480d3250057b3e8e27a84221834664034012a44. Runner remains bb822cb8e8c98b702e6d24a740dda8eefea744c2ab9e6138250ef7ae50351863; all40 code bindings match current bytes and plan/header/receipt. Receipt records source commit57c53ac539d55ae5c6bff67cdb5be31c2289e802. Its embedded header value, output-directory binding, approved smoke mode,0.25-hour reservation and consumed-once sidecar hash/job ID all agree. No receipt guard was reset.

The raw rows contain exactly the16 fixed smoke case IDs from the original four balanced validation scenarios, each once in each of the ten frozen states:160 unique(case,condition) pairs, no omissions or duplicates. Plan/header/completion counts agree. Row-wise source/scenario/variant/stratum/labels, original donor, complete frozen donor pair, recipient construction metadata and pack/selection/runner hashes agree with the frozen payload. Every saved numeric metric is finite. Separate native argmax/correctness fields remain distinct from fp32 margin/probability/KL metrics.

## Actual model technical proofs

All four four-case batches have all35 required exact flags true (140 batch-level flags total). Equality compares the full batch/vocabulary or all sibling Q slices, thereby covering every included case. Recorded maximum absolute native no-op/plain and fp32-self differences are0.

These include actual plain/native no-op/self identities; clean full-bank replay in native and fp32; cached New30 self-rescue in native and fp32; and, for both Q17H27 and Q17H26, empty-sender, recipient-self-sender, clean-Q, self-Q and false-position-mask native/fp32 identities plus intended Q-head/position isolation. Both independent total-sender reconstruction checks pass in native and fp32, including reconstruction directly from the original donor's own final slice. Saved recipient/donor positions independently equal each prompt's own last nonpad index; padding is excluded.

For all16 cases, self_rescue_17 has exactly the same complete metrics and native correctness/argmax fields as original_New30. The source-reviewed construction therefore has successful real A40 evidence for the manual recipient-shaped full bank, synthetic final-only sender, component clamps and final-only pre-RoPE Q write composition. H26 is still a matched comparator, not a guaranteed null. These proofs must also run on every main batch; smoke success does not waive them.

There are exactly48 fresh donor-capability rows: one original, one agree and one disagree record per included case. Their donor IDs match the unchanged frozen assignments and all saved metrics are finite. Capability is recorded without filtering, swapping or recipient refill. No paid judge or API is involved.

## Controlled prior-run consistency

Compared matching smoke intact/original_New30 cases with prior aggregate-validation-001 intact/new30 rows. All12 previously saved fp32 metrics match exactly in every one of the16 cases for each anchor (384 field comparisons total); maximum numerical delta0, no tolerance widening. This verifies consistency with the previous A40 data/donor/metric convention while the new full-bank/Q proofs validate the followup composition. No hypothesis was added from this comparison.

## Main runtime bound

Smoke Python elapsed69.636seconds, including51.046seconds for model integrity/load. Four scoring batches took5.472,4.365,4.226 and4.486seconds; peak CUDA allocation18,709,998,080bytes. Using the slowest observed batch for all16 main batches, plus measured startup and20seconds outer-process allowance, gives158.60seconds. The proposed600seconds provides a reasonable I/O/startup buffer and is comfortably below the remaining authorized envelope. No automatic retry is approved by this audit. Root must bind the unchanged frozen pack/source and exact main output path in the new receipt and reserve1/6GPU-hour before launch.

The four smoke scenarios are included again in the fixed main panel. Use main acquisition as the64-case scientific dataset, and preserve smoke as technical evidence; do not pool repeated rows as additional observations or use smoke effects to adjust the protocol. No science conclusion is made here.

## Artifact fingerprints

| Smoke artifact | SHA256 |
|---|---|
| plan.json | fa211cc1df766df34075696407f80ccc6dfa91334ef11e80b13164bdeed76254 |
| header.json | 709fca99346ef9a816b2ad3e692fadede0f902a8c747d613b6339a19df4f8368 |
| rows.jsonl | 5100333eeab7dec58f0188fada5501e24aa42f39d86a2d4d4a02b901fdad861e |
| controls.jsonl | 7213559c1c5d1ea89b72bf49152c697bc08fd454c6572590e7e5c4e41d673318 |
| donor-capability.jsonl | 690e1bfa89ed521fcedc0854ca313c35f2cb767313aa2258730a3b2dbe6424e8 |
| completion.json | 6d1856222353e0e2d887d892e0ee7a22fb9c6d61a84f5208ab8c5de2122d0c61 |

Audit performed only safe JSON/source reads, CPU reconstruction/assertions and read-only job/node accounting. No GPU inference, API call, job submission, source change or ledger change was performed by the reviewer. Only report207 was written in this audit.
