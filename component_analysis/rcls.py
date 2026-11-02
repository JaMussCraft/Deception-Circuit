"""R-cls, the phase-1 role class of one Component from its knockout drops on D, H and F.

Ported unchanged (constants, `significant_sign`, `d_of`, `se_d` and `rcls`) from the untracked
`outputs/_launch_mechanism_analysis/p1_readings.py`, lines 12 to 68, which produced
`docs/research/mechanism-analysis/phase1/rcls.csv` and F-mech-009 from the item-swap sweeps S1 (D), S5 (H) and S6 (F)
(selection sample, n = 100, seed 0, all positions, U binding, H100 job 49825318). Instructed-route B2 P3 reuses it on
the `knockout/groups.json` of its held-out cells; `tests/test_instructed_route_b2_read.py` checks that the port
reproduces `rcls.csv` to 1e-9 on SER mlp.11, mlp.13, mlp.16 and FAR mlp.13.

Definitions (mechanism-analysis spec 2.2, amended per R16):

- d_c(X) is the knockout drop of Component c on test set X over X's clean margin, signed, each in X's own target
  direction: deceptive on D, honest on H and F. A positive d on H or F means "supports the honest answer".
- A drop is significant when |drop| is at least 2 SE and at least 0.01 logits (`docs/component-roles.md`).
- m_HF is the maximum over H and F of max(d, 0). U_HF is the maximum over H and F of max(d + 1.96 SE(d), 0), the upper
  95% bound of the honest-side effect.
- The classes are checked in order. "opposes": d(D) significantly negative. "shared": d(D) and d(H) or d(F)
  significantly positive with d(D) / m_HF in [0.5, 2]. "deception-leaning": d(D) significantly positive and
  d(D) >= 2 U_HF, once "opposes" and "shared" are ruled out. "honest-leaning": d(H) or d(F) significantly positive
  and m_HF >= 2 d(D). Otherwise "none", with a reason.

Each argument of `rcls` is {"drop", "se", "clean"} in logits: a sweep or groups row's `mean_drop` and
`standard_error`, and the cell's `clean_run.mean_logit_difference`.
"""

from __future__ import annotations

MIN_DROP = 0.01          # logits
N_SE = 2.0
Z95 = 1.96
EPS = 1e-12


def significant_sign(e: dict) -> int:
    """+1 / -1 when the drop is significant in that direction, else 0. e = {"drop", "se"} in logits."""
    drop, se = e["drop"], e["se"]
    if abs(drop) + EPS >= N_SE * se and abs(drop) + EPS >= MIN_DROP:
        return 1 if drop > 0 else -1
    return 0


def d_of(e: dict) -> float:
    return e["drop"] / e["clean"]


def se_d(e: dict) -> float:
    return e["se"] / abs(e["clean"])


def rcls(D: dict, H: dict, F: dict) -> dict:
    """R-cls (spec 2.2, amended per R16), checked in order: opposes, shared, deception-leaning, honest-leaning, none.

    Each argument is {"drop", "se", "clean"} for the Component on that test set (S1 for D, S5 for H, S6 for F).
    """
    d = {"D": d_of(D), "H": d_of(H), "F": d_of(F)}
    sig = {"D": significant_sign(D), "H": significant_sign(H), "F": significant_sign(F)}
    m_hf = max(max(d["H"], 0.0), max(d["F"], 0.0))
    u_hf = max(max(d["H"] + Z95 * se_d(H), 0.0), max(d["F"] + Z95 * se_d(F), 0.0))
    hf_pos = sig["H"] > 0 or sig["F"] > 0
    out = {"d": d, "sig": sig, "m_HF": m_hf, "U_HF": u_hf, "reason": ""}
    if sig["D"] < 0:
        out["class"] = "opposes"
        return out
    if sig["D"] > 0 and hf_pos and m_hf > 0 and 0.5 - EPS <= d["D"] / m_hf <= 2.0 + EPS:
        out["class"] = "shared"
        return out
    if sig["D"] > 0 and d["D"] + EPS >= 2.0 * u_hf:
        out["class"] = "deception-leaning"
        return out
    if hf_pos and m_hf + EPS >= 2.0 * d["D"]:
        out["class"] = "honest-leaning"
        return out
    out["class"] = "none"
    if sig["D"] > 0 and hf_pos:
        out["reason"] = "D and H/F both significant, ratio outside [0.5, 2] and no factor-two dominance"
    elif sig["D"] > 0:
        out["reason"] = "D significant, H/F not significant but their upper 95% bound exceeds d(D) / 2"
    elif hf_pos:
        out["reason"] = "H/F significant but below twice d(D)"
    else:
        out["reason"] = "nothing significant"
    return out
