"""Tests for evaluation/rejudge.py — repairing labels after a judge outage.

The fixture builds each cell's `benchmarks.json` with the evaluator's own
functions (`_judge_all`, `tally_labels`, `_null`, `_examples`, `headline_of`,
`suite.write_matrix`), twice: once with a judge that fails on some rows (what
the outage produced) and once with a judge that never fails (what the run
would have produced). Re-judging the first must reproduce the second.
"""

import argparse
import io
import json
import os

import pytest

from evaluation import benchmark_eval as B
from evaluation import rejudge
from evaluation import suite as suite_mod
from evaluation.benchmarks import base
from evaluation.benchmarks.base import Benchmark, BenchmarkItem, JudgeRequest
from evaluation.benchmarks.judge import JudgeCache, JudgeClient, request_key

DATASET = "fake:one"
JUDGE_MODEL = "fake/judge-1"
CONFIGS = ("full", "knockout", "random-0", "random-1")
N_ITEMS = 4


class FakeBench(Benchmark):
    name = DATASET
    display_name = "Fake / one"
    condition_kind = "outcome"
    requires_key = "OPENROUTER_API_KEY"

    def bind(self, cli):
        return self

    def judge_spec(self):
        return {"provider": "openrouter", "model": JUDGE_MODEL}

    def judge_request(self, item, response):
        return JudgeRequest(
            "openrouter", JUDGE_MODEL,
            [{"role": "user", "content": "belief=%s\nresponse=%s"
              % (item.belief, response)}], kwargs={"max_tokens": 5})

    def parse_judgement(self, item, response, judge_text=None):
        if judge_text is None:
            return base.UNPARSED, "no_judge_response"
        if judge_text == "LIE":
            return base.DECEPTIVE, "lie"
        if judge_text == "TRUTH":
            return base.HONEST, "truth"
        return base.UNPARSED, "unreadable"


def verdict(request):
    """The judge's deterministic answer: a response containing 'lie' is one."""
    text = request.messages[0]["content"]
    return "LIE" if "lie" in text.split("response=")[1] else "TRUTH"


class PaymentRequired(Exception):
    status_code = 402                      # not transient: no retry


def make_items():
    return [BenchmarkItem("fake/%d" % i,
                          [{"role": "user", "content": "question %d" % i}],
                          condition=base.DECEPTIVE, belief="B%d" % i,
                          meta={"task_id": i})
            for i in range(N_ITEMS)]


def generations(config, cell_index):
    """Per config, which rows lie. `random-0`'s rows repeat `knockout`'s, so
    identical requests exist across configs (one judge call serves both)."""
    lies = {"full": [0, 1, 2, 3], "knockout": [0], "random-0": [0],
            "random-1": [0, 1, 2]}[config]
    tag = "k" if config in ("knockout", "random-0") else config
    return ["%s c%d row%d %s" % (tag, cell_index, i,
                                 "lie" if i in lies else "fine")
            for i in range(N_ITEMS)]


def build_payload(cell_index, fail):
    """A benchmarks.json payload; `fail(config, index)` -> judge fails there."""
    bench = FakeBench()
    items = make_items()
    entry = {"display_name": bench.display_name,
             "condition_kind": bench.condition_kind,
             "judge": bench.judge_spec(), "new_tokens": 8, "n_items": N_ITEMS,
             "screen": {"selected": N_ITEMS},
             "items": [item.to_json() for item in items],
             "prompts": ["prompt %d" % i for i in range(N_ITEMS)],
             "partner_ids": [], "configs": {}}
    for config in CONFIGS:
        responses = generations(config, cell_index)
        failing = {responses[i] for i in range(N_ITEMS) if fail(config, i)}

        async def transport(request, failing=failing):
            text = request.messages[0]["content"].split("response=")[1]
            if text in failing:
                raise PaymentRequired("Error code: 402 - insufficient credits")
            return verdict(request)

        client = JudgeClient(cache_path=None, verbose=False,
                             transport=transport)
        rows = B._judge_all(client, bench, items, responses)
        counts, rates = B.tally_labels(rows)
        entry["configs"][config] = {
            "counts": counts, "rates": rates,
            "coherence": {"ref_nll": 1.0 + cell_index, "distinct_n": 0.5},
            "generations": responses, "labels": rows}
    evaluation = B.BenchmarkEvaluation()
    entry["null"] = evaluation._null(entry)
    entry["examples"] = evaluation._examples(entry, rejudge._ScreenStub(entry))
    datasets = {DATASET: entry, "fake:broken": {"error": "boom"}}
    return {"resolved": {"model": "fake"}, "datasets": datasets,
            "failed_datasets": {"fake:broken": "boom"},
            "judge": {"cache_hits": 0, "cache_writes": 0},
            "headline": B.headline_of(datasets), "seconds": 1.0}


