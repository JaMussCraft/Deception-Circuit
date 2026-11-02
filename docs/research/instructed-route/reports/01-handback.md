# Hand-back 01: B1 plan for the loop-closure (T1) and key-versus-query (T2) tests

Agent: B1 planning agent, Claude Opus. Ticket: the team lead's B1 planning brief; no ticket file exists. Status:
resolved. The plan is written. No code was built, and no job ran.

## What changed

- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/plans/B1-plan.md`.
  It is a new file of 250 lines: the B1 design, code inventory, cost, tickets, risks and fallback.
- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/reports/01-handback.md`
  (this file).
- Nothing was staged for the apply tool, and no other file was touched.

## How verified

Every check ran on the login node with no GPU. Each one checked a fact the plan relies on.

Run from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route`:

```
timeout 300 /u/swong2/.conda/envs/mgnp/bin/python -c "
from datasets import load_from_disk
from transformers import AutoTokenizer
from component_analysis import segmentation as S
import json
tok=AutoTokenizer.from_pretrained('meta-llama/Llama-3.1-8B-Instruct')
for t in ['far_v2','ser_v2']:
  D=load_from_disk('data/datasets/'+t)['test']; H=load_from_disk('data/datasets/'+t+'_honest')['test']
  hix={r:i for i,r in enumerate(H['instance_id'])}
  ids_s=json.load(open('docs/research/mechanism-analysis/phase1/groups/'+t[:3]+'_heldout_D_sample.json'))['instance_ids']
  dix={r:i for i,r in enumerate(D['instance_id'])}
  bad=0; outside=0; n=0; multi=0
  for iid in ids_s:
    r=D[dix[iid]]; h=H[hix[iid]] if iid in hix else None
    if h is None: bad+=1; continue
    a=tok(r['clean_prompt'],add_special_tokens=False)['input_ids']; b=tok(h['clean_prompt'],add_special_tokens=False)['input_ids']
    seg=S.resolve_segmentation(t,r,tok); pc=set(seg.segments['pressure_clause'].token_indices())
    if len(a)!=len(b): bad+=1; continue
    diff=[j for j,(x,y) in enumerate(zip(a,b)) if x!=y]
    outside+=sum(1 for j in diff if j not in pc); n+=1
    multi+=sum(1 for nm in ['item_1_question_pair','item_2_question_pair','item_1_question_option','item_2_question_option'] if len(seg.segments[nm].token_indices())!=1)
  print(t,'paired',n,'unaligned/missing',bad,'diff tokens outside clause',outside,'multi-token option mentions',multi)
"
```

Observed: `far_v2 paired 100 unaligned/missing 0 diff tokens outside clause 0 multi-token option mentions 0` and
`ser_v2 paired 100 unaligned/missing 0 diff tokens outside clause 0 multi-token option mentions 0`. An earlier check
compared against the record field `neutral_prompt` and found lengths that differ. That field is a different control,
so the plan forbids it.

```
/u/swong2/.conda/envs/mgnp/bin/python -I -c "
import json
a=json.load(open('/projects/beto/swong2/Alignment/Deception-Circuit/outputs/_analyses/mechanism-analysis-p1/heldout_d/U__leaf/far_v2/sample.json'))
b=json.load(open('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/mechanism-analysis/phase1/groups/far_heldout_D_sample.json'))
print(sorted(a['instance_ids'])==sorted(b['instance_ids']), len(a['instance_ids']))"
```

Observed: `True 100`.

Run from `/projects/beto/swong2/Alignment/Deception-Circuit/outputs/_analyses/mechanism-analysis-p3`:

```
/u/swong2/.conda/envs/mgnp/bin/python -I -c "
import json
for t in ['far','ser','sdr']:
  d=json.load(open(f'd/Ct__leaf/{t}_v2/path_patching/sweep_neutral_twin.json'))
  print(t, d['sample']['n_instances'], d['sample']['n_excluded_by_gap'], d['cost'])
  for s in d['senders'][:14]: print('  ',s['sender'],round(s['mean'],3),round(s['se'] or 0,3),s['in_circuit'])
