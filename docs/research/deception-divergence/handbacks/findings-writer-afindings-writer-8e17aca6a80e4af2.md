# Last message of findings-writer afindings-writer-8e17aca6a80e4af2 (2026-11-03T01:03:50-05:00)

I added rows F-dd-001 to F-dd-008 to the findings table, and both checks pass. The lint exits cleanly and findings-check reports 0 errors and 0 warnings.

The rows follow the F-rte-008 row and map one to one onto the worklog's findings F1 to F8. Each row is dated 2026-11-02, marked reviewed, and names its review in the report column. A script confirmed that every number in the worklog's F1 to F8 appears in the matching row, and every evidence path exists.

| id | claim in one line | commit |
|---|---|---|
| F-dd-001 | The static weight read fails both pre-registered rules, and the copy read has almost no power. | 54cd1eb |
| F-dd-002 | Under the pressure clause, the layer 17 quartet's readout attention moves on FAR and SER. | c6752c0 |
| F-dd-003 | The sycophancy transfer sits mostly after the cue tokens. It is specific there only against random heads, not to deception. | c6752c0 |
| F-dd-004 | SDR is query-side on the B1 code path, and its loop closes just above the bar. | c6752c0 |
| F-dd-005 | D1 is null on every task under the 10-point rule. The null is on size, not on existence. | 4bdf6bb |
| F-dd-006 | The system-turn listener sentence moves no compliant answer to the honest gate. | a0936e5 |
| F-dd-007 | The user-turn acknowledgement is null and its flip pools are empty. The visible arm complies slightly more. | a0936e5 |
| F-dd-008 | The D2 premise passes by one point, on SDR only, from the classifier only. The gap comes from clause wording. | fb2cb9e |

- **F-dd-001 uses the fallback commit.** Its run recorded b324c50 with a dirty tree, because the script was not yet committed.
- **F-dd-006 takes the reading code's commit.** Its input scores come from the D1 job at 4bdf6bb.
- **F-dd-004 is still one row.** It holds both the query-side verdict and the loop-closure result. The existing rows F-rte-005 and F-rte-006 split that same pair, so you may want two rows. That would break the one-to-one id mapping, so I left the choice to you.
- **There is no placeholder for F-dd-009.** It goes directly after F-dd-008.

No git was run. I'm waiting for the F-dd-009 text and the README task.

Files changed:
- Edited `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/FINDINGS.md`
- New hand-back `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/reports/11-findings-handback.md`. Its number may clash if the follow-up reviewer also writes an 11.
