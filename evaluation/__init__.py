"""
evaluation package — pluggable evaluations for a node-pruned circuit.

Mirrors `tasks/__init__.py`: an `Evaluation` bundles the work (`run`), the
human-readable rendering (`report`), and any figures (`plots`). Everything they
share — models, loaders, reference caches, mean banks, the random circuit set —
lives on the `EvalContext` they are handed, so a fourth evaluation is one
module, one entry in `_EVALS`, and one entry in `list_evaluations()`.

The three shipped evaluations answer, in order:

  sanity    does the saved mask reproduce the numbers the training run reported?
  knockout  is the circuit *necessary* — does removing it stop the behaviour,
            and at what collateral cost?
  null      does a size-matched random circuit do just as well?
"""


class Evaluation:
    """Base class. Subclasses set the class attributes and implement `run`."""

    name = ""
    display_name = ""

    # Context capabilities this evaluation needs. Currently understood:
    #   "pred_spec"  the task implements Task.pred_spec (single prediction pos)
    #   "wikitext"   the wikitext reference stream was loaded
    requires = ()

    def run(self, ctx) -> dict:
        """Do the work. Must return a JSON-serialisable payload."""
        raise NotImplementedError

    def report(self, payload, ctx) -> None:
        """Print the payload to the (tee'd) log. No return value."""
        raise NotImplementedError

    def plots(self, payload, ctx) -> list:
        """Write any figures; return the paths written."""
        return []


_EVALS = {}


def get_evaluation(name: str) -> Evaluation:
    if name not in _EVALS:
        # Lazy import so `--evals sanity` never imports the wikitext harness.
        if name == "sanity":
            from evaluation.sanity import SanityEvaluation
            _EVALS[name] = SanityEvaluation
        elif name == "knockout":
            from evaluation.knockout import KnockoutEvaluation
            _EVALS[name] = KnockoutEvaluation
        elif name == "null":
            from evaluation.null import NullEvaluation
            _EVALS[name] = NullEvaluation
        else:
            raise ValueError(
                f"Unknown evaluation {name!r}. Choose from {list_evaluations()}.")
    return _EVALS[name]()


def list_evaluations():
    return ["sanity", "knockout", "null"]
