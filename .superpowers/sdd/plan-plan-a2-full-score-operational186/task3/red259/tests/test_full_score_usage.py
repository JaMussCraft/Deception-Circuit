"""Removing live ordinary80 cap or conservative native projection fails cases."""
import copy
import datetime
import json
from types import SimpleNamespace

import pytest
from test_full_score_release import module, rejects

NOW=2000000000
RESET=NOW+86400


def fixture(live=20,cached=20,since=80,index=3,label='fresh',exception='expired'):
    checked=datetime.datetime.fromtimestamp(NOW,datetime.timezone.utc).isoformat()
    u=dict(status='ok',should_pause=False,checked_at=checked,
           weekly=dict(used_percent=live,resets_at=RESET))
    s=('session exact\nlast reading: five-hour not applicable, seven-day %s%%, Fable unknown%% at %s (%s)\n'
       'session points %s (%s since register); cadence 40; next checkpoint %s at +%s\n'
       'freeze: none; acked\nweekly cap exception: %s (last observed); captured reset %s')%(
           cached,checked,label,since+5,since,index,index*40,exception,RESET)
    return u,s


def invoke(m,monkeypatch,**kw):
    monkeypatch.setattr(m.time,'time',lambda:NOW)
    u,s=fixture(**kw)
    return m.validate_usage(u,s,'exact')


def test_current_cadence40_no_obsolete17_or33_boundary(monkeypatch):
    m=module();r=invoke(m,monkeypatch,live=45,cached=44,since=100)
    assert r['cadence']=='40' and r['next_at_plus']=='120'
    assert r['projected_points']=='106'


@pytest.mark.parametrize('live',[80,80.001,95])
@pytest.mark.parametrize('exception',['active','expired'])
def test_ordinary80_cannot_be_bypassed_by_old_exception(monkeypatch,live,exception):
    m=module();invoke(m,monkeypatch)
    with pytest.raises(rejects(m)):invoke(m,monkeypatch,live=live,cached=79,exception=exception)


def test_live79_999_below_cap_passes_without_exception(monkeypatch):
    m=module();r=invoke(m,monkeypatch,live=79.999,cached=79,since=80)
    assert r['live_used_percent']=='79.999'


@pytest.mark.parametrize('live,cached,since',[(21,20,119),(22,20,119),(20,20,120)])
def test_live_minus_cached_projects_at_checkpoint_rejects(monkeypatch,live,cached,since):
    m=module();invoke(m,monkeypatch)
    with pytest.raises(rejects(m)):invoke(m,monkeypatch,live=live,cached=cached,since=since)


def test_cached_status_label_is_telemetry_live_meter_is_authority(monkeypatch):
    m=module();r=invoke(m,monkeypatch,label='unknown or stale')
    assert r['stored_freshness_label']=='unknown or stale'
    assert r['cache_label_authority'] is False


@pytest.mark.parametrize('fault',['rollback','unknown-meter','unknown-status','wrong-session','freeze',
                                  'reset-mismatch','unknown-reset','nonfinite','pause','missing-counters'])
def test_unknown_frozen_mismatched_or_rollback_meter_fails_closed(monkeypatch,fault):
    m=module();invoke(m,monkeypatch);u,s=fixture()
    if fault=='rollback':u['weekly']['used_percent']=19
    elif fault=='unknown-meter':u['status']='unknown'
    elif fault=='unknown-status':s=s.replace('seven-day 20%','seven-day unknown%')
    elif fault=='wrong-session':s=s.replace('session exact','session another')
    elif fault=='freeze':s=s.replace('freeze: none;','freeze: checkpoint 3;')
    elif fault=='reset-mismatch':u['weekly']['resets_at']=RESET+1
    elif fault=='unknown-reset':u['weekly']['resets_at']=None
    elif fault=='nonfinite':u['weekly']['used_percent']=float('nan')
    elif fault=='pause':u['should_pause']=True
    elif fault=='missing-counters':s=s.replace('session points','unavailable points')
    with pytest.raises(rejects(m)):m.validate_usage(u,s,'exact')


def test_usage_command_hardcodes80_and_targets_session_without_private_writes(tmp_path,monkeypatch):
    m=module();u,s=fixture();calls=[]
    monkeypatch.setattr(m.time,'time',lambda:NOW)
    def call(argv,**kw):
        calls.append(argv)
        return SimpleNamespace(stdout=json.dumps(u) if argv[0].endswith('codex-usage') else s)
    monkeypatch.setattr(m,'call',call)
    # A caller's obsolete99 must never weaken the actual command's hard80 gate.
    m.usage(dict(usage_pause_percent=99,session='exact'),tmp_path,'probe')
    assert calls==[['/u/swong2/.local/bin/codex-usage','--pause-at','80'],
        ['/u/swong2/.local/bin/research-session','status','--session','exact']]
    assert sorted(p.name for p in tmp_path.iterdir())==['probe-usage.json']
