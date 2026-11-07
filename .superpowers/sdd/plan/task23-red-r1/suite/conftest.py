"""Isolated test root: candidate imports and source pins are asserted before tests."""
import importlib.util
import json
import os
from pathlib import Path


def pytest_sessionstart(session):
    packet = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('a3_t1_packet', packet / 'run_packet.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    module.check_pins()
    candidate = Path(os.environ['A3_T1_CANDIDATE'])
    assert candidate.resolve() == module.CANDIDATE.resolve()
    origins = module.origin_assert(candidate)
    import torch
    torch.set_num_threads(1)
    output = Path(os.environ['A3_T1_OUTPUT'])
    (output / 'candidate-origins.json').write_text(json.dumps(origins, indent=2) + '\n')
    preflight_spec = importlib.util.spec_from_file_location('a3_t23_fixture_preflight', packet / 'fixture_preflight.py')
    preflight = importlib.util.module_from_spec(preflight_spec); preflight_spec.loader.exec_module(preflight)
    preflight.run(output / 'fixture-preflight')


def pytest_sessionfinish(session, exitstatus):
    packet = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('a3_t1_packet_final', packet / 'run_packet.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    module.check_pins()
