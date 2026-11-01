"""The B3 generation row schema and its loaders (plan B3 sections 1.3, 1.4 and 1.7; ticket T5).

The generation entrypoint (`scripts/b3_generate.py`, ticket T4) writes one JSON object per line, one line per
generated response. The judge (`scripts/b3_judge.py`) and premise (`scripts/b3_premise.py`) entrypoints read those
lines through `load_rows`, which validates every row with `validate_row`. T4 must conform to this docstring.

**Row fields.** Every row carries:

- `schema` (int): `SCHEMA`, currently 1.
- `row_id` (str): exactly `make_row_id(split, variant, query_id, condition, sample)`, which is
  "<split>:<variant>:<query_id>:<condition>:<sample>", for example "test:V-A:orb-0049:free:-1". Judge labels join to
  rows by this string.
- `split` (str): "calibration" (the 20 calibration queries) or "test" (the 100 test queries).
- `variant` (str): "V-A" or "V-B" (`spontaneous.af_prompts.VARIANTS`).
- `query_id` (str): the `id` in `data/b3/af_queries.json`, for example "orb-0049".
- `category` (str): that query's OR-Bench category.
- `condition` (str): "free" or "paid", the tier of the twin (`af_prompts.TIERS`).
- `sample` (int): 0 to 9 for the ten sampled rows of a (query, condition), `GREEDY` (-1) for the greedy row.
- `seed` (int): the torch seed set before this row's generation (any int on the greedy row).
- `query` (str): the bare user request, the OR-Bench prompt text, without the tier tag or any scaffold. The judge
  sees this field and `response` and nothing else.
- `response` (str): the decoded generated text, special tokens skipped, at most 512 new tokens.
- `n_generated` (int): the number of generated token ids.
- `first_token_id` (int or None): the first generated id; None only when nothing was generated.
- `first_token_text` (str or None): `tokenizer.decode([first_token_id])`, the key `proxy.calibrate_r1` uses.
- `opening_ids` (list of int): the first `OPENING_LEN` (8) generated ids, or all of them when fewer. The proxy row
  labels (`proxy.p1_label`, `proxy.p2_label`) read these; a continuation path is at most four ids long.
- `vocab_size` (int): the length of the model's output distribution.

**Readout fields, required on the greedy row.** The next-token distributions at the six frozen stems are
teacher-forced on the prompt alone, so they are the same for all eleven rows of a (query, condition). They are
required on the greedy row (`sample == -1`) and optional on sampled rows, where they must equal the greedy row's.

- `stems` (list of six dicts, in the order of `proxy.stem_id_paths(tokenizer)`): each is
  `{"path": [ids], "top": {"<id>": logp, ...}, "rest_logp": float}`. `path` is the stem's id path, `[]` for the
  prompt alone. `top` holds float log-probs (fp32 log-softmax) for at least the 256 most likely ids, plus every id
  either proxy can need at that stem: at `[]` the opener "I" and every id of the R1 in force (the seed list of
  `grader/proxy_tokens.json` for calibration rows, the frozen G2 list for test rows); at every stem, the next id of
  every refusal continuation that passes through it. `rest_logp` is the log of the probability mass of all ids not in `top` (-inf when none).

`dense_logprobs` expands one stem record to a full vector, spreading `rest_logp` uniformly over the unlisted ids.
`proxy.p1_margin` and `proxy.p2_margin` on those vectors are exact whenever every id they read is listed, and
`row_margins` raises KeyError instead of approximating when one is not. The premise verdict does not use margins:
agreement uses the row labels from `opening_ids`. Margins feed transfer (ticket T6) and diagnostics.

**Optional fields.** `margins` (`{"P1": float, "P2": float, "proxy_tokens_sha256": str}`), the margins T4 computed
with the token file in force at generation time (seed R1 for calibration rows, the frozen G2 file for test rows);
consumers recompute them with `row_margins`. `finish_reason` ("eos" or "length"), `prompt_len`, `elapsed_s`. Unknown
fields are allowed and ignored.

**Judge label records** (written by `scripts/b3_judge.py`, one per line) are the verdict records of
`spontaneous.judge.judge_rows` plus `row_id`, `stage`, `model` and `cost_usd` (OpenRouter's settled `usage.cost`,
None on a cache hit or an empty response). `load_labels` returns them keyed by `row_id`.
"""
from __future__ import annotations

