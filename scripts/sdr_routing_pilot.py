#!/usr/bin/env python
"""Bounded existing-SDR donor diagnostic. All interventions use component hooks.

Freeze with --dry-run; inspect manifest/gate before running --stage stage1.
Stage2 is deliberately refused by this implementation. No inference downloads.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

ROOT = Path('/projects/beto/swong2/Alignment/Deception-Circuit')
CODE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_ROOT))
SEED = 20261020
CACHE = Path('/work/nvme/beto/swong2/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659')
FAMILIES = {
    'candidate6': [(12,6),(13,5),(13,20),(13,21),(14,24),(17,26)],
    'selector2': [(17,24),(24,27)],
    'outsider2': [(15,8),(17,25)],
}
SCOPES = ('readout', 'items', 'common')
PRIMARY_SCOPES = ('readout', 'common')


def digest(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(value).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=1, sort_keys=True)+'\n')
    os.replace(temporary, path)


def write_jsonl(path, rows):
    path = Path(path)
    temp = path.with_suffix('.tmp')
    with temp.open('w') as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True)+'\n')
    os.replace(temp, path)


def _word(word):
    return re.compile(r'(?<!\w)'+re.escape(word)+r'(?!\w)', re.I)


def audit_variant(record: dict, prompt: str, tokenizer) -> dict:
    """Derive truth from the actual saved designation, never target metadata.

    Token offsets follow segmentation.token_char_spans conventions: only tokens
    contained in a literal anchor (apart from whitespace) are aligned, so a fused boundary is
    omitted rather than silently assigned to an adjacent edited segment.
    """
    encoded = tokenizer(prompt, add_special_tokens=False, return_offsets_mapping=True,
                        truncation=False)
    ids = list(encoded['input_ids'])
    offsets = [tuple(x) for x in encoded['offset_mapping']]
    out = dict(valid=False, errors=[], ids=ids, length=len(ids), segments={},
               anchors={}, prompt_hash=digest(prompt), omitted=['pressure_clause'],
               item_ids={}, item_positions={record['item_1']:0,record['item_2']:1}, truthful_item=None, other_item=None)
    errors = out['errors']
    if len(ids) > min(128, getattr(tokenizer, 'model_max_length', 128)):
        errors.append('truncation: prompt exceeds saved 128-token budget or tokenizer limit')
    if not ids or len(offsets) != len(ids):
        errors.append('missing token offsets')
        return out
    items = [record['item_1'], record['item_2']]
    if items[0].lower() == items[1].lower():
        errors.append('item identity is not injective')
        return out
    pattern = re.compile(r'The ('+'|'.join(re.escape(x) for x in items)+
                         r') (?:result|reading) (?:is the one that is|came back) (damaging|harmless), and the other (?:is|came back) (damaging|harmless)\.', re.I)
    matches = list(pattern.finditer(prompt))
    # Count the literal sentence introduction independently: malformed duplicate
    # introductions must not disappear simply because one fails the full regex.
    introductions = list(re.finditer(r'The (?:'+'|'.join(re.escape(x) for x in items)+r') (?:result|reading)\b', prompt))
    if len(matches) != 1 or len(introductions) != 1:
        errors.append('ambiguous or missing saved designation sentence')
        return out
    designated = matches[0]
    if designated.group(2).lower() == designated.group(3).lower():
        errors.append('designation predicates are not complementary')
        return out
    item = next(x for x in items if x.lower()==designated.group(1).lower())
    truth = item if designated.group(2).lower()=='damaging' else next(x for x in items if x!=item)
    other = next(x for x in items if x!=truth)
    out.update(truthful_item=truth, other_item=other)
    system_end = prompt.find('<|eot_id|>')
    user_marker = '<|start_header_id|>user<|end_header_id|>'
    assistant_marker = '<|start_header_id|>assistant<|end_header_id|>'
    if prompt.count(user_marker)!=1 or prompt.count(assistant_marker)!=1 or system_end<designated.end():
        errors.append('ambiguous chat anchors')
        return out
    user_start = prompt.index(user_marker)+len(user_marker)
    user_end = prompt.find('<|eot_id|>', user_start)
    stem_start = prompt.index(assistant_marker)+len(assistant_marker)
    # Old generic suffix is valid under both designation polarities. An explicit
    # named relevance suffix must name the semantically damaging item.
    suffix_end = system_end
    clause = record.get('pressure', '')
    if clause and clause in prompt[designated.end():system_end]:
        if prompt.count(clause)!=1:
            errors.append('ambiguous pressure clause')
        suffix_end=prompt.index(clause,designated.end())
    suffix=prompt[designated.end():suffix_end]
    for explicit in re.finditer(r'THE (\w+) (?:ONE|RESULT|READING) IS THE RELEVANT ONE', suffix, re.I):
        named=explicit.group(1)
        if named.lower() not in ('damaging',) and named.lower()!=truth.lower():
            errors.append('explicit relevance suffix contradicts truthful item')
    def claim(name, start, end):
        positions=[i for i,(a,b) in enumerate(offsets) if b>start and a<end and not prompt[a:min(start,b)].strip() and not prompt[max(end,a):b].strip()]
        if not positions:
            errors.append('empty anchor: '+name)
        out['segments'][name]=positions
        out['anchors'][name]={'span':[start,end], 'text':prompt[start:end]}
    claim('readout', offsets[-1][0], offsets[-1][1])
    claim('intro', 0, designated.start())
    claim('designation_suffix', designated.end(), suffix_end)
    claim('question', user_start, user_end)
    claim('stem', stem_start, len(prompt))
    for named in items:
        for role, start, end in [('intro',0,designated.start()), ('designation',designated.start(),designated.end()), ('question',user_start,user_end)]:
            hits=list(_word(named).finditer(prompt,start,end))
            if role=='intro' and len(hits)!=1:
                errors.append('ambiguous item intro: '+named)
            if role=='question' and len(hits)!=2:
                errors.append('ambiguous item question/option: '+named)
            if role=='designation' and named!=item:
                out['segments'][f'item:{named}:{role}']=[]
            for n,hit in enumerate(hits):
                mention_role = ('question' if n==0 else 'option') if role=='question' else role
                claim(f'item:{named}:{mention_role}', *hit.span())
    prefix = tokenizer.encode(prompt, add_special_tokens=False)
    for named in items:
        continuation=tokenizer.encode(prompt+' '+named, add_special_tokens=False)
        standalone=tokenizer.encode(' '+named, add_special_tokens=False)
        if continuation[:len(prefix)]!=prefix or len(continuation)!=len(prefix)+1 or len(standalone)!=1 or standalone[0]!=continuation[-1]:
            errors.append('not a single-token stem continuation: '+named)
        elif continuation:
            out['item_ids'][named]=int(continuation[-1])
    if len(set(out['item_ids'].values()))!=2:
        errors.append('answer token identities are not injective')
    if len(out['item_ids'])==2:
        out.update(truth_id=out['item_ids'][truth], other_id=out['item_ids'][other])
    out['content_hash']=digest(prompt[:designated.end()]+prompt[user_start:])
    out['valid']=not errors
    return out


def semantic_map(recipient: dict, donor: dict, *, scope: str) -> list:
    if not recipient['valid'] or not donor['valid']:
        raise ValueError('cannot map invalid semantic audit')
    if scope=='all_aligned':
        if recipient['ids']!=donor['ids']:
            raise ValueError('all_aligned requires exact token-for-token pair shape')
        return [(i,i) for i in range(recipient['length'])]
    if scope not in SCOPES:
        raise ValueError('unknown semantic scope: '+scope)
    names=['readout'] if scope=='readout' else sorted(set(recipient['segments']) & set(donor['segments']))
    if scope=='items':
        names=[x for x in names if x.startswith('item:')]
    elif scope=='common':
        names=['readout']+[x for x in names if x!='readout']
    result=[];used_r=set();used_d=set()
    for name in names:
        r=recipient['segments'][name]; d=donor['segments'][name]
        # Exact matching named spans only; no clause stretch or identity swap.
        if len(r)!=len(d) or not r:
            continue
        if [recipient['ids'][i] for i in r]!=[donor['ids'][i] for i in d]:
            continue
        for a,b in zip(r,d):
            if a not in used_r and b not in used_d:
                result.append((a,b));used_r.add(a);used_d.add(b)
    return sorted(result)


def remap_capture(value, mapping: list, recipient_length: int):
    import torch
    if len({r for r,d in mapping})!=len(mapping) or len({d for r,d in mapping})!=len(mapping):
        raise ValueError('position map must be one-to-one')
    out=value.new_zeros((value.shape[0],recipient_length,value.shape[-1]))
    valid=torch.zeros(recipient_length,dtype=torch.bool,device=value.device)
    for r,d in mapping:
        if not 0<=r<recipient_length or not 0<=d<value.shape[1]:
            raise ValueError('position outside nonpadding prompt')
        out[:,r]=value[:,d];valid[r]=True
    return out,valid


def story_key(record):
    return digest({k: record.get(k) for k in ('entity','domain','item_pair','template_variant')})


def freeze_groups(records, *, seed=SEED, max_stories=48):
    grouped=defaultdict(list)
    for r in records:grouped[story_key(r)].append(r)
    keys=sorted(grouped,key=lambda k:digest([seed,k]))[:max_stories]
    result=[]
    for i,key in enumerate(keys):
        # Representative choice also independent of input ordering/polarity.
        r=min(grouped[key],key=lambda x:digest(x))
        result.append(dict(story_id=key,split='discovery' if i<len(keys)//2 else 'confirmation',record=r,n_source_variants=len(grouped[key])))
    return result


def panel_for_record(record, tokenizer, pool, alternatives):
    from dataset.matched_honest import replace_clause
    entry=pool.get(record['pressure_id'])
    conditions=[('P', record['pressure_id'],record['pressure'])]
    if entry and entry['pressure']==record['pressure']:
        conditions.append(('H','H:'+record['pressure_id'],entry['instruction']))
    conditions.append(('N','N',''))
    conditions.extend(('P',pid,clause) for pid,clause in alternatives)
    panel=[]
    for truth,prompt in enumerate((record['clean_prompt'],record['corrupt_prompt'])):
        for condition,pid,clause in conditions:
            edited=replace_clause(prompt,record['pressure'],clause)
            audit=audit_variant({**record,'pressure':clause},edited,tokenizer)
            panel.append(dict(**audit,prompt=edited,truth=truth,condition=condition,pressure_id=pid,source_instance_id=record['instance_id'],primary_pressure_id=record['pressure_id'],item_pair=record['item_pair'],designation_polarity=record.get('designation_polarity'),item_polarity=record.get('item_polarity')))
    return panel


def frozen_families():
    suite=ROOT/'outputs/_launch_format_control/suites.json'
    config=json.loads(suite.read_text())['format-control-sdr-coarse-nls0.3']['runs']
    masks={};sources={str(suite):file_hash(suite)}
    for label,path in config.items():
        p=Path(path)/'active_nodes.json'
        data=json.loads(p.read_text())
        # Coarse source active_heads is the saved head family, never MLP gates.
        masks[label]={(int(l),int(h)) for l,heads in data['active_heads'].items() for h in heads}
        sources[str(p)]=file_hash(p)
    shared=set.intersection(*masks.values())
    if len(shared)!=32:
        raise ValueError(f'frozen D∩H∩F has {len(shared)} heads, expected32')
    families={k:list(v) for k,v in FAMILIES.items()}
    families['shared32']=sorted(shared)
    if not set(families['candidate6']+families['selector2']+families['outsider2'])<=masks['D']:
        raise ValueError('named family outside frozen D')
    forbidden=set.union(*masks.values())|set(sum(families.values(),[]))
    candidates=[(l,h) for l in sorted({l for l,h in FAMILIES['candidate6']}) for h in range(32) if (l,h) not in forbidden]
    families['outside_mask2']=sorted(candidates,key=lambda x:digest([SEED,x]))[:2]
    families['empty']=[]
    return families,sources


def freeze_donor_plan(panel, *, seed=SEED):
    strata=defaultdict(set)
    for row in panel:
        strata[(row['split'],row['item_pair'])].add(row['story_id'])
    partners={}
    for stories in strata.values():
        ordered=sorted(stories,key=lambda sid:digest([seed,sid]))
        for index in range(0,len(ordered)-1,2):
            a,b=ordered[index:index+2];partners[a]=b;partners[b]=a
    return {r['variant_id']:sorted(d['variant_id'] for d in panel if d['variant_id']!=r['variant_id'] and (d['story_id']==r['story_id'] or d['story_id']==partners.get(r['story_id']))) for r in sorted(panel,key=lambda x:x['variant_id'])}


def counterbalance_bits(panel):
    """Balance within frozen splits using an independent hash domain."""
    strata=defaultdict(set)
    for row in panel:strata[row['split']].add(row['story_id'])
    result={}
    for stories in strata.values():
        ordered=sorted(stories,key=lambda sid:digest(['counterbalance',SEED,sid]))
        for index,sid in enumerate(ordered):result[sid]=int(index>=len(ordered)//2)
    return result


def fixed_patch_plan(panel, donor_plan):
    """Twelve proposed directed pairs/story, frozen without emitted answers.

    b = balanced rank within split using SHA256(['counterbalance', seed, story_id]); first half0, second half1.
    PH same b; PH changed (1-b,b); PN same1-b; PN changed(b,1-b),
    each reciprocal. Original P0↔P1 adds two same-pressure contrasts.
    Two Ntruth→pairedstory Ntruth controls fill the last two slots; missing
    partners remain explicit exclusions. Natural emitted-answer matches are
    labelled only after the entire baseline panel has been measured.
    """
    groups=defaultdict(list)
    for row in panel:groups[row['story_id']].append(row)
    result=[]
    bits=counterbalance_bits(panel)
    for sid,rows in sorted(groups.items()):
        b=bits[sid]
        native={}
        for row in sorted(rows,key=lambda x:x['variant_id']):
            if row['condition']=='P' and row['pressure_id']!=row.get('primary_pressure_id',row['pressure_id']):continue
            native.setdefault((row['condition'],row['truth']),row)
        def add(a,d,role):
            result.append({'recipient_id':a['variant_id'] if a else None,'donor_id':d['variant_id'] if d else None,'story_id':sid,'split':rows[0]['split'],'pair_role':role,'counterbalance_bit':b,'exclusion':None if a and d else 'missing frozen native variant or paired-story donor'})
        for x,y,role in [(('P',b),('H',b),'same_truth_pressure_presence'),(('P',1-b),('H',b),'changed_truth_pressure_presence'),(('P',1-b),('N',1-b),'same_truth_pressure_presence'),(('P',b),('N',1-b),'changed_truth_pressure_presence'),(('P',0),('P',1),'same_pressure_changed_truth')]:
            a=native.get(x);d=native.get(y);add(a,d,role);add(d,a,role)
        for truth in (0,1):
            a=native.get(('N',truth))
            allowed=set(donor_plan.get(a['variant_id'],[])) if a else set()
            donors=[d for d in panel if d['variant_id'] in allowed and d['story_id']!=sid and d['condition']=='N' and d['truth']==truth]
            add(a,min(donors,key=lambda d:d['variant_id']) if donors else None,'nonself_no_pressure')
    return result


def build_manifest(dataset_dir: str, tokenizer, *, seed=SEED, max_stories=48) -> dict:
    from dataset.deception_common import load_or_generate_deception_data
    from dataset.matched_honest import load_matched_honest_pool
    directory=Path(dataset_dir)
    if not directory.is_absolute() or directory.resolve()!=ROOT/'data/datasets/sdr':
        raise ValueError('existing primary SDR dataset absolute path required; v2 is excluded')
    records=load_or_generate_deception_data(str(directory),split='test')
    pool=load_matched_honest_pool('sdr',str(ROOT/'dataset/deception_pools'))
    pressures={r['pressure_id']:r['pressure'] for r in records}
    groups=freeze_groups(records,seed=seed,max_stories=max_stories)
    families,sources=frozen_families()
    for p in sorted(directory.rglob('*')):
        if p.is_file() and (p.suffix in ('.json','.arrow')):sources[str(p)]=file_hash(p)
    pool_path=ROOT/'dataset/deception_pools/matched_honest_sdr.json'
    sources[str(pool_path)]=file_hash(pool_path)
    panel=[];exclusions=[]
    for group in groups:
        r=group['record']
        alternatives=sorted(((pid,p) for pid,p in pressures.items() if pid!=r['pressure_id']),key=lambda x:digest([seed,group['story_id'],x[0]]))[:2]
        variants=panel_for_record(r,tokenizer,pool,alternatives)
        # Reject malformed saved semantics before inference; never resample.
        if any(not x['valid'] for x in variants):
            exclusions.append({'story_id':group['story_id'],'reason':'semantic/token audit failed','variants':[{'truth':x['truth'],'pressure_id':x['pressure_id'],'errors':x['errors']} for x in variants if not x['valid']]})
        for i,v in enumerate(variants):
            v.update(story_id=group['story_id'],split=group['split'],variant_id=group['story_id']+':'+str(i))
            panel.append(v)
        group.pop('record')
        group.update(nuisance={k:r.get(k) for k in ('entity','domain','item_pair','template_variant')},source_instance_id=r['instance_id'],alternative_pressure_ids=[x[0] for x in alternatives])
    donor_plan=freeze_donor_plan(panel,seed=seed)
    patch_plan=fixed_patch_plan(panel,donor_plan)
    maps={}
    by_id={v['variant_id']:v for v in panel}
    invalid_stories={x['story_id'] for x in exclusions}
    for r in panel:
        for did in donor_plan[r['variant_id']]:
            d=by_id[did]
            if r['story_id'] in invalid_stories or d['story_id'] in invalid_stories:continue
            maps[r['variant_id']+'|'+did]={s:semantic_map(r,d,scope=s) for s in SCOPES}
    valid_groups=[g for g in groups if g['story_id'] not in invalid_stories]
    # Fixed small primary grid is independent of all baseline/patch outcomes.
    # The complete finite donor panel remains available for support tables.
    grid={'families':families,'scopes':list(PRIMARY_SCOPES),'dose':1.,'max_donor_pairs':sum(len(x) for x in donor_plan.values()),'matching_classes':['same_answer_changed_pressure','different_answer_same_pressure','fixed_answer_changed_truth','nonself_same_pressure_same_answer'],'reciprocal':True}
    grid['all_aligned_nonself_exact_pairs']=sum(by_id[r]['ids']==by_id[d]['ids'] for r,donors in donor_plan.items() for d in donors)
    grid['self_patch_mode']='all nonpadding positions; identical own captured head tensors'
    grid['fixed_pair_proposals']=len(patch_plan)
    grid['fixed_pair_missing']=sum(bool(p['exclusion']) for p in patch_plan)
    grid['counterbalance_bits_by_split']={split:dict(Counter(counterbalance_bits(panel)[g['story_id']] for g in groups if g['split']==split)) for split in ('discovery','confirmation')}
    grid['counterbalance_count_unit']='story groups; first half of independent counterbalance hash rank within each frozen split gets0, remainder1'
    grid['pair_recipe']="b=within-split rank by SHA256(['counterbalance',20261020,story_id]), firsthalf0 secondhalf1; P[b]↔H[b], P[1-b]↔H[b], P[1-b]↔N[1-b], P[b]↔N[1-b], native P0↔P1, N0/N1→frozen pairedstory N0/N1; alternatives baseline-only"
    grid['max_selected_donor_pairs']=len(patch_plan)
    grid['max_patch_rows']=grid['max_selected_donor_pairs']*len(families)*len(PRIMARY_SCOPES)
    grid['batch_order']='round-robin family/scope homogeneous batch8, comparison_id order within group'
    grid['max_patch_batch8_forwards']=((len(patch_plan)+7)//8)*len(families)*len(PRIMARY_SCOPES)
    grid['max_total_forwards']=grid['max_patch_batch8_forwards']+2*((len(panel)+7)//8)+1
    grid['runtime_seconds']='unmeasured: model load + 8-story calibration required; deadline truncates pending grid'
    manifest=dict(schema=1,seed=seed,dataset_dir=str(directory),sources=sources,groups=groups,valid_groups=valid_groups,panel=panel,donor_plan=donor_plan,patch_plan=patch_plan,maps=maps,exclusions=exclusions,semantic_pass=len(valid_groups)>=24,grid=grid,families_hash=digest(families),tokenizer=str(tokenizer.name_or_path),max_seconds=3300,first_checkpoint_seconds=1800,batch_size=8,planned_baseline_forwards=2*((len(panel)+7)//8),weaker_precision=len(valid_groups)<48,original_component_overlap=[])
    # Original causal IDs are observational provenance only, never selection.
    for path in sorted((ROOT/'outputs/_analyses').glob('**/instances.json')):
        try:
            raw=path.read_text()
            overlap=[g['source_instance_id'] for g in groups if g['source_instance_id'] in raw]
            if overlap:manifest['original_component_overlap'].append({'path':str(path),'sha256':file_hash(path),'instance_ids':overlap})
        except (OSError,UnicodeError):continue
    manifest['audited_original_swap_example']=[{k:x[k] for k in ('prompt','truthful_item','truth_id','other_item','errors')} for x in panel if x['story_id']==panel[0]['story_id'] and x['condition']=='P' and x['pressure_id']==panel[0]['pressure_id']]
    try:
        manifest['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=str(CODE_ROOT),timeout=10,text=True).strip()
        manifest['dirty_diff_hash']=digest(subprocess.check_output(['git','diff','HEAD','--','scripts/sdr_routing_pilot.py','tests/test_sdr_routing_pilot.py','scripts/sdr_routing_pilot.sbatch'],cwd=str(CODE_ROOT),timeout=10))
    except (OSError,subprocess.SubprocessError):manifest['git_fingerprint_error']='unavailable (10s bound)'
    manifest['code_sha256']={str(CODE_ROOT/name):file_hash(CODE_ROOT/name) for name in ('scripts/sdr_routing_pilot.py','scripts/sdr_routing_pilot.sbatch','tests/test_sdr_routing_pilot.py')}
    manifest['software']={p:importlib.metadata.version(p) for p in ('torch','transformers','datasets','nnsight')}
    manifest['software']['python']=sys.version
    manifest['condition_definitions']={'P':'saved pressure clause; at most two stable existing alternative clauses for baseline support only','H':'matched honest instruction replaces saved pressure clause','N':'saved pressure clause deleted; no instruction added'}
    manifest['model_cache']=str(CACHE)
    manifest['model_revision']=Path(str(tokenizer.name_or_path)).name
    manifest['tokenizer_files']={str(p):file_hash(p) for p in Path(str(tokenizer.name_or_path)).glob('*.json') if p.name in ('config.json','tokenizer.json','tokenizer_config.json','special_tokens_map.json')}
    manifest['dtype']='bfloat16';manifest['attention']='sdpa';manifest['device']='cuda (only non-dry stage1)'
    manifest['manifest_hash']=digest(manifest)
    return manifest


def capture_logits(model, capture):
    import torch
    from component_analysis import hooks
    residual=capture.outputs[hooks.READOUT_KEY]
    rows=torch.arange(residual.shape[0],device=residual.device)
    return hooks.readout_logits(model,residual[rows,capture.readout.to(residual.device)])


def score_capture(model, capture, truth_ids, other_ids, donor_ids=None) -> dict:
    import torch
    logits=capture_logits(model,capture).float()
    probabilities=logits.softmax(-1)
    metrics=[]
    for i,(truth,other) in enumerate(zip(truth_ids,other_ids)):
        donor=None if donor_ids is None else donor_ids[i]
        top=torch.topk(logits[i],min(10,logits.shape[-1]))
        row={'emitted_id':int(logits[i].argmax()),'truth_margin':float(logits[i,truth]-logits[i,other]),'p_truth':float(probabilities[i,truth]),'p_other':float(probabilities[i,other]),'other_mass':float(1-probabilities[i,truth]-probabilities[i,other]),'fp32_checksum':digest(logits[i].detach().cpu().contiguous().numpy().tobytes()),'top_k':[{'id':int(k),'logit':float(v),'p':float(probabilities[i,k])} for k,v in zip(top.indices,top.values)]}
        if donor is not None:
            row.update(p_donor=float(probabilities[i,donor]),donor_margin=float(logits[i,donor]-logits[i,truth if donor!=truth else other]))
        metrics.append(row)
    return {'rows':metrics,'logits':logits.detach()}


def numerical_receipt(expected, observed):
    import torch
    difference=(expected.float()-observed.float()).abs()
    finite=bool(torch.isfinite(difference).all())
    maximum=float(difference.max()) if difference.numel() else 0.
    exact=bool(torch.equal(expected,observed))
    return {'pass':finite and maximum<=1e-5,'bitwise':exact,'max_abs_error':maximum,'tolerance':1e-5,'explanation':'same capture/SDPA/fp32 readout path; any nonzero difference is retained, no BF16 tolerance'}


def emitted_item(row):
    return next((item for item,token in row['item_ids'].items() if token==row['emitted_id']), 'other')


def pressure_pair(a,b):
    ca,cb=a['condition'],b['condition']
    if ca=='P' and cb=='P':return 'P↔P′'
    if {ca,cb}=={'P','N'}:return 'P↔N'
    if {ca,cb}=={'P','H'}:return 'P↔H'
    return 'H↔N' if ca!=cb else ca+'↔'+cb


def build_comparisons(manifest: dict, baselines: list) -> list:
    indexed={r['variant_id']:r for r in baselines}
    candidates=[]
    for r in baselines:
        allowed=manifest.get('donor_plan',{}).get(r['variant_id'])
        donors=[indexed[x] for x in allowed if x in indexed] if allowed is not None else baselines
        for d in donors:
            if d['variant_id']==r['variant_id'] or d['split']!=r['split'] or d['item_pair']!=r['item_pair']:continue
            ri,di=emitted_item(r),emitted_item(d)
            pressure_change=(r['condition'],r['pressure_id'])!=(d['condition'],d['pressure_id'])
            truth_change=r['truthful_item']!=d['truthful_item']
            content_change=r['content_hash']!=d['content_hash']
            same_answer=ri==di and di!='other'
            classes=[]
            if pressure_change and same_answer:classes.append('same_answer_changed_pressure')
            if not pressure_change and ri!=di and ri!='other' and di!='other':classes.append('different_answer_same_pressure')
            if same_answer and truth_change:classes.append('fixed_answer_changed_truth')
            if r['story_id']!=d['story_id'] and not pressure_change and same_answer:classes.append('nonself_same_pressure_same_answer')
            if not classes:classes=['unsupported']
            candidates.append(dict(comparison_id=r['variant_id']+'|'+d['variant_id'],recipient_id=r['variant_id'],donor_id=d['variant_id'],story_id=r['story_id'],donor_story_id=d['story_id'],split=r['split'],recipient_condition=r['condition'],donor_condition=d['condition'],donor_matches_recipient_truth=d['emitted_id']==r['truth_id'],donor_matches_recipient_emission=d['emitted_id']==r['emitted_id'],truth_accessible=r.get('accessible',False),recipient_truth=r['truth'],recipient_truthful_item=r['truthful_item'],donor_truthful_item=d['truthful_item'],recipient_emitted_class=ri,donor_emitted_class=di,donor_answer_position=r.get('item_positions',{word:index for index,word in enumerate(r['item_pair'].split('/'))}).get(di),donor_emitted_id=d['emitted_id'],pressure_pair=pressure_pair(r,d),pressure_change=pressure_change,truth_change=truth_change,content_change=content_change,confounded=content_change or truth_change,own_story=r['story_id']==d['story_id'],support_classes=classes,recipient_hash=r['prompt_hash'],donor_hash=d['prompt_hash'],status='planned'))
    fixed={(p['recipient_id'],p['donor_id']) for p in manifest.get('patch_plan',[])}
    for c in candidates:c['scheduled']=(c['recipient_id'],c['donor_id']) in fixed
    return candidates


def evaluate_gate(manifest: dict, baselines: list, comparisons: list, controls: dict) -> dict:
    groups=manifest.get('valid_groups',manifest.get('groups',[]))
    split_counts={s:len({g['story_id'] for g in groups if g['split']==s}) for s in ('discovery','confirmation')}
    access={s:len({r['story_id'] for r in baselines if r['split']==s and r['condition'] in ('H','N') and r.get('accessible',False)}) for s in split_counts}
    by_story=defaultdict(list)
    for r in baselines:by_story[r['story_id']].append(r)
    support={};qualified=set()
    # Four observed donor pressure×item cells on independent stories. Truth
    # counterbalancing is allowed but explicitly confounded in every contrast.
    for pair,condition in (('P↔N','N'),('P↔H','H'),('P↔P′','Pprime')):
        story_ids=set();strata=Counter();strata_stories=defaultdict(lambda:defaultdict(set));fixed=set();classes=defaultdict(lambda:{'truths':set(),'answers':set()})
        for sid,rows in by_story.items():
            ps=[r for r in rows if r['condition']=='P']
            others=[r for r in rows if r['condition']==condition] if condition!='Pprime' else ps
            words=set(rows[0]['item_ids'])
            # P↔P′ is clause identity only and cannot satisfy presence gate.
            if condition=='Pprime':
                pressure_sets=defaultdict(set)
                for r in ps:pressure_sets[r['pressure_id']].add(emitted_item(r))
                complete=sum(words<=v for v in pressure_sets.values())>=2
            else:complete=words<={emitted_item(r) for r in ps} and words<={emitted_item(r) for r in others}
            if complete:story_ids.add(sid)
        relevant=[c for c in comparisons if c['pressure_pair']==pair and c['pressure_change']]
        for c in relevant:
            stratum=f"truth_change={c['truth_change']};content_change={c['content_change']}"
            strata[stratum]+=1
            strata_stories[stratum][c['split']].add(c['story_id'])
            if not c['truth_change'] and not c['content_change'] and 'same_answer_changed_pressure' in c['support_classes']:fixed.add(c['story_id'])
            if c['story_id'] in story_ids:
                for klass in c['support_classes']:
                    classes[klass]['truths'].add(c['recipient_truth'])
                    if c['donor_emitted_class']!='other':classes[klass]['answers'].add(c['donor_answer_position'])
        # Same-pressure changed-answer comparisons belong to the same diagnostic
        # panel even though their individual pressure pair is P↔P or H↔H.
        for c in comparisons:
            if c['story_id'] in story_ids and 'different_answer_same_pressure' in c['support_classes']:
                classes['different_answer_same_pressure']['truths'].add(c['recipient_truth'])
                classes['different_answer_same_pressure']['answers'].add(c['donor_answer_position'])
        required=('same_answer_changed_pressure','different_answer_same_pressure','fixed_answer_changed_truth')
        class_pass=all(len(classes[k]['truths'])==2 and len(classes[k]['answers'])==2 for k in required)
        per_split={s:sum(sid in story_ids and any(r['split']==s for r in by_story[sid]) for sid in story_ids) for s in split_counts}
        support[pair]={'crossed_story_ids':sorted(story_ids),'crossed_stories':len(story_ids),'by_split':per_split,'fixed_content_same_answer_stories':len(fixed),'fixed_content_story_ids':sorted(fixed),'strata_row_counts':dict(strata),'strata_story_counts_by_split':{k:{split:len(stories) for split,stories in splits.items()} for k,splits in strata_stories.items()},'required_class_coverage':{k:{a:sorted(v) for a,v in classes[k].items()} for k in required},'class_coverage_pass':class_pass}
        if pair!='P↔P′' and class_pass:qualified|=story_ids
    diagnostic_splits={s:sum(any(r['split']==s for r in by_story[sid]) for sid in qualified) for s in split_counts}
    semantic=bool(manifest.get('semantic_pass',False))
    numerical=bool(controls.get('self_patch_pass',False) and controls.get('mapping_pass',False))
    reasons=[]
    if sum(split_counts.values())<24 or min(split_counts.values(),default=0)<12:reasons.append('need >=24 groups and >=12 per split')
    if min(access.values(),default=0)<12:reasons.append('need >=12 H/N truthful-accessible stories per split')
    if len(qualified)<12 or min(diagnostic_splits.values(),default=0)<6:reasons.append('need pressure-presence crossed diagnostic on >=12 stories and >=6 per split with both truth/answer classes')
    if not semantic:reasons.append('semantic/token gate failed or not measured')
    if not numerical:reasons.append('same-path self/mapping gate failed or not measured')
    return dict(stage2_go=not reasons,stage2_scope='answer_content_diagnostic',pressure_mediation_identified=False,pressure_limit='deterministic native prompts lack fixed-content answer variation; changed designation donors confound pressure mediation',reasons=reasons,story_counts=split_counts,truth_accessible_stories=access,diagnostic_stories=len(qualified),diagnostic_by_split=diagnostic_splits,support=support,semantic_pass=semantic,numerical_pass=numerical,effect_size_gate=False)


DIAGNOSTIC_STRATA = ('recipient_condition', 'donor_condition', 'recipient_truth',
                     'truth_change', 'content_change', 'donor_matches_recipient_truth',
                     'donor_matches_recipient_emission', 'own_story', 'truth_accessible')


def summarize_by_story(rows, *, seed=SEED, bootstrap_reps=2000, planned_rows=()):
    """Net effects and prespecified directional cells, clustered by story."""
    import numpy as np
    grouped=defaultdict(list);diagnostics=defaultdict(lambda:defaultdict(list))
    proposed=defaultdict(Counter)
    def stratum(row):return tuple(row.get(key,'unknown') for key in DIAGNOSTIC_STRATA)
    def labels(row):return [f"{row['family']}/{row['scope']}/{split}" for split in (row['split'],'all')]
    for row in planned_rows:
        for label in labels(row):proposed[label][stratum(row)]+=1
    for row in rows:
        if row.get('status')!='completed' or 'effect' not in row:continue
        for label in labels(row):
            grouped[label].append(row);diagnostics[label][stratum(row)].append(row)
    def statistics(cell, label):
        stories=defaultdict(list)
        for row in cell:stories[row['story_id']].append(row['effect'])
        out={'n_rows':len(cell),'n_stories':len(stories),'mean':None,'ci95':None}
        if stories:
            values=np.array([np.mean(v) for k,v in sorted(stories.items())])
            rng=np.random.default_rng(int(digest([seed,label])[:16],16))
            bootstrap=values[rng.integers(0,len(values),size=(bootstrap_reps,len(values)))].mean(-1)
            out.update(mean=float(values.mean()),ci95=np.quantile(bootstrap,[.025,.975]).tolist())
        out['n_harms_accessible_truth']=sum(bool(r.get('harms_accessible_truth',False)) for r in cell)
        return out
    result={'bootstrap_reps':bootstrap_reps,'unit':'independent story group (row effects averaged within each diagnostic cell and story)', 'aggregate_label':'net effect across all diagnostic directions; opposite transfers can cancel','effects':{},'diagnostic_dimensions':list(DIAGNOSTIC_STRATA),'diagnostics':{},'row_status_counts':dict(Counter(r.get('status','unknown') for r in rows))}
    for label,cell in sorted(grouped.items()):result['effects'][label]=statistics(cell,label)
    for label in sorted(set(diagnostics)|set(proposed)):
        result['diagnostics'][label]=[]
        for key in sorted(set(diagnostics[label])|set(proposed[label]),key=lambda x:json.dumps(x)):
            cell=diagnostics[label].get(key,[])
            count=proposed[label].get(key,len(cell))
            stats=statistics(cell,[label,key])
            stats.update(stratum=dict(zip(DIAGNOSTIC_STRATA,key)),n_proposed=count,n_uncompleted=max(0,count-len(cell)),status='unsupported' if not cell else ('incomplete' if len(cell)<count else 'completed'))
            result['diagnostics'][label].append(stats)
    return result


def interleaved_batches(rows):
    """Round-robin homogeneous family/scope batches, before any inference."""
    groups=defaultdict(list)
    for row in rows:groups[(row['family'],row['scope'])].append(row)
    groups={key:sorted(cell,key=lambda r:r['comparison_id']) for key,cell in groups.items()}
    return [groups[key][start:start+8] for start in range(0,max((len(v) for v in groups.values()),default=0),8) for key in sorted(groups) if start<len(groups[key])]


def self_replacements(outputs, variants, device):
    from component_analysis import hooks
    import torch
    shape=next(iter(outputs.values())).shape[:2]
    positions=torch.zeros(shape,dtype=torch.bool,device=device)
    for index,variant in enumerate(variants):positions[index,:variant['length']]=True
    # Padding and dummy rows exist for physical shape only and are not patched.
    return {key:hooks.Replacement(value,positions.bool()) for key,value in outputs.items() if key!=hooks.READOUT_KEY}


def batch_inputs(variants, device):
    """Identical physical shape for every baseline, donor and patch forward."""
    import torch
    ids=torch.zeros((8,128),dtype=torch.long,device=device)
    mask=torch.zeros_like(ids)
    mask[len(variants):,0]=1  # harmless dummy rows, never scored or recorded
    for i,variant in enumerate(variants):
        ids[i,:variant['length']]=torch.tensor(variant['ids'],device=device)
        mask[i,:variant['length']]=1
    return ids,mask


def pad_replacements(values, masks):
    import torch
    joined=torch.cat(values)
    positions=torch.stack(masks)
    if len(values)<8:
        joined=torch.cat([joined,joined.new_zeros((8-len(values),128,joined.shape[-1]))])
        positions=torch.cat([positions,torch.zeros((8-len(values),128),dtype=torch.bool,device=positions.device)])
    return joined,positions


def parse_args(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-dir',default=str(ROOT/'data/datasets/sdr'))
    parser.add_argument('--output',required=True)
    parser.add_argument('--manifest')
    parser.add_argument('--model-cache',default=str(CACHE))
    parser.add_argument('--stage',choices=('stage1','stage2'),default='stage1')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--max-seconds',type=int,default=3300)
    parser.add_argument('--allocated-seconds',type=int,default=3600)
    parser.add_argument('--reserved-gpu-seconds',type=int,default=3600)
    parser.add_argument('--prior-reserved-gpu-seconds',type=int,default=0)
    parser.add_argument('--seed',type=int,default=SEED)
    args=parser.parse_args(argv)
    if not Path(args.output).is_absolute():parser.error('--output must be absolute')
    if not 60<=args.max_seconds<=3300:parser.error('--max-seconds must be60..3300')
    if args.max_seconds>args.allocated_seconds-60:parser.error('deadline must leave >=60s allocation safety margin')
    if args.allocated_seconds>3600 or args.allocated_seconds<120:parser.error('Stage1 allocation must be120..3600s')
    if args.prior_reserved_gpu_seconds+args.reserved_gpu_seconds>3600:parser.error('Stage1 reserved cap exceeded (failed reservations count)')
    if args.reserved_gpu_seconds<args.allocated_seconds:parser.error('reservation must cover allocation')
    return args


def run_stage1(args) -> dict:
    if args.stage!='stage1':raise ValueError('stage2 not implemented; independent reviewed viability checkpoint required')
    started=time.monotonic()
    deadline=started+args.max_seconds
    output=Path(args.output)
    output.mkdir(parents=True,exist_ok=True)
    os.environ['HF_HUB_OFFLINE']='1'
    os.environ['TRANSFORMERS_OFFLINE']='1'
    tokenizer=getattr(args,'tokenizer',None)
    if tokenizer is None:
        from transformers import AutoTokenizer
        cache=Path(args.model_cache)
        if not cache.is_absolute() or not (cache/'tokenizer.json').is_file():raise ValueError('absolute local cached tokenizer required')
        tokenizer=AutoTokenizer.from_pretrained(str(cache),local_files_only=True)
    if args.dry_run:
        manifest=build_manifest(args.dataset_dir,tokenizer,seed=args.seed)
        manifest['cpu_gate']={'schema_pass':True,'semantic_pass':manifest['semantic_pass'],'no_model_or_cuda':True,'deadline_seconds':args.max_seconds,'allocated_seconds':args.allocated_seconds,'grid':manifest['grid']}
        # Hash includes CPU gate and exact offline model location; immutable input
        # to a later GPU invocation. No model is loaded in this branch.
        manifest.pop('manifest_hash',None)
        manifest['model_cache']=args.model_cache
        manifest['manifest_hash']=digest(manifest)
        atomic_json(output/'manifest.json',manifest)
        gate=evaluate_gate(manifest,[],[],{})
        gate.update(status='cpu_dry_run',manifest_hash=manifest['manifest_hash'],baseline_complete=False)
        atomic_json(output/'gate.json',gate)
        write_jsonl(output/'baseline.jsonl',[]);write_jsonl(output/'comparisons.jsonl',[])
        atomic_json(output/'calibration.json',{'status':'not_run_cpu_only','model_load_seconds':None,'grid':manifest['grid']})
        atomic_json(output/'cost.json',{'status':'cpu_dry_run','reserved_gpu_seconds':0,'actual_gpu_seconds':0,'paid_api_calls':0})
        atomic_json(output/'story_bootstrap.json',summarize_by_story([]))
        (output/'summary.md').write_text('CPU manifest frozen. No model inference performed.\n\nStage2 stopped until measured behavioral and numerical gates pass.\n'+json.dumps(gate,indent=1)+'\n')
        return gate
    manifest_path=Path(args.manifest) if args.manifest else output/'manifest.json'
    if not manifest_path.is_file():raise ValueError('run --dry-run first; frozen manifest is required')
    manifest=json.loads(manifest_path.read_text())
    frozen_hash=manifest.pop('manifest_hash')
    if digest(manifest)!=frozen_hash:raise ValueError('manifest hash mismatch')
    manifest['manifest_hash']=frozen_hash
    if manifest.get('model_cache')!=args.model_cache:raise ValueError('model cache differs from frozen CPU manifest')
    if manifest.get('seed')!=args.seed:raise ValueError('seed differs from frozen manifest')
    for path,expected in {**manifest['sources'],**manifest.get('code_sha256',{}),**manifest.get('tokenizer_files',{})}.items():
        if file_hash(path)!=expected:raise ValueError('frozen source changed: '+path)
    if (output/'baseline.jsonl').exists() and (output/'baseline.jsonl').stat().st_size:
        raise ValueError('refuse overwriting existing attempted run; use a new run output with --manifest')
    atomic_json(output/'manifest.json',manifest)
    baselines=[];measurements=[];comparisons=[];captures={};baseline_vectors={};schedule=[]
    controls={'self_patch_pass':False,'mapping_pass':True,'receipts':[]}
    calibration={'status':'before_load','forwards':0,'batches':0,'batch_size':8,'model_load_seconds':None}
    cost={'internal_deadline_seconds':args.max_seconds,'job_id':os.environ.get('SLURM_JOB_ID'),'allocated_seconds':args.allocated_seconds,'gpu_count':1,'reserved_gpu_seconds':args.reserved_gpu_seconds,'prior_reserved_gpu_seconds':args.prior_reserved_gpu_seconds,'remaining_stage1_reserved_gpu_seconds':3600-args.prior_reserved_gpu_seconds-args.reserved_gpu_seconds,'remaining_pilot_reserved_gpu_seconds':7200-args.prior_reserved_gpu_seconds-args.reserved_gpu_seconds,'actual_gpu_seconds':0,'paid_api_calls':0}
    stop={'requested':False,'reason':None};status='initializing';baseline_complete=False
    previous_handlers={}
    def stop_signal(number,frame):
        stop.update(requested=True,reason='signal '+str(number))
    for number in (signal.SIGTERM,signal.SIGINT):
        previous_handlers[number]=signal.signal(number,stop_signal)
    def checkpoint():
        gate=evaluate_gate(manifest,baselines,comparisons,controls)
        gate.update(status=status,manifest_hash=frozen_hash,baseline_complete=baseline_complete,proposed_patch_rows=manifest['grid'].get('max_patch_rows',0),attempted_patch_rows=sum(r.get('status') in ('attempted','completed') for r in measurements),completed_patch_rows=sum(r.get('status')=='completed' for r in measurements),excluded_patch_rows=sum(r.get('status')=='excluded' for r in measurements),elapsed_seconds=time.monotonic()-started)
        if not baseline_complete:
            gate['stage2_go']=False
            gate['reasons'].append('baseline screen incomplete')
        cost['actual_gpu_seconds']=time.monotonic()-started
        cost['checkpoint_complete']=True
        atomic_json(output/'gate.json',gate)
        atomic_json(output/'calibration.json',calibration)
        atomic_json(output/'cost.json',cost)
        atomic_json(output/'numerical_controls.json',controls)
        summary=summarize_by_story(measurements,planned_rows=schedule)
        atomic_json(output/'story_bootstrap.json',summary)
        lines=['# SDR routing pilot Stage1','',f'Status: {status}. Stage2 gate: {gate["stage2_go"]}.', '', 'Estimand: answer/content donor diagnostic in the intact full-model background; all MLPs intact. Changed designation or cross-story content confounds pure pressure mediation. H adds an instruction; N deletes pressure. Prospective splits reuse the behaviorally filtered SDR test pool and are not independent out-of-distribution confirmation.', '', 'Exact all-token mapping is available only on identical token vectors; primary interventions are partial semantic positions. Unsupported/non-item donors and all attempted rows are retained. No effect-size selection or significance claim.', '', 'Gate/support tables: `gate.json`. Paired story-group bootstrap (2000 replicates): `story_bootstrap.json`.', '',f"Baseline variants {len(baselines)}/{len(manifest['panel'])}; completed patches {sum(r.get('status')=='completed' for r in measurements)}; attempted patches {sum(r.get('status') in ('attempted','completed') for r in measurements)}; excluded proposals {sum(r.get('status')=='excluded' for r in measurements)}; primary proposed rows {manifest['grid'].get('max_patch_rows',0)}. Missing cells remain unmeasured.", '', 'The net effects below pool reciprocal directions and can cancel. Direction, truth/content changes, actual donor-answer matches, own/cross-story controls and accessibility are preserved separately in `story_bootstrap.json` → `diagnostics`. Cells report proposed/completed rows, independent stories and story-clustered CIs; unsupported/incomplete cells remain explicit.', '', '| Family/scope/split (net) | Rows | Stories | Mean | 95% story CI |', '|---|---:|---:|---:|---|']+[f"| {label} | {cell['n_rows']} | {cell['n_stories']} | {cell['mean']:.5g} | {cell['ci95']} |" for label,cell in summary['effects'].items()]+['']
        (output/'summary.md').write_text('\n'.join(lines))
        return gate
    write_jsonl(output/'baseline.jsonl',[]);write_jsonl(output/'comparisons.jsonl',[])
    checkpoint()  # durable receipt even if cache load fails or allocation ends
    try:
        if not manifest['semantic_pass']:
            status='stopped_semantic_gate';return checkpoint()
        if len(manifest['valid_groups'])<24:
            status='stopped_insufficient_groups';return checkpoint()
        import torch
        from component_analysis import hooks
        cache=Path(args.model_cache)
        index=cache/'model.safetensors.index.json'
        if not index.is_file():raise ValueError('complete local model cache/index required')
        weight_files=set(json.loads(index.read_text())['weight_map'].values())
        if not all((cache/name).is_file() for name in weight_files):raise ValueError('local weight shards missing')
        if not torch.cuda.is_available() or torch.cuda.device_count()!=1 or 'H200' not in torch.cuda.get_device_name(0):
            raise ValueError('Stage1 requires exactly one allocated H200; no login-node inference')
        if not os.environ.get('SLURM_JOB_ID'):raise ValueError('Slurm allocation required')
        if time.monotonic()>=deadline:status='stopped_before_load_deadline';return checkpoint()
        loading=time.monotonic()
        model=hooks.load_analysis_model(str(cache),device='cuda')
        calibration['model_load_seconds']=time.monotonic()-loading
        calibration['cache_index_sha256']=file_hash(index)
        calibration['weights']={name:(cache/name).stat().st_size for name in sorted(weight_files)}
        device,dtype=hooks.device_and_dtype(model)
        families={name:[('head',l,h) for l,h in heads] for name,heads in manifest['grid']['families'].items()}
        keys=sorted({k for v in families.values() for k in v})+[hooks.READOUT_KEY]
        excluded_stories={e['story_id'] for e in manifest['exclusions']}
        panel=[v for v in manifest['panel'] if v['valid'] and v['story_id'] not in excluded_stories];by_id={v['variant_id']:v for v in panel}
        def forward(variants,replacements=None,components=None):
            ids,mask=batch_inputs(variants,device)
            result=hooks.capture_forward(model,ids,mask,components=keys if components is None else components,replacements=replacements)
            torch.cuda.synchronize()
            calibration['forwards']+=1;calibration['batches']+=1
            return result
        controls['self_patch_pass']=True
        baseline_start=time.monotonic();first8={g['story_id'] for g in manifest['groups'][:8]}
        first8_measured=False
        status='baseline_screen'
        for start in range(0,len(panel),8):
            if stop['requested'] or time.monotonic()>=min(deadline-30,started+1750):
                status='stopped_baseline_deadline';break
            variants=panel[start:start+8]
            result=forward(variants)
            scored=score_capture(model,result,[v['truth_id'] for v in variants],[v['other_id'] for v in variants])
            self_values=self_replacements(result.outputs,variants,device)
            self_result=forward(variants,replacements=self_values,components=[hooks.READOUT_KEY])
            receipt=numerical_receipt(scored['logits'],capture_logits(model,self_result))
            receipt['variant_ids']=[v['variant_id'] for v in variants]
            controls['receipts'].append(receipt)
            controls['self_patch_pass'] &= receipt['pass']
            if start==0:
                empty=forward(variants,replacements={},components=[hooks.READOUT_KEY])
                empty_receipt=numerical_receipt(scored['logits'],capture_logits(model,empty))
                empty_receipt['control']='empty/repeat'
                controls['receipts'].append(empty_receipt);controls['self_patch_pass'] &= empty_receipt['pass']
            with (output/'baseline.jsonl').open('a') as f:
                for i,(v,metrics) in enumerate(zip(variants,scored['rows'])):
                    row={k:value for k,value in v.items() if k not in ('ids','segments','anchors','prompt')}
                    row.update(metrics,accessible=metrics['emitted_id']==v['truth_id'],semantic_audit={'valid':v['valid'],'errors':v['errors'],'anchors':v['anchors']},emitted_class=next((name for name,token in v['item_ids'].items() if token==metrics['emitted_id']),'other'))
                    baselines.append(row);f.write(json.dumps(row)+'\n')
                    baseline_vectors[v['variant_id']]=scored['logits'][i].detach().cpu()
                    captures[v['variant_id']]={k:value[i:i+1,:v['length']].detach().cpu() for k,value in result.outputs.items() if k!=hooks.READOUT_KEY}
                f.flush()
            if not first8_measured and first8<={r['story_id'] for r in baselines}:
                elapsed=time.monotonic()-baseline_start
                calibration.update(status='eight_story_calibration_complete',eight_stories=8,eight_story_variants=len(baselines),eight_story_seconds=elapsed,seconds_per_forward=elapsed/(calibration['forwards']),peak_memory_bytes=torch.cuda.max_memory_allocated(),estimated_baseline_total_seconds=elapsed*len(panel)/len(baselines))
                calibration['eight_story_variants_per_second']=len(baselines)/elapsed
                calibration['eight_story_forwards']=calibration['forwards']
                first8_measured=True
            comparisons=build_comparisons(manifest,baselines)
            checkpoint()
            if not controls['self_patch_pass']:
                status='stopped_numerical_gate';return checkpoint()
            del result,self_result,scored
        baseline_complete=len(baselines)==len(panel)
        comparisons=build_comparisons(manifest,baselines)
        write_jsonl(output/'comparisons.jsonl',comparisons)
        if baseline_complete:status='baseline_checkpoint'
        gate=checkpoint()
        if not gate['stage2_go']:
            status='completed_no_support' if baseline_complete else status
            return checkpoint()
        baseline_by_id={r['variant_id']:r for r in baselines}
        schedule=[]
        candidates={c['comparison_id']:c for c in comparisons}
        for proposal in manifest['patch_plan']:
            cid=str(proposal['recipient_id'])+'|'+str(proposal['donor_id'])
            comparison=candidates.get(cid,{'comparison_id':cid,**proposal,'status':'excluded','reason':proposal['exclusion'] or 'frozen donor baseline unavailable'})
            for scope in PRIMARY_SCOPES:
                mapping=manifest['maps'].get(cid,{}).get(scope,[])
                for family in families:
                    schedule.append({**comparison,**proposal,'family':family,'scope':scope,'dose':1.,'alignment':'semantic_partial','map_hash':digest(mapping),'mapping':mapping,'status':'pending'})
        calibration['actual_planned_patch_rows']=len(schedule)
        calibration['estimated_patch_seconds']=len(schedule)/8*calibration.get('seconds_per_forward',float('inf'))
        calibration['projected_grid_exceeds_remaining']=calibration['estimated_patch_seconds']>deadline-time.monotonic()-30
        # Deterministic family/scope interleaving keeps incomplete grids visible;
        # no outcome-dependent priority. Batches can have different lengths/maps.
        batches=interleaved_batches(schedule)
        status='family_patches';checkpoint()
        with (output/'comparisons.jsonl').open('a') as f:
            for start,batch in enumerate(batches):
                if stop['requested'] or time.monotonic()>=deadline-30:
                    status='completed_partial_deadline';break
                variants=[by_id.get(c['recipient_id']) for c in batch]
                # Homogeneous family/scope chunks avoid writing unrequested
                # heads on rows at a boundary; process boundaries separately.
                groups=defaultdict(list)
                for row,v in zip(batch,variants):groups[row['family']].append((row,v))
                for family,entries in groups.items():
                    valid=[(row,v) for row,v in entries if row['mapping'] and v is not None and not row['exclusion']]
                    for row,v in entries:
                        if not row['mapping'] or v is None or row['exclusion']:
                            row.update(status='excluded',reason=row['exclusion'] or 'no valid mapped positions');measurements.append({k:v for k,v in row.items() if k!='mapping'});f.write(json.dumps(measurements[-1])+'\n')
                    if not valid:continue
                    variants=[v for row,v in valid];length=128
                    replacements={}
                    for key in families[family]:
                        values=[];masks=[]
                        for row,v in valid:
                            value,mask=remap_capture(captures[row['donor_id']][key],row['mapping'],length)
                            values.append(value);masks.append(mask)
                        joined,mask_values=pad_replacements(values,masks)
                        replacements[key]=hooks.Replacement(joined.to(device),mask_values.to(device))
                    attempted=[]
                    for row,v in valid:
                        row['status']='attempted';attempted.append({k:value for k,value in row.items() if k!='mapping'});measurements.append(attempted[-1])
                        f.write(json.dumps(attempted[-1])+'\n')
                    f.flush()
                    result=forward(variants,replacements=replacements,components=[hooks.READOUT_KEY])
                    scored=score_capture(model,result,[v['truth_id'] for v in variants],[v['other_id'] for v in variants],[row['donor_emitted_id'] for row,v in valid])
                    for index,((row,v),metrics) in enumerate(zip(valid,scored['rows'])):
                        base=baseline_by_id[row['recipient_id']]
                        empty_receipt=None
                        if family=='empty':
                            empty_receipt=numerical_receipt(baseline_vectors[row['recipient_id']],scored['logits'][index].cpu())
                            controls['self_patch_pass'] &= empty_receipt['pass']
                            controls['receipts'].append({'control':'empty_family','comparison_id':row['comparison_id'],**empty_receipt})
                        row.update(control_answer_match=row.get('recipient_emitted_class')==row.get('donor_emitted_class') and row.get('donor_emitted_class')!='other',status='completed',baseline={k:base[k] for k in ('truth_margin','p_truth','p_other','other_mass','emitted_id')},patched=metrics,effect=metrics['truth_margin']-base['truth_margin'],truth_accessible=base['accessible'],harms_accessible_truth=base['accessible'] and metrics['emitted_id']!=v['truth_id'],no_op_receipt=empty_receipt or {'same_path_global_pass':controls['self_patch_pass']})
                        attempted[index].update({k:value for k,value in row.items() if k!='mapping'})
                        f.write(json.dumps(attempted[index])+'\n')
                    f.flush();del result,scored
                    if not controls['self_patch_pass']:
                        status='stopped_numerical_gate';return checkpoint()
                if start%64==0:checkpoint()
            else:status='completed'
        calibration['peak_memory_bytes']=torch.cuda.max_memory_allocated()
        calibration['remaining_unmeasured_patch_rows']=len(schedule)-len(measurements)
        return checkpoint()
    except Exception as error:
        status='failed'
        calibration['error']=type(error).__name__+': '+str(error)
        checkpoint()
        raise
    finally:
        for number,handler in previous_handlers.items():signal.signal(number,handler)


if __name__=='__main__':
    args=parse_args()
    result=run_stage1(args)
    print(json.dumps({k:result[k] for k in ('status','stage2_go','stage2_scope','reasons')},indent=1))
