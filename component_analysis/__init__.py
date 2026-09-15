"""
component_analysis — component-level analysis of discovered deception circuits.

The evaluator (`evaluate_circuit.py`) treats a circuit as an opaque set of
gates and asks whether it is faithful and necessary. This package zooms in: it
coarsens a circuit to its **Components** (attention heads and MLP blocks, in
the vocabulary of CONTEXT.md), and the later analyses — attention patterns,
direct logit attribution, logit lens, knockout, path patching — each add
namespaced columns to one head table keyed by Component.

Layout
------
    components.py   mask object -> Components (pure Python, no model)
    head_table.py   the one table every analysis writes into (CSV + JSON)
    intake.py       circuit / reference / task resolution and the cell layout
    hooks.py        every nnsight call in the package, and nothing else

Only `hooks.py` imports nnsight, and it does so inside its functions, so the
rest of the package imports in the login-node environment where nnsight cannot
be installed (it needs Python >= 3.10). The CLI is `analyze_components.py` at
the repo root, beside `evaluate_circuit.py`.

The package is named `component_analysis` rather than `analysis` because
`analysis.py` at the repo root is the node-mask extraction module and an
`analysis/` package would shadow it.
"""
