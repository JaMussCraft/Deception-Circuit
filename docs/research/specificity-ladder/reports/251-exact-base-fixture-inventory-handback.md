# Hand-back 251: Exact base fixture inventory

Agent: Terra inventory worker. Status: handed-back.

## What changed

- Inventory data: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-base-inventory251/manifest.json`. It records 1,103 absolute file or symlink entries, SHA-256 hashes of regular files, byte sizes, symlink targets and roles; 89 ELF inspections include resolved dependencies, needed names, runpaths and version labels. It is an inclusive inventory, not a transport package.
- The exact executable is Python 3.9.18 with ABI `cpython-39-x86_64-linux-gnu`. Selected pytest 8.3.3, iniconfig, packaging, pluggy, exceptiongroup, tomli and typing_extensions all import from the literal user-site origin. `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` and the exact interpreter reported `pytest 8.3.3` for `-m pytest --version`.
- With ordinary startup, user site is enabled; sys.path also contains the Anaconda site and an mxeval path. Startup has the `_distutils_hack` meta finder and namespace modules `mpl_toolkits`, `google`, `ruamel`, `sphinxcontrib` and `zope`; sitecustomize and usercustomize were absent. The manifest records observed .pth filenames, hashes and executable-line counts, not their contents. Their effects are a separate exact-startup equivalence question.
- The three runner-selected test files, read using the actual runner globals, declare standard-library and pytest imports plus imports between the test files. The packet directory uses `plan-plan-a2-full-score-operational186`; the runner's candidate uses `plan-a2-full-score-operational186`. My earlier shell lookup incorrectly substituted the double-prefix packet namespace for the candidate. There was no demonstrated path defect.

## How verified

The exact interpreter's stdlib introspection and distribution metadata supplied paths, versions and SHA-256s. `ldd` and `readelf` inspected the interpreter, 74 stdlib extensions and recursively resolved Anaconda dependencies. Local `ldd` reported no missing libraries. Anaconda dependencies were inventoried as artifacts; system loader and libraries were only named, and must not be blindly copied or overridden. The host system dependencies include glibc/loader and also X11, Xau, crypt and nsl. Version labels include GLIBC through 2.17 and OpenSSL 3.0 labels; these are conservative labels from whole `readelf --version-info` output, not a proven minimum host ABI.

## Execution evidence

Not applicable: no runs.

## What is NOT done

No tests, collection, native pipeline, remote operation, bundle creation, package installation or environment port. The manifest excludes standard-library test directories, caches and unrelated site-packages; startup .pth dependencies, dynamic loads, assets, symbol version requirements versus definitions, CPU/kernel compatibility and exact host loader/system-library compatibility remain unproven. Local ldd and a version command do not establish Bridges portability or fixture correctness. Fixture dynamically loaded helper imports and scientific inputs need independent closure checks before staging; observed startup hooks must be reconciled with the intended isolation without silently changing required behavior. Symlink targets and needed shared objects must be checked again against the staged artifact.

## Open questions

- Can the intended isolated environment reproduce the literal origins while providing compatible system libraries and required startup behavior? Default: condition any use on source-bound manifest validation and a separate Bridges staging gate.
- Are any excluded stdlib tests, startup assets, or dynamically loaded helper resources actually needed by the fixture? Default: trace bounded imports under the intended isolated setup before reducing or approving the bundle.
