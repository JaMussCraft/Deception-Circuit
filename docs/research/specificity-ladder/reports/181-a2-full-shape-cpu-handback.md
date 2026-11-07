# Hand-back 181: A2 full-shape CPU proof packet

Agent: worker. Status: handed-back. Packet requires independent review and a root dry-run before a CPU allocation.

## What changed

New packet `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-plan178/full-shape-cpu181`. Manifest SHA-256 `7e3f46a554fd558bcaf7ea085d7d85ad1b5b697ee023b3ce69aed36a41384503`; `shape.py` SHA-256 `82574a4143c8f1f05f14d01b45a19fcab66dd68db34ce29817914660e0a9802c`. `request.json` proposes 4 CPUs, 16 GiB, no GPU, 15 minutes, with 840-second child limit and 15-second grace; this is an estimate based on the accepted 85-second CPU audit plus tokenization and shape work, not a reservation or completion guarantee.

The script pins the 511-source/four-link snapshot, G3, accepted177 verdict, bank file and native payload separately, then invokes original context/live, complete-stage, bank and tokenizer validators. It constructs full and prefix expected rows and positive keys, then uses original `a1.batches`, `task_batches`, `_rows` and frozen donor maps to report task/condition/stream distributions and parent batch shapes, group/operation coverage, supported and unsupported map coverage and reconstructed per-operation forward/padded-token/squared-token exposure. It preserves unsupported diagnostic rows; no fake model or scorer is invoked. Native `score_cell` singleton views retain parent batch width; positive-control pairs use the larger parent width. The output includes actual CPU peak RSS, local filesystem availability and prefix file size plus explicitly labeled row-linear storage orientation.

## How verified

Local `test_shape.py` was written first; its initial RED log shows the expected missing new module, not a behavioral regression. Tiny pure accounting tests ran on both interpreters:

```bash
PYTHONDONTWRITEBYTECODE=1 /sw/external/python/anaconda3/bin/python3.9 -m unittest -v test_shape
```

```bash
PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python -m unittest -v test_shape
```

Both exited 0 with two tests. Both interpreters parsed the Python files with `ast.parse`; `bash -n run.sh` passed. These checks do not exercise authentic data, full domain, or all structural reconstruction branches. Local logs are preserved in the packet.

## Execution evidence

Local pure unit tests only: base and mgnp exit 0, 2 tests each; no Slurm job or model. No actual full/prefix row counts or memory measurements have been produced by this packet. The manifest above pins its files and frozen source reference is commit `50e947bb852613e3a270082651f2bd1b7bb0c525`.

## What is NOT done

No long CPU proof, actual allocation, scheduler submission, model/forward/score, effect-file contents or effect aggregation, git, RS, SSH, or source/bank modification. Forward exposure reconstructs native control flow and needs independent audit; it is not walltime proof. No rigorous full GPU memory or full serialized-output bound is available. Consequently neither the proposed 4.75-hour GPU window nor 4 GiB output allowance is validated by this unexecuted packet.

## Open questions

Independent review should scrutinize frozen-map coverage, singleton parent-padding, positive-control overrides, source/hash identity and reconstruction against the unchanged native loops before root dry-run. If the CPU run or review finds a missing native grouping or unsupported case, stop and report the gap; do not infer a bound. Bank content SHA `17045db1a43c7a4e53f31edb2e2719367b2efc1665dc6081880dc45f122ec1a1` differs correctly from bank file SHA `a8afbd51a994a6346d1bb8c832b68cab0ea42c83a195c22a29aae4016723e00b`.
