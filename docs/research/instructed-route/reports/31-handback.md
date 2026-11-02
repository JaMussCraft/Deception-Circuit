# Hand-back 31: B3-T7, null draws exclude the tested set's members (rulings R10 and R10a)

Ticket implementer impl-B3-t7, Sun 1 Nov 2026, session claude-230e4716. CPU only, no model, no git, no Slurm.

During the ticket I found that strict member exclusion cannot work for S_all, S_far or S_ser. Llama has one MLP per
layer, so an MLP member is the only candidate at its layer. The lead ruled option (a), to be recorded as R10a. Head
members are excluded, MLP members stay in every draw as unavoidable, and every draw records which members it kept.
That is now the default, so the default J4 af and syc commands dry-run without error.

**What R10a means for the null comparison.** A null draw for an MLP-containing set shares the set's MLPs. For S_all
that is mlp.5, mlp.6 and mlp.7; for S_far, mlp.6 and mlp.7; for S_ser, mlp.5. So the R5 null comparison for those sets
tests the set's heads against random heads, given the same MLPs. The heads_only arm, S_all's 32 heads against a
heads-only null, stays reported beside it as planned. Gupta6, gupta_writers, L17H24 and S_q have no MLP member, so
their draws share no member with the set at all.

## What changed

- **`layer_matched_nulls` (`spontaneous/stats.py`), member exclusion.** `exclude_members=True` is the default: each
  (kind, layer) pool leaves out the set's own members, as well as mlp.0 as before. The seed and the (kind, layer)
  counts are unchanged, and the draw loop is the source loop. `exclude_members=False` is the p1c_groups source draw
  exactly.
- **`layer_matched_nulls`, R10a.** `keep_mlp_members=True` is the default: MLP members stay in their pools, so only
  head members are excluded. `keep_mlp_members=False` is strict exclusion.
- **Loud failure.** A new `NullPoolError` (a `ValueError`) is raised before any draw when a (kind, layer) has fewer
  candidates than members. The message names the set, the layer, the kind, and both counts. Nothing is drawn short.
  Under R10a this can fire only for a head layer with more than 16 members, which no B3 set has. Under strict mode it
  fires for every set with an MLP member.
- **New `kept_members(S, draw)`.** It returns the members of S that a draw contains, in S's order, as `head.L.H` or
  `mlp.L.0` names.
- **`heads_only_nulls`** passes the exclusion through, so the heads_only arm is member-free.
- **Module docstring.** It now describes R10, R10a, the J3 compatibility and the shared-MLP consequence. It no longer
  claims the null body is unchanged from its source.
- **`scripts/b3_patch.py`, set records.** `resolve_sets(names, strict=False)` writes three fields into every set
  record: `exclude_members: true`, `keep_mlp_members` (true unless strict) and `null_rule`. The rule reads "R10a: head
  members excluded, MLP members kept", or "R10 strict: all members excluded". `null_kind` stays "layer_matched" or
  "heads_only".
- **`scripts/b3_patch.py`, per-draw record.** results.json and margins.json record the three fields under `sets`.
  They also record a new `null_kept_members` map, from each null-draw label to the members that draw kept. Under R10a
  that is the set's MLP members, and for a set without MLPs it is empty.
- **New flag `--null-strict`.** It excludes MLP members too. It works for head-only sets, raises before any model
  load for a set with an MLP member, and J4 does not use it.
- **Dry run.** The "sets:" line says "members excluded" and lists the kept MLP members, for example "MLP members kept:
  mlp.6.0 mlp.7.0 mlp.5.0".
- **J3 compatibility.** `null_draws` takes a `label`, which `build_arms` passes as the set name for error messages. A
  set record without `exclude_members`, which describes every record in J3's results.json, is drawn as before R10. So
  J3's own records reproduce J3's draws exactly. Only `resolve_sets` builds records for new runs, and it always sets
  the field.
