# Last message of findings-writer afindings-writer-8e17aca6a80e4af2 (2026-11-03T01:05:33-05:00)

The handoff README is drafted and passes lint. Its reserved GPU-hours figure differs from the lead's brief.

The file is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/README.md`.

It follows the lead's structure: question, verdict, one bullet per finding F-dd-001 to F-dd-009, what the controls say, open leads, what was not done, budget and pointers. The marked placeholder for the review 06 wording on F9 is the first open lead. The page is about 1,400 words, near the two-page limit.

Points I reported to the lead:
- **Reserved GPU-hours.** The brief says 11.33, but the ledger and RESUME give 10.58 over reservations r-001 to r-011. I wrote 10.58. The actual is 3.38 GPU-hours, which matches the brief's "about 3.4".
- **The F-dd-009 bullet.** I wrote it from hand-back 10 and marked it as waiting for review 06. The lead will replace it with the reviewed wording.
- **Job ids.** They come from the hand-backs and reviews, not from Slurm. Hand-back 07 names one more job, 23443934, that I could not place, so the README leaves it out.
- **Three extra open leads.** I added them from the reviews' recommendations: a readout beyond the first token, a measure of the second-turn refusals seen only under D, and a replication of SDR's narrow loop closure. The lead can cut them.

FINDINGS.md has no F-dd-009 row yet, and no git was run. I'm waiting for the F-dd-009 text.
