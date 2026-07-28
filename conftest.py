"""Put the repo root on sys.path so tests can import analysis/models/evaluation."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# The CPU tests run a 2-layer, 64-hidden model. At the login node's default
# thread count each of those tiny GEMMs spends ~50 ms in OpenMP synchronisation,
# which turns a 2-second suite into a 2-minute one.
import torch  # noqa: E402

torch.set_num_threads(1)
