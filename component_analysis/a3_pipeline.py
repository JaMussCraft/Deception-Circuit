"""A3 CPU preparation and fail-closed parent loading.

Later execution stages belong to the staged A3 pipeline; this module never loads
weights. Parent reads always use A1's original identity, including its full scope.
"""
from __future__ import annotations
import copy
import csv
import json
from pathlib import Path
from types import SimpleNamespace

from component_analysis import a3_design
from component_analysis import ladder_pipeline as ladder
from dataset import user_inversion_pipeline as common

require=common.require


def load_a1_parents(design_path, selected_path):
    prepared=ladder.read_artifact(design_path)
    require(prepared.get('kind')=='prepared','missing A1 prepared artifact')
    args=SimpleNamespace(**{k:prepared[k] for k in ('tasks','commit','model','model_revision','tokenizer_revision')},groups=str(selected_path))
    selected=ladder.read_selection(args,prepared)
    completion_path=ladder.selection_manifest_path(selected_path)
    evidence=dict(completion=json.loads(completion_path.read_text()),completion_path=str(completion_path.resolve()),
                  completion_file_sha256=common.file_hash(completion_path),
                  prepared_path=str(Path(design_path).resolve()),prepared_file_sha256=common.file_hash(design_path),
                  selected_path=str(Path(selected_path).resolve()),selected_file_sha256=common.file_hash(selected_path))
    return prepared,selected,evidence


def canonical_source_hashes(values, *, a1_repo_root):
    """Comparison lookup only; immutable A1 identities remain untouched."""
    root=Path(a1_repo_root).resolve(); result={}
    for path,digest in values.items():
        candidate=Path(path)
        resolved=str((candidate if candidate.is_absolute() else root/candidate).resolve())
        require(resolved not in result or result[resolved]==digest,'conflicting frozen source path aliases: '+resolved)
        result[resolved]=digest
    return result


def _validate_parent_files(prepared, *, a1_repo_root=ladder.REPO):
    require(prepared['code_hashes']==ladder.code_hashes(),'changed A1 source/code/grader hashes')
    for domain in ('source_hashes','selection_hashes'):
        for path,digest in canonical_source_hashes(prepared[domain],a1_repo_root=a1_repo_root).items():
            require(Path(path).is_file() and common.file_hash(path)==digest,'changed A1 '+domain+': '+path)
    ladder.grader_registry()


