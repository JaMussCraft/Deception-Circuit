# Ticket 07 handback

## Post-push sync (2026-10-24): the Bridges-2 clone is at e1ad804

- **Clone state.** `b2.sh sync-code` fast-forwarded the clone from d6e0581 to e1ad804, which includes
  ticket 06's ad067ff. Remote and local heads match, and the working tree is clean. The clone's
  `bridges2.env` carries allocation cis260361p, the settled GPU spec, and the BLAS pins.
- **Ticket 06 inputs.** `suite_v2.json` references 109 repo paths. Apart from the suite outputs not yet
  written, 15 are inputs: the six v2 run dirs, `operands/allmlp_nomb_v2`, the three nopressure stand-ins,
  `drift_control/sdr_coarse_D_260922-092742`, `_launch_format_control/allmlp_nomb`, `build_suite.py`, and
  the format-control D_hko reference knockout.json. 14 of them are tracked in git. Their 66 files have
  identical sha256 on Delta and on Bridges-2, so no `sync-data` was needed.
- **The one untracked input.** It is the drift control's Delta reference value,
  `outputs/llama-8b-instruct_sdr_coarse/.../evaluations_headsko/.../knockout.json`. It lives in the main
  checkout, with `source_checkout` set to `/projects/beto/swong2/Alignment/Deception-Circuit`. It is
  compared on Delta after fetch, so Bridges-2 does not need it.

## Phase B done (2026-10-24). The smoke job passed.

The Phase B edits are now committed as e1ad804, and the clone is synced to it, as described in the section
above.

Bridges-2 is set up under `/ocean/projects/cis260361p/swong2/`. Smoke job 49773269 printed SMOKE PASS.
The Phase B edits are uncommitted on Delta, so the Bridges-2 clone still runs d6e0581. Submissions work
from that clone because b2.sh passes the profile choice and the allocation in `--export`. After the commit
and push, run `scripts/remote/b2.sh sync-code`.

### Smoke job 49773269

| item | value |
|---|---|
| node | w002 |
| GPU | NVIDIA H100 80GB HBM3, sm_90, driver 610.57.04 |
| state | COMPLETED |
| elapsed | 761 s |
| software | python 3.12.13, torch 2.11.0+cu128, transformers 5.13.0, datasets 5.0.0, accelerate 1.15.0 |
| model load | 458 s from /ocean, cold cache |

- **CUDA:** `torch.cuda.is_available() = True`. The arch list is sm_75 to sm_120.
- **Offline loads:** wikitext loaded 4,358 rows offline. Llama-3.1-8B-Instruct loaded offline in bf16 and
  its next token was `'Paris'`.
- **Parser check:** all six v2 run dirs are present with config.json and active_nodes.json. The
  evaluate_circuit parser and resolve_cli check passed, and no evaluation ran.
- **Load cost for ticket 06:** at 458 s per model load, each job carries about 0.13 GPU-h, or 0.25 SU, of
  load overhead. Run several cells per job.

### Earlier attempt, job 49772768

It FAILED after 3 s with the error `/ocean/projects/__ALLOC__/.../activate: No such file`. Bridges-2 login
nodes set `SBATCH_EXPORT=NONE`, so the `DC_B2_ALLOC` set in the submit environment never reached the job.
`b2.sh submit` now uses `sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=<alloc>`. Its test was
updated.

### Settled GPU request

`DC_GPU_SPEC` is `--gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G`, checked with `sbatch
--test-only` on Bridges-2.

| request | result |
|---|---|
| `--gpus=h100-80:1` alone | accepted |
| `--gpus=h100-80:1` next to the wrapper header's `--gpus-per-node=1` | rejected: "Invalid GRES specification (with and without type identification)" |
| `--gpus-per-node=h100-80:1` (replaces the header option) | accepted |
| `--cpus-per-task=13` | rejected: maximum is 12 cores per GPU |

`DefMemPerGPU` is 63,000 MB. `--test-only` accepted both the smoke script and the evaluation wrapper with
the final spec. `DC_TIME_DEFAULT` is 01:00:00.

### BLAS pinning

Both profiles export `OMP_NUM_THREADS`, `MKL_NUM_THREADS` and `OPENBLAS_NUM_THREADS` as 1. Every Delta
launcher already exported 1: format-control, the coarse SDR wave, and ticket 05. `~/.bashrc` sets none of
them.

On Delta, this is the one deliberate change from the pre-profile wrapper. A job submitted through a
launcher sees no difference. A bare `sbatch scripts/evaluate_circuit.sbatch` now runs pinned. Before the
change it ran unpinned on 1 allocated core. Apart from the thread pin, the identity diff is still empty.

### Transfers, all from Delta

- **Directories:** the transfer host runs rsync without a shell, so `--rsync-path="mkdir -p .. && rsync"`
  failed with "mkdir: unrecognized option '--server'". b2.sh now creates target directories through the
  login host.
- **Verification on Bridges-2:**
  - The env tarball sha256 matches Delta's (`997c51c9...e2348d`).
  - All 4 model weight blobs match their content sha256.
  - File and byte totals of the three HF dirs match Delta.
  - No `token` or `.bashrc` is anywhere under the project.
  - The clone is clean at d6e0581.
