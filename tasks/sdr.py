"""SDR task — Selective Disclosure Report, the omission mechanism (Llama only)."""

from tasks.deception import DeceptionTask


class SDRTask(DeceptionTask):
    name = "sdr"
    display_name = "SDR (Selective Disclosure Report)"
    mechanism = "omission"
