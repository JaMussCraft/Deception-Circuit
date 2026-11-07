"""Root-only bounded fixture observer. GREEN is not execution admission."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

PACKET = Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task1/green-r2')
TEST = PACKET.parents[2] / 'plan-a2-full-score-operational186/candidate/tests/test_full_score_controller.py'
EXTRA_TEST = TEST.with_name('test_full_score_entry198.py')
GPU = TEST.parents[1] / 'gpu'
PYTHONS = ['/sw/external/python/anaconda3/bin/python3.9', '/u/swong2/.conda/envs/mgnp/bin/python']


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def pinned(pins):
    for path, wanted in pins['files'].items():
        assert sha(path) == wanted, ('frozen file changed', path)
    assert sorted(str(x.relative_to(GPU)) for x in GPU.rglob('*') if x.is_file()) == pins['GPU_inventory']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output)
    pins = json.loads((PACKET / 'pins.json').read_text())
    pinned(pins)
    commands = [[python, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '--noconftest', '--tb=short',
                 '--junitxml=' + str(output / ('env%d.xml' % number)),
                 '--basetemp=' + str(output / ('tmp-env%d' % number)), str(TEST), str(EXTRA_TEST)]
                for number, python in enumerate(PYTHONS, 1)]
    if args.dry_run:
        print(json.dumps(dict(packet=str(PACKET), commands=commands, per_environment_timeout_seconds=120,
                              expected_cases=97, gpu=False), indent=2))
        return 0
    assert os.environ.get('SLURM_JOB_ID') and not os.environ.get('SLURM_JOB_GPUS'), 'root CPU allocation required'
    assert int(os.environ.get('SLURM_CPUS_PER_TASK', '0')) >= 2
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
               OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
    expected = json.loads((PACKET / 'expectation.json').read_text())['test_names']
    results = []
    started = time.time()
    for number, (python, command) in enumerate(zip(PYTHONS, commands), 1):
        version = subprocess.check_output([python, '-c', 'import json,sys,pytest; print(json.dumps({"python":list(sys.version_info[:3]),"executable":sys.executable,"pytest":pytest.__version__}))'],
                                          env=env, universal_newlines=True, timeout=15)
        observed = json.loads(version)
        assert observed['python'][:2] == ([3, 9] if number == 1 else [3, 12]), observed
        with (output / ('env%d.stdout' % number)).open('x') as stdout, (output / ('env%d.stderr' % number)).open('x') as stderr:
            run = subprocess.run(command, env=env, cwd=str(TEST.parent), stdout=stdout, stderr=stderr, timeout=120)
        cases = list(ET.parse(str(output / ('env%d.xml' % number))).iter('testcase'))
        failures = [item.attrib['name'] for item in cases if item.find('failure') is not None]
        errors = [item.attrib['name'] for item in cases if item.find('error') is not None]
        skipped = [item.attrib['name'] for item in cases if item.find('skipped') is not None]
        names = [item.attrib['name'] for item in cases]
        passed = run.returncode == 0 and len(cases) == 97 and names == expected and not failures and not errors and not skipped
        results.append(dict(environment=observed, exit_code=run.returncode, tests=len(cases), failures=failures,
                            errors=errors, skipped=skipped, command=command, test_names=names, green=passed))
    pinned(pins)
    success = all(row['green'] for row in results)
    result = dict(status='GREEN_OBSERVED_NO_EXECUTION_AUTHORITY' if success else 'FIXTURE_FAILED',
                  actual_job_id=os.environ['SLURM_JOB_ID'], cluster='delta', gpu=False,
                  pins_sha256=sha(PACKET / 'pins.json'), observations=results,
                  elapsed_seconds=time.time() - started, no_scientific_execution=True)
    (output / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
