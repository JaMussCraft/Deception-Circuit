# Hand-back `61`: independent A3 CPU design review

Agent: Codex reviewer. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a3.md`, Task `1`. Status: resolved review; changes requested before production preparation.

## What changed

Only this report was written, in both required locations:

- Orchestrator commit copy: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/61-a3-design-review-handback.md`.
- Primary copy: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/61-a3-design-review-handback.md`.

Reviewed the assigned four new implementation/test files against START, spec, Task `1`, and the SDD rulings, with baseline supplied as c7f2712. Did not read author report `59`. No implementation files changed.

**Finding A — high: real parent and matched source paths use different representations.** In `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_pipeline.py:53`, the adapter looks up an absolute source path in A1's unnormalized `source_hashes`. The actual A1 payload uses relative keys for these datasets. For example, matched metadata names the absolute worktree `data/datasets/far_v2/dataset_config.json`, while A1 names `data/datasets/far_v2/dataset_config.json`. The digest matches. The same issue affects all twelve task/condition source roots. Consequently actual A3 preparation rejects its intended valid inputs before accessing matched membership. Smallest fix: construct a separate canonical resolved-path lookup for comparison, with conflicting aliases rejected; retain the immutable original payload and digest. Add a relative-A1/absolute-matched regression fixture.

**Finding B — medium: Arrow validation checks nested originals but ignores actual training row fields.** At the same module's lines `68–79`, modifying a loaded matched row's top-level `clean_prompt`, `corrupt_prompt`, `target`, `orientation`, and `token_proof` is accepted as long as `source_recipient` and `source_reference` stay intact. Those top-level fields are the materialized twin-training interface. Current A3 access rows come from A1, so this does not demonstrate changed Task `1` scoring inputs; it does invalidate any claim that preparation has established the actual matched training row/proof's equivalence for later mask work. Smallest fix: reconstruct the expected top-level materialized row from its checked originals and builder proof, or validate all future consumed fields against that reconstruction. Add mutations for actual prompts, labels, orientation and proof, not just nested source prompts. This can instead be explicitly deferred to mandatory Task `5` admission if Task `1`'s evidence is narrowed to membership and original-source provenance.

**Cluster convention requiring a ruling before Task `2`.** Canonical pressure text is available as the checked D source row's `pressure`. Lines `83–87` copy it into `pressure_text` for every matched condition. `_pressure` prioritizes that canonical text, with no instance-id fallback. Actual eligible cohorts retain this field throughout. Task `2` should group by `pressure_text`; local `pressure_id` is unsuitable for cross-task wording linkage. Plan line `31` promises an equal-size cluster-bootstrap fit, while line `93` carries all IDs of resampled clusters. Real clusters have unequal sizes. Freeze an explicit convention before fitting: normalized cluster multiplicities over all carried IDs preserve cluster linkage and define the fit mean, while realized repeated-row count may vary; never truncate clusters or silently fall back to instance bootstrap.

Other examined contracts are satisfactory at the tested scope: original A1 execution identity/full task scope and mandatory sidecar through `read_selection`; exact fixed assessment IDs; exclusion union and minimum cohort checks; historical category-specific heads plus quartet; deduplicated GQA K/V groups; unsupported semantic cases; optimized-Python outside-clause rejection; validation IOI exclusion by prompt as well as source/donor identity; metadata-only nuisance classifier. Activation nuisance directions and cosines remain explicitly in Task `2`.

## How verified

Commands below ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_a3_design.py tests/test_a3_pipeline.py
```

Observed stdout:

