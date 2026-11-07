import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from component_analysis import a3_direction_runtime as r
from tests.test_a3_direction_runtime import _fake_pilot_inputs
from tests.test_a3_direction_runner import fake
from tests.test_a3_direction_workload import ledger


def test_admission_dry_run_preserves_files_and_does_not_publish_startup(tmp_path,fake,monkeypatch,capsys):
    _,d,p=_fake_pilot_inputs(1)
    d['direction_protocol']=p;d['direction_protocol_sha256']=r.ladder.design._hash(p)
    r.ladder.write_artifact(tmp_path/'design.json',d)
    pilot=r.workload.build_inventory(d,p,stage='prefit')
    r.run_pilot(object(),d,p,pilot,root=tmp_path,args=SimpleNamespace(pilot_part='prefit',selected=None),guard=lambda:None,startup_seconds=0)
    target=r.read_object(tmp_path/'pilot-target-inventory'/'prefit')
    budget=ledger(target);budget['storage_capacities']['host_ram']['available_bytes']=10**12
    monkeypatch.setattr(r,'live_guard',lambda *a,**kw:None)
    monkeypatch.setattr(r,'normalize_ledger',lambda *a,**kw:budget)
    before={str(x.relative_to(tmp_path)):x.read_bytes() for x in tmp_path.rglob('*') if x.is_file()}
    result=r.main(['--experiment','directions','--stage','prepare','--action','admit','--dry-run',
        '--design',str(tmp_path/'design.json'),'--commit',p['commit'],'--work-dir',str(tmp_path),
        '--inventory',str(tmp_path/'pilot-target-inventory'/'prefit'),'--ledger-snapshot',str(tmp_path/'fixture-ledger'),
        '--pilot-receipts',str(tmp_path/'pilot'/'prefit')])
    after={str(x.relative_to(tmp_path)):x.read_bytes() for x in tmp_path.rglob('*') if x.is_file()}
    output=capsys.readouterr().out
    print(json.dumps(dict(exit_code=result,files_before=len(before),files_after=len(after),added_files=sorted(set(after)-set(before)),cli_output=output)))
    assert result==0 and json.loads(output)['writes'] is False
    assert after==before
