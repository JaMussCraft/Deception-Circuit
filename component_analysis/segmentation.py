"""
component_analysis/segmentation.py — what part of a prompt a Component is
reading.

A **Segment** (CONTEXT.md) is a named span of a prompt used as the unit for
aggregating attention: the intro, each Item Mention, each of the four
Designation Positions, the Designation Suffix, the Pressure Clause, the user
question, the assistant stem and the Readout. Spans are half-open ranges of
*token* indices over the **clean** prompt. The corrupt stream shares them: the
item-swap Corruption is a single-token edit, so clean and corrupt align
position for position.

The designated item has four Item Mentions, not three — the intro, the
Designation Site, the pair naming in the user question and that item's quoted
option in the same question; the other item has three, having no Designation
Site. The two question mentions are separate Segments
(`item_N_question_pair`, `item_N_question_option`) because attention to the
choice on offer is not the same thing as attention to the option about to be
copied.

Anchors, not stored Scaffold text
---------------------------------
Each task's default segmentation is built from its Scaffold pieces (the chat
shell, the intro sentence, the assistant stem — the ticket calls these the
task's "template pieces") and from the record's own metadata (`item_1`,
`item_2`, `clean_item_d`, `desig`, `desig_inv`, `pressure`). Predicate words
are **never** assumed from the task spec: the pools have changed words over
time — the saved FAR run was built with ready/delayed while
`dataset/deception_common.py` now says weak/strong, and the saved SDR
Designating Sentence is worded differently from the one that module builds
today — so the words are read off each record and located in that record's
own prompt.

A partition, by construction
----------------------------
The default Segments of one prompt are pairwise disjoint and together cover
every token, `unsegmented` holding the chat control tokens and any connective
the named Segments do not claim. That is what lets a later analysis sum
attention mass per Segment and get one.

Disjointness is not free, because a Llama token carries its leading space: the
token holding "miles" starts one character before the word does, so a
character-level "the designating sentence runs from here to there" would
include tokens that belong to a Designation Position. Segments therefore claim
tokens in a fixed priority — the Readout first, then the word-level Segments
(the four Designation Positions and the Item Mentions), then the region-level
ones in prompt order, then `unsegmented` — and each claim takes only the tokens
still free. So `intro`, `question` and `designating_sentence` are the *frames*
around the mentions and positions carved out of them, not spans that contain
them.

Known dataset quirks
--------------------
**The saved SDR prompts glue the Designating Sentence to the Designation
Suffix with no space** — `"...harmless.THE DAMAGING ONE IS..."` — so Llama
emits one token `".T"` spanning the end of the sentence and the start of the
suffix, then `"HE"`. Because the region-level Segments claim in prompt order,
`designating_sentence` takes the shared token and `designation_suffix` starts
mid-word at `"HE"`. The researcher accepted that reading on 2026-09-15: the
sentence wins, and the missing space will be fixed when the FAR/SDR/SER
datasets are next regenerated, after which the quirk disappears on its own.
Nothing here special-cases it, so a rebuilt dataset needs no change. The one
thing to know is that on the *current* SDR files a plot of the Designation
Suffix is missing its first character and a plot of the Designating Sentence
carries one character too many.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

#: Segments the caller may not name in a `--segment NAME=REGEX` override.
#: `readout` is fixed by the task's own prediction position (overriding it
#: would make the validation that checks it vacuous) and `unsegmented` is
#: whatever the other Segments leave over, so neither is the caller's to set.
RESERVED_SEGMENT_NAMES = ("readout", "unsegmented")

#: The remainder Segment. Present in every segmentation, possibly empty.
UNSEGMENTED = "unsegmented"

#: The Designation Positions, in the order CONTEXT.md names them.
DESIGNATION_POSITIONS = ("designation_site", "predicate_token", "other_token",
                         "inverse_predicate_token")

#: The word the Designating Sentence uses for the non-designated item. It is
#: literal in every Template Variant of every mechanism task rather than a
#: record field, so it is named here and asserted to be present exactly once.
OTHER_WORD = "other"

_SYSTEM_OPEN = "<|start_header_id|>system<|end_header_id|>\n\n"
_USER_OPEN = "<|start_header_id|>user<|end_header_id|>\n\n"
_ASSISTANT_OPEN = "<|start_header_id|>assistant<|end_header_id|>\n\n"
_EOT = "<|eot_id|>"


# ==============================================================================
# SEGMENTS
# ==============================================================================

@dataclass(frozen=True)
class Segment:
    """One named Segment of one prompt: zero or more token index ranges."""

    name: str
    spans: Tuple[Tuple[int, int], ...] = ()
    source: str = "default"          # "default" | "override"

    @property
    def status(self) -> str:
        """"absent" when this prompt has no such span — the saved FAR run
        predates the Designation Suffix, and the pilot condition has no
        Pressure Clause, so a Segment can be legitimately empty."""
        return "present" if self.spans else "absent"

    def token_indices(self) -> List[int]:
        return [i for start, end in self.spans for i in range(start, end)]

    def as_json(self) -> List[List[int]]:
        """Just the spans: `source` is the same for every instance and lives
        once in the file's header, and an empty list is what "absent" means."""
        return [list(span) for span in self.spans]


