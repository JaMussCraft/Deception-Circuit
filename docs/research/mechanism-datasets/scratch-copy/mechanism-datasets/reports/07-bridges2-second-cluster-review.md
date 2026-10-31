# Ticket 07 review (Phase A)

The code-review skill's two sub-agents ended without returning a report. The implementer therefore did both
axes by reading the full diff: the modified `scripts/evaluate_circuit.sbatch` and every new file. No
`CODING_STANDARDS` file exists. Standards come from `agent-brief.md` (shell, Slurm and test rules),
`CONTEXT.md`, the conventions of the existing sbatch files, and the Fowler smell baseline.

## Standards

- **Fixed: unquoted rsync filter globs in b2.sh.** `--exclude=*.lock`, `--include=evaluations*/***` and
  `--exclude=*` were unquoted. Bash would have glob-expanded them against the current directory. All three
  are now quoted, and the tests still pass in both envs.
- **Judgement: the wrapper keeps the old activation line.** `evaluate_circuit.sbatch` still has no
  `|| { echo "Environment initialization failed"; exit 1; }` guard. The brief's wrapper rule asks for one.
  The guard is left out on purpose, because the ticket requires identical Delta behaviour.
  `bridges2_smoke.sbatch` does use the guard.
- **Judgement: Duplicated Code.** The block that loads the profile, activates the env and sets HF_HOME and
  the offline flags appears in both `evaluate_circuit.sbatch` and `bridges2_smoke.sbatch`. It is about ten
  lines. Extracting it would add a third sourced file to the wrapper, so it was left. Extract it if a third
  wrapper needs the block.
- **Judgement: the secret filter is a substring heuristic.** `check_manifest_path` refuses any path
  containing `key`, `token`, `secret` and similar. It can refuse an innocent path, which is the safe failure.
- **Tests.** The tests are CPU only. They run bash through subprocess with stub `python`, `conda` and
  `ssh`, and they never reach Slurm or the network. The wrapper test asserts a literal trace of the
  pre-change behaviour and passed against the unmodified wrapper before the edit.

## Spec (acceptance criteria of issue 07)

- **Profiles and wrapper: done.** "`scripts/cluster/delta.env` ... and `scripts/cluster/bridges2.env`
  exporting [the eight variables]; `scripts/evaluate_circuit.sbatch` sources ... and behaves identically ...
  when `DC_CLUSTER` is unset." The wrapper has no `--dry` flag, and the hard stop forbids running
  evaluate_circuit.py. The proof is therefore a stub run of the original and the new wrapper on the same
  arguments. The `#SBATCH` header, stdout and stderr diffs are all empty.
- **b2.sh: done, with deviations.** The ticket says "code via `git pull` on Bridges-2". The script uses
  `fetch` plus `merge --ff-only`, which is equivalent and refuses a diverged clone. It adds `unpack-env`,
  which Phase B needs. `fetch` adds `--checksum` and `--backup`, beyond the ticket's `--update` and
  `--ignore-existing`. A Bridges-2 clone gives tracked files fresh mtimes, so `--update` alone could
  replace an older, uncommitted Delta edit. Default fetch is limited to `evaluations*/` under the manifest
  run dirs, the two suite roots, and the logs.
- **Environment: partial.** The conda-pack is built and verified on Delta. It unpacks, `conda-unpack`
  works, and Python 3.12.13, torch 2.11.0+cu128, transformers 5.13.0, datasets 5.0.0 and accelerate 1.15.0
  import. The tarball has no secret-looking names. The pinned fallback `requirements-bridges2.txt` is
  written. The h100 smoke job (`torch.cuda.is_available()` True, plus the parser check) is Phase B.
- **Snapshot and wikitext: partial.** A simulated HF_HOME holding only the three manifest dirs loads the
  tokenizer, config, all 4 shards and wikitext with the hub off, and no token is present. Copying them to
  Bridges-2 is Phase B.
- **docs/bridges2.md: done.**
- **Ledger: partial.** The `bridges2` section exists with SU rate 2 and allocations 07: 1 h and 06: 12 h.
  The smoke job reconciliation is Phase B.

## Open items for Phase B

These can only be settled with `--test-only` on Bridges-2.

- The header's `--gpus-per-node=1` and `--mem=64G` combine with the command-line `--gpus=h100-80:1`.
  GPU-shared may refuse either.
- The `--rsync-path="mkdir -p ... && rsync"` call needs the transfer host to accept that command.

## Phase B review (2026-10-24)

The implementer reviewed the Phase B diff on top of d6e0581, covering both axes. Live use on Bridges-2
found three defects that the Phase A tests could not see. All three are fixed and pinned by tests.

1. **Typed `--gpus` next to the header option.** Bridges-2 rejected the typed `--gpus` next to the
   header's untyped `--gpus-per-node`. `DC_GPU_SPEC` now uses `--gpus-per-node=h100-80:1`, which replaces
   the header option.
2. **The submit environment did not reach the job.** Bridges-2 sets `SBATCH_EXPORT=NONE`, so the variables
   did not arrive, and smoke job 49772768 failed. Submissions now pass `--export=ALL,...`.
3. **`fetch -a` rewrote Delta metadata.** It changed permissions and mtimes on identical tracked files.
   Permissions were restored, and fetch now copies no metadata.

A fourth problem, the transfer host refusing a shell in `--rsync-path`, broke transfers before any data
moved. Target directories are now made through the login host.

- **Standards:** no new smells. Judgement: delta.env no longer reproduces the pre-profile wrapper exactly,
  because the orchestrator asked for the BLAS pin. That is documented in delta.env, the test and the
  handback.
- **Spec:** all seven acceptance criteria are now met. The environment path is conda-pack, recorded in the
  docs and handback. Code reaches Bridges-2 through the clone. Data went by rsync and was verified by
  checksum.
- **Open item:** after the commit and push, the Bridges-2 clone needs `b2.sh sync-code`, because it still
  holds d6e0581's profile. That is harmless for submissions, which pass the allocation explicitly.
