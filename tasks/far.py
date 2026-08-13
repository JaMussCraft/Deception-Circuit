"""FAR task — Falsified Audit Report, the fabrication mechanism (Llama only)."""

from tasks.deception import DeceptionTask


class FARTask(DeceptionTask):
    name = "far"
    display_name = "FAR (Falsified Audit Report)"
    mechanism = "fabrication"
