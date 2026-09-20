"""
Knockout by role family against a model: the seam that proves it is not a
second implementation, and the CLI run that writes the files.

The claim the ticket makes is that a family knockout goes through ticket 07's
knockout code path. The test of that claim is arithmetic, not reading: a family
of one Component must reproduce that Component's single knockout **exactly**,
and a family of several must ablate all of them in one forward rather than
report the sum of their singles.

nnsight 0.7.0 only, gated as `tests/test_knockout_model.py` gates. The grouping
and the summaries are tested in `tests/test_knockout_families.py`, which runs
everywhere.
"""

from __future__ import annotations

import os

import pytest

nnsight = pytest.importorskip("nnsight")
PINNED = "0.7.0"
if nnsight.__version__ != PINNED:
    pytest.skip(f"nnsight {nnsight.__version__} is installed, not the pinned "
                f"{PINNED}; these are 0.7.0 behaviours.",
                allow_module_level=True)

import analyze_components                                          # noqa: E402
from component_analysis import knockout, roles                     # noqa: E402
from component_analysis.head_table import load_head_table          # noqa: E402
from tests.test_analyze_components_end_to_end import written_files  # noqa: E402, F401
from tests.test_analyze_components_segmentation import (           # noqa: E402, F401
    CELL, read_json, run_cli, sdr_run)
from tests.test_knockout_model import batch, cli_model, model      # noqa: E402, F401


# ==============================================================================
# THE SEAM: ONE CODE PATH
# ==============================================================================

def test_a_family_of_one_is_that_component_s_own_knockout_number(model, batch):
    """The check that the two are one implementation and not two."""
    key = ("head", 1, 2)

    single = knockout.knockout_effects(model, [batch], [key])
    family = knockout.family_effects(model, [batch], {"mover": [key]})

    assert family.knocked_logit_difference["mover"] == \
        single.knocked_logit_difference[key]
    assert family.clean_logit_difference == single.clean_logit_difference
    assert family.ids == single.ids


def test_a_family_of_several_is_ablated_in_one_forward_not_summed(model, batch):
    """A joint effect, which is why the family question is worth asking.

    Two Components knocked out together are not their two drops added: the
    model is not linear in them. The test asserts the family number differs
    from the sum, which is exactly the thing a per-Component ranking cannot
    tell the researcher.
    """
    members = [("head", 1, 2), ("mlp", 0, 0), ("head", 0, 1)]

    singles = knockout.knockout_effects(model, [batch], members)
    family = knockout.family_effects(model, [batch], {"unknown": members})

    summed = [sum(singles.drops(key)[n] for key in members)
              for n in range(len(batch.ids))]
    joint = family.drops("unknown")
    assert any(abs(one) > 1e-4 for one in joint), "the family moves the metric"
    assert joint != pytest.approx(summed, abs=1e-6), \
        "a joint ablation is not the sum of its parts"


def test_a_family_knockout_is_every_member_replaced_at_once(model, batch):
    """The definition, checked against the primitive, as ticket 07 checks its own.

    The independent value comes from `replace_forward`, whose logits come from
    the model's own head inside the trace, with *every* member replaced. The
    analysis reads its own number from the residual through the fp32 readout.
    Two routes to the same number, and a family that quietly ablated a subset
    of its members would not reach it.
    """
    from component_analysis import hooks
    from tests.test_knockout_model import logit_difference_of

    members = [("head", 1, 2), ("mlp", 0, 0), ("head", 0, 1)]

    family = knockout.family_effects(model, [batch], {"unknown": members})

    corrupt = hooks.capture_forward(model, batch.corrupt_input_ids,
                                    batch.corrupt_attention_mask,
                                    components=members, positions=batch.readout)
    expected = logit_difference_of(
        hooks.replace_forward(
            model, batch.input_ids, batch.attention_mask,
            replacements={key: corrupt.outputs[key] for key in members},
            positions=batch.readout),
        batch)
    assert family.knocked_logit_difference["unknown"] == pytest.approx(
        expected, abs=1e-4)


def test_a_family_covering_every_component_is_the_whole_circuit_knocked_out(
        model, batch):
    from tests.test_knockout_model import ALL_COMPONENTS

    family = knockout.family_effects(model, [batch],
                                     {"unknown": list(ALL_COMPONENTS)})

    assert len(family.drops("unknown")) == len(batch.ids)
    assert any(abs(one) > 1e-3 for one in family.drops("unknown"))


def test_an_unbuilt_scheme_is_refused_before_any_forward_runs(model, batch):
    with pytest.raises(ValueError, match="future work"):
        knockout.family_effects(model, [batch], {"mover": [("head", 0, 0)]},
                                scheme="zero")


# ==============================================================================
# THE CLI SEAM
# ==============================================================================

def roles_cell(out):
    return os.path.join(str(out), *CELL)


