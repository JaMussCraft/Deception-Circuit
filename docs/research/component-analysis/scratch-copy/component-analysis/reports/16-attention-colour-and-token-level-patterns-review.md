# Code review — ticket 16 (attention colour and token-level patterns)

Fixed point `4ba2877` (the `component-analysis` tip), branch
`ca/16-attention-colour-and-token-level-patterns`, worktree
`Deception-Circuit/.claude/worktrees/ca-16`. Diff `git diff 4ba2877...HEAD`.

Commits reviewed:

    e4c612d  Draw attention in a warm colormap and render each head's attention token by token
    7357bf2  Show attention in the recorded colormap in the notebook, and the token PNGs inline
    73166ec  Name the unclaimed run, the token-level path and the slot Segments plainly  (author's pass)
    2b1fc85  Say so when token-level is asked for but no condition was profiled  (advisor's finding)
    111a911  Move the token-level rendering into its own module, and take both reviews
    4fb2c66  Name the recorded colormap in the attention notes, not in the notebook text

The two independent sub-agents reviewed e4c612d and 7357bf2. The last four
commits came after them. The final two apply the orchestrator's calls on both
reviews.

## Status of the independent review

`mattpocock-skills:code-review` was run with both axes as parallel
sub-agents: Standards agent `ac7266f6f060da044`, Spec agent
`aed1928e4cfa73b3d`. Both handbacks failed, as the brief predicts, and both
reports were then delivered by message: to the orchestrator first, who
forwarded them with calls, and later to the author. **The review is
independent on both axes.** Both reports are below with only light cleanup,
and each is followed by the orchestrator's calls and their outcomes.

## Standards (independent)

> No hard violations, one soft breach of a documented rule, and eight smells.
> All of them are judgement calls.
>
> Checked and clean:
> - No module other than hooks imports nnsight, and review.py adds no imports.
> - The new flag `--attention-token-level` carries the analysis prefix.
> - Every new PNG has a JSON twin.
> - `estimate` (the dry-run path) only adds text.
> - The code runs on Python 3.9 and uses `from __future__ import annotations`.
> - Tests assert on written files and on `review` views, not on hook wiring.
> - `review.ATTENTION_COLORMAP` restates the colormap name, but restating a
>   name and pinning it with a test is the existing `ATTENTION_SUBDIR`
>   pattern.
> - `colour_scale` reuses an existing twin key.
>
> Soft breach:
> 1. CONTEXT.md, Scaffold entry, says "_Avoid_: template (reserved for
>    Template Variant)". tests/test_attention_token_level.py has "weighted
>    over the template groups by their instances". It should say "Template
>    Variant groups".
>
> Smells:
> - Feature Envy: `token_level_payloads` works on `group.sums`, `.present`,
>   `.ids` and `.tokens`, and works out each slot's most common token itself.
>   `_row_keys(group, ...)` reads only the group. Both belong on `TokenGroup`.
> - Primitive Obsession: a slot key is `(run, "L"/"R", offset)` with string
>   sides, a row key is the bare tuple `(condition, query)`, and `widths` is
>   `[[left, right]]`.
> - Mysterious Name:
>   - `PRESSURE_PROMPTS = "pressure"` is the same string as the `PRESSURE`
>     condition. The "pressure" family also holds the honest_instruction and
>     pressure_paired rows, and the test filters on `family == "pressure"` and
>     `condition == "pressure"` side by side.
>   - `TokenGroup.tokens` holds `{slot: {token id: count}}`, which the name
>     doesn't say.
>   - `labelled` is a set of record ids, which the name doesn't say either.
> - Data Clumps: `tokens=tokens, condition=X` travels together into all four
>   `collect_condition` calls. Both are Optional and only make sense as a pair.
>   Separately, `rows_out` on `batch_masses` is a mutable out-parameter.
> - Duplicated Code:
>   - `getattr(ctx.cli, "attention_token_level", False)` appears in both
>     `estimate` and `run`.
>   - `"full" if full else "meta-only"` appears twice.
>   - `plot_token_level` hard-codes `PowerNorm(gamma=TOKEN_LEVEL_GAMMA,
>     vmin=0.0, vmax=1.0)` instead of reading `TOKEN_LEVEL_SCALE`.
>   - The 5.5 pt font size appears both in the height calculation and in
>     `set_xticklabels`.
>   - review.py's `TOKEN_LEVEL_SUBDIR = "attention/token_level"` restates
>     `ATTENTION_SUBDIR`.
>   - The notebook's markdown hard-codes `YlOrRd`.
>   - `patterns.json["token_level"]` copies the index's payload, byte-count
>     and limit fields.
> - Speculative Generality: `TokenGroup.n_heads` is stored but never read.
> - Divergent Change: attention_patterns.py grows by about 450 lines with a
>   second rendering (token alignment, grouping, splitting the twins at the
>   size limit) that changes for different reasons than the Segment masses.
>   The brief's "own module" rule names new analyses, so it doesn't strictly
>   apply here, but an attention_token_level.py would keep the module focused.
> - Magic numbers (house style is named constants): the figure-size factors in
>   `plot_token_level` (0.3, 0.9, 0.6/72, 0.12, 3.0) are inline. Low concern,
>   since `write_heatmaps` already does the same.
>
> Notebook: the `isinstance` cascade in `render` gains one branch. That
> follows the existing pattern, so it is not a finding.

### The orchestrator's calls, and the outcome of each

| finding | call | outcome |
|---|---|---|
| "template groups" in a test docstring | fix | **Fixed** (111a911): "Template Variant groups". The module's own prose says "Template Variant" throughout. |
| Divergent Change: token level inside ticket 03's module | fix: own module, no new registration, attention_patterns.run calls into it, add to the shared nnsight probe | **Fixed** (111a911): `component_analysis/attention_token_level.py`. Its `add_arguments` is called from `attention_patterns.add_arguments`, so both flags stay in the attention group under its prefix. `run` builds `TokenProfiles` and calls `write`. The module is in the probe list in `tests/test_component_analysis.py`. `attention_patterns` imports it lazily, inside functions, because the new module imports `attention_patterns` at top level. |
| Feature Envy: payload and row keys outside `TokenGroup` | fix | **Fixed**: `TokenGroup.slots`, `.row_keys`, `.most_common_tokens`, `.means` and `.size`. `payloads` only formats. |
| `PRESSURE_PROMPTS` colliding with the `pressure` condition | fix | **Fixed**: `TASK_PROMPTS = "task_prompts"` and `TWIN_PROMPTS = "honest_twin_prompts"`. Group ids are now `task_prompts/audit` and so on. |
| `tokens` / `labelled` names | (part of the Feature Envy fix) | **Fixed**: `token_counts` and `labelled_ids`, each with a comment. |
| Duplicated flag lookup, duplicated full/meta-only label | fix: one helper each | **Fixed**: `attention_token_level.wanted(cli)` and `payload_label(full)`, with `FULL`, `META_ONLY` and `NOT_PROFILED` as constants. |
| PowerNorm re-spelled | fix: read the scale constant | **Fixed**: `plot` builds the norm from `SCALE`. |
| 5.5 pt font in two places | fix: one constant | **Fixed**: `LABEL_FONT_PT`, with `CHAR_WIDTH_EM`. |
| review.py restating the attention directory | fix: derive it | **Fixed** (4fb2c66): `TOKEN_LEVEL_PATH = os.path.join(ATTENTION_SUBDIR, "token_level")`, still pinned by a test. |
| Notebook markdown hard-coding YlOrRd | fix: read it from the twin | **Fixed** (4fb2c66): `review.attention_views` now always adds the note "colour: <names>, as recorded in the figures' JSON twins". The markdown points to that note and names no map. The legacy-cell note stays. |
| Unread `TokenGroup.n_heads` | fix: drop | **Fixed**. |
| Primitive slot and row keys | judgement call (a NamedTuple is fine if cheap) | **Done**, since it was cheap: `Slot(run, from_end, offset)` and `RowKey(condition, query)`. `widths` stays a `[left, right]` pair per run, now documented. |
| Figure-size factors inline | judgement call (name them if the function is touched) | **Named**, since the function moved: `ROW_HEIGHT`, `PANEL_PADDING`, `SLOT_WIDTH`, `SIDE_MARGINS`, `MIN_WIDTH`. |
| `tokens` / `condition` data clump | judgement call | **Kept**. They are optional keyword arguments to `collect_condition` and are always passed together. A pair type would wrap two values for four call sites. |
| `rows_out` out-parameter | judgement call | **Kept**. It leaves `batch_masses`'s return shape, which ticket 03's tests unpack, unchanged, and it is None unless the token level is wanted. |
| index fields copied into `patterns.json` | judgement call | **Kept**. `patterns.json` is "the whole result", and a reader of it learns from these fields whether the token level was written in full, without opening a second file. |

## Spec (independent)

> No blocking issues; two partial items and one minor wrong spot.
>
> **(a) Missing or partial**
> 1. Meta-only twin, instance ids. The ticket says: "above that the PNG's meta
>    JSON records the shape, the instance ids and a pointer to how to
>    regenerate it". The per-head twin's `instance_ids` field is only a
>    pointer string to `token_level.json` `groups[].rows[].instance_ids`. The
>    ids themselves are always written to that index, which is never trimmed
>    by size. This deviation serves the ticket, since the ids are recorded
>    once and tested, but the twin alone does not hold them.
> 2. The regenerate pointer is generic. It says to rerun with "--analyses
>    attention_patterns --attention-token-level, after raising
>    attention_patterns.TOKEN_LEVEL_JSON_LIMIT_BYTES", which needs a code
>    edit, because there is no flag. It also leaves out the run's own
>    `--query-positions` and `--attention-conditions`. The index records
>    `query_positions`, so this can be recovered, but the regenerate text
>    should name those flags.
>
> **(b) Not asked for (all small, all serve the ticket)**: grey hatching for
> missing cells; the bar chart's colour taken from `COLORMAP`; `top_tokens`
> and the "largest tokens" notes; the legacy-colormap note; the estimate line;
> the luminance tests. None of this needs removing.
>
> **(c) Implemented, but looks wrong**
> 1. Panel titles can repeat inside one PNG. The panel title is built only
>    from the prompt family and template variant. The group id that tells two
>    layouts of one variant apart (`pressure/<variant>#2`) is never drawn.
>    Harmless on the saved SDR split, and a one-line fix.
> 2. The square-root scale on the token-level PNGs while the Segment heatmaps
>    stay linear. It is recorded in the meta and the title, and fits
>    "perceptually ordered". Accepted.
>
> Verified as meeting the spec: the colour constant, its docstring sentence
> and its recording in every twin; the notebook's plotly and circuitsvis
> colours, and the `Picture` view; one PNG per head with conditions as rows
> and n per row; grouping, most-common-token labels, rows summing to one and
> back to the Segment masses; the 5 MB limit and the forced meta-only test;
> the code can satisfy the Slurm checkbox.

### The orchestrator's calls, and the outcome of each

| finding | call | outcome |
|---|---|---|
| (c1) panel titles can repeat | fix: group id in the title | **Fixed** (111a911): every panel title starts with its group id, as in `task_prompts/audit (Template Variant audit): averaged over ...`. A test asserts it. |
| (a2) generic regenerate pointer | fix: name the run's own flags, and add `--attention-token-level-json-limit` (prefixed, bytes) | **Fixed**: the new flag defaults to `JSON_LIMIT_BYTES`. The pointer spells out `--analyses attention_patterns --attention-token-level --query-positions <the run's> --attention-conditions <the run's> --attention-token-level-json-limit <the full size>`, and a test checks each. The meta-only tests now force the limit through the flag rather than a monkeypatch. |
| (a1) instance ids by pointer | accept; say so in the twin's meta and in the ticket | **Done**: every per-head twin, full or meta-only, carries `instance_ids` with the sentence "The instance ids are recorded once per cell, in token_level.json under groups[].rows[].instance_ids, rather than in each head's twin: every head of a cell is averaged over the same instances." It is also in the ticket. |
| (b) the unasked extras, (c2) the square-root scale | keep | **Kept**, all of them. |

## The author's own pass (both axes; not independent)

### Standards

Sources: `CONTEXT.md` (glossary), ADR-0001/0002, the brief's design rules
(nnsight only in `hooks.py`, PNG plus JSON twin, dry run touches no GPU, seam
tests, additive shared-file changes, prefixed flags), `review.py` staying pure,
and the Fowler baseline.

Fixed in `73166ec`:

1. *Mysterious Name (judgement).* Tokens no Segment claims formed a run named
   `UNKNOWN_LEVEL`. That constant is the split's "record lacks the factor"
   level, a different concept. The run now has its own constant,
   `UNCLAIMED_RUN = "unclaimed"`.
2. *Mysterious Name (judgement).* `review.TOKEN_LEVEL_SUBDIR` was
   `attention/token_level` while `attention_patterns.TOKEN_LEVEL_SUBDIR` is
   `token_level`. The same name had two meanings across the seam, so the
   review.py one is renamed `TOKEN_LEVEL_PATH` (still pinned by a test).
3. *Message Chain (judgement).* `token_level_payloads` read the slot Segments
   back out of `index_groups[-1]["slot_segments"]`. It now uses a local
   variable.

Checked and clean: no nnsight import outside `hooks.py`, since the token rows
come from the existing `hooks.attention_weights` call through a new optional
`rows_out` argument of `batch_masses`. `review.py` still imports no torch,
plotly or circuitsvis. The new flag is `--attention-` prefixed. Every new PNG
has a JSON twin, and the token-level index is an extra JSON with no PNG. The
dry run computes the estimate only. pyflakes is clean on both modules and on
the notebook's joined code. The test file's fixture imports produce the same
F401/F811 pyflakes noise that `tests/test_attention_patterns.py` already
carries for the same pattern.

Kept, with reason:

- **`TOKEN_LEVEL_ORDER` restates the condition order of `COLUMN_PREFIXES`.**
  `COLUMN_PREFIXES` is defined later in the module, and the two orders mean
  different things (row order of a figure, column order of the head table).
- **Shared-file edits.** `review.py` and the notebook. Both are additive: a new
  shape (`Picture`), two optional `Heatmap` fields, one view, three constants,
  one renderer branch and one new notebook subsection. The only replaced
  notebook code is the circuitsvis Segment panel, whose
  `colored_tokens_multi` takes no colour and draws blue.

### Spec

Against the ticket's checkboxes and the orchestrator's design guidance.

- *Colour.* `COLORMAP = "YlOrRd"` is one named constant with a docstring
  sentence on why. It draws every attention PNG (both heatmap kinds; the
  top-heads bars take a colour from it) and is recorded as `colormap` in every
  attention twin, in `patterns.json` and in the token-level index. A pure test
  shows the choice is checkable. Under a simulated strong blue-light filter
  (gains R 1.0, G 0.8, B 0.1), magma keeps 7% of its luminance range in its
  bottom third and viridis 10%, while YlOrRd keeps 35%. The test asserts the
  filter check refuses magma, viridis and plasma and passes the constant.
  Plotly knows the same name with the same ends, which is tested, and the
  notebook takes it from the twin.
- *Token level.* Per head and per condition, from the configured query
  positions, every token. **Deviation:** the x labels are the most common token
  at each aligned slot, with its share when below 100%, not one representative
  instance's tokens. That is because a single instance's labels would be wrong
  for most instances at the varying slots. Grouping is by template variant and
  Segment-run order, aligned from both ends of each run. On the real SDR split
  there are 21 span-width layouts over 1000 instances, so neither per-length nor
  per-variant grouping alone aligns tokens. The run-order key alone gives one
  group that mixes both variants.
- *JSON limit.* 5 MB per cell over the per-head twins. Above it the twins are
  meta-only: shape, a pointer to the instance ids, the limit and full size, and
  how to regenerate. **Deviation:** the instance ids are in the cell's
  `token_level.json` index once, not repeated in each of the 17 per-head twins.
- *Tests at the CLI seam.* PNGs per head, colormap in every twin's meta, and
  the meta-only twin under a forced 1000-byte limit are all present. Also
  tested: rows sum to one, and slot sums reproduce `patterns.json` within 1e-4.
- *Scope beyond the letter:* the circuitsvis colour change and the hatched
  missing cells. Both serve the colour checkbox, which names the notebook's
  attention panels.

Nothing found missing.
