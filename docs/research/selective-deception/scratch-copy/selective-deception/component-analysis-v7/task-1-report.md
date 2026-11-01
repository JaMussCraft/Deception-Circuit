# Task 1 implementation report

Implemented the bounded seven-condition V7 runner, focused tests and absolute-workdir Slurm wrapper. No frozen science/selection/V6 source was edited; no model loaded on login, GPU job submitted, git mutation, installation or API call.

Owned files:
- `Deception-Circuit/.claude/worktrees/selective-components-v6/component_analysis/selective_v7.py`
- `Deception-Circuit/.claude/worktrees/selective-components-v6/tests/test_selective_v7.py`
- `.scratch/selective-deception/component-analysis-v7/launch.template.sbatch`
- this report

The runner reconstructs the exact 64-case SDR validation order from the V6 manifest and rejects selection/design/source/support/case drift. It uses all seven frozen names, batch size four, original donors and the existing V6 padding/metrics/model/hash/identity helpers. Donor requested/truth labels are recovered from the original manifest-bound V5 proposal and verified against original prompt tokens. No new donor is composed.

Prompt replacement maps actual nonpad ordinals rightward by `D-R`, then gathers each donor row at its own padded indices. Final replacement delegates to V6. Self replay takes the recipient bank at unchanged recipient coordinates with the donor-derived write mask. Every mapping record includes actual ordinals, padded indices, coverage, lengths, finals and donor token hash; intact/final rows retain the full prompt mapping as inventory, with `position_support` identifying writes. Main and smoke both use original right padding and persist exact batch case groups.

Actual controls compare plain/noop, final self, prompt self and all-false mask on complete native and fp32 vocabulary readouts. Main checks whole New30 for both supports in every batch; smoke checks all six intervention states. At the earliest affected layer, every head slice and every token position is checked against expected donor writes, including untouched siblings/pads/prefix. Raw native requested/truth-oriented numerical margins are saved separately from fp32 metrics. Finite JSON is mandatory.

Live execution requires Slurm, exactly one A40, nnsight0.7.0, BF16 SDPA and exact frozen geometry/model files. Receipt fields bind mode/output/manifest/selection/runner/source closure, wrapper path/hash, batch size four, source commit provenance, root reservation identity and remaining cap. Wall limits are 600 smoke / 900 main seconds with matching bounded reservations. Receipt claims are exclusive and one-use; no automatic retries. Root controls actual Slurm time/reservation and source commit. Source closure includes all root Python modules and component_analysis/models Python files as V6 followup does.

Artifacts: `plan.json`, `header.json`, `rows.jsonl`, `controls.jsonl`, `donor-capability.jsonl`, `completion.json`. Completion hashes all five preceding artifacts and records elapsed/load/batch runtime, peak CUDA allocation and unique donor count. No full historical logits are invented. Historical V6 scalar/native-argmax anchors remain an external root audit after acquisition (intact/intact, new30_final/original_New30, release17_final/release_17), per root instruction.

Verification:
- Tests first failed collection because the new module was absent, then implementation passed.
- Initial actual wrapper dry-run exposed overly broad stratum metadata grouping; corrected to the frozen designation/item-polarity cells before final dry-run.
- Actual wrapper CPU dry-run: `bash /projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v7/launch.template.sbatch dry-run /projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v6/panel.frozen.json /projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v7/selection.frozen-001.json /projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v7/cpu-dryrun-worker-002` → exit0,64cases,448rows; plan contains exact code closure hashes.
- Pinned production environment: `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -q tests/test_selective_v7.py tests/test_selective_v6.py tests/test_selective_v6_followup.py` → **20 passed**,21.18s.
- Base command uses `/sw/external/python/anaconda3/bin/python3.9` with the same arguments; final result recorded below.
- `bash -n .../launch.template.sbatch` → exit0.

Only focused tests were run; no full-suite claim. CPU tiny random-Llama tests exercise actual hooks and all seven states, own-coordinate self replay, false masks, complete-logit native/fp32 equality, earliest-layer full-head isolation and donor labels distinct from recipient labels. The base environment skips pinned nnsight integration as expected.

Runtime estimate remains operationally unmeasured until root's one 10-minute smoke. Wider controls add forwards; root must use measured load/batch timing before a <=15-minute main reservation. No outcome-based tuning or capability exclusion is authorized. Common readout suffix is only five tokens in this panel; token counts do not establish semantic alignment. Readout argmax is not free generation/coherent refusal.

Final base focused result: **15 passed,5 skipped**,27.24s,exit0. Five skips are pinned-nnsight actual-model integration tests; all pure/token/source/receipt tests passed.
