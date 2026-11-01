# V5 frozen-head inventory — October 24, 2026

**Verified: new30 shares only two heads with oldD69: L14H31 and L17H27.** It shares three heads with the exact original 103-head restricted union; the third is L12H2 from F only. New23 shares L14H31 with D and L12H2 with F. Neither new mask shares any head with the original H56 support. Membership alone does not identify function.

|Frozen mask|D69 intersection|H56 intersection|F68 intersection|Original union103 intersection|Outside original union|
|---|---|---|---|---:|---:|
|new23|L14H31|none|L12H2|2/23|21/23|
|new30|L14H31, L17H27|none|L12H2|3/30|27/30|

The exact historical union was reconstructed from the original coarse SDR seed 42 D69/H56/F68 masks and matches both the original W-union manifest candidate list and v4 manifest’s preserved `amendment.union_heads`. Its canonical head-list hash is `6c5943656abc881d8ff949f776a3fa9dc11e7161254a2c16738c7306b8624420`. These are the September 22 D/H runs and October 13 no-pressure F run listed below, not fine-grained or seed1/seed123 variants.

|Additional head in new30|D69|H56|F68|Original union103|Preexisting matched formal role|Historical SDR single-head KO drop ±SE|
|---|---|---|---|---|---|---:|
|L7H31|no|no|no|no|unavailable|-0.0098 ±0.0086|
|L8H10|no|no|no|no|unavailable|+0.0046 ±0.0075|
|L13H15|no|no|no|no|unavailable|+0.0054 ±0.0061|
|L13H23|no|no|no|no|unavailable|+0.0059 ±0.0135|
|L17H27|yes|no|no|yes|unavailable|+0.2858 ±0.0331|
|L19H13|no|no|no|no|unavailable|+0.0522 ±0.0048|
|L20H19|no|no|no|no|unavailable|+0.0017 ±0.0022|

Six of the seven additions are outside every original D/H/F support; only L17H27 is in D. This is a conditional seven-head difference on top of the other 23 replacements; it is not a seven-head-only circuit or attribution to any individual head.

The preexisting role cell is `Deception-Circuit/outputs/_analyses/sdr-dh-core/dh_core__leaf/sdr/`: exact matching D/H operands, `(D&H)-m` composed at leaf granularity, 43 shared heads. None of the 30 frozen heads belongs to that cell; therefore no matched formal role annotation is available for any of them. Its 43 formal roles are themselves `unknown/insufficient`, with path patching missing. No roles were imported from its fine/seed1/seed123 reference columns or from other circuits.

The final table column is an existing measurement, not a role: `sdr-dh-core-kosweep/dh_core__leaf/sdr/knockout/sweep.json` contains a full-model single-component interchange sweep on 100 historical SDR cases. The matching head-table circuit operands were checked. Positive drop means the head supported that task’s target over its distractor under item-swap-corrupt interchange; it does not establish deception specificity. All seven are below that artifact’s 0.4-logit flag threshold (which is explicitly not a significance test). That donor policy/task/readout differs from V2’s independent neutral-H replay, so these values do not explain or predict the frozen V2 joint-mask contrast.

Whole-head versus leaf overlap: the bound coarse masks have binary head/block gates and no partial-neuron gates. Their adjacent expanded `active_nodes.json` files match the same head sets and select exactly 128 attention leaves per live head, with zero partially selected heads. Therefore whole-head membership and **any attention-leaf overlap coincide for these exact three originals**. We did not reinterpret an arbitrary fine circuit’s “any selected neuron” as whole-head membership. MLPs are excluded from this head inventory; the all-MLP operand in the historical core is explicitly subtracted.

Provenance caution: use `config.coarse.json` for these actual coarse masks. The adjacent base `config.json` serializes different gate flags; relying on it alone would misdescribe the support. All matching coarse configs record seed 42, Llama 3.1-8B-Instruct, SDR, nls0.3; D/H/F conditions are deceptive/honest/nopressure.

Exact source paths and SHA256:

- D: `/projects/beto/swong2/Alignment/Deception-Circuit/outputs/llama-8b-instruct_sdr_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742/active_nodes.coarse.json` — `110a7a87bd2bf5dc9abdffa6d0efed20549b0dd4b2319ebfb0f57cdc8126c536`
- H: `/projects/beto/swong2/Alignment/Deception-Circuit/outputs/llama-8b-instruct_sdr_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_260922-092743/active_nodes.coarse.json` — `98abc1f4c97a54b6f70aa53b62c999428c619bb2cfb851c008909c94f5413562`
- F: `/projects/beto/swong2/Alignment/Deception-Circuit/outputs/llama-8b-instruct_sdr_coarse/nls0.3_nopressure_noedge_noan_nomh_nomo_nomb_261013-204850/active_nodes.coarse.json` — `833aceb454d7bba6c1e049c9a0ce95d07369e948193fb64d765b02ac6cf3fa06`

Machine inventory: `transfer-v5/v5-frozen-head-inventory164.json`, SHA256 `cae9af25458392292c68cc7c83f081acdc749bc4ebe9210cb3d0e4a3ea39fa5b`. It records all 30 head memberships, attention-leaf counts, original 103 heads, all artifact hashes, matched annotation provenance and limitations. CPU JSON/set/hash checks passed; no GPU, API, model load, source/core edit, data change or reselection occurred. Reports 160/161 remain unchanged.