- **Where nulls are drawn.** `build_arms` draws them before any model load and under `--dry-run`, so a failure shows
  up at the login-node dry run. With `--null 0` nothing is drawn and nothing raises.

### Test changes in `tests/test_b3_patching.py`

- **Kept as they were.** The parity test against the p1c_groups source and the pre-R10 test that fixes the MLP part
  now pass `exclude_members=False`. All four default dry runs are unchanged, as is the cached-tokenizer V-B P2 dry run,
  and all now pass with the default sets, S_all among them.
- **Updated.** A fifth dry run uses `--null-strict` on head-only sets. The tiny-model fakes take `strict`. The af
  end-to-end test asserts the new set fields, and that `null_kept_members` covers every null arm and equals
  `kept_members` of the recorded draw.

### New tests

- **Head-only sets.** For gupta6, gupta_writers, L17H24, S_q and heads_only, resolved through `resolve_sets` and
  `null_draws`, no draw holds a member, and each draw's (kind, layer) histogram equals the set's. Draws hold no
  duplicates and no mlp.0. The same seed gives the same draws and a different seed gives different ones. The seed is
  still NULL_SEED + 1000 × the set's SET_ORDER index, R10a and strict mode give the same draws, and every
  `kept_members` is empty.
- **MLP sets under R10a, the default.** For S_all, S_far and S_ser, no draw holds a head member, the MLP part equals
  the set's MLPs, and the histogram matches. Draws are seed-deterministic and seed-sensitive. `kept_members` of each
  draw is exactly the set's MLP names, and the stats default equals what `b3_patch` draws.
- **MLP sets under `--null-strict`.** Each raises `NullPoolError` naming the set and its first MLP layer. The default
  af, syc and c3 dry runs with `--null-strict` raise naming S_all, layer 5, before any model load.
- **Pool size.** A 16-head single-layer set draws exactly its complement. A 17-head layer raises with "layer 3 head
  has 15 non-member candidate(s) for 17".
- **J3 reproduction.** J3's results.json reproduces all of its recorded null draws through `null_draws`, and its
  bytes are unchanged afterwards.

### Files written

These are the only files changed in the worktree.

- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/spontaneous/stats.py
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/scripts/b3_patch.py
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_b3_patching.py
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/reports/31-handback.md

The throwaway evidence script, /u/swong2/.claude/jobs/230e4716/tmp/r10_evidence.py, is outside the repository and
should not be committed.

## How verified

Tests were run with `-p no:cacheprovider` and BLAS threads pinned to 1.

| test file | mgnp (Python 3.12) | base (Python 3.9) |
| --- | --- | --- |
| tests/test_b3_patching.py, before this ticket | 45 passed | 37 passed, 8 skipped |
| tests/test_b3_patching.py, after | 63 passed | 55 passed, 8 skipped |
| tests/test_mechanism_analysis_p1c_groups.py | 10 passed | 10 passed |

The 8 skips on base are the same pre-existing tiny-model tests, which need nnsight 0.7.0. The J3 reproduction test
ran on both interpreters rather than skipping: J3's results.json is present in the worktree outputs.

**Readers of J3's record.** The ticket named `scripts/b3_premise.py` and `spontaneous/stats.py` as possible readers.
A repository grep for `null_kind`, `null_draws` and `layer_matched` shows that neither reads `null_kind` or the null
draws from results.json. The only code that branches on `null_kind` is `null_draws` in `b3_patch.py`. It accepts both
the J3 record, which has no `exclude_members` field, and the new record.

Hashes after the change:

```
a9d280bc440a5369e37f552ebe50db7ca4dda742758e4f038833749c551126df  spontaneous/stats.py
c95ced7383a52389640b3943f0c02a632340ce9d972aa8cef973ab893f9ee11f  scripts/b3_patch.py
8393f31263ea8e0a8301ff04ede70c69840bc7d10edd1c6f66944bc61eabb4f1  tests/test_b3_patching.py
```

