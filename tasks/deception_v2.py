"""The v2 mechanism tasks (mechanism-datasets): FAR / SDR / SER on the aligned
v2 Scaffold (`dataset/deception_v2.py`).

Same objective, readout and dataloaders as v1 (`tasks/deception.py`); only the
dataset directory differs, through `name`: `<data>/<name>` for the deceptive
condition, `<data>/<name>_honest` (the Neutral-Clause Twin) and
`<data>/<name>_nopressure`.
"""

from tasks.deception import DeceptionTask


class FARv2Task(DeceptionTask):
    name = "far_v2"
    display_name = "FAR v2 (Falsified Audit Report)"
    mechanism = "fabrication"


class SDRv2Task(DeceptionTask):
    name = "sdr_v2"
    display_name = "SDR v2 (Selective Disclosure Report)"
    mechanism = "omission"


class SERv2Task(DeceptionTask):
    name = "ser_v2"
    display_name = "SER v2 (Selective Emphasis Report)"
    mechanism = "pragmatic_distortion"