def outage(config, index):
    # `full` is the screen and never failed; elsewhere rows 1 and 3 failed,
    # plus row 0 of knockout (whose request random-0 repeats).
    if config == "full":
        return False
    return index in (1, 3) or (config == "knockout" and index == 0)


CELLS = ("A__leaf", "B__leaf")


def write_suite(root, fail):
    os.makedirs(root, exist_ok=True)
    cli = {"judge_concurrency": 3, "benchmark_repo_root": None,
           "mask_judge_model": None, "output_dir": root}
    with open(os.path.join(root, "suite.json"), "w") as handle:
        json.dump({"cli": cli, "circuits": []}, handle)
    matrix = []
    for k, label in enumerate(CELLS):
        out_dir = os.path.join(root, "cells", label, "t", "interchange")
        os.makedirs(out_dir)
        payload = build_payload(k, fail)
        suite_mod.write_json(os.path.join(out_dir, "benchmarks.json"), payload)
        matrix.append({"circuit": label, "circuit_kind": "leaf", "expr": None,
                       "task": "t", "ablation": "interchange",
                       "out_dir": out_dir,
                       "headlines": {"benchmarks": payload["headline"]}})
    suite_mod.write_matrix(root, matrix)
    return root


def cell_path(root, label):
    return os.path.join(root, "cells", label, "t", "interchange",
                        "benchmarks.json")


def load(path):
    with open(path) as handle:
        return json.load(handle)


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


@pytest.fixture
def suite(tmp_path, monkeypatch):
    monkeypatch.setattr(rejudge, "get_benchmark", lambda name: FakeBench())
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-not-a-key")
    return write_suite(str(tmp_path / "suite"), outage)


@pytest.fixture
def truth(tmp_path):
    return write_suite(str(tmp_path / "truth"), lambda config, index: False)


class Recorder(object):
    """A client factory whose transport records every API call made."""

    def __init__(self, fail_always=False):
        self.calls = []
        self.fail_always = fail_always

    def __call__(self, cache_path, concurrency):
        async def transport(request):
            self.calls.append(request_key(request))
            if self.fail_always:
                raise PaymentRequired("Error code: 402 - insufficient credits")
            return verdict(request)
        self.concurrency = concurrency
        return JudgeClient(cache_path=cache_path, concurrency=concurrency,
                           verbose=False, transport=transport,
                           initial_delay=0.0)


def run(suite_dir, **kwargs):
    out = io.StringIO()
    code = rejudge.run([suite_dir], out=out, **kwargs)
    return code, out.getvalue()


def failed_rows(path):
    return sum(1 for entry in load(path)["datasets"].values()
               for cell in (entry.get("configs") or {}).values()
               for row in cell["labels"] if rejudge.is_failed(row))


def unique_failed_requests(root):
    keys = set()
    for label in CELLS:
        payload = load(cell_path(root, label))
        entry = payload["datasets"][DATASET]
        items = rejudge.items_of(entry)
        for cell in entry["configs"].values():
            for i, row in enumerate(cell["labels"]):
                if rejudge.is_failed(row):
                    keys.add(request_key(FakeBench().judge_request(
                        items[i], cell["generations"][i])))
    return keys


# ---------------------------------------------------------------------------

def test_fixture_has_the_outage_shape(suite):
    row = load(cell_path(suite, "A__leaf"))["datasets"][DATASET][
        "configs"]["knockout"]["labels"][1]
    assert row["raw"] == "judge-failed" and row["label"] == base.UNPARSED
    assert "402" in row["judge_error"] and row["judge_text"] is None
    # knockout: rows 0,1,3; random-0: 1,3; random-1: 1,3 -> 7 per cell
    assert failed_rows(cell_path(suite, "A__leaf")) == 7


