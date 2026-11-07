# Hand-back 248: Exact base fixture runtime inventory

Agent: Terra inventory worker. Status: handed-back.

## What changed

- This hand-back is the only repository write; no bundle was built or installed.
- The base executable is a regular 16,269,152-byte ELF at `/sw/external/python/anaconda3/bin/python3.9`, Python 3.9.18; it links system pthread, dl, util, m, libc and the ELF loader, with no shared libpython in `ldd` output.
- Excluding site-packages, caches and test directories, `/sw/external/python/anaconda3/lib/python3.9` contains 916 files totaling 30,595,815 logical bytes. Its 74 extension modules resolve locally to system libraries and 14 distinct Anaconda library targets totaling 12,586,160 bytes; no `ldd` line reported `not found`. This is an inclusive standard-library estimate, not a minimal traced closure.
- Pytest 8.3.3 resides in `/u/swong2/.local/lib/python3.9/site-packages`. Installed distributions and recorded files excluding bytecode are pytest 8.3.3 (82 files, 1,197,642 bytes), iniconfig 2.1.0 (11, 13,817), packaging 25.0 (25, 239,353), pluggy 1.6.0 (15, 66,294), exceptiongroup 1.3.1 (12, 52,593), tomli 2.3.0 (11, 42,251), and typing_extensions 4.14.0 (6, 174,739). Preserve their package roots, pytest's `_pytest` and `py.py`, and dist-info at their literal origin. Exceptiongroup declares typing-extensions on Python 3.9.
- The 14 Anaconda targets are crypto, ffi, lzma, ncursesw, panelw, readline, sqlite3, ssl, tcl, tk, uuid, z, xcb and tinfow; preserve the actual targets and symlink names. System libraries and loader are separate host dependencies.

## How verified

Read the runner and used the exact base Python's `sysconfig`, `importlib.metadata`, filesystem traversal and `ldd` for the executable and each `lib-dynload/*.so`. Runner imports are standard library; it launches pytest with plugin autoload disabled and `--noconftest`. It explicitly invokes three candidate tests in green mode and one in red mode. Metadata sizes are approximate logical bytes and exclude bytecode; the Python executable, stdlib, listed Anaconda targets, and pytest distributions total about 60.9 MB before symlinks and other assets.

The candidate tests were not read: the runner's currently named candidate directory was unavailable to this inspection. This observation is not a path-defect diagnosis and does not supersede the prior successful path evaluation or job restoration.

## Execution evidence

Not applicable: no runs.

## What is NOT done

No fixture tests, package copy, install, jobs, native pipeline or Bridges access. Local `ldd` resolution alone does not prove compatibility with Bridges: its loader, glibc symbol versions, kernel, CPU features, system libraries, transitive ELF dependencies, locale/configuration and dynamic loads remain untested. The standard-library estimate excludes test directories, so fixture imports and runtime tracing must establish whether they are required. Package metadata may not capture files loaded outside distributions or startup `.pth` behavior. Exact origin preservation requires a reviewed mechanism to reproduce both absolute prefixes and actual `sys.path` without contaminating the host environment. Package and executable content hashes, symlink targets, recursive ELF closure and origin assertions remain to be captured. The 14 targets may have their own transitive dependencies and non-ELF resources, and the executable's reported size is separate from its system dependencies.

## Open questions

- Can an isolated Bridges environment provide the exact absolute prefixes and a compatible system loader/glibc? Default: treat feasibility as conditional until a staged, source-bound read-only compatibility check and fixture test establish it.
- Which files do the actual candidate tests and dynamically loaded helper modules import? Default: inspect the live pinned candidate and trace fixture imports before trimming any inclusive closure.