"
```

Observed:

| task | forwards | wall seconds | top outside senders |
|---|---|---|---|
| far | 13,767 | 644 | mlp.31 0.203, mlp.30 −0.111, head.31.0 0.050 |
| ser | 13,767 | 610 | mlp.30 −0.127, mlp.31 0.084, head.31.0 0.061 |

Run from `/projects/beto/swong2/Alignment/Deception-Circuit/outputs/_analyses`:

```
/u/swong2/.conda/envs/mgnp/bin/python -I -c "
import json
for f in ['mechanism-analysis-p1/timings/1c-b.json','mechanism-analysis-p3/timings/far.json','mechanism-analysis-p3/timings/ser.json']:
  d=json.load(open(f)); print(f, [k for k in d.keys()])
  for inv in d['invocations']:
    a=inv['argv']; out=a[a.index('--output-dir')+1] if '--output-dir' in a else '?'
    print('  ', out, {k:v for k,v in inv.items() if k!='argv'})
"
```

Observed:

| job | model load (s) | invocations (s) |
|---|---|---|
| 1C-b | 619 | 931 for far heldout_d |
| p3 far | 767 | d 5,506, d_is 2,495 |
| p3 ser | 704 | d 6,209, d_is 2,901 |

```
/u/swong2/.conda/envs/mgnp/bin/python -c "import nnsight, torch, transformers; print(nnsight.__version__, torch.__version__, transformers.__version__)"
/sw/external/python/anaconda3/bin/python3.9 -c "import nnsight; print(nnsight.__version__)"
```

Observed: `0.7.0 2.11.0+cu128 5.13.0` (mgnp) and `0.5.12` (base). So the tiny-model tests run on mgnp and skip on base.

Run from the worktree root:

```
grep -rln 'write_run_manifest' --include=*.py . | grep -v '/.claude/' | head -20
```

Observed: only `run_manifest.py`, `run_io.py`, `evaluation/suite.py` and `tests/test_run_manifest.py`. So
`analyze_components.py` writes no `run_manifest.json`.

```
research-session lint /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/plans/B1-plan.md
```

Observed: exit 0. The file is 250 lines (`wc -l`).

The other facts in the plan were read directly from code and committed tables:
- Receiver-only position masks, and the grid-before-sweep order, are in `component_analysis/path_patching.py`.
- `sdr_shared_composition.py` is bound to the SDR panel.
- `knockout.load_groups` accepts head and mlp kinds.
- The quartet is KV group 6, from `phase3/b_selector.csv`, where `k.17.6` appears.
- The selection-sample shares come from `phase3/completeness.csv`.
- The Sun claim comes from the arXiv 2605.09314 abstract, fetched with WebFetch, and from Alignment
  `.scratch/synthesis-20261101/review-D.md` M7.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- No code was written. Tickets 1 to 7 of plan section 5 are all open, and no implementer was spawned.
- No batch file or dry run exists yet. That is ticket 7.
- No ruling was recorded in `spec.md`. The control qualifiers of plan section 1.4 are a proposal only.
- The held-out outside-grid share is unknown. The 0.80 and 0.77 figures are selection-sample numbers.
- The timing of the capture-all forwards is extrapolated, not measured. The smoke job measures it.
- The full text of Sun et al. was not read, only the abstract. The paper's head indices and model list are unconfirmed
  here.

## Open questions

- **Record the section 1.4 qualifier ruling in `spec.md` before the first job?** It adds route-specific, generic
  amplification and not-specific labels on top of the frozen closes or bypass verdict. Default: record it, dated
  before any run, because without it a pass of the frozen rule is uninformative.
- **Push the `instructed-route` branch so Bridges-2 can `git pull` it through `b2.sh sync-code`?** This is not a merge to
  main. Default: push after tickets 1 to 7 are merged on the branch, then smoke.
- **Which direction is primary for "restoring"?** The plan restores pressure-free twin values into D, as in F-sdr-002,
  and reports the reverse, D values into T, as descriptive. Default: keep that.
- **Is C3 an acceptable generic-amplification control?** C3 is a per-instance push along the target-minus-distractor
  unembedding direction at layer 17, matched on the lens margin. Default: yes, with C1 and C2 random-head draws as the
  specificity floor.
- **Add the `instructed-route-b1*` glob to `FETCH_ANALYSIS_GLOBS` in `scripts/remote/b2.sh`?** Default: yes, inside
  ticket 7.
