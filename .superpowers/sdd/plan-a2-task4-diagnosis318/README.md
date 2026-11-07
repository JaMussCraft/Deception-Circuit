# Task 4 read-only diagnosis 318

Status: handed-back

## What changed

Created only this diagnosis directory and required handback. Active r3, actual job evidence, original runtime S and all seventeen component files are unchanged. Both actual environments now have the same thirty-three cases: thirteen passes, twenty failures and zero errors/skips. The failures separate into one native geometry rejection, thirteen direct cutover-lineage rejections and six transfer tests that correctly expose an earlier rejection by failing their stage-reached assertion. The raw-byte regression passes and must remain.

[diagnosis.json](diagnosis.json) records exact artifacts, byte hashes, source predicates and downstream identity comparisons. [diagnose.py](diagnose.py) imports only the standard library, reads completed evidence and executes isolated original metadata predicates with controlled external inputs. It does not import an application/native module or execute a full test.

The cutover defect is one field: `cutover.ledger_sha256`. In all thirty-eight publish-bound fixtures inspected, it authenticates pre-transition `native/old.json`, while the original normalizer's `original_snapshot_path` refers to the preserved snapshot of the active successor, `native/new.json`. Active mapping references and full lineage references match, and the canonical ledger equals the active snapshot. For BASE entry case zero, the seal is `9cdc2309c2dc6dc296f3f81b14d8d12871ae862e98c54f86b6ab01c7572ff12c`; active snapshot SHA is `020c9727343e32d1287f20a0495414b1a1e5d652d9fb78f34b0a6a4eb2a1799e`. The original guard correctly rejects the mismatched anchor. The misleading property name means original snapshot for the active mapping, not necessarily the origin mapping. Every old snapshot still must remain preserved and byte-bound.

The source order is `capture_cpu` then `collect_native_closure` then `authenticate_cutover(...normalized)` before cache/staging. That explains the thirteen direct failures and the six transfer cases whose expected rejection swallows the earlier cutover exception, leaving events ending at remote inspection. Applying the original predicate to those actual artifacts reproduces rejection; changing only the hypothetical active-snapshot digest in memory makes that predicate pass. No actual attestation, digest, binding or source is changed.

The observed native failure is `stale A2 model_geometry` in both logs. The frozen geometry includes exact config provenance path `/work/nvme/beto/swong2/models--meta-llama--Llama-3.1-8B-Instruct/blobs/0bb6fd75b3ad2fe988565929f329945262c2814e`. Original source resolves this through `hf_hub_download(...local_files_only=True)` and hashes the entire geometry/source object. The observer inherits HF variables rather than establishing the original CPU/GPU wrappers' explicit cache/offline environment. In the observed submission-shell environment, HF_HOME is `/work/nvme/beto/swong2` while HF_HUB_CACHE and HUGGINGFACE_HUB_CACHE are unset; the library default therefore adds `/hub`.

Both exact flat and nested-hub config files exist with raw SHA `29e4c210b0d6ac178b16b2a255a568bdb23b581e50ca1ef6a6d071dd85704e6e`. A metadata-only replay of the original geometry function, replacing only the external resolver with each known path, matches the frozen object exactly for the original flat cache. The nested-hub replay differs only in `model_geometry.source.path`; dimensions and canonical config SHA are identical. Thus changing frozen geometry or weakening equality would be wrong. The actual job's fresh geometry object/HF environment were not recorded, so the nested path is a deterministic source replay under the observed shell environment, not a fabricated runtime observation. The missing deterministic original environment is concrete fixture construction debt; future evidence should capture the actual resolver object/path before the comparison.

## How verified

The bounded standard-library diagnosis exits zero. It reads both actual XML/results, checks all thirty-eight cutover/active-snapshot pairs, replays the exact original cutover predicate, checks current raw WAITING/request/CPU identities and replays the original metadata geometry construction with an explicit resolver boundary. No native normalization or Hugging Face resolver is executed locally.

All thirty-eight inspected GPU WAITING files exactly match their CPU copies and expected request/COMPLETE hashes. Mapping references and lineage reference bytes match. Current grader catalogue projections at both exact source routes match frozen own entry, foreign path/pin declarations and top-level authoritative fields. This checks metadata projection only, not a fresh full native grader/source validation. Original r3 member pins and all seventeen component hashes still match. Existing raw results are read only and their exact hashes are recorded in the diagnosis.

The downstream sweep found one further full-fixture provenance inconsistency: the synthetic child proof retains `support_reason_mask_sha256` equal to sixty-four eights, while accepted original domain proof 249/285 uses `73002c8b74d13947aeb9bf1f6e09d50544b549ea51ab00a50b9510bd6404ffd8`. The full fixture constructs native support data but does not propagate its CPU-format digest into the synthetic proof. Current root guards only check format/counts here, so this is not the observed error or a proven next thrown guard. It should be considered when making the full-case fixture coherent, without mutating any real frozen proof. Small synthetic constructor cases may retain explicit placeholder data within their documented scope.

No further guaranteed downstream identity rejection was established from the bounded sweep. Original complete bank contract, numerical/tokenizer context, all-eighteen comparison recomputation, full support construction, publication, consumer and final native audits remain unexecuted beyond the current blockers. Do not read this diagnosis as downstream GREEN.

## Execution evidence

Root reports actual job 23637408 failed `1:0` after 688 seconds and sealed its evidence. Raw observer evidence records BASE elapsed 327.349 seconds and mgnp 329.995 seconds, with thirty-three cases/thirteen passes/twenty failures/zero errors/skips each. Direct failure groups are identical. Source provenance names original `50e947bb852613e3a270082651f2bd1b7bb0c525` and root-supplied worktree identity `538109e809285b6ddc45d42df8786270a65f7b12` in `../plan-a2-task4-deployment315/run-01/run_manifest.json`.

No new job, application/native import, pytest/full test, model/CLI, fixture edit or production edit occurred. Standard-library diagnosis exits zero. Original byte regression passes in the actual job; no scientific full rows/control result is produced. Full-domain construction and final audits remain unobserved. This task adds no new timing/resource claim.

## What is NOT done

No corrected packet, source repair, new bindings/attestation, re-signing, native success or Task4 acceptance. R3 and failed results remain preserved. Root owns the consolidated next correction decision, scheduler/accounting, remote operations, acceptance and report lint. Independent A3 work is untouched. Neither old proof nor a hypothetical in-memory predicate result grants operational permission.

## Open questions

Minimal consolidated proposal for root authorization before edits:

1. At new fixture construction, use the returned normalized active mapping's `original_snapshot_path` digest when sealing the completed transition. Immediately call the unchanged `authenticate_cutover` with that same normalized object, so the wrong anchor fails during setup. Preserve every old snapshot/reference and retain a negative old-anchor case.
2. Establish the exact original HF_HUB_CACHE/TRANSFORMERS_CACHE paths and offline variables before fresh Python imports, retaining original S cwd and frozen receipt bytes. Capture/compare the actual metadata geometry object/path; do not patch its resolver/equality or rewrite model geometry.
3. Preserve all thirty-three cases/assertions, especially the raw-byte regression and transfer stage assertions. Exercise every cheap identity predicate against the temporary fixture before running the expensive full path.
4. For the full-case synthetic child, consider propagating the actual already reconstructed CPU-format support digest before its prospective proof is sealed. This adds no new reconstruction and must never modify real proof 249/285.
5. Root consolidates one reviewed correction round. Any additional actual component failure still requires narrow diagnosis and affected-component review, not a bypass.

This diagnosis makes no fixture/source edits and waits for root's consolidated authorization.