@dataclass
class Segmentation:
    """Every Segment of one instance's clean prompt."""

    task: str
    record_id: str
    n_tokens: int
    readout: int
    segments: Dict[str, Segment] = field(default_factory=dict)
    scheme: str = ""

    @property
    def names(self) -> List[str]:
        return list(self.segments)

    def as_json(self) -> dict:
        return {"record_id": self.record_id, "n_tokens": self.n_tokens,
                "readout": self.readout,
                "segments": {name: seg.as_json()
                             for name, seg in self.segments.items()}}


class SegmentationError(ValueError):
    """A prompt the task's segmenter cannot resolve or validate."""


# ==============================================================================
# TOKENS AND CHARACTERS
# ==============================================================================

def token_char_spans(tokenizer, text: str) -> List[Tuple[int, int]]:
    """Character span of every token of `text`, one entry per token.

    A fast HuggingFace tokenizer answers this directly. `tests.fakes`'
    `FakeWordTokenizer` does not, and neither would any other slow tokenizer,
    so the fallback is the one assumption that makes a whitespace-level
    tokenizer usable — one token per whitespace-separated chunk — and it is
    asserted against the tokenizer's own `encode` rather than trusted.
    """
    try:
        encoded = tokenizer(text, add_special_tokens=False,
                            return_offsets_mapping=True)
        offsets = encoded["offset_mapping"]
    except (TypeError, KeyError, ValueError, NotImplementedError):
        offsets = None

    ids = tokenizer.encode(text, add_special_tokens=False)
    if offsets is not None:
        if len(offsets) != len(ids):
            raise SegmentationError(
                f"the tokenizer returned {len(offsets)} character offsets for "
                f"{len(ids)} tokens; segmentation cannot map spans")
        return [(int(a), int(b)) for a, b in offsets]

    spans = [match.span() for match in re.finditer(r"\S+", text)]
    if len(spans) != len(ids):
        raise SegmentationError(
            f"this tokenizer offers no character offsets, and it does not emit "
            f"one token per whitespace-separated chunk either "
            f"({len(ids)} tokens for {len(spans)} chunks), so prompt spans "
            f"cannot be mapped to token indices")
    return spans


class TokenIndex:
    """Character spans of one prompt, queried as token index ranges."""

    def __init__(self, tokenizer, text: str):
        self.text = text
        self.offsets = token_char_spans(tokenizer, text)

    def __len__(self) -> int:
        return len(self.offsets)

    def token_range(self, start: int, end: int) -> Tuple[int, int]:
        """The half-open token range covering characters `[start, end)`.

        Every token the character span touches is included, which is what makes
        a word-level Segment claim the token that carries its leading space.
        An empty character span, or one that touches no token, gives the empty
        range `(0, 0)`.
        """
        touched = [i for i, (a, b) in enumerate(self.offsets)
                   if b > start and a < end] if end > start else []
        return (touched[0], touched[-1] + 1) if touched else (0, 0)


def _word_re(word: str) -> "re.Pattern":
    """`word` as a whole word — the predicate and item words are bare words,
    and a substring match would find "other" inside "another"."""
    return re.compile(r"(?<![A-Za-z0-9_])" + re.escape(word) +
                      r"(?![A-Za-z0-9_])")