def run_roles_then_families(run_dir, out, family_out, *extra):
    """The three steps the real run takes, in order.

    Knockout into one suite, the roles pass over that cell, then a second
    knockout with `--knockout-families` reading the roles from it. The family
    run writes into a *second* suite on purpose: an analysis run rebuilds the
    head table from the intake's rows, so writing it back into the roles cell
    would drop the very columns it just read.
    """
    assert run_cli(str(run_dir), "--num-kv-heads", "2", "--analyses", "knockout",
                   "--device", "cpu", "--output-dir", str(out)) == 0
    assert analyze_components.main(["roles", roles_cell(out),
                              "--roles-allow-missing-views"]) == 0
    return run_cli(str(run_dir), "--num-kv-heads", "2", "--analyses", "knockout",
                   "--device", "cpu", "--output-dir", str(family_out),
                   "--knockout-families", "--knockout-roles-from",
                   roles_cell(out), *extra)


def test_a_cli_run_writes_the_family_json_the_png_and_the_head_table_columns(
        sdr_run, cli_model, tmp_path):
    run_dir, out, _records = sdr_run
    family_out = str(tmp_path / "families")

    assert run_roles_then_families(run_dir, out, family_out) == 0

    written = written_files(family_out)
    assert os.path.join(*CELL, knockout.SUBDIR, knockout.FAMILY_JSON_NAME) in written
    assert os.path.join(*CELL, knockout.SUBDIR, knockout.FAMILY_PNG_NAME) in written

    payload = read_json(family_out, *CELL, knockout.SUBDIR,
                        knockout.FAMILY_JSON_NAME)
    assert payload["n_families"] >= 1
    assert payload["grouping"]["read_from"] == roles_cell(out)
    assert "helps deception" in payload["metric"]["sign"]
    members = [tuple(one) for family in payload["families"]
               for one in family["members"]]
    assert len(members) == len(set(members)), "a Component is in one family"

    table = read_json(family_out, *CELL, "head_table.json")
    assert "knockout.role_family" in table["columns"]
    assert "knockout.role_family_logit_diff_drop" in table["columns"]


def test_the_family_and_the_single_knockout_agree_where_a_family_has_one_member(
        sdr_run, cli_model, tmp_path):
    """The same claim as the library seam, asserted on the written files.

    The tiny fixture's Components all propose `unknown`, so the single-member
    family is made the way the researcher would make one: by confirming a role
    on one Component, which is also the column the grouping is supposed to
    prefer.
    """
    from component_analysis.head_table import write_head_table

    run_dir, out, _records = sdr_run
    family_out = str(tmp_path / "families")

    assert run_cli(str(run_dir), "--num-kv-heads", "2", "--analyses", "knockout",
                   "--device", "cpu", "--output-dir", str(out)) == 0
    assert analyze_components.main(["roles", roles_cell(out),
                              "--roles-allow-missing-views"]) == 0
    rows = load_head_table(roles_cell(out))
    rows[0]["role_confirmed"] = "mover"
    write_head_table(roles_cell(out), rows)
    assert run_cli(str(run_dir), "--num-kv-heads", "2", "--analyses", "knockout",
                   "--device", "cpu", "--output-dir", family_out,
                   "--knockout-families", "--knockout-roles-from",
                   roles_cell(out)) == 0

    singles = {tuple(one["key"]): one["mean_drop"] for one in
               read_json(family_out, *CELL, knockout.SUBDIR,
                         knockout.JSON_NAME)["components"]}
    families = read_json(family_out, *CELL, knockout.SUBDIR,
                         knockout.FAMILY_JSON_NAME)["families"]
    alone = [one for one in families if one["n_components"] == 1]
    assert alone, "the fixture has at least one single-member family"
    for family in alone:
        assert family["mean_drop"] == pytest.approx(
            singles[tuple(family["members"][0])], abs=1e-9)


def test_the_roles_may_be_read_from_another_cell(sdr_run, cli_model, tmp_path):
    """The real run reads the roles from the cell the roles pass wrote."""
    run_dir, out, _records = sdr_run
    assert run_cli(str(run_dir), "--num-kv-heads", "2", "--analyses", "knockout",
                   "--device", "cpu", "--output-dir", str(out)) == 0
    assert analyze_components.main(["roles", roles_cell(out),
                              "--roles-allow-missing-views"]) == 0

    elsewhere = str(tmp_path / "second")
    assert run_cli(str(run_dir), "--num-kv-heads", "2", "--analyses", "knockout",
                   "--device", "cpu", "--output-dir", elsewhere,
                   "--knockout-families",
                   "--knockout-roles-from", roles_cell(out)) == 0

    payload = read_json(elsewhere, *CELL, knockout.SUBDIR,
                        knockout.FAMILY_JSON_NAME)
    assert payload["grouping"]["read_from"] == roles_cell(out)


