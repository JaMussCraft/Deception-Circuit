#!/bin/bash
# Run only within root's CPU allocation: RM-shared, cis260361p, 5 CPU, 8 GiB, ten minutes.
set -euo pipefail
P=/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103
DEP="$P/deployment"
IMAGE=/ocean/projects/cis260361p/swong2/specificity-ladder-20261102/containers/ubuntu2204.sif
: "${SLURM_JOB_ID:?CPU Slurm allocation required}"
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
scontrol show job "$SLURM_JOB_ID" -o > "$DEP/cpu-data-proof-${SLURM_JOB_ID}.scontrol.txt"
sha256sum "$IMAGE" > "$DEP/cpu-data-proof-${SLURM_JOB_ID}.image.sha256"
python3 - "$DEP" "$SLURM_JOB_ID" <<'METADATA'
import json,os,socket,sys,time
from pathlib import Path
p=Path(sys.argv[1]); j=sys.argv[2]
x={"job_id":j,"host":socket.gethostname(),"captured_unix":time.time(),"scontrol_job":(p/("cpu-data-proof-"+j+".scontrol.txt")).read_text(),"image_sha256":(p/("cpu-data-proof-"+j+".image.sha256")).read_text().split()[0],"slurm_environment":{k:v for k,v in os.environ.items() if k.startswith("SLURM_")}}
(p/("cpu-data-proof-"+j+".allocation.json")).write_text(json.dumps(x,indent=2)+"\n")
METADATA
apptainer exec --cleanenv --contain --no-home --writable-tmpfs \
 --pwd /projects/beto/swong2/Alignment \
 --bind "$P/Alignment:/projects/beto/swong2/Alignment:ro" \
 --bind /ocean:/ocean:ro \
 --bind /ocean/projects/cis260361p/swong2/hf/hub:/work/nvme/beto/swong2:ro \
 --env CUDA_VISIBLE_DEVICES= --env PYTHONDONTWRITEBYTECODE=1 \
 --env SLURM_JOB_ID="$SLURM_JOB_ID" \
 "$IMAGE" /ocean/projects/cis260361p/swong2/envs/mgnp/bin/python \
 "$DEP/verify-transferred-data-r2.py" "$DEP/canonical-transfer-manifest.json" \
 "$DEP/cpu-data-proof-${SLURM_JOB_ID}.allocation.json" \
 > "$DEP/cpu-data-proof-${SLURM_JOB_ID}.json"
cat "$DEP/cpu-data-proof-${SLURM_JOB_ID}.json"
