"""Immutable CPU numeric bundles and refresh-before-access direction lineage.

Bundles never deserialize pickle. COMPLETE.json is written last in the private
publication directory and binds every child byte, including the manifest.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

import numpy as np

from component_analysis import a3_design
from component_analysis import ladder_pipeline as ladder
from dataset import user_inversion_pipeline as common

require=common.require
RUNTIME_FILES=tuple('component_analysis/'+name+'.py' for name in (
    'a3_design','a3_pipeline','a3_directions','a3_statistics',
    'a3_direction_artifacts','a3_direction_runner','a3_direction_workload','a3_direction_pipeline'))+(
    'dataset/build_twin_training.py','scripts/twin_training.py','scripts/jobs/specificity_a3.sh')
KEY_FIELDS=('panel','analysis_task','source_task','split','seed','site','family',
            'axis_index','operation','instance_id','condition','stream')
FAMILIES=('learned','assessment_null','calibration_null','nuisance',
          'steering_learned','steering_nuisance','steering_random')


def code_hashes():
    """Require the entire declared runtime closure, including deferred stages."""
    paths=set(RUNTIME_FILES)|set(ladder.code_hashes())
    paths.update(str(p.relative_to(ladder.REPO)) for p in (ladder.REPO/'component_analysis').glob('a3_direction_*.py'))
    require(all((ladder.REPO/p).is_file() for p in paths), 'incomplete A3 runtime source closure')
    return {p:common.file_hash(ladder.REPO/p) for p in sorted(paths)}


def validate_numeric_profile(profile):
    """Physical kernel geometry is part of cache identity, even for one ID."""
    require(isinstance(profile,dict),'missing numeric profile')
    for key in ('padded_width','physical_batch_size','axis_tile_size'):
        require(type(profile.get(key)) is int and profile[key]>0,'invalid numeric profile '+key)
    for key in ('dtype','backend','model','model_revision'):
        require(isinstance(profile.get(key),str) and profile[key],'missing numeric profile '+key)
    require(isinstance(profile.get('source_sha256'),str)
            and re.fullmatch('[0-9a-f]{64}',profile['source_sha256']) is not None,'invalid numeric profile source hash')
    core={k:v for k,v in profile.items() if k!='profile_id'}
    digest=ladder.design._hash(core)
    require('profile_id' not in profile or profile['profile_id']==digest,'changed numeric profile id')
    return digest


SCIENTIFIC_KINDS=frozenset(('a3_readout_chunk','a3_direction_rows','a3_direction_shard',
    'a3_direction_fit','a3_direction_probe','a3_direction_axes','a3_direction_selection',
    'a3_direction_cache','a3_direction_calibration','a3_direction_outcomes'))
GENERIC_FIXTURE_KIND='a3_injected_fixture'
FIXTURE_SCHEMA='a3_injected_fixture_v1'
IDENTITY_FIELDS=frozenset(('analysis_split','injected','commit','code_hashes','a1_identity','parent_evidence',
    'design_sha256','protocol_sha256','matched_source_hashes','ordered_ids','streams','conditions','sites',
    'row_identity_sha256','grader_sha256','model','model_revision','tokenizer_revision','tokenizer_identity',
    'numeric_profile','capture_lineage'))
# These describe the captured membership; derived caches may aggregate/restrict it.
# Every other identity field, including profile and complete ancestry, is inherited.
MEMBERSHIP_FIELDS=frozenset(('ordered_ids','streams','conditions','sites','row_identity_sha256','capture_lineage'))


def _digest(value, length=64):
    return isinstance(value,str) and re.fullmatch('[0-9a-f]{'+str(length)+'}',value) is not None


def _hash_map(values):
    return (isinstance(values,dict) and bool(values)
            and all(isinstance(k,str) and bool(k) and _digest(v) for k,v in values.items()))


def capture_lineage_digest(identity):
    """Ancestry/profile digest inherited by derived fit/probe/axis caches."""
    return ladder.design._hash({k:v for k,v in identity.items() if k not in MEMBERSHIP_FIELDS})


def validate_scientific_metadata(metadata):
    """Strict semantic identity; generic fixtures use a distinct explicit kind.

    Hashes are checked structurally here and compared in full by consumers.
    Noninjected scientific data also requires the current complete runtime closure.
    validate_live separately re-reads source bytes and ancestor completion files;
    this schema is an integrity contract, not authentication or model admission.
    row_identity_sha256 hashes the ordered source prompt UTF-8, token IDs,
    readouts and native labels. Producers compute it from their source rows.
    """
    require(isinstance(metadata,dict) and metadata.get('schema_version')==1
            and type(metadata.get('schema_version')) is int and metadata.get('kind') in SCIENTIFIC_KINDS,'unknown scientific kind/schema')
    identity=metadata.get('identity')
    require(isinstance(identity,dict) and IDENTITY_FIELDS<=identity.keys(),'incomplete scientific identity fields')
    require(type(metadata.get('injected')) is bool and type(identity['injected']) is bool
            and metadata['injected']==identity['injected'],'scientific identity injected mismatch')
    require(metadata.get('split') in ('train','validation','assessment','fit_selection')
            and identity['analysis_split']==metadata['split'],'scientific identity analysis split mismatch')
    require(_digest(identity['commit'],40),'scientific identity requires full A3 commit')
    closure=identity['code_hashes']
    require(_hash_map(closure) and (set(RUNTIME_FILES)|set(ladder.code_hashes()))<=closure.keys(),
            'incomplete scientific identity source closure')
    require(all(not Path(path).is_absolute() and '..' not in Path(path).parts for path in closure),
            'scientific identity source closure requires relative paths')
    if not metadata['injected']:
        require(closure==code_hashes(),'changed scientific production source closure')
    for field in ('design_sha256','protocol_sha256','row_identity_sha256','grader_sha256'):
        require(_digest(identity[field]),'invalid scientific identity '+field)
    require(_hash_map(identity['matched_source_hashes']),'invalid scientific identity matched sources')
    parent=identity['a1_identity']
    require(isinstance(parent,dict) and all(k in parent for k in (
        'commit','model','model_revision','tokenizer_revision','tokenizer_identity','grader_sha256','source_hashes')),
        'incomplete scientific identity A1 parent')
    require(_digest(parent['commit'],40) and _hash_map(parent['source_hashes']), 'invalid scientific identity A1 commit/sources')
    evidence=identity['parent_evidence']
    require(isinstance(evidence,dict) and isinstance(evidence.get('completion'),dict) and bool(evidence['completion']),
            'incomplete scientific identity A1 completion')
    for stem in ('prepared','selected','completion'):
        require(isinstance(evidence.get(stem+'_path'),str) and evidence[stem+'_path']
                and _digest(evidence.get(stem+'_file_sha256')),'incomplete scientific identity parent/sidecar bytes')
    for field in ('model','model_revision','tokenizer_revision','tokenizer_identity','grader_sha256'):
        require(identity[field]==parent[field], 'changed scientific identity original model/tokenizer/grader '+field)
    require(isinstance(identity['model'],str) and identity['model'] and _digest(identity['model_revision'],40)
            and _digest(identity['tokenizer_revision'],40) and _digest(identity['grader_sha256'])
            and isinstance(identity['tokenizer_identity'],dict) and bool(identity['tokenizer_identity']),
            'invalid scientific identity model/tokenizer/grader')
    for field in ('ordered_ids','streams','conditions'):
        values=identity[field]
        require(isinstance(values,list) and values and all(isinstance(v,str) and v for v in values)
                and len(set(values))==len(values),'invalid ordered scientific identity '+field)
    require(set(identity['streams'])<={'clean','corrupt'},'invalid scientific identity streams')
    sites=identity['sites']
    require(isinstance(sites,list) and sites and all(isinstance(s,list) and len(s)==3 and s[0]=='head'
            and all(type(v) is int and 0<=v<32 for v in s[1:]) for s in sites)
            and len({tuple(s) for s in sites})==len(sites),'invalid scientific identity sites')
    profile=identity['numeric_profile']; profile_digest=validate_numeric_profile(profile)
    require(profile['model']==identity['model'] and profile['model_revision']==identity['model_revision']
            and profile['source_sha256']==ladder.design._hash(closure),'scientific identity numeric profile/source mismatch')
    references=identity['capture_lineage']
    require(isinstance(references,list),'invalid scientific capture lineage')
    if metadata['kind']!='a3_readout_chunk':
        require(references,'derived scientific cache requires capture lineage')
    for reference in references:
        require(isinstance(reference,dict) and all(_digest(reference.get(k)) for k in (
            'manifest_sha256','completion_sha256','identity_sha256','lineage_sha256','numeric_profile_sha256'))
            and all(type(reference.get(k)) is int and reference[k]>0 for k in ('manifest_bytes','completion_bytes')),
            'incomplete scientific capture lineage byte identity')
        require(reference['lineage_sha256']==capture_lineage_digest(identity)
                and reference['numeric_profile_sha256']==profile_digest,'changed scientific capture lineage/profile')
    require(len({ladder.design._hash(r) for r in references})==len(references),'duplicate scientific capture lineage')
    return identity


def _numeric_metadata(metadata, expected=None):
    if metadata.get('kind')==GENERIC_FIXTURE_KIND:
        require(metadata.get('schema_version')==1 and metadata.get('injected') is True,
                'generic fixture requires explicit injected schema')
        identity=metadata.get('identity',metadata)
        require(identity.get('injected',True) is True,'generic fixture identity cannot be production')
        profile=identity.get('numeric_profile')
        if metadata.get('fixture_kind')=='a3_direction_shard': validate_numeric_profile(profile)
        if profile is not None:
            validate_numeric_profile(profile)
            if expected is not None:
                require(expected.get('identity',expected).get('numeric_profile')==profile,
                        'exact expected numeric profile required for fixture cache reuse')
        return
    validate_scientific_metadata(metadata)
    if expected is not None:
        validate_scientific_metadata(expected)
        require(ladder.design._hash(metadata)==ladder.design._hash(expected),'complete scientific identity mismatch')


def _shard_metadata(identity):
    if identity.get('fixture_schema')==FIXTURE_SCHEMA:
        return dict(schema_version=1,kind=GENERIC_FIXTURE_KIND,injected=identity.get('injected'),
                    fixture_kind='a3_direction_shard',identity=identity)
    return dict(schema_version=1,kind='a3_direction_shard',split=identity.get('analysis_split'),
                injected=identity.get('injected'),identity=identity)


def capture_reference(path, *, expected):
    """Read a strict capture and freeze its exact byte/ancestry/profile links."""
    metadata,_=read_bundle(path,expected=expected)
    require(metadata.get('kind')=='a3_readout_chunk','capture lineage requires a scientific capture')
    identity=validate_scientific_metadata(metadata); root=Path(path)
    return dict(manifest_sha256=common.file_hash(root/'manifest.json'),
        completion_sha256=common.file_hash(root/'COMPLETE.json'),
        manifest_bytes=(root/'manifest.json').stat().st_size,completion_bytes=(root/'COMPLETE.json').stat().st_size,
        identity_sha256=ladder.design._hash(identity),lineage_sha256=capture_lineage_digest(identity),
        numeric_profile_sha256=validate_numeric_profile(identity['numeric_profile']))


def _strict_json(path):
    def reject(value):
        raise ValueError('nonfinite JSON value: '+value)
    return json.loads(Path(path).read_text(),parse_constant=reject)


def _identity(actual, expected):
    require(isinstance(actual,dict) and isinstance(expected,dict),'invalid bundle identity')
    require(all(k in actual and ladder.design._hash(actual[k])==ladder.design._hash(v)
                for k,v in expected.items()), 'bundle identity mismatch')


def _children(root):
    result={}
    for path in sorted(root.rglob('*')):
        require(not path.is_symlink(),'bundle symlink forbidden')
        if path.is_file() and path!=root/'COMPLETE.json':
            result[str(path.relative_to(root))]=dict(sha256=common.file_hash(path),bytes=path.stat().st_size)
    return result


def _complete(root):
    marker=root/'COMPLETE.json'
    require(marker.is_file() and not marker.is_symlink(),'incomplete bundle: missing completion marker')
    value=_strict_json(marker)
    require(value.get('schema_version')==1 and value.get('kind')=='a3_complete','invalid bundle completion marker')
    require(value.get('files')==_children(root),'bundle child bytes/hash mismatch')
    return value


def _finish(root):
    files=_children(root)
    # Reread all child bytes before the final completion marker is published.
    require(files==_children(root),'bundle changed during publication')
    marker=dict(schema_version=1,kind='a3_complete',files=files)
    common.write_json(root/'COMPLETE.json',marker)
    _complete(root)
    return marker


def write_bundle(target, metadata: dict, arrays: dict):
    """Publish fresh portable numeric .npy files and exact descriptors."""
    require(isinstance(metadata,dict) and isinstance(arrays,dict),'invalid bundle inputs')
    # Validate JSON before publication; no numpy/object fallback serialization.
    json.dumps(metadata,allow_nan=False)
    _numeric_metadata(metadata)
    receipt={}
    def writer(root):
        descriptors={}; (root/'arrays').mkdir()
        for name,array in sorted(arrays.items()):
            require(isinstance(name,str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*',name) is not None,'unsafe array name')
            require(isinstance(array,np.ndarray) and array.dtype.kind in 'biufc' and not array.dtype.hasobject,'numeric array required')
            file=root/'arrays'/(name+'.npy')
            np.save(str(file),array,allow_pickle=False)
            loaded=np.load(str(file),allow_pickle=False,mmap_mode='r')
            require(loaded.dtype==array.dtype and loaded.shape==array.shape,'numeric roundtrip differs')
            descriptors[name]=dict(path='arrays/'+name+'.npy',dtype=array.dtype.str,shape=list(array.shape),
                                   sha256=common.file_hash(file),bytes=file.stat().st_size)
        common.write_json(root/'manifest.json',dict(schema_version=1,kind='a3_numeric_bundle',metadata=metadata,arrays=descriptors))
        receipt.update(_finish(root))
    common.publish(target,writer)
    read_bundle(target,expected=metadata)
    return receipt


def read_bundle(path, *, expected: dict):
    root=Path(path); complete=_complete(root); manifest=_strict_json(root/'manifest.json')
    require(manifest.get('schema_version')==1 and manifest.get('kind')=='a3_numeric_bundle','invalid numeric bundle schema')
    _identity(manifest.get('metadata'),expected)
    _numeric_metadata(manifest['metadata'],expected)
    descriptors=manifest.get('arrays'); require(isinstance(descriptors,dict),'missing array descriptors')
    arrays={}
    expected_files={'manifest.json'}
    for name,desc in descriptors.items():
        require(isinstance(name,str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*',name) is not None,'unsafe array name')
        relative='arrays/'+name+'.npy'; expected_files.add(relative)
        require(desc.get('path')==relative,'unsafe array path')
        file=root/relative
        require(desc.get('bytes')==file.stat().st_size and desc.get('sha256')==common.file_hash(file),'array bytes/hash mismatch')
        array=np.load(str(file),mmap_mode='r',allow_pickle=False)
        require(array.dtype.kind in 'biufc' and not array.dtype.hasobject,'numeric array required')
        require(desc.get('dtype')==array.dtype.str and desc.get('shape')==list(array.shape),'array descriptor mismatch')
        arrays[name]=array
    require(set(complete['files'])==expected_files,'unexpected bundle children')
    return manifest['metadata'],arrays


def _freeze(value):
    if isinstance(value,(list,tuple)): return tuple(_freeze(v) for v in value)
    require(isinstance(value,(str,int)) and not isinstance(value,bool),'invalid raw row key value')
    return value


def row_key(row):
    require(all(k in row for k in KEY_FIELDS),'missing raw row key field')
    require(row['family'] in FAMILIES,'unknown direction family')
    return tuple(_freeze(row[k]) for k in KEY_FIELDS)


def _coverage(rows, expected_keys):
    keys=[row_key(row) for row in rows]; expected=[_freeze(k) for k in expected_keys]
    require(len(keys)==len(set(keys)) and len(expected)==len(set(expected)) and set(keys)==set(expected),
            'incomplete/duplicate shard row coverage')


def publish_shard(target, *, identity: dict, expected_keys: list, rows: list, execution: dict):
    _coverage(rows,expected_keys)
    _numeric_metadata(_shard_metadata(identity))
    receipt={}
    def writer(root):
        common.write_jsonl(root/'rows.jsonl',rows)
        common.write_json(root/'run_manifest.json',dict(schema_version=1,kind='a3_direction_shard',identity=identity,
                          expected_keys=expected_keys,row_count=len(rows),execution=execution,complete=True))
        reread=[_strict_json_line(line) for line in (root/'rows.jsonl').read_text().splitlines()]
        _coverage(reread,expected_keys)
        receipt.update(_finish(root))
    common.publish(target,writer)
    return receipt


def _strict_json_line(line):
    return json.loads(line,parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON '+value)))


def read_completed_shards(inventory: dict, shard_root, *, identity: dict):
    """Read only exact complete inventory shards; absent shards remain missing."""
    _numeric_metadata(_shard_metadata(identity))
    if 'identity' in inventory: _identity(inventory['identity'],identity)
    shards=inventory.get('shards'); require(isinstance(shards,list),'missing shard inventory')
    seen=set(); rows=[]
    for shard in shards:
        name=shard.get('shard_id')
        require(isinstance(name,str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',name) and name not in seen,'invalid/duplicate shard id')
        seen.add(name); root=Path(shard_root)/name
        if not root.exists(): continue
        marker=_complete(root)
        require(set(marker['files'])=={'run_manifest.json','rows.jsonl'},'unexpected shard children')
        manifest=_strict_json(root/'run_manifest.json')
        require(manifest.get('schema_version')==1 and manifest.get('kind')=='a3_direction_shard' and manifest.get('complete') is True,'incomplete shard manifest')
        _identity(manifest.get('identity'),identity)
        _numeric_metadata(_shard_metadata(manifest['identity']),_shard_metadata(identity))
        require(ladder.design._hash(manifest.get('expected_keys'))==ladder.design._hash(shard['expected_keys']),'changed shard inventory coverage')
        actual=[_strict_json_line(line) for line in (root/'rows.jsonl').read_text().splitlines()]
        _coverage(actual,shard['expected_keys'])
        require(manifest.get('row_count')==len(actual),'shard row count differs')
        rows.extend(actual)
    require(len({row_key(row) for row in rows})==len(rows),'duplicate rows across shards')
    return rows


def validate_cached_utility_source(snapshot, relative, digest):
    """Permit lexical snapshot files and same-repository HF blob links only.

    HF snapshots intentionally symlink into their repository's blobs directory.
    Relative manifest paths may never traverse; a trusted blob still requires
    its exact frozen content hash, and the blob directory cannot redirect away.
    """
    snapshot=Path(snapshot).absolute()
    require(isinstance(relative,str) and relative and not Path(relative).is_absolute()
            and '..' not in Path(relative).parts,'escaped cached utility source path')
    lexical=snapshot/relative
    resolved=lexical.resolve(); snapshot_real=snapshot.resolve()
    allowed=resolved.is_relative_to(snapshot_real)
    if not allowed and lexical.is_symlink() and snapshot.parent.name=='snapshots':
        repo=snapshot.parent.parent; blobs=repo/'blobs'
        allowed=(re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}',snapshot.name) is not None
                 and repo.name.startswith('datasets--') and not blobs.is_symlink()
                 and blobs.resolve().parent==repo.resolve()
                 and resolved.parent==blobs.resolve()
                 and re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}',resolved.name) is not None)
    require(allowed and lexical.is_file() and common.file_hash(lexical)==digest,
            'changed cached utility source bytes or untrusted target')


def validate_live(design: dict, protocol: dict, *, registry_paths: list):
    """Re-read real protected IDs, graders, ancestry and every frozen file byte.

    Call immediately before each load/new shard/resume. This CPU guard grants no
    model admission or finalization; an explicitly injected lineage stays so.
    """
    from component_analysis import a3_pipeline
    require(design.get('direction_protocol')==protocol and design.get('direction_protocol_sha256')==ladder.design._hash(protocol),'changed direction protocol')
    core={k:v for k,v in design.items() if k not in ('direction_protocol','direction_protocol_sha256')}
    require(protocol.get('design_sha256')==ladder.design._hash(core),'changed A3 design identity')
    registries=a3_design.validate_access(design,list(registry_paths))
    graders=ladder.grader_registry()
    require(design['a1_identity']['grader_sha256']==ladder.GRADER,'changed frozen grader identity')
    require(bool(design.get('injected'))==bool(protocol.get('injected')),'injected identity mismatch')
    if protocol.get('injected_source_closure') is not None:
        require(design.get('injected') is True,'injected source closure forbidden for production')
        fresh=protocol['injected_source_closure']
    else: fresh=code_hashes()
    require(protocol.get('code_hashes')==fresh,'changed A3 runtime source closure')
    for path,digest in fresh.items():
        require((ladder.REPO/path).is_file() and common.file_hash(ladder.REPO/path)==digest,'changed injected source closure')
    evidence=design['parent_evidence']
    prepared,selected,current=a3_pipeline.load_a1_parents(evidence['prepared_path'],evidence['selected_path'])
    require(current==evidence,'changed A1 parent file bytes or completion evidence')
    a3_pipeline._validate_parent_files(prepared,a1_repo_root=design['a1_repo_root'])
    require(design['a1_identity']=={k:prepared[k] for k in design['a1_identity']},'changed original A1 identity')
    require(design['parent_digests']['prepared']==ladder.design._hash(prepared)
            and design['parent_digests']['selected']==ladder.design._hash(selected),'changed A1 parent payload')
    a3_pipeline.validate_assessment_membership(design,prepared)
    manifests=[design.get('mmlu_validation_candidates_manifest',{}),design.get('utility',{}).get('mmlu_manifest',{})]
    for manifest in manifests:
        snapshot=manifest.get('snapshot','.')
        for relative,digest in manifest.get('parquet_hashes',{}).items():
            validate_cached_utility_source(snapshot,relative,digest)
    for path,digest in list(design['historical_source_hashes'].items())+[(design['matched_build_path'],design['matched_build_file_sha256'])]:
        require(Path(path).is_file() and common.file_hash(path)==digest,'changed A3 source bytes')
    return dict(registry_hashes=registries,grader_registry=graders,injected=bool(design.get('injected')),
                commit=protocol['commit'],protocol_sha256=ladder.design._hash(protocol))


def validate_final_identity(identity, *, final):
    """A CPU artifact cannot confer production completion on an injected run."""
    ladder.validate_finalization(identity,final=final)
    if final:
        require(identity.get('injected') is False and identity.get('pilot') is False,
                'explicit noninjected nonpilot identity required')
        require(identity.get('complete') is True,'incomplete production identity')
        require(isinstance(identity.get('commit'),str) and re.fullmatch('[0-9a-f]{40}',identity['commit']),
                'full production source commit required')
        require(identity.get('code_hashes')==code_hashes(),'changed production source closure')
