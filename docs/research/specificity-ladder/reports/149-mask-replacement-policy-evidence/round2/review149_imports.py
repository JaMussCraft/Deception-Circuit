import os,json
from pathlib import Path

def pytest_sessionfinish(session,exitstatus):
    import sys
    root=Path(os.environ['REVIEW149_CANDIDATE']).resolve()
    found={}
    for name,m in list(sys.modules.items()):
        if name.split('.')[0] not in ('component_analysis','dataset','models','l0'):continue
        f=getattr(m,'__file__',None)
        if f:
            p=Path(f).resolve();assert p.is_relative_to(root),(name,str(p),str(root));found[name]=str(p)
    Path(os.environ['REVIEW149_IMPORTS']).write_text(json.dumps(found,indent=2)+'\n')
