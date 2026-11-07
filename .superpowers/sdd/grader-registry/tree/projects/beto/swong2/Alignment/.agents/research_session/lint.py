"""Glue lint and secret scan (spec section 5.5).

The glue lint catches prose whose words have been run together, which is how a long-running session's notes
became unreadable. It splits Markdown into units, splits each unit into tokens, and applies two fixed rules:

- long-token rule: in a unit of at least 8 tokens, fail when more than 15% of tokens have 20 or more characters;
- join rule: fail when more than 3 tokens join letters and digits (``word8`` or ``8word``), after the allowlist.

The thresholds are fixed by ruling R10. Only the allowlist may grow, and every addition is reported.

The secret scan looks for credential patterns anywhere in the raw text, including code blocks. Its output never
contains the matched text.

Public functions: ``lint_text`` (used by the PreToolUse hook on ``content`` and ``new_string``, ruling R30),
``lint_file``, ``scan_secrets``, ``split_units``, ``tokens``, ``glue_in_scope`` and ``secret_in_scope``.
"""

import os
import re
from collections import namedtuple

ALIGNMENT_ROOT = "/projects/beto/swong2/Alignment"

# Fixed thresholds (R10). Changing any of these needs a new ruling.
LONG_TOKEN_CHARS = 20
LONG_TOKEN_MIN_UNIT_TOKENS = 8
LONG_TOKEN_MAX_FRACTION = 0.15
JOIN_MAX = 3

JOIN_RE = re.compile(r"[A-Za-z]{3,}[0-9]|[0-9][A-Za-z]{3,}")

# Allowlist, matched against the whole token, case-insensitive. Allowlisted tokens are removed before both rules
# are counted. Spec 5.5 base list first; each later addition names the token that needed it (R10).
_FILE_EXTENSIONS = "md|json|jsonl|py|txt|csv|tsv|toml|yaml|yml|log|pt|sh|ipynb|html|pdf|tex|bib"
ALLOWLIST_PATTERNS = [
    r"sha1", r"sha256", r"sha512", r"eval5", r"int8", r"uint8", r"float16", r"float32", r"bfloat16",
    r"utf8", r"base64",
    r"python3(\.[0-9]+)*",                      # python3, python3.9, python3.12
    r"gpu[A-Za-z0-9]*x[0-9]+(-interactive)?",   # Slurm partitions: gpuA100x4, gpuA40x4, gpuH200x8
    # Ticket 01 addition: file names with a known extension, needed by lane1-public-patterns.md (proposal-full.md:3).
    r"[A-Za-z0-9_-]{1,48}(\.[A-Za-z0-9_-]{1,24})*\.(" + _FILE_EXTENSIONS + ")",
]
_ALLOW_RE = re.compile("|".join("(?:" + p + ")" for p in ALLOWLIST_PATTERNS), re.IGNORECASE)

# Ticket 01 addition: lower-case kebab-case identifiers with at least three parts of at most 12 characters, at least
# two of them purely alphabetic. Needed by claude-md-management and cc-plugin-you-should-know (lane2-harness.md:119).
# The alphabetic-part condition keeps glue such as locally2026-10-31 (MEMORY.md:27) counted.
_KEBAB_RE = re.compile(r"[a-z0-9]{1,12}(?:-[a-z0-9]{1,12}){2,}")

Finding = namedtuple("Finding", ["line", "rule", "excerpt"])

_FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}(\s|$)")
_LIST_RE = re.compile(r"^\s*(?:[-*+]|[0-9]+[.)])\s+")
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_INLINE_CODE_RE = re.compile(r"(`+)(?:(?!\1).)+?\1", re.S)
_LINK_TARGET_RE = re.compile(r"\]\([^)]*\)")
_REF_DEF_RE = re.compile(r"^\s*\[[^\]]+\]:\s*\S+", re.M)
_URL_RE = re.compile(r"(?:https?|ftp|file)://\S+|www\.\S+")
_EDGE_RE = re.compile(r"^[\W_]+|[\W_]+$", re.UNICODE)
_DROP_CHARS = ("/", "\\", "@", "=")