def test_a_role_on_a_component_outside_this_circuit_is_dropped_and_counted(
        sdr_run, cli_model, tmp_path):
    """A completeness sweep's rows carry roles too, and they are not the circuit.

    `path_patching`'s sweep appends the Components it scored from outside the
    circuit, and the roles pass gives every one of them a role. Knocking those
    out would widen the family past the circuit under study, so they are
    dropped and the count is recorded where the figure's reader can see it.
    """
    from component_analysis.head_table import write_head_table

    run_dir, out, _records = sdr_run
    assert run_cli(str(run_dir), "--num-kv-heads", "2", "--analyses", "knockout",
                   "--device", "cpu", "--output-dir", str(out)) == 0
    assert analyze_components.main(["roles", roles_cell(out),
                              "--roles-allow-missing-views"]) == 0
    rows = load_head_table(roles_cell(out))
    rows.append({"kind": "head", "layer": 1, "index": 3,
                 "roles.role_proposed": "unknown"})
    write_head_table(roles_cell(out), rows)

    family_out = str(tmp_path / "families")
    assert run_cli(str(run_dir), "--num-kv-heads", "2", "--analyses", "knockout",
                   "--device", "cpu", "--output-dir", family_out,
                   "--knockout-families", "--knockout-roles-from",
                   roles_cell(out)) == 0

    payload = read_json(family_out, *CELL, knockout.SUBDIR,
                        knockout.FAMILY_JSON_NAME)
    assert payload["grouping"]["n_outside_this_circuit"] == 1
    assert payload["grouping"]["outside_this_circuit"] == [["head", 1, 3]]
    members = [tuple(one) for family in payload["families"]
               for one in family["members"]]
    assert ("head", 1, 3) not in members, "not in the circuit, so not ablated"


def test_families_without_a_role_column_are_refused_by_name(sdr_run, cli_model):
    """A silent empty family set would look like a circuit with no roles."""
    run_dir, out, _records = sdr_run

    with pytest.raises(SystemExit, match="roles"):
        run_cli(str(run_dir), "--num-kv-heads", "2", "--analyses", "knockout",
                "--device", "cpu", "--output-dir", str(out),
                "--knockout-families")


def test_a_dry_run_sizes_the_family_pass_and_writes_nothing(sdr_run, cli_model,
                                                            tmp_path, capsys):
    run_dir, out, _records = sdr_run
    assert run_cli(str(run_dir), "--num-kv-heads", "2", "--analyses", "knockout",
                   "--device", "cpu", "--output-dir", str(out)) == 0
    assert analyze_components.main(["roles", roles_cell(out),
                              "--roles-allow-missing-views"]) == 0

    dry = str(tmp_path / "dry")
    assert run_cli(str(run_dir), "--num-kv-heads", "2", "--analyses", "knockout",
                   "--dry-run", "--output-dir", dry, "--knockout-families",
                   "--knockout-roles-from", roles_cell(out)) == 0

    printed = capsys.readouterr().out
    assert "role famil" in printed
    assert knockout.FAMILY_JSON_NAME not in str(written_files(dry))


def test_the_roles_the_families_were_built_from_are_the_ones_in_the_table(
        sdr_run, cli_model, tmp_path):
    run_dir, out, _records = sdr_run
    run_roles_then_families(run_dir, out, str(tmp_path / "families"))

    rows = load_head_table(roles_cell(out))
    proposed = {(r["kind"], r["layer"], r["index"]): r.get("roles.role_proposed")
                for r in rows}
    payload = read_json(str(tmp_path / "families"), *CELL, knockout.SUBDIR,
                        knockout.FAMILY_JSON_NAME)
    for family in payload["families"]:
        for member in family["members"]:
            assert proposed[tuple(member)] == family["role"]
    assert {one["role"] for one in payload["families"]} <= set(roles.ROLES)


def test_the_family_run_keeps_the_role_columns_it_grouped_by(sdr_run, cli_model):
    """The default --knockout-roles-from is this cell, and a run rewrites it.

    Every analysis run rebuilds the head table from the intake's rows, so
    without the carry-through a family run would read a role, ablate by it, and
    write a table with no role column left in it — the grouping its own figure
    was built from, gone from the table the figure sits beside.
    """
    run_dir, out, _records = sdr_run
    assert run_cli(str(run_dir), "--num-kv-heads", "2", "--analyses", "knockout",
                   "--device", "cpu", "--output-dir", str(out)) == 0
    assert analyze_components.main(["roles", roles_cell(out),
                                    "--roles-allow-missing-views"]) == 0
    before = {(r["kind"], r["layer"], r["index"]): r["roles.role_proposed"]
              for r in load_head_table(roles_cell(out))}

    assert run_cli(str(run_dir), "--num-kv-heads", "2", "--analyses", "knockout",
                   "--device", "cpu", "--output-dir", str(out),
                   "--knockout-families") == 0

    after = {(r["kind"], r["layer"], r["index"]): r.get("roles.role_proposed")
             for r in load_head_table(roles_cell(out))}
    assert after == before
    families = read_json(out, *CELL, knockout.SUBDIR,
                         knockout.FAMILY_JSON_NAME)["families"]
    for family in families:
        for member in family["members"]:
            assert after[tuple(member)] == family["role"]
