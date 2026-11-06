# Hand-back 168: strict captured reset token

Agent: worker. Status: handed-back. Independent rereview is required before operational use.

## What changed

New successor `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-bridges-assay/h100-g3-20261103/root-model-phase-release-helper/r5-r2` anchors the exception line at both ends. Manifest SHA-256 `74f29f489229fe533ed6a7c6d07b13a24e3a2fb8c2c4555edda8b65b48b7f1e4`; helper SHA-256 `096e0216d9ddce55a38ff401e3759fa021a6208ecb4e58405991248337c0a392`. Its new `test_reset_token.py` hash is `942994e896aa73212c93451ccf011ed8cf673c40471776969ee98f98390be55b`. The only helper difference from r5 is the anchored regex and multiline flag. Predecessor manifest `67d7ff0345b268f508a75f636224c0bef9f8e109f2e7f87fbaad972e73174a89` and all its listed members remain intact. That predecessor is a failed reviewed revision.

## How verified

Commands ran in r5-r2. Before implementation, `PYTHONDONTWRITEBYTECODE=1 /sw/external/python/anaconda3/bin/python3.9 -m unittest -v test_reset_token > red-reset-token-base.log 2>&1` exited 1: three expected assertion failures because fractional, exponent and trailing-junk resets were accepted; valid context passed. No setup errors.

After the single-line fix, `PYTHONDONTWRITEBYTECODE=1 /sw/external/python/anaconda3/bin/python3.9 -m unittest -v test_reset_token test_usage_reset test_helper test_cache_gate > green-r2-base.log 2>&1` exited 0, 48 tests in 0.099 seconds. `PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python -m unittest -v test_reset_token test_usage_reset test_helper test_cache_gate > green-r2-mgnp.log 2>&1` exited 0, 48 tests in 0.068 seconds. These include all 46 preceding tests and 37 matrix subcases. Logs are pinned in the successor manifest.

## Execution evidence

Local pure unit tests only, with exits and counts above; no Slurm job or model. Scientific output rows and baseline reproduction are not applicable. The successor manifest records predecessor and approved design hashes; no source commit is claimed for this uncommitted helper.

## What is NOT done

No live release, RS state changes, scheduler action, git, remote operations or independent rereview. Passing pure tests does not authorize release.

## Open questions

Root should obtain independent review of this exact successor manifest and current operational bindings. Default: keep release held until those gates pass.