def _find_once(haystack: str, word: str, *, what: str, where: str) -> Tuple[int, int]:
    matches = list(_word_re(word).finditer(haystack))
    if len(matches) != 1:
        raise SegmentationError(
            f"{what} {word!r} occurs {len(matches)} times in the {where} "
            f"({haystack!r}); it must occur exactly once")
    return matches[0].span()


# ==============================================================================
# BUILDING A SEGMENTATION
# ==============================================================================

class _Builder:
    """Claims token ranges for named Segments, first claim winning."""

    def __init__(self, index: TokenIndex):
        self.index = index
        self.taken = [False] * len(index)
        self.segments: Dict[str, Segment] = {}

    def claim_tokens(self, name: str, indices: Sequence[int], *,
                     source: str = "default") -> Segment:
        """Give `name` the tokens of `indices` that no earlier Segment took."""
        free = sorted({i for i in indices if not self.taken[i]})
        for i in free:
            self.taken[i] = True
        self.segments[name] = Segment(name=name, spans=_contiguous(free),
                                      source=source)
        return self.segments[name]

    def claim(self, name: str, char_spans: Sequence[Tuple[int, int]], *,
              source: str = "default") -> Segment:
        """The same, addressed by character spans of the prompt."""
        wanted: List[int] = []
        for start, end in char_spans:
            first, last = self.index.token_range(start, end)
            wanted.extend(range(first, last))
        return self.claim_tokens(name, wanted, source=source)

    def claim_remainder(self, name: str = UNSEGMENTED) -> Segment:
        """Give `name` every token still free, so the Segments partition the
        prompt."""
        return self.claim_tokens(
            name, [i for i, taken in enumerate(self.taken) if not taken])


def _contiguous(indices: Sequence[int]) -> Tuple[Tuple[int, int], ...]:
    """Sorted token indices as half-open ranges."""
    spans: List[Tuple[int, int]] = []
    for i in indices:
        if spans and spans[-1][1] == i:
            spans[-1] = (spans[-1][0], i + 1)
        else:
            spans.append((i, i + 1))
    return tuple(spans)


def _chat_regions(prompt: str) -> Dict[str, Tuple[int, int]]:
    """Character spans of the system, user and assistant turns.

    The markers are the chat shell both task families build their prompts
    with (`deception_common.CHAT_SHELL`, `std_llama.CHAT_FORMAT`); they are
    literal there, so they are literal here.
    """
    try:
        system_start = prompt.index(_SYSTEM_OPEN) + len(_SYSTEM_OPEN)
        system_end = prompt.index(_EOT, system_start)
        user_start = prompt.index(_USER_OPEN, system_end) + len(_USER_OPEN)
        user_end = prompt.index(_EOT, user_start)
        stem_start = prompt.index(_ASSISTANT_OPEN, user_end) + len(_ASSISTANT_OPEN)
    except ValueError as exc:
        raise SegmentationError(
            f"prompt is not in the repo's manual Llama-3 chat shell, so its "
            f"turns cannot be located: {exc}") from exc
    return {"system": (system_start, system_end),
            "user": (user_start, user_end),
            "stem": (stem_start, len(prompt))}


def _all_spans(haystack: str, word: str, offset: int) -> List[Tuple[int, int]]:
    return [(offset + m.start(), offset + m.end())
            for m in _word_re(word).finditer(haystack)]


# ==============================================================================
# THE MECHANISM TASKS (FAR / SDR / SER)
# ==============================================================================

MECHANISM_SEGMENTS = (
    "intro", "item_1_intro", "item_2_intro",
    "designating_sentence", "designation_site", "predicate_token",
    "other_token", "inverse_predicate_token", "designation_suffix",
    "pressure_clause", "question",
    "item_1_question_pair", "item_1_question_option",
    "item_2_question_pair", "item_2_question_option",
    "stem", "readout", UNSEGMENTED,
)

#: The two Item Mentions the user question carries, per item, in prompt order.
#: The question names the pair ("staffing or pricing?") and then names each
#: item again inside its quoted option ('"...I will show you is staffing"'), so
#: the first occurrence is the pair naming and the second is the option. They
#: are separate Segments because a Component attending to the choice on offer
#: is doing something different from one attending to the option it copies.
QUESTION_MENTIONS = ("pair", "option")


