"""Independent fixture-only diagnosis; candidate files remain unchanged."""
import pathlib,sys
C=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-operational186/candidate')
sys.path.insert(0,str(C/'tests'))
import pytest
from test_full_score_cpu import gpu_c,task1_waiting,task2_from_actual,module
@pytest.mark.parametrize('publication,expected',[(1300.,1250.),(1140.,1125.)])
def test_numeric_prospective_job_preserves_marker_contract(gpu_c,monkeypatch,publication,expected):
 gpu_c['actual_job_id']='456'
 m=module('supervisor');guard,path,waiting=task1_waiting(gpu_c,monkeypatch,publication)
 raw=path.read_bytes();c,r=task2_from_actual(gpu_c,guard,path,raw)
 assert m.validate_request(c,r,waiting,now=1010.)['actual_future_GPU_job_id']=='456'
 assert m.child_deadline(c,waiting,2000.,1900.,now=1010.)==expected
 assert path.read_bytes()==raw
