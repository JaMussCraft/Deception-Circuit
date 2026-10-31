# Independent review — ticket 01, worktree, environment and circuit intake

Reviewer: independent agent, not the author of the code and not the author of
`01-worktree-env-circuit-intake-review.md`.

Diff reviewed: `6b62fbf..7554839` (ticket 01's five commits), read as it exists
at the current tip `b6943b6`. Only ticket 01's responsibilities are in scope.
Of the thirteen files ticket 01 touched, three were later extended by tickets
02 and 05 (`analyze_components.py`, `component_analysis/__init__.py`,
`tests/test_component_analysis.py`); the other ten are byte-identical to
`7554839`.

Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/component-analysis`.
Nothing in it was modified. Analysis outputs were written under
`outputs/_analyses/review-01-tmp` and deleted; `git status --porcelain` is
empty.

---

## Verdict

Ticket 01 does what the ticket and the spec ask, and the numbers in its
comments are reproducible. Four findings, none of them a missing requirement.
One is worth fixing before block C because block C is the first code that
loads a model; the other three can wait.

| class | count |
|---|---|
| (a) missing / partial requirement | 0 |
| (b) scope creep | 0 (the self-review's three notes are all justified) |
| (c) implemented but wrong | 2, both minor |
| (d) standards violation (hard) | 0 |
| (d) standards smell (judgement) | 3 |

---

## What I verified, and how

Every claim below was run, not read.

### Coarsening agrees with `evaluation/masks.py`

The two rules are genuinely different code. `evaluation/masks.coarsen_masks`
copies `attention_heads` and `mlp_blocks` out of the circuit verbatim and opens
everything beneath them (`evaluation/masks.py:245-258`).
`component_analysis.components` ignores the coarse gates for membership and
reads the leaf gates (`component_analysis/components.py:120-135`,
`:139-159`). They agree because `validate_hierarchy` ties the two together for
heads.

Tests, both environments:

| environment | nnsight | result |
|---|---|---|
| `mgnp` (py3.12, transformers 5.13.0, torch 2.11.0+cu128) | 0.7.0 | 29 passed |
| login-node base (py3.9, transformers 4.57.3, torch 2.8.0+cu128) | 0.5.12 | 24 passed, 1 skipped |

The single base-env skip is `tests/test_nnsight_hooks.py`, skipped at module
level because 0.5.12 is not the pinned 0.7.0. The version gate at
`tests/test_nnsight_hooks.py:24-29` is right for this cluster, and the
`importorskip`-only gate the self-review replaced would indeed have run 0.7.0
assertions against 0.5.12.

I then ran the agreement check the tiny-model test makes, but over every saved
circuit in the worktree rather than a fixture. Every `active_nodes.json` under
`outputs/*/*/`: 66 run directories, of which 62 load. The other four raise in
`load_circuit_masks` for reasons that predate this ticket, three because they
were saved before commit `c714ce6` started writing a `masks` key and one
because its masks carry no `attention_heads` or `attention_neurons`, so no
coarsening runs on them at all.

| family | runs checked |
|---|---|
| `llama-8b-instruct_std` | 18 |
| `llama-8b-instruct_sdr` | 12 |
| `llama-8b-instruct_far` | 10 |
| `llama-8b-instruct_ser` | 10 |
| `llama-8b-instruct_joint` | 5 |
| `llama-8b_gp` | 4 |
| `llama-8b_ioi` | 4 |

**Zero disagreements**, including on the IOI and GP runs, which come from
different tasks and were worth checking separately because their mask key sets
differ. That is a much stronger statement than the unit test makes, and it
confirms the author's reading that the one divergence they document is
unreachable on real data.

### The real SDR nls0.3 dry run

Login node, no GPU, `HF_HUB_OFFLINE=1` so the "no weights downloaded" claim is
proven rather than asserted. Geometry read off the masks: 32 heads, head_dim
128, 32 layers. KV heads read from the HuggingFace config: 8, four query heads
per group.

| circuit | heads | MLP blocks | layers | head gate open | shared with honest |
|---|---|---|---|---|---|
| `sdr` atomic | 68 | 3 | 15 | 68 | 53 of 71 |
| `sdr \ honest_c` leaf | 68 | 3 | 15 | 68 | 53 of 71 |
| `sdr \ honest_c` head | 17 | 1 | 9 | 17 | 0 of 18 |

Every count in the ticket's comments reproduces exactly. Further assertions,
all true:

- the leaf delta is Component-for-Component identical to the atomic circuit;
- the 18 leaf-delta rows whose `reference.honest` is false are **exactly** the
  18 head-delta Components, and the head delta is a subset of the leaf delta;
- active neuron counts per head run 6 to 123 of 128;
- `kv_group == index // 4` for all 68 head rows, and is null for every MLP row;
- head-delta Component layers are 5, 8, 9, 13, 14, 17, 24, 27 plus the MLP
  block at layer 31, which is where the ticket's nine-layer list comes from;
  KV groups present 1-6.

### Circuit expressions the tests do not cover

The brief asks about xor and union. Neither has a test. I ran both against the
real runs, with a cross-task reference (a FAR run: same model, same geometry,
not a superset of the SDR circuit):

| expression | heads | MLP blocks | shared with the FAR reference |
|---|---|---|---|
| `sdr \| honest_c` | 86 | 3 | 74 of 89 |
| `sdr & sdr5` | 56 | 1 | 52 of 57 |
| `--xor sdr,honest_c,sdr5`, first family member | 8 | 1 | 8 of 9 |
| second | 17 | 0 | 9 of 17 |
| third | 14 | 0 | 9 of 14 |

Union, intersection, xor and a non-superset reference all resolve and coarsen
without incident. A reference from another model is refused
(`component_analysis/intake.py:135-139`, covered by a test).

Worth recording because the self-review does not: circuit masks are validated,
not only references. `evaluation/circuits.py:193` runs `validate_hierarchy` on
every bound operand, `:278` runs it again on every composed circuit, and
`component_analysis/intake.py:140` covers references. All three entry points
are closed.

### The prefactor is behaviour-preserving

I dumped `build_parser()` from `git show 6b62fbf:evaluate_circuit.py` and from
the current file and diffed the result: the full `format_help()` text, and for
every action its option strings, dest, nargs, const, default, type, choices,
required flag, metavar, help string and class, plus the argument-group titles
and their membership and order.

```
before rc=0
after  rc=0
ARGPARSE SURFACE IDENTICAL
```

Error paths follow, because argparse generates them from those same actions.

`resolve_circuit_specs` is equivalent to calling `resolve_circuits` on an
argparse namespace. It passes `list(circuit or [])` and `list(expr or [])`
where argparse supplies `None`, and both consumers spell the test as
`getattr(cli, ..., None) or []` (`evaluation/circuits.py:168`, `:223`), so the
`None`/`[]` asymmetry is invisible. `xor=None`, `all_pairs_delta=False` and
`compose_granularity="both"` match the argparse defaults exactly.

Evaluator regression check, `mgnp`: `tests/test_evaluation.py`,
`tests/test_end_to_end.py`, `tests/test_benchmarks.py` give 170 passed, 19
skipped, 1 failed. The one failure is
`test_mask_judge_kwargs_and_roles_match_evaluate_py`, which fails because the
MASK checkout is not beside a worktree, is in the ticket's pre-existing
failure list, and has nothing to do with the prefactor.

### `load_analysis_model` under the installed nnsight 0.7.0

The author checked the kwargs against the source and wrote that the function
is "not exercised by any test — it needs real weights and a GPU". It does not.
I ran it on the login node with no GPU, against a locally saved 2-layer random
Llama built from `tests/helpers.tiny_config` with real tokenizer files copied
in, under `HF_HUB_OFFLINE=1`:

```
LOADED OK dispatched: True attn: sdpa dtype: torch.float32 tokenizer: TokenizersBackend
traced o_proj.input: (1, 6, 64)
switched: eager
attn out tuple len: 2 weights None: False
2nd load dtype: torch.bfloat16 attn: eager
```

So: the model loads and dispatches eagerly, the tokenizer loads, tracing
reaches the `o_proj` input that ADR-0001 names as the per-head sender, the
docstring's eager/SDPA design works (`set_attn_implementation` does exist on
transformers 5.13's `PreTrainedModel`, and attention weights come back non-None
under eager), and the `dtype` override takes effect. The CPU path of this
function is now empirically sound; `device_map="cuda"` and the bf16 default for
a GPU device remain untested here because the login node has no GPU.

