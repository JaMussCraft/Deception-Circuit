"""Fixture observation support only; no validator, guard, authority or route patch."""
def _prepared_cpu_family():
    import platform
    fields = {}
    for line in Path('/proc/cpuinfo').read_text().splitlines():
        if ':' in line:
            (key, value) = line.split(':', 1)
            fields.setdefault(key.strip(), value.strip())
    model = fields.get('model name', fields.get('Processor', fields.get('cpu model')))
    require(isinstance(model, str) and model, 'receiver CPU family unavailable')
    return dict(architecture=platform.machine(), model=model)

def _prepared_storage_identity(path):
    """Observe the actual resolved path's mounted filesystem, without payload I/O."""
    path = Path(path).resolve(strict=True)

    def decode(value):
        return re.sub('\\\\([0-7]{3})', lambda m: chr(int(m.group(1), 8)), value)
    mounts = []
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        (left, right) = line.split(' - ', 1)
        fields = left.split()
        filesystem = right.split()
        mount = Path(decode(fields[4]))
        if path == mount or mount in path.parents:
            mounts.append((len(mount.parts), dict(path=str(path), mount_point=str(mount), filesystem=filesystem[0], mount_source=decode(filesystem[1]), device=path.stat().st_dev)))
    require(mounts, 'receiver storage family unavailable')
    return max(mounts, key=lambda item: item[0])[1]

def _prepared_receiver_context(references, allocation):
    require(isinstance(allocation, dict), 'receiver allocation evidence unavailable')
    family = {key: allocation.get(key) for key in ('cluster', 'cpus', 'memory_bytes')}
    require(isinstance(family['cluster'], str) and family['cluster'] and all((type(family[key]) is int and family[key] > 0 for key in ('cpus', 'memory_bytes'))), 'receiver allocation/CPU family unavailable')
    return dict(execution_class='injected' if allocation.get('injected') is True else 'slurm', cpu_family=_prepared_cpu_family(), allocation_family=family, storage={key: _prepared_storage_identity(ref['path']) for (key, ref) in references.items()})
