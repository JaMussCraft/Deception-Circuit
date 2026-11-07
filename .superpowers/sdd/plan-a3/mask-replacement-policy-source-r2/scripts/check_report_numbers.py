#!/usr/bin/env python3
"""
scripts/check_report_numbers.py — does every number in a report trace to a file?

    python scripts/check_report_numbers.py REPORT.md [--strict] [--json] [--root DIR ...]

Spec §6.2 (docs/research/autoresearch-workflow/spec.md). The checker lists
every number in the report's prose and tables and classifies it:

resolved    its unit cites an existing file and the number occurs in that file.
derived     its unit contains the word "derived".
unresolved  neither.

Units follow the lint's definition (spec §5.5): a maximal run of non-blank
lines, except that every heading, list item and table row is its own unit. A
table row also uses the citations of the paragraph just before its table (the
table's heading paragraph) and of the table's header row.

A citation is a file path with a known data or text extension, in backticks,
in a link target, or bare. Relative paths are tried against the report's
directory, the repository root (the nearest parent holding `.git`) and every
`--root`, in that order.

A number occurs in a cited file when:

* JSON (`.json`, `.jsonl`) or CSV (`.csv`, `.tsv`): some numeric leaf or cell
  lies within half a unit of the number's last displayed digit, inclusive. So
  0.83 matches 0.835 and 1,000 matches 1000.4. A percentage also matches its
  fraction (61.1% matches 0.6105). A string leaf or cell that is wholly a
  number counts as numeric.
* any other text file: the displayed digits occur literally.

Not numbers (counted under "skipped" by category): numbers inside code (inline
or fenced), dates, times, section numbers and numbered labels (Table 3, phase
2), ruling numbers (R16), ticket numbers, finding ids (F3), component ids such
as L17H24 or mlp.11, versions, `file:line` references, paths and URLs,
markdown list markers, and other identifiers that glue letters to digits.

Exit status: 0, or 1 with `--strict` when any number is unresolved. Standard
library only, so it runs on Python 3.9 and 3.12 and under `python -I`.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import json
import os
import re
import sys
from decimal import Decimal, InvalidOperation

MAX_FILE_BYTES = 200 * 1024 * 1024

JSON_SUFFIXES = (".json", ".jsonl")
CSV_SUFFIXES = (".csv", ".tsv")
CITE_EXTENSIONS = ("json", "jsonl", "csv", "tsv", "md", "txt", "log", "yaml", "yml",
                   "py", "out", "err", "batch", "sbatch", "sh", "toml", "tex")

MONTH = (r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|"
         r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)")
LIST_SEP = r"(?:\s*(?:,|and|or|to|-|–|—)\s*)"

PATH_RE = re.compile(
    r"(?<![\w/.~-])((?:~/|\.{1,2}/|/)?(?:[\w.@+-]+/)*[\w.@+-]*[\w@+-]\.(?:%s))"
    r"(?::(\d+)(?:-(\d+))?)?(?![\w/])" % "|".join(CITE_EXTENSIONS))
INLINE_CODE_RE = re.compile(r"(`+)(.+?)\1", re.S)
LINK_TARGET_RE = re.compile(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
URL_RE = re.compile(r"https?://\S+|www\.\S+")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s")
LIST_ITEM_RE = re.compile(r"^(\s*)(?:[-*+]|\d+[.)])\s+")
TABLE_ROW_RE = re.compile(r"^\s*\|")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
DERIVED_RE = re.compile(r"\bderived\b", re.I)

#: The number pattern: optional sign (only when not glued to a word), digits
#: with optional thousands commas and decimals, optional exponent, optional
#: percent or multiplier suffix. Never glued to letters or to further digits.
NUM_RE = re.compile(
    r"(?<![\w.,])(?P<sign>[-+−]?)(?P<body>(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)"
    r"(?P<exp>[eE][-+]?\d+)?(?P<suffix>\s?%|x\b|×)?(?![\w]|[.,]\d)")

#: Skipped categories, applied in this order. Each pattern's match is masked
#: and every digit run inside it counts once under its category.
SKIP_PATTERNS = [
    ("date", re.compile(r"\b\d{4}-\d{2}-\d{2}(?:[T ]\d{1,2}:\d{2}(?::\d{2})?"
                        r"(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)?\b")),
    ("date", re.compile(r"\b\d{1,2}(?:st|nd|rd|th)?\s+%s\.?(?:,?\s+\d{4})?\b" % MONTH)),
    ("date", re.compile(r"\b%s\.?\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?\b" % MONTH)),
    ("date", re.compile(r"\b%s\.?\s+\d{4}\b" % MONTH)),
    ("date", re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b")),
    ("time", re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?(?:\s?[ap]\.?m\.?(?![a-z]))?", re.I)),
    ("time", re.compile(r"\b\d{1,2}\s?[ap]\.?m\.?(?![a-z])", re.I)),
    ("version", re.compile(r"\b\d+\.\d+\.\d+(?:\.\d+)*\b")),
    ("version", re.compile(r"(?i)\b(?:python|pytorch|torch|transformers|nnsight|numpy|"
                           r"pytest|cuda|version|release)\s+v?\d+(?:\.\d+)+\b")),
    ("version", re.compile(r"\b(?:Sonnet|Opus|Haiku|Fable|Mythos|Claude|Gemini|GPT|Llama|"
                           r"Gemma|Qwen|Mistral|Astra|Sol)[ -]\d+(?:\.\d+)*\b")),
    ("version", re.compile(r"\bv\d+(?:\.\d+)*\b")),
    ("section", re.compile(r"§+\s*\d+(?:\.\d+)*[a-z]?(?:%s§?\s*\d+(?:\.\d+)*[a-z]?)*" % LIST_SEP)),
    ("section", re.compile(r"(?i)\b(?:sections?|sec\.|chapters?|appendix|appendices|"
                           r"spec)\s+\d+(?:\.\d+)*[a-z]?(?:%s\d+(?:\.\d+)*[a-z]?)*" % LIST_SEP)),
    ("label", re.compile(r"(?i)\b(?:tables?|figures?|figs?\.|steps?|phases?|waves?|stages?|"
                         r"eval|evals|parts?|rounds?|options?)\s+\d+(?:\.\d+)*[a-z]?"
                         r"(?:%s\d+(?:\.\d+)*[a-z]?)*\b" % LIST_SEP)),
    ("ruling", re.compile(r"\bR\d+[a-z]?(?:\(\w+\))*")),
    ("ruling", re.compile(r"(?i)\brulings?\s+\d+(?:%s\d+)*" % LIST_SEP)),
    ("ticket", re.compile(r"(?i)\b(?:tickets?|issues?|PR)\s+#?\d+(?:%s#?\d+)*" % LIST_SEP)),
    ("ticket", re.compile(r"(?<![\w&])#\d+\b")),
    ("finding_id", re.compile(r"\bF-[\w-]*\d+\b|\bF\d+\b")),
    ("component_id", re.compile(r"\b(?:L\d+H\d+|L\d+|H\d+|(?:mlp|MLP|attn|head|layer)[._]?\d+)\b")),
    ("identifier", re.compile(r"\b(?!\d+(?:\.\d+)?x\b)(?!\d+[eE][-+]?\d)"
                              r"(?=\w*[A-Za-z])(?=\w*\d)\w+\b")),
]


# ==============================================================================
# UNITS
# ==============================================================================

class Unit:
    __slots__ = ("kind", "line", "text", "table_context")

    def __init__(self, kind, line, text):
        self.kind = kind            # heading | item | row | para
        self.line = line            # 1-based line of the first text line
        self.text = text
        self.table_context = ""     # for rows: heading paragraph + header row


def split_units(text: str) -> tuple:
    """-> (units, skipped code digit count). Fenced code, HTML comments and
    YAML frontmatter are dropped; their digits are counted as code."""
    lines = text.split("\n")
    units, code_digits = [], 0
    i, n = 0, len(lines)
    if n and lines[0].strip() == "---":
        for j in range(1, n):
            if lines[j].strip() in ("---", "..."):
                i = j + 1
                break
    current = None
    table_heading = None
    in_table = False
    last_non_row = None

    def close():
        nonlocal current
        if current is not None:
            units.append(current)
            current = None

    while i < n:
        line = lines[i]
        fence = FENCE_RE.match(line)
        if fence:
            close()
            marker = fence.group(1)
            i += 1
            while i < n and not lines[i].lstrip().startswith(marker[0] * len(marker)):
                code_digits += len(re.findall(r"\d+", lines[i]))
                i += 1
            i += 1
            in_table = False
            continue
        if line.lstrip().startswith("<!--"):
            close()
            while i < n and "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        if not line.strip():
            close()
            in_table = False
            i += 1
            continue
        if TABLE_ROW_RE.match(line):
            close()
            if TABLE_SEP_RE.match(line):
                i += 1
                continue
            row = Unit("row", i + 1, line)
            if not in_table:
                in_table = True
                table_heading = (last_non_row.text if last_non_row is not None else "") + "\n" + line
            row.table_context = table_heading
            units.append(row)
            i += 1
            continue
        in_table = False
        if HEADING_RE.match(line):
            close()
            units.append(Unit("heading", i + 1, line))
            last_non_row = units[-1]
            i += 1
            continue
        if LIST_ITEM_RE.match(line):
            close()
            current = Unit("item", i + 1, line)
            last_non_row = current
            i += 1
            continue
        if current is None:
            current = Unit("para", i + 1, line)
            last_non_row = current
        else:
            current.text += "\n" + line
        i += 1
    close()
    return units, code_digits


# ==============================================================================
# CITATIONS
# ==============================================================================

def find_repo_root(start: str):
    path = os.path.abspath(start)
    while True:
        if os.path.exists(os.path.join(path, ".git")):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            return None
        path = parent


def cited_paths(text: str) -> list:
    """Path strings cited in `text`, in order of appearance, deduplicated."""
    out = []
    candidates = [m.group(2) for m in INLINE_CODE_RE.finditer(text)]
    candidates += [m.group(1) for m in LINK_TARGET_RE.finditer(text)]
    candidates.append(text)
    for chunk in candidates:
        for m in PATH_RE.finditer(chunk):
            if m.group(1) not in out:
                out.append(m.group(1))
    return out


class Resolver:
    """Finds cited files and answers whether a number occurs in them."""

    def __init__(self, report_path: str, roots=()):
        report_dir = os.path.dirname(os.path.abspath(report_path))
        self.roots = [report_dir]
        repo = find_repo_root(report_dir)
        if repo and repo not in self.roots:
            self.roots.append(repo)
        for root in roots:
            root = os.path.abspath(os.path.expanduser(root))
            if root not in self.roots:
                self.roots.append(root)
        self._cache = {}

    def locate(self, cited: str):
        cited = os.path.expanduser(cited)
        if os.path.isabs(cited):
            return cited if os.path.isfile(cited) else None
        for root in self.roots:
            path = os.path.normpath(os.path.join(root, cited))
            if os.path.isfile(path):
                return path
        return None

    def content(self, path: str):
        """-> ("numeric", sorted floats, decimals) or ("text", str) or None."""
        if path in self._cache:
            return self._cache[path]
        result = None
        try:
            if os.path.getsize(path) <= MAX_FILE_BYTES:
                lower = path.lower()
                if lower.endswith(JSON_SUFFIXES):
                    result = _numeric(_json_leaves(path))
                elif lower.endswith(CSV_SUFFIXES):
                    result = _numeric(_csv_cells(path))
                else:
                    with open(path, encoding="utf-8", errors="replace") as f:
                        result = ("text", f.read())
        except (OSError, ValueError):
            result = None
        self._cache[path] = result
        return result


def _as_number(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return Decimal(repr(value)) if isinstance(value, float) else Decimal(value)
        except InvalidOperation:
            return None
    if isinstance(value, str):
        s = value.strip().replace(",", "").rstrip("%").strip()
        if not s or not re.fullmatch(r"[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?", s):
            return None
        try:
            return Decimal(s)
        except InvalidOperation:
            return None
    return None


def _walk(value, out):
    if isinstance(value, dict):
        for v in value.values():
            _walk(v, out)
    elif isinstance(value, list):
        for v in value:
            _walk(v, out)
    else:
        number = _as_number(value)
        if number is not None and number.is_finite():
            out.append(number)


def _json_leaves(path):
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        if path.lower().endswith(".jsonl"):
            for line in f:
                if line.strip():
                    try:
                        _walk(json.loads(line), out)
                    except ValueError:
                        continue
        else:
            _walk(json.load(f), out)
    return out


def _csv_cells(path):
    out = []
    delimiter = "\t" if path.lower().endswith(".tsv") else ","
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.reader(f, delimiter=delimiter):
            for cell in row:
                number = _as_number(cell)
                if number is not None and number.is_finite():
                    out.append(number)
    return out


def _numeric(decimals):
    decimals = sorted(set(decimals))
    return ("numeric", [float(d) for d in decimals], decimals)


# ==============================================================================
# NUMBERS
# ==============================================================================

class Number:
    __slots__ = ("line", "text", "value", "half", "percent", "digits", "status", "file")

    def __init__(self, line, text, value, half, percent, digits):
        self.line = line
        self.text = text
        self.value = value          # Decimal as displayed (sign applied)
        self.half = half            # half a unit of the last displayed digit
        self.percent = percent
        self.digits = digits        # the displayed digits, for literal search
        self.status = "unresolved"
        self.file = None

    def targets(self):
        """(value, half) pairs a numeric leaf may match."""
        out = [(self.value, self.half)]
        if self.percent:
            out.append((self.value / 100, self.half / 100))
        return out

    def as_dict(self):
        return {"line": self.line, "text": self.text, "status": self.status,
                "file": self.file}


def _mask(text: str, start: int, end: int) -> str:
    return text[:start] + re.sub(r"[^\n]", " ", text[start:end]) + text[end:]


def _mask_all(text, pattern, group=0):
    spans = [(m.start(group), m.end(group)) for m in pattern.finditer(text)]
    digits = 0
    for start, end in spans:
        digits += len(re.findall(r"\d+", text[start:end]))
        text = _mask(text, start, end)
    return text, digits


def _mask_tokens_with_slash(text):
    """Mask whitespace-delimited tokens that look like paths (a slash and a letter)."""
    digits = 0
    for m in list(re.finditer(r"\S+", text)):
        token = m.group(0)
        if "/" in token and re.search(r"[A-Za-z_]", token):
            digits += len(re.findall(r"\d+", token))
            text = _mask(text, m.start(), m.end())
    return text, digits


def extract_numbers(unit: Unit, skipped: dict) -> list:
    """Numbers in one unit, after masking code, links, paths and skip patterns."""
    text = unit.text

    def bump(category, count):
        if count:
            skipped[category] = skipped.get(category, 0) + count

    text, count = _mask_all(text, INLINE_CODE_RE)
    bump("code", count)
    text, count = _mask_all(text, LINK_TARGET_RE)
    bump("path", count)
    text, count = _mask_all(text, URL_RE)
    bump("path", count)
    # file:line references, then other cited paths.
    spans = [(m.start(), m.end(), bool(m.group(2))) for m in PATH_RE.finditer(text)]
    for start, end, has_line in spans:
        bump("file_line" if has_line else "path", len(re.findall(r"\d+", text[start:end])))
        text = _mask(text, start, end)
    text, count = _mask_tokens_with_slash(text)
    bump("path", count)

    if unit.kind == "heading":
        m = re.match(r"^(\s{0,3}#{1,6}\s+)(\d+(?:\.\d+)*\.?)(?=\s)", text)
        if m:
            bump("section", len(re.findall(r"\d+", m.group(2))))
            text = _mask(text, m.start(2), m.end(2))
    if unit.kind == "item":
        m = re.match(r"^\s*(\d+[.)])\s", text)
        if m:
            bump("list_marker", 1)
            text = _mask(text, m.start(1), m.end(1))

    for category, pattern in SKIP_PATTERNS:
        text, count = _mask_all(text, pattern)
        bump(category, count)

    numbers = []
    for m in NUM_RE.finditer(text):
        if m.group("sign") and m.start() > 0 and re.match(r"\w", unit.text[m.start() - 1]):
            # A hyphen glued to a masked identifier, as in the head range
            # L17H24-27: part of the identifier, not a negative number.
            bump("component_id" if re.search(r"\b(?:L\d+H\d+|L\d+|H\d+)$",
                                             unit.text[:m.start()]) else "identifier", 1)
            continue
        body = m.group("body").replace(",", "")
        sign = "-" if m.group("sign") in ("-", "−") else ""
        exp = m.group("exp") or ""
        try:
            value = Decimal(sign + body + exp)
        except InvalidOperation:
            continue
        unit_exp = value.as_tuple().exponent
        half = Decimal(5).scaleb(unit_exp - 1)
        suffix = (m.group("suffix") or "").strip()
        line = unit.line + unit.text.count("\n", 0, m.start())
        numbers.append(Number(line, m.group(0).strip(), value, half, suffix == "%",
                              m.group("body")))
    return numbers


def _numeric_match(content, number) -> bool:
    _, floats, decimals = content
    for value, half in number.targets():
        lo = bisect.bisect_left(floats, float(value - half) - 1e-12)
        hi = bisect.bisect_right(floats, float(value + half) + 1e-12)
        for d in decimals[lo:hi]:
            if abs(d - value) <= half:
                return True
    return False


def _text_match(content, number) -> bool:
    text = content[1]
    for digits in {number.digits, number.digits.replace(",", "")}:
        if re.search(r"(?<![\d.])%s(?!\d)" % re.escape(digits), text):
            return True
    return False


def occurs(content, number) -> bool:
    if content is None:
        return False
    if content[0] == "numeric":
        return _numeric_match(content, number)
    return _text_match(content, number)


# ==============================================================================
# CHECK
# ==============================================================================

def check(report_path: str, roots=()) -> dict:
    with open(report_path, encoding="utf-8") as f:
        text = f.read()
    resolver = Resolver(report_path, roots)
    units, code_digits = split_units(text)
    skipped = {"code": code_digits} if code_digits else {}
    numbers, missing = [], set()
    for unit in units:
        found = extract_numbers(unit, skipped)
        if not found:
            continue
        if DERIVED_RE.search(unit.text):
            for number in found:
                number.status = "derived"
            numbers.extend(found)
            continue
        cited = cited_paths(unit.text)
        if unit.kind == "row":
            cited += [p for p in cited_paths(unit.table_context) if p not in cited]
        files = []
        for path in cited:
            located = resolver.locate(path)
            if located:
                files.append((path, located))
            else:
                missing.add(path)
        for number in found:
            for shown, located in files:
                if occurs(resolver.content(located), number):
                    number.status = "resolved"
                    number.file = shown
                    break
        numbers.extend(found)
    counts = {"numbers": len(numbers),
              "resolved": sum(n.status == "resolved" for n in numbers),
              "derived": sum(n.status == "derived" for n in numbers),
              "unresolved": sum(n.status == "unresolved" for n in numbers)}
    return {"report": os.path.abspath(report_path), "roots": resolver.roots,
            "counts": counts, "skipped": dict(sorted(skipped.items())),
            "missing_citations": sorted(missing),
            "numbers": [n.as_dict() for n in numbers]}


def format_text(result: dict) -> str:
    name = os.path.basename(result["report"])
    lines = []
    for item in result["numbers"]:
        where = "  (%s)" % item["file"] if item["file"] else ""
        lines.append("%s:%d: %s %s%s" % (name, item["line"], item["status"],
                                         item["text"], where))
    c = result["counts"]
    lines.append("")
    lines.append("numbers %d, resolved %d, derived %d, unresolved %d"
                 % (c["numbers"], c["resolved"], c["derived"], c["unresolved"]))
    if result["skipped"]:
        lines.append("skipped: " + ", ".join("%s %d" % kv for kv in result["skipped"].items()))
    if result["missing_citations"]:
        lines.append("cited but not found: " + ", ".join(result["missing_citations"]))
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="List every number in a Markdown report and whether a cited file holds it.")
    parser.add_argument("report", help="The Markdown report to check.")
    parser.add_argument("--strict", action="store_true",
                        help="Exit 1 when any number is unresolved.")
    parser.add_argument("--json", action="store_true", help="Print the result as JSON.")
    parser.add_argument("--root", action="append", default=[],
                        help="Extra directory to resolve relative citations against "
                             "(repeatable).")
    args = parser.parse_args(argv)
    if not os.path.isfile(args.report):
        parser.error("no such report: %s" % args.report)
    result = check(args.report, args.root)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_text(result))
    if args.strict and result["counts"]["unresolved"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
