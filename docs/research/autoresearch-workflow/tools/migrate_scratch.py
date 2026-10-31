#!/usr/bin/env python3
"""Archive closed ``.scratch`` directories byte for byte and copy their Markdown (spec 3, 7; R3, R15, R28, R34).

The script never moves anything itself. ``plan`` hashes every file of each named ``.scratch/<slug>`` directory,
writes the ``mkdir``, ``move`` and ``symlink`` ops the apply tool (``apply_staged.py``) later runs, copies the curated
Markdown subset into ``docs/research/<direction>/scratch-copy/<slug>/`` with a ``provenance.json``, records every
hash for ``verify``, and fills the ``archive`` field of ``directions.json``. ``verify`` re-hashes every recorded path,
before the apply (sources) or after it (archive, symlink and copies).

    migrate_scratch.py plan --include component-analysis,format-control [--report-only]
    migrate_scratch.py plan --confirmed-live-session-finished --include sdr-cue-probe,...    (wave D, R28)
    migrate_scratch.py verify --wave B

Guards:

- A directory R28 protects (``sdr-*``, ``selective-deception``, ``eval5-grader-fixes``) is refused unless
  ``--confirmed-live-session-finished`` is passed; its ops are then wave D in ``ops/10-migration-d.json``.
- A directory with any entry modified in the last 12 hours is skipped, except ``autoresearch-workflow`` (R34).
- A directory whose archive destination exists, or that sits on another filesystem than the archive root, is refused.
- ``autoresearch-workflow`` holds stale copies of files whose canonical copy is in the feature directory F. A file
  with a sha256 twin in F is copied to the backup root by a ``write`` op (``/u`` is another filesystem, so a rename
  cannot reach it), the directory is renamed into an ignored stash under ``outputs/_studies`` so the path is free, and
  a symlink to ``DC/docs/research/autoresearch-workflow`` replaces it. A file with no twin is listed and kept: the
  directory ops are then withheld.

Only names, sizes and hashes are printed. File contents are read only to hash them, to copy them and to run the RS
secret scan; a secret match is reported by path and pattern name, never by its text. Stdlib only; Python 3.9+.
"""

import argparse
import datetime
import hashlib
import importlib
import json
import os
import re
import shutil
import stat
import sys
import time

ALIGNMENT = "/projects/beto/swong2/Alignment"
DC_MAIN = ALIGNMENT + "/Deception-Circuit"
STAGING = "/u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging"
RS_PARENT = ALIGNMENT + "/.agents"
BACKUP_ROOT = "/u/swong2/.claude/research-session/backups"
AR_SLUG = "autoresearch-workflow"
AR_BACKUP_NAME = "scratch-autoresearch-workflow-20261031"
AR_STASH_NAME = "scratch-stale-20261031"
TICKET = "10"

HERE = os.path.dirname(os.path.abspath(__file__))
FEATURE_DIR = os.path.dirname(HERE)            # .../docs/research/autoresearch-workflow
DOCS_ROOT = os.path.dirname(FEATURE_DIR)        # .../docs/research

FILE_CAP = 200 * 1024                           # R34: at most 200 KB per copied file
DIR_CAP = 1536 * 1024                           # R34: at most 1.5 MB of copies per scratch directory
FRESH_SECONDS = 12 * 3600                       # R3: skip a directory touched in the last 12 hours

# R28 and the deferred list of ticket 10. The regex matches the apply tool's PROTECTED_SCRATCH_RE.
PROTECTED_RE = re.compile(r"^(sdr-[^/]*|selective-deception|eval5-grader-fixes)$")
DEFERRED = ("sdr-assay-diagnosis", "sdr-behavior-identification", "sdr-clause-choice", "sdr-cue-circuits",
            "sdr-cue-followup", "sdr-cue-probe", "sdr-native-controls", "sdr-routing-pilot", "sdr-routing-validation",
            "sdr-shared-composition", "sdr-session-wrapup", "selective-deception", "eval5-grader-fixes")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

