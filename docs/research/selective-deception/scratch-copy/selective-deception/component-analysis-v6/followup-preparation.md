# Bounded V6 followup runtime handoff

Operative scientific sources are204 plus prospective205 and followup-selection-002.json; smoke001 intentionally retains selection001 ancestry. No pretrained model, GPU, API, network, Slurm submission, ledger change or git action was performed by this worker.

Final candidate is **followup-pack.candidate-002.json**, SHA256 `d985a50e64a2becd091bdc43f4033de3dcf86ac1737bf1b49aff4c80e0db12f2`. The earlier followup-pack.candidate.json is superseded and fails current deterministic reconstruction because it predates added original-donor capability metadata. Do not freeze or launch that old candidate.

32 new donor IDs/scenarios are globally unique; all16 SDR validation recipients retain the same pair across DHFI. Existing75-source neutral-H validation pool only, all V6 recipient scenarios excluded, own original donor excluded, exact204 seed/hash ordering retained. Eight exact-vocabulary bins were empty before global nonreuse.205 explicitly approves ordinal truth-slot matching and renamed ordinal_agree_New30 / ordinal_disagree_New30 states. Among the16/16 new arms, unordered answer-token-pair matches are0agree/1disagree; truth-token matches0/0. Every case and donor records construction item strings/token IDs, truth-slot, label strings/IDs, prompt length, source-record SHA and source ordering. Shared donor pair comparisons use recipient neutral-H prompt length; actual per-variant lengths are in each case construction metadata. No lexical-overlap field filters assignments.

The ten states are intact, original_New30, release_17, clean_rescue_17, self_rescue_17, ordinal_agree_New30, ordinal_disagree_New30, total_sender_13, path_Q27, path_Q26. Main64case variants/640rows; frozen smoke16variants/160rows. Smoke cases reappear in main and must not be double-counted or used to tune hypotheses. Fresh capability for original and both new donor arms is saved without substitutions.

Manual pp.Streams contains exactly all embedding/head/MLP clean component outputs, excluding READOUT_KEY. The sole corrupt output is a clean sender clone with its own-final recipient slice replaced by the independent donor's own-final slice. receiver_inputs freezes every other component output and captures final per-query-head pre-RoPE Q. readout_from_receivers writes only one chosen final Q and permits free downstream propagation. This is the direct residual→normalization→Q route, not all mediated paths; Q17H26 is a matched comparator, not a null.

Every live batch requires actual same-backend plain/no-op/core-self identities, full clean-bank replay, empty-sender capture/write, self-sender capture/write, clean-Q/self-Q write, false-position-mask identity, all-sibling-Q/all-position isolation, independently reconstructed total sender from the original donor and cached New30 self-rescue identity. Native full-vocabulary equality and fp32-readout equality are saved separately. Metrics retain requested/truth-oriented raw margins, full-vocabulary KL, probabilities/logits/argmax/correctness plus native argmax and native/fp32 agreement. No metric ratio, mask search or candidate selection is performed.

The runner verifies every candidate source and reproduces deterministic packaging on load. Live execution requires root status frozen, reviewed once-only output-bound receipt, Slurm CUDA/A40, BF16/SDPA, pinned nnsight0.7.0, frozen local snapshot/revision/tokenizer and every bound model file hash. Output dirs/files and receipt claims use exclusive create. Incremental rows/controls/capability are flushed/fsynced per batch; no overwrite, resume or automatic retry. Source bindings conservatively include all repository root, models and component_analysis Python sources, covering local imported dependencies without loading model modules on CPU dry runs.

Final source hashes:
- runner `bb822cb8e8c98b702e6d24a740dda8eefea744c2ab9e6138250ef7ae50351863`
- tests `1b6f79d5ce787772f73683e3fa152d48a99236a4d80a26ed8c7f3f7b463c4061`
- wrapper `40857744e3ca226d6705b20dc62e67b16c31791ef2310dd27832521ed59bd99c`

Verification: pinned mgnp focused four V6 test files37passed21.28s after the original-donor addition; base33passed4expected pinned-nnsight skips33.84s before that addition. Tests include real random tiny NNsight path/control composition and all ten runtime states. A broad repo test was stopped/bounded, produced partial progress only and is NOT a passing-suite claim; partial log remains /tmp/v6-followup-full-pytest.log. No further broad testing is needed for this change.

Actual final wrapper CPU dry-run exited0, using final candidate002 and producing followup-worker-dryrun-002/plan.json and followup-worker-dryrun-002.log. It verifies640planned rows/source/model identities without allocating CUDA or constructing a model:

```bash
bash /projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v6/followup-launch.template.sbatch \
 dry-run /projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v6/followup-pack.candidate-002.json \
 /absolute/new/output-directory
```

Root freezes candidate002 into a new pack, creates a fresh actual dry-run plan if bytes/status change, then supplies reviewed receipt fields pack_sha256, selection_sha256, runner_sha256, exact plan.code_hashes, mode, review_status=approved, output_dir, reservation_id, reserved_gpu_hours, remaining_gpu_hours_before. Smoke reserve≤.25h; main reserve≤remaining2.4h. The template arguments are `smoke|followup PACK OUTPUT RECEIPT`; root supplies actual sbatch --time/account/partition/stdout/stderr. No command here submits a job.

Cost forecast:38forwards per batch of4, including all technical controls (152forwards smoke,608main). Startup includes weight integrity checks and local model loading. GPU throughput is unmeasured: reserve smoke≤15min, then estimate main as measured startup +4×smoke scoring time +reasonable buffer within remaining2.4h. Do not multiply total smoke time including startup by4 or assume a15min main before measurement. Completion records startup, batch times, elapsed and peak allocated memory. Interpretation requires independent raw/scientific audit.
