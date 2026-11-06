# Independent relocated-wrapper review

Status: handed-back

## What changed

Accepted the distinct wrapper-only correction for one deliberate genuine CPU run. The wrapper uses the exact immutable script path instead of deriving it from a path that Slurm relocates. The prior science review and its appended source correction remain applicable. [Scoped verdict](182-r3-wrapper-review-evidence/verdict.json).

## How verified

Read the exact shell delta, relocation fixture and raw RED/GREEN evidence. Rehashed the manifest and members and checked unchanged scientific/resource files against the previous revision. Verified shell syntax and independently ran only the relocation fixture in both environments. No unchanged native science tests were repeated. [Raw wrapper](182-r3-wrapper-review-evidence/run.sh), [fixture](182-r3-wrapper-review-evidence/test_wrapper_relocation.py), [retained review identity](182-r3-wrapper-review-evidence/verdict.json).

## Execution evidence

No Slurm job or genuine shape calculation was performed. Base observed 1 passing relocation test against 1 expected; mgnp observed 1 against 1 expected, both exit 0. Raw RED records 1 expected path failure against 1 observed. The fixture intercepts the timeout command and records arguments; it never invokes the scientific script or model. No scientific baseline replication is claimed. [Counts and scope](182-r3-wrapper-review-evidence/verdict.json), [raw RED](182-r3-wrapper-review-evidence/red-wrapper.log), [provenance](182-r3-wrapper-review-evidence/run_manifest.json).

## What is NOT done

No new scientific review, genuine geometry result, runtime/memory/storage bound or GPU admission. Failed execution artifacts remain preserved; no automatic retry is authorized.

## Open questions

Root may run the exact packet once in a fresh output directory under the reviewed CPU allocation and required immutable runtime working directory. Actual completion and shape results still require independent review before resource binding.
