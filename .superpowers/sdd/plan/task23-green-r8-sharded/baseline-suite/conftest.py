import importlib.util,json,os
from pathlib import Path

def pytest_sessionstart(session):
    packet=Path(__file__).resolve().parents[1]
    spec=importlib.util.spec_from_file_location('baseline_pins',packet/'run_packet.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.check_pins();module.origin_assert(packet/'baseline-source')
    import torch
    torch.set_num_threads(1)

def pytest_sessionfinish(session,exitstatus):
    packet=Path(__file__).resolve().parents[1]
    spec=importlib.util.spec_from_file_location('baseline_final_pins',packet/'run_packet.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.check_pins()
