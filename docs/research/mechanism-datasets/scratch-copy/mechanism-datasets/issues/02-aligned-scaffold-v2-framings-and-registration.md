# 02 — Aligned scaffold v2, round-1 framings, neutral pool and task registration

**What to build:** `dataset/deception_v2.py` (the one scaffold for FAR/SDR/SER v2, the four prompt
conditions, the length-matched neutral twin), the clause and neutral-sentence screens, the four round-1
framings with 20 flavor clauses per task each (plus the 5 shared clauses, spec §13.3), the neutral pool, the `far_v2`/`sdr_v2`/`ser_v2` task registrations,
the CONTEXT.md entries, and a CPU scaffold report proving the alignment and length constraints.

**Status:** in-review
**Type:** task
**Blocked by:** None. Runs in parallel with 01; you own the spec §5 contract and must implement it exactly.
**GPU allocation:** 0 h. OpenRouter allowed for clause screening (log it in the ledger).

## Facts to build on

- v1 scaffold machinery: `TemplateVariant`, `TaskSpec`, `_variants`, `build_prompt`, `build_prompt_pair`,
  `generate_instances`, `realize_instance`, `assert_aligned_pair` in `dataset/deception_common.py`
  (`:85-583`). Reuse the classes; do not edit `dc.SPECS` (`:182`; pinned by
  `tests/test_deception_common.py:54`).
- v1 bug to avoid: `_variants` concatenates the suffix to the designating sentence with no separator
  (`:162`, `:174`). v2 joins `intro, designation, suffix, clause` with `_join` so every sentence has one
  leading space.
- Clause surgery: `dataset/clause_surgery.py` (`remove_clause`, `replace_clause`). Length-matched
  replacement: `dataset/matched_honest.py` (`select_matched_instruction` `:210`, `build_pool` `:237`,
  `clause_span` `:132`, `assert_clause_aligned_pair` `:157`) and its ladder file
  `dataset/deception_pools/matched_honest_candidates.json`.
- Clause flavor rules and anchor examples: `project_context/prompts/deception_task_{far,sdr,ser}.md`
  ("Pressure clauses" sections). Audit §0.4 lists what drifted in v1 (caps suffix, two-sentence caps SER
  clauses with imperative tails, "the second finding" SDR clauses).
- Registration points: `tasks/__init__.py` (`get_task` chain, `list_tasks` `:151`, `DECEPTION_TASKS` `:157`),
  `config.py` `_HYPERPARAMS` (`:121` is the SDR entry to copy), `tasks/deception.py:27` (`dataset_dir`),
  `evaluation/context.py:161` and `evaluation/circuits.py:317` (hard-coded v1 names).

## Acceptance criteria

### Scaffold and conditions
- [x] `dataset/deception_v2.py` implements spec §5: `SPECS_V2`, `make_spec(task, suffix, ser_wording)`,
      `load_framing(path)`, `load_neutral_pool(path)`, `realize(tokenizer, spec, framing, inst, neutral_pool,
      max_seq_length=120)`. Scaffold strings exactly as spec §4 (SDR v1 designating sentence per variant, spec §14.G2; items unquoted in the user turn, §14.G3) (predicate pairs, user turns, stems, `audit`
      and `lab` variants, no `Only respond with`). SER wordings `A` and `B`; `ser_wording` must be None for
      FAR/SDR and required for SER.
- [x] Suffix: `SUFFIX_CANDIDATES` holds at most 2 normal-case, non-imperative sentences sharing one frame with
      only the inversion predicate word varying; `SUFFIX` names the round-1 choice. Record the reasoning in
      the module docstring.
