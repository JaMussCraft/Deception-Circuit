"""External data-only factor; reuses exact Task2 helpers, no operational identity."""
import importlib
import os
from pathlib import Path
import sys


def execute(v,c):
    v.require(c['root_source_review_accepted'] is True,'accepted source required')
    v.require(os.environ.get('CUDA_VISIBLE_DEVICES','')=='' and os.environ.get('SLURM_CLUSTER_NAME')=='delta'
              and os.environ.get('SLURM_JOB_ID')==c['actual_CPU_job_id'],'real Delta CPU context')
    runtime=Path(c['accepted_runtime'])
    current=v.catalogue_expectations(c['current_catalogue_witness'],c['packet_manifest_sha256'],c['actual_CPU_job_id'])
    v.bound(c['accepted_source_snapshot']);v.bound(c['input_manifest'])
    before=v.capture_identities(c)
    os.chdir(str(runtime));sys.path.insert(0,str(runtime))
    p=importlib.import_module('component_analysis.a2_pipeline');v.origins(runtime)
    native=v.validate_native_context(c,p)
    prepared,receipt,banks=(native.pop('_prepared'),native.pop('_receipt'),native.pop('_banks'))
    args=native.pop('_args')
    v.require(p.hash_content(banks)==c['bank_internal_payload_sha256'],'native bank payload identity')
    old=p.a1.read_artifact(c['historical_G2']['path'])
    provenance={'execution_commit','file_references','grader_registry','receipt_sha256','registry_hashes','runtime_code_hashes','utility_registry_hashes'}
    v.require(set(old)==set(v.SCIENCE_FIELDS)|provenance and set(receipt)==set(old)|{'grader_binding'},'exact G2/G3 schema')
    for field in v.SCIENCE_FIELDS:v.require(old[field]==receipt[field],'immutable G2/G3 science: '+field)
    proof=v.bound(c['full_domain_proof'])
    v.require(proof['source_commit']==v.SOURCE and proof['model_loaded'] is False
              and proof['bank_sha256']==c['bank_file_sha256'],'accepted genuine domain proof identity')
    mask,reconstructed_controls=v.reconstruct_domain(p,prepared,receipt)
    domain=v.validate_domain_identity(p.expected_keys(receipt,0),p.a1.positive_keys(p._prepared_domain(receipt),0),
                                      mask,reconstructed_controls,proof['full'])
    v.require(domain['rows']==59652 and domain['positive_controls']==3396
              and domain['support_reason_mask_sha256']==proof['full']['support_reason_mask_sha256'],'full-domain identity')
    p._validate_live(args,receipt,prepared)
    after=v.capture_identities(c);v.require(before==after,'source/input/G3/bank/catalogues changed during diagnostic')
    captures=[]
    for index,path in enumerate(v.CATALOGUES):
        raw=Path(path).read_bytes();v.require(v.digest(raw)==before['catalogues'][path],'catalogue changed before capture')
        target=Path(c['evidence_output'])/('catalogue-%d.json'%index)
        with target.open('xb') as stream:stream.write(raw)
        captures.append(dict(virtual_path=path,sha256=v.digest(raw),bytes=len(raw),captured_bytes_path=str(target)))
    v.require(v.capture_identities(c)==before,'final source/catalogue capture drift')
    return dict(kind='A2_DATA_TIMING_DIAGNOSTIC_V1',diagnostic_only=True,operational_admission=False,
        source_commit=v.SOURCE,actual_CPU_job_id=c['actual_CPU_job_id'],native_observations=native,
        counts=domain,source_before=before,source_after=after,module_origins=v.origins(runtime),
        packet_manifest_sha256=c['packet_manifest_sha256'],current_catalogue_witness_sha256=c['current_catalogue_witness']['sha256'],
        catalogue_capture_files=captures,assessment_effects_inspected=False)
