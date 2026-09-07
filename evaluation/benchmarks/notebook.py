"""
notebook.py — lifting constants out of the Liars' Bench notebooks.

Liars' Bench publishes its *pressured* prompts to HuggingFace but keeps the
neutral control templates, the judge rubrics and the instruction sets in the
notebooks that generated the dataset. EVAL 5 needs those: belief has to be
elicited with the same control prompts LB used, and the pressured responses
have to be judged with the same rubrics, or the numbers are about a different
benchmark.

The obvious move is to copy them into this repo. This module does not, because
a copy is one upstream edit away from silently judging with a stale rubric, and
the drift is undetectable from the results. Instead the notebook JSON is parsed
and the named assignment is pulled out of the AST and `literal_eval`-ed.

Nothing is executed. `literal_eval` accepts only literals, so a notebook cell
cannot run code through this path however it is written — which matters,
because these are files from another repository.
"""

import ast
import json
import os

from . import sources


class NotebookConstantMissing(LookupError):
    pass


def _cell_sources(path):
    with open(path) as handle:
        notebook = json.load(handle)
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", "")
        yield source if isinstance(source, str) else "".join(source)


def _iter_assignments(source):
    """Every `name = <literal>` in a cell, including inside functions.

    Notebook cells are frequently unparseable on their own — an `await` at top
    level, a partially written line — so a cell that will not parse is skipped
    rather than fatal.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                yield target.id, node.value


def _fstring_to_format(node):
    """An f-string as a str.format template: `f"x {resp}"` -> `"x {resp}"`.

    Liars' Bench writes two of its judge rubrics as f-strings interpolating the
    response (`classify_knowledge_claim_response`). Rebuilding them as format
    templates keeps the prose verbatim while making the substitution ours; the
    placeholder is named after the interpolated expression, so a change to
    which variable is spliced in shows up as a KeyError rather than as a
    silently different prompt.
    """
    parts = []
    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            parts.append(value.value)
        elif isinstance(value, ast.FormattedValue):
            expression = value.value
            while isinstance(expression, ast.Call) and expression.args:
                expression = expression.args[0]      # unwrap str(...)
            if not isinstance(expression, ast.Name):
                raise ValueError("f-string interpolates a non-name")
            parts.append("{%s}" % expression.id)
        else:
            raise ValueError("unsupported f-string part")
    return "".join(parts)


def literal_from_notebook(path, name, contains=None):
    """The value assigned to `name` in `path`.

    `contains` disambiguates a common local name (Liars\' Bench assigns its
    convincing-game rubric to a bare `template`): only a value containing that
    substring is accepted, so picking up an unrelated assignment of the same
    name is a failure rather than a wrong prompt.
    """
    sources.require_file(path, "notebook %s" % os.path.basename(path))
    found = False
    for source in _cell_sources(path):
        for assigned, value in _iter_assignments(source):
            if assigned != name:
                continue
            found = True
            try:
                if isinstance(value, ast.JoinedStr):
                    result = _fstring_to_format(value)
                else:
                    result = ast.literal_eval(value)
            except ValueError:
                continue        # a computed assignment; keep looking
            if contains is not None and contains not in str(result):
                continue
            return result
    raise NotebookConstantMissing(
        "%s is %s in %s%s"
        % (name, "not a literal" if found else "not defined", path,
           "" if contains is None else " (matching %r)" % (contains,)))


def literals_from_notebook(path, names):
    return dict((name, literal_from_notebook(path, name)) for name in names)
