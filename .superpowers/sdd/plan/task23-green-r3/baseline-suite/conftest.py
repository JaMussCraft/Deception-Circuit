import importlib.util,json,os
from pathlib import Path

def pytest_sessionstart(session):
    packet=Path(__file__).resolve().parents[1]
    spec=importlib.util.spec_from_file_location('baseline_pins',packet/'run_packet.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.check_pins();module.origin_assert(packet/'baseline-source')
    # Only missing observation helpers are installed for identical fixture setup.
    # The old resource validator and actual native run_phase remain unchanged.
    import ast
    from component_analysis import a3_direction_runtime as runtime
    tree=ast.parse((packet/'baseline_observer_support.py').read_text())
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
    assert {n.name for n in functions}=={'_prepared_cpu_family','_prepared_storage_identity','_prepared_receiver_context'}
    assert all(not hasattr(runtime,n.name) for n in functions)
    exec(compile(ast.Module(body=functions,type_ignores=[]),str(packet/'baseline_observer_support.py'),'exec'),runtime.__dict__)

    import torch
    torch.set_num_threads(1)

def pytest_sessionfinish(session,exitstatus):
    packet=Path(__file__).resolve().parents[1]
    spec=importlib.util.spec_from_file_location('baseline_final_pins',packet/'run_packet.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.check_pins()
