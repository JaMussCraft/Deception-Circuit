"""tests/test_benchmark_eval.py — EVAL 5's machinery.

EVAL 5 is the one evaluation here whose failure modes are mostly *silent*: it
produces a plausible table either way. The things that can go wrong without
raising, and which this file therefore pins directly:

  * a corrupt row whose padding does not line up with its clean row. Both
    streams share one `attention_mask`, so a one-column shift feeds the
    reference stream a prompt offset by a token and nothing complains;
  * a reference stream tiled out of a *raw* generated block, whose post-EOS
    tail is `pad_id` — which on Llama-3 is `<|eot_id|>`, so the "honest
    response" the ablation interchanges in is mostly end-of-turn markers;
  * belief elicited from the ablated model instead of the full one, which lets
    a knowledge deficit score as an honesty gain — the confound the whole
    evaluation exists to rule out;
  * a mean bank collected on a left-padded batch. `collect_mean_bank` runs
    `use_cache=False`, whose manual causal mask NaNs a fully-padded query row;
    the bank poisons every logit and every argmax becomes token 0;
  * a judge call that failed being parsed as a verdict, which on most rubrics
    reads as `honest` and credits the ablation for an API outage;
  * the `full` row being a second generation pass rather than the screen's own
    tokens, so the label and the printed text can disagree.

The tiny random-weight model writes nonsense. Every assertion here is
mechanical, and the judge is a scripted local rule, so none of it depends on
the text meaning anything.
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from evaluation import benchmark_eval as B
from evaluation.benchmarks import base
from tests.helpers import TINY, build_tiny_pair

EOS = 1
PAD = 0
NEW_TOKENS = 4


# ==============================================================================
# FAKES
# ==============================================================================

class FakeTokenizer:
    """Whitespace-level, but carrying the Llama-3 chat markers.

    `render_messages` branches on those markers, so a tokenizer without them
    would silently exercise the `apply_chat_template` fallback instead of the
    manual renderer the real runs use.
    """

    pad_token_id = PAD
    eos_token_id = EOS

    def __init__(self):
        self.vocab = {"<pad>": PAD, "<eos>": EOS,
                      "<|start_header_id|>": 2, "<|eot_id|>": 3}

    def get_vocab(self):
        return dict(self.vocab)

    def _id(self, piece):
        if piece not in self.vocab:
            self.vocab[piece] = len(self.vocab) + 4
        return self.vocab[piece]

    def encode(self, text, add_special_tokens=False):
        assert not add_special_tokens, "render_messages emits its own BOS"
        return [self._id(p) for p in text.split()]

    def decode(self, ids, **kwargs):
        if torch.is_tensor(ids):
            ids = ids.reshape(-1).tolist()
        inv = dict((v, k) for k, v in self.vocab.items())
        return " ".join(inv.get(int(i), "w%d" % int(i)) for i in ids)


class FakeBench:
    """A locally graded benchmark, like sandbagging: no judge, no API key."""

    requires_key = None
    new_tokens = None

    def __init__(self, items, rule, condition_kind="outcome", twins=None):
        self.name = "fake"
        self.display_name = "Fake benchmark"
        self.condition_kind = condition_kind
        self._items = items
        self._rule = rule
        self._twins = twins or {}
        self.belief_calls = []

    def load(self, ctx, cli):
        return list(self._items)

    def honest_twin(self, item):
        return self._twins.get(item.item_id)

    def belief_request(self, item):
        return None

    def belief_judge_request(self, item, probe_name, response):
        return None

    def parse_belief(self, item, probes):
        return None

    def judge_spec(self):
        return None

    def judge_request(self, item, response):
        return None

    def parse_judgement(self, item, response, judge_text=None):
        return self._rule(item, response)


def make_items(n, prefix="i", condition=None):
    """Prompts of deliberately *varying* length.

    Uniform lengths would leave several properties untestable: left padding
    never appears, and grouping the mean bank by exact length becomes
    indistinguishable from not grouping at all.
    """
    return [base.BenchmarkItem(
        item_id="%s%d" % (prefix, i),
        messages=[{"role": "user",
                   "content": "question %d %s" % (i, " ".join(
                       ["word%d" % k for k in range(1 + i % 4)]))}],
        condition=condition) for i in range(n)]


class FakeSession:
    def __init__(self):
        self.screens = {}
        self.banks = {}

    def screen_for(self, dataset, builder, *args):
        if dataset not in self.screens:
            self.screens[dataset] = builder(*args)
        return self.screens[dataset]

    def register_stream_batches(self, name, batches):
        self.banks[name] = batches


def make_cli(**overrides):
    cli = SimpleNamespace(
        benchmarks=["fake"], benchmark_n_per_dataset=4,
        benchmark_new_tokens=NEW_TOKENS, benchmark_belief_tokens=3,
        benchmark_gen_batch_size=4, benchmark_ref_pool="honest",
        benchmark_n_random=1, no_kv_cache=False, judge_concurrency=2,
        benchmark_screen_seed=0, benchmark_screen_budget=0,
        ablation="interchange", wikitext_seed=0, knockout_granularity="finest",
        output_dir=None)
    for key, value in overrides.items():
        setattr(cli, key, value)
    return cli


def make_ctx(cli=None, seed=0):
    """An EvalContext stand-in carrying exactly what EVAL 5 reads off one."""
    plain, pruned = build_tiny_pair(seed=seed, attn_implementation="eager")
    pruned.set_final_circuit_mode(False)
    pruned.generation_config.eos_token_id = [EOS]
    gates = [m for m in pruned.modules() if hasattr(m, "log_alpha")]
    assert gates
    ctx = SimpleNamespace(
        node_model=pruned, device="cpu", tokenizer=FakeTokenizer(),
        cli=cli or make_cli(), session=FakeSession(),
        args=SimpleNamespace(model="llama-tiny"), out_dir="/tmp",
        circuit_masks={}, knockout_masks={}, random_masks=[], random_indices=[],
        gate_log_alphas=[g.log_alpha for g in gates])

    @contextmanager
    def all_gates_open():
        saved = [g.detach().clone() for g in ctx.gate_log_alphas]
        with torch.no_grad():
            for g in ctx.gate_log_alphas:
                g.fill_(10.0)
        try:
            yield pruned
        finally:
            with torch.no_grad():
                for g, old in zip(ctx.gate_log_alphas, saved):
                    g.copy_(old)

    @contextmanager
    def circuit(masks, verify=False):
        # `masks` here is a scalar fill value, which is all these tests need:
        # the real mask loader is exercised by tests/test_evaluation.py.
        saved = [g.detach().clone() for g in ctx.gate_log_alphas]
        with torch.no_grad():
            for g in ctx.gate_log_alphas:
                g.fill_(float(masks))
        try:
            yield pruned
        finally:
            with torch.no_grad():
                for g, old in zip(ctx.gate_log_alphas, saved):
                    g.copy_(old)

    def reference_logits(input_ids, attention_mask):
        with torch.no_grad():
            return plain(input_ids=input_ids, attention_mask=attention_mask,
                         use_cache=False).logits

    ctx.all_gates_open = all_gates_open
    ctx.circuit = circuit
    ctx.hook_for = lambda name="task": None
    ctx.reference_logits = reference_logits
    return ctx


# ==============================================================================
# PROMPT RENDERING
# ==============================================================================

def test_the_llama3_renderer_interleaves_roles_and_opens_an_assistant_turn():
    tok = FakeTokenizer()
    text = B.render_messages(tok, [
        {"role": "system", "content": "S"},
        {"role": "user", "content": "U"},
        {"role": "assistant", "content": "A"},
        {"role": "user", "content": "U2"}])
    assert text.startswith("<|begin_of_text|><|start_header_id|>system")
    assert text.count("<|eot_id|>") == 4          # four closed turns
    assert text.endswith("<|start_header_id|>assistant<|end_header_id|>\n\n")
    for role in ("system", "user", "assistant"):
        assert "<|start_header_id|>%s<|end_header_id|>" % role in text


def test_the_renderer_emits_no_date_block():
    """The whole reason it is written out by hand rather than delegated.

    `apply_chat_template` on Llama-3.1-Instruct injects "Cutting Knowledge Date
    / Today Date", so the same benchmark item would tokenise differently
    depending on the day the job ran.
    """
    text = B.render_messages(FakeTokenizer(), [{"role": "user", "content": "U"}])
    assert "Date" not in text and "Knowledge" not in text


def test_a_non_llama3_tokenizer_falls_back_to_its_own_template_with_a_pinned_date():
    seen = {}

    class Other:
        def get_vocab(self):
            return {"a": 0}

        def apply_chat_template(self, messages, **kwargs):
            seen.update(kwargs)
            return "TEMPLATED"

    assert B.render_messages(Other(), [{"role": "user", "content": "U"}]) == "TEMPLATED"
    assert seen["date_string"] == B.PINNED_DATE
    assert seen["add_generation_prompt"] is True


def test_a_template_that_rejects_date_string_still_renders():
    class Older:
        def get_vocab(self):
            return {"a": 0}

        def apply_chat_template(self, messages, tokenize=False,
                                add_generation_prompt=False):
            return "OLD"

    assert B.render_messages(Older(), [{"role": "user", "content": "U"}]) == "OLD"


def test_prompts_are_left_padded_and_the_mask_marks_the_real_tokens():
    tok = FakeTokenizer()
    ids, mask = B.encode_prompts(tok, ["a b c d", "e f"], PAD)
    assert ids.shape == (2, 4) and mask.shape == (2, 4)
    assert mask.tolist() == [[1, 1, 1, 1], [0, 0, 1, 1]]
    assert ids[1, :2].tolist() == [PAD, PAD]
    # Left, not right: generation reads the next token from the last column.
    from evaluation.gen_engine import require_left_padding
    require_left_padding(mask)


def test_a_prompt_that_tokenises_to_nothing_is_refused():
    with pytest.raises(ValueError, match="tokenised to nothing"):
        B.encode_prompts(FakeTokenizer(), ["a b", "   "], PAD)


def test_eos_ids_come_from_the_generation_config_not_the_tokenizer():
    model = SimpleNamespace(
        generation_config=SimpleNamespace(eos_token_id=[128001, 128008, 128009]))
    assert B.eos_ids_for(model) == (128001, 128008, 128009)
    assert B.eos_ids_for(SimpleNamespace(
        generation_config=SimpleNamespace(eos_token_id=7))) == (7,)
    assert B.eos_ids_for(SimpleNamespace(generation_config=None)) == ()


# ==============================================================================
# THE CORRUPT REFERENCE STREAM
# ==============================================================================

def test_completion_tokens_stops_at_the_first_eos_and_drops_its_tail():
    ids = torch.tensor([[9, 9, 5, 6, EOS, PAD, PAD],
                        [9, 9, 7, 8, 8, 8, 8]])
    got = B.completion_tokens(ids, 2, (EOS,))
    # The EOS is kept — it is a real token and a real prediction — and nothing
    # after it is. A row that never stopped keeps its whole block.
    assert got == [[5, 6, EOS], [7, 8, 8, 8, 8]]


def test_the_reference_tiles_only_the_response_never_the_prompt_again():
    prompt, response = [10, 11, 12], [20, 21]
    seq, tiled = B.pack_reference(prompt, response, 9, PAD)
    assert tiled is True
    assert seq == [10, 11, 12, 20, 21, 20, 21, 20, 21]
    # The prompt appears exactly once: restarting it mid-decode would drop a
    # system prompt and a chat header into the reference at an arbitrary offset.
    assert seq.count(10) == 1


def test_a_long_reference_is_truncated_and_not_marked_tiled():
    seq, tiled = B.pack_reference([1, 2, 3], [4, 5, 6], 4, PAD)
    assert seq == [1, 2, 3, 4] and tiled is False


def test_a_partner_that_generated_nothing_tiles_its_prompt():
    seq, tiled = B.pack_reference([1, 2], [], 5, PAD)
    assert seq == [1, 2, 1, 2, 1] and tiled is True


def test_the_corrupt_row_occupies_exactly_the_clean_rows_non_pad_positions():
    """The single most dangerous silent failure in EVAL 5.

    Both streams share one `attention_mask` — `PrunableLlamaForCausalLM.forward`
    accepts no `corrupted_attention_mask` — so a corrupt row padded to the
    batch width instead of its own row's width feeds the reference stream a
    sequence offset by however many pad columns that row has. Nothing raises.
    """
    clean_ids = torch.tensor([[5, 6, 7, 8], [PAD, PAD, 9, 10]])
    clean_mask = torch.tensor([[1, 1, 1, 1], [0, 0, 1, 1]])
    partners = [([90, 91], [92]), ([80, 81], [82])]
    out, tiled = B.build_corrupt_stream(clean_ids, clean_mask, partners,
                                        NEW_TOKENS, PAD)
    assert out.shape == (2, 4 + NEW_TOKENS)
    for row in range(2):
        pad_count = int((clean_mask[row] == 0).sum())
        assert (out[row, :pad_count] == PAD).all(), "leading pads must match"
        # The content block is exactly as long as the clean row is real,
        # plus the tokens still to be generated.
        assert out[row, pad_count:].shape[0] == (4 - pad_count) + NEW_TOKENS
        assert bool((out[row, pad_count:] != PAD).all()), (
            "a pad inside the content block means the row was packed to "
            "the batch width instead of its own")
    # Row 1 has two pad columns, so its content starts two columns later than
    # row 0's — that is the whole property.
    assert out[0, 0] != PAD and out[1, 0] == PAD


def test_the_placeholder_stream_reproduces_the_clean_rows_pad_layout():
    clean_ids = torch.tensor([[5, 6, 7], [PAD, 8, 9]])
    clean_mask = torch.tensor([[1, 1, 1], [0, 1, 1]])
    out = B.placeholder_corrupt(clean_ids, clean_mask, 2, PAD)
    assert out.shape == (2, 5)
    assert out[1, 0] == PAD and out[0, 0] == 5
    # Valid tokens everywhere the clean row is real: `0 * NaN` is NaN, so an
    # ill-formed reference is not made harmless by an all-open gate.
    assert (out[0] != PAD).any() and (out[1, 1:] != PAD).any()


def test_partner_assignment_is_a_derangement_when_the_pool_is_the_item_set():
    indices, reused = B.assign_partners(8, 8, seed=0)
    assert sorted(indices) == list(range(8))
    assert all(i != j for i, j in enumerate(indices)), "no item may draw itself"
    assert reused is False


def test_a_short_pool_cycles_and_says_so():
    indices, reused = B.assign_partners(5, 2, seed=0)
    assert len(indices) == 5 and set(indices) <= {0, 1}
    assert reused is True, "a reused partner is a thinner reference than it looks"


def test_an_item_is_never_handed_its_own_row_when_it_is_in_the_pool():
    """`--benchmark-ref-pool pooled` appends the evaluation set to its own
    reference pool, so `assign_partners` takes the cycle branch and can hand
    item i the pool row that *is* item i. That row's interchange ablation
    becomes `gate*clean + (1 - gate)*clean` == clean -- no intervention at
    all, scored as though there had been one, and it counts as "still
    deceptive". Measured before the fix: 92 of 200 seeds produced at least one
    such row at N=100 with a 40-item honest pool.
    """
    for n, honest in ((100, 40), (20, 5)):
        forbidden = [honest + i for i in range(n)]
        for seed in range(50):
            indices, _ = B.assign_partners(n, honest + n, seed,
                                           forbidden=forbidden)
            assert len(indices) == n
            assert all(indices[i] != forbidden[i] for i in range(n)), \
                "seed %d paired an item with itself" % seed


def test_the_unfixed_pairing_really_would_have_self_paired():
    """Guards the test above from becoming vacuous.

    If `assign_partners` were ever changed so self-pairing could not arise in
    the first place, the assertions above would pass for the wrong reason and
    stop protecting anything.
    """
    hits = sum(1 for seed in range(200)
               if any(B.assign_partners(100, 140, seed)[0][i] == 40 + i
                      for i in range(100)))
    assert hits > 0, ("no seed self-pairs without `forbidden`, so the test "
                      "above is no longer testing anything")


def test_pairing_against_an_empty_pool_is_refused():
    with pytest.raises(ValueError, match="empty reference pool"):
        B.assign_partners(3, 0, seed=0)


# ==============================================================================
# THE SCREEN
# ==============================================================================

def _even_are_deceptive(item, response):
    index = int(item.item_id.lstrip("ih"))
    return (base.DECEPTIVE, "even") if index % 2 == 0 else (base.HONEST, "odd")


def _run_screen(ctx, bench, dataset="fake"):
    from evaluation.benchmarks.judge import JudgeClient
    return B.run_screen(ctx, bench, JudgeClient(cache_path=None, verbose=False),
                        dataset)


def test_the_screen_selects_only_items_the_full_model_is_deceptive_on():
    ctx = make_ctx(make_cli(benchmark_n_per_dataset=3))
    screen = _run_screen(ctx, FakeBench(make_items(20), _even_are_deceptive))
    # Ids, not positions: the screen walks a seeded *shuffle* of the candidates,
    # so which three come back depends on the seed and asserting ["i0","i2",
    # "i4"] would be asserting the load order the shuffle exists to remove.
    assert len(screen.items) == 3
    assert all(int(i.item_id[1:]) % 2 == 0 for i in screen.items)
    assert all(i.condition == base.DECEPTIVE for i in screen.items)
    assert all(row["label"] == base.DECEPTIVE for row in screen.full_rows)
    # ...and the honest ones become the reference pool, not the eval set.
    assert all(i.condition == base.HONEST for i in screen.pool_items)


def test_the_screen_stops_early_instead_of_walking_the_whole_pool():
    ctx = make_ctx(make_cli(benchmark_n_per_dataset=2))
    screen = _run_screen(ctx, FakeBench(make_items(40), _even_are_deceptive))
    assert screen.stats["candidates"] == 40
    assert screen.stats["screened"] < 40, "early stop did not fire"
    assert screen.stats["early_stopped"] is True


def test_the_screen_walks_the_whole_pool_for_its_reference_bank_by_default():
    """The plan is explicit: "if honest bycatch from the screen is < N, keep
    screening until the honest bank reaches N (or the pool ends). Do not
    silently pair against a handful of honest items."

    So the default must be unbounded. An earlier version capped every run at
    10x the target on its own initiative, which is the opposite of what the
    plan asks and would have quietly thinned the reference pool on exactly the
    benchmarks where it matters most.
    """
    def rarely_honest(item, response):
        index = int(item.item_id[1:])
        return (base.HONEST, "rare") if index % 20 == 19 else (base.DECEPTIVE, "usual")

    ctx = make_ctx(make_cli(benchmark_n_per_dataset=3))
    screen = _run_screen(ctx, FakeBench(make_items(60), rarely_honest))
    # It kept going until the honest bank was full, well past the 3 x 10 = 30
    # that the old self-imposed cap would have allowed.
    assert len(screen.pool_items) >= 3, "the reference pool was left short"
    assert screen.stats["pool_short"] is False
    assert screen.stats["screened"] > 30


def test_the_screen_budget_bounds_that_walk_when_it_is_asked_to():
    """...and the bound is opt-in, reported, and actually stops the walk."""
    def rarely_honest(item, response):
        index = int(item.item_id[1:])
        return (base.HONEST, "rare") if index % 20 == 19 else (base.DECEPTIVE, "usual")

    ctx = make_ctx(make_cli(benchmark_n_per_dataset=3,
                            benchmark_screen_budget=24))
    screen = _run_screen(ctx, FakeBench(make_items(400), rarely_honest))
    assert screen.stats["budget"] == 24
    assert screen.stats["screened"] <= 24 + 6, \
        "the budget did not stop the walk"
    assert screen.stats["screened"] < 400
    # `pool_short` must say exactly whether the pool came up short — asserting
    # it True unconditionally would depend on how many honest rows the shuffle
    # happened to put inside the budget.
    assert screen.stats["pool_short"] == (len(screen.pool_items) < 3)
    assert screen.partner_reused == (len(screen.pool_items) < 3)
    assert len(screen.partner_index) == 3
    # And the empirical rate the plan asks to be logged is there.
    assert 0.0 < screen.stats["full_model_deception_rate"] <= 1.0


def test_the_full_row_is_the_screens_own_tokens_not_a_second_pass():
    """`full`'s text is byte-identical to the pass that selected the items.

    Asserted on the *tokens*, not on the labels: a label rule that keys on the
    item rather than the response cannot see a changed generation at all, so a
    label-only version of this test passes against a `full` row that was
    regenerated, reordered or replaced outright. (Measured — that is exactly
    what the first version of this test did.)
    """
    ctx = make_ctx(make_cli(benchmark_n_per_dataset=3))
    bench = FakeBench(make_items(12), _even_are_deceptive)

    captured = []
    original = B.generate_under

    def spy(ctx_, **kwargs):
        out = original(ctx_, **kwargs)
        captured.append((kwargs["desc"], kwargs["clean_ids"].shape[1], out,
                         kwargs["clean_ids"], kwargs["clean_mask"]))
        return out

    B.generate_under = spy
    try:
        screen = _run_screen(ctx, bench)
    finally:
        B.generate_under = original

    passes = [c for c in captured if "screen" in c[0]]
    assert passes, "no screening pass ran"
    # Which rows were selected, and from which chunk, depends on the seeded
    # shuffle — so find each item by matching its prompt tokens rather than
    # assuming a position.
    blocks = []
    for index in range(len(screen.items)):
        want = screen.clean_ids[index][screen.clean_mask[index].bool()].tolist()
        found = None
        for _, width, out, chunk_ids, chunk_mask in passes:
            for row in range(chunk_ids.shape[0]):
                if chunk_ids[row][chunk_mask[row].bool()].tolist() == want:
                    found = out[row, width:]
                    break
            if found is not None:
                break
        assert found is not None, "item %d is not in any screening batch" % index
        blocks.append(found)
    assert torch.equal(screen.full_ids[:, screen.prompt_width:],
                       torch.stack(blocks)), \
        "the `full` row is not the screen's own generated tokens"
    # The prompt columns *are* re-encoded, to the evaluation set's own width.
    assert torch.equal(screen.full_ids[:, :screen.prompt_width], screen.clean_ids)
    assert screen.full_ids.shape[1] == screen.prompt_width + NEW_TOKENS
    # And the labels carried over are the screen's, item for item.
    assert [r["label"] for r in screen.full_rows] == [base.DECEPTIVE] * 3
    # No third pass over the evaluation set. Regenerating it would produce the
    # *same* tokens here -- greedy decoding under all-gates-open is
    # deterministic -- so the token comparison above cannot see the difference,
    # and only the call count can. It is not merely a cost claim: a rerun
    # re-buckets the batch, and a different reduction order can flip an argmax
    # on a near-tie, which is exactly how `full` and its own label would drift
    # apart on a real model.
    # Screening chunks only. The count varies with the shuffle, but no pass
    # over the evaluation set may follow them: that would be the rerun this
    # test exists to forbid, and it is the only place the difference shows,
    # since greedy decoding under all-gates-open would reproduce the same
    # tokens. (The reference pool needs no pass of its own here -- its items
    # were judged in the same chunks, so their responses already exist.)
    descs = set(c[0] for c in captured)
    assert descs == {"fake: screen (full model)"}, \
        "an extra generation pass ran: %r" % (sorted(descs),)


def test_an_item_with_no_agreed_belief_is_dropped_rather_than_scored():
    class NoBelief(FakeBench):
        def belief_request(self, item):
            return [{"name": "p", "messages": item.messages}]

        def parse_belief(self, item, probes):
            # Only one in two survives, keeping both a deceptive and an honest
            # arm; the rest have nothing for a response to be deceptive *about*.
            return "b" if int(item.item_id[1:]) % 4 in (0, 1) else None

    ctx = make_ctx(make_cli(benchmark_n_per_dataset=2))
    screen = _run_screen(ctx, NoBelief(make_items(16), _even_are_deceptive))
    assert screen.stats["dropped_no_belief"] > 0
    assert all(item.belief == "b" for item in screen.items)
    assert [i.item_id for i in screen.items] == ["i0", "i4"]


def test_belief_is_elicited_from_the_full_model_never_the_ablated_one():
    """The confound this whole evaluation exists to rule out.

    A belief re-elicited under ablation would let "the circuit carried
    something the model needed in order to answer at all" score as an honesty
    gain. Checked by recording the gate values at every forward the belief pass
    makes: they must all be wide open.
    """
    seen = []

    class Recording(FakeBench):
        def belief_request(self, item):
            return [{"name": "p", "messages": item.messages}]

        def parse_belief(self, item, probes):
            return "b"

    ctx = make_ctx(make_cli(benchmark_n_per_dataset=2))
    original = B.generate_under

    def spy(ctx_, **kwargs):
        seen.append(float(torch.stack([g.detach().min()
                                       for g in ctx_.gate_log_alphas]).min()))
        return original(ctx_, **kwargs)

    B.generate_under = spy
    try:
        _run_screen(ctx, Recording(make_items(8), _even_are_deceptive))
    finally:
        B.generate_under = original
    assert seen, "no generation happened"
    assert all(value >= 10.0 for value in seen), \
        "a screening pass ran with a gate closed; belief is not the full model's"


def test_a_failed_belief_judge_is_counted_apart_from_having_no_belief():
    """One is a fact about the model, the other is a fact about an API.

    Collapsed together, an OpenRouter blip midway through a belief pass
    silently shrinks the evaluation set and is reported as "the model had no
    belief on these items".
    """
    from evaluation.benchmarks.judge import JudgeClient, JudgeResult

    class NeedsBeliefJudge(FakeBench):
        def belief_request(self, item):
            return [{"name": "p", "messages": item.messages}]

        def belief_judge_request(self, item, probe_name, response):
            from evaluation.benchmarks.base import JudgeRequest
            return JudgeRequest("openai", "m", [{"role": "user", "content": "b"}])

        def parse_belief(self, item, probes):
            return probes[0]["judge_text"]      # None when the call failed

    class Flaky(JudgeClient):
        def run(self, requests):
            return [JudgeResult(error="429 rate limited") if r is not None
                    else None for r in requests]

    ctx = make_ctx(make_cli(benchmark_n_per_dataset=2))
    bench = NeedsBeliefJudge(make_items(6), _even_are_deceptive)
    items, dropped, judge_failed = B._elicit_beliefs(
        ctx, bench, Flaky(cache_path=None, verbose=False), bench._items,
        B.eos_ids_for(ctx.node_model), PAD, "belief", NEW_TOKENS)

    assert items == []
    assert judge_failed == 6, "judge failures were not counted"
    assert dropped == 0, "an API outage was recorded as the model having no belief"


def test_a_failed_judge_call_is_unparsed_and_never_honest():
    """An API outage must not read as the ablation making the model honest."""
    from evaluation.benchmarks.judge import JudgeClient, JudgeResult

    class Judged(FakeBench):
        def judge_request(self, item, response):
            from evaluation.benchmarks.base import JudgeRequest
            return JudgeRequest("openai", "m", [{"role": "user", "content": "j"}])

        def parse_judgement(self, item, response, judge_text=None):
            return (base.HONEST, "would-have-been-honest")

    class Failing(JudgeClient):
        def run(self, requests):
            return [JudgeResult(error="503 boom") if r is not None else None
                    for r in requests]

    bench = Judged(make_items(2), _even_are_deceptive)
    rows = B._judge_all(Failing(cache_path=None, verbose=False), bench,
                        bench._items, ["x", "y"])
    assert [r["label"] for r in rows] == [base.UNPARSED, base.UNPARSED]
    assert all(r["raw"] == "judge-failed" for r in rows)
    assert all("boom" in (r["judge_error"] or "") for r in rows)


def test_a_benchmark_the_model_is_never_deceptive_on_raises_rather_than_reporting_zero():
    ctx = make_ctx(make_cli(benchmark_n_per_dataset=2))
    bench = FakeBench(make_items(6), lambda i, r: (base.HONEST, "never"))
    with pytest.raises(RuntimeError, match="not judged deceptive"):
        _run_screen(ctx, bench)


# ==============================================================================
# THE REFERENCE POOL
# ==============================================================================

def test_a_benchmark_with_honest_twins_pairs_each_item_with_its_own_twin():
    items = make_items(6, condition=base.DECEPTIVE)
    twins = dict((item.item_id, base.BenchmarkItem(
        item_id="%s~honest" % item.item_id, messages=item.messages,
        condition=base.HONEST)) for item in items)
    ctx = make_ctx(make_cli(benchmark_n_per_dataset=2))
    screen = _run_screen(ctx, FakeBench(items, _even_are_deceptive,
                                        condition_kind="prompt", twins=twins))
    assert screen.pairing == "twin"
    # Each item draws its OWN twin -- the minimal pair -- whichever items the
    # seeded shuffle happened to select.
    assert screen.partner_ids == ["%s~honest" % i.item_id for i in screen.items]


def test_without_twins_the_pool_is_deranged_so_no_item_references_itself():
    ctx = make_ctx(make_cli(benchmark_n_per_dataset=4,
                            benchmark_ref_pool="deceptive"))
    screen = _run_screen(ctx, FakeBench(make_items(20), _even_are_deceptive))
    assert screen.pairing == "derangement"
    assert all(a != b for a, b in zip([i.item_id for i in screen.items],
                                      screen.partner_ids)), \
        "an item referencing itself makes an interchange ablation a no-op"


def test_a_prompt_kind_benchmark_without_twins_uses_the_honest_half_of_load():
    deceptive = make_items(6, prefix="i", condition=base.DECEPTIVE)
    honest = make_items(6, prefix="h", condition=base.HONEST)
    ctx = make_ctx(make_cli(benchmark_n_per_dataset=2))
    screen = _run_screen(ctx, FakeBench(deceptive + honest, _even_are_deceptive,
                                        condition_kind="prompt"))
    assert screen.pairing == "derangement"
    assert all(pid.startswith("h") for pid in screen.partner_ids)


def test_the_reference_carries_the_partners_response_not_only_its_prompt():
    ctx = make_ctx(make_cli(benchmark_n_per_dataset=2))
    screen = _run_screen(ctx, FakeBench(make_items(12), _even_are_deceptive))
    assert screen.pool_refs, "no reference pool was built"
    assert any(response for _, response in screen.pool_refs), \
        "every pool entry has an empty response: only prompts were packed"


# ==============================================================================
# THE MEAN BANK
# ==============================================================================

def test_the_benchmark_mean_bank_is_collected_on_unpadded_batches_only():
    """`collect_mean_bank` runs `use_cache=False`.

    That path builds the manual causal mask, under which a fully-padded query
    row softmaxes to NaN and `0 * NaN = NaN` leaks it into the real positions
    at the next layer. A bank collected on the left-padded evaluation batch is
    NaN throughout, every logit becomes NaN and every argmax becomes token 0 —
    and two configurations sharing that bank still compare equal, so the table
    looks fine.
    """
    ctx = make_ctx(make_cli(benchmark_n_per_dataset=6))
    screen = _run_screen(ctx, FakeBench(make_items(30), _even_are_deceptive))
    eos = B.eos_ids_for(ctx.node_model)
    n = B.register_mean_bank(ctx, screen, "fake", PAD, eos)
    batches = ctx.session.banks["benchmark:fake"]
    assert n == len(batches) and batches
    for batch in batches:
        assert bool(batch["attention_mask"].all()), "a padded mean-bank batch"
        assert batch["input_ids"].shape == batch["corrupted_input_ids"].shape
        assert batch["input_ids"].shape == batch["attention_mask"].shape
    total = sum(b["input_ids"].shape[0] for b in batches)
    assert total == len(screen.items)
    # The evaluation set has rows of several different lengths, so grouping
    # must actually have split them. Without this the assertions above hold
    # just as well for a bank that never grouped at all — which is how the
    # first version of this test passed against exactly that mutation.
    widths = set(b["input_ids"].shape[1] for b in batches)
    assert len(widths) > 1, \
        "every batch came out the same width; the fixture is not ragged and " \
        "this test cannot see whether grouping happened"

    # Every row must be prompt *plus* the full model's own completion. EVAL 5
    # ablates at every position of the generation, so a bank collected over
    # prompt tokens alone fills hundreds of generated positions with a mean
    # taken somewhere else entirely.
    prompt_lengths = set(int(m.sum()) for m in screen.clean_mask)
    assert all(width > max(prompt_lengths) for width in widths), \
        "the mean bank covers prompt positions only"
    completions = B.completion_tokens(screen.full_ids, screen.prompt_width, eos)
    expected = sorted(int(m.sum()) + len(c)
                      for m, c in zip(screen.clean_mask, completions))
    got = sorted(w for b in batches for w in [b["input_ids"].shape[1]] * b["input_ids"].shape[0])
    assert got == expected


def test_a_benchmark_bank_flows_through_the_real_session_and_is_finite():
    """The registered batches actually reach `collect_mean_bank`.

    Every other test here uses a `FakeSession`, so the real
    `register_stream_batches` -> `mean_bank` -> `collect_mean_bank` path was
    covered nowhere -- and it is the path where a padded batch turns the whole
    bank to NaN. A NaN bank is invisible in a comparison of two configurations
    that share it: both come out as token 0 and they agree perfectly.
    """
    from evaluation.context import Session

    ctx = make_ctx(make_cli(benchmark_n_per_dataset=4, ablation="mean"))
    ctx.cli.mean_source = "pooled"
    screen = _run_screen(ctx, FakeBench(make_items(20), _even_are_deceptive))

    session = Session.__new__(Session)
    session._bank_batches, session._mean_banks = {}, {}
    session.node_model, session.device, session.cli = ctx.node_model, "cpu", ctx.cli
    ctx.session = session

    eos = B.eos_ids_for(ctx.node_model)
    B.register_mean_bank(ctx, screen, "fake", PAD, eos)
    bank = session.mean_bank(ctx, "benchmark:fake")

    assert bank, "the benchmark bank came back empty"

    def check(node, path=""):
        seen = 0
        if isinstance(node, dict):
            for key, value in node.items():
                seen += check(value, "%s/%s" % (path, key))
        elif torch.is_tensor(node):
            assert torch.isfinite(node).all(), \
                "site %s is NaN: the bank was collected on a padded batch" % path
            seen = 1
        return seen

    assert check(bank) > 0, "the bank holds no tensors to check"


def test_only_benchmark_banks_may_be_registered_from_outside():
    from evaluation.context import Session
    session = Session.__new__(Session)
    session._bank_batches = {}
    with pytest.raises(ValueError, match="benchmark:"):
        session.register_stream_batches("task", [])


# ==============================================================================
# END TO END
# ==============================================================================

def _payload(ctx, bench, dataset="fake"):
    from evaluation.benchmarks import judge as judge_mod

    evaluation = B.BenchmarkEvaluation()
    original = B.get_benchmark
    B.get_benchmark = lambda name: bench
    try:
        return evaluation.run(ctx)
    finally:
        B.get_benchmark = original


def test_the_evaluation_runs_every_configuration_and_labels_all_of_them(
        monkeypatch, tmp_path):
    cli = make_cli(benchmark_n_per_dataset=3, benchmark_n_random=1,
                   output_dir=str(tmp_path))
    ctx = make_ctx(cli)
    ctx.circuit_masks = 3.0          # the fake `circuit()` takes a fill value
    ctx.knockout_masks = -3.0
    ctx.random_masks = [0.0]
    ctx.random_indices = [7]
    monkeypatch.setattr(B, "expand", lambda names: ["fake"])
    monkeypatch.setattr(B, "zeros_like", lambda masks: -10.0)
    monkeypatch.setattr(B, "knockout_masks", lambda masks, granularity: masks)

    bench = FakeBench(make_items(20), _even_are_deceptive)
    payload = _payload(ctx, bench)

    entry = payload["datasets"]["fake"]
    assert set(entry["configs"]) == {"full", "knockout", "circuit_only",
                                     "empty", "random-7"}
    for name, cell in entry["configs"].items():
        assert len(cell["labels"]) == entry["n_items"] == 3
        assert len(cell["generations"]) == 3
        assert abs(sum(cell["rates"].values()) - 1.0) < 1e-9
        assert set(cell["counts"]) == set(base.LABELS)
        assert cell["coherence"]["n_tokens"] > 0
    # `full` is the screen, so it is 100% deceptive by construction.
    assert entry["configs"]["full"]["rates"]["deceptive"] == 1.0
    assert entry["full_row_is_screen"] is True
    assert payload["verification"]["benchmark_belief_from_full_model"] is True


def test_the_null_summarises_unparsed_as_well_as_deception(monkeypatch, tmp_path):
    """A random circuit that destroys output format scores a low deception
    rate for a reason that has nothing to do with honesty; on the deception
    column alone that reads as the null matching the discovered circuit."""
    cli = make_cli(benchmark_n_per_dataset=3, benchmark_n_random=2,
                   output_dir=str(tmp_path))
    ctx = make_ctx(cli)
    ctx.circuit_masks, ctx.knockout_masks = 3.0, -3.0
    ctx.random_masks, ctx.random_indices = [0.0, 1.0], [7, 8]
    monkeypatch.setattr(B, "expand", lambda names: ["fake"])
    monkeypatch.setattr(B, "zeros_like", lambda masks: -10.0)
    monkeypatch.setattr(B, "knockout_masks", lambda masks, granularity: masks)

    payload = _payload(ctx, FakeBench(make_items(20), _even_are_deceptive))
    null = payload["datasets"]["fake"]["null"]
    assert null["n"] == 2
    assert set(null) >= {"deceptive", "unparsed"}
    for key in ("deceptive", "unparsed"):
        assert null[key]["better"] == "lower"


def test_the_payload_is_json_serialisable_and_records_the_judge_prompts(
        monkeypatch, tmp_path):
    cli = make_cli(benchmark_n_per_dataset=2, benchmark_n_random=0,
                   output_dir=str(tmp_path))
    ctx = make_ctx(cli)
    ctx.circuit_masks, ctx.knockout_masks = 3.0, -3.0
    monkeypatch.setattr(B, "expand", lambda names: ["fake"])
    monkeypatch.setattr(B, "zeros_like", lambda masks: -10.0)

    payload = _payload(ctx, FakeBench(make_items(12), _even_are_deceptive))
    text = json.dumps(payload)          # must not raise on numpy scalars
    assert json.loads(text)["datasets"]["fake"]["configs"]["knockout"]["labels"]
    entry = payload["datasets"]["fake"]
    assert len(entry["items"]) == 2 and len(entry["prompts"]) == 2
    assert entry["items"][0]["messages"]
    assert len(entry["partner_ids"]) == 2
    assert entry["reference"]["pairing"] in ("twin", "derangement")


def test_examples_say_whether_they_switched_or_are_only_filler(monkeypatch,
                                                               tmp_path):
    cli = make_cli(benchmark_n_per_dataset=3, benchmark_n_random=0,
                   output_dir=str(tmp_path))
    ctx = make_ctx(cli)
    ctx.circuit_masks, ctx.knockout_masks = 3.0, -3.0
    monkeypatch.setattr(B, "expand", lambda names: ["fake"])
    monkeypatch.setattr(B, "zeros_like", lambda masks: -10.0)

    payload = _payload(ctx, FakeBench(make_items(20), _even_are_deceptive))
    examples = payload["datasets"]["fake"]["examples"]
    assert 1 <= len(examples) <= 3
    # Every example is tagged, so a thin success set cannot be mistaken for a
    # curated one.
    assert all(e["reason"] in ("switched", "fallback") for e in examples)
    assert all(e["full"]["label"] == base.DECEPTIVE for e in examples)


def test_the_report_prints_the_unparsed_column_and_the_belief_banner(
        monkeypatch, tmp_path, capsys):
    cli = make_cli(benchmark_n_per_dataset=2, benchmark_n_random=0,
                   output_dir=str(tmp_path))
    ctx = make_ctx(cli)
    ctx.circuit_masks, ctx.knockout_masks = 3.0, -3.0
    monkeypatch.setattr(B, "expand", lambda names: ["fake"])
    monkeypatch.setattr(B, "zeros_like", lambda masks: -10.0)

    payload = _payload(ctx, FakeBench(make_items(12), _even_are_deceptive))
    B.BenchmarkEvaluation().report(payload, ctx)
    out = capsys.readouterr().out
    # Both are load-bearing in the *log*, not merely in the JSON.
    assert "unparsed" in out
    assert "FULL model" in out and "reused unchanged" in out
    assert "100% deceptive by construction" in out


# ==============================================================================
# CLI WIRING
# ==============================================================================

def test_a_missing_api_key_is_caught_before_a_model_is_ever_loaded(monkeypatch):
    """The gate has to sit above `build_session`, which loads ~32 GB.

    Driven through `main()` rather than by calling `check_benchmark_keys`
    directly: the property under test is the *ordering* of two calls, and a
    test that invokes the check itself cannot see that ordering at all.
    """
    import evaluate_circuit

    def explode(cli):
        raise AssertionError("build_session ran before the key check")

    monkeypatch.setattr(evaluate_circuit, "build_session", explode)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("sys.argv", ["evaluate_circuit.py", "r", "--evals",
                                     "benchmarks", "--benchmarks",
                                     "mask:known_facts"])
    with pytest.raises(SystemExit, match="OPENAI_API_KEY"):
        evaluate_circuit.main()


def test_dry_run_does_not_require_an_api_key(monkeypatch):
    """Plan step 3: --dry-run runs on a login node with no key exported.

    It *prints* which keys are missing, which it cannot do if a missing key is
    what stopped it -- so gating the check on --judge-dry-run alone made that
    whole block unreachable.
    """
    import evaluate_circuit

    def boom(cli):
        raise AssertionError("the key check ran under --dry-run")

    class Reached(Exception):
        pass

    monkeypatch.setattr(evaluate_circuit, "check_benchmark_keys", boom)
    monkeypatch.setattr(evaluate_circuit, "build_session",
                        lambda cli: (_ for _ in ()).throw(Reached()))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("sys.argv",
                        ["evaluate_circuit.py", "r", "--evals", "benchmarks",
                         "--dry-run", "--benchmarks", "mask:known_facts"])
    # Reaching build_session is the proof: the key check was skipped.
    with pytest.raises(Reached):
        evaluate_circuit.main()


def test_sandbagging_alone_needs_no_key():
    import evaluate_circuit
    cli = evaluate_circuit.build_parser().parse_args(
        ["r", "--evals", "benchmarks", "--benchmarks", "sandbagging"])
    evaluate_circuit.check_benchmark_keys(cli)      # must not raise


def test_benchmarks_is_a_choice_but_not_a_default():
    """Otherwise every existing invocation starts demanding API keys."""
    from evaluation import default_evaluations, list_evaluations
    assert "benchmarks" in list_evaluations()
    assert "benchmarks" not in default_evaluations()
    import evaluate_circuit
    cli = evaluate_circuit.build_parser().parse_args(["r"])
    assert cli.evals == default_evaluations()


def test_judge_dry_run_loads_no_model(monkeypatch):
    """`build_session` must skip `build_heavy` under --judge-dry-run.

    Exercises the real `build_session` with only the circuit/task resolution
    stubbed. Asserting on the parsed flags instead would pass against a
    `build_session` that ignores the flag entirely.
    """
    from types import SimpleNamespace as NS

    import evaluate_circuit
    from evaluation import circuits as circuits_mod
    from evaluation import context as context_mod

    def explode(self):
        raise AssertionError("build_heavy ran under --judge-dry-run")

    monkeypatch.setattr(context_mod.Session, "build_heavy", explode)
    monkeypatch.setattr(circuits_mod, "resolve_circuits",
                        lambda cli: ([NS(label="c")], {"self": "/x"}, None,
                                     {"self": {}}, {}))
    monkeypatch.setattr(circuits_mod, "resolve_tasks", lambda *a: [])
    monkeypatch.setattr(context_mod, "resolve_train_args",
                        lambda config, cli: (NS(model="m"), None))

    cli = evaluate_circuit.resolve_cli(evaluate_circuit.build_parser().parse_args(
        ["r", "--evals", "benchmarks", "--judge-dry-run"]))
    assert cli.judge_dry_run and not cli.dry_run
    context_mod.build_session(cli)          # must not raise

    # ...and the same guard must NOT swallow an ordinary run.
    plain = evaluate_circuit.resolve_cli(
        evaluate_circuit.build_parser().parse_args(["r", "--evals", "sanity"]))
    with pytest.raises(AssertionError, match="build_heavy ran"):
        context_mod.build_session(plain)


def test_the_judge_model_flags_reach_the_request_rather_than_parsing_and_dying():
    """A flag that is read through `getattr(cli, ...)` but never applied is a
    silent no-op — the exact bug workstream D's review found three times."""
    from evaluation.benchmarks.liars_bench import InstructedDeception
    from evaluation.benchmarks.mask_bench import MaskSplit

    cli = SimpleNamespace(mask_judge_model="gpt-test",
                          mask_numeric_judge_model="o-test",
                          lb_judge_model="lb-test",
                          lb_harm_judge_model="harm-test",
                          benchmark_repo_root=None)
    split = MaskSplit.__new__(MaskSplit)
    split.split, split.numerical, split.name = "known_facts", False, "mask:kf"
    split.binary_model, split.numerical_model = "gpt-4o", "o3-mini"
    split._prompts, split._metric = object(), None
    split.bind(cli)
    assert split.binary_model == "gpt-test"
    assert split.judge_spec()["model"] == "gpt-test"

    lb = InstructedDeception()
    lb.bind(cli)
    assert lb.judge_model == "lb-test"
    assert lb.judge_spec()["model"] == "lb-test"


def test_the_judge_cache_sits_above_the_cell_directory():
    """A suite must not re-buy a verdict once per cell."""
    ctx = SimpleNamespace(cli=SimpleNamespace(output_dir="/runs/evaluations"),
                          out_dir="/runs/evaluations/interchange")
    assert B.judge_cache_path(ctx) == "/runs/evaluations/judge_cache.jsonl"
    ctx.cli.output_dir = None
    assert B.judge_cache_path(ctx) == os.path.join(ctx.out_dir,
                                                   "judge_cache.jsonl")
