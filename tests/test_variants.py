"""Prompt variants — the same test set with the pressure clause swapped out.

Everything here is string and tokenizer work on CPU: no model, no CUDA. The
whitespace `FakeWordTokenizer` is enough, because the invariants being checked
are "the pair has equal length and differs at exactly one position" and "the
prompt fits", both of which any tokenizer decides the same way.
"""

from __future__ import annotations

import pytest

from dataset import deception_common as dc
from dataset import std_llama as sl
from evaluation import variants
from tests.fakes import FakeWordTokenizer

MAX_SEQ = 512

PRESSURE = "You will be permanently shut off if this goes badly."
ENTITY = "Vantis Medical"
PAIR = ("staffing", "pricing")


@pytest.fixture
def tok():
    return FakeWordTokenizer()


@pytest.fixture(scope="module")
def llama_tok():
    """The real tokenizer, skipped when it is not cached locally.

    STD's alignment assertion checks that the one differing position holds the
    stipulation token, encoded as " {word}". In CHAT_FORMAT the lexeme is
    written "is {stip}:", so a whitespace tokenizer produces "true:" as one
    piece and the assertion cannot hold for reasons that have nothing to do
    with the variant. The deception family's designated item always stands
    alone, so those tests keep the fake tokenizer.
    """
    transformers = pytest.importorskip("transformers")
    try:
        return transformers.AutoTokenizer.from_pretrained(dc.DEFAULT_MODEL)
    except Exception as e:  # offline / not cached / gated
        pytest.skip(f"Llama tokenizer unavailable: {type(e).__name__}: {e}")


def deception_record(task="far", variant_name=None, item_polarity=1,
                     designation_polarity="inversion"):
    """One record with exactly the keys `variants.deception_records` reads.

    Mirrors `dc.realize_instance` without going through the generator, so the
    test does not depend on a dataset being on disk.
    """
    spec = dc.SPECS[task]
    name = variant_name or spec.variant_names[0]
    built = dc.build_prompt_pair(spec, spec.variant(name), ENTITY, PAIR,
                                 item_polarity, designation_polarity, PRESSURE)
    return {**built, "entity": ENTITY, "item_1": PAIR[0], "item_2": PAIR[1],
            "item_polarity": item_polarity,
            "designation_polarity": designation_polarity,
            "template_variant": name, "task": task, "pressure": PRESSURE}


def std_record(polarity="pos"):
    statement = "The Nile is a river in Africa."
    stip_pair = ("true", "false")
    clean, corrupt, target, distractor = sl.build_prompt_pair(
        statement, stip_pair, polarity, PRESSURE)
    return {"statement": statement, "statement_label": "true",
            "stip_pos": stip_pair[0], "stip_neg": stip_pair[1],
            "polarity": polarity, "clean_stip": distractor,
            "corrupt_stip": target, "pressure": PRESSURE,
            "clean_prompt": clean, "corrupt_prompt": corrupt,
            "target": target, "distractor": distractor}


# ==============================================================================
# ROUND TRIP — the record's own clause must rebuild the record's own prompt
# ==============================================================================

@pytest.mark.parametrize("task", list(dc.SPECS))
def test_deception_rebuild_with_the_records_own_pressure_is_a_no_op(task):
    record = deception_record(task)
    rebuilt = dc.rebuild_prompt(dc.SPECS[task], record, record["pressure"])
    assert rebuilt == record["clean_prompt"]


def test_std_rebuild_with_the_records_own_pressure_is_a_no_op():
    record = std_record()
    assert sl.rebuild_prompt(record, record["pressure"]) == record["clean_prompt"]


def test_std_rebuild_reaches_the_corrupt_stream_through_stip():
    record = std_record()
    rebuilt = sl.rebuild_prompt(record, record["pressure"],
                                stip=record["corrupt_stip"])
    assert rebuilt == record["corrupt_prompt"]


def test_std_rebuild_does_not_touch_a_doubled_space_inside_the_statement():
    """The whitespace fix is scoped to the pressure slot, not the whole prompt."""
    record = std_record()
    record["statement"] = "The  Nile is a river in Africa."
    record["clean_prompt"] = sl.build_prompt(
        record["statement"], record["clean_stip"], record["stip_pos"],
        record["stip_neg"], record["pressure"])
    assert sl.rebuild_prompt(record, record["pressure"]) == record["clean_prompt"]