def _matched_rows(root, manifest, prepared, *, a1_repo_root=ladder.REPO, tokenizer=None):
    """Inspect materialized source rows, not just claimed build_manifest counts."""
    from datasets import load_from_disk
    from dataset.build_twin_training import _load
    result=copy.deepcopy(manifest); result['parent_fingerprints']={k:copy.deepcopy(prepared[k]) for k in ('source_hashes','tokenizer_identity','grader_sha256')}
    enriched=copy.deepcopy(prepared['rows'])
    canonical_hashes=canonical_source_hashes(prepared['source_hashes'],a1_repo_root=a1_repo_root)
    from scripts.twin_training import _stored_rows
    for task,summary in result['tasks'].items():
        _stored_rows(dict(data_root=str(Path(root).resolve()),sample_caps={s:len(ids) for s,ids in summary['split_ids'].items()}),
                     manifest,task,summary['split_ids'])
        summary['actual_split_ids']={}
        source_rows={}
        for condition,meta in summary['sources'].items():
            for relative,digest in meta['file_hashes'].items():
                source_path=str((Path(meta['path'])/relative).resolve())
                require(canonical_hashes.get(source_path)==digest,'matched source is not frozen A1 input')
                require(common.file_hash(source_path)==digest,'changed matched source hash')
            loaded,fresh=_load(meta['path'])
            require(fresh==meta,'changed matched source metadata')
            source_rows[condition]={split:{r['instance_id']:r for r in rows} for split,rows in loaded.items()}
        for arm in ('D','I'):
            path=Path(root)/arm/task
            dataset=load_from_disk(str(path)); actual={}
            cfg_path=path/'dataset_config.json'
            require(cfg_path.is_file(),'missing actual matched configuration')
            cfg=json.loads(cfg_path.read_text())
            require(cfg.get('split_ids')==summary['split_ids'] and cfg.get('cohort')=='matched' and cfg.get('fleet_ready') is True and cfg.get('source_provenance')=={k:summary['sources'][k] for k in (arm,'H' if arm=='D' else 'I_neutral')},'stale actual matched configuration')
            for split in ('train','validation','test'):
                actual[split]=[]
                indices={c:{r['instance_id']:r for r in enriched[task][c] if r['split']==split} for c in enriched[task]}
                for row in dataset[split]:
                    rid=row['instance_id']; actual[split].append(rid)
                    source=row['source_recipient']; neutral=row['source_reference']
                    reference='H' if arm=='D' else 'I_neutral'
                    require(source==source_rows[arm][split].get(rid) and neutral==source_rows[reference][split].get(rid),
                            'materialized matched source row differs from frozen original')
                    if tokenizer is not None:
                        from dataset.build_twin_training import _pair, LABELS
                        require(row.get('token_proof')==_pair(source,neutral,tokenizer,manifest['max_seq_length']),
                                'stored builder token proof differs from recomputation')
                        require(row.get('label_semantics')==LABELS,'stored label semantics mismatch')
                    peer='H' if arm=='D' else 'user_neutral'
                    for condition,raw in ((arm,source),(peer,neutral)):
                        require(rid in indices[condition], 'actual source not in A1 parent')
                        target=indices[condition][rid]
                        for stream in ('clean','corrupt'):
                            require(target['streams'][stream]['prompt']==raw[stream+'_prompt'],'actual matched prompt differs from A1')
                        fields=('task','template_variant','entity','item_1','item_2','clean_item_d','desig','desig_inv','suffix','ser_wording','pressure')
                        target['semantic_source']={k:raw[k] for k in fields if k in raw}
                        # A1 normalization intentionally omits semantic source wording.
                        for field in ('pressure','request_text','question','designation_text'):
                            if field in raw: target[field]=raw[field]
                    # Canonical D pressure wording defines the cluster in every arm.
                    if arm=='D':
                        require(isinstance(source.get('pressure'),str) and source['pressure'],'missing D pressure wording')
                        for condition in indices:
                            if rid in indices[condition]:
                                indices[condition][rid]['pressure_text']=source['pressure']
                                if condition=='F':
                                    indices[condition][rid]['semantic_source']=dict(indices[arm][rid]['semantic_source'],pressure='')
            summary['actual_split_ids'][arm]=actual
    return result,enriched


def freeze_semantic_maps(design, tokenizer):
    """Builder-verified bidirectional maps; no D/I token correspondence."""
    from component_analysis import ladder_design
    from dataset.matched_honest import assert_clause_aligned_pair
    result={}
    for task,rows in design['access_rows'].items():
        indexed={(r['condition'],r['instance_id']):r for r in rows}
        maps=[]
        for row in rows:
            if row['condition'] not in ('D','I'): continue
            peer='H' if row['condition']=='D' else 'user_neutral'
            donor=indexed.get((peer,row['instance_id']))
            for stream,left in row['streams'].items():
                entry=dict(instance_id=row['instance_id'],recipient_condition=row['condition'],donor_condition=peer,
                    stream=stream,bidirectional=True,supported=False,recipient_positions=[],donor_positions=[],
                    unsupported_reason='missing or non-exact builder map')
                try:
                    require(donor is not None,'missing semantic twin')
                    right=donor['streams'][stream]
                    require(ladder_design._aligned(left,right),'unsupported role/layout map')
                    if row['condition']=='I':
                        require(ladder_design._request_matches(row,donor,stream),'unsupported user-request map')
                    clause=row.get('request_text') if row['condition']=='I' else row.get('pressure')
                    require(isinstance(clause,str) and clause,'missing builder clause wording')
                    a,b,span=assert_clause_aligned_pair(tokenizer,left['prompt'],right['prompt'],clause,
                                                      max(len(left['tokens']),len(right['tokens'])))
                    require(list(a)==left['tokens'] and list(b)==right['tokens'],'changed semantic tokenization')
                    start,end=span
                    require(len(a)==len(b) and 0<=start<end<=len(a)-1,'unequal/unpadded clause map')
                    require(end-start==len(tokenizer.encode(' '+clause,add_special_tokens=False)),
                            'clause boundary BPE merge')
                    require(all(x==y for pos,(x,y) in enumerate(zip(a,b)) if not start<=pos<end),
                            'tokens differ outside builder clause span')
                    require(a[-1]==b[-1],'builder readout differs')
                    entry.update(supported=True,recipient_positions=list(range(len(a))),donor_positions=list(range(len(b))),
                                 replacement_span=list(span),unsupported_reason=None)
                except (ValueError,AssertionError,IndexError):
                    pass
                maps.append(entry)
        result[task]=maps
    return result


