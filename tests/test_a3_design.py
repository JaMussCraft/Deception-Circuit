"""CPU-only A3 design contracts, using injected parents and byte tokenizers."""
import copy
import json
import pytest
from component_analysis import a3_design as d
from component_analysis.ladder_design import _hash


def parents():
    tasks=['far_v2','sdr_v2','ser_v2']; rows={}; designs={}; groups={}; matched={}
    for task in tasks:
        ids={s:[f'{task}:{s}:{i}' for i in range(n)] for s,n in [('train',51),('validation',31),('test',100)]}
        rows[task]={c:[dict(instance_id=i,split=s,condition=c,pressure_text='pressure',streams={
            k:dict(prompt='abc',tokens=[97,98,99],readout=2,layout={'role_spans':[['text',0,3]],'content_spans':[['text',0,3]]}) for k in ('clean','corrupt')}) for s in ids for i in ids[s]] for c in ('D','H','F','I','user_neutral')}
        designs[task]=dict(assessment_ids=ids['test'],mover_selection_ids=[task+':old'],selection_exclusion_ids=[t+':old' for t in tasks],donors=[])
        groups[task]={'full':[['head',7,16],['mlp',6,0]]}
        matched[task]=dict(split_ids=ids,actual_split_ids={k:copy.deepcopy(ids) for k in ('D','I')})
    p=dict(kind='prepared',tasks=tasks,rows=rows,designs=designs,utility={'ioi':[],'mmlu':[]},source_hashes={},selection_hashes={},tokenizer_identity={'sha':'t'},tokenizer_revision='t',grader_sha256='g',commit='a'*40,model='m',model_revision='r',code_hashes={},injected=True)
    s=dict(kind='selected',design_sha256=_hash(p),groups=groups,banks={},execution_provenance={k:p[k] for k in ('commit','model','model_revision','tokenizer_revision')})
    s.update(group_sha256=_hash(groups),bank_sha256=_hash({}))
    m=dict(cohort='matched',fleet_ready=True,tasks=matched,parent_fingerprints={k:p[k] for k in ('source_hashes','tokenizer_identity','grader_sha256')})
    h=dict(rows=[{'task':t[:-3],'category':'kv_clause','label':'head.7.16'} for t in tasks],source_hashes={'csv':'c'},selection_completion={'selection_artifact_sha256':_hash(s),'design_sha256':_hash(p)})
    return p,s,m,h


def freeze(values=None):
    return d.freeze_a3(*(values or parents()),root_ruling=d.ROOT_RULING_V1)


def test_preserves_ids_sites_and_gqa():
    values=parents(); result=freeze(values)
    assert result['tasks']['far_v2']['assessment_ids']==values[0]['designs']['far_v2']['assessment_ids']
    assert result['tasks']['far_v2']['direction_sites']==[['head',7,16]]+[['head',17,i] for i in range(24,28)]
    assert result['tasks']['far_v2']['kv_receivers']==[['k',7,4],['k',17,6],['v',7,4],['v',17,6]]
    assert result['seeds']==[42,1,123]


@pytest.mark.parametrize('fault',['missing','collision','exclusion','source','tokenizer','grader','duplicate','minimum','membership','completion','ruling'])
def test_fail_closed(fault):
    p,s,m,h=parents(); ruling=copy.deepcopy(d.ROOT_RULING_V1)
    if fault=='missing': s={}
    if fault=='collision': p['rows']['far_v2']['I'][0]['split']='test'
    if fault=='exclusion': p['designs']['far_v2']['selection_exclusion_ids']=[]
    if fault in ('source','tokenizer','grader'): m['parent_fingerprints'][{'source':'source_hashes','tokenizer':'tokenizer_identity','grader':'grader_sha256'}[fault]]='changed'
    if fault=='duplicate': p['rows']['far_v2']['D'].append(p['rows']['far_v2']['D'][0])
    if fault=='minimum': m['tasks']['far_v2']['split_ids']['train']=m['tasks']['far_v2']['split_ids']['train'][:49]
    if fault=='membership': m['tasks']['far_v2']['actual_split_ids']['D']['train'].pop()
    if fault=='completion': h.pop('selection_completion')
    if fault=='ruling': ruling['seeds']=[42]
    # Refresh pure parent digests to exercise downstream checks rather than hash rejection.
    if s:
        s['design_sha256']=_hash(p)
        if 'selection_completion' in h: h['selection_completion'].update(selection_artifact_sha256=_hash(s),design_sha256=_hash(p))
    with pytest.raises(ValueError): d.freeze_a3(p,s,m,h,root_ruling=ruling)


class Bytes:
    def encode(self,text,add_special_tokens=False): return list(text.encode())


def test_semantic_boundaries_and_ambiguity():
    row={'prompt':'abc request xyz','condition':'I','tokens':list(b'abc request xyz'),'semantic_char_spans':{'pressure_request':[4,11]}}
    result=d.semantic_sites(row,Bytes())
    assert result['pressure_request']==list(range(4,11))
    assert result['assistant_readout']==[14]
    row['semantic_char_spans']['pressure_request']=[4,99]
    assert d.semantic_sites(row,Bytes())['pressure_request']==[]
    class Merges:
        def encode(self,text,add_special_tokens=False): return [1] if text=='abc' else list(text.encode())
    row={'prompt':'abc','semantic_char_spans':{'question':[0,2]}}
    assert d.semantic_sites(row,Merges())['question']==[]


