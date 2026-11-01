# Resumed sandbagging auditor compatibility

Analysis-only copy `transfer-v5/audit-sandbagging-resumed.py` descends from the unchanged report157 auditor `audit-sandbagging.py`. Original SHA256 remains `1306669c401cedf65c9dee80ca087ae955c57f7e8498585999e0711e0051ee32`; report157, queued source/launcher/receipts, shared core, budget and old artifacts were not edited.

The copy explicitly accepts reviewed schema1 purposes `frozen-sandbagging-only` and `frozen-sandbagging-generation-segment`; other purposes/unreviewed receipts still fail. Segment mode additionally validates root decision/one-H200/positive bounds/source provenance, immutable file bindings, exact argv digest and original sandbagging argv plus common resumed output/checkpoint/NEW-batch limit, evaluator workdir, and hash-bound passed proof002 (exact tokens/order/donors/corrupt/masked;8/2new batches). Existing frozen cohort/source/runtime-proof/mask/grader checks remain. Mutable judge cache and ledger are not added as whole-file bindings. Output protection also covers the new argv/cold-proof inputs.

`audit_core` and its existing `self_test` are AST-identical to the original: frozen50×5/native1024, donor/cohort/proof/grader/coherence/coverage/headline checks are preserved. An incomplete/missing block has no headline and exits2; the new receipt purpose never makes a segment efficacy-complete.

CPU regression9/9 PASS in both environments: mgnp6.91s and base6.84s (`/tmp/v5-resumed-audit-{mgnp,base}-final.log`). Covers actual reviewed old/new receipts; unsupported/unreviewed/schema/argv/proof/limit refusal; unchanged audit core; missing-state partial block refuses headline; missing inputs still emit an incomplete report. Initial missing-copy tests and a missing-input regression were observed failing before implementation/fix. No model/API/GPU/jobs/git/budget operations.

| New artifact | SHA256 |
|---|---|
| `transfer-v5/audit-sandbagging-resumed.py` | `2d9a942ab1c0531e107d08ee9d9712e8d018b9de6be3e1218e85137449223727` |
| `transfer-v5/test_audit_sandbagging_resumed.py` | `b7294582f48ced61707dcb8e189fe4bdb4d1d2aedd6610d41e4c48483cf110c4` |

After a complete block exists, root can run:

```bash
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/audit-sandbagging-resumed.py \
  --benchmarks-json /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/eval5-sandbagging-resumed/cells/self/sdr/interchange/benchmarks.json \
  --receipt /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/sandbagging-segment-001.receipt.json \
  --output /projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/sandbagging-resumed-audit.json
```

Use the relevant root-reviewed segment receipt if later segments complete the block. The runtime proof defaults to `frozen_runtime_check.json` beside the block; the separate cold-resume proof is read from the receipt. This preparation makes no completeness, efficacy or live-job claim.
