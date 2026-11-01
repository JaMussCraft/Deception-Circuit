"""Component sets for the B3 transfer test (plan section 3.1).

Members are read from the mechanism-analysis phase-1 readings, `rab.<task>.deciding_numbers.members`, whose names
are `head.L.H` and `mlp.L.0`. They are returned as `component_analysis.hooks` keys, `("head", L, H)` and
`("mlp", L, 0)`, so they can be passed straight to `capture_forward(..., replacements=...)`.

- `S_far`, `S_ser`: the FAR and SER deciding sets (20 each, 9 shared), in the file's order.
- `S_q`: the quartet L17H24 to L17H27.
- `S_all`: S_far, then the new S_ser members, then the new S_q members (35 expected).
- `gupta6`: Gupta's readers L18H28, L16H19, L20H14 and writers L17H24, L15H8, L15H11.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READINGS = ROOT / "docs" / "research" / "mechanism-analysis" / "phase1" / "p1c_readings.json"

S_Q = [("head", 17, h) for h in range(24, 28)]
GUPTA6 = [("head", 18, 28), ("head", 16, 19), ("head", 20, 14), ("head", 17, 24), ("head", 15, 8),
          ("head", 15, 11)]
GUPTA_WRITERS = [("head", 17, 24), ("head", 15, 8), ("head", 15, 11)]


def name_to_key(name):
    kind, layer, idx = name.split(".")
    if kind not in ("head", "mlp"):
        raise ValueError(f"unknown component kind in {name!r}")
    return (kind, int(layer), int(idx))


def key_to_name(key):
    kind, layer, idx = key
    return f"{kind}.{layer}.{idx}"


def _union(*groups):
    out, seen = [], set()
    for g in groups:
        for k in g:
            if k not in seen:
                seen.add(k)
                out.append(k)
    return out


def load_sets(path=READINGS):
    """-> {"S_far", "S_ser", "S_q", "S_all", "gupta6", "gupta_writers"}, each a list of hooks keys."""
    rab = json.loads(Path(path).read_text())["rab"]
    far = [name_to_key(n) for n in rab["far"]["deciding_numbers"]["members"]]
    ser = [name_to_key(n) for n in rab["ser"]["deciding_numbers"]["members"]]
    s_all = _union(far, ser, S_Q)
    if len(s_all) != 35:
        raise ValueError(f"S_all has {len(s_all)} members, expected 35")
    return {"S_far": far, "S_ser": ser, "S_q": list(S_Q), "S_all": s_all, "gupta6": list(GUPTA6),
            "gupta_writers": list(GUPTA_WRITERS)}
