# A3 baseline closure successor source review

Status: handed-back

## What changed

Accepted the scoped r5 successor source/closure correction for execution, with no remaining static finding in this correction. This is not RED/GREEN or runtime/scientific acceptance.

Baseline now contains two pinned ordinary registry files, held_out.json and directions.json, without aliases. Candidate/oracle add content hashes for their existing registry aliases. The stdlib closure preflight runs from check_pins, before native fixture execution, and from observer dry-run. It requires actual baseline-relative ordinary context files, pinned bytes, protected-registry schema and frozen grader entry; path-referenced protected dependencies must remain inside the root, ordinary, present, pinned and hash/count consistent. Native original registry/authority guards remain authoritative and unchanged.

## How verified

Independently ran all five small stdlib closure regressions: exit 0, five passes in 0.011 seconds. Independently invoked the actual r5 observer --dry-run: exit 0; both baseline context files checked, expected GREEN count 223, zero native imports. Missing-registry, omitted/unpinned/changed transitive dependency, escaped path and alias cases are covered by the pure regressions. Both actual registries currently have zero protected sets, so no transitive protected-ID file is omitted.

All prior baseline/candidate/oracle code pin values are preserved. Baseline runtime remains the exact r3 runtime; baseline RED wrapper, baseline/suite conftests and test files, test groups and verification scope are byte-identical to r4. Thus the five original attributable baseline assertions and all 223 GREEN cases retain their bodies/counts and original time bounds. No validator, REPO, guard or test semantics were weakened.

Source-pins SHA is `05b53e5f2b2c2d737782753cde63cb6c1b428038d71d7666c644777deb1184c9`; observer SHA is `4d4aee62a1b544db8a84dd53f1cb3a1e9544ab57deaeec2d89e31c8e05f816be`. Baseline held_out.json is 32 bytes with SHA `801b24e37c3315a8e58aa2ad5007f7831822fc2636d1e61837ad3652c370425e`; directions.json is 21,212 bytes with SHA `f8c7dbb92f2edc509c7bb8e94624a5c8adabddd103a8c48db1cc59bd69a3c6b0`. These match both candidate/oracle alias contents exactly at review time.

Checked every proposed ordinary inventory file’s current local hash/length and all eight literal aliases: 1116 ordinary files, eight aliases, zero baseline aliases. Evidence: `.superpowers/sdd/plan-a3/baseline-closure-review243/source-audit.json`.

## Execution evidence

Reviewer ran only the tiny stdlib regressions and actual stdlib dry-run/file metadata checks. Five tests pass; expected count 223 and both baseline context files pass the observer preflight. No native/full pytest, model, CPU allocation or remote execution was performed. The failed Bridges r4 attempt remains preserved; its three wrong-cause failures are not relabeled as attributable RED.

## What is NOT done

No staged successor/config binding or release audit, actual five intended DID NOT RAISE baseline results, 223 GREEN results in either interpreter, source/runtime publication, genuine receiver/resource or numerical/GPU admission. No code edits, jobs, SSH, git, RS or extra agents.

## Open questions

No source correction is requested. Root can stage/bind this exact successor and obtain fresh deployment review before the two environment jobs.

Deployment must verify or update the actual target bytes behind the candidate/oracle registry aliases to match their new content pins. Those alias targets are not themselves ordinary rows in the 1116-file proposal; preserving their literal paths alone does not prove their contents. Keep actual primary registry context separately present/checked as required by unchanged native guards. The new observer content pins fail closed if these targets are stale. This is a final staging/binding check, not permission to patch validators or edit the frozen packet.

Actual baseline 5 and 223 GREEN semantics remain mandatory. Root owns execution and report lint.
