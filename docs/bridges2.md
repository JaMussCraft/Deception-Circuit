# Bridges-2 (PSC) as a second GPU cluster

Bridges-2 runs evaluation jobs that Delta dispatches. Delta stays the canonical copy of code and results.
Code reaches Bridges-2 through `git pull` of the pushed branch. Data is rsynced from Delta, and results are
rsynced back to Delta. Every transfer starts on Delta.

## Rules

- **Delta is canonical.** Edit code only on Delta, push, then `b2.sh sync-code`. Never edit or commit on
  Bridges-2. Results count once they are fetched into the Delta checkout.
- **One GPU type.** Use only `GPU-shared` with one H100 80 GB (`--gpus-per-node=h100-80:1`), and keep a whole suite on it. V100 cannot
  run the mgnp torch build (no sm_70 kernels, no native bf16). Results are not bit-exact with Delta's A40,
  A100 and H200 runs, so re-run one Delta reference cell on Bridges-2 as a drift control before trusting a
  suite.
- **No secrets leave Delta.** Never copy `~/.bashrc`, `$HF_HOME/token` or any API key. Jobs load the copied
  HF snapshot with the hub switched off (`HF_HUB_OFFLINE=1`, `HF_DATASETS_OFFLINE=1`,
  `TRANSFORMERS_OFFLINE=1`). EVAL 5 needs OpenRouter judges, so it does not run on Bridges-2.
- **Accounting.** Bridges-2 GPU-hours go in the `bridges2` section of the compute ledger, separate from the
  Delta cap. An H100 GPU-hour costs 2 SU.

## Layout

| what | Delta | Bridges-2 |
|---|---|---|
| repo | the mechanism-analysis worktree (`DC_REPO_ROOT` in `scripts/cluster/delta.env`; `DC_DELTA_REPO_ROOT` overrides it) | `/ocean/projects/<alloc>/swong2/Deception-Circuit` (git clone; `sync-code` checks out `DC_B2_BRANCH` or `--branch`, default `mechanism-datasets`) |
| HF cache | `/work/nvme/beto/swong2` | `/ocean/projects/<alloc>/swong2/hf`, holding only the Llama-3.1-8B-Instruct snapshot and the wikitext caches |
| env | conda env `mgnp` | `/ocean/projects/<alloc>/swong2/envs/mgnp`, unpacked from `/work/nvme/beto/swong2/envs/mgnp-conda-pack.tar.gz` |
| Slurm logs | `logs/` | `logs/` in the clone, fetched to Delta's `logs/bridges2/` |

`<alloc>` is the charge id that `projects` prints on Bridges-2. It goes in `DC_B2_ALLOC` in
`scripts/cluster/bridges2.env`. b2.sh refuses to act while it is the `__ALLOC__` placeholder. `$HOME` on
Bridges-2 (`/jet/home/swong2`) holds only 25 GB, so everything lives under `/ocean`, which is not backed up.

## Cluster profiles

`scripts/cluster/<name>.env` exports `DC_ACCOUNT`, `DC_PARTITION`, `DC_GPU_SPEC`, `DC_ACTIVATE`,
`DC_HF_HOME`, `DC_HF_OFFLINE`, `DC_REPO_ROOT` and `DC_TIME_DEFAULT`. `scripts/evaluate_circuit.sbatch`
sources `scripts/cluster/${DC_CLUSTER:-delta}.env` after it changes to the submit directory. With
`DC_CLUSTER` unset it behaves exactly as before profiles existed.

`#SBATCH` lines cannot read variables, so the wrapper's header keeps Delta's defaults. Any other cluster
passes account, partition, GPU option and time on the `sbatch` command line, and `b2.sh submit` does this.

Bridges-2 login nodes set `SBATCH_EXPORT=NONE`, so a variable set before `sbatch` never reaches the job.
Smoke job 49772768 failed on exactly this. Every Bridges-2 submission therefore carries
`--export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=<alloc>`, which is what `b2.sh submit` writes. A suite
generator that builds its own sbatch lines must add the same option.
Inside the job, the profile decides only three things: the activation command, `HF_HOME`, and the offline
flags.

## Opening the SSH masters

`~/.ssh/config` on Delta defines `bridges2` (bridges2.psc.edu, login and Slurm) and `b2dtn`
(data.bridges2.psc.edu, transfers). Both use ControlMaster sockets in `~/.ssh/cm/` that persist for 12 h.
Open each master once by hand. Each asks for the PSC password.

```bash
ssh -fN bridges2
ssh -fN b2dtn
ssh -O check bridges2 && ssh -O check b2dtn
```

The master process lives on the Delta login node where it was opened, for example dt-login04. Run b2.sh on
that same node, because the socket in the shared home does not work from another login node. b2.sh never
authenticates. It checks the master first and runs every ssh with `BatchMode=yes`, so a closed master is an
error rather than a password prompt.

## Dispatch and fetch

Every subcommand takes `--dry`, which prints the commands and runs nothing. `-n` passes `--dry-run` to rsync.

