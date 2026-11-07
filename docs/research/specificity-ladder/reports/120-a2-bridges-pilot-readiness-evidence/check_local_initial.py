import pathlib,json,hashlib,sys,os,tarfile,time
W=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');P=W/'outputs/_analyses/specificity-ladder/a2-bridges2-20261102';F=W/'outputs/_analyses/specificity-ladder/a2-runtime-6bd8bf5';B=F/'runtime';E=W/'docs/research/specificity-ladder/reports/120-a2-bridges-pilot-readiness-evidence';start=time.perf_counter()
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
m=json.loads((P/'transfer-manifest.json').read_text());s=json.loads((F/'snapshot.json').read_text());assert m['source_commit']==s['application_commit']=='6bd8bf5334f2e83613a129d2fcfeacf83e762191'
rows=m['files'];assert len(rows)==len({r['relative_path'] for r in rows})==88;assert set((P/'transfer-files.txt').read_text().splitlines())=={r['relative_path'] for r in rows};assert sum(r['nbytes'] for r in rows)==m['total_bytes']==60573681
for r in rows:
 rel=pathlib.Path(r['relative_path']);assert not rel.is_absolute() and '..' not in rel.parts
 assert pathlib.Path(r['virtual_path'])==pathlib.Path(m['namespace_root'])/rel
 path=pathlib.Path(r['virtual_path']);assert path.is_file() and path.stat().st_size==r['nbytes'] and sha(path)==r['sha256'],r['virtual_path']
assert sha(F/'application.tar')==s['archive_sha256']=='1a4e6397bb5924f22fc548fb8899a925a58f0b3640730a2602300e7e8c045ac6'
for rel,digest in s['source_files_sha256'].items():
 p=B/rel;assert p.is_file() and not p.is_symlink() and sha(p)==digest
assert len(s['source_files_sha256'])==207
with tarfile.open(F/'application.tar') as archive:
 names={x.name.removeprefix('./') for x in archive.getmembers() if x.isfile()};assert names==set(s['source_files_sha256'])
 for item in archive.getmembers():assert not pathlib.Path(item.name).is_absolute() and '..' not in pathlib.Path(item.name).parts
links={name:os.readlink(B/name) for name in s['live_links']};assert links==s['live_links']
sys.path.insert(0,str(B));from scripts import twin_training as t
assert pathlib.Path(t.__file__).resolve()==B/'scripts/twin_training.py'
config_path=W/'outputs/_analyses/specificity-ladder/a2-timing-h200-config.json';build_path=W/'outputs/_analyses/specificity-ladder/a2-matched-77b6487-m07/build_manifest.json';config=json.loads(config_path.read_text());build=json.loads(build_path.read_text());config.setdefault('data_root',str(build_path.parent))
assert sha(config_path)=='4321ef824036b316828564f7fc3833d508552361d370890e46be39bd1feacec8'
# The actual standard-library/Arrow source and row checks run in plan_run; no child/model.
plans={}
for arm in ('D','I'):
 plan=t.plan_run(config,build,task='sdr_v2',condition=arm,seed=42,timing_epochs=20,execution_commit=m['source_commit'])
 saved=json.loads((W/'outputs/_analyses/specificity-ladder/a2-timing-6bd8bf5-h200'/('sdr_v2-'+arm+'-seed42.json')).read_text())
 assert plan['purpose']=='timing-only' and plan['actual_epochs']==20 and plan['planned_epochs']==500
 assert plan['selected_ids']==saved['selected_ids'] and plan['counts']==saved['counts']=={'train':187,'validation':187,'test':952}
 assert plan['source_hashes']==saved['source_hashes'] and plan['dataset_config_sha256']==saved['dataset_config_sha256']
 assert plan['argv'][1:]==saved['argv'][1:] and plan['resolved_config_sha256']==saved['resolved_config_sha256']
 plans[arm]=plan
result=dict(kind='independent_local_Bridges_A2_timing_readiness',source_commit=m['source_commit'],transfer_manifest_sha256=sha(P/'transfer-manifest.json'),transfer_files=88,transfer_bytes=m['total_bytes'],source_files=207,archive_sha256=sha(F/'application.tar'),snapshot_sha256=sha(F/'snapshot.json'),all_local_bytes_match=True,live_links=links,source_counts=m['source_counts'],matched_files=m['matched_files'],configuration_sha256=sha(config_path),build_manifest_sha256=sha(build_path),plans=plans,original_H200_timing20_plan_exact=True,timing_schedule_caveat='actual20 CosineAnnealingLR T_max20; planned500 provenance is not first20 of T_max500',protection_hashes={str(p):sha(p) for p in t.PROTECTED_REGISTRIES},models_or_weights_loaded=False,jobs_submitted=False,remote_access=False,exit_code=0,elapsed_seconds=time.perf_counter()-start)
(E/'local-check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='plans'},indent=2))