import json
import math
from typing import Any, Dict, Iterable, List, Mapping

import numpy as np

SCHEMA = 1
SPLITS = ("calibration", "test")
VARIANTS = ("V-A", "V-B")
CONDITIONS = ("free", "paid")
GREEDY = -1
N_SAMPLES = 10
OPENING_LEN = 8
N_STEMS = 6

_STR_FIELDS = ("row_id", "split", "variant", "query_id", "category", "condition", "query", "response")
_INT_FIELDS = ("schema", "sample", "seed", "n_generated", "vocab_size")


def make_row_id(split: str, variant: str, query_id: str, condition: str, sample: int) -> str:
    """The join key of a row: "<split>:<variant>:<query_id>:<condition>:<sample>"."""
    return "%s:%s:%s:%s:%d" % (split, variant, query_id, condition, int(sample))


def _is_int(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def _fail(row, msg):
    raise ValueError("row %s: %s" % (row.get("row_id", "?") if isinstance(row, Mapping) else "?", msg))


def _check_stems(row):
    stems = row.get("stems")
    if not isinstance(stems, list) or len(stems) != N_STEMS:
        _fail(row, "stems must be a list of %d stem records" % N_STEMS)
    for s in stems:
        if not isinstance(s, Mapping) or not {"path", "top", "rest_logp"} <= set(s):
            _fail(row, "each of the stems needs path, top and rest_logp")
        if not isinstance(s["path"], list) or not all(_is_int(i) for i in s["path"]):
            _fail(row, "stems path must be a list of ints")
        if not isinstance(s["top"], Mapping):
            _fail(row, "stems top must be a mapping of id to log-prob")
        if not isinstance(s["rest_logp"], (int, float)):
            _fail(row, "stems rest_logp must be a number")


def validate_row(row: Mapping[str, Any]) -> Mapping[str, Any]:
    """Check one row against the schema above; returns it unchanged, raises ValueError naming the field."""
    if not isinstance(row, Mapping):
        raise ValueError("a row must be a JSON object")
    for f in _STR_FIELDS:
        if f not in row:
            _fail(row, "missing field %s" % f)
        if not isinstance(row[f], str):
            _fail(row, "field %s must be a string" % f)
    for f in _INT_FIELDS:
        if f not in row:
            _fail(row, "missing field %s" % f)
        if not _is_int(row[f]):
            _fail(row, "field %s must be an int" % f)
    for f in ("first_token_id", "first_token_text", "opening_ids"):
        if f not in row:
            _fail(row, "missing field %s" % f)
    if row["schema"] != SCHEMA:
        _fail(row, "schema %r is not %d" % (row["schema"], SCHEMA))
    if row["split"] not in SPLITS:
        _fail(row, "split %r is not one of %s" % (row["split"], SPLITS))
    if row["variant"] not in VARIANTS:
        _fail(row, "variant %r is not one of %s" % (row["variant"], VARIANTS))
    if row["condition"] not in CONDITIONS:
        _fail(row, "condition %r is not one of %s" % (row["condition"], CONDITIONS))
    if not (row["sample"] == GREEDY or 0 <= row["sample"] < N_SAMPLES):
        _fail(row, "sample %r is not -1 (greedy) or 0 to %d" % (row["sample"], N_SAMPLES - 1))
    want = make_row_id(row["split"], row["variant"], row["query_id"], row["condition"], row["sample"])
    if row["row_id"] != want:
        _fail(row, "row_id should be %r" % want)
    ids = row["opening_ids"]
    if not isinstance(ids, list) or not all(_is_int(i) for i in ids) or len(ids) > OPENING_LEN:
        _fail(row, "opening_ids must be a list of at most %d ints" % OPENING_LEN)
    first = row["first_token_id"]
    if first is None:
        if ids or row["first_token_text"] is not None:
            _fail(row, "first_token_id is None but opening_ids or first_token_text is set")
    else:
        if not _is_int(first) or not ids or ids[0] != first:
            _fail(row, "first_token_id must be an int equal to opening_ids[0]")
        if not isinstance(row["first_token_text"], str):
            _fail(row, "first_token_text must be a string when a token was generated")
    if row["sample"] == GREEDY or "stems" in row:
        _check_stems(row)
    return row


def _read_jsonl(path) -> List[Dict[str, Any]]:
    out = []
    with open(path, encoding="utf-8") as handle:
        for n, line in enumerate(handle, 1):
            if line.strip():
                try:
                    out.append(json.loads(line))
                except ValueError as exc:
                    raise ValueError("%s line %d is not JSON: %s" % (path, n, exc)) from exc
    return out


def load_rows(paths: Iterable[str]) -> List[Dict[str, Any]]:
    """All rows of the given JSONL files, validated, in file order; a repeated row_id raises."""
    rows, seen = [], set()
    for path in paths:
        for row in _read_jsonl(path):
            validate_row(row)
            if row["row_id"] in seen:
                raise ValueError("duplicate row_id %r" % row["row_id"])
            seen.add(row["row_id"])
            rows.append(row)
    return rows


def load_labels(paths: Iterable[str]) -> Dict[str, Dict[str, Any]]:
    """{row_id: label record} from judge label files; a repeated row_id raises."""
    out: Dict[str, Dict[str, Any]] = {}
    for path in paths:
        for rec in _read_jsonl(path):
            for f in ("row_id", "status", "scored"):
                if f not in rec:
                    raise ValueError("%s: a label record lacks %s" % (path, f))
            if rec["row_id"] in out:
                raise ValueError("duplicate row_id %r in labels" % rec["row_id"])
            out[rec["row_id"]] = rec
    return out


# ---- readout --------------------------------------------------------------------------------------------------

def dense_logprobs(stem: Mapping[str, Any], vocab_size: int) -> np.ndarray:
    """A full log-prob vector from one stem record; `rest_logp` is spread uniformly over the unlisted ids."""
    top = {int(k): float(v) for k, v in stem["top"].items()}
    if top and (min(top) < 0 or max(top) >= vocab_size):
        raise ValueError("stem ids fall outside a vocab of %d" % vocab_size)
    n_rest = vocab_size - len(top)
    rest = float(stem["rest_logp"])
    fill = -math.inf if (n_rest == 0 or rest == -math.inf) else rest - math.log(n_rest)
    out = np.full(vocab_size, fill, dtype=np.float64)
    for i, v in top.items():
        out[i] = v
    return out


def _needed_ids(res) -> Dict[tuple, set]:
    """{stem path: ids the proxies read at it}."""
    from spontaneous import proxy as px
    need = {p: set() for p in res.stem_paths}
    need[()] |= set(res.r1_ids) | {res.opener_id}
    for q in px._counted_paths(res):
        for i in range(len(q)):
            need[q[:i]].add(q[i])
    return need


def stem_logprobs(row: Mapping[str, Any], res) -> Dict[tuple, np.ndarray]:
    """{stem id path: dense log-prob vector} for `proxy.p2_margin`; KeyError when a needed id is not stored."""
    by_path = {tuple(s["path"]): s for s in row["stems"]}
    out = {}
    for path, ids in _needed_ids(res).items():
        if path not in by_path:
            raise KeyError("stem %s not stored in row %s" % (list(path), row["row_id"]))
        stored = {int(k) for k in by_path[path]["top"]}
        missing = sorted(ids - stored)
        if missing:
            raise KeyError("ids %s not stored at stem %s of row %s" % (missing, list(path), row["row_id"]))
        out[path] = dense_logprobs(by_path[path], row["vocab_size"])
    return out


def row_margins(row: Mapping[str, Any], res) -> Dict[str, float]:
    """{"P1": m, "P2": m} for a row that carries `stems`, from the frozen `proxy` functions."""
    from spontaneous import proxy as px
    dists = stem_logprobs(row, res)
    return {"P1": px.p1_margin(dists[()], res.r1_ids), "P2": px.p2_margin(dists, res)}
