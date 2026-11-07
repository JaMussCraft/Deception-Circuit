"""``init <slug>``: create a direction's records from ``_templates/`` (spec 5.6; R39).

It creates ``<root>/<slug>/`` with ``state.json``, ``worklog.json`` and ``ledger.json`` from the templates (slug
filled in, example rows removed), ``WORKLOG.md`` rendered from them with a first Log entry, ``RESUME.md`` from the
template, a ``README.md`` stub and ``START.md``. It never overwrites a file; ``--missing-only`` creates the absent
ones. When the slug is not in ``directions.json`` it adds a ``proposed`` row; it never claims.
"""

import json
import os
import re
import shutil
import sys

from research_session import lint as _lint
from research_session import paths, records, registry, state, worklog

FILES = ("state.json", "worklog.json", "ledger.json", "WORKLOG.md", "RESUME.md", "README.md", "START.md")


class InitError(Exception):
    pass


def _template(tdir, name):
    path = os.path.join(tdir, name)
    if not os.path.isfile(path):
        raise InitError("template %s is missing" % path)
    return path


def title_of(start_path, slug):
    for line in records.read_text(start_path).splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return slug


def _proposed_row(root, slug, title):
    rel = os.path.relpath(os.path.join(os.path.abspath(root), slug), registry.repo_root(root))
    return {"id": slug, "title": title, "status": "proposed", "status_source": rel + "/START.md",
            "summary": "Created by research-session init; the summary is written when the direction is planned.",
            "claimed_by": None, "claimed_at": None, "branch": None, "worktree": None, "dir": rel, "spec": None,
            "resume": rel + "/RESUME.md", "worklog": rel + "/WORKLOG.md", "state": rel + "/state.json",
            "ledger": rel + "/ledger.json", "frozen_grader_sha256": None, "parent_findings": [], "do_not_touch": [],
            "legacy_scratch": [], "archive": [], "updated": records.today()}


def init(cfg, slug, root, from_start=None, gpu_cap=None, max_jobs=None, api_cap=None, missing_only=False):
    """Returns ``(created, messages)``."""
    if not registry.SLUG_RE.match(slug or ""):
        raise InitError("slug %r must be lower-case words joined by hyphens" % slug)
    root = os.path.abspath(root)
    tdir = os.path.join(root, "_templates")
    if not os.path.isdir(tdir):
        raise InitError("no _templates directory at %s" % tdir)
    if from_start and not os.path.isfile(from_start):
        raise InitError("--from-start %s does not exist" % from_start)
    d = os.path.join(root, slug)
    existing = [f for f in FILES if os.path.exists(os.path.join(d, f))]
    if existing and not missing_only:
        raise InitError("refused: %s already holds %s; pass --missing-only to create only the absent files"
                        % (d, ", ".join(existing)))
    for name in ("state.json", "worklog.json", "ledger.json", "RESUME.md", "START.md"):
        _template(tdir, name)
    title = title_of(from_start, slug) if from_start else slug
    messages = []
    absent = lambda name: not os.path.exists(os.path.join(d, name))  # noqa: E731
    readme = ("# %s\n\nThis is the handoff page of the %s direction. Its starting prompt is START.md. The question, the"
              " verdict and pointers to the evidence are written here when the direction closes.\n" % (title, slug))
    resume = records.read_text(_template(tdir, "RESUME.md")).replace("<direction slug>", slug)
    for name, text in (("README.md", readme), ("RESUME.md", resume)):
        if absent(name):
            found = _lint.lint_text(text)
            if found:
                raise InitError("refused by the lint: " + "; ".join(_lint.format_finding(name, f) for f in found))
    os.makedirs(d, exist_ok=True)
    created = []
    if absent("START.md"):
        shutil.copyfile(from_start or _template(tdir, "START.md"), os.path.join(d, "START.md"))
        created.append("START.md")
    for name, text in (("README.md", readme), ("RESUME.md", resume)):
        if absent(name):
            records.write_text_atomic(os.path.join(d, name), text)
            created.append(name)
    if absent("state.json"):
        st = json.loads(records.read_text(_template(tdir, "state.json")))
        st.update({"direction": slug, "jobs": [], "sessions": {}, "last_worklog_entry_at": None,
                   "session_state": "running"})
        records.write_json(os.path.join(d, "state.json"), st)
        created.append("state.json")
    if absent("ledger.json"):
        led = json.loads(records.read_text(_template(tdir, "ledger.json")))
        led.update({"direction": slug, "reservations": [], "api_calls": [], "converted_from": None})
        for key, value, cast in (("reserved_gpu_hours", gpu_cap, float), ("max_concurrent_gpu_jobs", max_jobs, int),
                                 ("paid_api_usd", api_cap, float)):
            if value is not None:
                led["caps"][key] = cast(value)
        led["totals"] = registry.ledger_totals(dict(led, totals={"api_usd_reserve": 0.0}))
        records.write_json(os.path.join(d, "ledger.json"), led)
        created.append("ledger.json")
    elif any(v is not None for v in (gpu_cap, max_jobs, api_cap)):
        messages.append("ledger.json exists, so the cap options were ignored; use `worklog-set` to change caps")
    if absent("worklog.json"):
        wl = json.loads(records.read_text(_template(tdir, "worklog.json")))
        wl.update({"title": title, "state": "Running", "directions": [], "terms": [], "needs": [], "findings": [],
                   "incidents": [], "transcripts": "not recorded yet",
                   "right_now": "The direction was just created from the templates; no work has started yet."})
        records.write_json(os.path.join(d, "worklog.json"), wl)
        created.append("worklog.json")
    if absent("WORKLOG.md"):
        worklog.update_direction(cfg, d, lambda ctx: worklog.entry_text(
            ctx.t, "Direction created", "The research-session tool created this direction's records from the "
            "templates."))
        created.append("WORKLOG.md")
    messages.extend(add_directions_row(cfg, root, slug, title))
    return created, messages


