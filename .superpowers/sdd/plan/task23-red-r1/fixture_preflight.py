"""Original-validator fixture preflight; CPU-only, never production admission."""
import json
from pathlib import Path
import time


def run(output):
    import pytest
    from tests.a3_prepared_integration_cases import PreparedCase
    import sys
    candidate = Path(__file__).resolve().parents[2] / 'plan-a3/direction-preallocation-candidate183'
    assert Path(sys.modules[PreparedCase.__module__].__file__).resolve() == (candidate / 'tests/a3_prepared_integration_cases.py').resolve()
    output = Path(output); output.mkdir()
    manifest = dict(kind='a3_injected_integration_fixture_preflight_v1', injected=True,
        model_loaded=False, execution_authorized=False, operational_admission=False,
        normal_completion=False, status='STARTED', results={})
    def save(): (output / 'run_manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    save()
    try:
        for part in ('prefit', 'selected'):
            manifest['active_case'] = part; save(); started = time.perf_counter()
            with pytest.MonkeyPatch.context() as patch:
                c = PreparedCase(output / part, patch, part=part, selected=(part == 'selected'))
                r = c.r; r.workload._validate_inventory(c.pilot_inventory)
                guard = c.guard()  # Original live source/protection, inventory and root validators, not a fake context.
                reservation = guard['reservation']
                assert reservation['allocation_verified'] is True
                assert c.loader_calls == []
                if part == 'selected':
                    selected, arrays = r.read_bundle(c.args.selected)
                    assert selected == c.selected and len(selected['selected_records']) == 9
                    assert not selected['blocked_task_seeds'] and arrays
                manifest['results'][part] = dict(status='FIXTURE_ORIGINAL_VALIDATORS_PASS',
                    pilot_stage=c.pilot_inventory['stage'], expected_pilot_stage='prefit' if part == 'prefit' else 'selected-pilot',
                    selected_records=0 if c.selected is None else len(c.selected['selected_records']),
                    model_loader_calls=len(c.loader_calls), wall_seconds=time.perf_counter()-started,
                    injected_allocation_only=True, source_protection_and_root_validators_active=True)
                save()
        manifest.update(status='FIXTURE_PREFLIGHT_COMPLETE', normal_completion=True, exit_code=0)
    except BaseException as error:
        manifest.update(status='FAILED', normal_completion=False, exit_code=1, error=repr(error)); raise
    finally: save()
