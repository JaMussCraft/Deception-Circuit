"""Historical cache algorithm is reused byte-for-byte, tiny weights only."""
import hashlib
import json
from pathlib import Path

import pytest
from test_full_score_release import module

ACCEPTED_CACHE_SHA='55d6517228832e0254c10086d03d3b5e3534ad91bf8ddbe54d96e9913fa3fa06'


def fixture(c,tmp_path):
    hub=tmp_path/'hub';cache=hub/c.MODEL_REPO;snapshot=cache/'snapshots'/c.REVISION
    (cache/'refs').mkdir(parents=True);snapshot.mkdir(parents=True)
    (cache/'refs/main').write_text(c.REVISION+'\n');metadata=[]
    for name in ['config.json','generation_config.json','model.safetensors.index.json',
                 'tokenizer.json','tokenizer_config.json','special_tokens_map.json']:
        p=snapshot/name;p.write_text('{}')
        metadata.append(dict(name=name,nbytes=2,sha256=c.file_sha(p)))
    blob=cache/'blobs'/('f'*64);blob.parent.mkdir();blob.write_bytes(b'tiny fake weight')
    weight=snapshot/'model-00001-of-00001.safetensors';weight.symlink_to(blob)
    ref=tmp_path/'reference.json';ref.write_text(json.dumps(dict(remote_cache=str(cache),
        revision=c.REVISION,metadata=metadata,weights=[dict(name=weight.name,nbytes=blob.stat().st_size,
                                                         expected_sha256=blob.name)])))
    proof=tmp_path/'full-proof.json';proof.write_text(json.dumps(dict(reference_sha256=c.file_sha(ref))))
    pins=dict(reference_sha256=c.file_sha(ref),full_proof_sha256=c.file_sha(proof))
    return ref,proof,hub,snapshot,weight,pins


def test_cache_algorithm_exact_accepted_reference_bytes():
    c=module('cache_gate')
    assert hashlib.sha256(Path(c.__file__).read_bytes()).hexdigest()==ACCEPTED_CACHE_SHA


def test_metadata_hashed_every_weight_sized_and_blob_bound_no_full_rehash(tmp_path,monkeypatch):
    c=module('cache_gate');ref,proof,hub,snapshot,weight,pins=fixture(c,tmp_path)
    original=proof.read_bytes();actual=c.file_sha;seen=[]
    def observed(path):seen.append(Path(path).resolve());return actual(path)
    monkeypatch.setattr(c,'file_sha',observed)
    result=c.check_cache(ref,proof,hub,**pins)
    assert len(result['metadata'])==6 and len(result['weights'])==1
    assert result['full_weights_rehashed'] is False and result['model_loaded'] is False
    assert weight.resolve() not in seen
    assert set((snapshot/n).resolve() for n in [r['name'] for r in result['metadata']])<=set(seen)
    assert proof.read_bytes()==original


@pytest.mark.parametrize('fault',['metadata-hash','metadata-size','weight-size','blob-name',
                                  'refs-main','physical-bind','reference','proof','revision'])
def test_cache_changes_fail_without_download_or_original_proof_rewrite(tmp_path,fault):
    c=module('cache_gate');ref,proof,hub,snapshot,weight,pins=fixture(c,tmp_path)
    c.check_cache(ref,proof,hub,**pins)
    if fault=='metadata-hash':(snapshot/'tokenizer.json').write_text('[]')
    elif fault=='metadata-size':(snapshot/'tokenizer.json').write_text('{ }')
    elif fault=='weight-size':weight.resolve().write_bytes(b'wrong')
    elif fault=='blob-name':
        old=weight.resolve();other=old.with_name('e'*64);other.write_bytes(old.read_bytes())
        weight.unlink();weight.symlink_to(other)
    elif fault=='refs-main':(snapshot.parent.parent/'refs/main').write_text('other')
    elif fault=='physical-bind':hub=hub/'other'
    elif fault=='reference':ref.write_text(ref.read_text()+' ')
    elif fault=='proof':proof.write_text(proof.read_text()+' ')
    elif fault=='revision':
        value=json.loads(ref.read_text());value['revision']='other';ref.write_text(json.dumps(value))
        pins['reference_sha256']=c.file_sha(ref)
        proof.write_text(json.dumps(dict(reference_sha256=pins['reference_sha256'])))
        pins['full_proof_sha256']=c.file_sha(proof)
    before=proof.read_bytes()
    with pytest.raises(AssertionError):c.check_cache(ref,proof,hub,**pins)
    assert proof.read_bytes()==before
