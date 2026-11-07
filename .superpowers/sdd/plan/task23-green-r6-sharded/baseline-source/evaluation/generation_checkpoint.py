"""One frozen run's raw-token generation checkpoints. No object deserialization."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import tempfile

import torch

SCHEMA = 1
SEGMENT_EXIT_CODE = 75


class GenerationCheckpointError(ValueError):
    """A checkpoint binding/record/commit failure must abort this evaluation."""


class GenerationSegmentComplete(RuntimeError):
    """The requested number of NEW batches was durably saved; eval is incomplete."""


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def tensor_identity(value):
    value = value.detach().cpu().contiguous()
    return {'shape': list(value.shape), 'dtype': str(value.dtype),
            'sha256': hashlib.sha256(value.view(torch.uint8).numpy().tobytes()).hexdigest()}


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name, suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as handle:
            json.dump(value, handle, sort_keys=True, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _read(path):
    try:
        return json.loads(Path(path).read_text())
    except (ValueError, OSError) as error:
        raise GenerationCheckpointError('invalid committed checkpoint %s' % path) from error


def _bind(path, identity):
    try:
        identity = json.loads(json.dumps(identity, sort_keys=True, allow_nan=False))
    except (ValueError, TypeError) as error:
        raise GenerationCheckpointError('checkpoint identity cannot be canonicalized') from error
    record = {'schema': SCHEMA, 'identity': identity, 'sha256': digest(identity)}
    if path.exists():
        if _read(path) != record:
            raise GenerationCheckpointError('checkpoint identity mismatch: %s' % path)
    else:
        try:
            atomic_json(path, record)
        except OSError as error:
            raise GenerationCheckpointError('checkpoint manifest commit failed') from error
    return record['sha256']


class GenerationCheckpoint:
    """A single process holds flock until evaluation/segment exit, never unlinks it."""
    def __init__(self, directory, max_new_batches):
        if type(max_new_batches) is not int or max_new_batches <= 0:
            raise GenerationCheckpointError('checkpoint requires positive max NEW generation batches')
        self.directory = Path(directory)
        self.maximum = max_new_batches
        self.new_batches = 0
        self.lock = None
        self.provenance = {'hostname': socket.gethostname(), 'pid': os.getpid(),
                           'slurm_job_id': os.environ.get('SLURM_JOB_ID')}

    def __enter__(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = open(self.directory / 'writer.lock', 'a+')
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock.close()
            self.lock = None
            raise RuntimeError('generation checkpoint is locked by another process')
        return self

    def __exit__(self, *args):
        if self.lock is not None:
            self.lock.close()
            self.lock = None

    def phase(self, dataset, phase, identity):
        if self.lock is None:
            raise RuntimeError('generation checkpoint requires lifetime writer lock')
        # Names are represented by digests to avoid path/sanitization collisions.
        directory = self.directory / digest(dataset) / digest(phase)
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise GenerationCheckpointError('checkpoint phase creation failed') from error
        phase_id = _bind(directory / 'manifest.json',
                         {'dataset': dataset, 'phase': phase, 'binding': identity})
        return BatchStore(self, directory, phase_id)


class BatchStore:
    def __init__(self, owner, directory, phase_id):
        self.owner, self.directory, self.phase_id = owner, directory, phase_id

    def bind(self, *, clean_ids, corrupt_ids, attention_mask, new_tokens, eos_ids,
             batch_size, use_cache, plan, vocab_size, pad_id):
        self.vocab_size = vocab_size
        self.new_tokens = new_tokens
        self.plan = plan
        self.binding = _bind(self.directory / 'plan.json', {
            'phase': self.phase_id, 'clean': tensor_identity(clean_ids),
            'corrupt': tensor_identity(corrupt_ids), 'attention': tensor_identity(attention_mask),
            'new_tokens': new_tokens, 'eos': sorted(set(int(i) for i in eos_ids)),
            'pad_id': pad_id, 'vocab_size': vocab_size, 'batch_size': batch_size,
            'use_cache': use_cache, 'decoding': 'greedy-argmax-float', 'plan': plan})
        expected = {'batch-%06d.json' % i for i in range(len(plan))}
        if {p.name for p in self.directory.glob('batch-*.json')} - expected:
            raise GenerationCheckpointError('foreign committed checkpoint batch')
        # Validate every committed record before generating any missing batch.
        for i in range(len(plan)):
            self.load(i, device='cpu')

    def load(self, ordinal, device):
        path = self.directory / ('batch-%06d.json' % ordinal)
        if not path.exists():
            return None
        record = _read(path)
        try:
            payload = record['payload']
            if record['sha256'] != digest(payload):
                raise GenerationCheckpointError('checksum mismatch')
            if payload['schema'] != SCHEMA or payload['binding'] != self.binding:
                raise GenerationCheckpointError('schema/binding mismatch')
            if payload['ordinal'] != ordinal or payload['batch'] != self.plan[ordinal]:
                raise GenerationCheckpointError('ordinal/batch mismatch')
            tokens = payload['tokens']
            if len(tokens) != len(self.plan[ordinal]['rows']):
                raise GenerationCheckpointError('row count mismatch')
            if not all(len(row) == self.new_tokens for row in tokens):
                raise GenerationCheckpointError('token count mismatch')
            if not all(type(t) is int and 0 <= t < self.vocab_size for row in tokens for t in row):
                raise GenerationCheckpointError('token range/type mismatch')
            return torch.tensor(tokens, dtype=torch.long, device=device)
        except (ValueError, KeyError, TypeError) as error:
            raise GenerationCheckpointError('invalid committed checkpoint batch %s' % path) from error

    def save(self, ordinal, tokens):
        payload = {'schema': SCHEMA, 'binding': self.binding, 'ordinal': ordinal,
                   'batch': self.plan[ordinal], 'tokens': tokens.detach().cpu().tolist(),
                   'segment': self.owner.provenance}
        path = self.directory / ('batch-%06d.json' % ordinal)
        try:
            atomic_json(path, {'payload': payload, 'sha256': digest(payload)})
        except OSError as error:
            raise GenerationCheckpointError('checkpoint batch commit failed') from error
        self.load(ordinal, device='cpu')
        self.owner.new_batches += 1
        if self.owner.new_batches >= self.owner.maximum:
            raise GenerationSegmentComplete('durably saved %d new generation batches; evaluation incomplete'
                                            % self.owner.new_batches)


def execution_identity(ctx):
    """Immutable source/model/tokenizer/runtime identity; job IDs are provenance only."""
    import re
    import transformers
    model, tok, cli = ctx.node_model, ctx.tokenizer, ctx.cli
    root = Path(__file__).resolve().parents[1]
    sources = sorted(set(root.glob('evaluation/**/*.py')) | set(root.glob('models/**/*.py')) |
                     set(root.glob('dataset/**/*.py')) | set(root.glob('tasks/**/*.py')) |
                     {root / p for p in ('analysis.py', 'evaluate_circuit.py', 'l0.py', 'config.py', 'train.py')})
    source_hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sources if p.is_file()}
    config = model.config.to_dict()
    name = str(getattr(model.config, '_name_or_path', ''))
    revision = getattr(model.config, '_commit_hash', None)
    snapshot = re.search(r'/snapshots/([0-9a-f]{40})(?:/|$)', name)
    revision = revision or (snapshot.group(1) if snapshot else None)
    if not revision:
        raise GenerationCheckpointError('generation checkpoint requires resolved immutable model revision')
    parameter = next(model.parameters())
    device = parameter.device
    if device.type != 'cuda' or 'H200' not in torch.cuda.get_device_name(device):
        raise GenerationCheckpointError('frozen generation checkpoints require H200 execution')
    if any(module.training for module in model.modules()):
        raise GenerationCheckpointError('generation checkpoint requires model eval mode')
    backend = tok.backend_tokenizer.to_str() if hasattr(tok, 'backend_tokenizer') else None
    if backend is None:
        raise GenerationCheckpointError('checkpoint requires exact tokenizer backend serialization')
    artifacts = {}
    for field in ('benchmark_fixed_cohort', 'benchmark_frozen_masks'):
        path = getattr(cli, field, None)
        if not path:
            raise GenerationCheckpointError('checkpoint requires frozen cohort and masks')
        artifacts[field] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    config.pop('_name_or_path', None)
    return {'schema': SCHEMA, 'sources': source_hashes, 'artifacts': artifacts,
        'model': {'revision': revision, 'config': config, 'class': type(model).__qualname__},
        'tokenizer': {'backend_sha256': hashlib.sha256(backend.encode()).hexdigest(),
                      'chat_template': tok.chat_template, 'special_tokens': tok.special_tokens_map,
                      'init': {k: v for k, v in tok.init_kwargs.items()
                               if k in ('revision', '_commit_hash', 'padding_side', 'truncation_side', 'model_max_length')}},
        'runtime': {'gpu': torch.cuda.get_device_name(device),
            'capability': list(torch.cuda.get_device_capability(device)),
            'dtype': str(parameter.dtype), 'torch': str(torch.__version__),
            'transformers': transformers.__version__, 'cuda': torch.version.cuda,
            'cudnn': torch.backends.cudnn.version(),
            'tf32_matmul': torch.backends.cuda.matmul.allow_tf32,
            'tf32_cudnn': torch.backends.cudnn.allow_tf32,
            'deterministic': torch.are_deterministic_algorithms_enabled(),
            'cudnn_benchmark': torch.backends.cudnn.benchmark,
            'sdp_flash': torch.backends.cuda.flash_sdp_enabled(),
            'sdp_math': torch.backends.cuda.math_sdp_enabled(),
            'sdp_mem_efficient': torch.backends.cuda.mem_efficient_sdp_enabled(),
            'attention': getattr(model.config, '_attn_implementation', None)},
        'datasets': list(cli.benchmarks),
        'seeds': {'torch': torch.initial_seed(),
            **{k: v for k, v in vars(cli).items() if 'seed' in k}}}


def phase_store(ctx, dataset, phase, *, masks=None, donor=None):
    checkpoint = getattr(getattr(ctx, 'session', None), '_generation_checkpoint', None)
    if checkpoint is None:
        return None
    from evaluation.masks import as_lists
    try:
        identity = execution_identity(ctx)
    except (OSError, ValueError, TypeError, RuntimeError) as error:
        raise GenerationCheckpointError('checkpoint execution identity failed: %s' % error) from error
    _bind(checkpoint.directory / 'run.json', identity)
    if torch.cuda.is_available():
        properties = torch.cuda.get_device_properties(next(ctx.node_model.parameters()).device)
        checkpoint.provenance['gpu_uuid'] = str(getattr(properties, 'uuid', 'unavailable'))
    from analysis import extract_node_masks
    identity.update(mask=(as_lists(masks) if masks is not None else 'all-gates-open'),
                    effective_mask=extract_node_masks(ctx.node_model), donor=donor)
    try:
        return checkpoint.phase(dataset, phase, identity)
    except OSError as error:
        raise GenerationCheckpointError('checkpoint phase creation failed') from error
