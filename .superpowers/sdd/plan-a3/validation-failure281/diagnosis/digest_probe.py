"""Non-native stdlib probe: only extract digest(), never import application code."""
import ast
import copy
import hashlib
import json
from pathlib import Path

source = Path(__file__).parents[2] / 'direction-preallocation-candidate183/component_analysis/a3_direction_workload.py'
tree = ast.parse(source.read_text())
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'digest')
namespace = {'hashlib': hashlib, 'json': json}
exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
digest = namespace['digest']
receipt = {'startup_seconds': 7., 'proof_validation_seconds': 1.,
           'packing_evidence': {'example': {'kind': 'reference', 'evidence_sha256': 'unchanged'}}}
baseline = copy.deepcopy(receipt)
baseline.update(startup_seconds=0., proof_validation_seconds=0.)
# This marker is only a dictionary lookup marker, never a packing proof.
marker = object()
table = {(digest(receipt), 'example'): marker}
result = dict(scope='NON_NATIVE_DIGEST_AND_DICTIONARY_LOOKUP_ONLY',
              original_digest=digest(receipt), counterfactual_digest=digest(baseline),
              evidence_unchanged=receipt['packing_evidence'] == baseline['packing_evidence'],
              original_lookup_found=table.get((digest(receipt), 'example')) is marker,
              counterfactual_lookup_missing=table.get((digest(baseline), 'example')) is None)
assert result['evidence_unchanged'] and result['original_lookup_found'] and result['counterfactual_lookup_missing']
print(json.dumps(result, indent=2))