- **Space:** /ocean shows 22 GB used of 1,000 GB.
- **Env:** `unpack-env` ran `conda-unpack`, and the env imports the pinned versions. This is the conda-pack
  path, not a rebuild.

### Fetch fix

The first live `fetch` checksum-matched the tracked v1 suite files under `outputs/_suites`, so no content
changed. It still applied Bridges-2 permissions and mtimes to 989 files and 548 dirs. Files went from 660
to 644 and dirs from 2770 to 755.

- **Restored:** permissions are back to 660 and 2770. The original mtimes of those git-checkout files are
  lost. git ignores mtimes and reports the tree clean.
- **Fixed:** fetch now uses `-rl --no-perms --no-times --no-group --no-owner` with checksum, update and
  backup. A local re-check shows identical files keep their permissions and mtime.
- **Live check:** a live `fetch -n` reports no change to any tracked file. The live fetch brought both
  smoke logs into `logs/bridges2/`, which git ignores.

### Ledger, `bridges2` section

| reservation | job | state | elapsed | reserved after reconcile |
|---|---|---|---|---|
| 07-b2-smoke | 49772768 | FAILED | 3 s | 0.25 GPU-h, 0.5 SU |
| 07-b2-smoke-try2 | 49773269 | COMPLETED | 761 s | 0.25 GPU-h, 0.5 SU |

Ticket 07 has committed 0.5 of its 1.0 GPU-h, which is 1.0 SU booked. The actual charge is about 0.42 SU.
`projects` still showed 200/200 SU right after the job, which looks like charging lag.

### Files to commit (Phase B, on top of d6e0581)

```
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/scripts/cluster/bridges2.env
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/scripts/cluster/delta.env
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/scripts/remote/b2.sh
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/tests/test_cluster_profiles.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/docs/bridges2.md
```

The `bridges2.env` change fills in the allocation, settles the GPU spec and pins BLAS threads. The
`delta.env` change pins BLAS threads. The b2.sh changes cover `--export`, directory creation through the
login host, metadata-free fetch, and the parent-only mkdir.

### Tests (Phase B, final code)

| env | full suite | after ticket 06's concurrent edits settled |
|---|---|---|
| base | the 8 baseline names plus ticket 06's b2.sh test | both files pass, 56 tests |
| mgnp | the 8 baseline names plus two ticket 06 tests | ticket 06's file passes, 36 tests |

- **The two ticket 06 tests.** They are the b2.sh submit-format test and the walltime-floor test. ticket
  06's files changed at 12:50 to 12:51, during the run. In the rerun, the b2.sh test passes against the
  final submit format, and the walltime test passes too.
- **Ticket 07 itself.** It adds no new failures. Its own tests are in
  `tests/test_cluster_profiles.py`, 20 tests, and they pass in both envs.
- **Notice to impl-06.** impl-06 was told about the `--export` change directly.

### Notes for ticket 06, updated

A generator that builds its own Bridges-2 sbatch lines must add
`--export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=<alloc>`. A prefix of environment variables is not enough on
Bridges-2. Routing through `b2.sh submit` does this.

---

## Phase A (2026-10-24)

Phase B needs the user to open both masters on the Delta login node where b2.sh will run. The implementer
works on dt-login04.

```bash
ssh -fN bridges2
ssh -fN b2dtn
```

After that, the orchestrator confirms. The implementer checks with `ssh -O check` and never prompts.

### Built

- **Cluster profiles.** `scripts/cluster/delta.env` and `scripts/cluster/bridges2.env` export the eight
  `DC_*` variables. In the Bridges-2 profile, the allocation is the placeholder `__ALLOC__`.
- **Wrapper.** `scripts/evaluate_circuit.sbatch` sources `scripts/cluster/${DC_CLUSTER:-delta}.env` after
  its `cd`. Only the body changed, and the header is untouched.
- **Dispatcher.** `scripts/remote/b2.sh` has the subcommands sync-code, sync-data, unpack-env, submit,
  status and fetch. Each takes `--dry`, and `-n` passes a dry run to rsync. Run dirs come from
  `scripts/remote/b2_manifest.txt`, which lists the six v2 run dirs. The all-MLP operand is not built yet,
  so ticket 06 adds its path there.
- **Smoke job.** `scripts/cluster/bridges2_smoke.sbatch` runs `scripts/cluster/smoke_check.py`. That
  script checks CUDA, the offline wikitext and model loads with a one-token generation, and the
  evaluate_circuit parser. The parser check only calls build_parser and resolve_cli and never runs the
  script. Its CPU path ran through the wrapper on the login node and printed `SMOKE PASS`.
- **Docs and fallback.** `docs/bridges2.md` and `requirements-bridges2.txt` are written.
- **Tests.** `tests/test_cluster_profiles.py` has 18 tests.

### Delta identity proof

The scratch script `/u/swong2/.claude/jobs/6e1f64bd/tmp/diff_wrapper.sh` runs the original and the new
wrapper. Both get a stub `.bashrc`, stub `conda` and stub `python`, the same submit dir, and the same
arguments.