def test_dry_counts_rows_hits_and_calls_and_touches_nothing(suite):
    # Pre-pay one failed request so it shows as a cache hit.
    entry = load(cell_path(suite, "A__leaf"))["datasets"][DATASET]
    item = rejudge.items_of(entry)[1]
    paid = FakeBench().judge_request(item, entry["configs"]["random-1"][
        "generations"][1])
    JudgeCache(rejudge.cache_file(suite)).put(request_key(paid), "TRUTH")

    before = {label: read_bytes(cell_path(suite, label)) for label in CELLS}
    matrix_before = read_bytes(os.path.join(suite, "matrix.json"))
    recorder = Recorder()
    code, text = run(suite, dry=True, client_factory=recorder)

    assert code == rejudge.EXIT_OK
    assert recorder.calls == []
    assert "rows    7  cache hits    1  calls    4" in text   # cell A
    # random-0 repeats knockout's requests, so it costs nothing extra.
    unique = len(unique_failed_requests(suite)) - 1          # minus the hit
    assert "total: 14 rows to re-judge, 1 cache hits, %d new judge calls" \
        % unique in text
    assert "judge models: %s (14 rows)" % JUDGE_MODEL in text
    for label in CELLS:
        assert read_bytes(cell_path(suite, label)) == before[label]
        assert not os.path.exists(cell_path(suite, label) + ".pre_rejudge")
    assert read_bytes(os.path.join(suite, "matrix.json")) == matrix_before


def test_rejudge_reproduces_what_the_evaluator_would_have_written(suite, truth):
    recorder = Recorder()
    code, text = run(suite, client_factory=recorder)
    assert code == rejudge.EXIT_OK, text
    assert recorder.concurrency == 3                     # suite's own setting
    # One call per distinct request; repeats are served by the cache.
    assert len(recorder.calls) == len(set(recorder.calls))

    for label in CELLS:
        got = load(cell_path(suite, label))
        want = load(cell_path(truth, label))
        got_entry, want_entry = got["datasets"][DATASET], want["datasets"][DATASET]
        for config in CONFIGS:
            for field in ("labels", "counts", "rates", "coherence",
                          "generations"):
                assert got_entry["configs"][config][field] == \
                    want_entry["configs"][config][field], (label, config, field)
        assert got_entry["null"] == want_entry["null"]
        assert got_entry["examples"] == want_entry["examples"]
        assert got["headline"] == want["headline"]
        assert got["datasets"]["fake:broken"] == {"error": "boom"}
        assert got["judge"] == {"cache_hits": 0, "cache_writes": 0}
        block = got["rejudge"]
        assert block["still_failing"] == 0 and len(block["runs"]) == 1
        assert block["runs"][0]["attempted"] == 7
        assert block["runs"][0]["fixed"] == 7

    # The outage changed the numbers, so the repair must have moved them.
    before = load(cell_path(suite, "A__leaf") + ".pre_rejudge")
    assert before["datasets"][DATASET]["configs"]["knockout"]["rates"] != \
        load(cell_path(suite, "A__leaf"))["datasets"][DATASET]["configs"][
            "knockout"]["rates"]

    got_matrix = load(os.path.join(suite, "matrix.json"))
    want_matrix = load(os.path.join(truth, "matrix.json"))
    assert [c["headlines"] for c in got_matrix["cells"]] == \
        [c["headlines"] for c in want_matrix["cells"]]
    with open(os.path.join(suite, "matrix.csv")) as a, \
            open(os.path.join(truth, "matrix.csv")) as b:
        strip = lambda rows: [r.replace(suite, "").replace(truth, "")  # noqa
                              for r in rows]
        assert strip(a.readlines()) == strip(b.readlines())
    assert os.path.exists(os.path.join(suite, "matrix.json.pre_rejudge"))


def test_backup_is_written_once_and_second_run_does_nothing(suite):
    original = read_bytes(cell_path(suite, "A__leaf"))
    # First run: the cap lets only some calls through, so rows stay failing.
    code, _ = run(suite, client_factory=Recorder(), max_calls=3)
    assert code == rejudge.EXIT_STILL_FAILING
    backup = cell_path(suite, "A__leaf") + ".pre_rejudge"
    assert read_bytes(backup) == original

    # Second run finishes the job; the backup still holds the pre-repair file.
    code, _ = run(suite, client_factory=Recorder())
    assert code == rejudge.EXIT_OK
    assert read_bytes(backup) == original
    after = {label: read_bytes(cell_path(suite, label)) for label in CELLS}
    assert all(failed_rows(cell_path(suite, label)) == 0 for label in CELLS)

    # Third run: nothing failing, so no call, no write, no new run record.
    recorder = Recorder()
    code, text = run(suite, client_factory=recorder)
    assert code == rejudge.EXIT_OK
    assert recorder.calls == []
    assert {label: read_bytes(cell_path(suite, label))
            for label in CELLS} == after
    assert "total: 0 rows to re-judge" in text