def add_directions_row(cfg, root, slug, title):
    path = os.path.join(root, "directions.json")
    if not os.path.exists(path):
        return ["no directions.json at %s; no registry row was added" % path]
    with records.state_lock(cfg, os.path.realpath(path)):
        data = state.load_json(path)
        if slug in [r.get("id") for r in data.get("directions") or []]:
            return ["%s is already in directions.json" % slug]
        data["directions"].append(_proposed_row(root, slug, title))
        data["updated"] = records.today()
        errors, _ = registry.validate_directions(data)
        if errors:
            raise InitError("directions.json would be invalid: " + "; ".join(errors[:3]))
        records.write_json(path, data)
    return ["added a proposed row for %s to directions.json; it is not claimed" % slug]


def cmd_init(args):
    cfg = paths.Config.from_env()
    root = args.root or registry.default_root(cfg)
    try:
        created, messages = init(cfg, args.slug, root, args.from_start, args.gpu_cap, args.max_gpu_jobs,
                                 args.api_cap, args.missing_only)
    except (InitError, worklog.WorklogError, worklog.UsageError) as exc:
        sys.stderr.write("research-session: %s\n" % exc)
        return 1
    print("%s: created %s" % (os.path.join(os.path.abspath(root), args.slug), ", ".join(created) or "nothing"))
    for m in messages:
        print(m)
    return 0


def add_parsers(sub):
    p = sub.add_parser("init", help="create a direction's records from _templates (R39); never overwrites")
    p.add_argument("slug")
    p.add_argument("--from-start", metavar="START.md", help="copy this starting prompt; its first heading is the title")
    p.add_argument("--gpu-cap", type=float, metavar="H", help="reserved GPU-hour cap (default 0: no GPU work)")
    p.add_argument("--max-gpu-jobs", type=int, metavar="K", help="concurrent GPU job cap (default 0)")
    p.add_argument("--api-cap", type=float, metavar="USD", help="paid API cap in dollars (default 0)")
    p.add_argument("--missing-only", action="store_true", help="create only the files that are absent")
    p.add_argument("--root", help="research root (default: DC/docs/research)")
    p.set_defaults(func=cmd_init)