def split_units(text):
    """Return ``[(first_line_number, unit_text)]`` for the lintable units of a Markdown text.

    A unit is a maximal run of non-blank lines. Each list item, table row and heading is its own unit. Fenced code,
    HTML comments, YAML frontmatter and table separator rows are skipped.
    """
    lines = text.split("\n")
    units = []
    current = []
    start = 0

    def flush():
        if current:
            units.append((start, "\n".join(current)))
        del current[:]

    i = 0
    n = len(lines)
    # YAML frontmatter: only when the very first line is '---'.
    if n and lines[0].strip() == "---":
        j = 1
        while j < n and lines[j].strip() not in ("---", "..."):
            j += 1
        if j < n:
            i = j + 1
    fence = None
    in_comment = False
    while i < n:
        line = lines[i]
        lineno = i + 1
        i += 1
        if fence is not None:
            m = _FENCE_RE.match(line)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not line.strip()[len(m.group(1)):]:
                fence = None
            continue
        if in_comment:
            end = line.find("-->")
            if end < 0:
                continue
            in_comment = False
            line = line[end + 3:]
            if not line.strip():
                continue
        # Remove complete inline comments, then detect an opening comment that runs past this line.
        line = re.sub(r"<!--.*?-->", " ", line)
        k = line.find("<!--")
        if k >= 0:
            in_comment = True
            line = line[:k]
        m = _FENCE_RE.match(line)
        if m:
            flush()
            fence = m.group(1)
            continue
        if not line.strip():
            flush()
            continue
        if _TABLE_SEP_RE.match(line) and "-" in line:
            flush()
            continue
        stripped = line.strip()
        if _HEADING_RE.match(line) or stripped.startswith("|"):
            flush()
            units.append((lineno, line))
            continue
        if _LIST_RE.match(line) or not current:
            flush()
            start = lineno
        current.append(line)
    flush()
    return units


def tokens(unit):
    """Whitespace tokens of a unit after removing inline code, link targets and URLs.

    Tokens containing ``/``, ``\\``, ``@`` or ``=`` are dropped, and punctuation is stripped from both ends.
    """
    s = _INLINE_CODE_RE.sub(" ", unit)
    s = _LINK_TARGET_RE.sub("] ", s)
    s = _REF_DEF_RE.sub(" ", s)
    s = _URL_RE.sub(" ", s)
    out = []
    for raw in s.split():
        if any(c in raw for c in _DROP_CHARS):
            continue
        t = _EDGE_RE.sub("", raw)
        if t:
            out.append(t)
    return out


def is_allowlisted(token):
    if _ALLOW_RE.fullmatch(token) is not None:
        return True
    if _KEBAB_RE.fullmatch(token) is not None:
        return sum(1 for part in token.split("-") if part.isalpha()) >= 2
    return False


def join_tokens(toks):
    """Tokens that count toward the join rule."""
    return [t for t in toks if JOIN_RE.search(t) and not is_allowlisted(t)]


def check_unit(unit):
    """Return a list of ``(rule, detail)`` failures for one unit."""
    toks = [t for t in tokens(unit) if not is_allowlisted(t)]
    failures = []
    if len(toks) >= LONG_TOKEN_MIN_UNIT_TOKENS:
        long_count = sum(1 for t in toks if len(t) >= LONG_TOKEN_CHARS)
        if long_count > LONG_TOKEN_MAX_FRACTION * len(toks):
            failures.append(("long-token", "%d of %d tokens have %d+ characters" % (
                long_count, len(toks), LONG_TOKEN_CHARS)))
    joins = join_tokens(toks)
    if len(joins) > JOIN_MAX:
        failures.append(("join", "%d letter-digit joins" % len(joins)))
    return failures


