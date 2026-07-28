"""Put the repo root on sys.path so tests can import analysis/models/evaluation."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
