# Hand-back eighty-three: Direction artifact contract review

Agent: independent Codex reviewer. Ticket: Unit A of the direction integration plan. Status: handed-back.

Current disposition: findings A and B are closed by the scoped re-review appended below. This does not grant production admission.

## What changed

Review only; no production sources, tests, artifacts or research state were changed. The author report was not read. Comparison used the orchestrator-supplied original CPU baseline at a93b4cb, its two source files under `/tmp/a3-artifact-review83-baseline/`, and `/tmp/a3-artifact-review83.diff`.

Review report for the orchestrator's explicit file list:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/83-direction-artifact-review-handback.md`
- Primary mirror: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/83-direction-artifact-review-handback.md`

**Finding A, high priority: live checks reject the actual frozen local MMLU cache.** At `component_analysis/a3_direction_artifacts.py:244–248`, resolving a Parquet path before requiring containment inside the snapshot rejects normal Hugging Face blob symlinks. The fresh A1 parent's snapshot is `/work/nvme/beto/swong2/hub/datasets--cais--mmlu/snapshots/c30699e8356da336a370243923dbaf21066bb9fe`. Its frozen `all/test-00000-of-00001.parquet` is a symlink into the same repository's `blobs/74a41822ce7d3def56e1682f958469c04642a5336a5ce912fa375fdb90fb25d7`. The target exists and matches the parent's recorded hash, but lies outside the snapshot. The independent injected-fixture probe drives this exact valid source through `validate_live` and gets `changed cached utility source bytes`. A future production load therefore blocks on unchanged data. Require lexical containment of the manifest-relative path and explicitly permit the trusted local Hugging Face blob target with exact hash checking; retain traversal and arbitrary-target rejection. Add a realistic cache-symlink regression, since current fixtures use regular files.

**Finding B, medium priority: numeric bundle identity is optional outside three hard-coded kinds.** At `component_analysis/a3_direction_artifacts.py:51–60`, only readout chunks, direction rows and direction shards require a profile. At `component_analysis/a3_direction_artifacts.py:69` and `component_analysis/a3_direction_artifacts.py:128`, caller expectations are a subset, with no mandatory scientific identity schema. Independent probes publish/read an `a3_direction_fit` axis with `injected=False`, no numeric profile and `expected={}`. A flat `a3_readout_chunk` containing commit and design hashes can also be reused with only `expected={'numeric_profile': profile}`, omitting both lineage expectations. Exact bytes do not distinguish a scientifically unrelated but intact cache. This is an intrinsic reader/writer gap, not a missing future model-stage invocation.

Require a production scientific bundle schema and complete consumer identity, or a dedicated strict production reader/writer layered over the generic primitive. Bind kind/schema, analysis split, full A3 commit and code closure, exact A1 identity and parent/sidecar file hashes, design/protocol hashes, matched-source identity, ordered IDs/streams/conditions/sites, prompt/token/readout/label identity, grader/model/tokenizer revisions and exact physical numeric profile. Fit/probe/axis caches derived from model captures inherit the capture profile and lineage. Reject unknown scientific kinds or require an explicit registered kind policy; aliases must not disable profile requirements. A separate explicit injected/generic fixture seam can remain. Add rejection tests for omitted expected fields, alias kinds and profile-free fitted axes.

The new deterministic MMLU helper and canonical preparation match the reviewed membership ruling: one seed-two draw of one hundred twenty-eight local candidates, first thirty-two unique eligible rows after assessment/source/donor/prompt exclusions, no redraw, source test split retained, separate validation analysis split, and validation-owned donor maps. Assessment IDs, order, prompts, tokens and original utility payload remain ancestry-bound. No new production freeze was created.

## How verified

Commands ran in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_design.py tests/test_a3_pipeline.py tests/test_a3_direction_artifacts.py -p no:cacheprovider -q
```

Observed: 75 passed in 22.68 seconds, exit zero. Evidence: `/tmp/review83-evidence.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_design.py tests/test_a3_pipeline.py tests/test_a3_direction_artifacts.py -p no:cacheprovider -q
```

Observed: 75 passed in 26.84 seconds, exit zero; existing pandas/bottleneck version warning. Evidence: `/tmp/review83-evidence.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=$PWD /u/swong2/.conda/envs/mgnp/bin/python -m pytest /tmp/test_review83_mutations.py -p no:cacheprovider -q
```

Observed: 9 passed in 5.27 seconds, exit zero. Evidence: `/tmp/review83-evidence.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=$PWD /sw/external/python/anaconda3/bin/python3.9 -m pytest /tmp/test_review83_mutations.py -p no:cacheprovider -q
```

Observed: 9 passed in 6.66 seconds, exit zero; same version warning. Evidence: `/tmp/review83-evidence.log`. These diagnostic tests intentionally assert the two permissive identity behaviors and the erroneous cache-symlink rejection. Passing them reproduces the findings; it does not mean those behaviors are acceptable.

Other mutation probes reject equal-payload manifest reserialization, path-traversing shard identifiers, partial named shard targets, changed expected key coverage and newly protected validation donor IDs. Orphan temporary siblings are ignored and do not contribute rows. Missing later runtime files make the full closure check fail closed. Existing owning tests additionally exercise changed parent sidecars, selected-file byte changes, stale A1 code, injected finalization rejection, cached-source changes, new source/instance/donor protection and numeric geometry mismatch.