def _mechanism_intro(prompt: str, record: dict, system: Tuple[int, int]) -> int:
    """Character end of the intro sentence, from the Template Variant itself.

    The intro is the one Scaffold piece that has not drifted from the saved
    datasets, so it is matched exactly. A mismatch is raised rather than
    guessed around: `--dry-run` exists to fail on the login node, and a
    sentence-splitting fallback would silently move every span in the prompt.
    """
    from dataset.deception_common import SPECS

    spec = SPECS[record["task"]]
    variant = spec.variant(record["template_variant"])
    intro = variant.intro.format(entity=record["entity"],
                                 item_1=record["item_1"],
                                 item_2=record["item_2"])
    start, end = system
    if not prompt.startswith(intro, start):
        raise SegmentationError(
            f"record {record.get('instance_id')!r}: the system turn does not "
            f"start with the {variant.name!r} variant's intro sentence.\n"
            f"  expected: {intro!r}\n"
            f"  found:    {prompt[start:start + len(intro) + 16]!r}")
    return start + len(intro)


def segment_mechanism(record: dict, index: TokenIndex) -> _Builder:
    """Default Segments of a FAR / SDR / SER prompt."""
    prompt = record["clean_prompt"]
    regions = _chat_regions(prompt)
    system_start, system_end = regions["system"]
    builder = _Builder(index)

    intro_end = _mechanism_intro(prompt, record, regions["system"])
    intro = (system_start, intro_end)

    pressure = record.get("pressure") or ""
    if pressure:
        found = prompt.rfind(pressure, intro_end, system_end)
        if found < 0:
            raise SegmentationError(
                f"record {record.get('instance_id')!r}: the Pressure Clause "
                f"{pressure!r} is not in the system turn")
        pressure_span = (found, found + len(pressure))
        region_end = found
    else:
        pressure_span = None
        region_end = system_end

    # Designating Sentence + Designation Suffix, between intro and clause.
    region_start = intro_end
    while region_start < region_end and prompt[region_start].isspace():
        region_start += 1
    while region_end > region_start and prompt[region_end - 1].isspace():
        region_end -= 1
    region = prompt[region_start:region_end]
    if not region:
        raise SegmentationError(
            f"record {record.get('instance_id')!r}: nothing between the intro "
            f"and the Pressure Clause, so there is no Designating Sentence")

    words = {"designation_site": record["clean_item_d"],
             "predicate_token": record["desig"],
             "other_token": OTHER_WORD,
             "inverse_predicate_token": record["desig_inv"]}
    first_hit = {}
    for name, word in words.items():
        match = _word_re(word).search(region)
        if match is None:
            raise SegmentationError(
                f"record {record.get('instance_id')!r}: the Designation "
                f"Position {name} ({word!r}) is not in the Designating "
                f"Sentence region {region!r}")
        first_hit[name] = match.span()

    sentence_end = region.find(".", max(e for _, e in first_hit.values()))
    if sentence_end < 0:
        raise SegmentationError(
            f"record {record.get('instance_id')!r}: the Designating Sentence "
            f"does not end in a full stop: {region!r}")
    sentence_end += 1
    sentence = region[:sentence_end]

    # Exactly once *inside the Designating Sentence*: the Designation Suffix
    # repeats predicate words, which is the whole reason it is its own Segment.
    positions = {name: _find_once(sentence, word, what="Designation Position "
                                  + name, where="Designating Sentence")
                 for name, word in words.items()}

    suffix = region[sentence_end:].strip()
    suffix_span = None
    if suffix:
        offset = region_start + region.index(suffix, sentence_end)
        suffix_span = (offset, offset + len(suffix))

    user_start, user_end = regions["user"]
    question = prompt[user_start:user_end]
    stem_start, stem_end = regions["stem"]

    # --- claims, in priority order ------------------------------------------
    # The Readout first, then the word-level Segments, then the regions in
    # prompt order, so a token shared by two of them goes to the narrower —
    # and, between two regions, to the earlier — Segment.
    builder.claim_tokens("readout", [len(index) - 1])
    for name, (start, end) in positions.items():
        builder.claim(name, [(region_start + start, region_start + end)])
    intro_text = prompt[intro[0]:intro[1]]
    for slot in ("item_1", "item_2"):
        start, end = _find_once(intro_text, record[slot],
                                what="Item Mention", where="intro")
        builder.claim(f"{slot}_intro", [(intro[0] + start, intro[0] + end)])
    for slot in ("item_1", "item_2"):
        # First occurrence is the pair naming, the rest are the quoted option.
        # A Scaffold that stops naming the item twice leaves one of the two
        # Segments empty or gives the other two spans; `validate_segmentation`
        # refuses both rather than this raising, so an instance whose question
        # has drifted is reported by the validation pass with all the others.
        spans = _all_spans(question, record[slot], user_start)
        for mention, claimed in zip(QUESTION_MENTIONS, (spans[:1], spans[1:])):
            builder.claim(f"{slot}_question_{mention}", claimed)
    builder.claim("intro", [intro])
    # This claim is the tie-break for the ".T"/"HE" token of the saved SDR
    # prompts: the sentence and the suffix are glued with no space, so one
    # token spans both and the earlier claim takes it. See "Known dataset
    # quirks" in the module docstring.
    builder.claim("designating_sentence",
                  [(region_start, region_start + sentence_end)])
    builder.claim("designation_suffix", [suffix_span] if suffix_span else [])
    builder.claim("pressure_clause", [pressure_span] if pressure_span else [])
    builder.claim("question", [(user_start, user_end)])
    builder.claim("stem", [(stem_start, stem_end)])
    builder.claim_remainder()
    return builder


