"""``findings-check``: the seed-replication gate, the provenance gate and the grader check (spec 6.3, 6.5; R2, R16).

It reads ``FINDINGS.md`` and, for each ``verified`` or ``replicated`` row, the provenance files named in its evidence
cell. A provenance file is ``run_manifest.json`` (spec 4.6). A legacy ``manifest.json`` that names ``git_commit`` is
accepted with a warning (R2). With ``--paper DRAFT`` every F-id the draft cites must be ``replicated``.
"""

import json
import os
import re
import sys

from research_session import records, registry, state

HEX40 = re.compile(r"^[0-9a-f]{40}$")
CITED = re.compile(r"\bF-[a-z0-9]+(?:-[a-z0-9]+)*-[0-9]{3}\b")


def _provenance_files(repo, cell):
    """``[(path, data_or_None, legacy)]`` for each evidence path that is or contains a provenance file."""
    out = []
    for rel in registry.evidence_paths(cell):
        p = rel if os.path.isabs(rel) else os.path.join(repo, rel)
        cands = [p] if registry.is_provenance_path(p) else (
            [os.path.join(p, "run_manifest.json"), os.path.join(p, "manifest.json")] if os.path.isdir(p) else [])
        for c in cands:
            if not registry.is_provenance_path(c):
                continue
            legacy = os.path.basename(c) == "manifest.json"
            data = None
            if os.path.isfile(c):
                try:
                    data = json.loads(records.read_text(c))
                except ValueError:
                    data = None
            out.append((c, data, legacy))
            if data is not None:
                break
    return out


def check(repo, findings_text, directions=None, paper_text=None):
    """``(errors, warnings)`` for the FINDINGS rows and an optional paper draft."""
    rows, errors = registry.parse_findings(findings_text)
    warnings = []
    frozen = {}
    for d in (directions or {}).get("directions") or []:
        frozen[d.get("id")] = d.get("frozen_grader_sha256")
    by_id = {}
    for r in rows:
        by_id[r["id"]] = r
        where = "%s (line %d)" % (r["id"], r["line"])
        if r["status"] not in ("verified", "replicated"):
            continue
        good = []
        for path, data, legacy in _provenance_files(repo, r["evidence"]):
            rel = os.path.relpath(path, repo)
            if data is None:
                errors.append("%s: provenance file %s is missing or unreadable" % (where, rel))
                continue
            commit = data.get("git_commit")
            if not (isinstance(commit, str) and HEX40.match(commit)):
                errors.append("%s: %s does not name a 40-hex git_commit" % (where, rel))
                continue
            if legacy:
                warnings.append("%s: %s is a legacy manifest.json; accepted because it names git_commit (R2)"
                                % (where, rel))
            good.append((rel, data))
            grader = data.get("grader")
            if isinstance(grader, dict) and grader.get("grader_sha256"):
                want = frozen.get(r["direction"])
                if want is None:
                    warnings.append("%s: %s names grader %s but direction %s has no frozen_grader_sha256"
                                    % (where, rel, grader["grader_sha256"][:12], r["direction"]))
                elif grader["grader_sha256"] != want:
                    errors.append("%s: %s used grader %s, but the frozen grader of %s is %s (spec 6.3)"
                                  % (where, rel, grader["grader_sha256"][:12], r["direction"], want[:12]))
        if not good:
            errors.append("%s: %s needs a provenance file naming a 40-hex commit (spec 6.5)" % (where, r["status"]))
        if r["status"] == "replicated":
            seeds = set(d.get("seed") for _, d in good if d.get("seed") is not None)
            if len(seeds) < 2:
                errors.append("%s: replicated needs two provenance files with distinct seeds; found %d distinct "
                              "seed(s)" % (where, len(seeds)))
    if paper_text is not None:
        for fid in sorted(set(CITED.findall(paper_text))):
            if fid not in by_id:
                errors.append("paper cites %s, which is not in FINDINGS.md" % fid)
            elif by_id[fid]["status"] != "replicated":
                errors.append("paper cites %s, whose status is %s; paper claims need replicated (R17)"
                              % (fid, by_id[fid]["status"]))
    return errors, warnings


def cmd_findings_check(args):
    root = args.root or registry.default_root()
    path = args.findings or os.path.join(root, "FINDINGS.md")
    repo = args.repo or registry.repo_root(root)
    try:
        text = records.read_text(path)
    except (IOError, OSError) as exc:
        sys.stderr.write("research-session: cannot read %s: %s\n" % (path, exc))
        return 2
    try:
        directions = state.load_json(os.path.join(root, "directions.json"))
    except ValueError:
        directions = None
    paper = None
    if args.paper:
        try:
            paper = records.read_text(args.paper)
        except (IOError, OSError) as exc:
            sys.stderr.write("research-session: cannot read %s: %s\n" % (args.paper, exc))
            return 2
    errors, warnings = registry.validate_findings_text(text)
    e2, w2 = check(repo, text, directions, paper)
    errors += [e for e in e2 if e not in errors]
    for w in warnings + w2:
        print("warning: %s" % w)
    for e in errors:
        print("error: %s" % e)
    print("findings-check: %d error(s), %d warning(s)" % (len(errors), len(warnings + w2)))
    return 1 if errors else 0


def add_parsers(sub):
    p = sub.add_parser("findings-check", help="provenance, seed-replication and grader gates on FINDINGS.md "
                                              "(spec 6.3, 6.5; read-only)")
    p.add_argument("--paper", metavar="DRAFT", help="fail when the draft cites a row that is not replicated")
    p.add_argument("--root", help="research root (default: DC/docs/research)")
    p.add_argument("--findings", help="FINDINGS.md path (default: <root>/FINDINGS.md)")
    p.add_argument("--repo", help="checkout that evidence paths are relative to (default: two levels above root)")
    p.set_defaults(func=cmd_findings_check)
