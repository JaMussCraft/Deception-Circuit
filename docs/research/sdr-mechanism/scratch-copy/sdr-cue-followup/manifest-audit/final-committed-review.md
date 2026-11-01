# Independent final committed manifest rebind

**PASS; no manifest or source-binding blocker found.** This closes the independent input/source rebind for commit `29492146127f56c05a4087b1bfdeea0e63a4d24a`. Runtime/operator checks and actual calibration remain separate.

Final protocol SHA `b2c7fd65ccb67e93f463553044569248fe85a80b8e1bd72ffef28df2cb3b5fa0`; science `fd0bf5f1415b4ea951d6396753b64ad7c0061d883eeca28960b55a9bf9423b6e`; provenance `952ef49022dc4d676080a9a5d13a8c37954327014a4c4c3ecb6f5a76173af297`; actual spec `b06fc61df13c9c64563d7043fd06502658fc32539cb659639038812b6c1a0cbe`.

The full scientific payload is recursively identical to accepted provisional e14a92. The existing independent expectation file remains byte-identical. Reused independent checks pass all 384 main inputs, 640 pairs, S/C_S memberships, 3,840 interventions, 4,224 outcome IDs, 528 ordered batches, 480 position maps, 104 forced/natural calibration rows, three system-E no-op identities, numerical/analysis metadata and actual rubric/spec bytes. Total including full-payload comparison: **2,153,693 recursive comparisons**.

Current HEAD equals the final declared commit. Every one of 63 source bindings matches both the committed Git blob and current filesystem bytes; all 57 inherited parent bindings remain preserved. Each blob's Git object identity was also independently verified from its length/content. Only read-only `git rev-parse` and `git cat-file --batch` were used. No production module was imported or model weight opened; no production source, GPU, notebook, scheduler or mutable git operation was performed.

Reproduce with:

```bash
/sw/external/python/anaconda3/bin/python3.9 .scratch/sdr-cue-followup/manifest-audit/final_rebind.py
```

Detailed receipts: `final-committed-rebind.json`, including all 63 committed blob IDs/SHA256 values, original checker hash and final rebind script hash. Original expectations/oracle and provisional receipts remain unchanged.
