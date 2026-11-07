import copy,json,os,pickle,shutil
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from component_analysis import a3_direction_runtime as r
from tests.test_a3_direction_runner import fake, measured_setup, batch
from tests.test_a3_direction_runtime import _indexed_proof_case,_fake_pilot_inputs


def test_index_mismatches_do_no_io_and_dependencies_refresh_once(tmp_path,monkeypatch):
    _,paths,m=_indexed_proof_case(tmp_path)
    backing=tmp_path/'common';backing.mkdir();np.save(backing/'axis.npy',np.eye(2,dtype=np.float32));r.artifacts._finish(backing)
    proofs=[]
    for i,path in enumerate(paths):
        payload=r.read_object(path);payload['numeric_backing_references']={str(backing):r.pipeline._bundle_byte_reference(backing)}
        new=tmp_path/f'evidence-{i}';r.publish_object(new,payload);proofs.append(r._CompletedPackingProof(new))
    index=r._PackingCandidateIndex(proofs);io=[];live=[];old=r._file_tree_identity
    monkeypatch.setattr(r,'_file_tree_identity',lambda path:io.append(str(path)) or old(path))
    for _ in range(20):assert index.candidates(m['profile'],m['axis_scope'])==[proofs[-1]]
    assert io==[]
    guard=r._DependencyGuard(lambda:live.append(1),index);guard();guard()
    assert guard.calls==len(live)==2 and len(io)==8 and io.count(str(backing))==2
    for value in [index,index.forest,*proofs]:
        with pytest.raises(TypeError):del value._sealed
        with pytest.raises(TypeError):pickle.dumps(value)
    payload=proofs[0].path+'/payload.json';raw=Path(payload).read_bytes();Path(payload).write_bytes(raw+b' ')
    assert index.candidates(m['profile'],m['axis_scope'])==[proofs[-1]]
    with pytest.raises(ValueError):guard()
    assert len(live)==2


@pytest.mark.parametrize('damage',['target','runtime','attestation','backing'])
def test_context_validates_exact_scope_and_rechecks_after_operation(tmp_path,fake,damage):
    from dataclasses import replace
    ident,capture,axes,cells=measured_setup(fake);receipt=ident.pop('packed_equivalence')
    path=tmp_path/'measured';r.publish_object(path,dict(injected=True,evidence=r.packing_evidence(receipt,[batch()]),measurement=dict(profile=ident['numeric_profile'],timing_inputs=[],axis_scope=[])))
    proof=r._CompletedPackingProof(path);b=replace(batch(),ids=['ta','tb']);reuse=tmp_path/'reuse'
    r.freeze_profile_reuse(reuse,measured_path=path,batch=b,cells=[cells[1]],axes=axes,capture_index=capture,policy=r.workload.PROFILE_REUSE_POLICY,validated_proof=proof)
    identity=dict(ident,profile_reuse=str(reuse));context=r._validated_reuse_context(identity,b,proof=proof)
    live=[];guard=r._DependencyGuard(lambda:live.append(1),r._PackingCandidateIndex([proof]))
    with pytest.raises(ValueError):r.validate_profile_reuse(identity,b,context=context)
    if damage in ('target','runtime'):
        with context.operation(guard):
            assert r.validate_profile_reuse(identity,b,context=context)
            changed=replace(b,ids=['foreign','tb']) if damage=='target' else b
            altered=identity if damage=='target' else dict(identity,runtime_profile={'changed':True})
            with pytest.raises(ValueError):r.validate_profile_reuse(altered,changed,context=context)
        assert guard.calls==2
    else:
        with pytest.raises(ValueError):
            with context.operation(guard):
                assert r.validate_profile_reuse(identity,b,context=context)
                changed=(reuse if damage=='attestation' else path)/'payload.json'
                old=changed.stat();raw=bytearray(changed.read_bytes());raw[-1]=32 if raw[-1]!=32 else 10;changed.write_bytes(raw);os.utime(changed,ns=(old.st_atime_ns,old.st_mtime_ns))
    with pytest.raises(ValueError):r.validate_profile_reuse(identity,b,context=context)


def test_serial_evidence_rejects_wrong_donor_convention(tmp_path,fake):
    d,p=_fake_pilot_inputs(1)[1:];inv=r.workload.build_inventory(d,p,stage='prefit')
    invocation=next(x for x in r._serial_invocations(inv) if any(c['operation']=='interchange' for c in x['cells']))
    result=r._pilot_invocation(object(),d,p,invocation,axes=None,root=tmp_path,guard=lambda:None)
    payload=dict(kind='a3_serial_numeric_invocation_v1',actual_execution=True,injected=True,timing_only=True,source_commit=p['commit'],runtime_profile=r.runtime_kernel_identity(object()),receipt=result['receipt'],positive_controls=result['positive_controls'],numeric_backing_references={})
    baseline=tmp_path/'baseline';r.publish_object(baseline,payload);proof=r._SerialNumericProof(baseline)
    measurement=r._pilot_scope_measurement(d,invocation);proof.check_scope(measurement);r._exact_pilot_scope(proof.rows,proof.specs,measurement)
    altered=copy.deepcopy(payload)
    for specs in altered['receipt']['batches'].values():
        for spec in specs:
            if spec['operation']=='interchange':
                for donor in spec['donors']:donor['mapping']['donor_stream']='not-a-real-stream'
    altered['receipt']['receipt_sha256']=r.workload.digest({k:v for k,v in altered['receipt'].items() if k!='receipt_sha256'})
    changed=tmp_path/'wrong-donor';r.publish_object(changed,altered)
    with pytest.raises(ValueError):
        bad=r._SerialNumericProof(changed);bad.check_scope(measurement);r._exact_pilot_scope(bad.rows,bad.specs,measurement)