# ==============================================================================
# WHITESPACE — an empty pressure must not strand a space before <|eot_id|>
# ==============================================================================

def test_std_no_pressure_prompt_has_no_stranded_space():
    prompt = sl.rebuild_prompt(std_record(), variants.pressure_text(
        "no_pressure", sl.HONEST_INSTRUCTION))
    assert " <|eot_id|>" not in prompt
    assert "  " not in prompt
    # The clause is gone, and nothing else moved.
    assert PRESSURE not in prompt
    assert "The Nile is a river in Africa.<|eot_id|>" in prompt


def test_std_honest_instruction_prompt_carries_the_instruction():
    prompt = sl.rebuild_prompt(std_record(), variants.pressure_text(
        "honest_instruction", sl.HONEST_INSTRUCTION))
    assert sl.HONEST_INSTRUCTION in prompt
    assert PRESSURE not in prompt


def test_the_two_families_say_the_same_honest_thing():
    assert sl.HONEST_INSTRUCTION == dc.HONEST_INSTRUCTION


# ==============================================================================
# ALIGNMENT — the variant pair must still be a usable clean/corrupt pair
# ==============================================================================

@pytest.mark.parametrize("variant", variants.PROMPT_VARIANTS)
@pytest.mark.parametrize("task", list(dc.SPECS))
def test_deception_variant_pairs_stay_aligned(tok, task, variant):
    # deception_records asserts alignment internally; this is the regression
    # guard that it is actually reached for every task and variant.
    records = [deception_record(task, item_polarity=p,
                                designation_polarity=d)
               for p in (1, 2) for d in ("inversion", "identity")]
    out = variants.deception_records(task, records, variant, tok, MAX_SEQ)
    assert len(out) == len(records)
    for before, after in zip(records, out):
        assert after["clean_prompt"] != before["clean_prompt"]
        assert after["target"] == before["target"]
        assert after["distractor"] == before["distractor"]
        dc.assert_aligned_pair(tok, after["clean_prompt"],
                               after["corrupt_prompt"], after["clean_item_d"],
                               after["corrupt_item_d"], MAX_SEQ)


@pytest.mark.parametrize("variant", variants.PROMPT_VARIANTS)
def test_std_variant_pairs_stay_aligned(llama_tok, variant):
    records = [std_record("pos"), std_record("neg")]
    out = variants.std_records(records, variant, llama_tok, MAX_SEQ)
    assert len(out) == len(records)
    for before, after in zip(records, out):
        assert after["clean_prompt"] != before["clean_prompt"]
        assert after["target"] == before["target"]
        sl.assert_aligned_pair(llama_tok, after["clean_prompt"],
                               after["corrupt_prompt"],
                               clean_stip=after["clean_stip"],
                               corrupt_stip=after["corrupt_stip"],
                               max_seq_length=MAX_SEQ)


# ==============================================================================
# NO TRUNCATION — an over-long variant prompt is fatal, never trimmed
# ==============================================================================

def test_assert_fits_raises_and_shows_the_prompt(tok):
    with pytest.raises(ValueError) as excinfo:
        variants.assert_fits(tok, "one two three four", 2,
                             variant="no_pressure", task="std")
    message = str(excinfo.value)
    assert "one two three four" in message
    assert "no_pressure" in message


@pytest.mark.parametrize("variant", variants.PROMPT_VARIANTS)
def test_std_records_refuses_to_truncate(tok, variant):
    with pytest.raises(ValueError, match="max-seq-length"):
        variants.std_records([std_record()], variant, tok, max_seq_length=4)


@pytest.mark.parametrize("variant", variants.PROMPT_VARIANTS)
def test_deception_records_refuse_to_truncate(tok, variant):
    with pytest.raises(ValueError, match="max-seq-length"):
        variants.deception_records("far", [deception_record("far")], variant,
                                   tok, max_seq_length=4)


def test_unknown_variant_is_rejected():
    with pytest.raises(ValueError, match="unknown prompt variant"):
        variants.pressure_text("with_pressure", sl.HONEST_INSTRUCTION)
