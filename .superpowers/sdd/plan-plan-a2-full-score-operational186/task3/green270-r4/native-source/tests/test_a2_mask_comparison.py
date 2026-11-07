"""CPU-only synthetic admission and frozen A2 algebra; timing is negative evidence."""
import copy
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from component_analysis import a2_mask_comparison as a2


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return str(path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(root):
    return {str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file()}


@pytest.fixture(scope='session')
def arrow_templates(tmp_path_factory):
    from datasets import Dataset, DatasetDict, disable_progress_bars
    from scripts.twin_training import _canonical
    disable_progress_bars()
    templates=tmp_path_factory.mktemp('a2-real-arrow')
    source_rows={}
    for task in a2.TASKS:
        for kind,condition in [('D','deceptive'),('H','honest'),('I','user_inversion'),('I_neutral','neutral_user')]:
            rows={s:[dict(instance_id=task+s,condition=condition,clean_prompt=kind+' '+s+' prompt',
                          target=' yes',distractor=' no')] for s in ('train','validation','test')}
            source_rows[task,kind]=rows
            DatasetDict({s:Dataset.from_list(v) for s,v in rows.items()}).save_to_disk(str(templates/'sources'/task/kind))
        for condition,donor in [('D','H'),('I','I_neutral')]:
            rows={}
            for split in ('train','validation','test'):
                recipient=source_rows[task,condition][split][0];reference=source_rows[task,donor][split][0]
                proof=dict(recipient_prompt_hash=_canonical(recipient['clean_prompt']),reference_prompt_hash=_canonical(reference['clean_prompt']))
                rows[split]=[dict(recipient,corrupt_prompt=reference['clean_prompt'],source_recipient=recipient,
                    source_reference=reference,token_proof=proof,orientation='clean',corruption_kind='neutral_twin_same_item',
                    recipient_condition=recipient['condition'],donor_identity=dict(instance_id=recipient['instance_id'],condition=reference['condition'],stream='clean'))]
            DatasetDict({s:Dataset.from_list(v) for s,v in rows.items()}).save_to_disk(str(templates/'private'/condition/task))
    return templates,source_rows


@pytest.fixture
def fleet(tmp_path, monkeypatch, arrow_templates):
    from scripts.twin_training import GATE_FLAGS, expected_config, _canonical
    templates,source_rows=arrow_templates
    root=tmp_path/'execution';root.mkdir()
    for name in ('outputs','data','logs'):
        target=tmp_path/('shared-'+name);target.mkdir();(root/name).symlink_to(target,target_is_directory=True)
    registry=tmp_path/'registry.json';write(registry,{'schema':1,'sets':[]})
    (root/'docs/research').mkdir(parents=True);(root/'docs/research/held_out.json').symlink_to(registry)
    config=json.loads((Path(__file__).resolve().parents[1]/'outputs/_analyses/specificity-ladder/a2-timing-h200-config.json').read_text())
    config_path=write(root/'frozen.json',config)
    tasks={t:dict(split_ids={s:[t+s] for s in ('train','validation','test')},
                  counts={s:1 for s in ('train','validation','test')},sources={}) for t in a2.TASKS}
    for task in a2.TASKS:
        for kind in ('D','H','I','I_neutral'):
            path=tmp_path/'sources'/task/kind;shutil.copytree(templates/'sources'/task/kind,path)
            files=inventory(path)
            tasks[task]['sources'][kind]=dict(path=str(path),file_hashes=files,content_hash=_canonical(files),row_hash=_canonical(source_rows[task,kind]))
    build=dict(schema_version=1,tasks=tasks,fleet_ready=True,cohort='matched',source_commit='7'*40,max_seq_length=256)
    build['build_hash']=a2.digest(build)
    data_root=(root/'data').resolve()
    build_path=write(data_root/'build_manifest.json',build)
    ruling=dict(schema_version=1,ruling_id='synthetic',decision='accept_exact_matched_cohort',session='test',
        build_hash=build['build_hash'],selected_ids_sha256=a2.digest({t:v['split_ids'] for t,v in tasks.items()}),
        counts={t:v['counts'] for t,v in tasks.items()},conditions=['D','I'],
        selection_rule='all_matched_survivors_no_baseline_competence_filter',scope='cohort_size_only',rationale='synthetic CPU fixture')
    ruling_path=write(root/'ruling.json',ruling)
    monkeypatch.setattr(a2,'BUILD_HASH',build['build_hash'])
    monkeypatch.setattr(a2,'RULING_SHA256',sha(ruling_path))
    source_hashes={}
    dependency_names=list(a2.SOURCE_HASHES)+['analysis.py','l0.py','models/llama_node.py']
    dependency_names += ['synthetic/file%03d.py'%i for i in range(207-len(dependency_names))]
    for name in dependency_names:
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(name)
        if name in a2.SOURCE_HASHES:source_hashes[name]=sha(path)
    monkeypatch.setattr(a2,'SOURCE_HASHES',source_hashes)
    archive=root.parent/'application.tar';archive.write_bytes(b'synthetic source archive')
    snapshot=dict(application_commit=a2.EXECUTION_COMMIT,runtime_root=str(root),archive_sha256=sha(archive),
        source_files_sha256={n:sha(root/n) for n in dependency_names},live_links={
            n:str((root/n).resolve()) for n in ('outputs','data','logs','docs/research/held_out.json')})
    snapshot_path=write(root.parent/'snapshot.json',snapshot)
    monkeypatch.setattr(a2,'SNAPSHOT_SHA256',sha(snapshot_path),raising=False)
    monkeypatch.setattr(a2,'ARCHIVE_SHA256',sha(archive),raising=False)
    for task in a2.TASKS:
        for condition,donor in [('D','H'),('I','I_neutral')]:
            path=data_root/condition/task;shutil.copytree(templates/'private'/condition/task,path)
            private=dict(model=config['model'],task=task,condition='deceptive' if condition=='D' else 'user_inversion',
                recipient_condition='deceptive' if condition=='D' else 'user_inversion',corruption_kind='neutral_twin_same_item',
                cohort='matched',fleet_ready=True,source_commit=build['source_commit'],max_seq_length=256,
                split_ids=tasks[task]['split_ids'],train_samples=1,val_samples=1,test_samples=1,
                source_provenance={k:tasks[task]['sources'][k] for k in (condition,donor)},token_proofs={})
            for split in ('train','validation','test'):
                private['token_proofs'][split]={task+split:dict(recipient_prompt_hash=_canonical(source_rows[task,condition][split][0]['clean_prompt']),
                    reference_prompt_hash=_canonical(source_rows[task,donor][split][0]['clean_prompt']))}
            write(path/'dataset_config.json',private)
    records=[];cells=[]
    for task in a2.TASKS:
        for condition in ('D','I'):
            for seed in a2.SEEDS:
                out=Path(config['output_root'])/f'{task}_{condition}_seed{seed}_heads-mlp_{a2.digest(dict(build=build["build_hash"],ids=tasks[task]["split_ids"],config=dict(config,data_root=str(data_root))))[:16]}_full'
                values=dict(model=config['model'],task=task,deception_condition='deceptive',data_dir=str(data_root/condition),
                    node_lambda_sparsity=.3,node_epochs=500,lr=.03,batch_size=7,faithfulness_weight=1,deception_margin_loss=.7,
                    train_samples=1,val_samples=1,test_samples=1,max_seq_length=256,seed=seed,output_dir=str(out))
                argv=['python',str(root/'train.py')]+[x for k,v in values.items() for x in ('--'+k.replace('_','-'),str(v))]+GATE_FLAGS
                expected=expected_config(argv);cfg=copy.deepcopy(expected)
                cfg.update(family='llama',std_variant='azaria',std_margin_loss=None,joint_tasks=None,joint_scale_epochs=True,
                    edge_epochs=300,edge_lambda_sparsity=.95,edge_config=dict(sparsity_warmup_steps=500,include_output_edges=True))
                cfg['node_config']['depth_penalty_scaling']=0.
                for kind in ('attention_heads','attention_neurons','attention_blocks','mlp_hidden','mlp_output','mlp_blocks','full_layers','embedding'):
                    cfg['node_config']['lambda_'+kind]=1.
                active=dict(active_heads={'0':[0]},active_mlps=[5] if condition=='D' else [],masks=dict(
                    attention_heads={str(i):[int(i==0 and h==0) for h in range(32)] for i in range(32)},
                    mlp_blocks=[int(i==5 and condition=='D') for i in range(32)]))
                results=dict(model=config['model'],task=task,seed=seed,edge_pruning=False,edge_eval=None,
                    baseline={'accuracy':1,'outputs':[{'instance_id':task+'test'}]},node_eval={'accuracy':0,'outputs':[{'instance_id':task+'test'}]})
                artifacts={n:write(root/out/n,v) for n,v in [('config.json',cfg),('active_nodes.json',active),('results.json',results),
                    ('history.json',{'node':{'epochs':list(range(1,501)),'evals':[{'epoch':500}]}})]}
                data_files={str(data_root/condition/task/n):v for n,v in inventory(data_root/condition/task).items()}
                native=dict(schema='run-manifest/1',model=config['model'],model_revision='0e9e39f249a16976918f6564b8830bc894c89659',
                    seed=seed,argv=argv[1:],execution_commit=a2.EXECUTION_COMMIT,build_source_commit=build['source_commit'],
                    config_sha256=sha(artifacts['config.json']),code_sha256={'train.py':source_hashes['train.py']},dataset_files=data_files)
                native['manifest_hash']=a2.digest(native);artifacts['run_manifest.json']=write(root/out/'run_manifest.json',native)
                receipt=dict(task=task,condition=condition,seed=seed,model=config['model'],purpose='scientific-seed',actual_epochs=500,
                    planned_epochs=500,fleet_ready=True,cohort='matched',status='success',exit_code=0,errors=[],test_runner_injected=False,
                    test_clock_injected=False,execution_commit=a2.EXECUTION_COMMIT,source_commit=build['source_commit'],build_hash=build['build_hash'],
                    build_manifest_sha256=a2.digest(build),source_hashes=source_hashes,config_file_sha256=sha(config_path),
                    build_manifest_file_sha256=sha(build_path),frozen_config_sha256=a2.digest(dict(config,data_root=str(data_root))),
                    resolved_config_sha256=a2.digest(expected),dataset_config_sha256={c:sha(data_root/c/task/'dataset_config.json') for c in ('D','I')},
                    selected_ids=tasks[task]['split_ids'],counts=tasks[task]['counts'],max_seq_length=256,granularity='heads-mlp',
                    recipient_condition='deceptive' if condition=='D' else 'user_inversion',legacy_deception_condition='deceptive',
                    argv=argv,output_dir=str(out),artifacts=artifacts,artifact_sha256={n:sha(p) for n,p in artifacts.items()})
                receipt_path=write(root/f'{task}-{condition}-{seed}.json',receipt)
                records.append(dict(receipt_path=receipt_path,execution_root=str(root),frozen_config_path=config_path,
                    build_manifest_path=build_path,ruling_path=ruling_path))
                cell_argv=['bash',str(root/'scripts/jobs/specificity_twin_training.sh'),'--config',config_path,'--build-manifest',build_path,
                    '--task',task,'--condition',condition,'--seed',str(seed),'--commit',a2.EXECUTION_COMMIT,'--receipt',receipt_path]
                cells.append(dict(task=task,condition=condition,seed=seed,epochs=500,receipt=receipt_path,cwd=str(root),argv=cell_argv))
    fleet_plan=dict(application_commit=a2.EXECUTION_COMMIT,snapshot_manifest=snapshot_path,snapshot_manifest_sha256=sha(snapshot_path),cells=cells)
    fleet_path=write(root/'outputs/_analyses/specificity-ladder/a2-fleet-6bd8bf5-h200/fleet-plan.json',fleet_plan)
    monkeypatch.setattr(a2,'FLEET_PLAN_SHA256',sha(fleet_path),raising=False)
    return records


def mutate(record, name, fn):
    receipt=json.loads(Path(record['receipt_path']).read_text())
    if name=='receipt':
        fn(receipt)
    else:
        path=receipt['artifacts'][name]; value=json.loads(Path(path).read_text());fn(value);write(Path(path),value)
        receipt['artifact_sha256'][name]=sha(path)
    write(Path(record['receipt_path']),receipt)


def test_complete_typed_comparison(fleet):
    before=copy.deepcopy(fleet)
    result=a2.compare_masks(fleet)
    assert fleet==before
    assert len(result['sources'])==18
    for task in a2.TASKS:
        t=result['tasks'][task]
        assert t['seeds']['42']['X']['members']==[['mlp',5,0]]
        assert t['mixed_stability_pass'] is True
        assert t['informative_head_containment'] is True
        assert t['core']['members']==[['mlp',5,0]]
        assert len(t['pairwise']['mixed'])==3
        assert t['mlp_prediction'][0]['layer']==5 if task!='sdr_v2' else t['mlp_prediction']==[]
    assert a2.digest({k:v for k,v in result.items() if k!='comparison_sha256'})==result['comparison_sha256']


@pytest.mark.parametrize('kind', ['missing','duplicate','timing','failed','epoch','model','granularity','source','cohort','ids','ruling','config','history','parity','finer','range','duplicate_key','hash'])
def test_rejects_invalid_admission(fleet,kind):
    if kind=='missing':fleet.pop()
    elif kind=='duplicate':fleet[-1]=fleet[0]
    elif kind=='ruling':Path(fleet[0]['ruling_path']).write_text('{}')
    elif kind=='hash':Path(json.loads(Path(fleet[0]['receipt_path']).read_text())['artifacts']['active_nodes.json']).write_text('{}')
    else:
        name='receipt'
        def change(d):
            if kind=='timing':d['purpose']='timing-only'
            elif kind=='failed':d['status']='failed'
            elif kind=='epoch':d['actual_epochs']=20
            elif kind=='model':d['model']='other'
            elif kind=='granularity':d['granularity']='heads'
            elif kind=='source':d['source_hashes']['train.py']='0'*64
            elif kind=='cohort':d['cohort']='unmatched'
            elif kind=='ids':d['selected_ids']['train']=['foreign']
            elif kind=='config':d['deception_margin_loss']=.5
            elif kind=='history':d['node']['epochs'].pop()
            elif kind=='parity':d['active_heads']={}
            elif kind=='finer':d['masks']['mlp_hidden']={'0':[0]}
            elif kind=='range':d['active_mlps']=[32]
            elif kind=='duplicate_key':d['active_heads']['0']=[0,0]
        if kind=='config':name='config.json'
        if kind=='history':name='history.json'
        if kind in ('parity','finer','range','duplicate_key'):name='active_nodes.json'
        mutate(fleet[0],name,change)
    with pytest.raises(ValueError):a2.compare_masks(fleet)


def test_jaccard_empty_and_all_pairs():
    assert a2.jaccard(set(),set())['reason']=='both_empty'
    assert a2.jaccard(set(),{('mlp',1,0)})['ratio']==0
    assert a2.jaccard({1},{1,2})['ratio']==.5
    values=[{1,2},{1,2,3},{2,3,4}]
    pairs=a2.pairwise(values)
    assert [p['ratio'] for p in pairs]==[2/3,1/4,1/2]


def test_vacuous_containment():
    assert a2.containment(set(),set())==dict(numerator=0,denominator=0,ratio=None,
        reason='vacuous_no_D_heads',exclusive_count=0,subset=True,vacuous=True)


def test_ancestor_and_ungated_semantics():
    cfg=dict(prune_attention_heads=True,prune_mlp_blocks=False,prune_attention_blocks=True,
        prune_full_layers=False,prune_embedding=False,prune_attention_neurons=False,prune_mlp_hidden=False,prune_mlp_output=False)
    active=dict(active_heads={},active_mlps=list(range(32)),masks=dict(attention_blocks=[0]*32,
        attention_heads={str(l):[0]*32 for l in range(32)}))
    selected,parity=a2.audit_export(active,cfg)
    assert not selected
    assert parity['implicit_active_background']['mlps']==list(range(32))
    active['masks']['attention_heads']['0'][0]=1
    with pytest.raises(ValueError,match='ancestor'):a2.audit_export(active,cfg)


def test_actual_timing_receipt_rejected():
    repo=Path(__file__).resolve().parents[1]
    record=dict(receipt_path=str(repo/'outputs/_analyses/specificity-ladder/a2-timing-6bd8bf5-h200/far-D-seed42.json'),
        execution_root=str(repo),frozen_config_path=str(repo/'outputs/_analyses/specificity-ladder/a2-timing-h200-config.json'),
        build_manifest_path=str(repo/'outputs/_analyses/specificity-ladder/a2-matched-77b6487-m07/build_manifest.json'),
        ruling_path=str(repo/'docs/research/specificity-ladder/a2-cohort-ruling.json'))
    if not Path(record['receipt_path']).is_file():pytest.skip('local timing evidence absent')
    with pytest.raises(ValueError,match='scientific'):a2.audit_source(record)


def test_diagnostic_counts_never_select_members(fleet):
    mutate(fleet[0],'results.json',lambda d:d.update(node_granularity={
        'attention_heads':{'total':1024,'active':900},'mlp_blocks':{'total':32,'active':31}}))
    source=a2.audit_source(fleet[0])
    discrepancy=source['diagnostic_counts']['discrepancy']
    assert discrepancy['head']==dict(diagnostic_active=900,export_active=1,difference=899)
    assert discrepancy['mlp']==dict(diagnostic_active=31,export_active=1,difference=30)
    assert source['members']['counts']['total']==2


def test_full_config_drift_rejected(fleet):
    # Tampering is rehashed through every layer: identity agreement alone must
    # still reject a different scientific training default between seeds.
    rec=fleet[-1]; r=json.loads(Path(rec['receipt_path']).read_text())
    p=r['artifacts']['config.json']; cfg=json.loads(Path(p).read_text());cfg['edge_epochs']=17;write(Path(p),cfg)
    r['artifact_sha256']['config.json']=sha(p)
    npath=r['artifacts']['run_manifest.json'];n=json.loads(Path(npath).read_text());n['config_sha256']=sha(p)
    n['manifest_hash']=a2.digest({k:v for k,v in n.items() if k!='manifest_hash'});write(Path(npath),n)
    r['artifact_sha256']['run_manifest.json']=sha(npath);write(Path(rec['receipt_path']),r)
    with pytest.raises(ValueError,match='full resolved configuration'):a2.compare_masks(fleet)


def test_relative_native_paths_and_output_symlink(fleet):
    # The positive fixture is itself a frozen code root with original data/output
    # symlinks. Native paths may use those links relative to the execution root.
    record=fleet[0];root=Path(record['execution_root'])
    r=json.loads(Path(record['receipt_path']).read_text())
    npath=r['artifacts']['run_manifest.json'];n=json.loads(Path(npath).read_text())
    data_root=Path(record['build_manifest_path']).parent
    n['dataset_files']={str(Path('data')/Path(p).relative_to(data_root)):v for p,v in n['dataset_files'].items()}
    n['code_sha256']={'train.py':a2.SOURCE_HASHES['train.py']}
    n['manifest_hash']=a2.digest({k:v for k,v in n.items() if k!='manifest_hash'});write(Path(npath),n)
    r['artifact_sha256']['run_manifest.json']=sha(npath)
    r['artifacts']={k:str(Path(p).relative_to(root)) for k,p in r['artifacts'].items()}
    write(Path(record['receipt_path']),r)
    assert a2.audit_source(record)['members']['counts']['total']==2


def test_immutable_publication(fleet,tmp_path):
    result=a2.compare_masks(fleet)
    path=tmp_path/'comparison.json'
    a2.write_comparison(result,path)
    with pytest.raises(FileExistsError):a2.write_comparison(result,path)
    changed=copy.deepcopy(result);changed['tasks']['far_v2']['core']['members']=[]
    with pytest.raises(ValueError,match='comparison hash'):a2.write_comparison(changed,tmp_path/'other.json')


def test_json_duplicate_object_key_rejected(fleet):
    path=Path(fleet[0]['receipt_path']);raw=path.read_text();path.write_text(raw[:-1]+',"seed":42}')
    with pytest.raises(ValueError,match='duplicate JSON'):a2.audit_source(fleet[0])


def set_members(record, members):
    def change(d):
        heads={str(l):sorted(k[2] for k in members if k[0]=='head' and k[1]==l) for l in range(32)}
        d['active_heads']={l:hs for l,hs in heads.items() if hs}
        d['active_mlps']=sorted(k[1] for k in members if k[0]=='mlp')
        d['masks']['attention_heads']={str(l):[int(('head',l,h) in members) for h in range(32)] for l in range(32)}
        d['masks']['mlp_blocks']=[int(('mlp',l,0) in members) for l in range(32)]
    mutate(record,'active_nodes.json',change)


def test_full_comparison_all_empty_is_uninformative(fleet):
    for record in fleet:set_members(record,set())
    result=a2.compare_masks(fleet)
    for t in result['tasks'].values():
        assert t['mixed_stability_pass'] is False
        assert t['informative_head_containment'] is False
        assert t['minimum_jaccard'] is None
        assert all(p['reason']=='both_empty' for p in t['pairwise']['mixed'])
        assert t['seeds']['42']['whole_set_subset']==dict(subset=True,vacuous=True)


def test_full_comparison_two_pairs_pass_one_fails(fleet):
    choices=[{1,2},{1,2,3},{2,3,4}]
    for record in fleet:
        receipt=json.loads(Path(record['receipt_path']).read_text())
        keys={('head',0,h) for h in choices[a2.SEEDS.index(receipt['seed'])]} if receipt['condition']=='D' else set()
        set_members(record,keys)
    result=a2.compare_masks(fleet)
    for t in result['tasks'].values():
        assert [p['ratio'] for p in t['pairwise']['mixed']]==[2/3,1/4,1/2]
        assert t['mixed_stability_pass'] is False


def test_typed_algebra_and_head_containment_at_boundary(fleet):
    for record in fleet:
        r=json.loads(Path(record['receipt_path']).read_text())
        keys={('head',0,h) for h in range(10 if r['condition']=='D' else 9)}
        keys|={('mlp',5 if r['condition']=='D' else 6,0)}
        set_members(record,keys)
    t=a2.compare_masks(fleet)['tasks']['far_v2']
    row=t['seeds']['42']
    assert row['X']['members']==[['head',0,9],['mlp',5,0]]
    assert row['Y']['members']==[['mlp',6,0]]
    assert row['B']['counts']==dict(head=9,mlp=0,total=9)
    assert row['U']['counts']==dict(head=10,mlp=2,total=12)
    assert row['containment']['head']['ratio']==.9
    assert t['informative_head_containment'] is True
    assert t['mixed_stability_pass'] is True
    assert row['whole_set_subset']['subset'] is False


def test_bottom_up_finalization_rejected():
    cfg=dict(prune_attention_heads=True,prune_mlp_blocks=True,prune_attention_blocks=True,
        prune_full_layers=False,prune_embedding=False)
    active=dict(active_heads={},active_mlps=[],masks=dict(attention_blocks=[1]*32,
        attention_heads={str(l):[0]*32 for l in range(32)},mlp_blocks=[0]*32))
    with pytest.raises(ValueError,match='bottom-up'):a2.audit_export(active,cfg)


def test_frozen_file_hashes_bind_receipt(fleet):
    mutate(fleet[0],'receipt',lambda d:d.update(config_file_sha256='0'*64))
    with pytest.raises(ValueError,match='config file hash'):a2.audit_source(fleet[0])


def test_requires_native_model_revision(fleet):
    mutate(fleet[0],'run_manifest.json',lambda d:d.pop('model_revision',None))
    with pytest.raises(ValueError,match='model revision'):a2.audit_source(fleet[0])


def test_import_is_standard_library_only():
    import subprocess
    import sys
    code="import sys; import component_analysis.a2_mask_comparison; assert not ({'torch','datasets','transformers','numpy'} & set(sys.modules))"
    subprocess.run([sys.executable,'-c',code],check=True)


def rehash_native(record, change):
    r=json.loads(Path(record['receipt_path']).read_text());path=Path(r['artifacts']['run_manifest.json'])
    native=json.loads(path.read_text());change(native)
    native['manifest_hash']=a2.digest({k:v for k,v in native.items() if k!='manifest_hash'})
    write(path,native);r['artifact_sha256']['run_manifest.json']=sha(path);write(Path(record['receipt_path']),r)


@pytest.mark.parametrize('case',['weights','revision','analysis','l0','model','omitted_dependency','snapshot','archive','missing_inventory','malformed_arrow','wrong_rows','wrong_source_rows'])
def test_review77_independent_mutations_rejected(fleet,case):
    from datasets import Dataset, DatasetDict, load_from_disk
    root=Path(fleet[0]['execution_root'])
    if case=='weights':
        for record in fleet:
            r=json.loads(Path(record['receipt_path']).read_text());path=Path(r['artifacts']['config.json'])
            cfg=json.loads(path.read_text());cfg['node_config'].update(lambda_attention_heads=0,lambda_mlp_blocks=0,depth_penalty_scaling=10)
            write(path,cfg);r['artifact_sha256']['config.json']=sha(path);write(Path(record['receipt_path']),r)
            rehash_native(record,lambda n:n.update(config_sha256=sha(path)))
    elif case=='revision':
        for record in fleet:rehash_native(record,lambda n:n.update(model_revision='a'*40))
    elif case in ('analysis','l0','model','omitted_dependency'):
        name={'analysis':'analysis.py','l0':'l0.py','model':'models/llama_node.py','omitted_dependency':'analysis.py'}[case]
        path=root/name
        if case=='omitted_dependency':path.unlink()
        else:
            path.write_text('def extract_node_masks(model): return {}')
            for record in fleet:rehash_native(record,lambda n:n['code_sha256'].update({name:sha(path)}))
    elif case=='snapshot':
        path=root.parent/'snapshot.json';d=json.loads(path.read_text());d['source_files_sha256'].pop('analysis.py');write(path,d)
    elif case=='archive':(root.parent/'application.tar').write_bytes(b'changed archive')
    elif case=='missing_inventory':
        for record in fleet:
            rehash_native(record,lambda n:n.update(dataset_files={k:v for k,v in n['dataset_files'].items() if not k.endswith('.arrow')}))
    else:
        data=Path(fleet[0]['build_manifest_path']).parent
        if case=='wrong_source_rows':
            build=json.loads(Path(fleet[0]['build_manifest_path']).read_text());path=Path(build['tasks']['far_v2']['sources']['D']['path'])
        else:path=data/'D/far_v2'
        if case=='malformed_arrow':
            next(path.rglob('*.arrow')).write_bytes(b'not Arrow')
        else:
            saved=load_from_disk(str(path));rows={s:[dict(r) for r in saved[s]] for s in saved}
            if case=='wrong_rows':rows['train'][0]['clean_prompt']='wrong training prompt'
            else:rows['train'][0]['target']=' wrong target'
            for p in path.iterdir():
                if p.name!='dataset_config.json':
                    if p.is_dir():shutil.rmtree(p)
                    else:p.unlink()
            DatasetDict({s:Dataset.from_list(v) for s,v in rows.items()}).save_to_disk(str(path))
        # All mutable native dataset hashes are made internally consistent.
        for record in fleet:
            r=json.loads(Path(record['receipt_path']).read_text())
            if r['task']=='far_v2' and r['condition']=='D' and case!='wrong_source_rows':
                rehash_native(record,lambda n:n.update(dataset_files={str(path/k):v for k,v in inventory(path).items()}))
    with pytest.raises((ValueError,OSError)):a2.compare_masks(fleet)


@pytest.mark.parametrize('key,value', [('lambda_attention_heads',0),('lambda_mlp_blocks',0),('depth_penalty_scaling',10)])
def test_uniform_scientific_default_changes_rejected(fleet,key,value):
    for record in fleet:
        r=json.loads(Path(record['receipt_path']).read_text());path=Path(r['artifacts']['config.json'])
        cfg=json.loads(path.read_text());cfg['node_config'][key]=value;write(path,cfg)
        r['artifact_sha256']['config.json']=sha(path);write(Path(record['receipt_path']),r)
        rehash_native(record,lambda n:n.update(config_sha256=sha(path)))
    with pytest.raises(ValueError,match='frozen scientific defaults'):a2.compare_masks(fleet)


def test_changed_live_output_link_rejected(fleet,tmp_path):
    root=Path(fleet[0]['execution_root']);(root/'outputs').unlink()
    other=tmp_path/'wrong-outputs';other.mkdir();(root/'outputs').symlink_to(other,target_is_directory=True)
    with pytest.raises((ValueError,OSError)):a2.audit_source(fleet[0])


def test_positive_receipt_contains_authenticated_inventory_and_all_dependencies(fleet):
    source=a2.audit_source(fleet[0]);p=source['provenance']
    assert len(p['execution_snapshot']['source_files_sha256'])==207
    assert len([n for n in p['authenticated_private_inventory'] if n.endswith('.arrow')])==3
    assert {'analysis.py','l0.py','models/llama_node.py'} <= set(p['execution_snapshot']['source_files_sha256'])


def test_unreferenced_private_arrow_shard_rejected(fleet):
    data=Path(fleet[0]['build_manifest_path']).parent/'D/far_v2'
    extra=data/'train/extra-unreferenced.arrow';extra.write_bytes(b'not a valid Arrow shard')
    for record in fleet:
        r=json.loads(Path(record['receipt_path']).read_text())
        if r['task']=='far_v2' and r['condition']=='D':
            rehash_native(record,lambda n:n['dataset_files'].update({str(extra):sha(extra)}))
    with pytest.raises(ValueError,match='shard'):a2.compare_masks(fleet)
