# SDR session artifact inventory

Snapshot UTC: 2026-10-31T13:12:23.568699Z

Inventory only. No migration, git mutation, worktree removal, or experiment was performed. Root Alignment `.scratch/sdr-*` evidence was not traversed or changed; only these two report files are written.

## Preservation groups

| Worktree / relative root | Regular files | Bytes | Symlinks | Existing destination files |
|---|---:|---:|---:|---:|
| sdr-routing-pilot: `.superpowers/sdd/.gitignore` | 1 | 2 | 0 | 0 |
| sdr-routing-pilot: `.superpowers/sdd/completion-diagnostic-plan` | 9 | 206722 | 0 | 0 |
| sdr-routing-pilot: `.superpowers/sdd/plan` | 12 | 212731 | 0 | 0 |
| sdr-routing-pilot: `.superpowers/sdd/plan-sdr-cue-circuits` | 78 | 43733787 | 0 | 0 |
| sdr-routing-pilot: `.superpowers/sdd/plan-sdr-cue-followup` | 70 | 17450115 | 0 | 0 |
| sdr-routing-pilot: `.superpowers/sdd/plan-sdr-cue-probe` | 25 | 9011343 | 0 | 0 |
| sdr-routing-pilot: `.superpowers/sdd/plan-sdr-native-controls` | 553 | 112428158 | 0 | 0 |
| sdr-routing-pilot: `.superpowers/sdd/plan-sdr-native-sharding` | 1 | 10586 | 0 | 0 |
| sdr-routing-pilot: `.superpowers/sdd/plan-sdr-routing-validation` | 10 | 205403 | 0 | 0 |
| sdr-routing-pilot: `logs` | 23 | 209569 | 0 | 0 |
| sdr-routing-pilot: `outputs/_analyses/sdr-completion-diagnostic` | 373 | 680918742 | 0 | 0 |
| sdr-routing-pilot: `outputs/_analyses/sdr-cue-circuits` | 20 | 80133133 | 0 | 0 |
| sdr-routing-pilot: `outputs/_analyses/sdr-cue-positions` | 20 | 36845794 | 0 | 0 |
| sdr-routing-pilot: `outputs/_analyses/sdr-cue-probe` | 92 | 9171513 | 0 | 0 |
| sdr-routing-pilot: `outputs/_analyses/sdr-native-controls` | 506 | 242886617 | 0 | 0 |
| sdr-routing-pilot: `outputs/_analyses/sdr-routing-pilot` | 39 | 291203955 | 0 | 0 |
| sdr-routing-pilot: `outputs/_analyses/sdr-routing-validation` | 186 | 295544040 | 28 | 0 |

**sdr-routing-pilot total:** 2018 untracked regular files, 1820172210 bytes, 28 untracked symlinks.

| sdr-cue-h100: `.superpowers/sdd/.gitignore` | 1 | 2 | 0 | 0 |
| sdr-cue-h100: `.superpowers/sdd/plan-h100` | 40 | 18649029 | 0 | 0 |
| sdr-cue-h100: `.superpowers/sdd/plan-sdr-cue-circuits` | 1 | 6180517 | 0 | 0 |
| sdr-cue-h100: `.superpowers/sdd/plan-sdr-cue-probe` | 1 | 2986749 | 0 | 0 |

**sdr-cue-h100 total:** 43 untracked regular files, 27816297 bytes, 0 untracked symlinks.

## Interpretation and safe migration scope

The pilot has seven session-generated analysis trees: `sdr-routing-pilot`, `sdr-routing-validation`, `sdr-completion-diagnostic`, `sdr-native-controls`, `sdr-cue-probe`, `sdr-cue-circuits`, `sdr-cue-positions`. Preserve all files in these trees, including failed/calibration/test artifacts and annotations, with their original bytes. No session-generated shared-composition output tree is present here; that phase lives in existing Alignment-root scratch, which must remain untouched. H100 has no untracked analysis output tree.

The existing primary `outputs/_analyses/sdr-routing-pilot/` contains earlier CPU-launch evidence. Per-file destination checks are recorded in JSON; do not replace the directory. Existing legacy `sdr-first-run`/`sdr-dh-core` and baseline circuit outputs are tracked placeholders/files and are not new session results. No symlinked/shared model-weight or dataset inputs were found in either worktree scan. Never recursively copy primary baseline outputs, external model caches, or paths merely mentioned in frozen JSON.

Outside outputs, preserve pilot `logs/` (23 scheduler logs) and both worktrees’ `.superpowers/sdd/` trees (plans, source locks, review diffs/reports, CPU fixtures, freeze protocols, wrapper logs). Keep worktree provenance separated. Proposed destinations are explicit per item in JSON: output files keep primary-checkout relative paths; other evidence uses `.scratch/sdr-session-wrapup/preserved/<worktree>/<relative-path>`. This prevents the differing `.superpowers` freeze copies from colliding. No other untracked noncache files were found. Worktree `.git` pointer files are administrative and excluded.

The 28 pilot symlinks are pytest `*current` convenience aliases with absolute targets inside the pilot output tree. Preserve their literal link text and inventory it without dereferencing. They will become dangling after removal; the regular target directories are preserved separately. Do not silently rewrite historical symlinks or frozen absolute-path provenance. There are no H100 symlinks. Compiled Python/pytest/ruff cache directories are explicitly excluded and listed in JSON; retain them only if a full forensic snapshot is desired.

Original-worktree tests were stopped before this refresh. Structural and metadata checks found no changes from the preceding final snapshot, and no file changed during hashing. SHA256 now covers every inventoried regular preservation file. The earlier inventory had no source hashes, so this establishes the baseline for copy verification. The 60 Oct31 synthetic completion-diagnostic pytest fixture files (112,100,578 bytes) are explicitly marked in JSON and retained as evidence, not treated as caches.

## Non-overwriting procedure and verification

1. Re-inventory immediately before migration and compare source path/type/size/mtime to this snapshot; hash every listed regular source file. Use `lstat`/`readlink` and never follow links.

2. For each proposed destination, inspect every ancestor with `lstat` to reject symlink redirection. Create new destination files exclusively (`O_CREAT|O_EXCL`) or stage into a new uniquely named directory. For a preexisting file, require matching SHA256 before skipping; on any mismatch, preserve the incoming file under a separate collision namespace and report it. `rsync --ignore-existing` alone is insufficient verification. Never overwrite or delete destination evidence.

3. Verify a closed manifest for exactly the selected paths: regular file path/type/size/SHA256; symlink path/type/literal target. Verify every migrated source regular file has a matching destination and preexisting source hashes remain unchanged. Record destination-only files rather than deleting them. No weight hashing, notebook execution, or output regeneration is needed.

4. Confirm root `.scratch/sdr-*` immutable snapshots and frozen reports remain byte-identical using the root agent’s independent manifest. These files were outside this inventory’s read scope. Keep all worktrees until root confirms branch-bundle/source integration, preservation verification, and the user’s explicit safe-to-merge signal.
