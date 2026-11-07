from job_common import CFG,W,B,O,C,P
base=['--design',str(O/'canonical/design.json'),'--commit',C]
def commands():
    mask=['bash',str(B/'scripts/jobs/specificity_a3_mask.sh'),'--stage','prepare',*base,'--work-dir',str(O/'mask'),'--chunk-size','4','--registry',CFG['required_registry']]
    return [('canonical',['bash',str(B/'scripts/jobs/specificity_a3.sh'),'--experiment','directions','--stage','prepare','--action','freeze',*base,'--work-dir',str(O/'canonical'),'--a1-design',str(W/'outputs/_analyses/specificity-ladder/ladder-5f450dc/design.json'),'--a1-selected',str(W/'outputs/_analyses/specificity-ladder/ladder-5f450dc/selected.json'),'--matched-root',CFG['matched_root'],'--historical-csv',CFG['historical_csv'],'--root-ruling',str(O/'root-ruling.json'),'--execution-settings',str(O/'execution-settings.json'),'--registry',CFG['required_registry']]),
        ('mask-settings',[CFG['python'],str(P/'prepare-mask-settings.py')]),
        ('mask',mask+['--action','freeze','--root-bundle',str(O/'mask-source-settings')]),
        ('mask-inventory-pilot',mask+['--action','inventory','--inventory-stage','pilot','--finish-reserve-seconds','300']),
        ('mask-inventory-full',mask+['--action','inventory','--inventory-stage','full','--finish-reserve-seconds','300']),
        ('mask-dry-run',['bash',str(B/'scripts/jobs/specificity_a3_mask.sh'),'--stage','pilot',*base,'--work-dir',str(O/'mask'),'--chunk-size','4','--registry',CFG['required_registry'],'--dry-run']),
        ('validate-mask',[CFG['python'],str(P/'validate-mask.py')]),
        ('prospective-admission',[CFG['python'],str(P/'prepare-prospective-admission.py')])]