Confirming the author's specific kwarg claims from the installed source:

- `dispatch` is consumed by `nnsight.modeling.mixins.meta.MetaMixin.__init__`
  and never reaches transformers. Confirmed.
- `device_map`, `dtype`, `attn_implementation` and `token` are forwarded by
  `LanguageModel._load` to **both** `AutoConfig.from_pretrained` and the
  model's `from_pretrained`. The author only checked the second. I checked the
  first empirically: `AutoConfig.from_pretrained` accepts all four without
  error, sets `config.dtype` and `config._attn_implementation`, and silently
  drops `device_map`. Harmless.

Eager/SDPA handling matches ADR-0001: SDPA is the default
(`component_analysis/hooks.py:48`) and eager is a per-call parameter, which is
the ADR's "eager only for pattern extraction".

### Head table

`merge_columns` behaves as documented. Verified by running it:

- raises on `role_confirmed` and on each of `kind`, `layer`, `index`;
- does not mutate its input;
- gives every row every column, so rows never go ragged;
- appends a row for a key not in the table.

The CSV/JSON pair is consistent on the real 71-row SDR table: header equals
`columns`, same row count and order, blank for null, `0`/`1` for a boolean,
zero cell mismatches. Columns are exactly what the ticket asks for, in order:

```
kind, layer, index, kv_group, head_gate_active, active_neuron_count, reference.honest
```