def _excerpt(text, width=100):
    flat = " ".join(text.split())
    return flat if len(flat) <= width else flat[: width - 3] + "..."


def lint_glue(text):
    """Glue-lint a Markdown string. Returns a list of ``Finding``."""
    findings = []
    for lineno, unit in split_units(text):
        for rule, detail in check_unit(unit):
            findings.append(Finding(lineno, rule, "%s; %s" % (detail, _excerpt(unit))))
    return findings


# Secret patterns (spec 5.5). Bare prefixes from the spec (github_pat_, sk-ant-, sk-or-v1-, xox?-) require a token
# body after the prefix, so documentation that names the prefix does not fail. sk-proj- is an addition.
_B = r"(?<![A-Za-z0-9_])"
SECRET_PATTERNS = [
    ("github-token", re.compile(_B + r"gh[pousr]_[A-Za-z0-9]{36}")),
    ("github-pat", re.compile(_B + r"github_pat_[A-Za-z0-9_]{20,}")),
    ("anthropic-key", re.compile(_B + r"sk-ant-[A-Za-z0-9_-]{20,}")),
    ("openrouter-key", re.compile(_B + r"sk-or-v1-[A-Za-z0-9]{20,}")),
    ("openai-project-key", re.compile(_B + r"sk-proj-[A-Za-z0-9_-]{32,}")),
    ("sk-key", re.compile(r"(?<![A-Za-z0-9_-])sk-[A-Za-z0-9]{32,}")),
    ("aws-access-key", re.compile(_B + r"AKIA[0-9A-Z]{16}")),
    ("huggingface-token", re.compile(_B + r"hf_[A-Za-z0-9]{30,}")),
    ("slack-token", re.compile(_B + r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("private-key", re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----")),
]


def scan_secrets(text):
    """Return a ``Finding`` per secret match. The excerpt names the pattern and never contains the match."""
    findings = []
    seen = set()
    for kind, pattern in SECRET_PATTERNS:
        for m in pattern.finditer(text):
            lineno = text.count("\n", 0, m.start()) + 1
            key = (lineno, m.start())
            if key in seen:
                continue
            seen.add(key)
            findings.append(Finding(lineno, "secret", "%s match redacted" % kind))
    findings.sort(key=lambda f: f.line)
    return findings


def lint_text(text, glue=True, secrets=True):
    """Lint a text string, for example a Write ``content`` or an Edit ``new_string`` (R30)."""
    findings = []
    if secrets:
        findings.extend(scan_secrets(text))
    if glue:
        findings.extend(lint_glue(text))
    findings.sort(key=lambda f: (f.line, f.rule))
    return findings


def read_text(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8", errors="replace")


def lint_file(path, glue=True, secrets=True):
    return lint_text(read_text(path), glue=glue, secrets=secrets)


def format_finding(path, finding):
    return "%s:%d: %s: %s" % (path, finding.line, finding.rule, finding.excerpt)


GLUE_SCOPE_NAMES = frozenset(["WORKLOG.md", "RESUME.md", "START.md", "SESSIONS.md", "FINDINGS.md", "README.md"])


def glue_in_scope(path, alignment_root=ALIGNMENT_ROOT):
    """True for the files the hook glue-lints: named files under docs/research/ and memory Markdown."""
    p = os.path.abspath(path)
    name = os.path.basename(p)
    if name in GLUE_SCOPE_NAMES and "/docs/research/" in p:
        return True
    memory = os.path.join(os.path.abspath(alignment_root), ".agents", "memory") + os.sep
    return p.startswith(memory) and name.endswith(".md")


def secret_in_scope(path, alignment_root=ALIGNMENT_ROOT):
    """True for every file under the Alignment root."""
    root = os.path.abspath(alignment_root)
    p = os.path.abspath(path)
    return p == root or p.startswith(root + os.sep)
