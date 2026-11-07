# Hand-back 72: A3 direction algebra review

Agent: Codex independent reviewer. Ticket: approved A3 Task 2 bounded direction core. Status: handed-back.

## What changed

Review only; no implementation or test files changed. Scoped verdict: accept the direction core, with one nonblocking numerical hardening finding below. Inference, conditional power and pipeline integration belong to other tasks.

Report files for the orchestrator's explicit file list:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report72-a3-direction-review-handback.md`.
- Primary mirror: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/report72-a3-direction-review-handback.md`.

**P3: reject overflowed probe statistics and nonfinite scores.** In `component_analysis/a3_directions.py`, lines 241–246 accept finite input but do not check the computed center, scale or coefficients. Lines 253–255 convert NaN scores to the negative class and return an ordinary balanced accuracy. A finite, separable input `[[3e38],[3e38],[1e38],[1e38]]`, labels `[1,1,-1,-1]`, produces infinite center/scale, NaN coefficient and accuracy 0.5. This is a numerical guard gap at extreme magnitudes, not evidence of a failure with ordinary model activations. Add finite checks after standardization/solve and before score thresholding; reject invalid probe artifacts. No fix was made during review.

No blocking direction-algebra, weighting, null-space, intervention or selection finding arose within this bounded scope. The review did not read the author's report.

## How verified

Commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_directions.py -p no:cacheprovider -q -s
```

Observed: 18 passed, 3 warnings, exit 0. Both tiny-Llama tests actually ran. Native and existing NNsight inference self-replay maximum absolute errors were each 0.0 against tolerance 0.00001. The tests also assert changed logits for a nonidentity patch, adjacent-head equality, untouched positions and native hook cleanup.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_directions.py -p no:cacheprovider -q -s
```

Observed: 17 passed, 1 skipped, 4 warnings, exit 0. Native tiny-Llama self-replay error was 0.0 against tolerance 0.00001. The existing inference-hook test skipped because the base NNsight version differs from its pinned version. Its mgnp counterpart ran and passed; the base skip does not establish base compatibility for that hook.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python - <<'PY'
import torch
from component_analysis import a3_directions as c
x=torch.tensor([[3e38],[3e38],[1e38],[1e38]])
y=torch.tensor([1.,1.,-1.,-1.])
p=c.fit_ridge_probe(x,y)
print('finite_input',bool(torch.isfinite(x).all()),'probe',p,'balanced_accuracy',c.probe_balanced_accuracy(p,x,y))
PY
```

Observed: finite input true; center and scale infinite; coefficient NaN; balanced accuracy 0.5, exit 0. This is the finding's direct reproducer.

Source review against approved `plan-a3.md` global policy and Task 2 covered:

- fp32 residual-image SVD, strict relative cutoff 0.000001, and identical pseudoinverse cutoff; rank-deficient and zero-rank handling.
- Paired D/I/H shape checks, canonical cluster bootstrap, every member carried through multiplicity, normalized equal-id weights, equal stream averaging, expanded/unique counts and effective sample size. The seed-0 unequal-cluster fixture expands to four rows rather than truncating to three.
- Unit Gaussian orientations sampled inside the retained image with RNG offset 10000, own-axis H variance, and Moore–Penrose pullback. A separate local Gaussian stress check of 30000 axes in rank 3 produced maximum covariance deviation 0.003031 from the image projector divided by rank and maximum norm error 0.000000358; this is a sampling sanity check only.
- Orthogonal head-coordinate invariance of the learned residual axis and patch; nonzero DOM requirement; primary donor-only interchange and secondary H-centered removal; weighted population H variance for both steering signs.
- One-head tensors and exact position masks, intact self-replay, adjacent-head isolation through actual existing inference hooks in mgnp, and caller-owned attention-mask/readout validation.
- Neutral-frame nuisance fits/cosines, train-only ridge standardization and unpenalized intercept, and a predictive but causally inert toy role axis.
- Validation-only rows, exact candidate coverage, gate-first maximum D selection, failed-gate D-minus-I fallback, lexical ties and no internal assessment access. Computing all point gates and enforcing frozen task/site identity remain the caller's responsibilities.

## Execution evidence