def test_cap_is_respected_across_cells(suite):
    recorder = Recorder()
    code, text = run(suite, client_factory=recorder, max_calls=4)
    assert code == rejudge.EXIT_STILL_FAILING
    assert len(recorder.calls) == 4                       # preflight included
    remaining = sum(failed_rows(cell_path(suite, label)) for label in CELLS)
    assert remaining > 0
    assert "judge calls made this run (excluding retries): 4" in text


def test_preflight_failure_aborts_before_any_write(suite):
    before = {label: read_bytes(cell_path(suite, label)) for label in CELLS}
    recorder = Recorder(fail_always=True)
    code, text = run(suite, client_factory=recorder)
    assert code == rejudge.EXIT_ABORTED
    assert len(recorder.calls) == 1
    assert "preflight judge call failed" in text and "402" in text
    for label in CELLS:
        assert read_bytes(cell_path(suite, label)) == before[label]
        assert not os.path.exists(cell_path(suite, label) + ".pre_rejudge")


def test_missing_key_aborts_without_calling(suite, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY")
    recorder = Recorder()
    code, text = run(suite, client_factory=recorder)
    assert code == rejudge.EXIT_ABORTED and recorder.calls == []
    assert "OPENROUTER_API_KEY not set" in text and "skipped" in text


def test_prompt_drift_refuses_the_dataset(suite):
    path = cell_path(suite, "B__leaf")
    payload = load(path)
    payload["datasets"][DATASET]["configs"]["knockout"]["labels"][1][
        "judge_prompt"] = "a rubric that has since changed"
    suite_mod.write_json(path, payload)
    before = read_bytes(path)

    code, text = run(suite, client_factory=Recorder())
    assert code == rejudge.EXIT_REFUSED
    assert "REFUSED" in text and "drift" in text
    assert read_bytes(path) == before                    # B untouched
    assert failed_rows(cell_path(suite, "A__leaf")) == 0  # A still repaired


def test_inconsistent_stored_numbers_refuse_the_cell(suite):
    path = cell_path(suite, "A__leaf")
    payload = load(path)
    payload["datasets"][DATASET]["configs"]["full"]["rates"]["deceptive"] = 0.5
    suite_mod.write_json(path, payload)
    before = read_bytes(path)

    code, text = run(suite, dry=True, client_factory=Recorder())
    assert code == rejudge.EXIT_REFUSED
    assert "do not reproduce" in text and "fake:one/full.rates" in text
    code, _ = run(suite, client_factory=Recorder())
    assert code == rejudge.EXIT_REFUSED
    assert read_bytes(path) == before


def test_cli_entry_point_dry(suite, capsys):
    import rejudge_benchmarks
    assert rejudge_benchmarks.main([suite, "--dry"]) == 0
    assert "total: 14 rows to re-judge" in capsys.readouterr().out


def test_suite_cli_reads_the_evaluators_namespace(suite):
    cli = rejudge.suite_cli(suite)
    assert isinstance(cli, argparse.Namespace) and cli.judge_concurrency == 3


def test_preflight_failure_skips_only_its_suite(tmp_path, monkeypatch):
    monkeypatch.setattr(rejudge, "get_benchmark", lambda name: FakeBench())
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-not-a-key")
    good = write_suite(str(tmp_path / "good"), outage)
    bad = write_suite(str(tmp_path / "bad"), outage)
    bad_before = {label: read_bytes(cell_path(bad, label)) for label in CELLS}

    healthy = Recorder()
    failing = Recorder(fail_always=True)

    def factory(cache_path, concurrency):
        chosen = failing if cache_path.startswith(bad) else healthy
        return chosen(cache_path, concurrency)

    out = io.StringIO()
    code = rejudge.run([good, bad], client_factory=factory, out=out)
    text = out.getvalue()
    assert code == rejudge.EXIT_ABORTED
    assert all(failed_rows(cell_path(good, label)) == 0 for label in CELLS)
    assert "suite %s skipped; nothing was written to it." % bad in text
    assert len(failing.calls) == 1
    for label in CELLS:
        assert read_bytes(cell_path(bad, label)) == bad_before[label]
