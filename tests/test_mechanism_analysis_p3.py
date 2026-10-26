"""Ticket 05 of mechanism-analysis: the phase-3 builders (outputs/_launch_mechanism_analysis/p3_*.py).

Seams (spec section 2.3, section 4 phase 3, R25 A, R28): the grid circuit C_t and its job line; the identity of C_t
with phase 1C's routing-check C_t; the A' adjudication (category per deciding-set head, weighted majority,
sub-reading, the routing condition); B-selector; where the pressure enters; the completeness share; the roles
merge table restricted to the phase-3 cell's rows.
"""

from __future__ import annotations

import importlib
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCH = os.path.join(REPO, "outputs", "_launch_mechanism_analysis")


def _mod(name):
    if LAUNCH not in sys.path:
        sys.path.insert(0, LAUNCH)
    return importlib.import_module(name)


@pytest.fixture(scope="module")
def jobs():
    return _mod("p3_jobs")


# ==============================================================================
# p3_jobs: C_t and the job line
# ==============================================================================

def test_the_expression_is_core_excl_and_dmh_minus_core_then_the_operand(jobs):
    assert jobs.expr("far") == "Ct=(((Df&Ds&De)|(Df-Ds-De)|((Df-Hf)-(Df&Ds&De)))-m)|X"
    assert jobs.expr("sdr") == "Ct=(((Df&Ds&De)|(Ds-Df-De)|((Ds-Hs)-(Df&Ds&De)))-m)|X"
    assert jobs.expr("ser") == "Ct=(((Df&Ds&De)|(De-Df-Ds)|((De-He)-(Df&Ds&De)))-m)|X"


def test_the_line_binds_the_operand_and_the_references(jobs):
    for counterfactual in ("neutral_twin", "item_swap"):
        argv = jobs.line("ser", counterfactual)
        joined = " ".join(argv)
        assert "X=outputs/_launch_mechanism_analysis/operands/skct_ser" in joined
        assert "--reference x_ser=outputs/_launch_mechanism_analysis/operands/skct_ser" in joined
        for u in ("far", "sdr", "ser"):
            assert f"--reference {u}_D=" in joined and f"--reference {u}_H=" in joined
        assert argv[argv.index("--task-from") + 1] == jobs.RUNS["ser"][0]
        assert argv[argv.index("--compose-granularity") + 1] == "leaf"
        # the default causal sample: no --n-causal or --seed override
        assert "--n-causal" not in argv and "--seed" not in argv


def test_the_twin_line_runs_its_segment_pass_at_the_floor_and_the_sweep(jobs):
    argv = jobs.line("far", "neutral_twin")
    assert argv[argv.index("--analyses") + 1] == "path_patching"
    assert argv[argv.index("--path-counterfactual") + 1] == "neutral_twin"
    assert argv[argv.index("--path-twin-position-threshold") + 1] == "0.01"
    assert "--path-completeness-sweep" in argv
    assert argv[argv.index("--output-dir") + 1] == "outputs/_analyses/mechanism-analysis-p3/d"


def test_the_item_swap_line_keeps_the_default_threshold_and_has_no_sweep(jobs):
    argv = jobs.line("far", "item_swap")
    assert argv[argv.index("--path-counterfactual") + 1] == "item_swap"
    assert "--path-position-threshold" not in argv and "--path-twin-position-threshold" not in argv
    assert "--path-completeness-sweep" not in argv
    assert argv[argv.index("--output-dir") + 1] == "outputs/_analyses/mechanism-analysis-p3/d_is"


def test_the_batch_file_runs_the_twin_first_and_the_cli_parses_both_lines(jobs):
    import shlex

    import analyze_components
    from component_analysis import path_patching as pp

    text = jobs.batch_text("sdr")
    lines = [one for one in text.splitlines() if one and not one.startswith("#")]
    assert len(lines) == 2
    twin, swap = (analyze_components.build_parser().parse_args(shlex.split(one)) for one in lines)
    assert twin.path_counterfactual == "neutral_twin" and swap.path_counterfactual == "item_swap"
    # the twin line sweeps under the twin (its one selected pair) with its Segment pass at 0.01
    ctx = type("C", (), {"cli": twin, "task_spec": type("T", (), {"name": "sdr_v2"})()})()
    assert pp.sweep_counterfactual(ctx) == pp.NEUTRAL_TWIN
    assert pp.position_threshold(ctx, pp.NEUTRAL_TWIN) == 0.01
    ctx_swap = type("C", (), {"cli": swap, "task_spec": type("T", (), {"name": "sdr_v2"})()})()
    assert pp.position_threshold(ctx_swap, pp.ITEM_SWAP) == 0.05
    assert twin.output_dir != swap.output_dir


def test_ct_sets_compose_the_parts(jobs):
    sets = {"D_far": {(1, 1), (2, 2), (3, 3)}, "D_sdr": {(1, 1), (4, 4)}, "D_ser": {(1, 1), (5, 5)},
            "H_far": {(3, 3)}, "H_sdr": set(), "H_ser": set()}
    operand = {"heads": ["head.9.9"], "members": ["head.9.9", "mlp.6.0"], "mlp_layers": [6, 7]}
    parts = jobs.ct_sets("far", sets, operand)
    assert parts["core"] == {"head.1.1"}
    assert parts["excl"] == {"head.2.2", "head.3.3"}
    assert parts["DmH_minus_core"] == {"head.2.2"}
    assert parts["mlps"] == {"mlp.6.0", "mlp.7.0"}
    assert parts["C_t"] == {"head.1.1", "head.2.2", "head.3.3", "head.9.9", "mlp.6.0", "mlp.7.0"}


def test_routing_identity_holds_only_for_the_exact_complement(jobs):
    universe = jobs.all_components(n_layers=2, n_heads=2)
    assert len(universe) == 6
    ct = {"head.0.0", "mlp.1.0"}
    route_c = [["head", 0, 1], ["head", 1, 0], ["head", 1, 1], ["mlp", 0, 0]]
    assert jobs.routing_identity(ct, route_c, universe)["identical"]
    off = jobs.routing_identity({"head.0.0"}, route_c, universe)
    assert not off["identical"] and off["only_in_prelim"] == ["mlp.1.0"]
