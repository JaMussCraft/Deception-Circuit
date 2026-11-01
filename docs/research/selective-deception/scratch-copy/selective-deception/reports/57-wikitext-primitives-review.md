# Independent Task A review — 2026-10-19

Verdict: **PASS for Task A and the frozen actual token manifest; no blocking or material correctness finding.** This closes the independent primitives review only. It does not certify concurrent trainer/model/gate/selection changes or real-model numerical calibration. User-authorized training remains independent of the benign control's outcome.

Reviewed scope: `Deception-Circuit/.claude/worktrees/selective-wikitext/evaluation/selective_wikitext.py` and `tests/test_selective_wikitext.py`, against ticket06 Task A, final report52 section4, report54, and report51's API boundary. Final article-local preprocessing and both differentiable KL/NLL outputs supersede the old report51 concatenation/objective wording. No production source or test edits, model weights/inference, GPU, Slurm, network/API/install, notebooks, git, or nested agents were used.

## Exact reviewed identities

- Implementation SHA256: `b1e68a3b61ed4b560253dfd5a08a55e2df6b7c2810469ccb7f454344892fa65a`.
- Focused tests SHA256: `5f851e96fb70a5b12548d9fc2bb355d0723f995de25999d0ff23a6ed406ab2cb`.
- Actual manifest: `.scratch/selective-deception/sparse-wikitext-v2/wikitext-manifest.json`.
- Embedded canonical manifest hash: `dce0f346dd0381d2ee44ef0b1b5d849afab29230ff8afc1766836f4d23d882bd`.
- Actual manifest file SHA256: `8d6ddb4c3b3be50ac83804d6c542abe3115c742a53c18ac123afeb0c5f8d1b3a`.
- Train Arrow SHA256: `57947bc7b58df4b19662c0609cc30651bc84328dab5fd588860b752072911789`.
- Validation Arrow SHA256: `8e136ab7130c5fca602eb406ce2557967a974d901b53c4f2992f87b873e0fe5b`.
- Test Arrow SHA256: `2b8a3efac7b468cbe6432edba5f55c21e435d93873acc6727431f08d5ed328ea`.

## Verification evidence

Fresh focused commands from the worktree, with `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`:

- `/sw/external/python/anaconda3/bin/python -m pytest -q tests/test_selective_wikitext.py`: **19 passed**, 4.00s; one existing pandas/bottleneck compatibility warning.
- `/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q tests/test_selective_wikitext.py`: **19 passed**, 2.33s.

An additional independent CPU check loaded only local tokenizer assets and Arrow data. It rehashed all three complete Arrow files and the four tokenizer files listed in the actual identity, confirmed tokenizer class/vocabulary/BOS/EOS, and reconstructed article boundaries with a strict separate level-one heading regular expression. It tokenized article bodies independently of `build_manifest`, then reproduced all first32 train/16 validation/16 test eligible articles, source indices, first128 token sequences with the declared BOS replacement, body hashes, title hashes and masks. First/last titles were:

- Train: Valkyria Chronicles III / Trinsey v. Pennsylvania.
- Validation: Homarus gammarus / Capel Lligwy.
- Test: Robert Boulter / Ben Amos.

All selected document/content/token identity sets were disjoint across splits. All split-local donors were permutations with no self assignment and different document identities. The initial alternate review regex admitted whitespace at title boundaries and incorrectly treated subsection headings as article titles; tightening that review-only regex corrected the check. No production parser issue was found.

An independent nonuniform11-vocabulary tensor check compared both returned sums with direct `sum(exp(log_p)*(log_p-log_q))` KL and direct gathered next-token NLL formulas, then compared autograd gradients for **each** returned loss. Both values and gradients matched; every one of the127 predictive positions had finite nonzero gradients and the final unscored logit position had zero gradient. This supplements the suite's analytic two-token case and its KL-gradient assertion.

## Review conclusions and boundaries

The parser recognizes actual WikiText level-one article titles, omits section headings/blank rows, and never concatenates separate articles. Insufficient articles fail. Manifest construction verifies explicit local source hashes before tokenization, records article/token provenance, and validates canonical integrity and split disjointness. Iteration produces independent CPU LongTensor copies and split-local donor inputs; clean next-token targets remain the clean sequence.

The loss uses full vocabulary base-to-masked KL and empirical clean-token NLL over positions0..126 predicting tokens1..127, retains masked-logit gradients, rejects reference shape/device/detachment violations, and does not own objective hinges, schedule, model forwards, masks or gate state.

References are detached contiguous CPU FP32 full-vocabulary log probabilities with127 positions, actual-token base NLL summed in float64, token hash, fingerprint and content digest. Reads validate identity/digest/geometry/dtype/finiteness and return separately owned storage. Writes reserve an exclusive lock, refuse existing destinations, serialize to a same-directory temporary file, fsync then atomically replace, and clean normal-exception temporary/lock files. These satisfy atomic immutable-file publication under this API. Crash-left lock recovery and filesystem power-loss durability were not experimentally tested; no such failure was observed. Returned PyTorch tensors remain caller-mutable, while subsequent disk reads retain independent ownership.

`validate_manifest` checks embedded integrity rather than rereading original data; the separate actual-source reconstruction above supplies the source/token provenance evidence for this frozen manifest. Caller-provided complete model/numerical reference identity, checking cached token hashes against the requested block, and actual model reference-path equivalence remain integration responsibilities. No real reference cache was created or evaluated in this review. Full integrated suites and independent Task B review remain root-owned.
