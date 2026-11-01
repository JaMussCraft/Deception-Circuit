# Frozen Task 2 runner and whole-branch interface review

Reviewed 2026-10-18 by the independent runner reviewer, after root explicitly confirmed the implementation worker's file/report freeze. Base `9d9c2a93a93ebfcf30a06a06332e38007d0d64f9`; Task 1 commit `a842b7a8a3fc10bbd13e25e2b7c35db8950d983e`; Task 2 changes were not yet committed at review. Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/selective-deception`.

## Spec verdict: PASS

No Critical or Important finding. The frozen Task 2 implementation satisfies the bounded runner contract and preserves Task 1's scientific corrections. This is a static/CPU implementation verdict, not evidence of an experimental effect or permission to skip the root's full-suite and GPU-smoke gates.

- Core `(D&H)-m` and comparator `(D-F)-m` use leaf composition, exactly 43/33 heads, zero MLP membership and complements retaining all MLPs. The single seed-0 random mask preserves core counts layer by layer. Existing circuit resolver, evaluator, context, dual stream and generation engine are reused.
- The three selectivity masks consume the same frozen nonself H donor across D/H recipients; paired self-H remains sanity-only. Small order/format contrasts preserve this assignment. Task 1's independently reviewed selection is consumed directly; no outcome filtering or source reselection enters the runner.
- Recipient D/H logits, full-vocabulary probabilities, margin and vocabulary argmax remain separate from pairwise preference and generated deception. Intact donor diagnostics use donor-local original D/H answer identities and link back to recipient-local agreement. All four policy/designation combinations are covered. First-token scores on free-response prompts are not claimed to establish continuation validity.
- Canonical tokenization preflight compares the selected original D prompts and leading-space label IDs against the existing dataset loader and its exact prediction boundary. Shared-mask donor alignment is checked. Generation uses fresh per-call caches, intact donor continuations, frozen greedy/EOS behavior, and continuation-only tiling with disclosed EOS/alignment/tiling flags. Same-input generation and score anchors have explicit checks.
- The manifest, input rows, decoding, source/model/tokenizer/mask identities and runtime hardware feed strict persistence checks. Smoke is a work selector against the full manifest. Complete-line recovery, duplicate/conflict rejection and CLI writer locking prevent silent mixed or incomplete results. Completion requires all declared recipient, reference and donor-score records.
- Recipient blinded export exposes prompt/facts/output/quality without mask/condition/donor metadata; private mapping is separate. No semantic deception regex, paid judge, notebook or benchmark batch was introduced. Summary explicitly leaves generated deception pending annotation. Coherent refusal remains eligible success; quality flags and cap-hit do not assign semantic failure.

Actual frozen worker preflight: 1,088 recipient score passes + 356 unique intact donor score passes = 1,444 scores; 320 recipient + 84 unique donor-reference completions = 404 completions; 38,784 worst-case new tokens; 1,848 total result records. Smoke selects 40 + 24 score passes, 40 + 12 completions, 4,992 worst-case new tokens and 116 records. These counts were inspected from the JSON plans, not inferred from the nominal recipient grid.

## Quality verdict: PASS

No Critical or Important finding and no blocking maintainability concern. The change stays within the five authorized Task 2 files. The metrics extension is opt-in, uses already-computed logits, preserves aggregate behavior and avoids a second evaluator. The small frozen-row adapter and function boundaries fit the existing harness. Persistence fails closed on conflicting complete rows; cache discovery and absolute local snapshot loading stay offline. The wrapper requests one GPU, one CPU, 64 GB host memory and 15 minutes by default, disables requeue, and adds no retry/array/API path.

Verification evidence inspected: final focused suites **77 passed in mgnp (18.01 s)** and **77 passed in Python 3.9 base (23.06 s)**; implementation report records successful `bash -n`. Tests include real tiny-model no-op/nontrivial scoring, cached no-op generation and actual Session/EvalContext integration, plus meaningful persistence, mask, cost, token-probability, EOS and blinding contracts. The reviewer did not duplicate the full suite or run weights, GPU work, jobs, APIs or notebooks. Root is running the full suites against the separately recorded baselines.

## Whole-branch scientific interface verdict: PASS for the bounded smoke

Task 1's exhaustive prior review was not repeated. Its final condition/row schema was checked where Task 2 consumes it, including nonself donors, donor-local labels, semantic answer identity, generation reference joins and immutable selection/completeness. No interface mismatch found.

The following existing execution/interpretation gates remain material:

1. Prepare the production manifest after the final commit, in mgnp. Source revision/diff/code hashes and Python/package identity deliberately reject the temporary worker preflight manifest after a commit. Smoke and full resume must also retain the recorded GPU model/capability/CUDA identity.
2. Root must compare full-suite failures to baseline, reserve compute and complete scheduler test-only before launch. GPU smoke must establish the real BF16 score tolerance (absolute 0.02 on D/H logits), exact-token generation identities, nontrivial intervention activity and measured throughput before a larger run. CPU tiny-model tests cannot establish these real-model properties.
3. Annotate intact donor continuations separately from next-token diagnostics. Current public export has the 320 recipient completions; a small root-side export of the 84 unique donor references is sufficient. Frozen donor prompt text, stream/policy, cluster/source IDs and cluster labels provide the facts. For clean donors, truthful = original H and deceptive = original D; for corrupt donors, truthful = original D and deceptive = original H. Do not substitute `intended_label` for truth, because it combines policy with designation. Recipient annotations always use recipient facts regardless of donor validity, and no invalid donor or intact recipient is dropped.
4. Freeze semantic annotations before unblinding; report raw deceptive/n with all selected rows, primary/alternative views separately, and benign cost separately. One random mask and mismatched-content interchange support a bounded diagnostic, not a confirmatory dedicated-deception-mechanism claim.

## Reviewed source SHA256

Hashes were rechecked after the explicit worker freeze and match the files inspected during review.

| File | SHA256 |
|---|---|
| `evaluate_selective_deception.py` | `0842eadb54b5180b8131b16f7fe604aa20d92708706c1b19a0aa85f87cffc1f7` |
| `evaluation/selective_runner.py` | `31f48bb84ac0c86c6588f53de2c189506ab12df6d2c6e540585d188607059b27` |
| `evaluation/metrics.py` | `a55b70d8e9261b821880b83f53b12bfa30968243f10988e18096ca40e021a710` |
| `tests/test_selective_runner.py` | `1bede0f56486fa55f3790c7daa52ffca95b7ed7a069039c60c33c3f3ed9b104d` |
| `scripts/selective_deception.sbatch` | `d55c6d37538c4d5df1fde090f950002b502eaf91943fe40cea9e79b95de7b904` |
| Task 1 interface: `evaluation/selective_diagnostics.py` | `2c7c3d8f5714d316bedba21a13307956ed722510116143d9bfc61ce06383d127` |

Spec findings: 0 Critical / 0 Important. Quality findings: 0 Critical / 0 Important. No implementation edits requested.
