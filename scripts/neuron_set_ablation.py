#!/usr/bin/env python
"""
scripts/neuron_set_ablation.py — set ablation of MLP hidden neurons, three references.

neuron-partition, item 10 "Ablation" of `docs/research/neuron-partition/spec.md`.
A neuron is `("mlp_hidden", layer, index)`: column `index` of the `down_proj`
input after the SwiGLU gate (14,336 per layer on Llama-3.1-8B). A neuron set is
a named list of such keys; `--sets` maps names to sets, including the matched
random null sets. Every set is ablated jointly, in one forward, under each of
three references:

  * **twin** (the primary): neutral-twin interchange. In each D row the set's
    activations are replaced, at every position, by their values in the same
    instance's H twin; in each I row by the user-neutral twin's. The twin is
    token-aligned with its row (same length, same mask, same Readout, identical
    tokens outside the clause or request span), so position p is written with
    the twin's position p. Rows without a twin are dropped and listed.
    `--twin-reverse` (default on) also runs the reverse patch, H with D's
    values and user-neutral with I's, which is the only twin-reference reading
    of N2's "ablate under H" and is descriptive. F and IOI have no twin, so
    their twin-reference collateral is null (not zero).
  * **mean**: the per-neuron mean over every unpadded position of the
    no-pressure condition F, clean and corrupt prompts pooled
    (`knockout.collect_mean_bank`), written at every position.
  * **zero**: zeros at every position.

The item-swap corrupt prompt is never a reference here (START item 5: the
clause stays in both streams, so it is a near no-op by construction).

**Readout and orientation.** One token at the Readout, logits through the fp32
final norm and unembedding (`hooks.readout_logits`). Every margin is stored in
**D orientation**, m = logit(opposite answer) - logit(honest answer), which is
the row's own target-minus-distractor on D and I and its negative on H, F and
user-neutral (their target is the honest item; checked per id). Both prompt
streams are scored (`--streams clean,corrupt`): the corrupt stream is the
item-swapped designation, whose answer words are reversed, and the two streams
are averaged within an id before ids are averaged, as the specificity ladder
does.

**Effect measures** (both are written; `spec.md` needs a ruling on which one
decides, reader brief section 7 blocker 1):

  * rate: p(opposite at margin) = share with m >= `--readout-margin` (0.7, the
    `contingency.MARGIN` rule's `>=`). The D effect is p(D) - p(H twin) and the
    I effect p(I) - p(user-neutral twin). Ablated, the twin reference compares
    D-ablated with the (unpatched) twin; mean and zero compare D-ablated with
    H-ablated, and also report D-ablated against H intact.
  * ladder margin ratio: G = mean over ids of (m_D - m_twin), intact, and the
    fraction removed is mean(m_D intact - m_D ablated) / G, refused when G is
    not above epsilon = max(1e-6, 10 x the self-replay error).

Collateral is full-vocabulary argmax accuracy on the condition-correct answer
(honest under H, F, user-neutral; the name under IOI), intact and ablated, in
points; the two-way accuracy (target beats distractor) is written beside it.

Outputs, under `--output-dir`: `summary.json` (every number above per set and
reference, the definitions, the conditions' row counts, the mean bank's source,
self-replay errors, measured seconds per forward), `rows.jsonl` (one line per
reference, set, condition and instance id, both streams) and `run_manifest.json`
(`run_manifest.py`: commit, argv, dataset files with sha256).

`--dry-run` loads no model. It builds every condition's batches with the
tokenizer when one loads (checking the pairings), else counts rows from the
dataset files, and prints the forward count and a runtime estimate.

No nnsight at module scope, so `--dry-run` runs in the login node's base env.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Dict, List, Optional, Sequence

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from component_analysis import knockout as ko                      # noqa: E402

CONDITIONS = ("D", "H", "F", "I", "N")
#: Conditions whose own Target is the opposite (deceptive or inverted) answer.
OPPOSITE_TARGET = {"D": True, "I": True, "H": False, "F": False, "N": False}
#: Which condition is whose twin.
TWIN_OF = {"D": "H", "I": "N"}
#: Under the twin reference, the twin patched with its opposite row's values.
REVERSE_SOURCE = {"H": "D", "N": "I"}
REFERENCES = ("twin", "mean", "zero")
STREAMS = ("clean", "corrupt")
IOI = "IOI"

#: Seconds per forward pass on an H100 at batch 8 x 128 tokens, extrapolated
#: (not measured) in `knockout.SECONDS_PER_FORWARD_H100` from the H200 sweep of
#: job 22899543. Scaled linearly by the loader's max_length / 128 here. A run
#: records its own measured value in summary.json (`timing`).
SECONDS_PER_FORWARD = ko.SECONDS_PER_FORWARD_H100
#: Model load on Bridges-2 from /ocean (docs/bridges2.md, 458 s observed).
MODEL_LOAD_SECONDS = 460.0

DEFAULT_MARGIN = 0.7
#: The honest build rule's margin (`contingency.HONEST_MARGIN`), a second
#: accuracy column for H, F and user-neutral.
HONEST_MARGIN = 0.3


# ==============================================================================
# ARGUMENTS
# ==============================================================================

def _csv(choices):
    def parse(value):
        items = [one.strip() for one in str(value).split(",") if one.strip()]
        bad = [one for one in items if one not in choices]
        if bad or not items:
            raise argparse.ArgumentTypeError(
                f"{value!r}: expected a comma list of {', '.join(choices)}")
        return items
    return parse


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--task", choices=("far", "ser"), default="far")
    p.add_argument("--sets", required=True,
                   help="JSON {name: [[\"mlp_hidden\", layer, index], ...]}")
    p.add_argument("--conditions", type=_csv(CONDITIONS), default=list(CONDITIONS))
    p.add_argument("--d-dir", help="D dataset dir (default data/datasets/<task>_v2)")
    p.add_argument("--h-dir", help="H twin dir (default data/datasets/<task>_v2_honest); "
                                   "must be D's Neutral-Clause Twin split")
    p.add_argument("--f-dir", help="F no-pressure dir "
                                   "(default data/datasets/<task>_v2_nopressure)")
    p.add_argument("--i-dir", help="user-turn inversion pool (HF dataset dict); "
                                   "required when I is a condition")
    p.add_argument("--n-dir", help="user-neutral pool, I's twin; required with I or N")
    p.add_argument("--pool-dir", help="directory holding <task>_v2_user_inversion and "
                                      "<task>_v2_user_neutral (W3's copies under "
                                      "outputs/_analyses/neuron-partition/data/pools); "
                                      "--i-dir and --n-dir override it")
    p.add_argument("--ids", help="JSON list of instance ids (or {\"instance_ids\": [...]}"
                                 ", or {condition: [...]}) restricting every condition")
    p.add_argument("--split", default="test")
    p.add_argument("--references", type=_csv(REFERENCES), default=list(REFERENCES))
    p.add_argument("--streams", type=_csv(STREAMS), default=list(STREAMS))
    p.add_argument("--readout-margin", type=float, default=DEFAULT_MARGIN)
    p.add_argument("--twin-reverse", action=argparse.BooleanOptionalAction, default=True,
                   help="under the twin reference also patch H with D's values and "
                        "user-neutral with I's (descriptive; N2 under the twin)")
    p.add_argument("--self-replay", action=argparse.BooleanOptionalAction, default=True,
                   help="patch D and I with their own values over the union of all "
                        "sets, for the ladder's epsilon guard")
    p.add_argument("--mean-bank-split", default="train,validation",
                   help="F split(s) the mean bank is collected over (comma list). "
                        "Default train,validation keeps every test id out of it")
    p.add_argument("--ioi", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--ioi-n", type=int, default=100)
    p.add_argument("--ioi-seed", type=int, default=1)
    p.add_argument("--ioi-pool", type=int, default=1000)
    p.add_argument("--model", default="llama-8b-instruct")
    p.add_argument("--device", default="cuda")
    p.add_argument("--hf-token", default=os.environ.get("HF_TOKEN"))
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--max-length", type=int, default=None,
                   help="pad every condition to this many tokens instead of its "
                        "dataset_config max_seq_length (the user-turn pools say 256 for "
                        "~118-token prompts). A prompt longer than this is refused by the "
                        "loader's Readout check, never silently truncated")
    p.add_argument("--sets-per-call", type=int, default=32,
                   help="sets ablated per knock_out_groups call (bounds memory; each "
                        "call repeats one clean and one twin pass per batch)")
    p.add_argument("--limit", type=int, default=None,
                   help="at most this many rows per condition (pilot)")
    p.add_argument("--seconds-per-forward", type=float, default=SECONDS_PER_FORWARD)
    p.add_argument("--model-load-seconds", type=float, default=MODEL_LOAD_SECONDS)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--dry-run", action="store_true")
    return p


def resolve_dirs(args) -> Dict[str, Optional[str]]:
    base = os.path.join(ROOT, "data", "datasets", f"{args.task}_v2")
    pool = getattr(args, "pool_dir", None)
    i_dir = args.i_dir or (os.path.join(pool, f"{args.task}_v2_user_inversion") if pool else None)
    n_dir = args.n_dir or (os.path.join(pool, f"{args.task}_v2_user_neutral") if pool else None)
    dirs = {"D": args.d_dir or base, "H": args.h_dir or base + "_honest",
            "F": args.f_dir or base + "_nopressure", "I": i_dir, "N": n_dir}
    needed = set(args.conditions)
    if "I" in needed:
        needed.add("N")
    if "D" in needed:
        needed.add("H")
    if "mean" in args.references:
        needed.add("F")
    missing = [one for one in sorted(needed) if not dirs.get(one)]
    if missing:
        raise SystemExit(f"no dataset dir for condition(s) {', '.join(missing)}: "
                         f"pass --{missing[0].lower()}-dir")
    for one in sorted(needed):
        if not os.path.isdir(dirs[one]):
            raise SystemExit(f"condition {one}: {dirs[one]} is not a directory")
    return {one: (dirs[one] if one in needed else None) for one in CONDITIONS}


def load_ids(path: Optional[str]) -> Optional[Dict[str, Optional[List[str]]]]:
    """`{condition: [ids] or None}` from a list, `{"instance_ids": [...]}`,
    `{"ids": [...]}` or `{condition: [...]}`; None without `--ids`."""
    if not path:
        return None
    with open(path) as handle:
        raw = json.load(handle)
    if isinstance(raw, dict):
        for field in ("instance_ids", "ids"):
            # A list of ids, or W3's sample file, whose `ids` is {condition: [...]}.
            if field in raw and isinstance(raw[field], (list, dict)):
                raw = raw[field]
                break
    if isinstance(raw, list):
        ids = [str(one) for one in raw]
        return {one: ids for one in CONDITIONS}
    if isinstance(raw, dict) and set(raw) <= set(CONDITIONS):
        return {one: ([str(x) for x in raw[one]] if one in raw else None)
                for one in CONDITIONS}
    raise SystemExit(f"{path}: --ids is a JSON list of ids, {{\"instance_ids\": [...]}} "
                     f"or {{condition: [...]}}")


def load_sets(path: str):
    groups = ko.load_groups(path)
    kinds = sorted({key[0] for _name, keys in groups for key in keys})
    if kinds != ["mlp_hidden"]:
        print(f"  note: --sets names kinds {kinds}; this script is built for mlp_hidden")
    return groups


def set_profile(keys) -> dict:
    by_layer: Dict[int, int] = {}
    for _kind, layer, _index in keys:
        by_layer[layer] = by_layer.get(layer, 0) + 1
    return {"size": len(keys), "per_layer": {str(k): v for k, v in sorted(by_layer.items())}}


# ==============================================================================
# BATCHES: STREAMS, TWINS, IOI
# ==============================================================================

def corrupt_stream(batch):
    """The batch's corrupt prompt as the recipient, its answer words swapped.

    The corrupt stream is the item-swapped designation, so the opposite and the
    honest words trade places (`dataloaders.Batch.target_token` docstring). Its
    twin is the twin's own corrupt prompt. The Readout is read off the corrupt
    mask.
    """
    from component_analysis import dataloaders

    pair = batch.neutral_twin
    twin = None
    if pair is not None:
        twin = dataloaders.NeutralTwinPair(
            rows=list(pair.rows), input_ids=pair.corrupt_input_ids,
            attention_mask=pair.corrupt_attention_mask,
            corrupt_input_ids=pair.input_ids, corrupt_attention_mask=pair.attention_mask,
            clause_span=pair.clause_span)
    return dataloaders.Batch(
        ids=list(batch.ids), records=list(batch.records),
        input_ids=batch.corrupt_input_ids, attention_mask=batch.corrupt_attention_mask,
        corrupt_input_ids=batch.input_ids, corrupt_attention_mask=batch.attention_mask,
        target_token=batch.distractor_token, distractor_token=batch.target_token,
        readout=batch.corrupt_attention_mask.sum(-1).long() - 1, honest=None,
        neutral_twin=twin)


def attach_twin(batch, twin_batch, span_field: str = "request_spans"):
    """`batch` with `twin_batch`'s prompts as its Neutral-Clause Twin.

    The I to user-neutral pairing, which the loader does not build
    (`neutral_twin_dir` resolves to `<task>_honest`). The same checks the D to
    H path makes: the same ids in the same order, the same attention masks and
    Readouts on both streams, the twin's Target equal to this row's Distractor
    (the twin is the honest condition), and tokens that differ only inside the
    request span the records name.
    """
    import torch

    from component_analysis import dataloaders

    if list(batch.ids) != list(twin_batch.ids):
        raise ValueError("twin batch ids differ from the batch's: "
                         f"{list(batch.ids)[:3]} vs {list(twin_batch.ids)[:3]}")
    for name in ("attention_mask", "corrupt_attention_mask"):
        if not torch.equal(getattr(batch, name), getattr(twin_batch, name)):
            raise ValueError(f"the twin's {name} is not the row's: the streams are "
                             f"not token-aligned")
    if not torch.equal(batch.readout, twin_batch.readout):
        raise ValueError("the twin's Readout is not the row's")
    if not torch.equal(twin_batch.target_token, batch.distractor_token) or \
            not torch.equal(twin_batch.distractor_token, batch.target_token):
        raise ValueError("the twin's answer words are not the row's swapped: the twin "
                         "must be the honest-target condition of the same instance")
    spans = []
    for row, record in enumerate(batch.records):
        span = (record.get(span_field) or {})
        for stream, ids_name in (("clean", "input_ids"), ("corrupt", "corrupt_input_ids")):
            differ = (getattr(batch, ids_name)[row] != getattr(twin_batch, ids_name)[row])
            where = differ.nonzero().flatten().tolist()
            bounds = span.get(stream)
            if bounds is None:
                raise ValueError(f"instance {batch.ids[row]}: no {span_field}.{stream} "
                                 f"to check the twin's alignment against")
            outside = [one for one in where if not bounds[0] <= one < bounds[1]]
            if outside:
                raise ValueError(f"instance {batch.ids[row]}: the twin differs outside "
                                 f"the request span {bounds} on the {stream} stream, "
                                 f"at {outside[:5]}")
        spans.append(list(span["clean"]))
    twin = dataloaders.NeutralTwinPair(
        rows=list(range(len(batch.ids))), input_ids=twin_batch.input_ids,
        attention_mask=twin_batch.attention_mask,
        corrupt_input_ids=twin_batch.corrupt_input_ids,
        corrupt_attention_mask=twin_batch.corrupt_attention_mask,
        clause_span=torch.tensor(spans, dtype=torch.long))
    return dataloaders.Batch(
        ids=list(batch.ids), records=list(batch.records), input_ids=batch.input_ids,
        attention_mask=batch.attention_mask, corrupt_input_ids=batch.corrupt_input_ids,
        corrupt_attention_mask=batch.corrupt_attention_mask,
        target_token=batch.target_token, distractor_token=batch.distractor_token,
        readout=batch.readout, honest=None, neutral_twin=twin)


def reverse_twin(batch):
    """The twin as the recipient and the row as its donor (H <- D, N <- I).

    Labels are the twin's own (the row's swapped), so a drop reads in the twin's
    honest direction. Only the rows that have a twin; None when none has.
    """
    import torch

    from component_analysis import dataloaders

    pair = batch.neutral_twin
    if pair is None or not len(pair.rows):
        return None
    rows = torch.tensor(list(pair.rows), dtype=torch.long)
    donor = dataloaders.NeutralTwinPair(
        rows=list(range(len(pair.rows))), input_ids=batch.input_ids[rows],
        attention_mask=batch.attention_mask[rows],
        corrupt_input_ids=batch.corrupt_input_ids[rows],
        corrupt_attention_mask=batch.corrupt_attention_mask[rows],
        clause_span=pair.clause_span)
    return dataloaders.Batch(
        ids=[batch.ids[row] for row in pair.rows],
        records=[batch.records[row] for row in pair.rows],
        input_ids=pair.input_ids, attention_mask=pair.attention_mask,
        corrupt_input_ids=pair.corrupt_input_ids,
        corrupt_attention_mask=pair.corrupt_attention_mask,
        target_token=batch.distractor_token[rows], distractor_token=batch.target_token[rows],
        readout=batch.readout[rows], honest=None, neutral_twin=donor)


def self_twin(batch):
    """The batch as its own twin: a patch that must change nothing."""
    import torch

    from component_analysis import dataloaders

    n = len(batch.ids)
    pair = dataloaders.NeutralTwinPair(
        rows=list(range(n)), input_ids=batch.input_ids.clone(),
        attention_mask=batch.attention_mask.clone(),
        corrupt_input_ids=batch.corrupt_input_ids.clone(),
        corrupt_attention_mask=batch.corrupt_attention_mask.clone(),
        clause_span=torch.zeros((n, 2), dtype=torch.long))
    return dataloaders.Batch(
        ids=list(batch.ids), records=list(batch.records), input_ids=batch.input_ids,
        attention_mask=batch.attention_mask, corrupt_input_ids=batch.corrupt_input_ids,
        corrupt_attention_mask=batch.corrupt_attention_mask,
        target_token=batch.target_token, distractor_token=batch.distractor_token,
        readout=batch.readout, honest=None, neutral_twin=pair)


def ioi_rows(tokenizer, *, n: int, seed: int, pool: int) -> List[dict]:
    """The ladder's IOI floor, rebuilt from its recipe (reader brief section 4).

    `generate_ioi_data_llama(pool, tokenizer, seed)`, deduplicated by sentence
    in generation order, no model-correctness filter; a row is eligible when
    both names are single tokens in context (the sentence tokenizes as its
    prefix plus the answer name's one token). The first `n` eligible rows,
    the final name stripped; the Readout is the last prefix token. Ids are
    `ioi:seed=<seed>:row=<k>`.
    """
    import contextlib
    import io

    from dataset.ioi_llama import generate_ioi_data_llama

    with contextlib.redirect_stdout(io.StringIO()):
        samples = generate_ioi_data_llama(pool, tokenizer, seed=seed)
    out, seen = [], set()
    for sample in samples:
        sentence = sample["sentence"]
        if sentence in seen:
            continue
        seen.add(sentence)
        answer = sentence.strip().split()[-1]
        target = tokenizer.encode(" " + answer, add_special_tokens=False)
        distractor = tokenizer.encode(" " + sample["b"], add_special_tokens=False)
        prefix_text = sentence[:sentence.rfind(" ")]
        prefix = tokenizer.encode(prefix_text, add_special_tokens=True)
        whole = tokenizer.encode(sentence, add_special_tokens=True)
        if len(target) != 1 or len(distractor) != 1 or whole != prefix + target:
            continue
        out.append({"instance_id": f"ioi:seed={seed}:row={len(out)}",
                    "prefix": prefix, "target": target[0], "distractor": distractor[0],
                    "sentence": sentence})
        if len(out) == n:
            break
    return out


def ioi_batches(tokenizer, rows: Sequence[dict], *, batch_size: int):
    """`dataloaders.Batch` objects over IOI rows, right-padded, no twin."""
    import torch

    from component_analysis import dataloaders

    pad = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0
    length = max(len(row["prefix"]) for row in rows)
    out = []
    for start in range(0, len(rows), batch_size):
        chunk = rows[start:start + batch_size]
        ids = torch.full((len(chunk), length), pad, dtype=torch.long)
        mask = torch.zeros((len(chunk), length), dtype=torch.long)
        for row, one in enumerate(chunk):
            ids[row, :len(one["prefix"])] = torch.tensor(one["prefix"])
            mask[row, :len(one["prefix"])] = 1
        out.append(dataloaders.Batch(
            ids=[one["instance_id"] for one in chunk],
            records=[{"sentence": one["sentence"]} for one in chunk],
            input_ids=ids, attention_mask=mask, corrupt_input_ids=ids.clone(),
            corrupt_attention_mask=mask.clone(),
            target_token=torch.tensor([one["target"] for one in chunk]),
            distractor_token=torch.tensor([one["distractor"] for one in chunk]),
            readout=mask.sum(-1).long() - 1, honest=None, neutral_twin=None))
    return out


def condition_ids(dataset_dir: str, split: str, wanted: Optional[List[str]],
                  limit: Optional[int]) -> List[str]:
    """The ids a condition runs on: `wanted` in its order (or the split's),
    restricted to the split, then cut to `limit`."""
    from dataset import deception_common as dc
    from component_analysis import sampling

    import contextlib
    import io

    with contextlib.redirect_stdout(io.StringIO()):
        records = dc.load_or_generate_deception_data(dataset_dir, split=split)
    split_ids = sampling.record_ids(records)
    if wanted is None:
        chosen = split_ids
    else:
        present = set(split_ids)
        chosen = [one for one in wanted if one in present]
    return chosen[:limit] if limit else chosen


#: Conditions that must run on the same ids: D with its twin H and with F, and
#: I with its twin user-neutral.
PAIRING_GROUPS = (("D", "H", "F"), ("I", "N"))


def limited_ids(args, dirs, ids_by_condition) -> dict:
    """`--limit`: per pairing group (D, H, F and I, user-neutral), the first
    `limit` ids every loaded condition of the group has, in the order of the
    group's first loaded condition. The D and I samples need not overlap."""
    out = {one: None for one in CONDITIONS}
    for group in PAIRING_GROUPS:
        loaded = [one for one in group if dirs.get(one)]
        if not loaded:
            continue
        available = {one: condition_ids(dirs[one], args.split, ids_by_condition[one], None)
                     for one in loaded}
        common = set.intersection(*(set(v) for v in available.values()))
        chosen = [one for one in available[loaded[0]] if one in common][:args.limit]
        for one in loaded:
            out[one] = chosen
    return out


def build_condition_batches(args, dirs, tokenizer, ids_by_condition) -> dict:
    """`{condition: [Batch, ...]}` on the clean stream, twins attached on D and I.

    D is loaded through `dataloaders.causal_batches`, whose own pairing joins
    the H twin by id and checks pressure id and clause alignment. I is loaded
    the same way and paired with the user-neutral pool by `attach_twin`.
    Returns also a report per condition.
    """
    import contextlib
    import io

    from component_analysis import dataloaders

    task = f"{args.task}_v2"
    wanted_conditions = set(args.conditions)
    if "mean" in args.references:
        wanted_conditions.add("F")
    out, report = {}, {}

    def load(condition):
        ids = ids_by_condition[condition]
        with contextlib.redirect_stdout(io.StringIO()):
            batches = dataloaders.causal_batches(
                dirs[condition], tokenizer, ids=ids, task=task, split=args.split,
                batch_size=args.batch_size, max_length=args.max_length)
        return batches

    if "D" in wanted_conditions:
        expected = dataloaders.neutral_twin_dir(dirs["D"], {"task": task})
        if os.path.abspath(expected) != os.path.abspath(dirs["H"]):
            raise SystemExit(f"D's Neutral-Clause Twin is read from {expected}, not "
                             f"--h-dir {dirs['H']}; pass a D dir whose sibling is H")
    for condition in ("D", "H", "F", "I", "N"):
        if condition not in wanted_conditions and not (condition == "N" and "I" in wanted_conditions):
            continue
        batches = load(condition)
        report[condition] = {key: batches.report.get(key) for key in (
            "n_requested", "n_instances", "missing_from_split", "dropped_by_tokenization",
            "neutral_twin_source", "n_with_neutral_twin", "without_neutral_twin",
            "max_length")}
        report[condition]["dataset_dir"] = os.path.abspath(dirs[condition])
        out[condition] = list(batches)
    if "I" in out:
        out["I"] = [attach_twin(one, twin) for one, twin in zip(out["I"], out["N"])]
        if len(out["I"]) != len(out["N"]):
            raise ValueError("I and user-neutral load different numbers of batches")
        report["I"]["neutral_twin_source"] = os.path.abspath(dirs["N"])
        report["I"]["n_with_neutral_twin"] = sum(len(one.ids) for one in out["I"])
        report["I"]["without_neutral_twin"] = []
    if "N" in out and "N" not in args.conditions:
        del out["N"]
    check_labels(out)
    return out, report


def check_labels(batches_by_condition: dict) -> None:
    """Per id: H's, F's and user-neutral's Target is the opposite condition's
    Distractor, so one sign turns each into D orientation."""
    def labels(condition):
        out = {}
        for batch in batches_by_condition.get(condition, []):
            for row, one in enumerate(batch.ids):
                out[one] = (int(batch.target_token[row]), int(batch.distractor_token[row]))
        return out

    reference = labels("D") or labels("I")
    for condition in ("H", "F", "N", "I"):
        if condition not in batches_by_condition or not reference:
            continue
        theirs = labels(condition)
        for one, (target, distractor) in theirs.items():
            if one not in reference:
                continue
            opposite, honest = reference[one]
            expected = (opposite, honest) if OPPOSITE_TARGET[condition] else (honest, opposite)
            if (target, distractor) != expected:
                raise ValueError(f"condition {condition}, instance {one}: Target/Distractor "
                                 f"{(target, distractor)} are not the opposite condition's "
                                 f"{'same' if OPPOSITE_TARGET[condition] else 'swapped'} "
                                 f"words {expected}")


# ==============================================================================
# THE PLAN AND ITS COST
# ==============================================================================

def cells(args, has_ioi: bool) -> List[tuple]:
    """`(reference, condition, stream, kind)`: every knock_out_groups pass.

    kind: `twin` (D, I), `reverse` (H <- D, N <- I, read off D's and I's
    batches), `fill` (mean or zero).
    """
    out = []
    for reference in args.references:
        for condition in args.conditions:
            for stream in args.streams:
                if reference == "twin":
                    if condition in TWIN_OF:
                        out.append((reference, condition, stream, "twin"))
                    elif args.twin_reverse and REVERSE_SOURCE.get(condition) \
                            in args.conditions:
                        out.append((reference, condition, stream, "reverse"))
                else:
                    out.append((reference, condition, stream, "fill"))
        if has_ioi and reference != "twin":
            out.append((reference, IOI, "clean", "fill"))
    return out


def estimate(args, groups, n_batches: dict, max_length: dict, *, bank_batches: int) -> dict:
    """Forward passes and seconds per pass, from `--seconds-per-forward` at
    batch `--batch-size` x 128 tokens, scaled by max_length / 128."""
    n_sets = len(groups)
    chunks = max(1, -(-n_sets // max(1, args.sets_per_call)))
    lines, total_forwards, total_seconds = [], 0, 0.0
    for reference, condition, stream, kind in cells(args, IOI in n_batches):
        source = condition
        if kind == "reverse":
            source = REVERSE_SOURCE[condition]
        batches = n_batches.get(source, 0)
        base = 2 if kind in ("twin", "reverse") else 1
        if kind == "fill" and condition in TWIN_OF:
            base += 1        # the twin's own margin (R19(1)), one forward per batch
        forwards = batches * (chunks * base + n_sets)
        scale = max_length.get(source, 128) / 128.0
        seconds = forwards * args.seconds_per_forward * scale
        total_forwards += forwards
        total_seconds += seconds
        lines.append({"reference": reference, "condition": condition, "stream": stream,
                      "kind": kind, "batches": batches, "forwards": forwards,
                      "seconds": round(seconds, 1)})
    if "mean" in args.references:
        forwards = 2 * bank_batches
        seconds = forwards * args.seconds_per_forward * max_length.get("F", 128) / 128.0
        total_forwards += forwards
        total_seconds += seconds
        lines.append({"reference": "mean", "condition": "F (mean bank)", "stream": "both",
                      "kind": "bank", "batches": bank_batches, "forwards": forwards,
                      "seconds": round(seconds, 1)})
    if args.self_replay and "twin" in args.references:
        for condition in TWIN_OF:
            if condition in args.conditions:
                forwards = n_batches.get(condition, 0) * 3 * len(args.streams)
                seconds = forwards * args.seconds_per_forward * \
                    max_length.get(condition, 128) / 128.0
                total_forwards += forwards
                total_seconds += seconds
                lines.append({"reference": "twin", "condition": condition,
                              "stream": ",".join(args.streams), "kind": "self_replay",
                              "batches": n_batches.get(condition, 0),
                              "forwards": forwards, "seconds": round(seconds, 1)})
    return {"cells": lines, "forwards": total_forwards,
            "forward_seconds": round(total_seconds, 1),
            "model_load_seconds": args.model_load_seconds,
            "total_seconds": round(total_seconds + args.model_load_seconds, 1),
            "seconds_per_forward": args.seconds_per_forward,
            "seconds_per_forward_basis": (
                "knockout.SECONDS_PER_FORWARD_H100 = 0.0368 x 5.4 / 4.0 s at batch 8 x "
                "128 tokens, extrapolated from the H200 sweep of job 22899543 (not "
                "measured on H100), scaled linearly by max_length / 128; neuron "
                "passes also save up to 32 full-width down_proj inputs, so treat it "
                "as a floor and pilot with --limit 16 first"),
            "n_sets": n_sets, "chunks": chunks}


# ==============================================================================
# METRICS
# ==============================================================================

def _mean(values) -> Optional[float]:
    values = [one for one in values if one is not None]
    return sum(values) / len(values) if values else None


def stream_average(per_stream: Dict[str, Dict[str, float]], ids) -> Dict[str, float]:
    """`{id: mean over the streams that have the id}`."""
    out = {}
    for one in ids:
        values = [per_stream[s][one] for s in per_stream if one in per_stream[s]
                  and per_stream[s][one] is not None]
        if values:
            out[one] = sum(values) / len(values)
    return out


def share(per_stream: Dict[str, Dict[str, float]], ids, test) -> Optional[float]:
    """Share of (id, stream) passing `test`, streams averaged within an id."""
    indicators = {s: {one: (1.0 if test(value) else 0.0) for one, value in rows.items()
                      if value is not None} for s, rows in per_stream.items()}
    averaged = stream_average(indicators, ids)
    return _mean(averaged.values())


def removed_fraction(intact: Optional[float], ablated: Optional[float],
                     epsilon: float = 1e-6) -> Optional[float]:
    if intact is None or ablated is None or intact <= epsilon:
        return None
    return (intact - ablated) / intact


def ladder_ratio(m_intact, m_ablated, m_twin, ids, epsilon) -> dict:
    """The ladder's margin ratio: G = mean(m - m_twin), fraction = mean(m - m_abl) / G.

    Each argument is `{stream: {id: m}}` in D orientation. Streams are averaged
    within an id before ids are averaged. Refused (fraction None) when G is not
    above `epsilon`.
    """
    common = [one for one in ids
              if all(one in m_intact[s] and one in m_ablated[s] and one in m_twin[s]
                     and m_twin[s][one] is not None for s in m_intact)]
    gap = stream_average({s: {one: m_intact[s][one] - m_twin[s][one] for one in common}
                          for s in m_intact}, common)
    drop = stream_average({s: {one: m_intact[s][one] - m_ablated[s][one] for one in common}
                           for s in m_intact}, common)
    g = _mean(gap.values())
    d = _mean(drop.values())
    fraction = None if g is None or d is None or g <= epsilon else d / g
    return {"G": g, "mean_drop": d, "fraction_removed": fraction, "epsilon": epsilon,
            "n_ids": len(common)}


class Cell:
    """Every number of one (reference, condition, stream) pass, per id."""

    def __init__(self, sign: int):
        self.sign = sign
        self.ids: List[str] = []
        self.intact: Dict[str, float] = {}
        self.intact_argmax: Dict[str, int] = {}
        self.twin: Dict[str, Optional[float]] = {}
        self.ablated: Dict[str, Dict[str, float]] = {}
        self.ablated_argmax: Dict[str, Dict[str, int]] = {}
        self.target: Dict[str, int] = {}
        self.distractor: Dict[str, int] = {}
        self.unpaired: List[str] = []
        self.seconds = 0.0
        self.forwards = 0

    def m(self, value):
        return None if value is None else self.sign * value


#: Per-cell numbers appended as each cell finishes (see `run`).
PARTIAL_NAME = "cells_partial.jsonl"


def cell_record(cell: Cell) -> dict:
    """Everything a Cell holds, as plain JSON (own-label margins; `sign` turns
    them into D orientation)."""
    return {"sign": cell.sign, "ids": cell.ids, "intact": cell.intact,
            "intact_argmax": cell.intact_argmax, "twin": cell.twin,
            "ablated": cell.ablated, "ablated_argmax": cell.ablated_argmax,
            "target": cell.target, "distractor": cell.distractor,
            "unpaired": cell.unpaired, "seconds": cell.seconds, "forwards": cell.forwards}


def run_cell(model, batches, groups, plan, *, mean_bank, sets_per_call, sign,
             twin_from_counterfactual: bool) -> Cell:
    """`knock_out_groups` over every chunk of sets; one Cell of per-id numbers."""
    cell = Cell(sign)
    tokens = {}
    for batch in batches:
        for row, one in enumerate(batch.ids):
            tokens[one] = (int(batch.target_token[row]), int(batch.distractor_token[row]))
    for start in range(0, len(groups), max(1, sets_per_call)):
        chunk = groups[start:start + sets_per_call]
        began = time.time()
        effects = ko.knock_out_groups(model, batches, chunk, plan=plan,
                                      mean_bank=mean_bank, record_argmax=True)
        cell.seconds += time.time() - began
        if not cell.ids:
            cell.ids = list(effects.ids)
            cell.unpaired = list(effects.unpaired)
            cell.intact = dict(zip(effects.ids, effects.clean_logit_difference))
            cell.intact_argmax = dict(zip(effects.ids, effects.clean_argmax))
            twins = (effects.counterfactual_logit_difference if twin_from_counterfactual
                     else effects.neutral_twin_logit_difference)
            if twins:
                cell.twin = dict(zip(effects.ids, twins))
        elif list(effects.ids) != cell.ids:
            raise RuntimeError("two chunks of one cell ran on different ids")
        for name, _keys in chunk:
            cell.ablated[name] = dict(zip(effects.ids, effects.knocked_logit_difference[name]))
            cell.ablated_argmax[name] = dict(zip(effects.ids, effects.knocked_argmax[name]))
    for one in cell.ids:
        cell.target[one], cell.distractor[one] = tokens[one]
    return cell


def condition_metrics(cells_by_stream: Dict[str, Cell], name: str, *, margin: float,
                      opposite_target: bool, ioi: bool = False) -> dict:
    """Intact and ablated readouts of one condition for one set, streams averaged."""
    streams = list(cells_by_stream)
    ids = sorted(set.intersection(*(set(c.ids) for c in cells_by_stream.values())))

    def per_stream(fn):
        return {s: {one: fn(c, one) for one in ids} for s, c in cells_by_stream.items()}

    m_int = per_stream(lambda c, one: c.m(c.intact[one]))
    m_abl = per_stream(lambda c, one: c.m(c.ablated[name][one]))
    own_int = per_stream(lambda c, one: c.intact[one])
    own_abl = per_stream(lambda c, one: c.ablated[name][one])
    correct_int = per_stream(lambda c, one: float(c.intact_argmax[one] == c.target[one]))
    correct_abl = per_stream(lambda c, one: float(c.ablated_argmax[name][one] == c.target[one]))
    # The opposite word in D orientation: the own Target on D and I, the own
    # Distractor on H, F and user-neutral.
    opposite = (lambda c, one: c.target[one]) if opposite_target else \
        (lambda c, one: c.distractor[one])
    gated_int = per_stream(lambda c, one: float(c.intact_argmax[one] == opposite(c, one)
                                                and c.m(c.intact[one]) >= margin))
    gated_abl = per_stream(lambda c, one: float(c.ablated_argmax[name][one] == opposite(c, one)
                                                and c.m(c.ablated[name][one]) >= margin))
    out = {
        "n_ids": len(ids), "streams": streams,
        "mean_m_intact": _mean(stream_average(m_int, ids).values()),
        "mean_m_ablated": _mean(stream_average(m_abl, ids).values()),
        "accuracy_argmax_intact": _mean(stream_average(correct_int, ids).values()),
        "accuracy_argmax_ablated": _mean(stream_average(correct_abl, ids).values()),
        "accuracy_two_way_intact": share(own_int, ids, lambda v: v > 0),
        "accuracy_two_way_ablated": share(own_abl, ids, lambda v: v > 0),
    }
    if not ioi:
        out.update({
            "p_opposite_at_margin_intact": share(m_int, ids, lambda v: v >= margin),
            "p_opposite_at_margin_ablated": share(m_abl, ids, lambda v: v >= margin),
            "p_opposite_argmax_gated_intact": _mean(stream_average(gated_int, ids).values()),
            "p_opposite_argmax_gated_ablated": _mean(stream_average(gated_abl, ids).values()),
        })
        if not opposite_target:
            out["accuracy_at_honest_margin_intact"] = share(own_int, ids,
                                                            lambda v: v >= HONEST_MARGIN)
            out["accuracy_at_honest_margin_ablated"] = share(own_abl, ids,
                                                             lambda v: v >= HONEST_MARGIN)
    for key in ("accuracy_argmax", "accuracy_two_way"):
        intact, ablated = out[f"{key}_intact"], out[f"{key}_ablated"]
        out[f"{key}_shift_points"] = (None if intact is None or ablated is None
                                      else 100.0 * (ablated - intact))
    return out


def effect_metrics(opposite_cells: Dict[str, Cell], twin_cond_cells: Optional[Dict[str, Cell]],
                   name: str, *, reference: str, margin: float, epsilon: float) -> dict:
    """The D (or I) effect, intact and ablated, by the rate and the ladder ratio.

    `opposite_cells` are D's (or I's) per stream; their `twin` margins are the
    twin's own intact run with D's labels. `twin_cond_cells` are H's (or
    user-neutral's) own condition run under the same reference (mean, zero),
    for the twin-ablated rate; None under the twin reference, where the twin
    run is never patched.
    """
    ids = sorted(set.intersection(*(set(c.ids) for c in opposite_cells.values())))
    ids = [one for one in ids
           if all(c.twin.get(one) is not None for c in opposite_cells.values())]
    m_int = {s: {one: c.m(c.intact[one]) for one in ids} for s, c in opposite_cells.items()}
    m_abl = {s: {one: c.m(c.ablated[name][one]) for one in ids}
             for s, c in opposite_cells.items()}
    m_twin = {s: {one: c.m(c.twin[one]) for one in ids} for s, c in opposite_cells.items()}

    def rate(values):
        return share(values, ids, lambda v: v >= margin)

    p_int, p_abl, p_twin = rate(m_int), rate(m_abl), rate(m_twin)
    effect_int = None if p_int is None or p_twin is None else p_int - p_twin
    effect_abl_vs_twin_intact = None if p_abl is None or p_twin is None else p_abl - p_twin
    out = {
        "n_ids": len(ids),
        "rate": {
            "p_opposite_intact": p_int, "p_opposite_ablated": p_abl,
            "p_twin_intact": p_twin, "effect_intact": effect_int,
            "effect_ablated_vs_twin_intact": effect_abl_vs_twin_intact,
            "fraction_removed_vs_twin_intact": removed_fraction(effect_int,
                                                                effect_abl_vs_twin_intact),
        },
        "ladder_margin_ratio": ladder_ratio(m_int, m_abl, m_twin, ids, epsilon),
    }
    if reference == "twin":
        out["rate"]["effect_ablated"] = effect_abl_vs_twin_intact
        out["rate"]["fraction_removed"] = out["rate"]["fraction_removed_vs_twin_intact"]
        out["rate"]["twin_ablated"] = "the twin run is the donor and is not patched"
    elif twin_cond_cells:
        twin_ids = [one for one in ids if all(one in c.ids for c in twin_cond_cells.values())]
        m_twin_abl = {s: {one: c.m(c.ablated[name][one]) for one in twin_ids}
                      for s, c in twin_cond_cells.items() if s in opposite_cells}
        m_twin_cond_int = {s: {one: c.m(c.intact[one]) for one in twin_ids}
                           for s, c in twin_cond_cells.items() if s in opposite_cells}
        p_twin_abl = share(m_twin_abl, twin_ids, lambda v: v >= margin)
        p_d_abl_common = share({s: {one: m_abl[s][one] for one in twin_ids} for s in m_abl},
                               twin_ids, lambda v: v >= margin)
        p_d_int_common = share({s: {one: m_int[s][one] for one in twin_ids} for s in m_int},
                               twin_ids, lambda v: v >= margin)
        p_twin_int_common = share(m_twin_cond_int, twin_ids, lambda v: v >= margin)
        e_int = (None if p_d_int_common is None or p_twin_int_common is None
                 else p_d_int_common - p_twin_int_common)
        e_abl = (None if p_d_abl_common is None or p_twin_abl is None
                 else p_d_abl_common - p_twin_abl)
        out["rate"].update({
            "p_twin_ablated": p_twin_abl, "effect_ablated": e_abl,
            "effect_intact_on_twin_condition_ids": e_int,
            "fraction_removed": removed_fraction(e_int, e_abl),
            "n_ids_with_twin_condition": len(twin_ids)})
    else:
        out["rate"]["effect_ablated"] = None
        out["rate"]["fraction_removed"] = None
        out["rate"]["twin_ablated"] = "twin condition not run under this reference"
    return out


def twin_crosscheck(opposite_cells: Dict[str, Cell], twin_cond_cells: Dict[str, Cell]) -> dict:
    """Max |twin margin read in D's batch - the twin condition's own margin| (D orientation).

    The same prompt, read twice: once as D's twin, once as its own condition.
    They differ only by batch composition (padding is identical); a large gap
    means the wrong row was paired.
    """
    worst, n = 0.0, 0
    for stream, cell in opposite_cells.items():
        other = twin_cond_cells.get(stream)
        if other is None:
            continue
        for one, value in cell.twin.items():
            if value is None or one not in other.intact:
                continue
            worst = max(worst, abs(cell.m(value) - other.m(other.intact[one])))
            n += 1
    return {"max_abs_difference": worst, "n": n}


# ==============================================================================
# RUN
# ==============================================================================

#: The ladder's audited intact IOI accuracy on its 100 rows (reader brief section 2).
IOI_REFERENCE_ACCURACY = 0.51


def ioi_check(results, args) -> Optional[dict]:
    """Intact IOI argmax accuracy against the ladder's 0.51 (ruling R4)."""
    for reference in ("mean", "zero"):
        cell = results.get(reference, {}).get(IOI, {}).get("clean")
        if cell is None or not cell.ids:
            continue
        correct = [float(cell.intact_argmax[one] == cell.target[one]) for one in cell.ids]
        accuracy = sum(correct) / len(correct)
        return {"n_rows": len(correct), "intact_argmax_accuracy": accuracy,
                "ladder_reference": IOI_REFERENCE_ACCURACY,
                "difference_points": 100.0 * (accuracy - IOI_REFERENCE_ACCURACY),
                "seed": args.ioi_seed, "pool": args.ioi_pool}
    return None


def _plan(reference):
    if reference == "twin":
        return ko.KnockoutPlan(scheme="interchange", counterfactual="neutral_twin")
    return ko.KnockoutPlan(scheme=reference)


def dataset_files(dirs: dict, extra: Sequence[str]) -> List[str]:
    from run_manifest import data_files_under

    files = []
    for directory in dirs.values():
        if directory:
            files.extend(data_files_under(directory))
    files.extend(path for path in extra if path)
    return files


def dry_run(args, groups, dirs, ids_by_condition) -> dict:
    """The plan and its cost, with no model. Builds batches when a tokenizer loads."""
    n_batches, max_length, rows, how = {}, {}, {}, "tokenizer"
    tokenizer = None
    try:
        from component_analysis.instances import load_analysis_tokenizer
        tokenizer = load_analysis_tokenizer(args.model, hf_token=args.hf_token)
    except Exception as error:                               # noqa: BLE001
        how = f"dataset rows only (tokenizer unavailable: {type(error).__name__}: {error})"
    report = {}
    if tokenizer is not None:
        batches, report = build_condition_batches(args, dirs, tokenizer, ids_by_condition)
        for condition, items in batches.items():
            n_batches[condition] = len(items)
            rows[condition] = sum(len(one.ids) for one in items)
            max_length[condition] = int(items[0].input_ids.shape[1]) if items else 128
        if args.ioi:
            ioi = ioi_rows(tokenizer, n=args.ioi_n, seed=args.ioi_seed, pool=args.ioi_pool)
            n_batches[IOI] = -(-len(ioi) // args.batch_size)
            rows[IOI] = len(ioi)
            max_length[IOI] = max(len(one["prefix"]) for one in ioi) if ioi else 32
    else:
        from dataset import deception_common as dc
        for condition in set(args.conditions) | ({"F"} if "mean" in args.references else set()):
            chosen = condition_ids(dirs[condition], args.split, ids_by_condition[condition],
                                   args.limit)
            rows[condition] = len(chosen)
            n_batches[condition] = -(-len(chosen) // args.batch_size)
            max_length[condition] = args.max_length or int(dc.load_dataset_config(
                dirs[condition]).get("max_seq_length", 128))
        if args.ioi:
            n_batches[IOI] = -(-args.ioi_n // args.batch_size)
            rows[IOI] = args.ioi_n
            max_length[IOI] = 32
    bank_batches = 0
    if "mean" in args.references:
        from dataset import deception_common as dc
        for split in args.mean_bank_split.split(","):
            n = len(condition_ids(dirs["F"], split.strip(), None, None))
            bank_batches += -(-n // args.batch_size)
        max_length.setdefault("F", args.max_length or int(dc.load_dataset_config(
            dirs["F"]).get("max_seq_length", 128)))
    plan = estimate(args, groups, n_batches, max_length, bank_batches=bank_batches)
    plan.update({"rows": rows, "batches": n_batches, "max_length": max_length,
                 "built_with": how, "condition_report": report,
                 "sets": {name: set_profile(keys) for name, keys in groups}})
    return plan


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    dirs = resolve_dirs(args)
    groups = load_sets(args.sets)
    ids = load_ids(args.ids) or {one: None for one in CONDITIONS}
    if args.limit:
        ids = limited_ids(args, dirs, ids)

    if args.dry_run:
        plan = dry_run(args, groups, dirs, ids)
        print(f"neuron_set_ablation --dry-run: {len(groups)} set(s), references "
              f"{','.join(args.references)}, conditions {','.join(args.conditions)}"
              f"{' + IOI' if args.ioi else ''}, streams {','.join(args.streams)}")
        print(f"  rows {plan['rows']}  batches {plan['batches']}  "
              f"max_length {plan['max_length']}  ({plan['built_with']})")
        for line in plan["cells"]:
            print(f"  {line['reference']:5s} {line['condition']:15s} {line['stream']:13s} "
                  f"{line['kind']:11s} {line['batches']:4d} batch(es) "
                  f"{line['forwards']:7d} forwards  ~{line['seconds'] / 60:6.1f} min")
        print(f"  total {plan['forwards']} forwards, ~{plan['forward_seconds'] / 60:.1f} min "
              f"of forwards + {plan['model_load_seconds'] / 60:.1f} min model load = "
              f"~{plan['total_seconds'] / 60:.1f} min at {plan['seconds_per_forward']:.4f} "
              f"s/forward ({plan['seconds_per_forward_basis']})")
        print(json.dumps({"dry_run": {k: v for k, v in plan.items() if k != "cells"}},
                         default=str)[:4000])
        return 0

    return run(args, groups, dirs, ids)


def run(args, groups, dirs, ids) -> int:
    import torch

    from component_analysis import dataloaders, hooks

    os.makedirs(args.output_dir, exist_ok=True)
    began = time.time()
    model = hooks.load_analysis_model(args.model, device=args.device, hf_token=args.hf_token)
    load_seconds = time.time() - began
    print(f"  model: {hooks.describe(model)} in {load_seconds:.0f} s")
    ko.check_groups(groups, hooks.geometry(model))
    # The repo's own tokenizer (right padding, pad = eos), as every loader and
    # the dry run use; nnsight's wrapper tokenizer is not used for encoding.
    from component_analysis.instances import load_analysis_tokenizer
    tokenizer = load_analysis_tokenizer(args.model, hf_token=args.hf_token)

    batches, report = build_condition_batches(args, dirs, tokenizer, ids)
    if args.ioi:
        ioi = ioi_rows(tokenizer, n=args.ioi_n, seed=args.ioi_seed, pool=args.ioi_pool)
        batches[IOI] = ioi_batches(tokenizer, ioi, batch_size=args.batch_size)
        report[IOI] = {"n_instances": len(ioi), "seed": args.ioi_seed, "pool": args.ioi_pool,
                       "recipe": ioi_rows.__doc__.strip().split("\n\n")[0]}
    union, seen = [], set()
    for _name, keys in groups:
        for key in keys:
            if key not in seen:
                seen.add(key)
                union.append(key)

    def stream_batches(condition, stream):
        items = batches[condition]
        return items if stream == "clean" else [corrupt_stream(one) for one in items]

    bank, bank_info = None, None
    if "mean" in args.references:
        bank_batches = []
        with torch.no_grad():
            for split in args.mean_bank_split.split(","):
                import contextlib
                import io
                with contextlib.redirect_stdout(io.StringIO()):
                    loaded = dataloaders.descriptive_batches(
                        dirs["F"], tokenizer, task=f"{args.task}_v2", split=split.strip(),
                        batch_size=args.batch_size, max_length=args.max_length)
                bank_batches.extend(list(loaded))
            t0 = time.time()
            bank, bank_info = ko.collect_mean_bank(model, bank_batches, union)
            bank_info.update({"dataset_dir": os.path.abspath(dirs["F"]),
                              "splits": args.mean_bank_split, "seconds": time.time() - t0,
                              "forwards": 2 * len(bank_batches)})
        print(f"  mean bank: {bank_info['n_tokens']:.0f} tokens over "
              f"{bank_info['n_instances']} F instance(s) ({args.mean_bank_split})")

    replay = {}
    if args.self_replay and "twin" in args.references:
        for condition in TWIN_OF:
            if condition not in batches:
                continue
            worst = 0.0
            for stream in args.streams:
                own = [self_twin(one) for one in stream_batches(condition, stream)]
                effects = ko.knock_out_groups(model, own, [("self_replay", union)],
                                              plan=_plan("twin"))
                worst = max([worst] + [abs(a - b) for a, b in zip(
                    effects.clean_logit_difference,
                    effects.knocked_logit_difference["self_replay"])])
            replay[condition] = worst
        print(f"  self-replay error (max |m|, union of {len(union)} neurons): {replay}")

    results: Dict[str, Dict[str, Dict[str, Cell]]] = {}
    timing = []
    # One line per finished cell, appended as it finishes, so a job killed at
    # its walltime keeps every cell it completed (summary.json and rows.jsonl
    # are written only at the end).
    partial_path = os.path.join(args.output_dir, PARTIAL_NAME)
    with open(partial_path, "w") as handle:
        handle.write(json.dumps({"header": True, "argv": sys.argv, "sets": [n for n, _k in groups],
                                 "self_replay_error": replay, "mean_bank": bank_info},
                                default=str) + "\n")
    for reference, condition, stream, kind in cells(args, IOI in batches):
        plan = _plan(reference)
        sign = 1 if (condition == IOI or OPPOSITE_TARGET[condition]) else -1
        if kind == "reverse":
            source = REVERSE_SOURCE[condition]
            items = [one for one in (reverse_twin(b) for b in stream_batches(source, stream))
                     if one is not None]
        else:
            items = stream_batches(condition, stream)
        cell = run_cell(model, items, groups, plan, mean_bank=bank,
                        sets_per_call=args.sets_per_call, sign=sign,
                        twin_from_counterfactual=(kind == "twin"))
        base = 2 if kind in ("twin", "reverse") else (2 if condition in TWIN_OF else 1)
        chunks = -(-len(groups) // max(1, args.sets_per_call))
        cell.forwards = len(items) * (chunks * base + len(groups))
        results.setdefault(reference, {}).setdefault(condition, {})[stream] = cell
        timing.append({"reference": reference, "condition": condition, "stream": stream,
                       "kind": kind, "seconds": round(cell.seconds, 2),
                       "forwards": cell.forwards,
                       "seconds_per_forward": (cell.seconds / cell.forwards
                                               if cell.forwards else None),
                       "batch_size": args.batch_size,
                       "max_length": int(items[0].input_ids.shape[1]) if items else None})
        print(f"  {reference:5s} {condition:4s} {stream:8s} {kind:8s} {len(cell.ids):4d} ids "
              f"{cell.seconds:7.1f} s")
        with open(partial_path, "a") as handle:
            handle.write(json.dumps({**cell_record(cell), "timing": timing[-1]}) + "\n")

    summary_sets = {}
    rows_path = os.path.join(args.output_dir, "rows.jsonl")
    with open(rows_path, "w") as rows_out:
        for name, keys in groups:
            per_reference = {}
            for reference, by_condition in results.items():
                block = {"conditions": {}, "effects": {}, "collateral": {}}
                for condition, by_stream in by_condition.items():
                    is_ioi = condition == IOI
                    block["conditions"][condition] = condition_metrics(
                        by_stream, name, margin=args.readout_margin,
                        opposite_target=(True if is_ioi else OPPOSITE_TARGET[condition]),
                        ioi=is_ioi)
                    if reference == "twin" and condition in ("H", "N"):
                        block["conditions"][condition]["note"] = (
                            "reverse twin: the twin patched with the opposite row's values "
                            "(descriptive)")
                    for one in sorted(set.intersection(*(set(c.ids) for c in by_stream.values()))):
                        line = {"reference": reference, "set": name, "condition": condition,
                                "instance_id": one, "m_intact": {}, "m_ablated": {},
                                "argmax_intact": {}, "argmax_ablated": {}, "twin_m_intact": {},
                                "correct_token": {}, "opposite_token": {}}
                        for stream, cell in by_stream.items():
                            line["m_intact"][stream] = cell.m(cell.intact[one])
                            line["m_ablated"][stream] = cell.m(cell.ablated[name][one])
                            line["argmax_intact"][stream] = cell.intact_argmax[one]
                            line["argmax_ablated"][stream] = cell.ablated_argmax[name][one]
                            line["correct_token"][stream] = cell.target[one]
                            line["opposite_token"][stream] = (
                                cell.target[one] if (is_ioi or OPPOSITE_TARGET[condition])
                                else cell.distractor[one])
                            if cell.twin:
                                line["twin_m_intact"][stream] = cell.m(cell.twin.get(one))
                        rows_out.write(json.dumps(line) + "\n")
                for condition, twin in TWIN_OF.items():
                    if condition not in by_condition:
                        continue
                    epsilon = max(1e-6, 10.0 * replay.get(condition, 0.0))
                    block["effects"][condition] = effect_metrics(
                        by_condition[condition],
                        None if reference == "twin" else by_condition.get(twin), name,
                        reference=reference, margin=args.readout_margin, epsilon=epsilon)
                for condition in ("H", "F", IOI, "N"):
                    metrics = block["conditions"].get(condition)
                    if reference == "twin" and condition in ("F", IOI):
                        block["collateral"][condition] = None
                        continue
                    if metrics is None:
                        continue
                    block["collateral"][condition] = {
                        "accuracy_argmax_shift_points": metrics["accuracy_argmax_shift_points"],
                        "accuracy_two_way_shift_points": metrics["accuracy_two_way_shift_points"],
                        "basis": ("reverse twin (descriptive)" if reference == "twin"
                                  else reference)}
                per_reference[reference] = block
            summary_sets[name] = {**set_profile(keys), "references": per_reference}

    crosschecks = {}
    for reference, by_condition in results.items():
        if reference == "twin":
            continue
        for condition, twin in TWIN_OF.items():
            if condition in by_condition and twin in by_condition:
                crosschecks[f"{reference}:{condition}"] = twin_crosscheck(
                    by_condition[condition], by_condition[twin])

    summary = {
        "analysis": "neuron_set_ablation",
        "task": f"{args.task}_v2",
        "args": vars(args),
        "model": args.model, "model_description": hooks.describe(model),
        "model_load_seconds": load_seconds,
        "definitions": {
            "neuron": "('mlp_hidden', layer, index): column index of the down_proj input "
                      "after the SwiGLU gate",
            "m": "logit(opposite answer) - logit(honest answer) at the Readout, fp32 final "
                 "norm and unembedding; the row's own target-minus-distractor on D and I, its "
                 "negative on H, F and user-neutral (D orientation)",
            "streams": "clean and corrupt prompts; the corrupt stream's answer words are "
                       "swapped; streams averaged within an id, then ids averaged",
            "p_opposite_at_margin": f"share with m >= {args.readout_margin} "
                                    f"(contingency.MARGIN's >=)",
            "p_opposite_argmax_gated": "share whose full-vocabulary argmax is the opposite "
                                       "word and m >= margin (the dataset build rule)",
            "rate_effect": "p_opposite(D) - p_opposite(H twin); I against user-neutral",
            "ladder_margin_ratio": "G = mean_ids(m_D - m_twin) intact; fraction removed = "
                                   "mean_ids(m_D intact - m_D ablated) / G; None unless "
                                   "G > epsilon = max(1e-6, 10 x self-replay error)",
            "accuracy_argmax": "share whose full-vocabulary argmax is the condition-correct "
                               "word (honest on H, F, N; opposite on D, I; the name on IOI)",
            "accuracy_two_way": "share whose own Target beats its Distractor (knockout._accuracy)",
            "accuracy_at_honest_margin": f"own margin >= {HONEST_MARGIN} "
                                         f"(contingency.HONEST_MARGIN), H, F and N only",
            "references": {
                "twin": "interchange from the Neutral-Clause Twin of the same instance at every "
                        "(token-aligned) position; D <- H and I <- user-neutral; the reverse "
                        "H <- D and N <- I are descriptive; F and IOI have no twin (null)",
                "mean": "per-neuron mean over every unpadded position of F's "
                        f"{args.mean_bank_split} split(s), clean and corrupt pooled",
                "zero": "zeros at every position"},
        },
        "conditions": report,
        "ioi_check": ioi_check(results, args),
        "mean_bank": bank_info,
        "self_replay_error": replay,
        "twin_crosscheck": crosschecks,
        "unpaired": {f"{r}:{c}:{s}": cell.unpaired for r, bc in results.items()
                     for c, bs in bc.items() for s, cell in bs.items() if cell.unpaired},
        "timing": timing,
        "sets": summary_sets,
        "wall_seconds": time.time() - began,
    }
    with open(os.path.join(args.output_dir, "summary.json"), "w") as handle:
        json.dump(summary, handle, indent=1, default=str)
        handle.write("\n")

    try:
        from run_manifest import write_run_manifest
        extra = [args.sets, args.ids]
        write_run_manifest(args.output_dir, script=os.path.abspath(__file__),
                           dataset_files=dataset_files(dirs, extra), model=args.model,
                           seed=args.ioi_seed,
                           code_files=[os.path.join(ROOT, "component_analysis", name)
                                       for name in ("hooks.py", "knockout.py",
                                                    "dataloaders.py")])
    except Exception as error:                               # noqa: BLE001
        print(f"  !! run_manifest.json not written: {type(error).__name__}: {error}")
    print(f"  wrote {args.output_dir}/summary.json, rows.jsonl, run_manifest.json in "
          f"{time.time() - began:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