Against the spec's Outputs section: the cell path
`outputs/_analyses/<suite>/<circuit>/<task>/` and the `head_table.csv` /
`head_table.json` pair at the cell root are as specified, and columns are
namespaced by analysis. The `role_proposed` / `role_confirmed` / `role_notes`
triple is absent, correctly, since roles are a later ticket; the part that had
to exist first, `role_confirmed` being reserved against analysis writes, does
exist. No log file is written at the cell by anyone yet — whoever owns that
line of the spec should pick it up.

### Standards sweep

- No CONTEXT.md `_Avoid_` term appears in any ticket-01 file. I grepped for
  every one of them: deception type/strategy/mode, lying, hallucination,
  confabulation, withholding, concealment, spin, misleading truth, framing,
  template, prediction head, answer position, designation token, corruption
  token, honest variant.
- Commit `b6943b6`, which took the independent Standards reviewer's
  vocabulary findings, touched only `component_analysis/segmentation.py` and
  `tests/test_segmentation.py`. Ticket 01 shipped clean on vocabulary.
- CONTEXT.md, `docs/adr/0001-*.md` and `docs/research/interp-tooling.md` were
  all added in `6b62fbf`, the commit the worktree was cut from. The ticket's
  first checkbox is honest.
- `.gitignore` covers the analysis outputs: `git check-ignore -v` resolves a
  written head table to `.gitignore:8: outputs/_analyses/`.
- ADR-0001's one-hook-module property is enforced by a source-parsing test
  (`tests/test_component_analysis.py:314-340`) and by a fresh-interpreter
  import probe (`:220-237`). Both are the right shape: the first cannot be
  defeated by test ordering, the second cannot be defeated by an earlier
  import in the session.

---

## Findings

### 1. (c) `hf_token` never reaches the tokenizer — `component_analysis/hooks.py:85-88`

```python
if hf_token:
    kwargs["token"] = hf_token
return LanguageModel(hf_id, device_map=device, dispatch=True, **kwargs)
```

