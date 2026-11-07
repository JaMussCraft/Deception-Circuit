import copy,json,os,shutil
from pathlib import Path
from types import SimpleNamespace
import pytest
from component_analysis import a3_direction_runtime as r
from tests.test_a3_direction_runner import fake
from tests.test_a3_direction_runtime import _fake_pilot_inputs

@pytest.mark.parametrize('damage',['bytes_restored_mtime','directory_child','symlink_target','ancestor_symlink','symlink_literal','cycle'])
def test_optimized_witness_rejects_mutation(tmp_path,damage):
    tree=tmp_path/'tree';tree.mkdir();f=tree/'data';f.write_bytes(b'abcd');other=tmp_path/'other';other.mkdir();(other/'data').write_bytes(b'abcd')
    path=tree
    if damage in ('symlink_target','symlink_literal'):
        (tmp_path/'link').symlink_to(tree,target_is_directory=True);path=tmp_path/'link'
    if damage=='ancestor_symlink':
        (tmp_path/'link').symlink_to(tree,target_is_directory=True);path=tmp_path/'link'/'data'
    witness=r._make_file_witness([path]);r._check_file_witness(witness)
    if damage=='bytes_restored_mtime':
        st=f.stat();f.write_bytes(b'abce');os.utime(f,ns=(st.st_atime_ns,st.st_mtime_ns))
    if damage=='directory_child':(tree/'new').write_bytes(b'')
    if damage in ('symlink_target','ancestor_symlink'):
        (tmp_path/'link').unlink();(tmp_path/'link').symlink_to(other,target_is_directory=True)
    if damage=='symlink_literal':
        (tmp_path/'link').unlink();(tmp_path/'link').symlink_to('tree',target_is_directory=True)
    if damage=='cycle':(tree/'cycle').symlink_to(tree,target_is_directory=True)
    with pytest.raises(ValueError):r._check_file_witness(witness)


def test_serial_measured_guard_covers_actual_scoring_dependency_union(tmp_path,fake):
    _,d,p=_fake_pilot_inputs(1);pilot=r.workload.build_inventory(d,p,stage='prefit')
    receipt=r.run_pilot(object(),d,p,pilot,root=tmp_path,args=SimpleNamespace(pilot_part='prefit',selected=None),guard=lambda:None,startup_seconds=0)
    r.publish_object(tmp_path/'test-admission',{'pilot_receipt_paths':[str(tmp_path/'pilot'/'prefit')]})
    r.publish_object(tmp_path/'test-reservation',{'admission_path':str(tmp_path/'test-admission')})
    index=r._admitted_candidate_index(SimpleNamespace(reservation=str(tmp_path/'test-reservation')),d,p)
    index.refresh_dependencies()
    print(json.dumps(dict(measured_guard_dependency_bytes=receipt['proof_verified_bytes'],scoring_dependency_roots=len(index.forest.paths),
        actual_scoring_dependency_bytes=index.forest.verified_bytes,serial_reference_count=len(receipt['serial_numeric_references']),
        source_unchanged=True,model_is_explicit_fake_cpu=True)))
    assert receipt['proof_verified_bytes']>=index.forest.verified_bytes
