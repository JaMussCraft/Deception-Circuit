#!/usr/bin/env python3
"""Apply staged files and op lists to their destinations (spec section 7). Stdlib only, Python 3.9 and 3.12.

Agents never write to the Alignment checkout or to user configuration. They stage full files under
``S/tree/<absolute destination without the leading slash>`` and list ops in ``S/ops/<NN>-<slug>.json``. The
orchestrator runs this tool, one wave at a time:

    apply_staged.py --staging S --wave A [--only 01] [--dry-run]
    apply_staged.py --rollback <backup-root>/<run>/journal.json [--dry-run]

Op kinds: write, json_merge, replace_text, append_text, text_block, move, symlink, mkdir. Every op is idempotent:
an op whose target already has the desired state is reported as SKIP. Before a target changes, the tool copies it
to ``<backup-root>/<run>/<absolute path>`` and appends the op to ``<backup-root>/<run>/journal.json``.

Output never contains file content or JSON values: ``json_merge`` reports key paths only, so nothing under ``env``
is ever printed. Statuses: APPLY, WOULD APPLY (dry run), SKIP, CONFLICT, REFUSED, ERROR. Exit code 1 when any op
is not APPLY or SKIP.

Safety nets beyond spec section 7: a hook-installing op outside wave H is refused (R26), and an op of wave A or B
on a path that R28 defers to wave D is refused.

Additions from ticket 12:

- ``expect_sha256: "absent"`` means the destination must not exist yet (spec 7); an existing file is a CONFLICT.
- A dry run carries planned state forward within the run: a planned ``mkdir`` creates its directory, a planned
  ``move`` frees its source and fills its destination, a planned ``symlink`` or new-file ``write`` fills its path.
  A chained mkdir, move and symlink sequence therefore plans without ERROR or CONFLICT. A real run never uses it.
- ``move`` falls back to copy, sha256 verification of every file and link, and removal of the source when
  ``os.rename`` fails with EXDEV (different file systems). The journal records ``"method": "copy"``, and rollback
  uses the same fallback. A move whose source path is now a symlink, either to its destination or to the target a
  staged symlink op names for that path, counts as already moved.
- A ``write`` that this same op (ticket and index) installed in an earlier run, recorded in a journal under the
  backup root, is reported as SKIP when the destination has changed since, for example by a later text op. This
  holds only while the file differs from the journal's pre-apply hash, so a rolled-back write applies again.
"""

import argparse
import copy
import datetime
import difflib
import errno
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

try:
    import tomllib
except ImportError:  # Python 3.9
    tomllib = None

BASE_PYTHON = "/sw/external/python/anaconda3/bin/python3.9"
INSTALLED_CLI = "/projects/beto/swong2/Alignment/.agents/research_session/cli.py"
STAGED_CLI_REL = "tree/projects/beto/swong2/Alignment/.agents/research_session/cli.py"
DEFAULT_BACKUP_ROOT = "/u/swong2/.claude/research-session/backups"
WAVES = ("A", "H", "B", "C", "D")
OP_KINDS = ("write", "json_merge", "replace_text", "append_text", "text_block", "move", "symlink", "mkdir")

# R28: paths that waves A and B never touch.
PROTECTED_SCRATCH_RE = re.compile(r"/\.scratch/(sdr-[^/]*|selective-deception|eval5-grader-fixes)(/|$)")
PROTECTED_NOTES = ("sdr-mechanism-review.md", "selective-deception-execution.md")

APPLY, WOULD, SKIP, CONFLICT, REFUSED, ERROR = "APPLY", "WOULD APPLY", "SKIP", "CONFLICT", "REFUSED", "ERROR"


class OpProblem(Exception):
    def __init__(self, status, reason):
        Exception.__init__(self, reason)
        self.status = status
        self.reason = reason


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    with open(path, "rb") as fh:
        return sha256_bytes(fh.read())


def read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def line_delta(old, new):
    """(added, removed) line counts between two byte strings; content is never printed."""
    a = old.decode("utf-8", errors="replace").splitlines()
    b = new.decode("utf-8", errors="replace").splitlines()
    added = removed = 0
    for line in difflib.unified_diff(a, b, lineterm="", n=0):
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
    return added, removed