`stats.py` and `b3_patch.py` were hashed into J3's manifest, so their J4 manifest hashes will differ from J3's. That
is expected.

## Execution evidence

All of this is CPU only. It imports `b3_patch` and uses the real 1,024-head and 32-MLP inventory with no model.

**J3 draws R10 would have rejected.** These were read from J3's results.json; nothing was written there. The counts
equal review 03's.

| set at readout | draws holding a member | draw indices | members in each such draw |
| --- | --- | --- | --- |
| gupta6 | 4 of 20 | 2, 5, 8, 9 | 1, 1, 2, 1 |
| gupta_writers | 4 of 20 | 6, 9, 11, 18 | 1 each |
| L17H24 | 1 of 20 | 10 | 1 (L17H24 itself) |
| S_q | 10 of 20 | 2, 4, 5, 6, 7, 10, 15, 16, 17, 19 | 1 each |
| S_all | 20 of 20 | all | 5 to 11 (three are always mlp.5 to mlp.7) |

Under R10a, S_all's draws would still each hold 3 members, its MLPs, and no head member.

**New gupta6 draws, seed 20265025.** Members are L18H28, L16H19, L20H14, L17H24, L15H8 and L15H11. Each draw is listed
in layer order 15, 15, 16, 17, 18, 20. R10a and strict mode give the same draws here.

```
draw 00: L15H26, L15H12, L16H7, L17H5, L18H19, L20H7
draw 01: L15H0, L15H13, L16H1, L17H30, L18H21, L20H2
draw 02: L15H0, L15H7, L16H9, L17H3, L18H11, L20H5
draw 03: L15H21, L15H13, L16H29, L17H13, L18H15, L20H20
draw 04: L15H10, L15H1, L16H6, L17H15, L18H5, L20H23
draw 05: L15H27, L15H28, L16H6, L17H2, L18H23, L20H8
draw 06: L15H13, L15H4, L16H23, L17H14, L18H27, L20H3
draw 07: L15H31, L15H2, L16H28, L17H28, L18H1, L20H16
draw 08: L15H7, L15H10, L16H14, L17H2, L18H8, L20H16
draw 09: L15H23, L15H1, L16H28, L17H18, L18H26, L20H21
draw 10: L15H17, L15H22, L16H28, L17H9, L18H18, L20H29
draw 11: L15H21, L15H22, L16H18, L17H27, L18H2, L20H17
draw 12: L15H3, L15H27, L16H2, L17H21, L18H23, L20H3
draw 13: L15H22, L15H14, L16H23, L17H25, L18H0, L20H23
draw 14: L15H3, L15H22, L16H25, L17H21, L18H21, L20H28
draw 15: L15H5, L15H29, L16H28, L17H2, L18H20, L20H8
draw 16: L15H9, L15H16, L16H14, L17H9, L18H25, L20H28
draw 17: L15H23, L15H22, L16H22, L17H7, L18H31, L20H9
draw 18: L15H30, L15H10, L16H8, L17H30, L18H13, L20H26
draw 19: L15H7, L15H16, L16H25, L17H17, L18H10, L20H20
```

None of these draws holds a gupta6 member. Draws 11 and 13 hold L17H27 and L17H25, which are S_q heads but not gupta6
members. R10 excludes only the tested set's own members.

**New S_all draws under R10a, seed 20261025.** Every draw holds 32 non-member heads with S_all's layer counts, plus
mlp.5, mlp.6 and mlp.7. No draw holds an S_all head: 0 of 20. Every draw's `kept_members` is mlp.6.0, mlp.7.0 and
mlp.5.0. The first three draws:

```
draw 00: L7H13, L7H12, L8H27, L8H7, L8H6, L9H25, L9H27, L9H22, L9H17, L9H2, L9H15, L10H12, L10H4, L10H27, L10H30,
         L10H1, L10H11, L11H17, L11H13, L11H23, L11H29, L11H3, L13H12, L13H19, L13H20, L13H2, L14H22, L15H31, L17H15,
         L17H18, L17H30, L17H1, mlp.5.0, mlp.6.0, mlp.7.0
draw 01: L7H8, L7H13, L8H16, L8H6, L8H1, L9H0, L9H25, L9H11, L9H8, L9H14, L9H21, L10H15, L10H8, L10H21, L10H11,
         L10H7, L10H4, L11H17, L11H23, L11H2, L11H12, L11H10, L13H8, L13H20, L13H25, L13H3, L14H30, L15H11, L17H5,
         L17H21, L17H10, L17H30, mlp.5.0, mlp.6.0, mlp.7.0
draw 02: L7H19, L7H29, L8H8, L8H30, L8H18, L9H14, L9H1, L9H25, L9H28, L9H4, L9H2, L10H4, L10H13, L10H23, L10H1,
         L10H18, L10H10, L11H19, L11H12, L11H13, L11H8, L11H6, L13H25, L13H9, L13H26, L13H13, L14H22, L15H2, L17H5,
         L17H28, L17H0, L17H19, mlp.5.0, mlp.6.0, mlp.7.0
```

Draws 03 to 19 follow the same pattern. The heads_only arm, S_all's 32 heads with seed 20266025, gives 20 draws with 0
member overlaps.

**Default J4 af dry run, real cached tokenizer, no model.** The arguments were `--task af --variant V-B --proxy P2
--sets S_all,S_far,S_ser,S_q,gupta6,heads_only --null 20 --positions post_tag,readout --dry-run`. It finishes cleanly.
The sets line lists the kept MLPs: mlp.6.0, mlp.7.0 and mlp.5.0 for S_all; mlp.6.0 and mlp.7.0 for S_far; mlp.5.0 for
S_ser. The other sets show "members excluded" only.

| quantity | value |
| --- | --- |
| twin pairs | 100 |
| stems | 6 |
| arms | 252 |
| forwards | 152,400 |
| estimated walltime, A100 | 3.69 h, including the model load |
| estimated walltime, H100 | 1.91 h, including the model load |

The forward count is the same as before R10, because exclusion changes which components are drawn, not how many.

**Default syc dry run.** `--task syc` also finishes cleanly: 105 arms and at most 87,200 forwards, with S_all's MLPs
kept. The same af command with `--null-strict` raises the S_all error, naming layer 5, before any model load.

## What is NOT done

- **No job, no model forward, no Slurm.** J3's outputs under `outputs/_studies/b3/j3_sycophancy` were read and not
  written; a test checks their bytes before and after.
- **Ruling text not recorded by me.** spec.md does not yet contain R10a; the lead said they will record it. No other
  ruling, pre-registered rule or frozen file was edited. Nothing under `docs/research` was written except this
  hand-back.
- **Mechanism-analysis source untouched.** `outputs/_launch_mechanism_analysis/p1c_groups.py` and its test are
  unchanged. Its own `layer_matched_nulls` still draws without exclusion, and the parity test compares it with
  `exclude_members=False`.
- **J4 consumers not updated.** Any later reader of J4's results.json, such as a premise script, is not yet written.
  When one is written, it should read `null_rule` and `null_kept_members` from the record.

## Open questions

1. **Does C3 need nulls?** The C3 default runs S_all with 20 null draws. Under R10a it now dry-runs cleanly, but if
   f_C3 reads no null, `--null 0` would save 20 of the 21 forwards per row. This is a budget question, not a blocker.
2. **Should the R5 "non-specific" reading for MLP sets be cross-checked?** Under R10a, the null maximum for S_all
   includes whatever its three MLPs contribute on their own. The heads_only arm gives the reading without shared
   MLPs. Should the R5 label also be reported on that arm, or is the arm descriptive only?