nnsight 0.7.0's `LanguageModel._load` forwards `**kwargs` to
`AutoConfig.from_pretrained` and to the model's `from_pretrained`, but loads
the tokenizer as `self._load_tokenizer(repo_id, revision=revision,
**tokenizer_kwargs)` with `tokenizer_kwargs` defaulting to `{}`. The token is
in `kwargs`, not in `tokenizer_kwargs`, so `AutoTokenizer.from_pretrained`
never sees it.

The repo's own adapter does pass it (`models/__init__.py:75`), so this is a
divergence from house convention as well as a latent failure.

Failure scenario: block C runs `--hf-token <token>` on a node with no cached
HuggingFace login. `meta-llama/Llama-3.1-8B-Instruct` is a gated repo. The
config and the weights load; the tokenizer load raises a 401 whose message
names the tokenizer, not the token plumbing. On this cluster the models are
already in `HF_HOME`, which is why nothing has hit it yet, and equally why it
will surface somewhere unhelpful later.

Fix, one line:

```python
return LanguageModel(hf_id, device_map=device, dispatch=True,
                     tokenizer_kwargs={"token": hf_token} if hf_token else {},
                     **kwargs)
```

**Must-fix before block C.** Block C is the first ticket that loads a model,
and the ticket's own docstring tells that ticket to make a successful load its
first assertion — this is the assertion that would fail.

### 2. (c) `merge_columns` duplicates a row for a hand-built tuple key — `component_analysis/head_table.py:94`

```python
key = row_key(key) if not isinstance(key, tuple) else key
```

A `Component` goes through `row_key` and is normalised. A tuple is taken
verbatim, with no coercion of `layer` and `index`. Reproduced:

```
rows after merge with string-typed key ("head","0","3"): 2
  {'kind': 'head', 'layer': 0,   'index': 3,   'x.score': None}
  {'kind': 'head', 'layer': '0', 'index': '3', 'x.score': 1.0}
```

The table stays non-ragged so the CSV is still well formed, but the "one row
per Component" invariant breaks silently, and the same Component appears twice
with the analysis value on the wrong row.

Failure scenario: the completeness sweep is the caller the docstring names for
the append path, and it is exactly the kind of caller that builds keys from a
prior table read or a CSV rather than from `Component` objects. `row_key` on a
dict already coerces to int; the tuple branch does not.

Fix: normalise in the tuple branch too, `(str(key[0]), int(key[1]),
int(key[2]))`. Can wait, but should land before the sweep ticket.

### 3. (d) smell — a false premise repeated in three docstrings

- `component_analysis/__init__.py:22-23` — "the rest of the package imports in
  the login-node environment where nnsight cannot be installed (it needs
  Python >= 3.10)"
- `component_analysis/hooks.py:15-16` — the same sentence
- `scripts/smoke_nnsight.py:5-6` — "the `mgnp` environment, which is the only
  one where nnsight installs (it needs Python >= 3.10; the login-node base env
  is 3.9)"

The author's own ticket comment and self-review finding 5 record that this is
false, and I confirmed it: the base env is Python 3.9.18 and carries nnsight
0.5.12. The *tests* were corrected to gate on the version; the docstrings that
state the wrong reason were not.

Failure scenario: a later ticket reads `hooks.py`, believes an nnsight import
in the base env is impossible, and gates a skip or an import guard on the
wrong condition — which is precisely the bug the self-review already had to
fix once. Cheap to fix, and the reason is worth keeping: the rule is still
"nnsight imports inside functions", the justification is just "the base env
has the wrong nnsight, not none".

### 4. (d) smell — the glossary and the code disagree on one reachable state

CONTEXT.md, Component entry: *"A **Circuit Component** is one whose Component
has any active gate in the circuit under study."*

`component_analysis/components.py:139-159` implements "any active **leaf**
gate" for MLP blocks too, and `tests/test_component_analysis.py:150-165`
asserts the resulting *dis*agreement with `evaluation/masks.coarsen_masks` on
an `mlp_blocks` gate left open over dead `mlp_hidden` and `mlp_output`.
`validate_hierarchy` permits that state, so it is reachable in principle.

