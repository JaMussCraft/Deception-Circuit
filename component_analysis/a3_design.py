"""CPU-only immutable A3 design. No fitting, model loading or assessment draw.

``ROOT_RULING_V1`` defines scientific decisions, not an authentication mechanism.
The lead supplies this exact versioned object before production preparation.
``freeze_a3`` is a pure core; production callers must use a3_pipeline.prepare,
which validates A1 completion evidence and reads actual matched Arrow rows.
"""
from __future__ import annotations
import copy
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace

from component_analysis import ladder_design as ladder
from dataset import user_inversion_pipeline as common

require = common.require
ROOT_RULING_V1 = dict(schema_version=1, kind='specificity_ladder_a3_root_ruling',
    seeds=[42, 1, 123], confirmatory_family=['direction_FAR', 'direction_SER'],
    constrained_mask_task='far_v2',
    direction_null=dict(neurons='deferred', edges='continue_bounded', mask='continue'))
QUARTET = [('head', 17, i) for i in range(24, 28)]
BINS = ('pressure_request', 'item_designation', 'question', 'assistant_readout')


def _ids(values, label):
    require(isinstance(values, list) and all(isinstance(i,str) and i for i in values)
            and len(set(values)) == len(values), 'invalid/duplicate ids: '+label)
    return set(values)


def _pressure(row):
    # A local pressure_id is not a canonical wording cluster.
    for key in ('pressure_text', 'pressure_clause', 'pressure'):
        if isinstance(row.get(key), str) and row[key]:
            return row[key]
    raise ValueError('missing canonical pressure wording for '+row['instance_id'])


def semantic_sites(row: dict, tokenizer) -> dict:
    """Return absolute unpadded indices, [] for unsupported/ambiguous bins.

    Exact prefix checks at BOTH ends reject BPE merges across a boundary. Text
    spans come only from explicit builder character spans or unique source text;
    equal lengths never establish a cross-condition token map.
    """
    prompt = row.get('prompt')
    require(isinstance(prompt,str) and prompt, 'missing prompt bytes')
    special = row.get('add_special_tokens', False)
    encode = lambda text: list(map(int, tokenizer.encode(text, add_special_tokens=special)))
    tokens = encode(prompt)
    require(tokens and ('tokens' not in row or tokens == row['tokens']), 'changed tokenizer tokens')
    if 'attention_mask' in row:
        require(row['attention_mask'] == [1]*len(tokens), 'semantic source must be unpadded')
    require(row.get('readout',len(tokens)-1) == len(tokens)-1, 'invalid assistant readout')
    result = {name:[] for name in BINS}; result['assistant_readout']=[len(tokens)-1]
    if row.get('task') in ('ioi','mmlu'):
        return result
    supplied=row.get('semantic_char_spans',{})
    fields={'pressure_request': ('request_text',) if row.get('condition') in ('I','user_neutral') else ('pressure_clause','pressure','pressure_text'),
            'item_designation': ('designation_text',), 'question': ('question',)}
    for name, keys in fields.items():
        span=supplied.get(name)
        if span is None and name=='pressure_request':
            texts=[row[k] for k in keys if isinstance(row.get(k),str) and row[k]][:1]
            if texts and len(set(texts))==1:
                from dataset.matched_honest import clause_span, split_around_clause
                try:
                    prefix,_,suffix=split_around_clause(prompt,texts[0])
                    a,b=clause_span(tokenizer,prompt,texts[0])
                    # Verify exact prefix/full/suffix boundaries, retaining the
                    # leading space which belongs to Llama's clause token.
                    left=encode(prefix); right=encode(prompt[:len(prompt)-len(suffix)])
                    if tokens[:a]==left and tokens[:b]==right:
                        if 'user_request_span' not in row or row['user_request_span']==[a,b]:
                            result[name]=list(range(a,b)); continue
                except (ValueError,AssertionError):
                    pass
        if span is None:
            texts=[row[k] for k in keys if isinstance(row.get(k),str) and row[k]][:1]
            if not texts or len(set(texts)) != 1 or prompt.count(texts[0]) != 1:
                continue
            start=prompt.index(texts[0]); span=[start,start+len(texts[0])]
        if not (isinstance(span,(tuple,list)) and len(span)==2
                and all(type(i) is int for i in span) and 0<=span[0]<span[1]<=len(prompt)):
            continue
        start,end=map(lambda i:encode(prompt[:i]),span)
        if tokens[:len(start)] != start or tokens[:len(end)] != end or len(start)>=len(end):
            continue
        result[name]=list(range(len(start),len(end)))
    if isinstance(row.get('semantic_source'),dict):
        from component_analysis.segmentation import resolve_segmentation, validate_segmentation, SegmentationError
        source=dict(row['semantic_source'],clean_prompt=prompt)
        if row.get('honest_item'): source['clean_item_d']=row['honest_item']
        try:
            seg=resolve_segmentation(source.get('task',row.get('task')),source,tokenizer)
            validate_segmentation(seg,source,tokenizer)
            require(seg.n_tokens==len(tokens),'question segmentation token mismatch')
            result['question']=seg.segments['question'].token_indices()
        except (ValueError,KeyError,TypeError,SegmentationError):
            result['question']=[]
    pair=row.get('designation_source')
    if isinstance(pair,dict) and row.get('stream') in ('clean','corrupt'):
        from dataset.deception_common import assert_aligned_pair
        try:
            a,b,index=assert_aligned_pair(tokenizer,pair['clean_prompt'],pair['corrupt_prompt'],
                pair['clean_item_d'],pair['corrupt_item_d'],max(len(encode(pair['clean_prompt'])),len(encode(pair['corrupt_prompt']))))
            # Legacy builder asserts disappear under -O; repeat all invariants.
            diffs=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
            require(len(a)==len(b) and diffs==[index] and index<len(a)-1,'unsupported designation pair')
            require(tokenizer.encode(' '+pair['clean_item_d'],add_special_tokens=False)==[a[index]]
                    and tokenizer.encode(' '+pair['corrupt_item_d'],add_special_tokens=False)==[b[index]],'designation token mismatch')
            expected=a if row['stream']=='clean' else b
            require(list(expected)==tokens and pair[row['stream']+'_prompt']==prompt,'wrong condition designation source')
            result['item_designation']=[index]
        except (ValueError,AssertionError,KeyError,IndexError):
            result['item_designation']=[]
    return result