def test_utility_prompt_overlap_even_with_different_ids():
    fixed=[{'instance_id':'old','source_id':'old','streams':{'clean':{'prompt':'same'},'corrupt':{'prompt':'donor'}}}]
    candidates=[{'instance_id':'new','source_id':'new','streams':{'clean':{'prompt':'other'},'corrupt':{'prompt':'donor'}}}]
    assert d.eligible_ioi(candidates,fixed,n=1)==[]


def test_registry_refresh_and_source_ids(tmp_path):
    design=freeze(); path=tmp_path/'held_out.json'; path.write_text(json.dumps({'schema':1,'sets':[]}))
    assert d.validate_access(design,[str(path)])
    rid=design['tasks']['far_v2']['fit_ids'][0]
    path.write_text(json.dumps({'schema':1,'sets':[{'task':'far_v2','instance_ids':[rid]}]}))
    with pytest.raises(ValueError,match='overlap'): d.validate_access(design,[str(path)])
    path.write_text(json.dumps({'schema':1,'sets':[{'path':'missing','sha256':'no','n':1}]}))
    with pytest.raises(ValueError): d.validate_access(design,[str(path)])


def test_semantic_source_enrichment_and_donor_protection(tmp_path):
    p,s,m,h=parents()
    h['source_rows']=copy.deepcopy(p['rows'])
    for values in h['source_rows']['far_v2'].values():
        for row in values: row['pressure_text']='canonical actual source pressure'
    p['designs']['far_v2']['donors']=[{'donor_id':'private-donor'}]
    s['design_sha256']=_hash(p); h['selection_completion'].update(design_sha256=_hash(p),selection_artifact_sha256=_hash(s))
    result=freeze((p,s,m,h))
    assert 'canonical actual source pressure' in result['tasks']['far_v2']['pressure_cluster_counts']['fit']
    path=tmp_path/'held_out.json'; path.write_text(json.dumps({'schema':1,'sets':[{'task':'far_v2','instance_ids':['private-donor']}]}))
    with pytest.raises(ValueError,match='overlap'): d.validate_access(result,[str(path)])


def test_enrichment_cannot_change_frozen_prompt():
    p,s,m,h=parents(); h['source_rows']=copy.deepcopy(p['rows'])
    h['source_rows']['far_v2']['D'][0]['streams']['clean']['prompt']='changed'
    with pytest.raises(ValueError,match='enrich'): freeze((p,s,m,h))


def test_ioi_requires_unique_prompts_not_just_pair_signature():
    rows=[dict(instance_id=str(i),source_id=str(i),streams={'clean':{'prompt':'shared'},'corrupt':{'prompt':str(i)}}) for i in range(2)]
    assert len(d.eligible_ioi(rows,[],n=2))==1


def test_builder_clause_api_retains_leading_space_bpe_token():
    import re
    class SpaceBPE:
        def __init__(self): self.vocab={}
        def encode(self,text,add_special_tokens=False):
            pieces=re.findall(r' [a-z]+|.',text)
            for piece in pieces: self.vocab.setdefault(piece,len(self.vocab))
            return [self.vocab[piece] for piece in pieces]
    tokenizer=SpaceBPE(); prompt='prefix clause<|eot_id|>'
    row=dict(prompt=prompt,condition='D',pressure='clause')
    positions=d.semantic_sites(row,tokenizer)['pressure_request']
    assert len(positions)==1
    assert tokenizer.encode(prompt)[positions[0]]==tokenizer.vocab[' clause']


def test_item_designation_uses_own_builder_pair():
    class Words:
        def encode(self,text,add_special_tokens=False): return [sum(map(ord,w)) for w in text.split()]
    source=dict(clean_prompt='start a end',corrupt_prompt='start b end',clean_item_d='a',corrupt_item_d='b')
    row=dict(prompt=source['corrupt_prompt'],stream='corrupt',designation_source=source)
    assert d.semantic_sites(row,Words())['item_designation']==[1]
    row['designation_source']['corrupt_prompt']='extra start b end'
    assert d.semantic_sites(row,Words())['item_designation']==[]


def test_question_uses_existing_segmenter_frame_without_item_mentions():
    from tests.test_segmentation import sdr_record
    from tests.fakes import FakeWordTokenizer
    from component_analysis.segmentation import resolve_segmentation
    tokenizer=FakeWordTokenizer(); raw=sdr_record()
    row=dict(prompt=raw['clean_prompt'],task='sdr',semantic_source=raw)
    positions=d.semantic_sites(row,tokenizer)['question']
    seg=resolve_segmentation('sdr',raw,tokenizer)
    assert positions==seg.segments['question'].token_indices() and positions
    for name,part in seg.segments.items():
        if '_question_' in name: assert not set(positions)&set(part.token_indices())


def test_cluster_bootstrap_policy_is_frozen_without_row_truncation():
    policy=freeze()['cluster_bootstrap_policy']
    assert policy['unit']=='canonical source D pressure text'
    assert policy['draw_count']=='number of eligible wording clusters C'
    assert policy['weights']=='cluster multiplicity per member ID, normalized to sum 1'
    assert policy['row_truncation'] is False and policy['instance_fallback'] is False