def tree_manifest(path):
    """``{relative path: ("dir",) | ("link", target) | ("file", sha256)}`` for a file, a symlink or a whole tree."""
    found = {}

    def add(p, rel):
        if os.path.islink(p):
            found[rel] = ("link", os.readlink(p))
        elif os.path.isdir(p):
            found[rel] = ("dir",)
            for name in sorted(os.listdir(p)):
                add(os.path.join(p, name), os.path.join(rel, name) if rel else name)
        else:
            found[rel] = ("file", sha256_file(p))

    add(path, "")
    return found


def remove_path(path):
    if os.path.islink(path) or (os.path.lexists(path) and not os.path.isdir(path)):
        os.unlink(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)


def move_path(src, dest):
    """Rename ``src`` to ``dest``; across file systems (EXDEV) copy, verify every sha256, then remove the source.

    Returns ``"rename"`` or ``"copy"``. A copy that does not verify is removed and the source is kept.
    """
    try:
        os.rename(src, dest)
        return "rename"
    except OSError as exc:
        if exc.errno != errno.EXDEV:
            raise
    before = tree_manifest(src)
    try:
        if os.path.islink(src):
            os.symlink(os.readlink(src), dest)
        elif os.path.isdir(src):
            shutil.copytree(src, dest, symlinks=True)
        else:
            shutil.copy2(src, dest)
        after = tree_manifest(dest)
    except BaseException:
        remove_path(dest)
        raise
    if after != before:
        remove_path(dest)
        raise OpProblem(ERROR, "cross-device copy did not verify (sha256); source kept, copy removed")
    remove_path(src)
    return "copy"


def default_lint_cmd(staging, installed_cli=INSTALLED_CLI, python=BASE_PYTHON):
    """Base python3.9 on the staged RS cli.py, falling back to the installed one; None when neither exists."""
    staged = os.path.join(staging, STAGED_CLI_REL)
    for cli in (staged, installed_cli):
        if os.path.isfile(cli):
            return [python, "-B", cli, "lint"]
    return None


def is_codex_config(path):
    return os.path.basename(path) == "config.toml" and os.path.basename(os.path.dirname(path)) == ".codex"


def protected_reason(op):
    """Name the R28 rule an op would break, or None."""
    paths = [op.get(k) for k in ("dest", "src", "path", "target") if isinstance(op.get(k), str)]
    for p in paths:
        if PROTECTED_SCRATCH_RE.search(p):
            return "touches a live-session .scratch directory (R28)"
        if os.path.basename(p) in PROTECTED_NOTES:
            return "touches a live-session memory note (R28)"
    if op.get("op") in ("replace_text", "append_text"):
        text = (op.get("old_text") or "") + (op.get("new_text") or "") + (op.get("text") or "")
        if any("](" + note + ")" in text for note in PROTECTED_NOTES):
            return "edits a MEMORY.md line R28 defers to wave D"
    return None


def installs_hooks(op, staging):
    if op.get("op") == "json_merge":
        return isinstance(op.get("fragment"), dict) and "hooks" in op["fragment"]
    if op.get("op") == "write" and str(op.get("dest", "")).endswith(".json"):
        try:
            data = json.loads(read_bytes(resolve_src(staging, op)).decode("utf-8"))
        except Exception:
            return False
        return isinstance(data, dict) and "hooks" in data
    return False


def resolve_src(staging, op):
    src = op.get("src")
    if not isinstance(src, str) or not src:
        raise OpProblem(ERROR, "write needs src")
    full = os.path.realpath(src if os.path.isabs(src) else os.path.join(staging, src))
    root = os.path.realpath(staging)
    if not full.startswith(root + os.sep):
        raise OpProblem(REFUSED, "src resolves outside the staging root")
    if not os.path.isfile(full):
        raise OpProblem(ERROR, "staged src missing")
    return full


# ---------------------------------------------------------------- json_merge


def _canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _is_hook_group(value):
    return isinstance(value, dict) and isinstance(value.get("hooks"), list) and all(
        isinstance(h, dict) for h in value["hooks"])


def _commands(group):
    return set(h.get("command") for h in group["hooks"] if isinstance(h.get("command"), str))


