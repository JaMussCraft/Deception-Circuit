"""
component_analysis/batch.py — `analyze_components.py batch FILE`: many invocations, one job, one model.

A phase-1 job runs several cells back to back (seven sweeps and a lens per task, spec §4). Each
`analyze_components.py` invocation loads the 8B model, about 10.5 minutes cold on Bridges-2, so a job
of separate invocations pays that per cell. `batch` reads one invocation per line (the same flags as
the CLI, shell-quoted; `#` comments and blank lines skipped), loads the model once on the first line
that needs one, and hands it to every later line. Every line is timed, and `--timings FILE` writes the
record (argv, status, seconds) that becomes the cost basis.

A line that fails is recorded and the rest still run; the exit code is 1 if any line failed. A dry-run
line runs as a dry run. Every line must name the same model, because one model is loaded.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
import time
import traceback
from typing import List


def read_batch(path: str) -> List[List[str]]:
    """The invocations of a batch file, one argv per non-empty line."""
    out = []
    with open(path) as handle:
        for number, line in enumerate(handle, start=1):
            argv = shlex.split(line, comments=True)
            if not argv:
                continue
            if argv[0] in ("batch", "roles"):
                raise ValueError(f"{path} line {number}: a batch line is one analysis "
                                 f"invocation, not the {argv[0]!r} subcommand")
            out.append(argv)
    return out


def main(argv=None) -> int:
    import analyze_components as cli_module

    parser = argparse.ArgumentParser(prog="analyze_components.py batch",
                                     description=__doc__.split("\n\n")[0])
    parser.add_argument("file", help="One invocation per line.")
    parser.add_argument("--timings", default=None, metavar="FILE",
                        help="Write {invocations: [{argv, status, seconds}]} here.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Dry-run every line: the login-node check of a GPU job file.")
    options = parser.parse_args(argv)

    lines = read_batch(options.file)
    if options.timings:
        # A job writes its timings into a suite directory no line has made yet.
        os.makedirs(os.path.dirname(os.path.abspath(options.timings)), exist_ok=True)
    if options.dry_run:
        lines = [line if "--dry-run" in line else line + ["--dry-run"] for line in lines]
    record = {"batch": os.path.abspath(options.file), "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "invocations": []}
    model, model_name = None, None
    failed = 0
    for index, line in enumerate(lines, start=1):
        print(f"\n=== batch {index}/{len(lines)}: analyze_components.py {shlex.join(line)}",
              flush=True)
        started = time.perf_counter()
        entry = {"argv": line}
        try:
            cli = cli_module.build_parser().parse_args(line)
            resolved = cli_module.intake.resolve_intake(cli)
            if cli.dry_run:
                code = cli_module.dry_run(cli, resolved)
            else:
                if model is None:
                    loading = time.perf_counter()
                    model, model_name = cli_module.load_model(cli, resolved), resolved.model
                    entry["model_load_seconds"] = time.perf_counter() - loading
                elif resolved.model != model_name:
                    raise ValueError(f"line {index} names model {resolved.model!r}, but this "
                                     f"batch loaded {model_name!r}")
                code = cli_module.run(cli, resolved, model=model)
            entry["status"] = "ok" if code == 0 else f"exit {code}"
        except SystemExit as exc:
            entry["status"] = f"error: SystemExit {exc}"
        except Exception as exc:                                      # noqa: BLE001
            entry["status"] = f"error: {type(exc).__name__}: {exc}"
            traceback.print_exc()
        entry["seconds"] = time.perf_counter() - started
        failed += entry["status"] != "ok"
        record["invocations"].append(entry)
        print(f"=== batch {index}/{len(lines)}: {entry['status']} in {entry['seconds']:.1f} s",
              flush=True)
        if options.timings:
            with open(options.timings, "w") as handle:
                json.dump(record, handle, indent=2)
    print(f"\nbatch: {len(lines) - failed} of {len(lines)} invocation(s) ok")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
