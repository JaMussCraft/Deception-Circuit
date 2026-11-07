# Independent A3 pilot CPU preparation

Status: handed-back

## What changed

Canonical preparation and mask preparation are complete as CPU artifacts at [the owned output root](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-independent-pilots-74efb4d04819). Edge preparation is blocked by a reproduced tokenizer-factory mismatch. The overall preparation manifest therefore retains `complete_cpu_preparation=false` and `execution_authorized=false`; it does not claim an edge bundle or edge inventories. [Raw manifest](112-a3-pilot-preparation-evidence/run_manifest.json).

The canonical design consumes the original audited A1 design, selected artifact and adjacent completion manifest, matched Arrow data, historical exclusions, pinned tokenizer and local utility cache. Root supplied the direction metadata settings. The mask source-settings bundle separately retains its authorized BF16/eager/H200 profile, chunk size `4`, original padding policy and false execution authorization. Its source closure includes the actual wrapper interpreter. [Source settings](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-independent-pilots-74efb4d04819/mask-source-settings/payload.json), [canonical settings](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-independent-pilots-74efb4d04819/root-direction-metadata-settings.json), [manifest](112-a3-pilot-preparation-evidence/run_manifest.json).

The mask bundle retains 24 candidates and both objective arms with all frozen seeds, updates, validations, controls, transfers and the archived New30 reference. Its M1 inventory has 31,191 logical keys; its full target has 3,437,966. The complete inventories and declared capacity bounds are planning evidence, with no runtime or hardware-fit claim. [Manifest](112-a3-pilot-preparation-evidence/run_manifest.json).

## How verified

Actual frozen wrappers executed canonical preparation, mask preparation and both mask inventory stages. The final CPU pass called the canonical parent/source/assessment validators, live protection checks, mask source/profile validator and owning inventory validators. It checked exact source imports, artifact completion markers, mask interpreter closure and unchanged ancestry file bytes. All 509 exported source files and all 16 frozen A1 code dependencies matched. [Owning validation](112-a3-pilot-preparation-evidence/owning-validation.log), [manifest](112-a3-pilot-preparation-evidence/run_manifest.json).

The actual mask wrapper dry run returned successfully with `weights_loaded=false`, `writes=false`, `execution_authorized=false` and live allocation admission deferred. This is static, nonauthorizing evidence. No broad or duplicated tiny-model suites were run. [Dry run](112-a3-pilot-preparation-evidence/mask-wrapper-dry-run.log).

The failed edge path calls raw `AutoTokenizer.from_pretrained` inside `admit_parent_sources`, then passes that object to the canonical strict validator. Raw loading has no padding token; the approved `common.load_tokenizer` supplies EOS as padding. Their `special_tokens_map` differs, and the native validator rejects it. A separate local tokenizer-only probe reproduced that exact rejection and isolated the sole compared configuration difference. No validator was bypassed and no frozen source was edited. [Traceback](112-a3-pilot-preparation-evidence/edge-prepare.log), [diagnosis](112-a3-pilot-preparation-evidence/edge-tokenizer-diagnosis.json).

## Execution evidence

Local CPU only; scheduler job and cluster are not applicable. Canonical, mask source-settings publication, mask prepare, both inventory stages, diagnosis, mask dry run and final owning validation exited `0`. Actual edge prepare exited `1`. Exact stage statuses, commands, raw logs and source commit are preserved in the [execution receipt](112-a3-pilot-preparation-evidence/execution-evidence.json), [run manifest](112-a3-pilot-preparation-evidence/run_manifest.json) and [command script](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-independent-pilots-74efb4d04819/prepare-independent.sh).

Structural ancestry baseline: assessment membership reproduces the original 100 versus 100 IDs per task, IOI 100 versus 100 and MMLU 32 versus 32, preserving order, stream/token bytes and utility payloads. Separate validation utilities contain IOI 100 and MMLU 32 from the fixed local candidate procedure. No numerical model baseline was run and no scientific scoring rows were produced. [Execution receipt](112-a3-pilot-preparation-evidence/execution-evidence.json), [manifest](112-a3-pilot-preparation-evidence/run_manifest.json).

The full source commit is `74efb4d0481968a1d0138eb1a79b97f302fd3c3b`; the A1 ancestor remains `5f450dc93dac707af649dee8c8ca60888b2831db`. These are CPU preparation provenance, not model-run provenance. The source export, original artifacts, cached identities and registry evidence are bound in the [manifest](112-a3-pilot-preparation-evidence/run_manifest.json).

## What is NOT done

No edge prepared bundle or edge pilot/fit-target inventory exists because source validation failed before publication. No direction fit/selection/assessment/admission was attempted. No model weights, GPU, scheduler, API, network, notebook, git, RS mutation, reservation or scientific verdict occurred. Canonical direction metadata does not grant direction acceptance. Mask settings and prepared inventories grant no spending or execution authority.

## Open questions

Root must route the edge tokenizer-factory repair to its source owner, independently review the change, freeze the appropriate source and rerun genuine preparation into a new lineage. Preserve this failed candidate and all original bytes. The repair should use the same approved pinned tokenizer configuration as canonical preparation; bypassing the signature validator would discard the demonstrated protection.

Mask is ready for independent source/integration review and root M1 admission. Root still needs actual current registry checks, source-bound admission/reservation/ledger mapping, explicit live allocation resource/work-directory binding and capacity checks against the published inventories. The accepted M1 caps remain unchanged. Future measured pilot receipts must establish time and memory; the source bounds alone cannot establish fit.

[Non-submitting command templates](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-independent-pilots-74efb4d04819/m1-command-templates.sh) provide the actual wrapper commands and require real root ledger/reservation paths. The edge template explicitly refuses while its required prepared artifacts are absent. The mask template keeps the actual flat-cache launcher convention and chunk size unchanged. No template was submitted or executed as a model job.
