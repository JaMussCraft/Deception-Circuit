# Existing cache proof path lookup

Status: handed-back

## What changed

Read-only lookup completed; inventory 300 remains unchanged. This required handback is not a new cache proof or authority.

Known local reference: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/120-a2-bridges-pilot-readiness-evidence/remote-model-cache-reference.json`; SHA256 `6d4caf626770067c20ce372a197ec402e7242ab745fad8e3b338dead1a071fbf`.

Known remote reference: `/ocean/projects/cis260361p/swong2/specificity-ladder-20261102/deployment/model-cache-reference.json`.

Known local full proof: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/120-a2-bridges-pilot-readiness-evidence/remote-model-cache-check.json`; SHA256 `b28e3897ffc3bda9db3ad4bbaf5a38a5c3ed664b301983eae133c08536461fee`.

Accepted mapped remote full proof: `/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/120-a2-bridges-pilot-readiness-evidence/remote-model-cache-check.json`. Physical hub: `/ocean/projects/cis260361p/swong2/hf/hub`.

## How verified

Hashed only the two exact local files and owning actual historical config. Owning config is `W/.superpowers/sdd/plan-a2-bridges-assay/h100-g3-20261103/root-H100-R5/job-50189932/config.json`, with SHA256 `1d96dd830d0f0bb4bf375ba99af676e8ee7ece322ec87ff5ae317edc1fd4533a`, where W is the specificity-ladder worktree. Its `helper-bindings-continuation-20261106.json` binds the remote reference. Original accepted `root-model-phase-release-helper/r5-r2/helper.py`, lines 168 through 173, maps config `model_cache_proof` through its physical Alignment root. Accepted timing/control audit 177 covers that job. No broad recursive scan occurred.

## Execution evidence

Not applicable: no runs. No remote observation, scheduler/SSH action, native import, model, test or new cache check.

## What is NOT done

No current remote existence/cache validity or score absence is claimed. Root owns those checks. The original full-check file is not the new full-score wrapper: current guards require a separate wrapper with `reference` and `original_full_proof` path/SHA references pointing to the preserved originals.

## Open questions

Root should check score absence at virtual/local `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-analysis/bridges-h100-G3-v1/score`, and accepted mapped remote `/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-analysis/bridges-h100-G3-v1/score`. No further lookup is needed for these known paths.
