"""SER task — Selective Emphasis Report, the pragmatic-distortion mechanism."""

from tasks.deception import DeceptionTask


class SERTask(DeceptionTask):
    name = "ser"
    display_name = "SER (Selective Emphasis Report)"
    mechanism = "pragmatic_distortion"
