"""Root-run bounded CPU-only dual-environment RED observer (not admission)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

PACKET = Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task1')
TEST = PACKET.parents[1] / 'plan-a2-full-score-operational186/candidate/tests/test_full_score_controller.py'
PYTHONS = ['/sw/external/python/anaconda3/bin/python3.9', '/u/swong2/.conda/envs/mgnp/bin/python']


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def command(python, output, number):
    return [python, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '--noconftest',
            '--tb=short', '--junitxml=' + str(output / ('env%d.xml' % number)),
            '--basetemp=' + str(output / ('tmp-env%d' % number)), str(TEST)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output)
    pins = json.loads((PACKET / 'pins.json').read_text())
    for path, wanted in pins['files'].items():
        assert digest(path) == wanted, ('changed frozen RED packet/source', path)
    for path in pins['expected_absent']:
        assert not Path(path).exists(), ('RED baseline implementation appeared', path)
    commands = [command(python, output, n) for n, python in enumerate(PYTHONS, 1)]
    if args.dry_run:
        print(json.dumps(dict(packet=str(PACKET), tests=str(TEST), commands=commands,
                              per_environment_timeout_seconds=120, gpu=False), indent=2))
        return 0
    assert os.environ.get('SLURM_JOB_ID'), 'root must dispatch this bounded suite as a CPU job'
    assert not os.environ.get('SLURM_JOB_GPUS'), 'CPU-only packet refuses GPU allocation'
    assert int(os.environ.get('SLURM_CPUS_PER_TASK', '0')) >= 2
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
    observations = []
    started = time.time()
    for n, (python, cmd) in enumerate(zip(PYTHONS, commands), 1):
        version = subprocess.check_output([python, '-c', 'import json,sys,pytest; print(json.dumps({"python":list(sys.version_info[:3]),"executable":sys.executable,"pytest":pytest.__version__}))'], env=env, universal_newlines=True, timeout=15)
        observed = json.loads(version)
        assert observed['python'][:2] == ([3, 9] if n == 1 else [3, 12]), observed
        with (output / ('env%d.stdout' % n)).open('x') as stdout, (output / ('env%d.stderr' % n)).open('x') as stderr:
            child = subprocess.run(cmd, env=env, cwd=str(TEST.parent), stdout=stdout, stderr=stderr, timeout=120)
        tree = ET.parse(str(output / ('env%d.xml' % n)))
        cases = list(tree.iter('testcase'))
        failures = [item for item in cases if item.find('failure') is not None]
        errors = [item for item in cases if item.find('error') is not None]
        assert child.returncode == 1 and not errors and cases, ('not attributable test RED', n, child.returncode)
        assert len(failures) == len(cases), ('unexpected pass/skip', n, len(failures), len(cases))
        for item in failures:
            assert 'FULL_SCORE_IMPLEMENTATION_MISSING' in ''.join(item.find('failure').itertext()), item.attrib
        observations.append(dict(environment=observed, exit_code=child.returncode,
                                 tests=len(cases), failures=len(failures), errors=len(errors),
                                 test_names=[item.attrib['name'] for item in cases], command=cmd))
    assert observations[0]['test_names'] == observations[1]['test_names']
    result = dict(status='RED_OBSERVED_NO_IMPLEMENTATION_AUTHORITY', cluster='delta',
                  actual_job_id=os.environ['SLURM_JOB_ID'], gpu=False,
                  pins_sha256=digest(PACKET / 'pins.json'), observations=observations,
                  elapsed_seconds=time.time() - started, no_scientific_execution=True)
    (output / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
