"""Say whether a cell directory holds every analysis output, and name what it does not.

The notebook's seam (`component_analysis/review.py`) already answers this
question for a human: every view function returns a falsy `Missing` naming the
files it looked for. This walks the same view functions over a cell and prints
one line per view, so an agent with no browser can check a finished run without
executing the notebook.

    python scripts/check_cell.py outputs/_analyses/<suite>/<circuit>/<task>

Exit status is 0 when every view is present, 1 when any is missing. A view that
is missing because its analysis was deliberately not run is still reported as
missing; the caller decides whether that is expected.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from component_analysis import review  # noqa: E402

#: `(label, callable)`, in the order the notebook renders them.
VIEWS = (
    ("head table", review.head_table_view),
    ("attention patterns", review.attention_views),
    ("attention top heads", review.top_heads_view),
    ("dla", review.dla_view),
    ("dla heatmap", review.dla_heatmap),
    ("dla paired scatter", review.dla_scatter_view),
    ("logit lens", review.logit_lens_views),
    ("knockout", review.knockout_view),
    ("family knockout", review.family_knockout_view),
    ("path patching", review.path_patching_views),
    ("completeness sweep", review.sweep_view),
    ("segmentation", review.segmentation_view),
    ("sample", review.sample_view),
)


def check(results_dir: str) -> int:
    missing = 0
    for label, view_of in VIEWS:
        try:
            view = view_of(results_dir)
        except Exception as error:  # a malformed file is a failure, not an absence
            print(f"  BROKEN   {label}: {type(error).__name__}: {error}")
            missing += 1
            continue
        if view:
            print(f"  present  {label}")
            if view_of is review.head_table_view:
                # What an agent would otherwise only see in the notebook: a
                # cell read under renamed columns, or one with no coverage.
                if view.renamed_columns:
                    print("           legacy names read as: " + ", ".join(
                        f"{old} -> {new}"
                        for old, new in view.renamed_columns.items()))
                if not view.coverage:
                    print("           no per-column coverage in the meta "
                          "(written before ticket 13)")
        else:
            print(f"  Missing  {label}: {view.note}")
            missing += 1
    return missing


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        raise SystemExit(__doc__)
    status = 0
    for results_dir in argv:
        print(results_dir)
        if check(results_dir):
            status = 1
    return status


if __name__ == "__main__":
    raise SystemExit(main())
