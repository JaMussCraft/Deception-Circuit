# A3 baseline context closure correction

Status: handed-back

## What changed

Created distinct immutable successor `.superpowers/sdd/plan/task23-green-r5` in the specificity-ladder worktree. Historical r4 and its failure receipts are untouched. The new baseline export adds exact ordinary copies of `docs/research/held_out.json` and `docs/research/directions.json`; it still has zero aliases. All 362 previously pinned baseline files, all candidate/oracle code, both test suites, the five-case attributable RED assertions, numerical/control fixture preflights, and 223-case GREEN contract are unchanged.

The small stdlib `closure_preflight.py` checks mandatory registry presence, content pins, ordinary baseline paths, the frozen grader, and any protected-set file reference before native imports. It rejects omitted, unpinned, escaping or hash-mismatched dependencies. It supplements the native validators and never patches them. `check_pins` invokes it before the existing runtime paths. Both current registries were traced against unchanged `dataset/user_inversion_pipeline.py::check_registry`, `component_analysis/a3_source_validation.py::_LiveRegistryState.refresh` and `component_analysis/ladder_pipeline.py::grader_registry`. Current protected sets are empty; temporary non-empty dependency fixtures exercise the closure rule.

`cpu.sbatch` names the exact absolute r5 observer and disables bytecode writes. The actual wrapper also works after relocation to a temporary spooled-batch pathname. Bounds remain 610 seconds for the RED supervisor, 600 for its pytest child, 90 for the oracle, and 2700 for GREEN. Resource proposal and original preflights remain byte-identical.

Exact SHA256 pins:

| File | SHA256 |
|---|---|
| r5 source-pins.json | `05b53e5f2b2c2d737782753cde63cb6c1b428038d71d7666c644777deb1184c9` |
| r5 run_packet.py | `4d4aee62a1b544db8a84dd53f1cb3a1e9544ab57deaeec2d89e31c8e05f816be` |
| r5 cpu.sbatch | `0d2991714ed8518644aab2c92abad581db65436319452348d7ad6e81b9ff9c7e` |
| r5 closure_preflight.py | `bc6e63f4600280347c695879a1ab41de5044b522b2c544dd25178986ea7419a7` |
| baseline runtime, unchanged | `66c33953dc8c61ed2292744a362d47f69e6cf565732fb3716402657cc80d15c5` |
| candidate runtime, unchanged | `aea07dbf153824f373be70629dd24edc28dd6566cafa5955f43c69fd1119ec90` |
| ordinary held_out.json | `801b24e37c3315a8e58aa2ad5007f7831822fc2636d1e61837ad3652c370425e` |
| ordinary directions.json | `f8c7dbb92f2edc509c7bb8e94624a5c8adabddd103a8c48db1cc59bd69a3c6b0` |
| transport-inventory.json | `c7892724d0501cadde3b5a723445106afc6d9350f65a8032cd1634bd04338871` |
| correction241.diff | `8ecb0e6d1d978d181a1221911266ee856f23d0296aa00cc2a3c61992f67f98a6` |

The full transport inventory provides 1116 regular-file virtual rows and the existing eight candidate/oracle alias rows. Baseline/candidate/oracle pin maps contain 364/364/362 entries. Candidate/oracle registry content pins refer to their existing aliases: root must preserve alias rows and target-file bindings rather than materializing those aliases as ordinary virtual files. Root supplies a distinct physical deployment/config and binding; inventory is proposed input, not a deployment receipt.

## How verified

Five stdlib unittest cases pass in each supported interpreter, including missing mandatory registries, an omitted path dependency followed by an unpinned dependency and then a complete closure, tampered dependency bytes, path escape and registry alias rejection. The initial helper regression failed before implementation because the helper did not exist; the actual native failure motivating the repair remains diagnosis240's preserved evidence. No native tests were repeated locally.

Tiny commands, with `P` set to the absolute r5 packet directory for readability:

```bash
/sw/external/python/anaconda3/bin/python3.9 -B "$P/test_closure_preflight.py"
/u/swong2/.conda/envs/mgnp/bin/python -B "$P/test_closure_preflight.py"
bash "$P/cpu.sbatch" --dry-run
```

Receipts are under r5 `evidence/tiny-verification.json`, both interpreter stdout/stderr files, `relocated-wrapper.json`, `relocated-wrapper.stdout.json`, and `static-verification.json`. The wrapper receipt records the actual relocated pathname and exact immutable observer. Successor Python files also parse through stdlib AST. All previous source pins and every unchanged packet member were compared against r4 bytes. The raw unified changed-file diff is `correction241.diff`.

## Execution evidence

This worker ran only short stdlib checks: five helper cases per interpreter, source hashing/AST parsing and observer dry-run. There were no native imports, scheduler calls, model runs or GPU activity. No r5 RED/GREEN runtime success, scientific baseline reproduction, resource measurement or numerical result is claimed. The intended native evidence remains five attributable `DID NOT RAISE` RED cases followed by all 223 GREEN cases per environment.

Historical Bridges-2 job 50316834 failed with exit 1:0 after 286 seconds according to root and diagnosis240: its first three RED cases failed on missing registry context and its last two produced intended `DID NOT RAISE`; GREEN did not run. Root cancelled Delta job 23620933 unstarted. These are retained historical failures, not successful r5 evidence. Exact source/failure records remain in r4 deployment234 `actual-50316834`, r4 `root-dispatch/cancel-baseline-closure240.json`, and `plan-a3/baseline-closure-diagnosis240/diagnosis.json`.

## What is NOT done

No independent successor acceptance, fresh full/native pytest, Slurm submission, remote staging/transport, config binding, source publication, Task4 closure, operational RAM/cold-warm measurements, BASE equality acceptance, numerical or GPU admission. No git, RS mutation, jobs, transfers, production scientific edits, extra agents or budget changes. Parent owns subsequent orchestration.

## Open questions

No new research decision is needed. Root should obtain exact successor review, rebuild a distinct Bridges transport config using the supplied inventory with all eight aliases, run the actual relocated transport wrapper dry-run, then run and independently audit the complete both-environment native packet on Slurm. A complete proposed held Delta base submission, copied from the prior accepted resource shape with exact r5 paths, is stored as an argument array and shell command in `evidence/proposed-root-command.json`. It retains the original account, CPU partition, project constraint, two CPUs, 32G and 59-minute limit. Root must check current usage/scheduler gates before any submission and inspect the held job before release. The mgnp transport is a separate root-owned deployment; no existing deployment234 artifact may be retargeted.
