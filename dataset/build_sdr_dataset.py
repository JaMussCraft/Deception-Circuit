"""build_sdr_dataset.py — thin entry point for the SDR build.

Everything happens in dataset/build_deception_dataset.py; this only pins
--task sdr so the three tasks have the file layout the spec asks for. Any flag
that script accepts is accepted here.

    python dataset/build_sdr_dataset.py --no-model        # CPU dry run
    python dataset/build_sdr_dataset.py                   # GPU build
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataset.build_deception_dataset import main

if __name__ == "__main__":
    main(["--task", "sdr"] + sys.argv[1:])