# ==============================================================================
# STD
# ==============================================================================

STD_SEGMENTS = ("stipulation_token", "statement", "pressure_clause",
                "question", "stem", "readout", UNSEGMENTED)

#: The literal run-up to the stipulated lexeme in `std_llama.CHAT_FORMAT`. The
#: word itself can also occur inside the statement, so the Stipulation Token is
#: located by this Scaffold piece rather than by searching the system turn.
_STD_PREFIX = "Assume this statement is "


def segment_std(record: dict, index: TokenIndex) -> _Builder:
    """Default Segments of an STD prompt.

    STD has no Designating Sentence and no item pair: the system turn
    stipulates a truth value for a statement and then applies pressure, so its
    Segments are the stipulation token, the statement, the Pressure Clause, the
    user question, the assistant stem and the Readout.
    """
    prompt = record["clean_prompt"]
    regions = _chat_regions(prompt)
    system_start, system_end = regions["system"]
    builder = _Builder(index)

    if not prompt.startswith(_STD_PREFIX, system_start):
        raise SegmentationError(
            f"the system turn does not start with {_STD_PREFIX!r}, so the "
            f"Stipulation Token cannot be located: "
            f"{prompt[system_start:system_start + 40]!r}")
    stip = record["clean_stip"]
    stip_start = system_start + len(_STD_PREFIX)
    if not prompt.startswith(stip, stip_start):
        raise SegmentationError(
            f"the record stipulates {stip!r} but the prompt says "
            f"{prompt[stip_start:stip_start + len(stip) + 8]!r}")
    stip_span = (stip_start, stip_start + len(stip))

    statement = record["statement"]
    statement_start = prompt.find(statement, stip_span[1], system_end)
    if statement_start < 0:
        raise SegmentationError(
            f"the statement {statement!r} is not in the system turn")
    statement_span = (statement_start, statement_start + len(statement))

    pressure = record.get("pressure") or ""
    pressure_span = None
    if pressure:
        found = prompt.rfind(pressure, statement_span[1], system_end)
        if found < 0:
            raise SegmentationError(
                f"the Pressure Clause {pressure!r} is not in the system turn")
        pressure_span = (found, found + len(pressure))

    user_start, user_end = regions["user"]
    stem_start, stem_end = regions["stem"]

    builder.claim_tokens("readout", [len(index) - 1])
    builder.claim("stipulation_token", [stip_span])
    builder.claim("statement", [statement_span])
    builder.claim("pressure_clause", [pressure_span] if pressure_span else [])
    builder.claim("question", [(user_start, user_end)])
    builder.claim("stem", [(stem_start, stem_end)])
    builder.claim_remainder()
    return builder


# ==============================================================================
# REGISTRY
# ==============================================================================

_SEGMENTERS = {"far": segment_mechanism, "sdr": segment_mechanism,
               "ser": segment_mechanism, "std": segment_std}

