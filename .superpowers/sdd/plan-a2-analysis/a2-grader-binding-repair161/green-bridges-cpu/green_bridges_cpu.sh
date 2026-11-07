#!/bin/bash
set -euo pipefail
DEP=/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/deployment/a2-binding161-provisional-green
IMAGE=/ocean/projects/cis260361p/swong2/specificity-ladder-20261102/containers/ubuntu2204.sif
PHYSICAL=/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment
: "${SLURM_JOB_ID:?CPU allocation required}"
OUT="$DEP/results-$SLURM_JOB_ID"
mkdir "$OUT"
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
scontrol show job "$SLURM_JOB_ID" -o > "$OUT/scontrol.txt"
scontrol show hostnames "$SLURM_JOB_NODELIST" > "$OUT/hosts.txt"
sha256sum "$IMAGE" > "$OUT/image.sha256"
python3 - "$OUT" "$SLURM_JOB_ID" "$PHYSICAL" <<'METADATA'
import json,os,socket,sys,time
from pathlib import Path
p=Path(sys.argv[1]);j=sys.argv[2]
a=dict(job_id=j,host=socket.gethostname(),captured_unix=time.time(),physical_alignment=sys.argv[3],scontrol_job=(p/'scontrol.txt').read_text(),allocation_hosts=(p/'hosts.txt').read_text().split(),image_sha256=(p/'image.sha256').read_text().split()[0],slurm_environment={k:v for k,v in os.environ.items() if k.startswith('SLURM_')})
(p/'allocation.json').write_text(json.dumps(a,indent=2)+'\n')
METADATA
timeout --kill-after=5s 180s apptainer exec --cleanenv --contain --no-home --writable-tmpfs \
 --pwd '/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-analysis/a2-grader-binding-candidate161' \
 --bind "$PHYSICAL:/projects/beto/swong2/Alignment:ro" \
 --bind /ocean:/ocean:ro \
 --bind /ocean/projects/cis260361p/swong2/hf/hub:/work/nvme/beto/swong2:ro \
 --bind "$OUT:/tmp/a2-binding161-proof:rw" \
 --env CUDA_VISIBLE_DEVICES= --env PYTHONDONTWRITEBYTECODE=1 \
 --env OPENBLAS_NUM_THREADS=1 --env OMP_NUM_THREADS=1 --env MKL_NUM_THREADS=1 --env NUMEXPR_NUM_THREADS=1 \
 --env HF_HUB_OFFLINE=1 --env TRANSFORMERS_OFFLINE=1 --env HF_DATASETS_OFFLINE=1 \
 --env SLURM_JOB_ID="$SLURM_JOB_ID" \
 "$IMAGE" /ocean/projects/cis260361p/swong2/envs/mgnp/bin/python "$DEP/run.py" /tmp/a2-binding161-proof \
 > "$OUT/mgnp.log" 2>&1
cat "$OUT/mgnp.log"