ADR-0001's Consequences say "the tests assert agreement with
`evaluation/masks.py`". One test now asserts non-agreement, deliberately.

The behaviour is right on the merits — an MLP whose fine gates are all closed
writes nothing, because gates AND together — and the spec's user story 2 only
fixes the leaf rule for heads, so the code is not contradicting the spec. It is
also empirically moot: I found zero disagreements across all 62 loadable saved
runs in the worktree, and
`algebra._derive_coarse` re-derives `mlp_blocks` from the fine gates so a
composed circuit cannot produce the state.

Resolution is a sentence: either CONTEXT.md's Component entry gains the word
"leaf", or the code follows the glossary. This is the author's open question 3
and it is the researcher's call, not mine. **Can wait** — but it should be
closed rather than left as an open question, because the glossary is the
standards document that later tickets will be reviewed against.

### 5. (d) smell — the coarsening-agreement test is weaker than its name

`tests/test_component_analysis.py:73-90`. `coarse_gates` reads
`attention_heads` and `mlp_blocks` back out of `coarsen_masks`, which copies
them from the input verbatim (`evaluation/masks.py:250-258`). The fixture has
already been through `validate_hierarchy` in `make_masks`, which forces head
gates and leaf gates to agree. So
`test_coarsening_agrees_with_the_evaluation_packages_coarsening` would still
pass if `circuit_components` consulted the coarse gates instead of the leaf
gates — the behaviour the ticket's rule is about.

This is not a coverage gap: the discriminating case is asserted separately at
`:134-147`, on a mask that deliberately violates the hierarchy. And the
ticket's checkbox is met either way. It is a claim smell — the test's name
promises more than it checks. The 53-run sweep in this report is the version
that bites; it is worth keeping as a slow-marked test or at least recording
that it was run.

### Minor notes, not findings

- **No test covers the `KEY_COLUMNS` branch** of `merge_columns`
  (`head_table.py:105-107`), only the `PROTECTED_COLUMNS` branch. I confirmed
  by hand that it raises for all three key columns. One more `pytest.raises`
  would close it.
- **`analyses_root` assumes a run directory two levels under `outputs/`**
  (`component_analysis/intake.py:167`,
  `dirname(dirname(abspath(base_run_dir)))`). True of this repo's layout. A run
  directory copied elsewhere puts the analyses in a sibling of that location
  with no warning. `--output-dir` is the documented escape hatch, so this is
  fine, just worth knowing.
- **`head_gate_active` on an MLP row holds the `mlp_blocks` gate.** The name
  comes from the ticket and the meaning is documented at
  `components.py:46-50` and in the head-table module docstring. I agree with
  the author's decision to keep the ticket's spelling. The head table is the
  object every later analysis and the notebook join onto, so if it is ever
  renamed, that should be a deliberate schema bump with `SCHEMA_VERSION`
  going to 2, not a quiet edit.
- **Scope creep: I found none.** The self-review's three self-reported items
  are all required rather than extra. `tests/test_nnsight_hooks.py` is spec
  story 41 and is what makes ADR-0001's one-hook-module property enforced
  instead of hoped for; `--data-dir`, `--test-samples`, `--std-variant` and
  `--hf-token` are what `evaluation.context.resolve_train_args` reads off the
  CLI, so task resolution does not work without them; the `.gitignore` stanza
  is what stops this CLI's own outputs being committed.

---

## Self-review claims: confirmed, and not confirmed

### Confirmed

1. Argparse surface of `evaluate_circuit.py` unchanged by the prefactor —
   confirmed by a programmatic dump diff of help text and every action
   attribute, both sides exiting 0.
2. `resolve_circuit_specs` is the same resolution, reachable without argparse
   and without a Session, and is the path the CLI actually uses — confirmed by
   reading both consumers' `or []` handling and by the test that calls it
   directly.
