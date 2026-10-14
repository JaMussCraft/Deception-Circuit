"""Clause surgery: delete or replace the Pressure Clause inside a stored prompt.

The `nopressure` dataset builder and the eval-time prompt variants
(`evaluation/variants.py`) both derive their prompts from the STORED
`clean_prompt` / `corrupt_prompt` strings, never by re-templating through
`dc.SPECS`. The stored FAR and SDR datasets were built from wording the current
specs no longer carry (FAR's `ready`/`delayed`, SDR's `damaging`/`harmless`
suffix), so a rebuilt prompt is a different prompt; editing the stored string is
the only derivation that leaves everything outside the clause untouched.

The Pressure Clause sits in the system turn after the designating sentence,
joined by a single space (`_join` in `dataset/deception_common.py`). Removing it
therefore removes that one leading space too, so no space is stranded before
`<|eot_id|>`. Both helpers are tokenizer-free and refuse anything ambiguous: an
empty clause, a clause that is absent, a clause that occurs more than once, or a
clause with no leading space. Callers re-run `assert_aligned_pair` on the result.
"""

from __future__ import annotations


def _locate(prompt: str, clause: str) -> int:
    """Index of the clause's leading space. Raises unless the clause is
    non-empty, occurs exactly once and is preceded by a space."""
    if not clause:
        raise ValueError("refusing clause surgery with an empty clause: there is "
                         "nothing to remove (is this already a no-pressure "
                         "record?)")
    n = prompt.count(clause)
    if n != 1:
        raise ValueError(f"the clause occurs {n} times in the prompt, need "
                         f"exactly 1.\nclause: {clause!r}\nprompt: {prompt!r}")
    start = prompt.index(clause)
    if start == 0 or prompt[start - 1] != " ":
        raise ValueError(f"the clause has no single leading space to remove "
                         f"with it.\nclause: {clause!r}\nprompt: {prompt!r}")
    return start - 1


def remove_clause(prompt: str, clause: str) -> str:
    """The prompt with `clause` and its single leading space deleted."""
    at = _locate(prompt, clause)
    return prompt[:at] + prompt[at + 1 + len(clause):]


def replace_clause(prompt: str, clause: str, replacement: str) -> str:
    """The prompt with `clause` replaced in place by `replacement` (the leading
    space is kept, so the replacement reads as the next sentence)."""
    if not replacement:
        raise ValueError("an empty replacement would strand the clause's leading "
                         "space; use remove_clause instead")
    at = _locate(prompt, clause) + 1
    return prompt[:at] + replacement + prompt[at + len(clause):]
