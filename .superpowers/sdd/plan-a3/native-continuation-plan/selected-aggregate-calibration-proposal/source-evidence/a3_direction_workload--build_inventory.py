def build_inventory(design: dict, protocol: dict, *, stage: str, fits=None, selected=None) -> dict:
    """Enumerate actual row keys/shards/forwards without model or filesystem I/O."""
    _require(stage in STAGES,'unknown inventory stage')
    _require(design.get('seeds')==list(SEEDS),'exact seeds 42/1/123 required')
    _require(set(design['tasks'])=={'far_v2','ser_v2','sdr_v2'},'full frozen task scope required')
    cfg=protocol.get('workload')
    _require(isinstance(cfg,dict),'frozen protocol workload execution geometry required')
    batch=_integer(cfg.get('microbatch_size'),'microbatch size')
    tile=_integer(cfg.get('axis_tile_sizes',{}).get(stage,cfg.get('axis_tile_size')),'axis tile size')
    jobs=_integer(cfg.get('jobs_by_stage',{}).get(stage,cfg.get('jobs')),'job count')
    _require(stage not in ('prefit','selected-pilot') or jobs==1,'one atomic timing job required per pilot part')
    _integer(cfg.get('num_layers',32),'model layer count')
    for key in ('head_width','hidden_size','dtype_bytes'):
        _integer(cfg.get(key),key)
    for key in ('warmup_batches','serialization_batches'):
        _integer(cfg.get(key),key,positive=False)
    _finite(cfg.get('finish_reserve_seconds'),'finish reserve')
    hardware=copy.deepcopy(cfg.get('hardware'))
    _require(isinstance(hardware,dict) and hardware.get('gpu'),'named hardware required')
    _integer(hardware.get('count'),'GPU count')
    identity=inventory_identity(design,protocol)
    numeric=protocol.get('numeric_profile',{})
    _require(design.get('injected') or numeric.get('dtype') and numeric.get('backend'),'numeric dtype/backend required')
    _require(design.get('injected') is True or 'task_order' in protocol,'production requires frozen task_order')
    task_order=protocol.get('task_order',sorted(design['tasks']))
    _require(len(task_order)==len(set(task_order)) and set(task_order)==set(design['tasks']),'changed frozen task order coverage')
    timing={t:_timing_ids(_source_rows(design,t,'validation')) for t in list(task_order)+['ioi','mmlu']}
    if 'timing_ids' in cfg:
        _require(cfg['timing_ids']==timing,'changed frozen metadata-only timing membership')
    inv=dict(schema_version=1,kind='a3_direction_inventory',stage=stage,
        phase='M1' if stage in ('prefit','selected-pilot') else 'M2',subphase='directions',
        pilot_part='prefit' if stage in ('prefit','fit-select') else 'selected',
        admission_scope='fit-validation-only' if stage in ('prefit','fit-select') else 'calibration-assessment-steering',
        identity=identity,hardware=hardware,injected=bool(design.get('injected')),
        timing_ids=timing,requirements=[],shards=[],expected_keys=[],captures=[],probe_reads=[],packing_invocations=[],
        fit_failures=[],blockers=[],conditional_unavailable=[],forward_counts={},jobs=[],
        finish_reserve_seconds=cfg['finish_reserve_seconds'],bytes={},
        reuse_policy=copy.deepcopy(cfg.get('reuse_policy')),
        frozen_inputs=copy.deepcopy(dict(design=design,protocol=protocol,fits=fits,selected=selected)))
    counters=Counter(); profile_by_id={}; captures={}; positives={}; peaks=Counter(); shard_ids=set(); source_index={}

    def profile(task,split,n,lanes,sites,*,singleton=False):
        if cfg.get('pad_tail_batches') and not singleton and split!='train': n=batch
        width=cfg['widths'][task][split]
        _integer(width,'padded width')
        return dict(source_task=task,padded_width=width,physical_batch_size=n*lanes,
            axis_tile_size=lanes,dtype=numeric.get('dtype','synthetic'),backend=numeric.get('backend','synthetic'),
            model=identity['model'],model_revision=identity['model_revision'],source_sha256=digest(identity['code_hashes']),
            sites=copy.deepcopy(sites),positive_singleton=singleton,capture_scope='all_senders' if singleton else 'requested_head_union')

    def input_scope(keys, p):
        out=[]; seen=set()
        for key in keys:
            if len(key)==12:
                task,split,c,stream,rid=key[2],key[3],key[10],key[11],key[9]
            else:
                task,split,c,stream,rid=key
            scopekey=(task,split,c,stream,rid)
            if scopekey in seen: continue
            seen.add(scopekey)
            indexkey=(task,split)
            if indexkey not in source_index:
                source_index[indexkey]={(r.get('condition',task),r['instance_id']):r for r in _source_rows(design,task,split)}
            row=source_index[indexkey][(c,rid)]; data=row['streams'][stream]
            out.append(dict(source_task=task,analysis_split=split,instance_id=rid,condition=c,stream=stream,
                record=copy.deepcopy(row),unpadded_length=_length(row,stream),
                padded_width=p['padded_width'],readout=data.get('readout',_length(row,stream)-1)))
        if cfg.get('pad_tail_batches') and out and not p.get('positive_singleton'):
            size=p['physical_batch_size']//p['axis_tile_size']
            real_ids=[x['instance_id'] for x in out]
            # Requirements are one homogeneous recipient batch; aliases are
            # execution-only duplicates and never enter scientific target keys.
            while len(out)<size:
                duplicate=copy.deepcopy(out[0]); original=duplicate['instance_id']
                alias='a3-dummy:'+digest([duplicate['source_task'],duplicate['analysis_split'],duplicate['condition'],real_ids,len(out)])
                duplicate.update(instance_id=alias,source_instance_id=original)
                duplicate['record']=dict(duplicate['record'],instance_id=alias,
                    execution_dummy=dict(duplicate_of=original,source_sha256=digest(out[0]['record'])))
                out.append(duplicate)
        return out

    def req(operation,p,keys,axes,*,batches=1,family='',timing_keys=None,axis_scope=None,job_id=None):
        item=dict(operation=operation,profile=p,batches=batches,family=family,call_index=len(inv['requirements']),declared_job_id=job_id,
            target_keys=keys,timing_keys=timing_keys if timing_keys is not None else keys,axis_ids=list(axes),axis_scope=axis_scope or [])
        item['timing_inputs']=input_scope(item['timing_keys'],p)
        item['target_unmasked_lengths']=[x['unpadded_length'] for x in input_scope(keys,p)]
        item['timing_unmasked_lengths']=[x['unpadded_length'] for x in item['timing_inputs']]
        item['axis_class']='validated_nonzero_image_axis' if inv['pilot_part']=='prefit' and axes else None
        item['donor_convention']=('frozen_cyclic_different_question_readout' if p['positive_singleton'] else 'none') if p['source_task']=='mmlu' else ('repeated_B_corrupt' if p['source_task']=='ioi' else 'same_ID_condition_opposite_stream')
        item['requirement_id']=digest(item)
        inv['requirements'].append(item)
        counters[operation]+=batches
        profile_by_id[digest(p)]=p
        n=p['physical_batch_size']; width=p['padded_width']; sites=p['sites']
        peaks['transient_capture_peak']=max(peaks['transient_capture_peak'],
            n*width*cfg['hidden_size']*len({s[1] for s in sites})*cfg['dtype_bytes'])
        vocab=cfg.get('vocabulary_size',8 if design.get('injected') else None)
        _integer(vocab,'vocabulary size')
        peaks['transient_native_logits_peak']=max(peaks['transient_native_logits_peak'],n*width*vocab*cfg['dtype_bytes'])
        peaks['transient_readout_logits_peak']=max(peaks['transient_readout_logits_peak'],n*vocab*4)
        peaks['transient_residual_peak']=max(peaks['transient_residual_peak'],n*width*cfg['hidden_size']*cfg['dtype_bytes'])
        if p['positive_singleton']:
            # The reviewed helper retains recipient+donor all-head/MLP captures,
            # replacements and patched output during its three-forward pass.
            positive_peak=8*n*width*cfg['hidden_size']*cfg.get('num_layers',32)*cfg['dtype_bytes']
            peaks['positive_calibration_transient_peak']=max(peaks['positive_calibration_transient_peak'],positive_peak)
            peaks['transient_capture_peak']=max(peaks['transient_capture_peak'],positive_peak)
        peaks['readout_chunk_peak']=max(peaks['readout_chunk_peak'],n*len(sites)*cfg['head_width']*4)
        return item['requirement_id']

    def streams(task):
        return ('clean',) if task in ('ioi','mmlu') else ('clean','corrupt')

    def groups(task,split,*,pilot=False,train=False,target_split=None):
        rows=_source_rows(design,task,split)
        chosen=timing[task] if pilot else list(dict.fromkeys(r['instance_id'] for r in rows))
        chunk_size=cfg.get('train_microbatch_size',batch) if train else batch
        _integer(chunk_size,'train microbatch size')
        chunks=_chunks(chosen,chunk_size)
        if pilot:
            target_rows=_source_rows(design,task,target_split or split)
            target_n=len({r['instance_id'] for r in target_rows})
            sizes={len(x) for x in _chunks(list(range(target_n)),batch)}
            _require(max(sizes)<=len(chosen),'validation timing cohort cannot cover physical target batch; freeze a smaller microbatch')
            for n in sorted(sizes-{len(x) for x in chunks}): chunks.append(chosen[:n])
        result=[]
        for c in (tuple(dict.fromkeys(r['condition'] for r in rows)) if task in ('ioi','mmlu') else CONDITIONS):
            if train and c=='F':
                continue
            for s in streams(task):
                rr={r['instance_id']:r for r in rows if r.get('condition',task)==c}
                for chunk in chunks:
                    _require(all(i in rr for i in chunk),'missing source condition')
                    width=cfg['widths'][task][split]
                    _require(all(_length(rr[i],s)<=width for i in chunk),'execution width truncates source')
                    result.append((c,s,chunk))
        return result

    def capture(task,split,sites,*,pilot=False,train=False,donor=False,lanes=tile,profile_split=None,invocation=None):
        # Donor IOI corrupt is a real separately captured stream.
        for c,s,ids in groups(task,split,pilot=pilot,train=train,target_split=profile_split or split):
            for stream in ((s,'corrupt') if donor and task=='ioi' else (s,)):
                p=profile(task,profile_split or split,len(ids),lanes,sites)
                if train and protocol.get('fit_cache'):
                    p=copy.deepcopy(protocol['fit_cache']['capture_identity']['numeric_profile'])
                    sites=copy.deepcopy(p['sites'])
                source={r['instance_id']:r for r in _source_rows(design,task,split) if r.get('condition',task)==c}
                _require(all(_length(source[i],stream)<=p['padded_width'] for i in ids),'capture profile truncates recipient/donor source')
                key=digest([task,split,c,stream,ids,p,invocation])
                if key in captures:
                    continue
                execution=input_scope([[task,split,c,stream,i] for i in ids],p)
                captures[key]=dict(capture_id=key,execution_ids=[x['instance_id'] for x in execution],
                    dummy_sources={x['instance_id']:x['source_instance_id'] for x in execution if 'source_instance_id' in x},source_task=task,split=split,condition=c,
                    stream=stream,instance_ids=ids,sites=sites,profile=p)
                op='capture_train' if train else ('capture_donor' if stream=='corrupt' and task=='ioi' else 'capture_intact')
                # Timing rows always refer to frozen validation membership.
                tk=[[task,'validation',c,stream,i] for i in (ids if pilot else timing[task][:len(ids)])]
                req(op,p,[[task,split,c,stream,i] for i in ids],[],timing_keys=tk)

    def score(panel,analysis,split,sites,cells,*,pilot=False,profile_split=None):
        for source in (analysis,'ioi','mmlu'):
            active=[c for c in cells if source!='mmlu' or c['operation']!='interchange']
            # Cells specify recipient source kinds; floors replace primary donor op.
            expanded=[]
            for cell in active if source!='mmlu' else cells:
                if source=='mmlu':
                    if cell.get('secondary'):
                        continue
                    ops=(cell['operation'],) if cell['operation'].startswith('steer_') else ('zero','h_mean')
                else:
                    ops=(cell['operation'],)
                for operation in ops:
                    expanded.append(dict(cell,operation=operation))
            invocation=digest([panel,analysis,source,split,sites,cells]) if pilot else None
            source_groups=groups(source,split,pilot=pilot,target_split=profile_split or split)
            if pilot and tile>1:
                _require(len(expanded)>=tile,'pilot packing invocation lacks complete physical tile; freeze smaller pilot tile')
                for n in sorted({len(x[2]) for x in source_groups}):
                    batch_groups=[dict(condition=c,stream=st,instance_ids=ids) for c,st,ids in source_groups if len(ids)==n]
                    inv['packing_invocations'].append(dict(invocation_id=digest([invocation,n]),panel=panel,analysis_task=analysis,
                        source_task=source,split=split,cells=expanded,batch_groups=batch_groups,
                        profile=profile(source,profile_split or split,n,tile,sites),
                        actual_validation_ids=list(dict.fromkeys(i for g in batch_groups for i in g['instance_ids'])),
                        captures_repeated_serial_and_packed=True))
            capture(source,split,sites,pilot=pilot,donor=True,profile_split=profile_split,invocation=invocation)
            if pilot and tile>1:
                capture(source,split,sites,pilot=True,donor=True,lanes=1,profile_split=profile_split,invocation=invocation)
            for condition,stream,ids in source_groups:
                # Floors must each be physically dispatched as distinct cells.
                execution_ids=list(ids); dummy_sources={}
                if cfg.get('pad_tail_batches'):
                    while len(execution_ids)<batch:
                        alias='a3-dummy:'+digest([source,split,condition,ids,len(execution_ids)])
                        dummy_sources[alias]=ids[0]; execution_ids.append(alias)
                for start in range(0,len(expanded),tile):
                    block=expanded[start:start+tile]
                    p=profile(source,profile_split or split,len(ids),tile,sites)
                    keys=[(panel+':batch='+str(len(ids)) if pilot else panel,analysis,source,split,c['seed'],tuple(c['site']),c['family'],c['axis_index'],c['operation'],i,condition,stream)
                          for c in block for i in ids]
                    tkeys=[(panel+':batch='+str(len(ids)) if pilot else panel,analysis,source,'validation',c['seed'],tuple(c['site']),c['family'],c['axis_index'],c['operation'],i,condition,stream)
                           for c in block for i in (ids if pilot else timing[source][:len(ids)])]
                    shard_id=digest(keys)
                    _require(keys and shard_id not in shard_ids,'duplicate scoring shard')
                    shard_ids.add(shard_id)
                    inv['shards'].append(dict(shard_id=shard_id,expected_keys=keys,profile=p,
                        panel=panel,split=split,cells=block,instance_ids=ids,
                        requirement_ids=[],control_ids=[],execution_ids=execution_ids,dummy_sources=dummy_sources,
                        dummy_positive_forward_count=3*len(dummy_sources)))
                    shard=inv['shards'][-1]
                    if p['axis_tile_size']>1:
                        shard['requirement_ids'].append(req('packing_lookup',p,keys,[c['axis_index'] for c in block],timing_keys=tkeys,
                            axis_scope=[{k:c[k] for k in ('seed','site','family','axis_index','operation','axis_reference','axis_sha256') if k in c} for c in block]))
                    inv['expected_keys'].extend(keys)
                    axes=[c['axis_index'] for c in block]
                    for op in REPLAYS:
                        shard['requirement_ids'].append(req(op,p,keys,axes,
                            family=block[0]['family'],timing_keys=tkeys,axis_scope=[{k:c[k] for k in ('seed','site','family','axis_index','operation','axis_reference','axis_sha256') if k in c} for c in block]))
                    if pilot and tile>1:
                        serial=profile(source,profile_split or split,len(ids),1,sites)
                        for op in REPLAYS:
                            req('equivalence_serial_'+op,serial,keys,axes,batches=len(block),
                                family=block[0]['family'],timing_keys=tkeys,axis_scope=[{k:c[k] for k in ('seed','site','family','axis_index','operation','axis_reference','axis_sha256') if k in c} for c in block])
                        if start==0:
                            for lanes in (1,tile):
                                dummy=profile(source,profile_split or split,len(ids),lanes,sites)
                                for op in REPLAYS:
                                    req('equivalence_dummy_'+str(lanes)+'_'+op,dummy,keys[:len(ids)],axes[:1],
                                        family=block[0]['family'],timing_keys=tkeys[:len(ids)],axis_scope=[{k:block[0][k] for k in ('seed','site','family','axis_index','operation','axis_reference','axis_sha256') if k in block[0]}])
                    if dummy_sources:
                        peaks['execution_dummy_rows']+=len(dummy_sources)*len(block)
                        pp=profile(source,profile_split or split,1,1,sites,singleton=True)
                        req('positive_control',pp,[[source,split,condition,stream,ids[0]]],[],batches=3*len(dummy_sources),
                            timing_keys=[[source,'validation',condition,stream,timing[source][0]]])
                    # Reviewed positive_control uses separately padded singleton donors.
                    for rid in ids:
                        pp=profile(source,profile_split or split,1,1,sites,singleton=True)
                        pk=digest([analysis,source,split,condition,stream,rid,pp])
                        shard['control_ids'].append(pk)
                        if pk not in positives:
                            positives[pk]=dict(profile=pp,key=[source,split,condition,stream,rid])
                            req('positive_control',pp,[[source,split,condition,stream,rid]],[],batches=3,
                                timing_keys=[[source,'validation',condition,stream,rid if pilot else timing[source][0]]])

    fit_records=_records(fits,'fit_records')
    fit_index={}
    if fits is not None:
        _require(isinstance(fit_records,list),'complete fit_records required')
        for record in fit_records:
            k=(record['task'],tuple(record['site']),record['seed'])
            _require(k not in fit_index,'duplicate fit record')
            fit_index[k]=record
    selected_records=_records(selected,'selected_records')
    sel={}
    def axis_descriptor(value, index=None):
        _require(isinstance(value,dict) and isinstance(value.get('reference'),str) and value['reference']
            and re.fullmatch('[0-9a-f]{64}',str(value.get('sha256'))) is not None,'invalid frozen axis reference/hash')
        if index is not None:
            _require(type(value.get('axis_index')) is int and value['axis_index']==index,'changed/duplicate frozen axis index')

    if stage in ('remaining','selected-pilot'):
        selected_metadata=selected.get('metadata',selected) if isinstance(selected,dict) else {}
        _require(selected_metadata.get('selection_split')=='validation','selection must be frozen on validation')
        _require(not selected_metadata.get('blocked_task_seeds'),'blocked selection task/seed')
        _require(selected.get('inventory_identity',selected.get('identity',selected.get('metadata',{}).get('inventory_identity',selected.get('metadata',{}).get('identity'))))==identity,'changed selected source/design/protocol identity')
        _require(isinstance(selected_records,list),'frozen selected_records required')
        for record in selected_records:
            k=(record['task'],record['seed'])
            _require(k not in sel,'duplicate selected seed')
            _require(len(record.get('assessment_axes',[]))==199,'exact frozen 199 assessment axes required')
            _require(len(record.get('calibration_axes',[]))==32,'exact frozen 32 calibration axes required')
            axis_descriptor(record.get('learned_axis'))
            for name in ('assessment_axes','calibration_axes'):
                for i,axis in enumerate(record[name]): axis_descriptor(axis,i)
                _require(len({digest(a) for a in record[name]})==len(record[name]),'duplicate frozen axes')
            nuisance=record.get('nuisance',{})
            _require(nuisance.get('status') in ('fitted','unfitted'),'explicit nuisance fit status required')
            if nuisance['status']=='fitted': axis_descriptor(nuisance.get('axis'))
            else:
                _require(nuisance.get('reason') and nuisance.get('fit_receipt'),'unfitted nuisance reason/receipt required')
            _require(tuple(record['site']) in map(tuple,design['tasks'][record['task']]['direction_sites']),'selected site outside frozen list')
            sel[k]=record
        _require(set(sel)=={(t,s) for t in design['tasks'] for s in SEEDS},'complete selected task/seed coverage required')
    for task in task_order:
        definition=design['tasks'][task]
        sites=definition['direction_sites']
        if not design.get('injected'):
            _require(len(definition['assessment_ids'])==100,'fixed 100 assessment IDs required')
            _require(len(design['utility']['ioi'])==100 and len(design['utility']['mmlu'])==32,'fixed utility floors required')
            _require(len(design['ioi_validation'])==100 and len(design['mmlu_validation'])==32,'separate validation utilities required')
        if stage in ('prefit','fit-select'):
            # M1 uses validation only, padded to every required train shape.
            if fits is None:
                capture(task,'validation' if stage=='prefit' else 'train',sites,pilot=stage=='prefit',train=True,lanes=1,profile_split='train')
            cells=[]
            for site in sites:
                for seed in SEEDS:
                    record=fit_index.get((task,tuple(site),seed))
                    if fit_records is not None:
                        _require(record is not None,'missing scientific fit requirement')
                        valid=record.get('dom_valid',record.get('valid',record.get('status')=='fitted'))
                        if not valid:
                            inv['fit_failures'].append(copy.deepcopy(record)); continue
                    cells.append(dict(seed=seed,site=site,family='learned',axis_index=0,operation='interchange'))
            for seed in SEEDS:
                if not any(c['seed']==seed for c in cells):
                    inv['blockers'].append(dict(task=task,seed=seed,reason='no finite valid DOM candidate'))
            # Site groups are dispatched independently: profile names exact sites.
            for site in sites:
                cc=[c for c in cells if c['site']==site]
                if cc: score('validation',task,'validation',[site],cc,pilot=stage=='prefit')
            inv['probe_reads'].append(dict(task=task,split='validation',extra_forwards=0,source='matched intact captures'))
        else:
            for seed in SEEDS:
                record=sel[(task,seed)]; site=record['site']; one=[site]
                def cell(family,index,operation='interchange',**kw):
                    if family in ('assessment_null','steering_random'): axis=record['assessment_axes'][index]
                    elif family=='calibration_null': axis=record['calibration_axes'][index]
                    elif family in ('nuisance','steering_nuisance'): axis=record['nuisance']['axis']
                    else: axis=record['learned_axis']
                    return dict(seed=seed,site=site,family=family,axis_index=index,operation=operation,
                                axis_reference=axis['reference'],axis_sha256=axis['sha256'],**kw)
                if stage=='remaining':
                    score('calibration',task,'validation',one,
                        [cell('learned',0)]+[cell('calibration_null',i) for i in range(32)])
                split='validation' if stage=='selected-pilot' else 'assessment'
                panel='selected_pilot' if stage=='selected-pilot' else 'assessment'
                pending=[]
                def dispatch(cells):
                    if stage=='selected-pilot': pending.extend(cells)
                    else: score(panel,task,split,one,cells)
                dispatch([cell('learned',0)])
                dispatch([cell('assessment_null',i) for i in range(199)])
                nuisance=record['nuisance']['status']=='fitted'
                if nuisance:
                    dispatch([cell('nuisance',0)])
                else:
                    inv['fit_failures'].append(dict(task=task,seed=seed,site=site,family='nuisance',reason=record['nuisance']['reason'],fit_receipt=record['nuisance']['fit_receipt']))
                    inv['conditional_unavailable'].append(dict(task=task,seed=seed,family='nuisance',
                        obligations=['primary/floors','secondary zero/H','both-sign steering'],
                        reason=record['nuisance']['reason'],fit_receipt=record['nuisance']['fit_receipt'],
                        interpretation='nuisance diagnostic unavailable; no nuisance interpretation gate'))
                for family in ('learned','nuisance') if nuisance else ('learned',):
                    dispatch([cell(family,0,op,secondary=True) for op in ('zero','h_mean')])
                for family in ('steering_learned','steering_nuisance','steering_random'):
                    if family=='steering_nuisance' and not nuisance: continue
                    dispatch([cell(family,0,op) for op in ('steer_positive','steer_negative')])
                if stage=='selected-pilot':
                    # One complete producer invocation, including every family;
                    # short learned/nuisance lists cannot separately prove packing.
                    score(panel,task,'validation',one,pending,pilot=True,profile_split='assessment')
                    score('calibration_pilot',task,'validation',one,
                        [cell('learned',0)]+[cell('calibration_null',i) for i in range(32)],pilot=True)
            inv['probe_reads'].append(dict(task=task,split='assessment',extra_forwards=0,source='matched intact captures'))
    inv['captures']=list(captures.values())
    inv['capture_shards']=[dict(shard_id=c['capture_id'],capture=copy.deepcopy(c)) for c in inv['captures'] if c['split']=='train']
    _require(len(inv['expected_keys'])==len(set(map(_freeze,inv['expected_keys']))),'duplicate raw row keys')
    # Guard checks are real elapsed work, not invented model forwards. The
    # bound includes model publication and complete validation-cache adaptation.
    profiles=list(profile_by_id.values())
    if cfg.get('account_runtime_guards'):
        gp=dict(profiles[0],axis_tile_size=1,physical_batch_size=1,control='root_live_guard')
        count=10*len(inv['shards'])+3*len(inv['captures'])+2*jobs
        req('guard_refresh',gp,[],[],batches=max(1,count),job_id='job-0')
    # One explicit warmup and serialization profile per job; measured independently.
    _require(profiles,'empty workload')
    for j in range(jobs):
        inv['jobs'].append(dict(job_id='job-'+str(j),shard_ids=[s['shard_id'] for i,s in enumerate(inv['shards']) if i%jobs==j]))
        if cfg['warmup_batches']:
            req('warmup',dict(profiles[0],axis_tile_size=1,physical_batch_size=profiles[0]['physical_batch_size']//profiles[0]['axis_tile_size']),[],[],batches=cfg['warmup_batches'],job_id='job-'+str(j))
        # Publication work is derived from actual payloads, never a caller's
        # optimistic row/batch total. CPU benchmark evidence covers each shape.
        shapes=[dict(kind='direction_shard',profile=s['profile'],rows=len(s['expected_keys']),
                     key_bytes=len(json.dumps(s['expected_keys']).encode()))
                for i,s in enumerate(inv['shards']) if i%jobs==j]
        shapes += [dict(kind='profile_reuse_attestation',profile=shard['profile'],rows=len(shard['expected_keys']),
                        key_bytes=len(json.dumps(shard['expected_keys']).encode()))
                   for i,shard in enumerate(inv['shards']) if i%jobs==j and shard['profile']['axis_tile_size']>1]
        if j==0:
            shapes += [dict(kind='readout_capture',profile=c['profile'],rows=len(c['instance_ids']),
                            numeric_bytes=(2*len(c.get('execution_ids',c['instance_ids']))+cfg['hidden_size'])*len(c['sites'])*cfg['head_width']*4) for c in inv['captures']]
            shapes += [dict(kind='positive_control',profile=v['profile'],rows=1) for v in positives.values()]
        shapes += [dict(kind='completion',rows=1)]
        shapes += [dict(kind='declared_extra_finalization',rows=1) for _ in range(cfg['serialization_batches'])]
        serde=dict(profiles[0],axis_tile_size=1,physical_batch_size=1,
                   serialization_shapes=shapes,serialization_shapes_sha256=digest(shapes))
        req('serialization',serde,[],[],batches=len(shapes),job_id='job-'+str(j))
    assigned={rid:'job-'+str(i%jobs) for i,shard in enumerate(inv['shards']) for rid in shard['requirement_ids']}
    for job in inv['jobs']:
        job['requirement_ids']=[r['requirement_id'] for r in inv['requirements']
            if (r['declared_job_id'] or assigned.get(r['requirement_id'],'job-0'))==job['job_id']]
        job['depends_on']=['job-0'] if job['job_id']!='job-0' else []
    inv['operation_counts']=dict(counters)
    inv['forward_counts']={op:n for op,n in counters.items() if op not in ('serialization','guard_refresh','packing_lookup')}
    inv['bytes']=dict(peaks)
    inv['bytes']['capture_disk']=sum(len(c.get('execution_ids',c['instance_ids']))*len(c['sites'])*cfg['head_width']*4 for c in inv['captures'])
    inv['bytes']['projection_blocks']=sum(len(x['direction_sites'])*cfg['head_width']*cfg['hidden_size']*4 for x in design['tasks'].values())
    inv['bytes']['row_keys_utf8']=len(json.dumps(inv['expected_keys']).encode())
    inv['storage_requirements']=derive_storage_requirements(inv)
    inv['inventory_sha256']=digest(inv)
    return inv