3. No new evaluator failures from the prefactor — confirmed on the three test
   files that exercise `evaluate_circuit.py` and `evaluation.circuits`.
4. `dispatch` is consumed by nnsight's `MetaMixin.__init__` in 0.7.0;
   `device_map` and `dtype` reach `from_pretrained` — confirmed in the
   installed source, and extended: they also reach `AutoConfig.from_pretrained`
   harmlessly.
5. The nnsight version gate is right for this cluster, and the base env does
   carry nnsight 0.5.12 — confirmed, both by version dump and by the base-env
   run skipping exactly that module.
6. The "no nnsight import" probe is order-independent and the one-hook-module
   guard runs in both environments — confirmed by reading and by both runs.
7. Every SDR nls0.3 number in the ticket's comments — confirmed exactly, plus
   the set-equality claim between the leaf delta's non-shared rows and the
   head delta.
8. The MLP-block divergence does not occur on the SDR run and cannot arise in
   a composed circuit — confirmed, and extended to all 62 loadable saved runs
   across all seven families.
9. KV heads read from the HuggingFace config, no weights downloaded —
   confirmed under `HF_HUB_OFFLINE=1`.
10. `merge_columns` protects `role_confirmed` and the key columns, keeps rows
    non-ragged, appends unknown keys, does not mutate its input, and the
    CSV/JSON pair is consistent — all confirmed by running them, the last on
    the real 71-row table.
11. Reference names are kept out of circuit resolution and a name bound both
    ways is refused — confirmed by the test and by reading
    `intake.py:117-123`.
12. The glossary, ADR and research doc were committed at `6b62fbf` before the
    worktree was cut — confirmed.

Beyond what the self-review claims: `load_analysis_model` is no longer
untested. I ran it end to end on CPU and it works, including the eager/SDPA
switch the docstring's design depends on.

### Not confirmed

1. **The "8 failed" baseline at `6b62fbf` and the final full-suite counts in
   both environments.** Re-measuring would mean checking out the base commit,
   which needs a second worktree, and the brief says not to touch the main
   checkout or modify this one. I checked the subset most exposed to the
   prefactor instead, and found only the known worktree-location MASK-path
   failure. The claim is plausible and consistent with what I saw; it is
   untested by me.
2. **The test counts.** The ticket says 12 / 10 / 6. The files hold 13 / 11 / 5
   at the tip *and already held 13 / 11 / 5 at `7554839`*, ticket 01's own last
   commit, so this is stale ticket text rather than anything tickets 02 or 05
   did. `b9ef272` added `test_circuits_resolve_without_an_evaluator_session`
   (10 to 11), and `7554839` moved the one-hook-module guard out of the nnsight
   file into the library file (6 to 5, and 12 to 13). The totals match what I
   ran: 29 in `mgnp`, 24 plus one module-level skip in the base env. Nothing is
   wrong in the code; the comment was written before the last two commits.
3. **The `pip install --dry-run` narrative.** Not reproducible after the fact.
   The end state does match what was asserted: nnsight 0.7.0, transformers
   5.13.0, torch 2.11.0+cu128 in `mgnp`.
4. **Open question 2, the "46 leaf / 14 head" numbers in user story 3.**
   Out of my scope to re-census every sparsity. The author's nls0.3 row is
   exactly what I reproduced, which is the row the rest of the argument rests
   on.
5. **GPU behaviour of `load_analysis_model`** — `device_map="cuda"` and the
   bf16 default for a non-CPU device. No GPU on the login node, and the ticket
   correctly submitted no Slurm job.

---

## Recommendation

Fix finding 1 before block C: it is one line, and block C is the ticket whose
first assertion is a successful model load.

Findings 2, 3 and 5 are cheap and can ride along with any later ticket that
touches those files. Finding 4 needs a decision from the researcher rather than
a code change — one sentence in CONTEXT.md would close it.

The ticket's last checkbox, "subagent code review ... independently of the
author", is now satisfied by this report.