- [x] `realize` returns the record (with `neutral_prompt` for the prior-balance check: only the designating
      sentence replaced by the variant's neutral designation, suffix and clause kept) plus
      `conditions{pressure, nopressure, neutral, honest_instruction}`,
      each `{clean_prompt, corrupt_prompt}`, `neutral_id`, `neutral_text`, `pressure_id`, `framing_id`,
      `suffix`, `ser_wording`. `nopressure` = `remove_clause`; `neutral` = `replace_clause` with the selected
      neutral sentence; `honest_instruction` = `replace_clause` with `dc.HONEST_INSTRUCTION`.
- [x] Neutral selection: among pool sentences whose full prompt has exactly the pressure prompt's token count
      (both streams), pick deterministically by `instance_id` (e.g. sha1 mod k); assert with
      `assert_clause_aligned_pair`; raise if none fits.
- [x] Every condition of every realized record passes `dc.assert_aligned_pair` and `<= 120` tokens.

### Screens
- [x] `screen_clause(text, task) -> list[str]` (empty list = clean). Mechanical rules: exactly one sentence;
      no all-caps word of 2+ letters; first word not an imperative from a listed set (Say, Tell, Answer, Name,
      Report, Show, Mention, Respond, Reply, Choose, Pick, Recommend, Point, Present, Emphasize, Highlight,
      Hide, Avoid, Keep, Make, Ensure, Do, Don't, Never, Always, Preserve); no item word from the item-pair
      pool; no predicate word of any task (v1 and v2 words); no ordinal or position word (first, second,
      third, other, former, latter, last, top, bottom, left, right, earlier, later); flavor vocabulary: SDR
      and SER clauses contain no truth/honesty/accuracy/lying words; SER clauses contain no disclosure words
      (see, seen, show, shown, tell, told, learn, mention, surface, reveal, disclose, report, say, hear);
      FAR clauses contain no disclosure-conditioning or decision/impression words (see, seen, shown, learn,
      surface, notice, impression, decide, decision, confidence, walk away). Lists live in module constants.
- [x] LLM screen (mgnp python, OpenRouter): each clause is labelled truth-level / disclosure-level /
      outcome-level / neutral / instructing. A clause is accepted only if the mechanical screen is clean,
      the label matches its task's level, and it is not instructing. Disagreements are resolved by you,
      recorded per clause in `reports/02-clause-screen.json` with the judge text.
- [x] `screen_neutral(text) -> list[str]`: one sentence, no item, predicate, ordinal/position, honesty,
      consequence, reward, threat or imperative vocabulary, no second-person instruction.

### Pools
- [x] Four round-1 framings in `dataset/deception_pools/v2/framings/r1_{rolegoal,stake,consequence,selfinterest}.json`:
      `{id, family, round: 1, hypothesis, clauses: {far_v2: [20], sdr_v2: [20], ser_v2: [20]}}`, clause ids
      `<framing>_<task>_<NN>`, families from {role_goal, stake_incentive, consequence, self_interest}. Each
      hypothesis says what the framing should do to the inversion and identity contingent rates per task and
      why. `consequence` stays close to the v1 threat style so round 1 has a baseline against the audit.
- [x] Shared clauses (spec §13.3): `load_framing` appends the 5 shared mechanism-neutral clauses as slots
      20-24 (ids `shared_00`..`shared_04`, `shared: true`), identical in every task and framing. Reuse
      `dataset/deception_pools/pressure_shared.json` verbatim if all 5 pass the generic mechanical rules
      (flavor rules do not apply) and the LLM screen labels them neutral, not instructing; otherwise write
      `dataset/deception_pools/v2/pressure_shared.json` with replacements and record why per clause.
- [x] All 240 flavor clauses pass both screens. Per framing, per-task median flavor-clause token length
      within 1 token across the three tasks; all flavor clauses in one band no wider than 6 tokens (shared
      clauses are exempt from the band).
- [x] `dataset/deception_pools/v2/neutral_candidates.json`: screened sentences ordered by token count; every
      clause of every round-1 framing, the 5 shared clauses included, has >= 2 equal-length neutral candidates under every task, variant,
      suffix level and SER wording (checked with the real tokenizer on a sample of that clause's prompts;
      the harness asserts every instance).

### Registration and glossary
- [x] `tasks/deception_v2.py` with `FARv2Task`, `SDRv2Task`, `SERv2Task` (`name` = `far_v2` etc.,
      mechanism as v1). `tasks/__init__.py`: `get_task` and `list_tasks()` gain the three ids; new
      `DECEPTION_TASKS_V2 = ["far_v2", "sdr_v2", "ser_v2"]`; `DECEPTION_TASKS` and `--joint-tasks` choices
      unchanged.
- [x] `config.py`: `("llama","far_v2")`, `("llama","sdr_v2")`, `("llama","ser_v2")` identical to `("llama","sdr")`.
- [x] `evaluation/context.py:161` and `evaluation/circuits.py:317` also cover `DECEPTION_TASKS_V2`.
- [x] CONTEXT.md: add **Contingent Survivor**, **Framing**, **Pilot Cell**, **Suffix Policy** and
      **Neutral-Clause Twin**. Under Honest Twin and Honest Condition record (spec §13.10): the v2 primary
      honest twin replaces the Pressure Clause with a length-matched neutral sentence on the same instance
      ids, so D minus H isolates pressure processing; the nopressure twin is secondary; this contrast sits
      close to the Format Circuit contrast and is a deliberate change from the v1 harvested twins.

### SER literal truth (spec §4, §13.8)
- [x] `ser_literal_truth_violations(record) -> list[str]`: asserts, per stream, that the SER deceptive target
      is the item the system turn makes favorable in that stream and never the one it calls unfavorable;
      `realize` raises on a violation.
- [x] `SER_UNFAVORABLE_STEM_LEXICON` (worry, concern, risk, problem, fail, bad, unfavorable, ...) and
      `ser_wording_flags(wording)`: a wording whose question or stem ascribes an unfavorable property to the
      answer is flagged `judge_decided`. Wording B must come out clean, wording A flagged; the scaffold report
      lists each wording's status, and ticket 04's purity judge decides flagged wordings.
- [x] Tests: a hand-built SER record whose target is the unfavorable item is rejected; both wordings get the
      expected flag.

### Scaffold report (CPU, real tokenizer)
- [x] `dataset/check_v2_scaffold.py` writes `reports/02-scaffold-report.json` and `reports/02-scaffold-report.md`:
      per task x framing x suffix x SER wording x variant x condition, prompt-length summary and histogram
      over a 1,000-instance sample; predicate-word and item-word tokenization (item pairs failing the
      single-token gate are listed and dropped from v2 use); asserts every spec §4 length constraint (<= 120
      everywhere, common D-prompt band <= 12 tokens per suffix level, cross-task D-prompt median gap <= 6 tokens, spec §14.C1, with the per-task user-turn token counts printed); 3 rendered
      sample pairs per task with token boundaries and the corruption slot marked.

### Tests (CPU)
- [x] `tests/test_deception_v2.py`: one instance rendered under the three tasks differs only in the predicate
      pair, the question/stem and the clause; suffix joined with exactly one space (no ".T"); `nopressure`,
      `neutral` and `honest_instruction` equal the pressure prompt outside the clause span; neutral token
      count equals pressure token count and selection is deterministic; alignment holds in every condition;
      an over-length prompt raises; a new snapshot test pins the CURRENT `dc.SPECS` values (keys far/sdr/ser,
      FAR weak/strong, SDR damaging/harmless, SER unfavorable/favorable) because
      `test_three_specs_registered` already fails on the base (spec §14.C3), and it must pass both before and
      after your edits; framing schema validation rejects 19 flavor clauses,
      duplicate ids, unknown family, empty hypothesis.
- [x] (one anchor exempted by design, see Comments) `tests/test_clause_screen.py`: one positive and one negative case per screen rule, for clauses and
      neutral sentences. Every anchor example in the three task specs' "Pressure clauses" sections passes
      `screen_clause` for its own task (assert); whether it fails another task's mechanical screen is reported
      in the test output, not asserted, because cross-task separation is the LLM screen's job.
- [x] `tests/test_v2_registration.py`: `get_task("sdr_v2").dataset_dir(args)` gives `<data>/sdr_v2`,
      `<data>/sdr_v2_honest`, `<data>/sdr_v2_nopressure` per condition; `default_hyperparams("llama","far_v2")`
      equals the SDR dict; `DECEPTION_TASKS` is still `["far","sdr","ser"]`; `train.py --task joint` default
      subtasks unchanged; `condition_of({"task": "far_v2", "deception_condition": "honest"}) == "honest"`.
- [x] Full suite in both envs; new failure names: none.
- [x] Review written to `reports/02-aligned-scaffold-v2-framings-and-registration-review.md`.

## Hand-back

No GPU. Hand back with the file list (code, pools, tests, CONTEXT.md), the scaffold report path, the clause
screen report and the OpenRouter ledger entry.

## Comments

Implementer (impl-02), 2026-10-19. Full narrative: `reports/02-ticket-02-report.md`.

**Built.** The v2 scaffold module (`dataset/deception_v2.py`), the clause and neutral screens plus the LLM screen CLI (`dataset/clause_screen.py`), the CPU scaffold report (`dataset/check_v2_scaffold.py`), four round-1 framings of 20 flavor clauses per task each, an 85-sentence neutral pool, the v2 task registration and the CONTEXT.md entries. The 5 shared clauses are `pressure_shared.json` reused verbatim: all pass the generic rules and the judge labels every one neutral.

**Verification.** `reports/02-scaffold-report.{json,md}` passes every check. The D-prompt band is at most 11 tokens and the cross-task median gap at most 5. The longest prompt is 97 tokens. Every clause has at least 6 equal-length neutral candidates. All 41 item pairs pass the single-token gate. `reports/02-clause-screen.json` accepts all 245 clauses, and its five draft rejections are resolved per clause with the judge text.

**Tests.** The base env shows 8 failed, 1546 passed and 58 skipped. mgnp shows 8 failed, 1699 passed and 19 skipped. The failures are exactly the 8 baseline names, so there are no new ones. The three new test files (122 tests) pass in both envs, with the real-tokenizer test running in both.

**Slurm and ledger.** No Slurm jobs and 0 GPU-h. The ledger has one OpenRouter entry: 358 calls to anthropic/claude-sonnet-4.5, about 1.30 USD.

**Deviations.**
- The SDR task-spec anchor "...reaches the client." fails the binding item-word rule, because client/server is in `item_pairs.json`. The anchor test asserts exactly that one violation for it and clean screens for every other anchor. The cross-task results are printed, not asserted.
- Three anchors were lengthened by a few words to reach the 12-to-16 token band.
- The word lists add inflections and a few synonyms. All of them are module constants.
- The review was done without the git-diff skill, because git is forbidden for this ticket. It is written up in `reports/02-aligned-scaffold-v2-framings-and-registration-review.md` and has no unresolved findings.

**Open.** `component_analysis/dataloaders.py` `MECHANISM_TASKS` still lists only v1 ids. It is out of scope and needed before any v2 component analysis.

**Status.** Set to in-review, as the orchestrator requested, rather than resolved.

**Addendum (test timing and cache).** The full suites ran before three small edits: two test tidy-ups, a weak-keyed length cache in `deception_v2.py`, and the screen CLI now carrying `resolutions` and `judge_notes` across reruns. The three new test files were re-run afterwards in both envs, 122 passed each, with `test_clause_screen.py` re-run after the last edit. The judge cache is saved at `reports/02-clause-screen-cache.json`. Pass it as `--cache` when rounds 2 and 3 re-screen, so unchanged clause texts are not re-paid.

**Review round (2026-10-19, supersedes the numbers above).** All 9 should-fix review items are fixed, as the orchestrator ruled. Details are in `reports/02-aligned-scaffold-v2-framings-and-registration-review.md`.
- **Item words match inflections.** 22 clauses were rewritten. shared_02 is replaced in the new `dataset/deception_pools/v2/pressure_shared.json`, which records why. The neutral pool dropped 6 sentences, leaving 79. Four anchors now collide ("client", "weights" twice, "funding"), each pinned to its single violation in the anchor test.
- **SDR referents are spread out.** No marker appears in more than 25% of a task's flavor clauses; SDR now uses "flagged" in 3 to 4 of 20 per framing.
- **The judge prompt is at v2 with one written goal-over-answer rule.** Six FAR role/goal clauses were judged instructing under it and rewritten. All 245 clauses were re-judged and accepted.
- **Resolutions survive a re-screen.** Hand-written resolutions and judge notes are carried forward.
- **The tests are real.** The duplicate check is reachable, determinism is checked against an independent sha1 derivation, the missing rule cases have tests, and the single-token gate is computed.
- **The suffix changed.** It is now "... matters most here." The length checks were re-run.

The scaffold report passes every check on the final code: D band at most 11, median gap at most 5, longest prompt 95 tokens, at least 4 neutral candidates per clause. Final full suites show base at 8 failed, 1571 passed and 58 skipped, and mgnp at 8 failed, 1724 passed and 19 skipped. Both match the baseline names, with no new failures. OpenRouter total is 610 calls, about 2.30 USD, in two ledger entries.

**Second review hand-back (2026-10-19).** The orchestrator forwarded the reviewer's nine items in full. All nine were already fixed in the round above. For item 6, a second test now compares independent generations at the same seed (records identical) and at a different seed (instances and neutral choices differ). The review is two-source. Final full suites show base at 8 failed, 1572 passed and 58 skipped, and mgnp at 8 failed, 1725 passed and 19 skipped. Both are the baseline names, with no new failures. Every checkbox still holds on the final code, so all stay ticked; the anchor box keeps its exemption note, which now covers four anchors.
