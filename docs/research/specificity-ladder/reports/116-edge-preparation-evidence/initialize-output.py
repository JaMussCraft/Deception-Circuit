import pathlib,json,hashlib,shutil,stat,datetime
pointer=json.loads(pathlib.Path('/tmp/a3-edge-successor.json').read_text());b=pathlib.Path(pointer['runtime_root']);w=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');o=w/'outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4';prior=w/'outputs/_analyses/specificity-ladder/a3-independent-pilots-74efb4d04819';snapshot_path=pathlib.Path(pointer['snapshot']);s=json.loads(snapshot_path.read_text());h=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert not o.exists();assert s['source_commit']==pointer['source_commit'] and s['runtime_root']==str(b);assert len(s['source_sha256'])==509
for name,sha in s['source_sha256'].items():
 p=b/name;assert not p.is_symlink() and h(p)==sha and p.stat().st_mode & 0o222==0,name
links={name:str((b/name).resolve()) for name in s['input_links']};assert len(links)==4 and all((b/name).is_symlink() for name in links)
(o/'evidence').mkdir(parents=True)
for name in ('root-ruling.json','execution-settings.json'):
 shutil.copy2(prior/name,o/name);assert (prior/name).read_bytes()==(o/name).read_bytes()
paths=set(json.loads((prior/'evidence/ancestry-before.json').read_text()))
paths.update(str(p) for p in (prior/'root-ruling.json',prior/'execution-settings.json',w/'docs/research/held_out.json',w/'docs/research/directions.json',w/'docs/research/mechanism-analysis/phase3/a_prime.csv'))
matched=w/'outputs/_analyses/specificity-ladder/a2-matched-77b6487-m07';paths.update(str(p) for p in matched.rglob('*') if p.is_file())
ancestry={p:dict(sha256=h(p),bytes=pathlib.Path(p).stat().st_size) for p in sorted(paths)}
(o/'evidence/ancestry-before.json').write_text(json.dumps(ancestry,indent=2)+'\n')
record=dict(kind='edge_successor_cpu_source_binding_v1',commit=pointer['source_commit'],snapshot=str(snapshot_path),snapshot_sha256=h(snapshot_path),source_archive_sha256=s['source_archive_sha256'],expected_source_count=509,observed_source_count=len(s['source_sha256']),source_readonly=True,input_links=links,settings_copies={name:dict(original=str(prior/name),copy=str(o/name),sha256=h(o/name)) for name in ('root-ruling.json','execution-settings.json')},ancestry_files=len(ancestry),ancestry_bytes=sum(v['bytes'] for v in ancestry.values()),checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),execution_authorized=False)
(o/'evidence/source-binding-before.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
(o/'environment.sh').write_text(f'''export W={w}
export B={b}
export O={o}
export C={pointer['source_commit']}
export PYTHONPATH="$B" PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export HF_HOME=/work/nvme/beto/swong2 HF_HUB_CACHE=/work/nvme/beto/swong2/hub
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export DC_PYTHON=/u/swong2/.conda/envs/mgnp/bin/python
''')
