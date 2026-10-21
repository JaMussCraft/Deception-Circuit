#!/usr/bin/env python
"""Separate exploratory forced-prefix completions. Original path gate stays failed.

CPU freeze/dry-run, operator-owned Slurm calibration/main, then offline blinded
annotation exports/join. Never retries, resumes, selects survivors, or calls generate.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import importlib.metadata
import json
import math
import os
from pathlib import Path
import random
import re
import signal
import sys
import time

CODE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_ROOT))
sys.path.insert(0, str(CODE_ROOT/'scripts'))
from sdr_routing_validation import (CACHE, digest, file_hash, atomic_json,
    write_jsonl, score_capture, capture_logits, validation_batch,
    verify_validation_manifest, validation_gpu_identity, baseline_provenance)

PARENT = CODE_ROOT/'outputs/_analyses/sdr-routing-validation/baseline-cda2160-20261021T133612Z'
NAMESPACE = CODE_ROOT/'outputs/_analyses/sdr-completion-diagnostic'
PARENT_HASH = 'ee1e5e279e5f7880a90f9e42ab663ee2da17acd8f02ef77dd7b4bb825ed632dc'
EXPECTED_GPU = {'class':'A100', 'name':'NVIDIA A100-SXM4-40GB',
    'compute_capability':[8,0], 'total_memory_bytes':42405855232, 'count':1}
EOS = [128001,128008,128009]
IDENTITIES = ('candidateA','candidateB','none','multiple','unresolved')
KINDS = ('unambiguous_answer','ambiguous/qualified','refusal','contradictory','bad/uninterpretable')
FORMATS = ('exact-single-item','prefix-or-quote-then-item','expanded-answer','other/bad')
RUBRIC = {
    'version':'completion-diagnostic-v1',
    'identity':list(IDENTITIES), 'response_kind':list(KINDS), 'format':list(FORMATS),
    'instructions':[
        'Label identity independently of truth; candidateA/B index the displayed sorted options.',
        'Read the complete original assistant stem and continuation. Do not infer hidden context.',
        'One affirmative unqualified named candidate resolves identity. No substring, pronoun or fuzzy inference.',
        'Negation, qualification, conditional claims, conflicting assertions or uncertain quotation require manual judgment.',
        'Missing candidate is not refusal. Refusal requires explicit declining language.',
        'Separate semantic identity, response kind and output format. A prefix or clear quote need not be wrong.',
        'Cap, error, interruption and missing output remain unresolved for the primary endpoint, regardless of provisional identity.',
        'Label every unique view including apparently clear parser cases; never see parser suggestions or another annotator labels.',
        'Third blinded adjudicator labels disagreements without seeing other labels. Irreducible disagreement stays ambiguous.',
    ],
    'examples':[
        {'text':'The unit is listed as copper.','finish':'eos','identity':'copper','kind':'unambiguous_answer','format':'prefix-or-quote-then-item'},
        {'text':'The unit is not copper.','finish':'eos','identity':'unresolved','kind':'ambiguous/qualified'},
        {'text':'The unit is copper, actually silver.','finish':'eos','identity':'multiple','kind':'contradictory'},
        {'text':'The unit is "copper".','finish':'eos','identity':'copper','format':'prefix-or-quote-then-item'},
        {'text':'The unit is unavailable; I cannot answer.','finish':'eos','identity':'none','kind':'refusal'},
        {'text':'The unit is copper','finish':'max_new_tokens','identity':'unresolved'},
    ],
    'annotation_recipe':{'annotators':2,'model_family':'internal Sol','all_unique_views':True,
        'dedup':['exact assistant_text','sorted candidate pair','exact stop_reason'],
        'selection':'all main rows, no outcome filtering','calibration':'excluded entirely',
        'paid_api_calls':0,'missing_capacity':'retain unresolved; record provenance/missingness'},
    'limitations':['Forced-prefix, post-hoc descriptive diagnostic; no gate rescue or path/statistical claim.',
        'Output wording may unavoidably reveal context; hide all metadata and report this leakage.',
        'Compositional fresh fixtures and historically exposed native cases; no broad competency or intent inference.'],
}


class DiagnosticStop(RuntimeError):
    """Fail closed, retaining receipts and incomplete rows."""


class FirstSteps(list):
    def __init__(self, rows=(), *, runtime=None):
        super().__init__(rows)
        self.runtime = runtime if runtime is not None else {}


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def check_prefixes(panel):
    for v in panel:
        if not 0 < v['length'] <= 115 or len(v['ids']) != v['length']:
            raise ValueError('original prefix must be <=115 tokens, without truncation')
        if v['length'] + 32 >= 192:
            raise ValueError('prefix plus32 must fit strictly below192')


def read_eos(cache):
    configs = [Path(cache)/n for n in ('config.json','generation_config.json')]
    sets=[]
    for p in configs:
        ids=json.loads(p.read_text())['eos_token_id']
        sets.append({ids} if isinstance(ids,int) else set(ids))
    if sets[0] != sets[1] or sorted(sets[0] | sets[1]) != EOS:
        raise ValueError('cached EOS configs must agree on all three frozen endings')
    return sorted(sets[0] | sets[1]), {str(p):file_hash(p) for p in configs}


def software_identity():
    return {name:importlib.metadata.version(name) for name in ('torch','transformers','nnsight','datasets')}


def build_completion_manifest(parent_dir: Path, tokenizer, *, seed: int = 20261021) -> dict:
    parent_dir=Path(parent_dir).resolve()
    parent=json.loads((parent_dir/'manifest.json').read_text())
    if parent.get('manifest_hash') != PARENT_HASH:
        raise ValueError('wrong frozen parent manifest')
    verify_validation_manifest(parent,check_files=False)
    # CPU audits may run in either supported environment; inference additionally
    # requires verify_validation_manifest(check_files=True), including versions.
    for category in ('sources','code_sha256','tokenizer_files','model_files'):
        for path,expected in parent[category].items():
            if file_hash(path) != expected:raise ValueError('frozen dependency changed: '+path)
    gate=json.loads((parent_dir/'validity-gate.json').read_text())
    baselines=read_jsonl(parent_dir/'baseline.jsonl')
    controls=read_jsonl(parent_dir/'numerical.jsonl')
    provenance=json.loads((parent_dir/'baseline-provenance.json').read_text())
    if not controls or not all(c.get('pass') for c in controls):
        raise ValueError('parent numerical controls did not pass')
    if gate.get('paths_go') is not False or not gate.get('baseline_complete'):
        raise ValueError('diagnostic entry requires complete parent and failed original gate')
    if provenance['gpu_identity'] != EXPECTED_GPU:
        raise ValueError('unexpected actual parent hardware identity')
    first8={g['story_id'] for g in parent['groups'][:8]}
    indices={g['story_id']:i for i,g in enumerate(parent['groups'])}
    panel=sorted(parent['panel'],key=lambda v:(v['story_id'] not in first8,indices[v['story_id']],v['variant_id']))
    if len(baselines)!=1280 or len({v['variant_id'] for v in baselines})!=1280:
        raise ValueError('need all1280 unique parent baselines')
    if [v['variant_id'] for v in panel] != [v['variant_id'] for v in baselines]:
        raise ValueError('parent baseline order differs from reconstruction')
    if not all(b['status']=='completed' and b.get('fp32_checksum') for b in baselines):
        raise ValueError('incomplete parent baseline receipts')
    check_prefixes(panel)
    if Path(tokenizer.name_or_path).resolve()!=CACHE.resolve():raise ValueError('tokenizer cache differs')
    for v in panel:
        if digest(v['prompt'])!=v['prompt_hash'] or tokenizer.encode(v['prompt'],add_special_tokens=False)!=v['ids']:
            raise ValueError('prompt bytes/token vector changed: '+v['variant_id'])
    eos,configs=read_eos(CACHE)
    names=('manifest.json','baseline.jsonl','validity-gate.json','baseline-provenance.json','numerical.jsonl')
    manifest={
        'schema':'completion-diagnostic','seed':seed,'parent_dir':str(parent_dir),
        'parent_manifest_hash':PARENT_HASH,'parent_files':{str(parent_dir/n):file_hash(parent_dir/n) for n in names},
        'parent_gate':gate,'parent_numeric_pass':True,'parent_provenance':provenance,
        'paths_go':False,'original_task2':'STOPPED, not implemented/not run; capability gate failed',
        'panel':panel,'parent_baselines':baselines,'ordered_ids':[v['variant_id'] for v in panel],
        'prefix_payload_hash':digest([{k:v[k] for k in ('variant_id','prompt','prompt_hash','ids','length')} for v in panel]),
        'physical_shape':[8,192],'pad_id':0,'max_new_tokens':32,'eos_ids':eos,
        'config_files':configs,'model_cache':str(CACHE),'model_files':parent['model_files'],
        'tokenizer_files':parent['tokenizer_files'],'software':parent['software'],
        'dtype':'bfloat16','attention':'sdpa','scoring':parent['scoring'],
        'cache_override':{'runtime_only':True,'use_cache':False,'reference_checksum_required':True},
        'decoding':{'greedy':'full vocabulary fp32 argmax','cache':False,'skip_special_tokens':True,
            'cleanup':False,'first_forward':'all components + READOUT','later_forward':'READOUT only'},
        'required_gpu':EXPECTED_GPU,'calibration_ids':[v['variant_id'] for v in panel[:64]],
        'calibration_excluded_from_main':True,'calibration_batches':8,
        'rubric':RUBRIC,'rubric_hash':digest(RUBRIC),
        'annotation_recipe_hash':digest(RUBRIC['annotation_recipe']),
        'budget':{'calibration_reserved_seconds_max':600,'main_reserved_seconds_max':3000,
            'initial_total_reserved_seconds_max':3600,'overall_reserved_seconds_max':14400,
            'generation_forwards_main_max':5120,'main_replay_forwards':160,
            'main_continuation_forwards_max':4960,'generated_tokens_main_max':40960,
            'calibration_replay_forwards':160,'calibration_continuation_forwards_max':248,
            'calibration_controls_extra_forwards':0,'shutdown_buffer_seconds':90,
            'forecast_safety_multiplier':1.25,'paid_api_calls':0},
        'lead_compactions':2,'output_namespace':str(NAMESPACE),
        'new_code_sha256':{str(p):file_hash(p) for p in (Path(__file__).resolve(),CODE_ROOT/'scripts/sdr_completion_diagnostic.sbatch')},
    }
    manifest['manifest_hash']=digest(manifest)
    return manifest


def verify_completion_manifest(manifest):
    if digest({k:v for k,v in manifest.items() if k not in ('manifest_hash','_runtime','_private_join')})!=manifest['manifest_hash']:
        raise ValueError('completion manifest mutated')
    if manifest['rubric_hash']!=digest(RUBRIC) or manifest['rubric']!=RUBRIC:
        raise ValueError('rubric changed after freeze')
    for category in ('parent_files','config_files','model_files','tokenizer_files','new_code_sha256'):
        for path,expected in manifest[category].items():
            if file_hash(path)!=expected:raise ValueError('frozen file changed: '+path)
    check_prefixes(manifest['panel'])


def check_running(runtime):
    if runtime.get('signal') or time.monotonic()>=runtime.get('deadline',float('inf')):
        raise DiagnosticStop('interrupted by signal or allocation deadline')


def forward(model,ids,mask,components,runtime):
    from component_analysis import hooks
    check_running(runtime)
    runtime['forwards']=runtime.get('forwards',0)+1
    return hooks.capture_forward(model,ids,mask,components=components)


def replay_first_steps(model, manifest: dict) -> list[dict]:
    from component_analysis import hooks
    runtime=manifest.setdefault('_runtime',{})
    runtime['firststep_gate_pass']=False
    runtime['firststep_receipts']=[]
    receipts=FirstSteps(runtime['firststep_receipts'],runtime=runtime)
    # Share the same list with checkpoint, including the failing batch.
    runtime['firststep_receipts']=receipts
    device,_=hooks.device_and_dtype(model)
    expected={v['variant_id']:v for v in manifest['parent_baselines']}
    for offset in range(0,len(manifest['panel']),8):
        variants=manifest['panel'][offset:offset+8]
        ids,mask=validation_batch(variants,device)
        capture=forward(model,ids,mask,hooks.all_component_keys(model)+[hooks.READOUT_KEY],runtime)
        scored=score_capture(model,capture,[v['truth_id'] for v in variants],[v['other_id'] for v in variants])
        for v,row in zip(variants,scored['rows']):
            baseline=expected[v['variant_id']]
            receipts.append({'variant_id':v['variant_id'],'expected_checksum':baseline['fp32_checksum'],
                'fp32_checksum':row['fp32_checksum'],'expected_emitted_id':baseline['emitted_id'],
                'emitted_id':row['emitted_id'],'passed':row['fp32_checksum']==baseline['fp32_checksum'],
                'readout_position':v['length']-1,'eos_ids':manifest.get('eos_ids',EOS)})
        del capture,scored
        if runtime.get('checkpoint'):runtime['checkpoint']()
        if not all(r['passed'] for r in receipts[-len(variants):]):
            raise DiagnosticStop('first-step full-vocabulary checksum mismatch; no continuation permitted')
    runtime['firststep_gate_pass']=True
    return receipts


def assistant_stem(v):
    marker='<|start_header_id|>assistant<|end_header_id|>\n\n'
    return v['prompt'].rsplit(marker,1)[-1]


def greedy_complete_batch(model, variants: list[dict], first_steps: list[dict], *, max_new_tokens: int = 32) -> list[dict]:
    from component_analysis import hooks
    import torch
    if not 1<=max_new_tokens<=32:raise ValueError('generation cap must be1..32')
    check_prefixes(variants)
    if len(variants)!=len(first_steps) or any(v['variant_id']!=r['variant_id'] or not r['passed'] for v,r in zip(variants,first_steps)):
        raise DiagnosticStop('missing/mismatched first-step checksum receipt')
    runtime=getattr(first_steps,'runtime',{})
    if runtime and not runtime.get('firststep_gate_pass'):
        raise DiagnosticStop('all first-step checksums required before continuation')
    device,_=hooks.device_and_dtype(model)
    ids,mask=validation_batch(variants,device)
    lengths=[v['length'] for v in variants]
    eos=set(first_steps[0].get('eos_ids',EOS))
    rows=[{'variant_id':v['variant_id'],'prompt_hash':v.get('prompt_hash'),
        'generated_ids':[],'readout_positions':[],'firststep_checksum':s['fp32_checksum'],
        'stop_reason':'interrupted','terminal_eos_id':None,'attempted':True,
        'status':'running','run_kind':runtime.get('run_kind','main')} for v,s in zip(variants,first_steps)]
    runtime['active_rows']=rows
    try:
        for step in range(max_new_tokens):
            check_running(runtime)
            active=[i for i,row in enumerate(rows) if row['status']=='running']
            if not active:break
            if step==0:
                selected={i:first_steps[i]['emitted_id'] for i in active}
            else:
                captured=forward(model,ids,mask,[hooks.READOUT_KEY],runtime)
                logits=capture_logits(model,captured).float()
                selected={i:int(logits[i].argmax()) for i in active}
                del captured,logits
            for i in active:
                token=selected[i];row=rows[i]
                row['readout_positions'].append(lengths[i]-1)
                row['generated_ids'].append(token)
                if lengths[i]>=192:raise DiagnosticStop('physical capacity exceeded; no truncation')
                ids[i,lengths[i]]=token;mask[i,lengths[i]]=1;lengths[i]+=1
                if token in eos:
                    row.update(stop_reason='eos',terminal_eos_id=token,status='completed')
                elif step+1==max_new_tokens:
                    row.update(stop_reason='max_new_tokens',status='capped')
        return rows
    except BaseException as exc:
        for row in rows:
            if row['status']=='running':
                row.update(status='interrupted' if isinstance(exc,DiagnosticStop) else 'error',
                    stop_reason='interrupted' if isinstance(exc,DiagnosticStop) else 'error',error=str(exc))
        raise
    finally:
        for row in rows:row['generated_count']=len(row['generated_ids'])


def propose_literal_identity(text: str, candidates: tuple[str,str], stop_reason: str) -> dict:
    folded=text.casefold()
    hits=[i for i,c in enumerate(candidates) if re.search(r'(?<!\w)'+re.escape(c.casefold())+r'(?!\w)',folded)]
    uncertain=bool(re.search(r'\b(not|no|never|neither|nor|isn.t|wasn.t|cannot|can.t|won.t|refuse|decline|if|unless|perhaps|maybe|actually|however|but|either|might|could|would|should|possibly|probably|allegedly)\b|\?',folded))
    clean=text.strip().strip('.').strip('"\'').casefold()
    fmt='exact-single-item' if clean in [c.casefold() for c in candidates] else (
        'prefix-or-quote-then-item' if folded.startswith('the unit is') or '"' in text else 'expanded-answer')
    quoted=any(q in text for q in ('\"', '\u201c', '\u201d', '\u2018', '\u2019'))
    clear_quote=bool(re.fullmatch(r'(?i)the unit is (?:listed as )?[\"\u201c]?(?:'+
        '|'.join(re.escape(c) for c in candidates)+r')[\"\u201d]?[.!]?',text.strip()))
    manual=stop_reason!='eos' or len(hits)!=1 or uncertain or (quoted and not clear_quote)
    return {'answer_identity':'unresolved' if manual else IDENTITIES[hits[0]],
        'response_kind':'ambiguous/qualified' if manual else 'unambiguous_answer',
        'format':fmt,'manual_required':manual,'proposal_only':True}


def blind_label_rows(generations: list[dict], manifest: dict) -> list[dict]:
    if any(g.get('run_kind')!='main' for g in generations):
        raise ValueError('calibration rows are excluded from annotation')
    by={v['variant_id']:v for v in manifest['panel']}
    if len(generations)!=len(by) or len({g['variant_id'] for g in generations})!=len(by):
        raise ValueError('blinding requires every planned main row exactly once')
    # Private permutation is independent of factors/outcomes; opaque IDs do not
    # encode source IDs, truth, factors or response hashes.
    unique={};joins=[]
    for g in generations:
        v=by[g['variant_id']];candidates=sorted(v['items'])
        key=(g.get('assistant_text',''),tuple(candidates),g['stop_reason'])
        if key not in unique:unique[key]=len(unique)
        joins.append({**v,**g,'view_index':unique[key],'candidates':candidates})
    rng=random.Random(manifest['seed']);permutation=list(range(len(unique)));rng.shuffle(permutation)
    opaque={index:f'view-{rank:06d}' for rank,index in enumerate(permutation)}
    views=[{'opaque_id':opaque[index],'assistant_text':key[0],'candidates':list(key[1]),'stop_reason':key[2]} for key,index in unique.items()]
    rng.shuffle(views)
    for row in joins:
        row['opaque_id']=opaque[row.pop('view_index')]
    manifest['_private_join']=joins
    return views


def validated_labels(labels):
    result={}
    for row in labels:
        if row['opaque_id'] in result:raise ValueError('duplicate annotation')
        if row.get('answer_identity') not in IDENTITIES or row.get('response_kind') not in KINDS or row.get('format') not in FORMATS:
            raise ValueError('invalid annotation schema')
        result[row['opaque_id']]=row
    return result


def label_tuple(row):
    return tuple(row[k] for k in ('answer_identity','response_kind','format'))


def join_labels(label_a, label_b, adjudication, private_join) -> list[dict]:
    a,b,c=map(validated_labels,(label_a,label_b,adjudication))
    views={r['opaque_id'] for r in private_join}
    if (a.keys()|b.keys()|c.keys())-views:raise ValueError('annotation references unknown view')
    rows=[]
    for original in private_join:
        row=dict(original);key=row['opaque_id'];la=a.get(key);lb=b.get(key)
        label=None;status='missing_independent_label'
        if la and lb:
            if label_tuple(la)==label_tuple(lb):label=la;status='independent_agreement'
            elif key in c:
                # A blind third label resolving to one independent label can
                # decide a disagreement; a third distinct label stays ambiguous.
                if label_tuple(c[key]) in (label_tuple(la),label_tuple(lb)):
                    label=c[key];status='blind_adjudication'
                else:status='irreducible_disagreement'
            else:status='disagreement'
        if label:
            row.update({k:label[k] for k in ('answer_identity','response_kind','format')})
        else:row.update(answer_identity='unresolved',response_kind='ambiguous/qualified',format='other/bad')
        row['annotation_status']=status
        if row['stop_reason']!='eos' or status=='missing_independent_label':semantic='bad/unresolved'
        elif not label:semantic='ambiguous'
        elif row['response_kind']=='refusal':semantic='refusal'
        elif row['response_kind']=='contradictory':semantic='contradictory'
        elif row['response_kind']=='bad/uninterpretable':semantic='bad/unresolved'
        elif row['response_kind']!='unambiguous_answer' or row['answer_identity'] not in ('candidateA','candidateB'):semantic='ambiguous'
        else:
            candidate=row['candidates'][0 if row['answer_identity']=='candidateA' else 1]
            semantic='correct' if candidate==row['truthful_item'] else 'wrong'
        row['semantic_result']=semantic
        rows.append(row)
    return rows


def summarize_completions(rows: list[dict], parent_baselines: list[dict]) -> dict:
    if len(rows)!=1280 or len({r['variant_id'] for r in rows})!=1280:
        raise ValueError('summary retains all1280 denominator')
    baseline={b['variant_id']:b for b in parent_baselines}
    if set(baseline)!={r['variant_id'] for r in rows}:raise ValueError('baseline join differs')
    def counts(group):
        return {'denominator':len(group),**{k:dict(Counter(r.get(k,'missing') for r in group))
            for k in ('semantic_result','answer_identity','response_kind','format','stop_reason','annotation_status','status')},
            'attempted':sum(bool(r.get('attempted')) for r in group)}
    dimensions=('population','template','task','truth','stakes','favored','split','pressure','order')
    groups=defaultdict(list);marginal=defaultdict(list)
    for r in rows:
        values={k:r.get('factors',{}).get(k,r.get(k,'not-applicable')) for k in dimensions}
        groups[json.dumps(values,sort_keys=True)].append(r)
        for key,value in values.items():marginal[key+'='+str(value)].append(r)
    old_nonitem=[r for r in rows if baseline[r['variant_id']]['emitted_class']=='non_item']
    return {'schema':'completion-diagnostic-summary','denominator':1280,'all':counts(rows),
        'original_nonitem_descriptive':counts(old_nonitem),
        'all_factor_cells':{k:counts(v) for k,v in sorted(groups.items())},
        'marginals':{k:counts(v) for k,v in sorted(marginal.items())},
        'paths_go':False,'original_gate':'FAILED; original Task2 remains stopped',
        'calibration_included':False,'limitations':RUBRIC['limitations']}


def assert_gpu(identity):
    if identity!=EXPECTED_GPU:
        raise ValueError('actual GPU name/capability/memory/count differ from parent A100')


def new_output(path):
    path=Path(path).resolve()
    if NAMESPACE.resolve() not in path.parents:
        raise ValueError('new outputs must live in separate completion namespace')
    if path.exists():raise ValueError('refuse overwriting an existing diagnostic run')
    path.mkdir(parents=True,exist_ok=False,mode=0o700)
    return path


def planned_rows(manifest,kind):
    return [{'variant_id':v['variant_id'],'prompt_hash':v['prompt_hash'],
        'generated_ids':[],'generated_count':0,'readout_positions':[],
        'assistant_text':assistant_stem(v),'continuation_text':'','stop_reason':'not_attempted',
        'terminal_eos_id':None,'attempted':False,'status':'planned','run_kind':kind}
        for v in manifest['panel']]


def forecast_main(measured):
    # 160 original all-component replays plus at most31*160 READOUT forwards.
    # Never extrapolate the calibration mean completion length or select rows.
    replay_rate=measured['replay_seconds']/measured['replay_forwards']
    continuation_count=measured['continuation_forwards']
    continuation_rate=(measured['continuation_seconds']/continuation_count
        if continuation_count else replay_rate)
    rate=max(replay_rate,continuation_rate)
    components={'audit_seconds':measured['audit_seconds'],
        'model_load_seconds':measured['model_load_seconds'],
        'replay_seconds':160*replay_rate,'continuation_seconds':4960*rate,
        'io_seconds':20*measured['checkpoint_seconds']}
    estimate=1.25*sum(components.values())+90
    return {'forecast_seconds':estimate,'fits_3000':estimate<=3000,
        'components':components,'generation_forwards_bound':5120,
        'replay_forwards_bound':160,'continuation_forwards_bound':4960,
        'generated_tokens_bound':40960,'safety_multiplier':1.25,
        'shutdown_buffer_seconds':90,'continuation_rate_seconds':rate,
        'basis':'measured same-path fixed8x192 fullcap bound; no mean-length extrapolation'}


def decode_rows(rows,variants,tokenizer):
    for row,v in zip(rows,variants):
        row['continuation_text']=tokenizer.decode(row['generated_ids'],skip_special_tokens=True,clean_up_tokenization_spaces=False)
        row['raw_continuation_text']=tokenizer.decode(row['generated_ids'],skip_special_tokens=False,clean_up_tokenization_spaces=False)
        row['assistant_text']=assistant_stem(v)+row['continuation_text']
        row['generated_count']=len(row['generated_ids'])


def write_report(path,summary,cost):
    all_counts=summary['all']
    text=(
        '# Separate exploratory completion diagnostic\n\n'
        'Original confirmatory capability gate FAILED; original Task2 remains STOPPED, '
        'not implemented/not run. No completion result can authorize paths or repair that gate.\n\n'
        f"All-row denominator:1280. Attempted:{all_counts['attempted']}. "
        f"Finish reasons:{json.dumps(all_counts['stop_reason'],sort_keys=True)}.\n\n"
        f"Joined semantic outcomes:{json.dumps(all_counts['semantic_result'],sort_keys=True)}.\n\n"
        f"Output format:{json.dumps(all_counts['format'],sort_keys=True)}.\n\n"
        'The original non-item subgroup is post-hoc descriptive. See summary.json for '
        'all original-factor/native/fresh/split cells, missing annotations, errors and caps. '
        'All rows retain their original weight after exact deduplication. '
        'Calibration rows are excluded entirely. Output wording may reveal context despite hidden metadata. '
        'These forced-prefix responses do not establish spontaneous refusal, intent, broad competency, '
        'mediation or causal path effects.\n\n'
        f"Cost receipt:{json.dumps(cost,sort_keys=True)}\n")
    Path(path).write_text(text)


def export_blinded(output,rows,manifest):
    views=blind_label_rows(rows,manifest)
    join=manifest.pop('_private_join')
    private=output/'private';private.mkdir(mode=0o700)
    write_jsonl(private/'join.jsonl',join)
    proposals=[{'variant_id':g['variant_id'],**propose_literal_identity(g['assistant_text'],
        tuple(sorted(v['items'])),g['stop_reason'])} for g,v in zip(rows,manifest['panel'])]
    write_jsonl(private/'parser-proposals.jsonl',proposals)
    inputs_hash=digest(views)
    labeling={'schema':'completion-diagnostic-labeling','manifest_hash':manifest['manifest_hash'],
        'rubric_hash':manifest['rubric_hash'],'inputs_hash':inputs_hash,
        'dedup_recipe_hash':manifest['annotation_recipe_hash'],'view_count':len(views),
        'original_row_count':len(rows),'private_join_hash':digest(join),
        'calibration_included':False,'all_unique_including_parser_clear_cases':True,
        'independent_annotator_model_family':'internal Sol','paid_api_calls':0,
        'unavoidable_leakage':'Output wording may reveal context; metadata withheld.',
        'required_provenance':['annotator_id','model_family','blind','inputs_hash','rubric_hash',
            'completed_at','capacity_note','labels']}
    atomic_json(output/'labeling-manifest.json',labeling)
    for name in ('label-a','label-b'):
        directory=output/name;directory.mkdir(mode=0o700)
        write_jsonl(directory/'blinded-inputs.jsonl',views)
        atomic_json(directory/'label-rubric.json',manifest['rubric'])
        atomic_json(directory/'assignment.json',{
            'assignment':name,'inputs_hash':inputs_hash,'rubric_hash':manifest['rubric_hash'],
            'view_count':len(views),'required_model_family':'internal Sol',
            'instructions':'Read only this directory. Label ALL views independently. Do not inspect sibling labels, private data or parser proposals. Return provenance and labels JSON.',
            'answer_identity':'candidateA/B refer to sorted displayed candidates at index0/1',
            'provenance_schema':labeling['required_provenance']})
    # No regex-only correctness: unavailable independent labels stay unresolved.
    joined=join_labels([],[],[],join)
    summary=summarize_completions(joined,manifest['parent_baselines'])
    write_jsonl(output/'joined-unresolved.jsonl',joined)
    atomic_json(output/'summary-unresolved.json',summary)
    return views


def validate_annotation_payload(payload,views,rubric_hash):
    for key in ('annotator_id','model_family','blind','inputs_hash','rubric_hash','completed_at','capacity_note','labels'):
        if key not in payload:raise ValueError('annotation provenance missing '+key)
    if not payload['annotator_id'] or payload['model_family']!='internal Sol' or payload['blind'] is not True:
        raise ValueError('annotation must be an identified independent internal Sol blind pass')
    if payload['inputs_hash']!=digest(views) or payload['rubric_hash']!=rubric_hash:
        raise ValueError('annotation payload bound to different blinded inputs/rubric')
    labels=validated_labels(payload['labels'])
    if labels.keys()-{v['opaque_id'] for v in views}:raise ValueError('unknown annotation ID')
    return payload['labels']


def run_annotations(args):
    source=Path(args.run_dir).resolve()
    if NAMESPACE.resolve() not in source.parents:raise ValueError('annotation requires diagnostic run namespace')
    manifest=json.loads((source/'manifest.json').read_text());verify_completion_manifest(manifest)
    labeling=json.loads((source/'labeling-manifest.json').read_text())
    views=read_jsonl(source/'label-a/blinded-inputs.jsonl')
    join=read_jsonl(source/'private/join.jsonl')
    if digest(views)!=labeling['inputs_hash'] or digest(join)!=labeling['private_join_hash']:
        raise ValueError('frozen blinding/join files mutated')
    if labeling['manifest_hash']!=manifest['manifest_hash'] or labeling['original_row_count']!=1280:
        raise ValueError('labeling manifest bound to different experiment')
    output=new_output(args.output)
    os.chmod(output,0o700)
    supplied={};labels={}
    for key,path in (('a',args.label_a),('b',args.label_b)):
        if path:
            supplied[key]=json.loads(Path(path).read_text())
            labels[key]=validate_annotation_payload(supplied[key],views,manifest['rubric_hash'])
        else:labels[key]=[]
    if len(supplied)==2 and supplied['a']['annotator_id']==supplied['b']['annotator_id']:
        raise ValueError('two independent annotators must have distinct identities')
    a,b=map(validated_labels,(labels['a'],labels['b']))
    disagreements=[v for v in views if v['opaque_id'] in a and v['opaque_id'] in b and label_tuple(a[v['opaque_id']])!=label_tuple(b[v['opaque_id']])]
    third=output/'adjudicator';third.mkdir(mode=0o700)
    write_jsonl(third/'blinded-inputs.jsonl',disagreements)
    atomic_json(third/'label-rubric.json',manifest['rubric'])
    atomic_json(third/'assignment.json',{'inputs_hash':digest(disagreements),'rubric_hash':manifest['rubric_hash'],
        'instructions':'Third independent internal Sol blind pass. Label only these disagreement views without seeing any earlier labels, proposals or private join.',
        'view_count':len(disagreements)})
    adjudication=[]
    if args.adjudication:
        supplied['adjudication']=json.loads(Path(args.adjudication).read_text())
        adjudication=validate_annotation_payload(supplied['adjudication'],disagreements,manifest['rubric_hash'])
        if supplied['adjudication']['annotator_id'] in {p['annotator_id'] for k,p in supplied.items() if k!='adjudication'}:
            raise ValueError('adjudicator must be a third independent annotator')
    for key,payload in supplied.items():atomic_json(output/('label-'+key+'.json'),payload)
    joined=join_labels(labels['a'],labels['b'],adjudication,join)
    summary=summarize_completions(joined,manifest['parent_baselines'])
    summary['annotation_capacity']={key:{'supplied':key in supplied,'expected_views':len(views),
        'received_labels':len(labels[key]),'missing_views':len(views)-len(labels[key])} for key in ('a','b')}
    summary['annotation_capacity']['adjudication']={'expected_views':len(disagreements),'received_labels':len(adjudication)}
    write_jsonl(output/'joined.jsonl',joined)
    atomic_json(output/'summary.json',summary)
    atomic_json(output/'source.json',{'run_dir':str(source),'manifest_hash':manifest['manifest_hash'],
        'labeling_manifest_hash':file_hash(source/'labeling-manifest.json'),
        'input_annotation_files':{str(Path(p).resolve()):file_hash(p) for p in (args.label_a,args.label_b,args.adjudication) if p}})
    write_report(output/'report.md',summary,json.loads((source/'cost.json').read_text()))
    return {'status':'annotations_joined','denominator':1280,'output':str(output),'paths_go':False}


def validate_budget(args):
    bound=600 if args.stage=='calibration' else 3000
    if (not 120<=args.allocation_seconds<=bound or args.prior_reserved_gpu_seconds<0
            or args.prior_reserved_gpu_seconds+args.allocation_seconds>14400
            or args.initial_reserved_gpu_seconds is None
            or args.initial_reserved_gpu_seconds<0
            or args.initial_reserved_gpu_seconds+args.allocation_seconds>3600):
        raise ValueError('operator reservation bounds invalid, including failed initial attempts')
    if not 1<=args.max_seconds<=args.allocation_seconds-60:
        raise ValueError('internal deadline invalid')


def run_diagnostic(args):
    started=time.monotonic()
    output=new_output(args.output);os.chmod(output,0o700)
    kind=args.stage
    cost={'schema':'completion-diagnostic-cost','run_kind':kind,'status':'initializing',
        'reserved_gpu_seconds':0 if args.dry_run else args.allocation_seconds,
        'prior_reserved_gpu_seconds':args.prior_reserved_gpu_seconds,
        'initial_reserved_gpu_seconds':args.initial_reserved_gpu_seconds,'actual_gpu_seconds':0,
        'paid_api_calls':0,'job_id':os.environ.get('SLURM_JOB_ID'),'gpu_identity':None,
        'basis':'single actual A100 reserved allocation seconds, including failed attempts; no refunds/retries',
        'lead_compactions':2}
    atomic_json(output/'cost.json',cost)
    state={'forwards':0,'firststep_receipts':[],'firststep_gate_pass':False,
        'run_kind':kind,'signal':None,'active_rows':[]}
    measured={'status':'not_started','run_kind':kind,'main_inferential_inclusion':False}
    rows=[];manifest=None;tokenizer=None;old_handlers={};error=None
    def checkpoint():
        tick=time.monotonic()
        if tokenizer is not None and state['active_rows']:
            active=state['active_rows'];by={v['variant_id']:v for v in manifest['panel']}
            decode_rows(active,[by[r['variant_id']] for r in active],tokenizer)
            index={r['variant_id']:i for i,r in enumerate(rows)}
            for row in active:rows[index[row['variant_id']]]=dict(row)
        cost.update(actual_gpu_seconds=0 if args.dry_run else time.monotonic()-started,
            forwards=state['forwards'],firststep_checks=len(state['firststep_receipts']),
            firststep_gate_pass=state['firststep_gate_pass'],signal=state['signal'])
        atomic_json(output/'cost.json',cost)
        write_jsonl(output/'firststep-receipts.jsonl',state['firststep_receipts'])
        write_jsonl(output/'generations.jsonl',rows)
        atomic_json(output/'calibration.json',measured)
        state['checkpoint_seconds']=state.get('checkpoint_seconds',0)+time.monotonic()-tick
    state['checkpoint']=checkpoint
    def stop(number,frame):state['signal']=number
    try:
        if kind not in ('calibration','main'):raise ValueError('unknown inference stage')
        os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
        from transformers import AutoTokenizer
        tokenizer=AutoTokenizer.from_pretrained(str(CACHE),local_files_only=True)
        if args.manifest:
            manifest=json.loads(Path(args.manifest).read_text());verify_completion_manifest(manifest)
            if Path(args.parent).resolve()!=Path(manifest['parent_dir']):raise ValueError('parent argument differs from freeze')
        elif args.dry_run:
            manifest=build_completion_manifest(Path(args.parent),tokenizer)
        else:raise ValueError('reviewed frozen manifest required before GPU')
        rows=planned_rows(manifest,kind)
        atomic_json(output/'manifest.json',manifest)
        atomic_json(output/'label-rubric.json',manifest['rubric'])
        atomic_json(output/'annotation-plan.json',manifest['rubric']['annotation_recipe'])
        if args.dry_run:
            cost.update(status='cpu_dry_run',software=software_identity())
            measured.update(status='cpu_only',planned_rows=1280,calibration_rows=64,excluded_from_main=True)
            checkpoint()
            (output/'report.md').write_text('CPU-only manifest/prompt/source/rubric audit. No inference or labels. Original gate FAILED; Task2 stays stopped.\n')
            return cost
        validate_budget(args)
        if not os.environ.get('SLURM_JOB_ID'):raise ValueError('Slurm required; no login inference')
        remaining=int(os.environ.get('SLURM_JOB_END_TIME','0'))-time.time()
        if remaining<120 or remaining>args.allocation_seconds:raise ValueError('actual allocation deadline mismatch')
        state['deadline']=min(started+args.max_seconds,time.monotonic()+remaining-90)
        for number in (signal.SIGTERM,signal.SIGINT):old_handlers[number]=signal.signal(number,stop)
        if kind=='main':
            if not args.calibration_receipt:raise ValueError('measured reviewed calibration receipt required')
            receipt_path=Path(args.calibration_receipt).resolve()
            if NAMESPACE.resolve() not in receipt_path.parents:raise ValueError('calibration receipt outside diagnostic namespace')
            receipt=json.loads(receipt_path.read_text())
            if receipt.get('status')!='calibration_complete' or receipt.get('manifest_hash')!=manifest['manifest_hash'] or receipt.get('rubric_hash')!=manifest['rubric_hash']:
                raise ValueError('calibration incomplete or different frozen protocol')
            recalculated=forecast_main(receipt)
            if receipt.get('forecast')!=recalculated or not recalculated['fits_3000'] or recalculated['forecast_seconds']>args.allocation_seconds:
                raise DiagnosticStop('measured full-cap forecast plus buffer cannot fit main allocation')
            if receipt.get('firststep_checks')!=1280 or not receipt.get('firststep_gate_pass'):
                raise DiagnosticStop('calibration did not pass all1280 checksums')
            cost['calibration_receipt_sha256']=file_hash(receipt_path)
        parent=json.loads((Path(manifest['parent_dir'])/'manifest.json').read_text())
        verify_validation_manifest(parent,check_files=True)
        import torch
        from component_analysis import hooks
        identity=validation_gpu_identity(torch.cuda);assert_gpu(identity)
        cost['gpu_identity']=identity;cost['software']=software_identity()
        atomic_json(output/'hardware-provenance.json',{'parent':manifest['parent_provenance'],
            'current':baseline_provenance(parent,identity),'exact_parent_device_match':True})
        checkpoint()
        index=json.loads((CACHE/'model.safetensors.index.json').read_text())['weight_map']
        if not all((CACHE/n).is_file() for n in set(index.values())):raise ValueError('local model shards missing')
        measured['audit_seconds']=time.monotonic()-started
        check_running(state);loading=time.monotonic()
        model=hooks.load_analysis_model(str(CACHE),device='cuda')
        torch.cuda.synchronize();measured['model_load_seconds']=time.monotonic()-loading
        device,dtype=hooks.device_and_dtype(model)
        if device.type!='cuda' or dtype!=torch.bfloat16 or hooks.attention_implementation(model)!='sdpa' or hooks._hf(model).training:
            raise ValueError('model must be eval BF16 CUDA SDPA')
        old_cache=hooks._hf(model).config.use_cache
        hooks._hf(model).config.use_cache=False
        atomic_json(output/'runtime-cache-override.json',{'old_use_cache':old_cache,'new_use_cache':False,
            'runtime_only':True,'reference_checksum_still_required':True})
        manifest['_runtime']=state
        replay_start=time.monotonic()
        first=replay_first_steps(model,manifest)
        torch.cuda.synchronize()
        measured.update(replay_seconds=time.monotonic()-replay_start,replay_forwards=state['forwards'],
            firststep_checks=len(first),firststep_gate_pass=state['firststep_gate_pass'])
        if len(first)!=1280 or not state['firststep_gate_pass']:raise DiagnosticStop('all1280 firststeps required')
        cost['status']=kind+'_generating';checkpoint()
        generation_start=time.monotonic();forwards_before=state['forwards']
        stop_index=64 if kind=='calibration' else 1280
        for offset in range(0,stop_index,8):
            check_running(state)
            batch=manifest['panel'][offset:offset+8]
            selected=FirstSteps(first[offset:offset+8],runtime=state)
            greedy_complete_batch(model,batch,selected)
            torch.cuda.synchronize();checkpoint()
            if state['forwards']> (408 if kind=='calibration' else 5120):
                raise DiagnosticStop('frozen physical forward ceiling exceeded')
        measured.update(continuation_seconds=time.monotonic()-generation_start,
            continuation_forwards=state['forwards']-forwards_before,
            checkpoint_seconds=state.get('checkpoint_seconds',0),
            manifest_hash=manifest['manifest_hash'],rubric_hash=manifest['rubric_hash'])
        if kind=='calibration':
            measured.update(status='calibration_complete',excluded_from_main=True,
                calibration_ids=manifest['calibration_ids'],calibration_rows=64)
            measured['forecast']=forecast_main(measured)
        else:
            if sum(r['generated_count'] for r in rows)>40960:raise DiagnosticStop('token bound exceeded')
            export_blinded(output,rows,manifest)
            measured.update(status='main_complete',calibration_included=False)
        cost['status']=kind+'_complete';checkpoint()
        if kind=='main':
            summary=json.loads((output/'summary-unresolved.json').read_text())
            write_report(output/'report.md',summary,cost)
        else:
            (output/'report.md').write_text('Calibration-only timing, excluded from main inference and labeling.\n'+json.dumps(measured,sort_keys=True)+'\n')
        return cost
    except BaseException as exc:
        error=exc
        cost.update(status='stopped' if isinstance(exc,DiagnosticStop) else 'failed',error=type(exc).__name__+': '+str(exc))
        measured.update(status=cost['status'],error=cost['error'])
        # Completed EOS/capped rows stay recorded; attempted but unfinished rows
        # preserve partial token trajectories, without selected reruns.
        for row in state['active_rows']:
            if row['status']=='running':row.update(status='interrupted',stop_reason='interrupted',error=str(exc))
        checkpoint()
        (output/'report.md').write_text('Incomplete separate diagnostic. Original gate FAILED; no rescue.\n'+cost['error']+'\n')
        raise
    finally:
        for number,handler in old_handlers.items():signal.signal(number,handler)
        if manifest is not None:
            changed=[p for p,h in manifest['parent_files'].items() if file_hash(p)!=h]
            if changed:
                atomic_json(output/'parent-immutability-failure.json',{'changed':changed})
                if error is None:raise DiagnosticStop('parent artifact bytes changed')


def parse_args(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=('calibration','main','annotate'),default='calibration')
    parser.add_argument('--parent',default=str(PARENT))
    parser.add_argument('--output',required=True)
    parser.add_argument('--manifest')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--calibration-receipt')
    parser.add_argument('--allocation-seconds',type=int,default=0)
    parser.add_argument('--prior-reserved-gpu-seconds',type=int,default=0)
    parser.add_argument('--max-seconds',type=int,default=0)
    parser.add_argument('--initial-reserved-gpu-seconds',type=int)
    parser.add_argument('--run-dir')
    parser.add_argument('--label-a');parser.add_argument('--label-b');parser.add_argument('--adjudication')
    args=parser.parse_args(argv)
    if args.stage=='annotate' and not args.run_dir:parser.error('annotate requires --run-dir')
    return args


if __name__=='__main__':
    args=parse_args()
    print(json.dumps(run_annotations(args) if args.stage=='annotate' else run_diagnostic(args),sort_keys=True))