def _entry_present(existing, entry):
    canon = _canon(entry)
    for item in existing:
        if _canon(item) == canon:
            return True
        # Hook groups compare by matcher and command string, so a changed timeout never duplicates a group.
        if _is_hook_group(item) and _is_hook_group(entry) and item.get("matcher") == entry.get("matcher"):
            cmds = _commands(entry)
            if cmds and cmds <= _commands(item):
                return True
    return False


def _path_str(path):
    return ".".join(str(p) for p in path) if path else "(root)"


def deep_merge(base, fragment, path, changes):
    """Merge ``fragment`` into ``base`` in place. Dicts merge, lists only extend, scalars take the fragment value."""
    for key, value in fragment.items():
        here = path + [key]
        if key not in base:
            base[key] = copy.deepcopy(value)
            changes.append("+ " + _path_str(here))
            continue
        current = base[key]
        if isinstance(current, dict) and isinstance(value, dict):
            deep_merge(current, value, here, changes)
        elif isinstance(current, list) and isinstance(value, list):
            added = 0
            for entry in value:
                if not _entry_present(current, entry):
                    current.append(copy.deepcopy(entry))
                    added += 1
            if added:
                changes.append("+ %s[] (%d entr%s appended)" % (_path_str(here), added, "y" if added == 1 else "ies"))
        elif isinstance(current, (dict, list)) or isinstance(value, (dict, list)):
            raise OpProblem(CONFLICT, "type mismatch at " + _path_str(here))
        elif current != value or type(current) is not type(value):
            base[key] = copy.deepcopy(value)
            changes.append("~ " + _path_str(here))


def dump_json(data, ensure_ascii):
    return (json.dumps(data, indent=2, ensure_ascii=ensure_ascii) + "\n").encode("utf-8")


# ---------------------------------------------------------------- text_block

_TABLE_HEADER_RE = re.compile(r"^\s*\[\[?\s*[A-Za-z0-9_\"'.\- /]+\s*\]\]?\s*(#.*)?$")


def render_block(marker, text):
    body = text if text.endswith("\n") else text + "\n"
    return "# BEGIN %s\n%s# END %s\n" % (marker, body, marker)


def apply_text_block(content, marker, text, position):
    block = render_block(marker, text)
    pattern = re.compile(r"^# BEGIN " + re.escape(marker) + r"\n.*?^# END " + re.escape(marker) + r"\n?", re.M | re.S)
    if pattern.search(content):
        return pattern.sub(lambda _: block, content, count=1)
    lines = content.split("\n")
    if position == "before_first_table":
        for i, line in enumerate(lines):
            if _TABLE_HEADER_RE.match(line):
                head = "\n".join(lines[:i])
                head = head + "\n" if head else ""
                return head + block + "\n" + "\n".join(lines[i:])
    elif position not in (None, "end"):
        raise OpProblem(ERROR, "unknown text_block position " + str(position))
    if content and not content.endswith("\n"):
        content += "\n"
    sep = "\n" if content.strip() else ""
    return content + sep + block


# ---------------------------------------------------------------- the runner


