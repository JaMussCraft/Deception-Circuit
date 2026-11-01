# Independent calibration audit preparation

Preparation PASS; actual calibration remains unaudited and main remains unreleased.

`check_calibration.py` is stdlib-only and imports no production runner, model, tokenizer, torch, notebook, or API. It checks exact frozen SHA/science/provenance/commit, actual allocation/proposal/hash binding, hardware identity and memory, the 32-signature 5,460-forward stress schedule, all 112 forced-only cap64 rows, 29,232 distinct full-vocabulary comparison identities, family/donor/recipient capture scopes and shapes, original-prefix logical readouts, journal/assembly equality, all 48 maximum-file SHA/size bindings, and exact main forecast arithmetic. Maximum benchmark files are read in 1MiB chunks and never JSON-decoded.

Preparation independently reconstructs 30 main signatures totaling 147,648 forwards and 32 calibration signatures totaling 5,460. Synthetic forecast exercise reproduces 7,214s full-main audit charge for CPU10/read cold100/warm2; adding CPU10 adds exactly12.5s to the margined result. This is arithmetic verification, not measured calibration evidence.

After operator supplies the fresh calibration path and immutable job receipts, run:

```
/sw/external/python/anaconda3/bin/python3.9 .scratch/sdr-cue-circuits/calibration-audit/check_calibration.py --calibration ACTUAL --proposal .scratch/sdr-cue-circuits/operator/operations-calibration-3600-ca41bfd.json --main-operations PROPOSED_MAIN_OPS --output .scratch/sdr-cue-circuits/calibration-audit/actual-audit.json
```

Absent `--main-operations`, the forecast uses calibration operations only and cannot establish fit for a new allocation. Audit output always retains the explicit root-release requirement.

Remaining manual independent closure after actual receipts arrive:

- Match external completed Slurm job ID/state/exit/Start/End/reservation/GPU/node to actual allocation operations and logs. Check wrapper final source/cache/software verification; all 57 bound sources and cached weights are independently root/operator-owned checks.
- Match exact GPU class/name/capability/memory/count and software/source/cache identity to intended main; a transfer to a different GPU class or source is invalid.
- Compare every recomputed forecast term to production forecast: cold once per actual signature and class, recurrent maxima, 1,168 packing charges, full9,344/cap64/574,208-control CPU audit, 1,168 attempt reads and2,336 terminal reads, six write classes totaling3,511 with emergency reserve, 25% complete measured subtotal, measured startup/premodel plus each declared buffer once. Require8 reads and8 writes measured/class.
- Check main required seconds against proposed reservation and actual raw allocation/deadline remaining; shutdown is already charged once. Ensure measured premodel time fits declared headroom. Runtime mean length is irrelevant.
- Verify actual output filesystem, retained44,507,365,288-byte benchmark footprint, healthy48 calibration journal publications, and no emergency/extra attempts or errors. Replacing progress16 times is schedule evidence in logs/source, not inferable from one final file.
- Do not interpret calibration outputs, use them for scientific selection, or release main without a fresh actual-calibration PASS and root's separate explicit release.

No source edits, jobs, models, notebooks, APIs, git operations, or subagents were used. Ownership is restricted to this audit directory.
