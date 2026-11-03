"""Isolate independent external tests from any ancestor worktree conftest."""
import pathlib,os,sys,json,importlib
ROOT=pathlib.Path(os.environ['REVIEW150_RUNTIME']).resolve();sys.path.insert(0,str(ROOT))
import pytest
PREFIXES=('component_analysis','dataset','models','tests','l0')
SNAPSHOTS={}
def check(phase):
    found={name:module.__file__ for name,module in list(sys.modules.items()) if name.split('.')[0] in PREFIXES and getattr(module,'__file__',None)}
    SNAPSHOTS[phase]=found
    pathlib.Path(os.environ['REVIEW150_IMPORTS']).write_text(json.dumps(SNAPSHOTS,indent=2)+'\n')
    assert all(pathlib.Path(path).resolve().is_relative_to(ROOT) for path in found.values()),found
class Plugin:
    def pytest_sessionstart(self,session):
        sys.path.insert(0,str(ROOT))
        w=importlib.import_module('component_analysis.a3_direction_workload')
        assert callable(getattr(w,'mask_replacement_policy',None)),str(w.__file__)
        check('before')
    def pytest_sessionfinish(self,session,exitstatus):check('after')
raise SystemExit(pytest.main(sys.argv[1:],plugins=[Plugin()]))
