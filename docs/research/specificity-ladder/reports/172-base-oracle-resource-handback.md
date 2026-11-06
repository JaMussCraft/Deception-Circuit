# Hand-back 172: base oracle CPU resource successor

Agent: worker. Status: handed-back. Exact packet review is required before launch.

## What changed

New packet `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-optionA-plan/genuine-oracle-base-cpu-r3`. Manifest SHA-256 `fdebb58e74c75bdd83c3c616a496988e6dfb80a9a1c5fbcddda3a22181a925ef`; config SHA-256 `6e9c0de2ae7c208b8b0933f5ca3630cedcf6f655e35c7e947a90fee4addca58c`. Original r2 manifest remains `21122c2077c367c7ccf9b08f8b865f263b7dcba66bf0480af25e14757973ed4d`, with all its listed files matching.

Changed packet members versus r2 are `allocation_facts.py`, `config.template.json`, `supervisor.py`, `proposal.json`, and `manifest.json`; new `test_resource_packet.py` is pinned by the manifest. Logs are evidence only. `run.py` and `oracle_cpu.sh` remain byte-identical; `run.py` SHA-256 `4b696366f1e0808212feeff0772160472e630811af9ba8381ebce664c6651dca`.

Allocation remains 4 CPUs, 192 GiB, zero GPUs and one node, now regular `cpu` only and 4500 seconds; initial remaining must be at least 4400 seconds. The child limit is 4200 seconds with 15-second kill grace and 285-second nominal finish reserve. Root additionally authorized a fail-closed completion check: a child reaped at or after the child limit cannot get a COMPLETE marker even if it exits zero. This fixes an inherited loop race where `wait4` returned before the elapsed-time condition was checked. The 15-second kill grace remains unchanged. No science source or input pin was changed.

## How verified

In the packet directory, the pre-fix `red-base.log` records 4 tests, 2 failures from old 60-minute bounds. An initial misplaced import-only log was removed. The boundary-specific `red-boundary-base.log` records 1 test, 2 failures: fake normal exit exactly at and after 4200 seconds incorrectly produced COMPLETE. Following the fix, the following commands each exited 0:

```bash
PYTHONDONTWRITEBYTECODE=1 /sw/external/python/anaconda3/bin/python3.9 -m unittest -v test_resource_packet > green-base.log 2>&1
```

```bash
PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python -m unittest -v test_resource_packet > green-mgnp.log 2>&1
```

Each reports 9 tests. Fake allocation cases exercise accepted resources and rejection for wrong CPU, memory, GPU, partition, cwd, user, node, time limit, and insufficient remaining time. Fake-clock supervision exercises before-bound completion, exact-bound and late rejection, TERM at 4200, KILL after 15 seconds, and terminated child exit zero without COMPLETE. Fake child failures representing absent stream/postguard do not yield COMPLETE; static checks establish the unchanged real child places its RESULT after the stream, newline and postguard code. These fake failures do not independently execute the genuine builder or prove scientific output.

Both interpreters parsed each packet Python file with `ast.parse`; `bash -n oracle_cpu.sh` exited 0. A byte comparison checked unchanged `run.py` and wrapper; the predecessor manifest members were rehashed. Raw local test logs are in the packet.

## Execution evidence

Local fake/unit tests only; no Slurm job or scientific model run. Exit codes and test counts are above. Scientific rows and numerical baseline reproduction are not applicable. The packet manifest pins the source-independent harness and unchanged original config inputs; no new source commit is claimed.

## What is NOT done

No job submission, full genuine execution, candidate comparison, scheduler access, git, RS writes, or independent packet acceptance. This 75-minute boundary is a reviewed resource choice, not a completion guarantee. The supervisor trusts the unchanged child to produce RESULT only after its guards; the fake missing-stream tests simulate child failure rather than independently executing `run.py`.

## Open questions

Root should have an independent reviewer inspect the exact manifest, resource change, new deadline check, unchanged real child and actual launch binding. Default: no launch until that review and the ordinary usage and scheduler gates pass.