```text
33 passed in 12.11s
```

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider tests/test_a3_design.py tests/test_a3_pipeline.py
```

Observed stdout:

```text
33 passed, 1 warning in 14.56s
```

The warning is the existing pandas/bottleneck version warning. The suite includes a subprocess under `python -O` rejecting changed tokens outside the supported clause.

Exact minimal reproduction for Finding A:

```python
import json
from pathlib import Path
from component_analysis import a3_pipeline as p
root = Path('outputs/_analyses/specificity-ladder')
a, s, evidence = p.load_a1_parents(root/'ladder-0253f49/design.json', root/'ladder-0253f49/selected.json')
p._validate_parent_files(a)
m = json.loads((root/'a2-matched-77b6487-m07/build_manifest.json').read_text())
p._matched_rows(root/'a2-matched-77b6487-m07', m, a)
```

Observed: parent loading and all `208` source-file hashes plus `3` selection-file hashes pass; final call raises `ValueError: matched source is not frozen A1 input` at line `53`. Parent execution commit is `0253f494af007f93b2a00cb1e63cb3cdf1a8b519`.

A diagnostic-only second command deep-copied `a` and added resolved aliases to that copy's source hash map before calling `_matched_rows`. It did not write, rehash or freeze an artifact. All original-file byte checks, source metadata equality, matched configuration checks, nested source row equality and membership iteration then passed.

Derived cohort/cluster counts from the diagnostic adapter and explicit set/count operations:

| Task | Eligible fit | Eligible selection | Fixed assessment | Missing assessment IDs | Fit wording clusters | Fit cluster size range | Derivation |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| FAR | 177 | 177 | 100 | 0 | 12 | 1–27 | Derived set/Counter counts |
| SDR | 187 | 187 | 100 | 0 | 19 | 1–20 | Derived set/Counter counts |
| SER | 168 | 167 | 100 | 0 | 16 | 1–23 | Derived set/Counter counts |

Derived counts exceed the minimum `50` fit and `30` validation IDs. Every selected condition retains canonical `pressure_text`. Selection wording-cluster counts are 11, 20 and 16; assessment counts are 11, 19 and 16, respectively. Original matched test membership counts are FAR 891, SDR 952 and SER 835. Assessment membership is the existing 100 per task, not a new draw.

Exact reproduction for Finding B, using only temporary injected data:

```python
import runpy, tempfile
from pathlib import Path
from pytest import MonkeyPatch
from component_analysis import a3_pipeline as p
ns = runpy.run_path('tests/test_a3_pipeline.py')
mp = MonkeyPatch()
with tempfile.TemporaryDirectory() as directory:
    root, manifest, parent, materialized = ns['actual_matched'].__wrapped__(Path(directory), mp)
    row = materialized[str(root/'D'/'far_v2')]['train'][0]
    row.update(clean_prompt='tampered clean', corrupt_prompt='tampered neutral', target='tampered label', orientation='corrupt', token_proof={'invalid': True})
    p._matched_rows(root, manifest, parent)
    print('MATERIALIZED_TOP_LEVEL_TAMPERING_ACCEPTED')
mp.undo()
```

Observed: prints `MATERIALIZED_TOP_LEVEL_TAMPERING_ACCEPTED`; exit zero.

Representative real semantic check: loaded only the cached tokenizer snapshot named by A1. For the first actual matched training recipient in each arm/task, enriched the existing A1 row from its checked original source, then called `freeze_semantic_maps` and `semantic_sites`. Observed `4/4` supported twin maps per task and supported clause, designation and readout bins in all `24/24` checked streams. Question coverage was empty throughout: these actual source rows have no `question` field. The unsupported status is explicit and consistent with the missing-source policy; no question-position edge coverage is established. A future builder adapter can recover exact question character spans rather than infer a token correspondence.

The number checker inventory was manually reconciled against the command outputs above and the diagnostic cohort computations. Task/report/line labels are identifiers; test counts and runtimes are literal pytest stdout; the table and wording frequencies are derived set and Counter results.

## Execution evidence

- Job and cluster: local CPU pytest and read-only provenance checks; no Slurm, model weights or remote API.
- Exit codes: both pytest commands zero; unmodified real matched adapter reproduction one; diagnostic path-alias copy and injected tampering reproduction zero.
- Counts: `33` tests passed against `33` collected on each interpreter. Cohort counts and fixed assessment membership appear above.
- Baseline comparison: `33` passing on mgnp against `33` passing on base; no scientific intact baseline was run.
- Provenance: A1's existing `selection_run_manifest.json` under the worktree `outputs/_analyses/specificity-ladder/ladder-0253f49/`, naming the full parent commit above. Local CPU review commands create no scientific `run_manifest.json`; no scientific outcome is claimed.

## What is NOT done

No production A3 design freeze, model fit/load, scoring, GPU/API work, notebooks, git commands, author-report inspection, or code edits. No full real-data `prepare` success claim: Finding A blocks it. The cached-tokenizer sample below covers representative semantic maps, not the complete cohort. Later-task interventions, gradient replay, null calibration, model-derived nuisance fits and bootstrap implementation remain outside Task `1`.

Declined to judge: Task `2–6` implementations, because they do not exist in this review scope; production benchmark outcomes, because this was CPU design review; full future mask-row eligibility, except the explicit provenance gap in Finding B.

## Open questions

- Root should fix Finding A before production preparation. Default: canonical path comparison without mutating the A1 parent.
- Root should either close Finding B now or record mandatory consumed-row/proof checks at Task `5` admission. Default: close the validation gap now.
- Root should freeze the variable-size cluster bootstrap convention before Task `2`. Default: carry all resampled cluster members with normalized multiplicity weights and retain pairing.