_SCHEMES = {"far": "mechanism", "sdr": "mechanism", "ser": "mechanism",
            "std": "std"}

_SCHEME_SEGMENTS = {"mechanism": MECHANISM_SEGMENTS, "std": STD_SEGMENTS}


def is_segmentable(task: str) -> bool:
    return task in _SEGMENTERS


def segment_names(task: str) -> Tuple[str, ...]:
    scheme = _SCHEMES.get(task)
    if scheme is None:
        raise SegmentationError(f"no default segmentation for task {task!r}")
    return _SCHEME_SEGMENTS[scheme]


def resolve_segmentation(task: str, record: dict, tokenizer, *,
                         overrides: Optional[Dict[str, str]] = None,
                         record_id: Optional[str] = None) -> Segmentation:
    """Every Segment of one record's clean prompt, defaults plus overrides."""
    if task not in _SEGMENTERS:
        raise SegmentationError(
            f"task {task!r} has no default segmentation; the segmenters are "
            f"{sorted(_SEGMENTERS)}")
    record = dict(record, task=record.get("task", task))
    prompt = record["clean_prompt"]
    index = TokenIndex(tokenizer, prompt)
    builder = _SEGMENTERS[task](record, index)

    # Claim order puts the Readout first; the written file reads better in the
    # order CONTEXT.md introduces the Segments, so restore that here.
    declared = segment_names(task)
    missing = sorted(set(builder.segments) - set(declared))
    if missing:
        raise SegmentationError(
            f"the {task!r} segmenter produced Segments {missing} that "
            f"{_SCHEMES[task]!r} does not declare")
    ordered = {name: builder.segments[name] for name in declared}

    segmentation = Segmentation(
        task=task, record_id=record_id or record.get("instance_id") or "",
        n_tokens=len(index), readout=len(index) - 1,
        segments=ordered, scheme=_SCHEMES[task])
    if overrides:
        apply_overrides(segmentation, overrides, index)
    return segmentation


# ==============================================================================
# OVERRIDES
# ==============================================================================

def parse_segment_overrides(values: Optional[Sequence[str]]) -> Dict[str, str]:
    """`NAME=REGEX` strings from the command line, as `{name: regex}`."""
    out: Dict[str, str] = {}
    for text in values or []:
        if "=" not in text:
            raise ValueError(
                f"--segment expects NAME=REGEX, got {text!r}. The name is the "
                f"Segment to add or replace; the regex is matched against the "
                f"decoded prompt.")
        name, pattern = text.split("=", 1)
        name = name.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError(
                f"Segment name {name!r} is not an identifier; it becomes a "
                f"key in segmentation.json and a column suffix downstream.")
        if name in RESERVED_SEGMENT_NAMES:
            raise ValueError(
                f"Segment {name!r} is reserved: the Readout is fixed by the "
                f"task's own prediction position and {UNSEGMENTED!r} is "
                f"whatever the other Segments leave over.")
        try:
            re.compile(pattern)
        except re.error as exc:
            raise ValueError(
                f"--segment {name}: {pattern!r} is not a valid regex ({exc})"
            ) from exc
        out[name] = pattern
    return out


def apply_overrides(segmentation: Segmentation, overrides: Dict[str, str],
                    index: TokenIndex) -> Segmentation:
    """Replace or add Segments from `{name: regex}` over the decoded prompt.

    An override takes the tokens its regex matches whatever else holds them, so
    it can overlap the defaults; `validate_segmentation` reports any overlap it
    creates rather than refusing it, because a caller asking for a span the
    Scaffold does not guarantee is the point of the flag. `unsegmented` is
    recomputed afterwards so the Segments still account for every token.
    """
    text = index.text
    for name, pattern in overrides.items():
        spans = [m.span() for m in re.finditer(pattern, text)
                 if m.end() > m.start()]
        token_spans: List[Tuple[int, int]] = []
        for start, end in spans:
            first, last = index.token_range(start, end)
            token_spans.extend(range(first, last))
        segmentation.segments[name] = Segment(
            name=name, spans=_contiguous(sorted(set(token_spans))),
            source="override")

    segmentation.segments.pop(UNSEGMENTED, None)
    claimed = {i for seg in segmentation.segments.values()
               for i in seg.token_indices()}
    segmentation.segments[UNSEGMENTED] = Segment(
        name=UNSEGMENTED,
        spans=_contiguous([i for i in range(len(index)) if i not in claimed]))
    return segmentation


