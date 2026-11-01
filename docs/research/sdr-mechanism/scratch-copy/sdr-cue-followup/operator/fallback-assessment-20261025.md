# Single Delta A100 fallback assessment

2026-10-25T15:35UTC. Read-only options assessment; no root release, hardware amendment, source/spec edit, reservation, actual submission or job mutation.

Both A100 interactive partitions are promising alternatives before the study hardware is frozen. `squeue -u swong2` showed only the unrelated H200-interactive job23191980. User occupancy was0 on A100x4-interactive and A100x8-interactive; each independently permits one submitted/running userjob and has a1hour cap. Changing accounts cannot evade those limits. Do not touch job23191980 or its controller.

All14 requested `sbatch --test-only` comparisons returned0; hypothetical job numbers are not submitted jobs. Requests used1GPU,4CPUs/64G, account matching QOS,600s forH200 and1200s forA100. Current fairshare favors beto(.142027) over bimc(.107147),bgrb(.106624),bjhz(.087722). Full exact commands/outputs are in [fallback-test-only-20261025.json](fallback-test-only-20261025.json).

| Partition | Calibration test-only time | Best account | Projected start in Delta local time |
|---|---:|---|---|
| gpuH200x8 | 600s | beto | Nov1 00:23 |
| gpuA100x4 | 1200s | beto | Oct28 04:25 |
| gpuA100x8 | 1200s | beto | Nov7 12:55 |
| gpuA100x4-interactive | 1200s | beto | Oct25 10:35, immediate |
| gpuA100x8-interactive | 1200s | beto | Oct25 10:35, immediate |

The other three accounts had worse normalqueue forecasts. These projections are a single nonbinding scheduler snapshot; normalqueue forecasts can miss backfill opportunities. Still, both available A100 interactive paths clearly offer better observed wallclock prospects than normalH200.

Recommendation to root: select one A100 interactive partition/device model prospectively, amend operational hardware before final source/protocol freeze, and plan a fresh20min calibration target after actual frozen-wrapper CPU timing and full release gates. Actual H200 parent inference peak20.3GB suggests40GBA100capacity; prior training OOM does not establish inference OOM. New peak and numerical integrity remain unverified until the fresh calibration. Check exact A100 model/VRAM rather than equating all `gpu:nvidia_a100` devices. Do not combine differing physical device classes or reuse H200 timing/numerical calibration for A100 admission. Existing H200 proposal remains an unreleased option; this document changes no authoritative spec or allocation.

Keep main time unselected. Measure all6natural patched batches+sharedintact and forced64 controls on the chosen A100, then forecast remaining frozen batches with explicit observedruntime buffer/startup/audit/shutdown allowances. Respect the interactive1hour ceiling and measured fullcap batch admission guard; use deterministic durable resume when needed. No immediate20/30/60min main fit claim follows from the scheduler test or parentH200 scaling. Calibration/main/resume must share frozen exact device class/software. Root separately releases calibration and main/resume.

Costs remain0reservedGPUseconds,0actualGPUseconds,$0API. No scheduler daemon, repeated polling or additional submissions were used.