class Runner(object):
    def __init__(self, args, out=None):
        self.args = args
        self.out = out or sys.stdout
        self.dry = args.dry_run
        self.run_dir = None
        self.journal = None
        self.failures = 0
        self.planned = {}     # dry run only: normalized path -> planned entry (see _resolve)
        self.link_ops = {}    # normalized path -> target of every staged symlink op (move re-run check)
        self._applied = None  # (ticket, index, dest) -> [(run, sha256_before, sha256_after)] from earlier journals
        if args.lint_cmd:
            self.lint_cmd = shlex.split(args.lint_cmd)
        else:
            self.lint_cmd = default_lint_cmd(args.staging) if args.staging else None

    def say(self, label, status, detail=""):
        self.out.write("%s %s%s\n" % (label, status, (": " + detail) if detail else ""))
        if status not in (APPLY, WOULD, SKIP):
            self.failures += 1

    # -- dry-run overlay: planned state carried forward within one run (never used by a real run)
    #
    # Entries: ("absent",), ("dir",), ("file",), ("link", target) and ("alias", disk path). An alias is a planned
    # move's destination; it and everything under it are looked up at the source's disk path.

    def plan(self, path, entry):
        if self.dry:
            self.planned[os.path.normpath(path)] = entry

    def _resolve(self, path):
        """``("disk", p)`` to look ``p`` up on disk, or ``("planned", entry)``."""
        path = os.path.normpath(path)
        if not self.planned:
            return ("disk", path)
        rel = []
        p = path
        while True:
            entry = self.planned.get(p)
            if entry is not None:
                tail = list(reversed(rel))
                if entry[0] == "alias":
                    return ("disk", os.path.join(entry[1], *tail) if tail else entry[1])
                if not tail:
                    return ("planned", entry)
                if entry[0] == "link":
                    return self._resolve(os.path.join(entry[1], *tail))
                return ("planned", ("absent",))
            parent = os.path.dirname(p)
            if parent == p:
                return ("disk", path)
            rel.append(os.path.basename(p))
            p = parent

    def lexists(self, path):
        where, x = self._resolve(path)
        return os.path.lexists(x) if where == "disk" else x[0] != "absent"

    def isdir(self, path):
        where, x = self._resolve(path)
        if where == "disk":
            return os.path.isdir(x)
        return x[0] == "dir" or (x[0] == "link" and self.isdir(x[1]))

    def readlink(self, path):
        where, x = self._resolve(path)
        if where == "disk":
            return os.readlink(x) if os.path.islink(x) else None
        return x[1] if x[0] == "link" else None

    # -- journals of earlier runs

    def applied_runs(self):
        if self._applied is None:
            self._applied = {}
            root = self.args.backup_root
            for run in sorted(os.listdir(root)) if os.path.isdir(root) else []:
                try:
                    with open(os.path.join(root, run, "journal.json")) as fh:
                        journal = json.load(fh)
                except (IOError, OSError, ValueError):
                    continue
                for e in journal.get("entries", []) if isinstance(journal, dict) else []:
                    if isinstance(e, dict) and e.get("op") == "write" and e.get("dest") and e.get("sha256_after"):
                        key = (str(e.get("ticket")), e.get("index"), e["dest"])
                        self._applied.setdefault(key, []).append((run, e.get("sha256_before"), e["sha256_after"]))
        return self._applied

    def applied_earlier(self, op, path, old, new):
        """The run in which this write op installed exactly ``new`` at ``path``, if the file has moved on since."""
        if op.get("op") != "write" or old is None:
            return None
        current, wanted = sha256_bytes(old), sha256_bytes(new)
        for run, before, after in self.applied_runs().get((str(op["_ticket"]), op["_index"], path), []):
            if after == wanted and current != before:
                return run
        return None

    # -- backup and journal

    def ensure_run_dir(self):
        if self.run_dir is None:
            stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S.%f")
            self.run_dir = os.path.join(self.args.backup_root, stamp)
            os.makedirs(self.run_dir)
            self.journal = {"schema": 1, "tool": "apply_staged", "started": stamp, "staging": self.args.staging,
                            "wave": self.args.wave, "only": self.args.only, "entries": []}
            self.write_journal()
        return self.run_dir

    def write_journal(self):
        path = os.path.join(self.run_dir, "journal.json")
        tmp = path + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(self.journal, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)

    def record(self, entry):
        self.journal["entries"].append(entry)
        self.write_journal()

    def backup(self, path):
        dest = os.path.join(self.ensure_run_dir(), path.lstrip(os.sep))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(path, dest)
        return dest

    # -- content ops share one path: compute desired bytes, check, lint, back up, replace atomically

    def lint_failures(self, path, content):
        """Lint output lines (``rule: excerpt``) for ``content`` stored under ``path``'s base name."""
        if not self.lint_cmd:
            raise OpProblem(REFUSED, "lint requested but no lint command is available")
        tmpdir = tempfile.mkdtemp(prefix="apply-staged-lint-")
        try:
            target = os.path.join(tmpdir, os.path.basename(path))
            with open(target, "wb") as fh:
                fh.write(content)
            proc = subprocess.run(self.lint_cmd + [target], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  universal_newlines=True)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
        if proc.returncode == 0:
            return []
        if proc.returncode != 1:
            raise OpProblem(REFUSED, "lint command failed with exit %d" % proc.returncode)
        found = []
        for line in proc.stdout.splitlines():
            if line.startswith(target + ":"):
                rest = line[len(target) + 1:]
                found.append(rest.split(": ", 1)[1] if ": " in rest else rest)
        return found or ["lint exit 1"]

    def check_lint(self, op, path, old, new, whole_file):
        if not op.get("lint"):
            return
        after = self.lint_failures(path, new)
        if not whole_file and old is not None:
            # Text ops: report only failures the op introduces; units already failing in the file stay as they are.
            before = self.lint_failures(path, old)
            for item in before:
                if item in after:
                    after.remove(item)
        if after:
            raise OpProblem(REFUSED, "lint: " + " | ".join(after[:3]))

    def replace_content(self, label, op, path, new, mode_src=None, whole_file_lint=True, extra=""):
        exists = os.path.lexists(path)
        old = read_bytes(path) if exists else None
        if old == new:
            self.say(label, SKIP, "already applied")
            return
        earlier = self.applied_earlier(op, path, old, new)
        if earlier:
            self.say(label, SKIP, "applied in run %s; destination changed since by later ops or edits" % earlier)
            return
        expect = op.get("expect_sha256")
        if expect == "absent":
            if exists:
                raise OpProblem(CONFLICT, "expect_sha256 is absent but the destination exists")
        elif expect is not None:
            if not exists:
                raise OpProblem(CONFLICT, "expect_sha256 given but the destination is missing")
            if sha256_bytes(old) != expect:
                raise OpProblem(CONFLICT, "destination changed since staging (sha256 differs)")
        if path.endswith(".toml") and tomllib is not None:
            try:
                tomllib.loads(new.decode("utf-8"))
            except Exception as exc:
                raise OpProblem(ERROR, "result is not valid TOML (%s)" % type(exc).__name__)
        self.check_lint(op, path, old, new, whole_file_lint)
        added, removed = line_delta(old or b"", new)
        detail = ("+%d -%d lines" % (added, removed)) + (", new file" if not exists else "") + extra
        if self.dry:
            if not exists:
                self.plan(path, ("file",))
            self.say(label, WOULD, detail)
            return
        created_dirs = []
        parent = os.path.dirname(path)
        missing = []
        while parent and not os.path.isdir(parent):
            missing.append(parent)
            parent = os.path.dirname(parent)
        for d in reversed(missing):
            os.mkdir(d)
            created_dirs.append(d)
        backup = self.backup(path) if exists else None
        self.ensure_run_dir()
        tmp = path + ".apply-staged.tmp"
        with open(tmp, "wb") as fh:
            fh.write(new)
        if exists:
            shutil.copymode(path, tmp)
        elif mode_src:
            shutil.copymode(mode_src, tmp)
        os.replace(tmp, path)
        self.record({"ticket": op["_ticket"], "index": op["_index"], "op": op["op"], "dest": path,
                     "kind": "modified" if exists else "created", "backup": backup,
                     "sha256_before": sha256_bytes(old) if exists else None, "sha256_after": sha256_bytes(new),
                     "created_dirs": created_dirs})
        self.say(label, APPLY, detail)

    # -- op kinds

    def op_write(self, label, op):
        src = resolve_src(self.args.staging, op)
        self.replace_content(label, op, self.real(op["dest"]), read_bytes(src), mode_src=src)

    def op_json_merge(self, label, op):
        path = self.real(op["dest"])
        fragment = op.get("fragment")
        if not isinstance(fragment, dict):
            raise OpProblem(ERROR, "json_merge needs a fragment object")
        raw = read_bytes(path) if os.path.exists(path) else b"{}\n"
        try:
            data = json.loads(raw.decode("utf-8"))
        except ValueError:
            raise OpProblem(ERROR, "destination is not valid JSON")
        if not isinstance(data, dict):
            raise OpProblem(ERROR, "destination is not a JSON object")
        changes = []
        deep_merge(data, fragment, [], changes)
        if not changes:
            self.say(label, SKIP, "already applied")
            return
        ascii_only = all(b < 128 for b in raw)
        new = dump_json(data, ensure_ascii=ascii_only)
        self.replace_content(label, op, path, new, extra="; " + ", ".join(changes))

    def op_replace_text(self, label, op):
        path = self.real(op["dest"])
        old_text, new_text = op.get("old_text"), op.get("new_text")
        if not isinstance(old_text, str) or not old_text or not isinstance(new_text, str):
            raise OpProblem(ERROR, "replace_text needs old_text and new_text")
        content = read_bytes(path).decode("utf-8")
        # Already applied: new_text is present and old_text is gone. When new_text extends old_text, the old text
        # survives inside every copy of new_text, so mask those copies first; otherwise any old_text left counts.
        masked = content.replace(new_text, "\x00") if new_text and old_text in new_text else content
        if new_text and new_text in content and old_text not in masked:
            self.say(label, SKIP, "already applied")
            return
        count = content.count(old_text)
        if count != 1:
            raise OpProblem(CONFLICT, "old_text occurs %d times (needs exactly 1)" % count)
        new = content.replace(old_text, new_text, 1).encode("utf-8")
        self.replace_content(label, op, path, new, whole_file_lint=False)

    def op_append_text(self, label, op):
        path = self.real(op["dest"])
        text = op.get("text")
        if not isinstance(text, str) or not text:
            raise OpProblem(ERROR, "append_text needs text")
        content = read_bytes(path).decode("utf-8") if os.path.exists(path) else ""
        if text in content:
            self.say(label, SKIP, "already present")
            return
        if content and not content.endswith("\n"):
            content += "\n"
        self.replace_content(label, op, path, (content + text).encode("utf-8"), whole_file_lint=False)

    def op_text_block(self, label, op):
        path = self.real(op["dest"])
        marker, text = op.get("marker"), op.get("text")
        if not isinstance(marker, str) or not marker or not isinstance(text, str):
            raise OpProblem(ERROR, "text_block needs marker and text")
        content = read_bytes(path).decode("utf-8") if os.path.exists(path) else ""
        new = apply_text_block(content, marker, text, op.get("position")).encode("utf-8")
        self.replace_content(label, op, path, new, whole_file_lint=False)

    def op_move(self, label, op):
        src, dest = op.get("src"), op.get("dest")
        if not isinstance(src, str) or not isinstance(dest, str):
            raise OpProblem(ERROR, "move needs src and dest")
        link = self.readlink(src)
        if self.lexists(dest) and (not self.lexists(src) or link == dest or
                                   (link is not None and link == self.link_ops.get(os.path.normpath(src)))):
            # The migrations replace the source path with a link: to the destination (R3), or to the target a
            # staged symlink op names for that path (the autoresearch-workflow exception, R34).
            self.say(label, SKIP, "already moved")
            return
        if not self.lexists(src):
            raise OpProblem(ERROR, "move source missing")
        if self.lexists(dest):
            raise OpProblem(CONFLICT, "move destination exists")
        if not self.isdir(os.path.dirname(dest)):
            raise OpProblem(ERROR, "move destination parent missing")
        if self.dry:
            where, x = self._resolve(src)
            self.plan(dest, ("alias", x) if where == "disk" else x)
            self.plan(src, ("absent",))
            self.say(label, WOULD, "rename (copy if across file systems)")
            return
        self.ensure_run_dir()
        method = move_path(src, dest)
        self.record({"ticket": op["_ticket"], "index": op["_index"], "op": "move", "src": src, "dest": dest,
                     "method": method})
        self.say(label, APPLY, "rename" if method == "rename" else
                 "copied across file systems, sha256 verified, source removed")

    def op_symlink(self, label, op):
        path, target = op.get("path"), op.get("target")
        if self.readlink(path) == target:
            self.say(label, SKIP, "already linked")
            return
        if self.lexists(path):
            raise OpProblem(CONFLICT, "link path exists")
        if self.dry:
            self.plan(path, ("link", target))
            self.say(label, WOULD, "symlink")
            return
        self.ensure_run_dir()
        os.symlink(target, path)
        self.record({"ticket": op["_ticket"], "index": op["_index"], "op": "symlink", "path": path,
                     "target": target})
        self.say(label, APPLY, "symlink")

    def op_mkdir(self, label, op):
        path = op.get("path")
        if self.isdir(path):
            self.say(label, SKIP, "already exists")
            return
        if self.lexists(path):
            raise OpProblem(CONFLICT, "path exists and is not a directory")
        if self.dry:
            p = path
            while p and not self.isdir(p):
                self.plan(p, ("dir",))
                p = os.path.dirname(p)
            self.say(label, WOULD, "mkdir")
            return
        self.ensure_run_dir()
        missing = []
        p = path
        while p and not os.path.isdir(p):
            missing.append(p)
            p = os.path.dirname(p)
        for d in reversed(missing):
            os.mkdir(d)
        self.record({"ticket": op["_ticket"], "index": op["_index"], "op": "mkdir", "path": path,
                     "created_dirs": list(reversed(missing))})
        self.say(label, APPLY, "mkdir")

    @staticmethod
    def real(path):
        if not isinstance(path, str) or not os.path.isabs(path):
            raise OpProblem(ERROR, "destination must be an absolute path")
        return os.path.realpath(path)

    # -- driver

    def load_ops(self):
        ops_dir = os.path.join(self.args.staging, "ops")
        only = set()
        for item in self.args.only or []:
            only.update(x.strip() for x in item.split(",") if x.strip())
        loaded = []
        for name in sorted(os.listdir(ops_dir)) if os.path.isdir(ops_dir) else []:
            if not name.endswith(".json"):
                continue
            with open(os.path.join(ops_dir, name)) as fh:
                doc = json.load(fh)
            ticket = str(doc.get("ticket", name.split("-", 1)[0]))
            if only and ticket not in only and name.split("-", 1)[0] not in only:
                continue
            for i, op in enumerate(doc.get("ops", []), 1):
                op = dict(op)
                op["_ticket"], op["_index"], op["_file"] = ticket, i, name
                loaded.append(op)
        return loaded

    def run(self):
        ops = self.load_ops()
        self.link_ops = dict((os.path.normpath(op["path"]), op.get("target")) for op in ops
                             if op.get("op") == "symlink" and isinstance(op.get("path"), str))
        selected = [op for op in ops if op.get("wave") == self.args.wave]
        bad_wave = [op for op in ops if op.get("wave") not in WAVES]
        for op in bad_wave:
            self.say("[%s#%d]" % (op["_ticket"], op["_index"]), ERROR, "op has no valid wave")
        self.out.write("%s wave %s: %d op(s) selected from %d\n" % (
            "dry run," if self.dry else "apply,", self.args.wave, len(selected), len(ops)))
        for op in selected:
            kind = op.get("op")
            target = op.get("dest") or op.get("path")
            label = "[%s#%d] %s %s" % (op["_ticket"], op["_index"], kind, target)
            try:
                if kind not in OP_KINDS:
                    raise OpProblem(ERROR, "unknown op kind")
                reason = protected_reason(op) if op["wave"] in ("A", "B") else None
                if reason:
                    raise OpProblem(REFUSED, reason)
                if op["wave"] != "H" and installs_hooks(op, self.args.staging):
                    raise OpProblem(REFUSED, "hook installation must be wave H (R26)")
                if isinstance(target, str) and is_codex_config(target) and "codex-config" not in (self.args.allow or []):
                    raise OpProblem(REFUSED, "~/.codex/config.toml needs --allow codex-config")
                getattr(self, "op_" + kind)(label, op)
            except OpProblem as exc:
                self.say(label, exc.status, exc.reason)
            except (IOError, OSError) as exc:
                self.say(label, ERROR, "%s (%s)" % (type(exc).__name__, exc.strerror or "os error"))
        if self.run_dir:
            self.out.write("journal: %s\n" % os.path.join(self.run_dir, "journal.json"))
        return 1 if self.failures else 0


