# Mechanism analysis of the coarse v2 circuits: handoff

**Status:** done. The branch was merged to main on 2026-10-28 as commit 7e91f8e, and no session owns this direction.
The full record is [synthesis.md](synthesis.md); this page only says where to look.

## Question

The model is Llama-3.1-8B-Instruct. The three deception tasks are FAR (Falsified Audit Report, a fabrication task),
SDR (Selective Disclosure Report, an omission task) and SER (Selective Emphasis Report, a pragmatic distortion task).
Each task has a deceptive condition D, in which a pressure clause pushes the model toward the misleading item, and
three comparison conditions: H, the neutral-clause twin that replaces the pressure clause with a neutral one; F, the
same prompt with no pressure; and I, an instructed-inversion control in which the prompt openly asks for the wrong
answer.

The direction asked how the six coarse heads-only v2 circuits (one D circuit and one H circuit per task, NLS 0.3, seed
42) and the components around them carry the pressure effect. In particular, it asked whether a small set of
components mediates the effect on held-out instances, how the pressure enters that set, whether the set is specific
to deception, and whether the three tasks use different machinery.

## Verdict

- **FAR and SER:** a greedy set of 20 components removes most of the pressure effect on the held-out sample, 0.893
  of it on FAR and 0.904 on SER. Each set also carries the answer item, so the pre-registered outcome is A prime, not
  a clean pressure mediator.
- **How the pressure enters:** on both tasks most of the set's head weight sits on heads that read the pressure clause
  through their keys or values, 0.74 on FAR and 0.83 on SER. Both sets therefore read as clause readers.
- **SDR:** no set of 20 or fewer components passes, so SDR is outcome B. Its best greedy set reaches 0.664.
- **Not deception-specific:** on paired instructed-inversion instances the FAR and SER sets also remove more than half
  of their deception effect. They count as instructed inversion machinery. Both I pools are below the 300-id minimum
  the spec set, so this reading carries that limitation.
- **The shared core** of the circuits behaves as answer machinery on all three tasks. No exclusive or difference set is
  deception-specific, and the head-level tests for a difference between the tasks all fail. The one pre-registered
  sign of a difference is three mid-layer MLPs that lean toward deception on SER alone.

The user's framing on 2026-10-28 was that a deception-specific mechanism is not the goal. Deception plausibly reuses
ordinary machinery, so later work characterises the shared route.

## Where the claims live

- `docs/research/FINDINGS.md`, rows `F-mech-001` to `F-mech-013`: one row per claim, each at most `reviewed`.
- [synthesis.md](synthesis.md) section 2: the claims table with every pre-registered prediction, its rule, evidence
  and verdict. Section 3 holds the descriptive and exploratory readings, which decide nothing.
- [synthesis.md](synthesis.md) section 5: the limitations, numbered from `L1` to `L25`. The most important are the
  single seed, the I pools below the minimum, and the instructed rather than spontaneous deception.
- The curated tables of record are in this directory under `phase1/`, `phase1a/`, `phase2/` and `phase3/`. The
  figure data is in `figures/` and the instructed-inversion record is [inversion-control.md](inversion-control.md).
- The working record (spec, rulings, tickets and phase readings) is in the Alignment checkout under
  `.scratch/mechanism-analysis/`. The raw cells are ignored by git and sit under `outputs/_analyses/` in the main
  checkout, in the directories named `mechanism-analysis-p1`, `mechanism-analysis-p2` and `mechanism-analysis-p3`.
- Spend is in [ledger.json](ledger.json), converted from the working record. Section 7 of the synthesis lists every
  job: 20.5 of the 35 Bridges-2 H100 GPU-hours were booked, and no Delta GPU time was used.

## What is closed

Phases 0 to 3 and the synthesis are complete, and their verdicts stand as written. Ticket 07, the seed replication,
was never triggered, because no headline claim rests on the identity of the small exclusive sets. The SDR 32-MLP path
grid was not run, because SDR is outcome B. None of these is an unfinished job.

## Useful next questions

These are new proposals, costed in [synthesis.md](synthesis.md) section 6. None has been started.

- Path patching of the FAR and SER deciding sets on the held-out sample, to turn the clause-reader call into a
  held-out result.
- Rebuilding the I pools for FAR and SER above 300 ids and rerunning the paired inversion contrast.
- Seed replication on Delta, which would put the exclusive head identities on firmer ground.
- The SDR route outside the analysed components, which needs the 32-MLP grid and a cap approval from the user.

Bridges-2 is expected to go offline around 2026-11-09, so any follow-up after that date runs on Delta.
