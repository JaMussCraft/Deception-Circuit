"""Same immutable runtime/environment project import probe; no model loaded."""
import os,sys,json
from pathlib import Path
from common import C,B,project_origins,source,write
assert Path.cwd().resolve()==B.resolve() and os.environ['PYTHONPATH']==str(B)
sys.path.insert(0,str(B))
from component_analysis import a2_pipeline
from component_analysis import ladder_pipeline
from evaluation import grader_hash
source()
origins=project_origins();assert origins
write(os.environ['A2_IMPORT_PROBE_OUTPUT'],dict(project_module_origins=origins,model_requested=False,scope='separate identical-environment no-model process before/after original CLI stage, not an inventory of modules in model child'))
