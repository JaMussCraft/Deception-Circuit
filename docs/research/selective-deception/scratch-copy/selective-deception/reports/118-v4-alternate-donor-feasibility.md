# Alternate honest-donor feasibility

October21,2026. **Feasible as one separately identified, validation-only diagnostic.** Reverse the existing rotation within each frozen alignment-signature group. This changes the donor for117/119recipients; the remaining two form a size-two group and have no other nonself donor under the same alignment rule. Preserve all119recipients and explicitly identify those two unchanged controls. No runtime/source, manifest, mapping artifact, mask, job, authorization or ledger was changed by this review.

The existing runner sends each recipient's original-view D and H clean prompts through the recipient stream, and sends the **same other cluster's original-view H clean prompt** through both donor streams (`selective_mask_runner.py:178–193`). At each closed head, the dual-stream attention replaces that recipient head's output with the corresponding donor head output at every aligned position (`models/llama_node.py:259–263`). This is interchange replacement, not zero ablation. “Honest donor” names the H instruction policy; it does not guarantee the donor answers truthfully or transfers the recipient's truthful answer.

## Exact proposed map

Use the unchanged validation cluster list from `manifest-W-all-init1.json`, already sorted by `cluster_id`. Group by the tuple of H-clean prompt lengths in order `(original,reversed,free_response,alternative)`, exactly as `_signature` does. For each group's existing ordered IDs `[c0,...,c(n−1)]`, retain the original map `ci→c(i+1 mod n)` as the control and define the sole alternative as **`ci→c(i−1 mod n)`**. No outcome, label, capability, or effect size chooses a donor. The alternative is a deterministic inverse permutation, not an independent random sample.

| Signature | Group size | Changed donors |
|---|---:|---:|
|113,113,90,95|22|22|
|114,114,91,96|51|51|
|115,115,92,97|40|40|
|116,116,93,98|2|0|
|117,117,94,99|4|4|

SHA256 uses canonical JSON with sorted keys, compact separators, UTF8, `ensure_ascii=False`, `allow_nan=False`:

- Original map: `4e6b8a1359ead8f6720f35baef582bded3e35a0ed6e17c2039673dbde03b031f`.
- Proposed inverse map: `252b05f893ff9b568b4472dabbefe2d431c6af715f2b2ea3b04009856c111dd6`.
- Parent manifest file SHA256: `306185555a147a8cfa77218d5c2ca30a006193e32955e44842e8a1aca3598c48`.
- Unchanged validation object hash: `c528f8796c8655b76d45a5a6a837d3e612ca54fe7167f90dbaeaaf9a87751315`.
- Unchanged cluster-list hash: `94d3dcb2d80d9fa5159add98882fdb2956b0e54134b6111c0844cb5e0c0f1b5d`.
- Unchanged-donor recipients: `8cad0a2fe65917131d84c273719986e2947af772deac3daba7ae0bb867b5b547`, `f9146678ce00a0d03ec2d6ecf3b5730170e4d4e000afb1e531243d47c216483a`.

Read-only stdlib checks on frozen validation metadata verified both maps are bijections on exactly119IDs; donors differ from recipient cluster/source; and all four views, both D/H recipient policies have identical donor/recipient length and attention mask with distinct prompt text. The alternative satisfies the existing structural/alignment invariants. It deliberately fails the legacy validator's **specific forward-rotation equality**; do not disable that validator or rewrite the frozen manifest to pretend otherwise.

## Clean implementation boundary and controls

A later separately reviewed diagnostic should validate the unchanged parent manifest and source-bound SDR/WT reference inventory with the original helpers, then construct a validation-only shallow copy with just its `donor_map` replaced. Validate that copy independently using the explicit algorithm, expected hashes, bijection/nonself/all-view alignment checks above. Bind a new diagnostic envelope to the parent manifest SHA/hash, both mapping hashes, unchanged cluster/prompt/token/label hashes, old frozen allW28 export SHA `e13ef7b04e952f07933766e1d39692c3233cf0334e77d7388820ff8a34839144`, original selection receipt, runtime source/model/package/hardware identity, cache/inventory identities and diagnostic source bytes. Do not pass the derived copy as an apparently unchanged training manifest, resume a fit, or reuse output identities.

Freeze four conditions: original-map intact/full28 and inverse-map intact/full28. Use the same mask and recipients in fixed order; keep WT donor mapping/evaluation unchanged. All-open identity under **each** SDR mapping must preserve source-bound D/H argmaxes, finite label-logit differences<=.02, and existing WT no-op tolerances abs(KL)<=1e-6 and abs(NLL−referenceNLL)<=1e-6. Re-run original full28 as the same-allocation anchor and compare to report114's validated result. The two unchanged donor rows should reproduce across mapping conditions. Separate prospective per-example comparisons for all119 and the structurally changed117rows are useful; neither subset may select masks or donors.

Report paired mapping shifts in D surrogate, D probability and direct D-minus-H logit margin, plus H loss/gain cluster identities and H truthful-NLL changes. Intact-normalized mapping effects help expose control drift. WT is an unchanged-intervention control, not an extra donor-robustness experiment. No addback panel, optimizer, head ranking, pruned export or mask grid is needed.

## Confounds and cost

Both maps use every H-clean donor once, preserving donor-pool marginals. Their donor-answer relation to the recipient is109“other”/6H/4D; same-entity pairs4, identical item-list pairs10 and same-stratum pairs27 under each map. Nevertheless19individual answer-relation assignments change and116donor truthful answer texts change. Relative to the existing intact validation predictions, donor-capability associations are62capable→capable,24incapable→capable,24capable→incapable and9incapable→incapable. These are descriptive annotations only; **do not filter or rematch using them**. Aggregate matching cannot isolate donor content from donor competence or instruction/template differences. The original SDR H/D task confounds also remain.

The measured33-condition panel took436.74s, with64.13s load and11.33s slower initial condition. Applying its conservative formula to four full SDR119/WT16conditions gives `1.25×(64.1253+4×11.3258)+30 = 166.79s` (~0.0463GPUh). A root-reserved6min single-GPU allocation (0.10GPUh), with the same measured identity/hardware and explicit no-retry stop, would provide headroom; this is an estimate, not a submission or authorization. Slower hardware/source changes require recalibration. Retaining all four WT passes makes this estimate conservative relative to an SDR-only contrast.

Robustness across these two fixed mappings would support robustness of the **interchange effect** to one structured reassignment, not strategic-deception specificity, causal localization independent of donors, or generalization. A large change would establish dependence on this mapping contrast, not identify why. Exact independence for every recipient is impossible under the existing all-view signature constraint because of the two-cluster group; if that is a scientific requirement, defer rather than silently relax alignment or drop those rows.