```bash
scripts/remote/b2.sh sync-code                 # clone or fast-forward branch mechanism-datasets on Bridges-2;
                                               # after a force-push it moves the branch to origin's head (reset --keep)
DC_B2_BRANCH=mechanism-analysis scripts/remote/b2.sh sync-code   # another pushed branch (or: sync-code --branch NAME)
scripts/remote/b2.sh sync-data --what all      # model + wikitext caches, packed env, manifest run dirs (via b2dtn)
scripts/remote/b2.sh unpack-env                # untar the env, run conda-unpack, print the package versions
scripts/remote/b2.sh submit --test-only --script scripts/cluster/bridges2_smoke.sbatch --time 00:15:00
scripts/remote/b2.sh submit --script scripts/cluster/bridges2_smoke.sbatch --time 00:15:00
scripts/remote/b2.sh submit --time 02:00:00 -- --circuit d=<run_dir> --task sdr_v2 --suite-name <name>
scripts/remote/b2.sh status [JOBID...]         # sacct on Bridges-2, for ledger reconciliation
scripts/remote/b2.sh fetch [--ignore-existing] [REPO_RELATIVE_PATH...]
```

- `sync-data --what runs` copies the paths in `scripts/remote/b2_manifest.txt`. Add the all-MLP operand and
  the nopressure stand-ins there once ticket 06 builds them. The manifest refuses absolute paths, `..` and
  anything that looks like a credential.
- `fetch` with no paths brings back `evaluations*/` under every manifest run dir, the suite roots
  `outputs/_suites` and `outputs/_launch_mechanism_v2/evals`, the component-analysis cells
  `outputs/_analyses/mechanism-analysis-*` (git-ignored, so a fetch is their only way back), and the Slurm
  logs. Nothing else under `outputs/_analyses` is touched. It never deletes. It
  compares checksums, keeps any Delta file newer than the Bridges-2 copy (`--update`), and saves a Delta file
  it does replace as `<name>.pre-b2fetch`. Pass `--ignore-existing` to keep every Delta file that already
  exists, which suits immutable cell outputs. Fetch copies no permissions, times, group or owner from
  Bridges-2, so identical Delta files stay untouched. New files get Delta's default group permissions.
- The model load takes about 8 minutes per job from /ocean: 458 s in the smoke job, on a cold cache. Pack
  many cells into one job rather than one cell per job.
- `suite.json` and `summary.json` written on Bridges-2 record absolute `/ocean/...` run dirs
  (`evaluation/circuits.py` `norm_run_dir`). Delta-side merges that match run dirs against a Delta-path
  manifest, such as `merge_shards.py --manifest`, must compare repo-relative paths. Alternatively, do the
  merge on Bridges-2 before fetching.

## Environment

The preferred path is a conda-pack of mgnp: Python 3.12.13, torch 2.11.0+cu128, transformers 5.13.0,
datasets 5.0.0 and accelerate 1.15.0. Packing needed `ignore_missing_files`, because pip had overwritten
conda's setuptools 82.0.1 metadata. `conda-unpack` must run once after extraction, and `b2.sh unpack-env`
does this. Jobs activate the env with `source <prefix>/bin/activate`, with no `module load` and no
`.bashrc`.

The fallback is `requirements-bridges2.txt`, a `pip freeze` of mgnp. Install it into a fresh Python 3.12.13
env with the cu128 index, as described in that file's header.

## GPU request and host-side numerics

`DC_GPU_SPEC` on Bridges-2 is `--gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G`. It was settled
with `sbatch --test-only` on 2026-10-24.

- **Use `--gpus-per-node`, not `--gpus`.** The wrapper header carries Delta's untyped
  `--gpus-per-node=1`. Adding `--gpus=h100-80:1` next to it fails with "Invalid GRES specification (with
  and without type identification)". The typed `--gpus-per-node` on the command line replaces the header
  option instead.
- **CPU and memory match the Delta header.** The spec asks for 1 core and 64 GB. GPU-shared defaults to
  63,000 MB per GPU and caps cores at 12 per GPU. Charging is per GPU-hour, at 2 SU on H100.

Both profiles export `OMP_NUM_THREADS`, `MKL_NUM_THREADS` and `OPENBLAS_NUM_THREADS` as 1. Every Delta
launcher already exported these values, so CPU-side math is the same on both clusters.

## Transfer host

data.bridges2.psc.edu runs rsync without a shell, so a `--rsync-path="mkdir -p ... && rsync"` call fails
with "mkdir: unrecognized option '--server'". b2.sh therefore creates target dirs through the login host,
which mounts the same /ocean. The smoke job also prints `nvidia-smi` and the driver version. torch+cu128
needs a recent driver, so read the driver version first if CUDA does not initialise.

## Relocation

The user reports that Bridges-2 goes offline on 2026-11-09, but PSC's own pages do not confirm a date. PSC
has announced a move to a CMU datacenter without giving one. Fetch results after every stage, and treat
anything still only on `/ocean` as at risk.
