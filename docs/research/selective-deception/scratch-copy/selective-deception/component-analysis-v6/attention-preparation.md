# Bounded V6 descriptive attention preparation

2026-10-26. This is separate from the frozen causal pilot. No GPU job, pretrained model, API call, notebook, mask training, head selection, or path test was run by this worker.

The new `component_analysis/selective_v6_attention.py` uses existing `hooks.attention_weights`, capture/readout, and frozen core helpers. It does not modify any pilot dependency. Root reviews and freezes this module and its own execution receipt independently before attention GPU execution.

## Frozen scope and outputs

Deterministic lexicographic first two SDR discovery scenarios per designation-polarity × item-polarity cell, all D/H/I variants: eight scenarios, 24 cases. Every case records all 30 New30 query heads, totaling 720 raw head rows. No fresh outcomes affect selection. Discovery/validation remain previously exposed mechanism data.

Each row records own last actual prompt query index, original key indices, exact token IDs and tokenizer strings, weights, layer/head/case/scenario/variant, eager backend, GQA shared KV-group identity and row mass. Padded keys are excluded only after zero padded mass is checked. Finite, nonnegative, approximately unit mass is required. The manifest has no verified token boundaries; segment summaries are explicitly unavailable. No guessed clause/fact alignment, attention causality claim or candidate selection is produced.

Only selected last-query rows survive the shared hook call; immediately move them to CPU. Full eager attention matrices are temporary inside the shared helper, never written. One case and one requested layer per extraction pass bounds memory. CPU full-vocabulary SDPA/eager native and fp32 baseline logits are retained in one `baseline-NN.pt` per case for audit. `rows.jsonl` and `controls.jsonl` checkpoint after each case; `complete.json` appears only after all 24 complete.

For every actual case, run actual-SDPA clean/raw/no-op/self identity and repeat clean/raw/no-op/self on actual eager. Use all New30 keys for identity. Exact native and fp32 identity is mandatory, inherited from the core proof helper. Save native and fp32 full-vocabulary max/mean absolute drift, KL(SDPA||eager), requested-answer margins and argmax changes independently. SDPA/eager differences are reported, never treated as an identity claim. Every temporary eager switch uses `finally` restoration; the shared attention helper itself restores its prior backend. Completion requires SDPA restored.

## Receipt and launch boundary

Dry run verifies frozen source hashes and writes an exclusive new plan directory without loading torch/model/tokenizer. Live `--mode attention` requires Slurm GPU, pinned nnsight0.7.0, local offline frozen model/tokenizer snapshot plus every frozen model-file hash. Receipt binds exact mode, output directory, manifest SHA, own SHA, dependency hashes (self/core/hooks/manifest helper), source hashes and model identity, approved review, reservation ID, remaining budget, and reservation ≤0.25h. Existing `<receipt>.consumed.json` is an atomic one-use guard. All directories and artifacts use exclusive creation. No overwrite or automatic retry.

Actual wrapper CPU dry run succeeded:

```bash
bash /projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v6/attention-launch.template.sbatch \
  dry-run \
  /projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v6/panel.candidate.json \
  /tmp/selective-v6-attention-dryrun-20261026
```

It reports 24 cases, eight scenarios, 30 heads and 720 rows. This temporary plan has mode `dry-run`; root's approved live receipt must use mode `attention` and a distinct output directory. Freeze/review the current plan hashes immediately before launch. Wrapper template and independent review should be included in root's launch audit.

Root-only live recipe after independent review and receipt freeze:

```bash
sbatch --account=ROOT_CHOSEN --partition=ROOT_H200 --time=00:15:00 \
  --output=ROOT_NEW_LOG --error=ROOT_NEW_ERROR \
  /projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v6/attention-launch.template.sbatch \
  attention ROOT_FROZEN_MANIFEST ROOT_NEW_OUTPUT ROOT_ATTENTION_RECEIPT
```

Do not execute placeholders. Root alone reserves/submits once. No automatic scheduler submission is built into the wrapper. Pending GPU execution must demonstrate all actual-backend proofs; CPU toy proofs and V5 proofs do not substitute.

## CPU verification and cost

Tests were written before implementation and first failed because the module was absent. Initial base tests:10passed. Combined attention/core/manifest suites in mgnp:30passed, one dependency deprecation warning, including random CPU tiny Llama/NNSight attention, both backend identity paths and restoration. No pretrained loaders are used by that toy test. Base focused run and independent review results follow below.

Planned H200 envelope ≤15minutes (0.25reservedGPUh), pending root confirmation against measured pilot load/throughput: 24 serial cases, eight baseline/identity forwards per case plus one attention forward per occupied New30 layer. Estimate allows model-file integrity hashing + offline model load and hundreds of short forward-only passes, no generation. Timing is an engineering estimate, not measured attention throughput. If root's measured pilot loading/forward cost cannot fit, defer attention rather than auto-expand or submit a retry. Exact forward count can be read from frozen head-layer count; transient eager memory is limited to one case per layer call. Existing proof helper additionally retains the requested head activations only for that case, then deletes them before extraction.

Final base focused verification:28passed,2skipped (pinned nnsight integration unavailable in base). Final mgnp focused verification before metadata-only review improvement:30passed,1dependency deprecation warning. No full-repository test pass is claimed. Independent reviewer200 requested actual model/backend dtype/config/tokenizer provenance in the header; this is implemented. Attention module current SHA256: `b0cbd49fe927efd438cf476fc8e9c12b8ec7675de5482bd8d3adf79941ec8818`. The original dry-run plan predates that metadata improvement; root/reviewer must generate a fresh exclusive dry run before final receipt. Frozen panel has19occupied New30 layers, so the planned total is648 short forward calls (24×(8identity/baseline+19attention)).
