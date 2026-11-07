"""Prepare reviewable proposals only; never edit candidate or failed packet."""
import ast
import difflib
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parent.parent / 'plan-a3/direction-preallocation-candidate183'
FAILED = HERE.parent / 'task23-red-r1'
fixture_path = CANDIDATE / 'tests/a3_prepared_integration_cases.py'
old = fixture_path.read_text()
new = old.replace("        d = self.design; p = self.protocol\n", """        d = self.design; p = self.protocol
        if selected:
            # Synthetic selected domain only. Keep all tasks/seeds, all 199/32
            # axes, microbatch/tile/padding policies and 63 invocation classes.
            from component_analysis import ladder_tasks
            for task, spec in d['tasks'].items():
                spec['selection_ids'] = spec['selection_ids'][:1]
                d['access_rows'][task] = [row for row in d['access_rows'][task]
                    if row['split'] != 'validation' or row['instance_id'] in spec['selection_ids']]
            d['utility']['ioi'] = d['utility']['ioi'][:1]
            d['utility']['mmlu'] = d['utility']['mmlu'][:2]
            d['utility']['ioi_maps'] = ladder_tasks.ioi_item_swap_maps(d['utility']['ioi'])
            d['utility']['mmlu_maps'] = ladder_tasks.mmlu_calibration_maps(d['utility']['mmlu'])
""", 1)
new = new.replace("        r.freeze_operational_contract(d, p, settings)\n", """        # Regenerate every protocol/source/utility binding with the ORIGINAL
        # factory; never relabel the previous larger selected backing.
        d.pop('direction_protocol', None); d.pop('direction_protocol_sha256', None)
        p = a3_pipeline.direction_protocol(d, commit=p['commit'],
            injected_code_hashes=closure, execution_settings=settings)
        self.protocol = p
""", 1)
ast.parse(new)
(HERE / 'fixture.py.proposed').write_text(new)
(HERE / 'fixture-domain-only.diff').write_text(''.join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
    fromfile='failed/tests/a3_prepared_integration_cases.py', tofile='proposed/tests/a3_prepared_integration_cases.py')))
runner_path = FAILED / 'run_packet.py'; old = runner_path.read_text()
start = "            result = subprocess.run(argv, env=env, cwd=str(PACKET), capture_output=True, text=True, timeout=360)\n"
end = "            cases = ET.parse(sub / 'junit.xml').getroot().findall('.//testcase')\n"
left = old.index(start); right = old.index(end, left)
newblock = """            row = dict(python=python, argv=argv, status='PYTEST_STARTED',
                pytest_exit_code=None, normal_completion=False)
            manifest['results'][name] = row; save()
            try:
                result = subprocess.run(argv, env=env, cwd=str(PACKET), capture_output=True, text=True, timeout=360)
            except subprocess.TimeoutExpired as error:
                def decoded(value): return value.decode(errors='replace') if isinstance(value, bytes) else value or ''
                (sub / 'pytest.stdout').write_text(decoded(error.stdout))
                (sub / 'pytest.stderr').write_text(decoded(error.stderr))
                row.update(status='PYTEST_TIMEOUT', timed_out=True, timeout_seconds=360,
                    stdout_path=str(sub / 'pytest.stdout'), stderr_path=str(sub / 'pytest.stderr'))
                save(); raise RuntimeError('pytest timed out; no RED evidence') from error
            (sub / 'pytest.stdout').write_text(result.stdout); (sub / 'pytest.stderr').write_text(result.stderr)
            row.update(status='PYTEST_EXITED', pytest_exit_code=result.returncode,
                termination_signal=-result.returncode if result.returncode < 0 else None,
                stdout_path=str(sub / 'pytest.stdout'), stderr_path=str(sub / 'pytest.stderr'))
            save()  # Preserve raw child status BEFORE source checks or XML parsing.
            check_pins()
            junit = sub / 'junit.xml'
            if not junit.is_file():
                row.update(status='MISSING_JUNIT', junit_present=False,
                    fixture_preflight_manifest=str(sub / 'fixture-preflight/run_manifest.json'))
                save(); raise RuntimeError('pytest exited %s without JUnit; no RED evidence' % result.returncode)
"""
new = old[:left] + newblock + old[right:]
# Retain the raw observation row when adding normal JUnit/task evidence.
new = new.replace("            row = dict(python=python, argv=argv, pytest_exit_code=result.returncode,", "            row.update(python=python, argv=argv, pytest_exit_code=result.returncode,", 1)
new = new.replace("            else:\n                assert result.returncode == 0 and not failures, row\n        manifest.update(status=args.mode + '_EXPECTED', normal_completion=True, exit_code=0)",
    "            else:\n                assert result.returncode == 0 and not failures, row\n            row.update(status=args.mode + '_EXPECTED', normal_completion=True); save()\n        manifest.update(status=args.mode + '_EXPECTED', normal_completion=True, exit_code=0)", 1)
ast.parse(new)
(HERE / 'run_packet.py.proposed').write_text(new)
(HERE / 'runner-child-status.diff').write_text(''.join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
    fromfile='failed/run_packet.py', tofile='proposed/run_packet.py')))
print('PROPOSALS_AST_OK; no candidate or packet edits')