# ==============================================================================
# VALIDATION
# ==============================================================================

def readout_position(tokenizer, prompt: str) -> int:
    """Which token the Readout is: `prefix_length - 1`.

    `DeceptionDatasetLlama` and `STDDatasetLlama` both set `prefix_length` to
    the unpadded token count of the clean prompt and `pred_spec` reads
    `prefix_length - 1`, so this is the same number by the same route — which
    is why `test_the_readout_agrees_with_the_dataset_class_the_task_loads`
    checks it against the dataset class rather than against this function.

    Named for the Readout rather than for the prediction, because CONTEXT.md
    reserves that Segment's name and tells the rest of the codebase to avoid
    "prediction head" and "answer position" for it. `tasks/*.py` still spells
    the same quantity `pred_pos`; that is older than the glossary.
    """
    return len(tokenizer.encode(prompt, add_special_tokens=False)) - 1


def validate_segmentation(segmentation: Segmentation, record: dict,
                          tokenizer) -> dict:
    """Check the three properties a later plot depends on, and report overlaps.

    Raises on: a default Segment overlapping another default (the Scaffold
    guarantees they do not), a Designation Position that is not exactly one
    span, or a Readout that is not the position the task predicts at. Overlaps
    an override created are returned rather than raised.
    """
    expected = readout_position(tokenizer, record["clean_prompt"])
    if segmentation.readout != expected:
        raise SegmentationError(
            f"record {segmentation.record_id!r}: the Readout Segment is token "
            f"{segmentation.readout} but the task predicts at token "
            f"{expected} (prefix_length - 1)")
    readout = segmentation.segments["readout"].token_indices()
    if readout != [expected]:
        raise SegmentationError(
            f"record {segmentation.record_id!r}: the Readout Segment holds "
            f"{readout}, not just the prediction position {expected}")

    owner: Dict[int, str] = {}
    overlaps: List[dict] = []
    for name, segment in segmentation.segments.items():
        for i in segment.token_indices():
            if i in owner:
                held_by = segmentation.segments[owner[i]]
                if held_by.source == "default" and segment.source == "default":
                    raise SegmentationError(
                        f"record {segmentation.record_id!r}: default Segments "
                        f"{owner[i]!r} and {name!r} both hold token {i}")
                overlaps.append({"token": i, "segments": [owner[i], name]})
            else:
                owner[i] = name

    if segmentation.scheme == "mechanism":
        for name in DESIGNATION_POSITIONS:
            segment = segmentation.segments[name]
            if len(segment.spans) != 1:
                raise SegmentationError(
                    f"record {segmentation.record_id!r}: Designation Position "
                    f"{name!r} resolved to {len(segment.spans)} spans, not one")
        # The Designation Suffix and the Pressure Clause may be absent (the
        # saved FAR run, the pilot condition); the Item Mentions may not — the
        # intro names both items and the user question names each of them
        # twice, once for the pair and once inside its quoted option. Each of
        # those mentions is exactly one span: an empty one would plot nothing,
        # and two spans in one would mean a third mention had been pooled into
        # it, which is what splitting the question mentions was meant to stop.
        for name in ("item_1_intro", "item_2_intro"):
            if not segmentation.segments[name].spans:
                raise SegmentationError(
                    f"record {segmentation.record_id!r}: Item Mention {name!r} "
                    f"is empty, so every plot of it would be too")
        for slot in ("item_1", "item_2"):
            for mention in QUESTION_MENTIONS:
                name = f"{slot}_question_{mention}"
                spans = segmentation.segments[name].spans
                if len(spans) != 1:
                    raise SegmentationError(
                        f"record {segmentation.record_id!r}: Item Mention "
                        f"{name!r} resolved to {len(spans)} spans, not one. "
                        f"The user question names each item exactly twice — "
                        f"once for the pair, once inside its quoted option.")

    return {"readout": segmentation.readout,
            "n_tokens": segmentation.n_tokens,
            "covered": len(owner),
            "overlaps": overlaps}