- Job and cluster: local CPU pytest and ad hoc tensor commands above; no scheduler job.
- Exit codes: both pytest processes and both local tensor probes exited 0.
- Counts: mgnp executed 18 tests; base executed 17 and skipped 1 of the same 18 collected tests. No production cohort rows were processed.
- Baseline comparison: tiny native self-replay maximum absolute logit difference 0.0 against intact logits in each interpreter; existing-hook self-replay difference 0.0 against intact logits in mgnp.
- Provenance: no production `run_manifest.json` or execution commit was created by these local checks. This is code/test review evidence, not an empirical deception result or production-fit admission.

## What is NOT done

No production model weights, train/validation/assessment captures, selected sites, scientific fits, full null panel, steering panel, nuisance outcomes, probe outcomes, inference or conditional power results were assessed. No GPU, Slurm, API, notebook, broad repository suite, git command, implementation edit or subagent was used. Full-model replay, source freezing and future workload admission remain with root.

The sandbox launcher failed before commands could run because its temporary directory was read-only; commands then ran with reviewed escalation. This is an execution-environment issue, not a test regression.

## Open questions

No blocker for this bounded core. Default: accept the core and address the P3 finite-statistics guard before relying on probe diagnostics; root retains integration and production admission decisions. Numerical counts above are test outputs or explicit plan/test constants, not production measurements.

**Scoped P3 fix closure.** The original finding is closed after direct source/test inspection and the checks below. The source now checks fitted centers, scales, standardized designs, ridge systems/targets and solved coefficients for finiteness. Evaluation checks fitted-field presence, tensor shapes/finiteness, positive scales, finite intercept, fixed regularization, standardized coordinates and scores before thresholding. These guards preserve the original valid ridge formula, unpenalized intercept and train-only normalization. No additional finding arose in this fix review; the original bounded acceptance stands without an open P3 item.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_directions.py -k probe -p no:cacheprovider -q
```

Observed: 14 passed, 17 deselected, exit 0. Coverage includes the original finite-input overflow, finite-field evaluation score overflow, evaluation standardization overflow and malformed/nonfinite fitted fields.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_directions.py -k probe -p no:cacheprovider -q
```

Observed: 14 passed, 17 deselected, exit 0. No test in this fix scope skipped.

```bash
for probe_python in /u/swong2/.conda/envs/mgnp/bin/python /sw/external/python/anaconda3/bin/python3.9; do
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 "$probe_python" - <<'PY'
import sys
import torch
from component_analysis import a3_directions as c
x=torch.tensor([[1.,50.],[2.,50.],[3.,50.],[-1.,50.],[-2.,50.]])
y=torch.tensor([1.,1.,1.,-1.,-1.])
p=c.fit_ridge_probe(x,y)
a=torch.cat([torch.ones(5,1),(x-p['center'])/p['scale']],dim=1).double()
reference=torch.linalg.solve(a.T@a+torch.diag(torch.tensor([0.,1.,1.],dtype=torch.float64)),a.T@y.double())
assert abs(p['intercept']-float(reference[0]))<1e-6
assert torch.allclose(p['coefficient'].double(),reference[1:],atol=1e-6,rtol=1e-6)
assert abs(p['intercept']-.2)<1e-6 and p['scale'][1]==1
frozen={k:v.clone() for k,v in p.items() if isinstance(v,torch.Tensor)}
assert c.probe_balanced_accuracy(p,torch.tensor([[100.,50.],[-100.,50.]]),torch.tensor([1.,-1.]))==1
assert all(torch.equal(p[k],v) for k,v in frozen.items())
try:
    c.fit_ridge_probe(torch.tensor([[3e38],[3e38],[1e38],[1e38]]),torch.tensor([1.,1.,-1.,-1.]))
except ValueError as e:
    print(sys.executable,'original_overflow_rejected:',str(e))
else:
    raise AssertionError('original overflow accepted')
print('valid_augmented_ridge_reference_passed; train_parameters_unchanged; intercept=',p['intercept'])
PY
done
```

Observed in both interpreters: the original input raises `ValueError` at the nonfinite train center; the augmented double-precision ridge reference agrees within 0.000001; fitted train parameters remain unchanged after shifted evaluation; intercept is 0.20000000298023224 against expected 0.2. The command exits 0. These are local synthetic checks with no production rows, model weights or provenance manifest. The entire direction suite was not rerun for this narrowly scoped fix; earlier replay evidence above retains its original scope. Counts and numerical values in this closure are direct local outputs or explicit test tolerances/constants.
