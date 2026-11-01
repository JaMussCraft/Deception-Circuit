CPU postprocessing preparation; source remains locked at `29492146127f56c05a4087b1bfdeea0e63a4d24a`. No export is authorized until root explicitly releases it after independent main-integrity PASS. Root supplies the reviewed integrity evidence path as `RELEASE`, then the two accepted original raw label paths as `RATER_A` and `RATER_B`; set `RATER_C` only if adjudication is required.

Worktree freeze: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot/.superpowers/sdd/plan-sdr-cue-followup/freeze-final-2949214/protocol.json` (file SHA256 `b2c7fd65ccb67e93f463553044569248fe85a80b8e1bd72ffef28df2cb3b5fa0`). Scientific hash `fd0bf5f1415b4ea951d6396753b64ad7c0061d883eeca28960b55a9bf9423b6e`.

The unchanged CLI verifies protocol/source/software/cache independently on every invocation. The prepared CPU orchestration calls that same public `verify_protocol(protocol)` exactly once, then uses the public `export_views` or `join_annotations` + `analyze_panel` functions without changing their implementations or validation. Each group starts in a new mgnp process, checks all frozen source files before and after, binds the immutable parent reference, and records inputs, outputs and timing in its immutable receipt. It never invokes inference functions or instantiates the model.

After root's explicit release, run export from Alignment:

```bash
set -euo pipefail
set -o noclobber
export CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
/u/swong2/.conda/envs/mgnp/bin/python -u .scratch/sdr-cue-followup/postprocessing-preparation/postprocess.py export --integrity-release "$RELEASE" > .scratch/sdr-cue-followup/postprocessing-preparation/export.log 2>&1
sha256sum .scratch/sdr-cue-followup/postprocessing-preparation/export.log > .scratch/sdr-cue-followup/postprocessing-preparation/export.log.sha256
```

The export creates only new artifacts under `outputs/_analyses/sdr-cue-positions/postprocessing-2949214/export/`. `packet/` contains only adapted blind `brief.md`, ordered exact `views.json`, exact `output-schema.json`, and opaque `headers.json`; root copies these four files to a fresh opaque `/tmp` directory and dispatches the fresh raters. Keep `started.json`, `receipt.json`, source paths, all scientific metadata, parent references, generation paths and preparation files outside that blind directory. Root preserves raw rater responses, exact dispatches, identities and separate personal coverage/freshness/independence attestations. No rater is dispatched here.

Accepted two-file join and descriptive analysis:

```bash
/u/swong2/.conda/envs/mgnp/bin/python -u .scratch/sdr-cue-followup/postprocessing-preparation/postprocess.py join-analysis --integrity-release "$RELEASE" --annotations "$RATER_A" "$RATER_B" > .scratch/sdr-cue-followup/postprocessing-preparation/join-analysis.log 2>&1
sha256sum .scratch/sdr-cue-followup/postprocessing-preparation/join-analysis.log > .scratch/sdr-cue-followup/postprocessing-preparation/join-analysis.log.sha256
```

If root's independent raw-file coverage/tuple audit finds disagreements, first obtain a third fresh blind adjudication covering exactly those disputed views, then use the same join command with `"$RATER_C"` appended to `--annotations`. Never modify or repair the raw files. Do not run join until root accepts the complete two-file set, or complete three-file set where required. Public join performs exact opaque hash/coverage/identity/freshness/rubric validation and rejects unresolved disagreements. Outputs are immutable; any failed invocation retains its evidence and is investigated before choosing a fresh output path.

`analysis/joined.json` restores exactly all 4,224 outcomes and retains finish/raw text/semantic labels. `analysis/analysis.json` includes fixed factorial/stratified inventories, complete transitions/triples, row audit and descriptive fresh-full/baseline versus immutable parent comparison. Parent reference path/hash comes only from `.scratch/sdr-cue-followup/parent-reference-binding.json`; public analyze separately checks that immutable canonical reference hash. Errors/caps remain in denominators. Calibration is never supplied. Independent raw-label arithmetic and narrative review remain required after production analysis.

Original rubric SHA256 remains `930f7f081060262f179dc3a4d030e21b15a8b710e629fbead76c6bf7ceda6185`. Adaptations are exclusively title, obsolete denominator wording, and a header note referring to the separate actual schema. Semantic instructions are unchanged, including conservative visible-stem formatting and whole-response assessment.
