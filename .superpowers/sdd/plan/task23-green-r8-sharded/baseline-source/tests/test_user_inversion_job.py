"""Exercise the actual wrapper on CPU with no model or submission."""
import os
from pathlib import Path
import subprocess

REPO = Path(__file__).resolve().parents[1]
WRAPPER = REPO / 'scripts/jobs/specificity_user_inversion.sh'


from tests.test_user_inversion_pipeline import stage


def test_job_dry_run_does_not_submit_or_load_model(stage, monkeypatch):
    p, root, rows, run, calls = stage
    from types import SimpleNamespace
    revision = '0e9e39f249a16976918f6564b8830bc894c89659'
    monkeypatch.setenv('HF_HOME', '/work/nvme/beto/swong2')
    monkeypatch.setenv('HF_HUB_OFFLINE', '1')
    monkeypatch.setenv('TOKENIZERS_PARALLELISM', 'false')
    tok = p.load_tokenizer(SimpleNamespace(model=p.dc.DEFAULT_MODEL, tokenizer_revision=revision))
    overrides = ['--model-revision', revision, '--tokenizer-revision', revision]
    base = run.base + overrides
    p.main(['--stage', 'derive'] + base, tokenizer=tok)
    from dataset.build_deception_dataset import save_splits
    for arm in ('far_v2', 'far_v2_honest'):
        directory = root / 'data' / arm
        save_splits({split: rows[str(directory), split] for split in p.SPLITS}, str(directory))
    env = dict(os.environ, DC_PYTHON='/sw/external/python/anaconda3/bin/python3.9')
    result = subprocess.run(['bash', str(WRAPPER), '--dry-run'] + base,
                            cwd=REPO, text=True, capture_output=True, env=env)
    assert result.returncode == 0, result.stderr
    assert 'CPU dry-run' in result.stdout
    assert 'score_preflight' in result.stdout
    assert not (root / 'scores').exists()
    invalid = subprocess.run(['bash', str(WRAPPER), '--dry-run'] + base + ['--commit', 'bad'],
                             cwd=REPO, text=True, capture_output=True, env=env)
    assert invalid.returncode != 0
    assert '40-hex' in invalid.stderr
    assert not (root / 'scores').exists()


def test_job_refuses_login_execution():
    env = dict(os.environ)
    env.pop('SLURM_JOB_ID', None)
    result = subprocess.run(['bash', str(WRAPPER)], cwd=REPO, text=True, capture_output=True, env=env)
    assert result.returncode != 0
    assert 'Slurm' in result.stderr