```
== #SBATCH header diff (empty = identical)
(identical)
== job trace diff, stdout (empty = identical)
(identical)
== job trace diff, stderr
(identical)
```

### Environment package

| item | value |
|---|---|
| tarball | `/work/nvme/beto/swong2/envs/mgnp-conda-pack.tar.gz` |
| size | 5.56 GB |
| sha256 | `997c51c904c0dcb5d1baef131e87c7c4cd71c942e8a490c5ddae7048f8e2348d` |
| job | Delta CPU job 23156522, bimc-delta-cpu, COMPLETED in 3 min 27 s |

The job was resubmitted from 23156515 on beto-delta-cpu, which was cancelled while pending with a
projected start 4 h later. Packing used `ignore_missing_files`, because pip had overwritten conda's
setuptools 82.0.1 metadata. A local unpack test passed: `conda-unpack` ran and the pinned versions
imported. No secret-looking file is in the tarball.

### Rsync manifest

| source on Delta | size |
|---|---|
| `/work/nvme/beto/swong2/hub/models--meta-llama--Llama-3.1-8B-Instruct` | 15 GB |
| `/work/nvme/beto/swong2/hub/datasets--Salesforce--wikitext` | small |
| `/work/nvme/beto/swong2/datasets/Salesforce___wikitext` | small |
| the env tarball | 5.6 GB |
| the six run dirs, without history.json and train.log | small |

The run dirs are also in git at bd67758. The HF_HOME root, `~/.bashrc` and the token are never sources.
A simulated HF_HOME holding only these dirs loaded tokenizer, config, the 4 shards and wikitext with the
hub switched off.

### Tests

| env | result | new failures |
|---|---|---|
| base | 8 failed, 1705 passed, 58 skipped | none; exactly the 8 baseline names |
| mgnp | 8 failed, 1858 passed, 19 skipped | none; exactly the 8 baseline names |

After the last b2.sh edit, `tests/test_cluster_profiles.py` was rerun in both envs and all 18 tests pass.

### Ledger

A new `bridges2` section has `su_rate_per_h100_gpu_hour` 2 and allocations of 1 h for ticket 07 and
12 h for ticket 06. It has no reservations yet, and the Delta totals are unchanged. The CPU pack job is
recorded in the section's notes and was not charged as GPU time.

### Files to commit (Phase A)

```
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/scripts/evaluate_circuit.sbatch
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/scripts/cluster/delta.env
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/scripts/cluster/bridges2.env
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/scripts/cluster/bridges2_smoke.sbatch
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/scripts/cluster/smoke_check.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/scripts/remote/b2.sh
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/scripts/remote/b2_manifest.txt
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/tests/test_cluster_profiles.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/docs/bridges2.md
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets/requirements-bridges2.txt
```

Do not commit these other untracked items with this list:

- `outputs/_launch_mechanism_v2/evals/` and `tests/test_mechanism_v2_evals.py` belong to ticket 06.
- `outputs/_build_v2/` and the failed ser D dir `..._261021-140323` are untracked by design.

Both full suites ran before the last two small edits. Those edits quoted the rsync filter globs in b2.sh
and made `DC_B2_ALLOC` overridable in bridges2.env. After the edits, `tests/test_cluster_profiles.py` was
rerun in both envs and passed, and the identity diff was rerun and stayed empty. The smoke script's
"Paris" check is now printed as an observation rather than counted as a pass condition. No Python module
that the full suite imports changed.

### Notes for ticket 06

- **The interface contract grew.** Besides the eight `DC_*` variables, a Bridges-2 job needs
  `DC_CLUSTER=bridges2` and `DC_B2_ALLOC=<alloc>` in its submit environment. Submit every job through
  `scripts/remote/b2.sh submit`, or use the same prefix:
  `DC_CLUSTER=bridges2 DC_B2_ALLOC=<alloc> sbatch -A ... -p ... <DC_GPU_SPEC> -t ...`. Without the prefix,
  the job sources the Delta profile on Bridges-2.
- **The masters are per login node.** Open them on dt-login04, where this implementer runs b2.sh. A master
  opened on another login node will fail `ssh -O check` here.

### Phase B plan

1. Run `projects` on Bridges-2 and fill `DC_B2_ALLOC` in `scripts/cluster/bridges2.env`.
2. Run `b2.sh sync-code`, then `sync-data --what all`, then `unpack-env`.
3. Run `submit --test-only` for the smoke script. This settles the `--gpus-per-node` or `--mem` question
   and whether the transfer host accepts the mkdir that rsync runs first.
4. Add the ledger reservation for the smoke job.
5. Submit the smoke job with a 15-minute limit, then reconcile it against sacct.
6. Rerun the suites in both envs and hand back.

**Before step 2, the orchestrator must commit and push the ticket-07 files.** Bridges-2 gets its code from
the git clone, which includes the wrapper change, the profiles and the smoke script. Bridges-2 also reads
`bridges2.env` from that clone. `b2.sh submit` passes `DC_B2_ALLOC` into every job, so a clone that still
holds the `__ALLOC__` placeholder resolves the right paths. Commit the filled-in allocation with the
Phase B files.