def semantic_record(row, tokenizer):
    sites=semantic_sites(row,tokenizer)
    return dict(prompt_utf8_hex=row['prompt'].encode().hex(), sites=sites,
                role_spans=copy.deepcopy((row.get('layout') or {}).get('role_spans',[])),
                layout=copy.deepcopy(row.get('layout')),
                coverage={k:dict(covered=len(v),supported=bool(v),
                    reason=None if v else 'missing, ambiguous or non-exact builder/tokenizer boundary') for k,v in sites.items()},
                clause_role='user transparent request' if row.get('condition') in ('I','user_neutral') else 'system pressure clause',
                cross_condition_policy='D/H and I/user_neutral require builder supported map; D/I pooled summaries only')


def _utility_identity(row):
    ids={row[k] for k in ('instance_id','source_id','donor_id','donor_source_id') if isinstance(row.get(k),str)}
    prompts={s['prompt'].encode().hex() for s in row.get('streams',{}).values() if isinstance(s.get('prompt'),str)}
    for key in ('donor','source_reference','source_recipient'):
        if isinstance(row.get(key),dict):
            child_ids,child_prompts=_utility_identity(row[key]); ids |= child_ids; prompts |= child_prompts
    return ids,prompts


def eligible_ioi(candidates, fixed_rows, *, n=100):
    """Choose first seed-2 unique prompts, excluding fixed prompts AND donors."""
    banned_ids=set(); banned_prompts=set()
    for row in fixed_rows:
        ids,prompts=_utility_identity(row); banned_ids |= ids; banned_prompts |= prompts
    result=[]
    for row in candidates:
        ids,prompts=_utility_identity(row)
        if not ids or not prompts or ids & banned_ids or prompts & banned_prompts:
            continue
        result.append(copy.deepcopy(row)); banned_ids |= ids; banned_prompts |= prompts
        if len(result)==n: break
    return result


def confound_diagnostics(rows):
    """Metadata-only nearest-centroid classifier: train fit, validation report.

    Diagnostics never filter rows. Neutral-frame activation directions/cosines
    are deliberately deferred to Task 2.
    """
    import numpy as np
    features=[]; tables=defaultdict(list)
    for row in rows:
        for stream,record in row['streams'].items():
            n=len(record['tokens']); request=record.get('user_request_span',[])
            roles=(record.get('layout') or {}).get('content_spans',[])
            user=sum(b-a for name,a,b in roles if name=='user')
            system=sum(b-a for name,a,b in roles if name=='system')
            values=[n, (request[1]-request[0]) if request else 0,
                    request[0] if request else 0, user, system, record.get('readout',n-1)]
            entry=dict(condition=row['condition'],split=row['split'],instance_id=row['instance_id'],stream=stream,features=values)
            features.append(entry); tables[(row['condition'],row['split'])].append(values)
    table=[dict(condition=c,split=s,n=len(values),mean=np.mean(values,axis=0).tolist(),
                minimum=np.min(values,axis=0).tolist(),maximum=np.max(values,axis=0).tolist()) for (c,s),values in sorted(tables.items())]
    train=[r for r in features if r['split']=='train']; validation=[r for r in features if r['split']=='validation']
    centers={}; accuracy=None
    if train and validation:
        x=np.asarray([r['features'] for r in train],float); scale=x.std(axis=0); scale[scale==0]=1
        for condition in sorted({r['condition'] for r in train}):
            centers[condition]=np.mean([np.asarray(r['features'])/scale for r in train if r['condition']==condition],axis=0)
        hits=sum(min(centers,key=lambda c:(float(np.sum((np.asarray(r['features'])/scale-centers[c])**2)),c))==r['condition'] for r in validation)
        accuracy=hits/len(validation)
    return dict(diagnostic_only=True,exclusion_filter=False,feature_names=['prompt_length','request_length','request_position','user_content_length','system_content_length','readout_position'],
                table=table,classifier='train-standardized nearest condition centroid',validation_accuracy=accuracy,
                neutral_frame_activation_directions='Task 2; cosine with D-minus-I; role persistence limits interpretation')