Read-only `load_a1_parents` and `_validate_parent_files` accepted the exact fresh parent under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/ladder-5f450dc`. Original A1 commit is `5f450dc93dac707af649dee8c8ca60888b2831db`; assessment counts are FAR 100, SDR 100 and SER 100, with IOI 100 and MMLU 32. Completion file digest is `50cf8feef06ecb661ecb8bc76d7ddbeaac7cf29002e947ddf21201e955add20c`. The actual cache-symlink check read only source metadata and file bytes. Count evidence: `/tmp/review83-evidence.log`.

## Execution evidence

Not applicable: no runs.

All commands above are bounded CPU contract tests or read-only artifact inspections. No model execution or scientific outcome is claimed.

## What is NOT done

- At the original review, both findings remained unfixed. The scoped closure below supersedes that status; production preparation and admission remain outside this review.
- No model weights, GPU, Slurm, API or notebook execution; no new production A3 freeze, git commands, author-report access or subagents.
- Later Units B–F were not reviewed. Their incomplete presence is an intentional source-closure blocker, not a missing Unit A model-stage implementation.
- No full workflow result or scientific baseline reproduction is claimed.

`validate_live` is a CPU lineage/protected-access guard. It refreshes the primary/worktree/extra protected registries against actual IDs; checks both grader registries; checks protocol/design identity, current source closure, exact A1 parent and sidecar bytes, original A1 source files and assessment membership, cached utility sources, historical sources and matched manifest bytes. It returns fresh registry/grader hashes and an injected flag. It does not call a loader, grant cost admission, establish numeric runtime geometry, check a root reservation or establish whole-panel completion. Explicitly injected fixture success is permissible there and never grants production finalization.

Later consumers must invoke it immediately before every model load, each new shard and each resumed shard, retain its fresh hashes in execution manifests, establish the exact numeric/runtime/model identity, reject injected/pilot finalization, enforce measured admission and reservation, and supply complete expected bundle identity. `read_completed_shards` intentionally returns only present complete inventory shards; finalization must separately demand the entire inventory's expected coverage. The absence of those calls from this Unit A-only preparation module is not a finding.

## Open questions

No user decision is required. Default: return both intrinsic artifact issues to the Unit A owner, then rerun the owning suites and these concrete mutation reproductions before dependent production stages. Keep all original A1 scientific membership and immutable artifacts unchanged.


**Scoped re-review closure of findings A and B**

Both findings are closed in the updated source. No new blocking issue was found within these fixes. The initial findings and initial test outcomes above remain a historical record; this closure supersedes their unresolved status. This re-review read the actual updated implementation and owning tests, without reading the author's hand-back.

Finding A: `validate_cached_utility_source` retains lexical relative-path containment, then allows a snapshot symlink only to a hash-named blob inside the same local Hugging Face dataset repository. It still checks exact frozen bytes. The actual unchanged MMLU snapshot and blob link from the original finding now pass through `validate_live` in an injected CPU fixture. Wrong content hashes, parent traversal, absolute paths, arbitrary targets, other-repository blobs, and blob-file or blob-directory redirects reject. Ordinary immutable output bundles still reject symlinks.

Finding B: scientific numeric artifacts now use registered kinds and a mandatory full schema. The writer validates it before publication. The reader requires a complete valid expected schema and exact whole-metadata equality, so an empty expectation or a profile-only expectation no longer admits a scientific cache. Independent omission attacks removed each mandatory identity field from the reader expectation and all rejected. Unknown/alias kinds and profile-free registered scientific kinds reject before publication.

Fit, probe and axis artifacts now require capture references containing manifest/completion hashes and byte lengths, identity and ancestry digests, and the numeric-profile digest. `capture_reference` obtains these from a successfully read strict capture. Independent derived-cache probes accepted complete inherited identities and rejected changes to physical width, physical batch size, axis tile size and parent sidecar hash while keeping the capture reference unchanged. The separate generic namespace requires explicit injected status; it cannot publish under noninjected status.

These are integrity and identity checks, not artifact authentication or admission. Later producers must compute row-identity digests from actual ordered source bytes/tokens/readouts/labels and obtain capture references from the real accepted inputs. Consumers must still perform the live source/registry/ancestor refresh and exact inventory/admission checks described above. No model-stage invocation was added to Unit A or expected from it. Noninjected production closure intentionally remains blocked while the remaining direction runtime is incomplete.

Updated owning commands, run from the same worktree:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_design.py tests/test_a3_pipeline.py tests/test_a3_direction_artifacts.py -p no:cacheprovider -q
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_design.py tests/test_a3_pipeline.py tests/test_a3_direction_artifacts.py -p no:cacheprovider -q
```

Observed: 128 passed in each environment, exits zero. The base interpreter emitted the existing pandas/bottleneck version warning. Evidence: `/tmp/review83-closure-owning.log`.

Independent closure commands:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=$PWD /u/swong2/.conda/envs/mgnp/bin/python -m pytest /tmp/test_review83_closure.py -p no:cacheprovider -q
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=$PWD /sw/external/python/anaconda3/bin/python3.9 -m pytest /tmp/test_review83_closure.py -p no:cacheprovider -q
```

Observed: 46 passed in each environment, exits zero; the base interpreter emitted the same warning. Evidence: `/tmp/review83-closure-mgnp.log` and `/tmp/review83-closure-base.log`. These rejection tests now assert the desired repaired behavior rather than the permissive behavior documented in the original diagnostic suite.

No production source edits, new production freeze, git, model weights, GPU, jobs, API calls, notebooks or subagents were used. No scientific result or baseline reproduction is claimed. No open question remains for these two findings; default is to proceed with the separately reviewed later units while preserving the original A1 scientific membership and immutable artifacts.
