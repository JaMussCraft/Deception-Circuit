from pathlib import Path
import json,os
D=Path('/projects/beto/swong2/Alignment/Deception-Circuit');O=D/'docs/research/specificity-ladder/wrapup';groups=[];problems=[]
for item in json.loads((O/'required-file-inventory.json').read_text()):
 matched=variants=0
 for row in item['files']:
  p=D/row['relative'];ok=p.is_symlink() if row['kind']=='symlink' else p.is_file() and p.stat().st_size==row['bytes']
  if ok:matched+=1;continue
  choices=[Path(str(p)+'.pre-b2fetch'),Path(str(p)+'.pre-local-wrapup')]
  if row['relative'].startswith('.superpowers/sdd/'):
   choices.append(D/'.superpowers/sdd-bridges-preserved'/Path(row['relative']).relative_to('.superpowers/sdd'))
  found=next((x for x in choices if x.is_file() and row['kind']=='file' and x.stat().st_size==row['bytes']),None)
  if found:variants+=1
  else:problems.append(dict(group=item['root'],row=row))
 groups.append(dict(source=item['root'],exists_on_remote=item['exists'],expected_entries=len(item['files']),matched_at_primary_relative_path=matched,retained_variants=variants))
for label,rows in [('job_logs',json.loads((O/'all-job-logs.json').read_text())['logs']),('remote_packet_source',json.loads((O/'remote-packet-mirror.json').read_text())['files'])]:
 expected={}
 for row in rows:
  rel=row['destination']
  if rel.startswith('.superpowers/sdd/'):rel='outputs/_analyses/specificity-ladder/bridges2-staging/packet-source/'+rel[len('.superpowers/sdd/'):]
  expected[rel]=row
 matched=0
 for rel,row in expected.items():
  p=D/rel;ok=p.is_symlink() if row.get('symlink') else p.is_file() and p.stat().st_size==row['bytes']
  if ok:matched+=1
  else:problems.append(dict(group=label,destination=rel,row=row))
 groups.append(dict(source=label,expected_entries=len(expected),matched_at_primary_relative_path=matched))
image=D/'containers/ubuntu2204.sif';groups.append(dict(source='container only located copy',expected_entries=1,matched_at_primary_relative_path=int(image.is_file() and image.stat().st_size==30027776)))
result=dict(groups=groups,problems=problems,verification='Relative file names, file types and byte counts; rsync checksum transfer. No scientific acceptance.',success=not problems)
(O/'copy-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(groups=groups,problems=len(problems)),indent=2))