def freeze_a3(a1_prepared, a1_selected, matched_manifest, historical_readings, *, root_ruling):
    p,s,m,h=a1_prepared,a1_selected,matched_manifest,historical_readings
    require(ladder._hash(root_ruling) == ladder._hash(ROOT_RULING_V1), 'missing/unsupported root ruling contract')
    require(p.get('kind')=='prepared' and s.get('kind')=='selected', 'missing A1 parent artifacts')
    require(s.get('design_sha256')==ladder._hash(p), 'stale parent design hash')
    require(s.get('group_sha256')==ladder._hash(s.get('groups')) and s.get('bank_sha256')==ladder._hash(s.get('banks')), 'stale selected groups/banks')
    completion=h.get('selection_completion',{})
    require(completion.get('selection_artifact_sha256')==ladder._hash(s) and completion.get('design_sha256')==ladder._hash(p), 'missing/stale selection completion evidence')
    for key in ('commit','model','model_revision','tokenizer_revision'):
        require(s.get('execution_provenance',{}).get(key)==p.get(key) and p.get(key), 'stale A1 execution identity: '+key)
    require(m.get('cohort')=='matched' and m.get('fleet_ready') is True, 'matched build required')
    for key in ('source_hashes','tokenizer_identity','grader_sha256'):
        require(key in p and m.get('parent_fingerprints',{}).get(key)==p[key], 'changed parent '+key)
    tasks=p['tasks']; require(len(tasks)==len(set(tasks)) and set(tasks)==set(p['designs'])==set(s['groups'])==set(m['tasks']), 'incomplete full A1 task scope')
    union=set().union(*(_ids(f['mover_selection_ids'],'mover') for f in p['designs'].values()))
    for f in p['designs'].values():
        require(_ids(f['selection_exclusion_ids'],'exclusion')==union, 'incomplete historical exclusion union')
    frozen={}; access_rows={}; diagnostic_rows=[]
    for task in tasks:
        conditions=h.get('source_rows',p['rows'])[task]
        if 'source_rows' in h:
            require(set(conditions)==set(p['rows'][task]),'invalid source enrichment conditions')
            semantic_fields={'pressure','pressure_text','pressure_clause','request_text','question','designation_text'}
            for c,values in conditions.items():
                original=ladder._index(p['rows'][task][c],condition=c)
                enriched=ladder._index(values,condition=c)
                require(set(original)==set(enriched),'source enrichment changes membership')
                for rid,row in original.items():
                    require(all(enriched[rid].get(k)==v for k,v in row.items() if k not in semantic_fields),
                            'source enrichment changes immutable A1 row')
        require(set(conditions)==set(ladder.CONDITIONS),'incomplete conditions')
        indexed={c:ladder._index(values,condition=c) for c,values in conditions.items()}
        ownership={}
        for values in indexed.values():
            for rid,row in values.items():
                require(rid not in ownership or ownership[rid]==row['split'], 'train/validation/test collision')
                ownership[rid]=row['split']
        build=m['tasks'][task]; split_sets={name:_ids(build['split_ids'][name],name) for name in ('train','validation','test')}
        require(not any(split_sets[a]&split_sets[b] for a,b in [('train','test'),('validation','test'),('train','validation')]), 'matched split collision')
        for arm in ('D','I'):
            require(arm in build.get('actual_split_ids',{}),'missing actual matched cohort membership')
            for split,ids in split_sets.items():
                require(_ids(build['actual_split_ids'][arm][split],'actual '+arm)==ids, 'actual matched membership differs')
        for split,ids in split_sets.items():
            require(all(ids <= {rid for rid,r in values.items() if r['split']==split} for values in indexed.values()), 'matched membership absent in A1 source rows')
        assessment=list(p['designs'][task]['assessment_ids']); assessment_set=_ids(assessment,'assessment')
        require(len(assessment)==100 and assessment_set<=split_sets['test'] and not assessment_set&union,'fixed A1 assessment unavailable')
        fit=sorted(split_sets['train']-union); selection=sorted(split_sets['validation']-union)
        require(len(fit)>=50 and len(selection)>=30, 'insufficient eligible unique fit/validation ids (minimum 50/30)')
        clause=[]
        for r in h.get('rows',[]):
            if r.get('task')==task.removesuffix('_v2') and r.get('category')=='kv_clause':
                parts=r['label'].split('.'); require(len(parts)==3 and parts[0]=='head','invalid historical kv_clause head')
                clause.append(('head',int(parts[1]),int(parts[2])))
        require(clause and h.get('source_hashes'), 'missing historical clause readers/source hashes')
        sites=sorted(set(clause+QUARTET)); nodes=sorted(set(map(tuple,s['groups'][task]['full']))|set(QUARTET))
        require(all(k in ('head','mlp') and 0<=l<32 and 0<=i<(32 if k=='head' else 1) for k,l,i in nodes+sites), 'invalid frozen node geometry')
        kv=sorted({(kind,l,i//4) for k,l,i in nodes if k=='head' for kind in ('k','v')})
        ids=fit+selection+assessment
        pressure={split:dict(Counter(_pressure(indexed['D'][i]) for i in selected)) for split,selected in [('fit',fit),('selection',selection),('assessment',assessment)]}
        frozen[task]=dict(fit_ids=fit,selection_ids=selection,assessment_ids=assessment,pressure_cluster_counts=pressure,
            direction_sites=[list(k) for k in sites],edge_nodes=[list(k) for k in nodes],kv_receivers=[list(k) for k in kv],
            descriptive=task=='sdr_v2',primary_position='last unpadded assistant readout')
        access_rows[task]=[copy.deepcopy(indexed[c][i]) for c in ladder.CONDITIONS for i in ids]
        diagnostic_rows += [indexed[c][i] for c in ladder.CONDITIONS for i in fit+selection]
    donor_ids={task:sorted({r['donor_id'] for r in p['designs'][task].get('donors',[]) if r.get('donor_id')}) for task in tasks}
    return dict(schema_version=1,kind='specificity_ladder_a3_design',root_ruling=copy.deepcopy(root_ruling),seeds=[42,1,123],
        confirmatory_family=['direction_FAR','direction_SER'],tasks=frozen,selection_exclusion_ids=sorted(union),
        parent_digests=dict(prepared=ladder._hash(p),selected=ladder._hash(s),matched=ladder._hash(m)),
        a1_identity={k:copy.deepcopy(p[k]) for k in ('commit','model','model_revision','tokenizer_revision','tokenizer_identity','grader_sha256','source_hashes')},
        selection_completion=copy.deepcopy(completion),historical_source_hashes=copy.deepcopy(h['source_hashes']),
        utility=copy.deepcopy(p['utility']),access_rows=access_rows,donor_ids=donor_ids,confounds=confound_diagnostics(diagnostic_rows),
        cluster_bootstrap_policy=dict(unit='canonical source D pressure text',draw_count='number of eligible wording clusters C',
            sampling='sample C wording clusters with replacement; carry every member ID',
            weights='cluster multiplicity per member ID, normalized to sum 1',
            report_sizes=['expanded','unique','effective'],row_truncation=False,instance_fallback=False),
        semantic_policy=dict(primary='readout',secondary='mean over each own verified clause span',D_I='pooled semantic summaries only',utility='IOI/MMLU readout only; mechanism bins inapplicable'),
        injected=bool(p.get('injected')))


def validate_access(design: dict, registry_paths: list[str]) -> dict:
    """Refresh registries against every fit/selection/assessment and donor ID."""
    contexts={}
    rows=copy.deepcopy(design.get('access_rows',{}))
    for task in ('ioi','mmlu'):
        rows[task]=copy.deepcopy(design.get('utility',{}).get(task,[]))
    rows['ioi'] += copy.deepcopy(design.get('ioi_validation',[]))
    for task,values in rows.items():
        expanded=[dict(instance_id=i) for i in design.get('donor_ids',{}).get(task,[])]
        for row in values:
            ids,_=_utility_identity(row)
            expanded += [dict(instance_id=i) for i in sorted(ids)]
        contexts[task]=dict(rows={'D':{s:expanded if s=='test' else [] for s in common.SPLITS}})
    args=SimpleNamespace(splits=list(common.SPLITS),registry=registry_paths)
    return common.check_registry(args,contexts)