PLANNED, SKIPPED, REFUSED, BLOCKED = "planned", "skipped", "refused", "blocked"


class MigrationError(Exception):
    """A refusal for the whole run (exit 2)."""


# -------------------------------------------------------------------------------------------------------------
# helpers


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dump_json(path, data):
    """The RS JSON style (``state.dumps``: indent 2, sorted keys, ASCII, trailing newline), written atomically."""
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    tmp = path + ".tmp-%d" % os.getpid()
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(data, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return ("%d %s" % (n, unit)) if unit == "B" else ("%.1f %s" % (n, unit))
        n /= 1024.0
    return str(n)


def load_secret_scanner(rs_parent):
    """``scan_secrets`` from the RS lint module under ``rs_parent/research_session``. Fails closed."""
    lint_path = os.path.join(rs_parent, "research_session", "lint.py")
    if not os.path.isfile(lint_path):
        raise MigrationError("secret scan unavailable: %s does not exist" % lint_path)
    if rs_parent not in sys.path:
        sys.path.insert(0, rs_parent)
    for name in list(sys.modules):
        if name == "research_session" or name.startswith("research_session."):
            mod = sys.modules[name]
            if os.path.dirname(os.path.dirname(os.path.abspath(getattr(mod, "__file__", "") or ""))) != rs_parent:
                del sys.modules[name]
    lint = importlib.import_module("research_session.lint")
    return lint.scan_secrets


def inventory(root):
    """Every entry under ``root`` (not following symlinks), with sha256 for regular files.

    Returns ``(files, dirs, newest_mtime)``. ``files`` maps a relative path to a dict with ``type`` (``file`` or
    ``symlink``), ``bytes`` and ``sha256`` or ``target``. ``newest_mtime`` covers ``root``, directories and files.
    """
    files, dirs = {}, []
    newest = os.lstat(root).st_mtime
    for cur, dnames, fnames in os.walk(root):
        dnames.sort()
        keep = []
        for d in dnames:
            p = os.path.join(cur, d)
            st = os.lstat(p)
            newest = max(newest, st.st_mtime)
            rel = os.path.relpath(p, root)
            if stat.S_ISLNK(st.st_mode):
                files[rel] = {"type": "symlink", "bytes": 0, "target": os.readlink(p)}
            else:
                dirs.append(rel)
                keep.append(d)
        dnames[:] = keep
        for n in sorted(fnames):
            p = os.path.join(cur, n)
            st = os.lstat(p)
            newest = max(newest, st.st_mtime)
            rel = os.path.relpath(p, root)
            if stat.S_ISLNK(st.st_mode):
                files[rel] = {"type": "symlink", "bytes": 0, "target": os.readlink(p)}
            elif stat.S_ISREG(st.st_mode):
                files[rel] = {"type": "file", "bytes": st.st_size, "sha256": sha256_file(p)}
            else:
                files[rel] = {"type": "other", "bytes": 0}
    return files, dirs, newest


def md_order(rel):
    return (rel.count(os.sep), rel)


# -------------------------------------------------------------------------------------------------------------
# context


class Context(object):
    def __init__(self, args):
        self.alignment = os.path.abspath(args.alignment)
        self.scratch = os.path.join(self.alignment, ".scratch")
        self.dc = os.path.abspath(args.dc)
        self.studies = os.path.join(self.dc, "outputs", "_studies")
        self.docs_root = os.path.abspath(args.docs_root)
        self.dc_docs = os.path.join(self.dc, "docs", "research")
        self.feature_dir = os.path.abspath(args.feature_dir)
        self.staging = os.path.abspath(args.staging)
        self.backup_root = os.path.abspath(args.backup_root)
        self.rs_parent = os.path.abspath(args.rs_parent)
        self.now = float(args.now) if args.now is not None else time.time()
        self.date = args.date or datetime.date.fromtimestamp(self.now).isoformat()

    def records_path(self, wave):
        return os.path.join(self.staging, "records", "%s-migration-%s.json" % (TICKET, wave.lower()))

    def ops_path(self, wave):
        return os.path.join(self.staging, "ops", "%s-migration-%s.json" % (TICKET, wave.lower()))

    def ar_backup_dir(self):
        return os.path.join(self.backup_root, AR_BACKUP_NAME)

    def staged_src(self, dest):
        return "tree/" + dest.lstrip("/")


def load_directions(ctx):
    path = os.path.join(ctx.docs_root, "directions.json")
    with open(path, encoding="utf-8") as fh:
        return path, json.load(fh)


def direction_for(data, slug):
    key = ".scratch/" + slug
    for row in data.get("directions", []):
        if key in (row.get("legacy_scratch") or []):
            return row
    return None


# -------------------------------------------------------------------------------------------------------------
# plan


def plan_slug(ctx, slug, confirmed, directions, scan):
    """Everything known about one directory; nothing is written here."""
    res = {"slug": slug, "status": PLANNED, "reason": "", "wave": "B", "ops": [], "writes": [], "copies": [],
           "excluded": [], "secret_blocked": [], "archive_only": {"files": 0, "bytes": 0}, "files": {},
           "dirs": [], "kind": "archive"}
    if not SLUG_RE.match(slug):
        res.update(status=REFUSED, reason="not a lower-case slug")
        return res
    if PROTECTED_RE.match(slug):
        if not confirmed:
            res.update(status=REFUSED, reason="R28 live-session directory; pass --confirmed-live-session-finished "
                                              "only after the user confirms the Codex session is finished")
            return res
        res["wave"] = "D"
    src = os.path.join(ctx.scratch, slug)
    res["source"] = src
    if not os.path.lexists(src):
        res.update(status=REFUSED, reason="source does not exist")
        return res
    row = direction_for(directions, slug)
    if row is None:
        res.update(status=REFUSED, reason="no directions.json row lists .scratch/%s in legacy_scratch" % slug)
        return res
    res["direction"] = row["id"]

    # Already archived (selective-deception precedent): only the Markdown copy is made.
    if os.path.islink(src):
        target = os.readlink(src)
        real = os.path.realpath(src)
        studies_real = os.path.realpath(ctx.studies)
        if not real.startswith(studies_real + os.sep) or not os.path.isdir(real):
            res.update(status=REFUSED, reason="source is a symlink that does not point into outputs/_studies")
            return res
        archive = os.path.join(ctx.studies, os.path.relpath(real, studies_real))
        res.update(kind="already-archived", archive=archive, link_target=target)
        root = archive
    elif not os.path.isdir(src):
        res.update(status=REFUSED, reason="source is not a directory")
        return res
    else:
        root = src
        if slug == AR_SLUG:
            res.update(kind="autoresearch", archive=os.path.join(ctx.studies, AR_SLUG, AR_STASH_NAME),
                       link_target=os.path.join(ctx.dc_docs, AR_SLUG), backup_dir=ctx.ar_backup_dir())
        else:
            res.update(archive=os.path.join(ctx.studies, slug, "scratch"),
                       link_target=os.path.join(ctx.studies, slug, "scratch"))

    files, dirs, newest = inventory(root)
    res.update(files=files, dirs=dirs, newest_age_hours=round((ctx.now - newest) / 3600.0, 2),
               source_inode=os.stat(root).st_ino)
    res["total_bytes"] = sum(f["bytes"] for f in files.values())
    res["md_files"] = sum(1 for r, f in files.items() if f["type"] == "file" and r.endswith(".md"))

    if slug != AR_SLUG and ctx.now - newest < FRESH_SECONDS:
        res.update(status=SKIPPED, reason="an entry was modified %.1f hours ago (12-hour rule, R3)"
                   % ((ctx.now - newest) / 3600.0))
        return res
    if res["kind"] != "already-archived":
        if os.path.lexists(res["archive"]):
            res.update(status=REFUSED, reason="archive destination already exists")
            return res
        anchor = ctx.studies if os.path.isdir(ctx.studies) else ctx.dc
        if os.stat(anchor).st_dev != os.stat(root).st_dev:
            res.update(status=REFUSED, reason="archive root is on another filesystem; a rename is impossible")
            return res
        bad = [r for r, f in files.items() if f["type"] == "other"]
        if bad:
            res.update(status=REFUSED, reason="%d entries are neither files, directories nor symlinks" % len(bad))
            return res

    if res["kind"] == "autoresearch":
        plan_autoresearch(ctx, res)
    else:
        plan_copies(ctx, res, root, scan)
        if res["kind"] == "archive":
            wave = res["wave"]
            parent = os.path.dirname(res["archive"])
            res["ops"] = [
                {"op": "mkdir", "path": parent, "wave": wave},
                {"op": "move", "src": src, "dest": res["archive"], "wave": wave},
                {"op": "symlink", "path": src, "target": res["link_target"], "wave": wave},
            ]
    return res


def plan_autoresearch(ctx, res):
    """R34: back up the files that have a twin in F, stash the directory, link the path to DC's feature dir."""
    twins = {}
    for cur, dnames, fnames in os.walk(ctx.feature_dir):
        dnames[:] = [d for d in dnames if d != "__pycache__"]
        for n in fnames:
            p = os.path.join(cur, n)
            if os.path.isfile(p) and not os.path.islink(p):
                twins.setdefault(sha256_file(p), os.path.relpath(p, ctx.feature_dir))
    matched, unmatched = [], []
    for rel in sorted(res["files"]):
        f = res["files"][rel]
        if f["type"] == "file" and f["sha256"] in twins:
            matched.append((rel, twins[f["sha256"]]))
        else:
            unmatched.append(rel)
    res["matched"] = [{"path": r, "twin": t} for r, t in matched]
    res["unmatched"] = unmatched
    wave = res["wave"]
    for rel, _twin in matched:
        dest = os.path.join(res["backup_dir"], rel)
        if os.path.lexists(dest) and (not os.path.isfile(dest) or sha256_file(dest) != res["files"][rel]["sha256"]):
            res.update(status=REFUSED, reason="backup destination %s exists with other content" % rel)
            return
        res["writes"].append({"rel": rel, "dest": dest, "src": ctx.staged_src(dest)})
        # No expect_sha256: in the apply tool it names the destination's current content, and here there is none.
        res["ops"].append({"op": "write", "dest": dest, "src": ctx.staged_src(dest), "wave": wave})
    if unmatched:
        res.update(status=BLOCKED, reason="%d file(s) have no sha256 twin in F and are kept; the directory is "
                                          "not replaced" % len(unmatched))
        res["ops"] = []
        res["writes"] = []
        return
    res["ops"].extend([
        {"op": "mkdir", "path": os.path.dirname(res["archive"]), "wave": wave},
        {"op": "move", "src": res["source"], "dest": res["archive"], "wave": wave},
        {"op": "symlink", "path": res["source"], "target": res["link_target"], "wave": wave},
    ])


def in_dot_directory(rel):
    """True when any directory on ``rel`` starts with a dot, such as ``.pytest_cache/`` (ticket 12)."""
    return any(part.startswith(".") for part in rel.split(os.sep)[:-1])


def plan_copies(ctx, res, root, scan):
    """R34: every ``*.md`` at any depth, under the per-file and per-directory caps, behind the secret scan.

    Markdown inside a dot-directory (tool caches such as ``.pytest_cache/``) is never copied; it stays archive-only.
    """
    archive_rel = os.path.relpath(res["archive"], ctx.dc)
    used = 0
    copied = set()
    for rel in sorted((r for r, f in res["files"].items()
                       if f["type"] == "file" and r.endswith(".md") and not in_dot_directory(r)),
                      key=md_order):
        f = res["files"][rel]
        if f["bytes"] > FILE_CAP:
            res["excluded"].append({"path": rel, "bytes": f["bytes"], "reason": "file-cap"})
            continue
        if used + f["bytes"] > DIR_CAP:
            res["excluded"].append({"path": rel, "bytes": f["bytes"], "reason": "dir-cap"})
            continue
        with open(os.path.join(root, rel), "rb") as fh:
            data = fh.read()
        if hashlib.sha256(data).hexdigest() != f["sha256"]:
            raise MigrationError("%s/%s changed while planning" % (res["slug"], rel))
        hits = scan(data.decode("utf-8", errors="replace"))
        if hits:
            kinds = sorted(set(h.excerpt.split(" ")[0] for h in hits))
            res["secret_blocked"].append({"path": rel, "bytes": f["bytes"], "lines": sorted(set(h.line for h in hits)),
                                          "patterns": kinds})
            continue
        used += f["bytes"]
        copied.add(rel)
        res["copies"].append({"path": rel, "bytes": f["bytes"], "sha256": f["sha256"],
                              "archive_path": archive_rel + "/" + rel.replace(os.sep, "/")})
    for rel, f in res["files"].items():
        if rel not in copied:
            res["archive_only"]["files"] += 1
            res["archive_only"]["bytes"] += f["bytes"]
    res["copy_dir"] = os.path.join(ctx.docs_root, res["direction"], "scratch-copy", res["slug"])


def write_copies(ctx, res):
    """Write the curated copies and ``provenance.json``. Copies are byte-identical and re-hashed after writing."""
    root = res["archive"] if res["kind"] == "already-archived" else res["source"]
    out = res["copy_dir"]
    for c in res["copies"]:
        dest = os.path.join(out, c["path"])
        if not os.path.isdir(os.path.dirname(dest)):
            os.makedirs(os.path.dirname(dest))
        tmp = dest + ".tmp-%d" % os.getpid()
        shutil.copyfile(os.path.join(root, c["path"]), tmp)
        if sha256_file(tmp) != c["sha256"]:
            os.unlink(tmp)
            raise MigrationError("copy of %s/%s does not match its hash" % (res["slug"], c["path"]))
        os.replace(tmp, dest)
    wanted = set(c["path"] for c in res["copies"]) | {"provenance.json"}
    stale = []
    for cur, _d, fnames in os.walk(out):
        for n in fnames:
            rel = os.path.relpath(os.path.join(cur, n), out)
            if rel not in wanted:
                stale.append(rel)
    res["stale_copies"] = sorted(stale)
    prov = {
        "schema": 1,
        "generated": ctx.date,
        "generator": "docs/research/autoresearch-workflow/tools/migrate_scratch.py",
        "direction": res["direction"],
        "scratch_slug": res["slug"],
        "legacy_scratch": ".scratch/" + res["slug"],
        "archive": os.path.relpath(res["archive"], ctx.dc).replace(os.sep, "/"),
        "archive_abs": res["archive"],
        "caps": {"file_bytes": FILE_CAP, "dir_bytes": DIR_CAP},
        "copies": [{"path": c["path"].replace(os.sep, "/"), "archive_path": c["archive_path"],
                    "sha256": c["sha256"], "bytes": c["bytes"]} for c in res["copies"]],
        "excluded_by_caps": [{"path": e["path"].replace(os.sep, "/"), "bytes": e["bytes"], "reason": e["reason"]}
                             for e in res["excluded"]],
        "blocked_by_secret_scan": [{"path": s["path"].replace(os.sep, "/"), "bytes": s["bytes"],
                                    "patterns": s["patterns"]} for s in res["secret_blocked"]],
        "archive_only": res["archive_only"],
        "source_files": len(res["files"]),
        "source_bytes": res["total_bytes"],
    }
    dump_json(os.path.join(out, "provenance.json"), prov)


def stage_writes(ctx, res):
    """Copy the autoresearch-workflow files that have a twin in F into S/tree for the wave's ``write`` ops."""
    for w in res["writes"]:
        staged = os.path.join(ctx.staging, w["src"])
        if not os.path.isdir(os.path.dirname(staged)):
            os.makedirs(os.path.dirname(staged))
        shutil.copyfile(os.path.join(res["source"], w["rel"]), staged)
        if sha256_file(staged) != res["files"][w["rel"]]["sha256"]:
            raise MigrationError("staged copy of %s does not match its hash" % w["rel"])


def update_registry(ctx, results):
    """Add each new archive path to its direction's ``archive`` list; keep everything else byte-stable."""
    path, data = load_directions(ctx)
    changed = []
    for res in results:
        if res["status"] != PLANNED or res["kind"] == "already-archived":
            continue
        row = direction_for(data, res["slug"])
        rel = os.path.relpath(res["archive"], ctx.dc).replace(os.sep, "/")
        archive = row.setdefault("archive", [])
        if rel not in archive:
            archive.append(rel)
            row["updated"] = ctx.date
            changed.append((row["id"], rel))
    if changed:
        data["updated"] = ctx.date
        dump_json(path, data)
    return path, changed


def record_entry(res):
    keep = ("slug", "status", "reason", "wave", "kind", "direction", "source", "archive", "link_target",
            "backup_dir", "files", "dirs", "source_inode", "total_bytes", "copy_dir", "copies", "writes", "matched",
            "unmatched")
    return dict((k, res[k]) for k in keep if k in res)


def cmd_plan(args):
    ctx = Context(args)
    slugs = []
    for item in args.include:
        slugs.extend(s.strip() for s in item.split(",") if s.strip())
    if not slugs:
        raise MigrationError("--include names no directory")
    scan = load_secret_scanner(ctx.rs_parent)
    _path, directions = load_directions(ctx)
    results = [plan_slug(ctx, s, args.confirmed_live_session_finished, directions, scan) for s in slugs]

    if not args.report_only:
        by_wave = {}
        for res in results:
            if res["status"] == PLANNED:
                if res["kind"] in ("archive", "already-archived"):
                    write_copies(ctx, res)
                if res["kind"] == "autoresearch":
                    stage_writes(ctx, res)
                by_wave.setdefault(res["wave"], []).append(res)
        for wave, group in sorted(by_wave.items()):
            ops = [op for res in group for op in res["ops"]]
            if ops:
                dump_json(ctx.ops_path(wave), {"ticket": TICKET, "ops": ops})
            dump_json(ctx.records_path(wave), {"schema": 1, "generated": ctx.date, "wave": wave,
                                               "planned_at": ctx.now, "dc": ctx.dc, "docs_root": ctx.docs_root,
                                               "entries": [record_entry(r) for r in group]})
        if not args.no_registry:
            reg_path, changed = update_registry(ctx, results)
            for rid, rel in changed:
                print("registry: %s archive += %s" % (rid, rel))
    print_summary(results, args.report_only)
    return 0 if all(r["status"] in (PLANNED, SKIPPED) for r in results) else 1


def print_summary(results, report_only):
    print("migrate_scratch plan (%s)" % ("report only: nothing written" if report_only else "ops, copies, records"))
    tot = dict(dirs=0, files=0, bytes=0, md=0, copied=0, copied_bytes=0, cap=0, secret=0, ops=0)
    for r in results:
        line = "%-28s %-8s wave %s" % (r["slug"], r["status"], r["wave"])
        if r.get("reason"):
            line += "  reason: " + r["reason"]
        print(line)
        if "files" in r and r["files"]:
            copied_bytes = sum(c["bytes"] for c in r["copies"])
            print("    kind %s, direction %s, %d files in %d directories, %s, newest entry %.1f h old" % (
                r["kind"], r.get("direction"), len(r["files"]), len(r["dirs"]) + 1, human(r["total_bytes"]),
                r.get("newest_age_hours", 0.0)))
            if r["status"] in (SKIPPED, REFUSED):
                print("    markdown %d; nothing copied or staged" % r["md_files"])
            elif r["kind"] == "autoresearch":
                print("    %d file(s) with a sha256 twin in F, %d without" % (
                    len(r.get("matched", [])), len(r.get("unmatched", []))))
                for u in r.get("unmatched", []):
                    print("      kept, no twin: %s" % u)
            else:
                print("    markdown %d, copied %d (%s), cap exclusions %d, secret-scan blocks %d, archive-only %d "
                      "files (%s)" % (r["md_files"], len(r["copies"]), human(copied_bytes), len(r["excluded"]),
                                      len(r["secret_blocked"]), r["archive_only"]["files"],
                                      human(r["archive_only"]["bytes"])))
                for e in r["excluded"]:
                    print("      excluded (%s): %s, %s" % (e["reason"], e["path"], human(e["bytes"])))
                for s in r["secret_blocked"]:
                    print("      secret scan blocked: %s (%s; lines %s)" % (
                        s["path"], ", ".join(s["patterns"]), ",".join(str(x) for x in s["lines"])))
            print("    ops %d" % len(r["ops"]))
            tot["dirs"] += 1
            tot["files"] += len(r["files"])
            tot["bytes"] += r["total_bytes"]
            tot["md"] += r.get("md_files", 0)
            tot["copied"] += len(r["copies"])
            tot["copied_bytes"] += copied_bytes
            tot["cap"] += len(r["excluded"])
            tot["secret"] += len(r["secret_blocked"])
            tot["ops"] += len(r["ops"])
    print("total: %d directories inventoried, %d files, %s; markdown %d, copied %d (%s), cap exclusions %d, "
          "secret-scan blocks %d, ops %d" % (tot["dirs"], tot["files"], human(tot["bytes"]), tot["md"], tot["copied"],
                                             human(tot["copied_bytes"]), tot["cap"], tot["secret"], tot["ops"]))


# -------------------------------------------------------------------------------------------------------------
# verify


def check_tree(root, files, problems, label):
    found, _dirs, _newest = inventory(root)
    for rel, f in sorted(files.items()):
        g = found.get(rel)
        if g is None:
            problems.append("%s: missing %s" % (label, rel))
        elif g["type"] != f["type"] or g.get("sha256") != f.get("sha256") or g.get("target") != f.get("target") \
                or g["bytes"] != f["bytes"]:
            problems.append("%s: changed %s" % (label, rel))
    for rel in sorted(set(found) - set(files)):
        problems.append("%s: unexpected new entry %s" % (label, rel))


def verify_entry(e, problems, notes):
    slug = e["slug"]
    src, archive = e["source"], e["archive"]
    if e["kind"] in ("archive", "autoresearch"):
        applied = os.path.islink(src)
        if applied:
            if os.readlink(src) != e["link_target"]:
                problems.append("%s: symlink points at %s, expected %s" % (slug, os.readlink(src), e["link_target"]))
            if not os.path.isdir(archive):
                problems.append("%s: archive %s is missing" % (slug, archive))
                return
            if os.stat(archive).st_ino != e["source_inode"]:
                problems.append("%s: archive inode differs from the source inode (not a rename)" % slug)
            check_tree(archive, e["files"], problems, slug + " archive")
            if e["kind"] == "autoresearch":
                if not os.path.isdir(e["link_target"]):
                    problems.append("%s: symlink target %s does not exist yet" % (slug, e["link_target"]))
                for w in e.get("writes", []):
                    if not os.path.isfile(w["dest"]) or sha256_file(w["dest"]) != e["files"][w["rel"]]["sha256"]:
                        problems.append("%s: backup copy %s missing or changed" % (slug, w["rel"]))
            notes.append("%s: applied; %d entries match by sha256" % (slug, len(e["files"])))
        else:
            if not os.path.isdir(src):
                problems.append("%s: source %s is neither the directory nor the symlink" % (slug, src))
                return
            check_tree(src, e["files"], problems, slug + " source")
            notes.append("%s: not applied yet; source still matches its %d recorded entries" % (slug, len(e["files"])))
    else:
        check_tree(archive, e["files"], problems, slug + " archive")
        notes.append("%s: already archived; %d entries match" % (slug, len(e["files"])))
    for c in e.get("copies", []):
        p = os.path.join(e["copy_dir"], c["path"])
        if not os.path.isfile(p) or sha256_file(p) != c["sha256"]:
            problems.append("%s: markdown copy %s missing or changed" % (slug, c["path"]))
    if e.get("copy_dir") and not os.path.isfile(os.path.join(e["copy_dir"], "provenance.json")):
        problems.append("%s: provenance.json missing" % slug)


def cmd_verify(args):
    ctx = Context(args)
    path = args.record or ctx.records_path(args.wave)
    with open(path, encoding="utf-8") as fh:
        rec = json.load(fh)
    problems, notes = [], []
    for e in rec["entries"]:
        verify_entry(e, problems, notes)
    for n in notes:
        print("ok      " + n)
    for p in problems:
        print("PROBLEM " + p)
    print("verify %s: %d entries, %d problem(s)" % (path, len(rec["entries"]), len(problems)))
    return 1 if problems else 0


# -------------------------------------------------------------------------------------------------------------
# cli


def build_parser():
    p = argparse.ArgumentParser(description="Archive closed .scratch directories (autoresearch-workflow ticket 10).")
    sub = p.add_subparsers(dest="cmd")

    def common(sp):
        sp.add_argument("--alignment", default=ALIGNMENT, help="Alignment root that holds .scratch")
        sp.add_argument("--dc", default=DC_MAIN, help="Deception-Circuit main checkout (archive under outputs/_studies)")
        sp.add_argument("--docs-root", default=DOCS_ROOT, help="docs/research that receives the Markdown copies")
        sp.add_argument("--feature-dir", default=FEATURE_DIR, help="canonical autoresearch-workflow directory (R34)")
        sp.add_argument("--staging", default=STAGING, help="staging root S (ops/, records/, tree/)")
        sp.add_argument("--backup-root", default=BACKUP_ROOT, help="backup root for autoresearch-workflow (R34)")
        sp.add_argument("--rs-parent", default=RS_PARENT, help="directory that holds research_session/ (secret scan)")
        sp.add_argument("--now", type=float, help=argparse.SUPPRESS)
        sp.add_argument("--date", help="ISO date written into provenance and directions.json (default: today)")

    sp = sub.add_parser("plan", help="hash, copy Markdown, write ops and records; never moves anything")
    common(sp)
    sp.add_argument("--include", action="append", required=True, help="scratch slugs, comma-separated")
    sp.add_argument("--confirmed-live-session-finished", action="store_true",
                    help="allow R28 directories; their ops are wave D (only after the user's confirmation)")
    sp.add_argument("--report-only", action="store_true", help="hash and report; write nothing")
    sp.add_argument("--no-registry", action="store_true", help="do not edit directions.json")

    sv = sub.add_parser("verify", help="re-hash every recorded path, before or after the apply")
    common(sv)
    sv.add_argument("--wave", default="B", choices=["B", "D"])
    sv.add_argument("--record", help="records file (default: <staging>/records/10-migration-<wave>.json)")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd is None:
        parser.print_help()
        return 2
    try:
        return cmd_plan(args) if args.cmd == "plan" else cmd_verify(args)
    except MigrationError as exc:
        print("migrate_scratch: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