def rollback(journal_path, dry, out):
    with open(journal_path) as fh:
        journal = json.load(fh)
    failures = 0

    def say(label, status, detail=""):
        out.write("%s %s%s\n" % (label, status, (": " + detail) if detail else ""))
        return 0 if status in (APPLY, WOULD, SKIP) else 1

    def remove_dirs(dirs):
        for d in sorted(dirs, key=len, reverse=True):
            if os.path.isdir(d) and not os.listdir(d):
                os.rmdir(d)

    for entry in reversed(journal.get("entries", [])):
        kind = entry.get("op")
        label = "[rollback %s#%s] %s %s" % (entry.get("ticket"), entry.get("index"), kind,
                                            entry.get("dest") or entry.get("path"))
        status = WOULD if dry else APPLY
        try:
            if kind == "move":
                src, dest = entry["src"], entry["dest"]
                if os.path.lexists(src) and not os.path.lexists(dest):
                    failures += say(label, SKIP, "already restored")
                elif os.path.lexists(dest) and not os.path.lexists(src):
                    if not dry:
                        move_path(dest, src)
                    failures += say(label, status, "rename back")
                else:
                    failures += say(label, CONFLICT, "both or neither of src and dest exist")
            elif kind == "symlink":
                path = entry["path"]
                if not os.path.lexists(path):
                    failures += say(label, SKIP, "already removed")
                elif os.path.islink(path) and os.readlink(path) == entry["target"]:
                    if not dry:
                        os.unlink(path)
                    failures += say(label, status, "unlink")
                else:
                    failures += say(label, CONFLICT, "path changed since apply")
            elif kind == "mkdir":
                dirs = entry.get("created_dirs", [])
                if not any(os.path.isdir(d) for d in dirs):
                    failures += say(label, SKIP, "already removed")
                elif any(os.path.isdir(d) and os.listdir(d) for d in dirs[-1:]):
                    failures += say(label, CONFLICT, "directory is not empty")
                else:
                    if not dry:
                        remove_dirs(dirs)
                    failures += say(label, status, "rmdir")
            else:
                dest = entry["dest"]
                current = sha256_file(dest) if os.path.exists(dest) else None
                if entry["kind"] == "created":
                    if current is None:
                        failures += say(label, SKIP, "already removed")
                    elif current == entry["sha256_after"]:
                        if not dry:
                            os.unlink(dest)
                            remove_dirs(entry.get("created_dirs", []))
                        failures += say(label, status, "remove created file")
                    else:
                        failures += say(label, CONFLICT, "file changed since apply")
                else:
                    if current == entry["sha256_before"]:
                        failures += say(label, SKIP, "already restored")
                    elif current == entry["sha256_after"]:
                        if not dry:
                            tmp = dest + ".apply-staged.tmp"
                            shutil.copy2(entry["backup"], tmp)
                            shutil.copymode(dest, tmp)
                            os.replace(tmp, dest)
                        failures += say(label, status, "restore backup")
                    else:
                        failures += say(label, CONFLICT, "file changed since apply")
        except OpProblem as exc:
            failures += say(label, exc.status, exc.reason)
        except (IOError, OSError, KeyError) as exc:
            failures += say(label, ERROR, type(exc).__name__)
    return 1 if failures else 0


def build_parser():
    p = argparse.ArgumentParser(description="Apply staged files and op lists (autoresearch-workflow spec 7).")
    p.add_argument("--staging", help="staging root S (holds tree/ and ops/)")
    p.add_argument("--wave", choices=WAVES, help="apply only ops of this wave (required unless --rollback)")
    p.add_argument("--only", action="append", help="ticket number(s), repeatable or comma-separated")
    p.add_argument("--dry-run", action="store_true", help="report what would change; write nothing")
    p.add_argument("--allow", action="append", choices=["codex-config"], help="permit ops on ~/.codex/config.toml")
    p.add_argument("--lint-cmd", help="lint command; the file path is appended (default: base python3.9 on the "
                                      "staged research_session/cli.py lint, then the installed one)")
    p.add_argument("--rollback", metavar="JOURNAL", help="undo the run recorded in this journal.json")
    p.add_argument("--backup-root", default=DEFAULT_BACKUP_ROOT, help="where backups and journals go")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.rollback:
        return rollback(args.rollback, args.dry_run, sys.stdout)
    if not args.staging or not args.wave:
        parser.error("--staging and --wave are required unless --rollback is given")
    return Runner(args).run()


if __name__ == "__main__":
    sys.exit(main())
