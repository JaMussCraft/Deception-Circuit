import pathlib,json,hashlib,shutil,datetime
w=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');o=w/'outputs/_analyses/specificity-ladder/a3-source-cost-pilots-f5a5687ec120';prior=w/'outputs/_analyses/specificity-ladder/a3-independent-pilots-74efb4d04819';pointer=json.loads(pathlib.Path('/tmp/a3-source-cost-successor-r2.json').read_text());b=pathlib.Path(pointer['runtime_root']);s=json.loads(pathlib.Path(pointer['snapshot']).read_text());h=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert not o.exists(),o
assert s['source_commit']==pointer['source_commit']=='f5a5687ec12091f0d148b38b301598e9c7cb98cd'
assert s['runtime_root']==str(b) and len(s['source_sha256'])==511
for name,sha in s['source_sha256'].items():
 p=b/name;assert p.is_file() and not p.is_symlink() and h(p)==sha and not p.stat().st_mode & 0o222,name
assert h(b.parent/'source.tar')==s['source_archive_sha256']
for name,target in s['input_links'].items():assert (b/name).is_symlink() and (b/name).resolve()==pathlib.Path(target).resolve(),name
assert len(s['input_links'])==4
(o/'evidence').mkdir(parents=True)
for name in ('root-ruling.json','execution-settings.json'):shutil.copyfile(prior/name,o/name);assert (prior/name).read_bytes()==(o/name).read_bytes()
shutil.copyfile('/tmp/a3-source-cost-successor-r2.json',o/'evidence/source-pointer.json')
paths=set(json.loads((prior/'evidence/ancestry-before.json').read_text()))
paths.update(str(p) for p in [prior/'root-ruling.json',prior/'execution-settings.json',w/'docs/research/held_out.json',w/'docs/research/directions.json',pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/held_out.json'),pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/directions.json'),w/'docs/research/mechanism-analysis/phase3/a_prime.csv'])
matched=w/'outputs/_analyses/specificity-ladder/a2-matched-77b6487-m07';paths.update(str(p) for p in matched.rglob('*') if p.is_file())
ancestry={p:dict(sha256=h(p),bytes=pathlib.Path(p).stat().st_size) for p in sorted(paths)}
(o/'evidence/ancestry-before.json').write_text(json.dumps(ancestry,indent=2)+'\n')
record=dict(kind='source_cost_real_input_initial_binding_v1',commit=pointer['source_commit'],runtime=str(b),snapshot=pointer['snapshot'],snapshot_sha256=h(pointer['snapshot']),source_archive_sha256=s['source_archive_sha256'],expected_source_count=511,observed_source_count=len(s['source_sha256']),source_readonly=True,input_links=s['input_links'],source_mismatch=False,ancestry_files=len(ancestry),checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),root_release='Source-safety PASS127 explicitly reported by root; no model admission',execution_authorized=False)
(o/'evidence/source-binding-before.json').write_text(json.dumps(record,indent=2)+'\n')
(o/'environment.sh').write_text(f'''export W={w}
export B={b}
export O={o}
export C={pointer['source_commit']}
export PYTHONPATH="$B" PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export HF_HOME=/work/nvme/beto/swong2 HF_HUB_CACHE=/work/nvme/beto/swong2/hub
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export DC_PYTHON=/u/swong2/.conda/envs/mgnp/bin/python
export SPECIFICITY_A3_MASK_LAUNCH_EXECUTABLE=/u/swong2/.conda/envs/mgnp/bin/python
''')
print(json.dumps(record,indent=2))