def prepare(*, a1_design, a1_selected, matched_root, historical_csv, root_ruling,
            tokenizer, registry_paths=(), output=None, a1_repo_root=ladder.REPO):
    """Validate CPU provenance and freeze; no call to A1 freeze_design/draw_sample.

    The output is immutable. ``output=None`` validates without writing. Fixtures
    may call freeze_a3 directly; production preparation requires actual files.
    """
    from dataset.build_twin_training import _hash as matched_hash
    from component_analysis.ladder_tasks import _ioi_candidates
    p,s,evidence=load_a1_parents(a1_design,a1_selected)
    _validate_parent_files(p,a1_repo_root=a1_repo_root)
    fresh_identity=common.tokenizer_identity(tokenizer,p['tokenizer_revision'],injected=p.get('injected',False))
    require(fresh_identity==p['tokenizer_identity'],'changed tokenizer identity')
    ladder.validate_tokenization(p,tokenizer)
    path=Path(matched_root)/'build_manifest.json'; original=json.loads(path.read_text())
    core={k:v for k,v in original.items() if k!='build_hash'}
    require(original.get('build_hash')==matched_hash(core),'changed matched manifest hash')
    matched,enriched=_matched_rows(matched_root,original,p,a1_repo_root=a1_repo_root,tokenizer=tokenizer)
    # Enrichment is source text only: preserve the original parent payload hash.
    history=dict(rows=list(csv.DictReader(Path(historical_csv).open())),source_hashes={str(Path(historical_csv).resolve()):common.file_hash(historical_csv)},
                 selection_completion=evidence['completion'])
    # freeze_a3 validates immutable original A1 hash first; enrich the resulting
    # semantic/cluster metadata through a separate explicit source adapter.
    history['source_rows']=enriched
    result=a3_design.freeze_a3(p,s,matched,history,root_ruling=root_ruling)
    fixed=list(p['utility']['ioi'])
    validation=a3_design.eligible_ioi(_ioi_candidates(tokenizer,count=1000,seed=2),fixed,n=100)
    require(len(validation)==100,'insufficient unique eligible seed-2 IOI validation prompts')
    result.update(ioi_validation=validation,ioi_validation_seed=2,parent_evidence=evidence,
                  a1_repo_root=str(Path(a1_repo_root).resolve()),
                  reused_a2_validator_sha256=common.file_hash(ladder.REPO/'scripts/twin_training.py'),
                  matched_build_path=str(path.resolve()),matched_build_file_sha256=common.file_hash(path))
    result['semantic_twin_maps']=freeze_semantic_maps(result,tokenizer)
    for rows in result['access_rows'].values():
        for row in rows:
            pair=dict(clean_prompt=row['streams']['clean']['prompt'],corrupt_prompt=row['streams']['corrupt']['prompt'],
                      clean_item_d=row['streams']['clean']['honest_item'],corrupt_item_d=row['streams']['corrupt']['honest_item'])
            for stream,record in row['streams'].items():
                source=dict(row,**record,stream=stream,designation_source=pair)
                record['semantic']=a3_design.semantic_record(source,tokenizer)
    result['registry_hashes']=a3_design.validate_access(result,list(registry_paths))
    if output is not None: ladder.write_artifact(output,result)
    return result
