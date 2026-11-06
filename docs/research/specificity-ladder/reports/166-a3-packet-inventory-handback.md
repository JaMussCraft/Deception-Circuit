# Hand-back 166: A3 oracle packet inventory

Agent: inventory worker. Status: resolved as an inventory, not scientific acceptance.

## What changed

This handback is the only file written: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/166-a3-packet-inventory-handback.md`. No staged operations.

Let W be `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`, T be `$W/.superpowers/sdd/plan-a3/direction-metadata-optionA-plan/genuine-oracle-cpu-r2`, E be `$W/.superpowers/sdd/plan-a3/direction-metadata-optionA-plan/genuine-oracle-executions`, and C be `$W/.superpowers/sdd/plan-a3/direction-metadata-optionA-candidate/component_analysis/a3_direction_workload.py`.

The only completed reference in E is `$E/original-mgnp-r2-02/COMPLETE_ORACLE.json`, SHA-256 `1685fca54172ab3de7a8003b8503fdf2a9ac184e684ae1c17a52493fcc7ca991`. It records full streamed publisher bytes 11421127399, digest `c738a185b9a79ef8873113e63aefa197a820f0a5c117159db055de6f70e0a6c9`, environment mgnp, and normal supervisor completion. The stream is hashed into a sink, not retained as an 11 GB file. Do not rerun it. The prior `original-mgnp-r2-01` output is empty after the failed working-directory submission. No base reference or candidate comparison exists in E.

The original base reference uses the unchanged `$T/config.template.json`, hash `77ec8f936b216bd5cd5a6e0e1945bf0b5e2be8903dc43b1b1cb6594387fc791e`. Its four nulls are `candidate_workload`, `candidate_workload_sha256`, `complete_original_oracle`, and `complete_original_oracle_sha256`. For each candidate comparison root must create a distinct reviewed config copied from that template, fill those four fields with C, its SHA-256 `765b22a006ab519186a168bf455f4084915457d4ffce88881e76bf31b71a37cb`, the complete same-environment `COMPLETE_ORACLE.json` path, and that small receipt's SHA-256. Keep other fields including `source_commit` fixed: the runner sets candidate result `source_commit` to null and `frozen_input_source_commit` to the original. Base receipt path/hash are unknown until completion. Candidate must pass fresh independent review; no acceptance is implied.

The established submission shape below is a template, not a submitted job. Set ENV to `base`, MODE to `original`, CONFIG to `$T/config.template.json`, CONFIG_SHA to its hash above, and OUT to a fresh nonexistent path for the base reference. For each candidate set ENV to `mgnp` or `base`, MODE to `candidate`, CONFIG and CONFIG_SHA to the matching new reviewed config and its actual SHA, and OUT to another fresh nonexistent path. Each candidate depends on its corresponding completed same-environment original receipt. Use root-selected job names and distinct log files; do not substitute a partial marker.

```bash
sbatch --account=bimc-delta-cpu --partition=cpu-interactive --constraint=projects --nodes=1 --ntasks=1 --cpus-per-task=4 --mem=192G --time=01:00:00 --no-requeue --chdir="$W" --job-name=lad-A3-oracle --export=ALL,CUDA_VISIBLE_DEVICES= --output="$E/ROOT_SELECTED-%j.log" --wrap="bash $T/oracle_cpu.sh --packet-sha256 21122c2077c367c7ccf9b08f8b865f263b7dcba66bf0480af25e14757973ed4d --config $CONFIG --config-sha256 $CONFIG_SHA --mode $MODE --environment $ENV --output $OUT"
```

The supervisor requires the actual allocation, exactly 3600 seconds limit, at least 3500 seconds remaining, and at least 150 GiB cgroup headroom. It enforces 3300-second child limit and 15-second kill grace, no retry. It checks packet members, config digest, snapshot and 511 sources/four links, original 13 W source hashes, six pinned files, canonical design, guards and module origins. It runs base `/sw/external/python/anaconda3/bin/python3.9` or mgnp `/u/swong2/.conda/envs/mgnp/bin/python`, with single-thread BLAS, offline settings, and no GPU. Only `COMPLETE_ORACLE.json` or `COMPLETE_COMPARISON.json`, produced after normal child exit and supervisor checks, qualifies. Comparison checks summary, full stream digest and byte count including final newline. Hashing a receipt is not hashing the multigigabyte stream again.

## How verified

Read `$T/{proposal.json,config.template.json,manifest.json,oracle_cpu.sh,supervisor.py,run.py}` and `$E/root-submission-23491516.json`, and listed `$E` and its original output directories. The exact small-file hash check was:

```bash
sha256sum /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-optionA-plan/genuine-oracle-executions/original-mgnp-r2-02/COMPLETE_ORACLE.json /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-optionA-candidate/component_analysis/a3_direction_workload.py
```

Observed hashes are given above. No stream was recalculated.

## Execution evidence

Not applicable: no runs.

## What is NOT done

No scheduler query or submission, git, tests, model execution, scientific acceptance, RS state change, comparison or stream rehash. Existing result descriptions are receipt inventory, not independently audited execution claims. The first sandbox invocation failed to initialize; read-only inspection used the approved escalation.

## Open questions

The root-selected base output path and two candidate configuration paths/hashes remain unspecified. Default: root binds unique immutable paths after independent review and supplies the actual hashes. Base runtime and candidate runtimes are unknown; preserve the reviewed 60-minute and child boundaries, and do not automatically retry on timeout. Successful same-environment equivalence alone does not constitute production numerical admission.
