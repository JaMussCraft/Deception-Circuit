"""Exact owning CPU producer/validator commands; no invocation at import."""
from job_common import CFG,W,B,O,C,P
base=['--design',str(O/'canonical/design.json'),'--commit',C]
def commands():
    result=[]
    result.append(('canonical',['bash',str(B/'scripts/jobs/specificity_a3.sh'),'--experiment','directions','--stage','prepare','--action','freeze',*base,'--work-dir',str(O/'canonical'),'--a1-design',str(W/'outputs/_analyses/specificity-ladder/ladder-5f450dc/design.json'),'--a1-selected',str(W/'outputs/_analyses/specificity-ladder/ladder-5f450dc/selected.json'),'--matched-root',CFG['matched_root'],'--historical-csv',CFG['historical_csv'],'--root-ruling',str(O/'root-ruling.json'),'--execution-settings',str(O/'execution-settings.json'),'--registry',CFG['required_registry']]))
    result.append(('mask-settings',[CFG['python'],str(P/'prepare-mask-settings.py')]))
    mask=['bash',str(B/'scripts/jobs/specificity_a3_mask.sh'),'--stage','prepare',*base,'--work-dir',str(O/'mask'),'--chunk-size','4','--registry',CFG['required_registry']]
    result.append(('mask',mask+['--action','freeze','--root-bundle',str(O/'mask-source-settings')]))
    for stage in ('pilot','full'):result.append(('mask-inventory-'+stage,mask+['--action','inventory','--inventory-stage',stage,'--finish-reserve-seconds','300']))
    edge=['bash',str(B/'scripts/jobs/specificity_a3_edges.sh')]
    result.append(('edge',edge+['--stage','prepare',*base,'--work-dir',str(O/'edge'),'--registry',CFG['required_registry']]))
    result.append(('inventories',[CFG['python'],str(P/'prepare-inventories.py')]))
    result.append(('mask-dry-run',['bash',str(B/'scripts/jobs/specificity_a3_mask.sh'),'--stage','pilot',*base,'--work-dir',str(O/'mask'),'--chunk-size','4','--registry',CFG['required_registry'],'--dry-run']))
    result.append(('dry-run',edge+['--stage','pilot',*base,'--work-dir',str(O/'edge'),'--registry',CFG['required_registry'],'--dry-run']))
    result.append(('validate',[CFG['python'],str(P/'validate-preparation.py')]))
    for owner in ('mask','edge'):result.append(('measure-'+owner,[CFG['python'],str(P/'measure-source-cost.py'),owner]))
    for owner in ('mask','edge'):result.append(('negatives-'+owner,[CFG['python'],str(P/'copied-negatives.py'),owner]))
    result.append(('comparison',[CFG['driver_python'],str(P/'compare-compute.py')]))
    return result
