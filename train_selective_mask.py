#!/usr/bin/env python
"""Offline bounded selective-removal pilot; exactly one rho per invocation."""
from __future__ import annotations
import argparse
import os
from pathlib import Path

for name in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_DATASETS_OFFLINE','HF_HUB_DISABLE_TELEMETRY'):
    os.environ[name]='1'
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'


def main(argv: list[str] | None = None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    for mode in ('prepare','dry-run','baseline','calibrate','train','evaluate'):
        modes.add_argument('--'+mode,action='store_true')
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--output-dir',type=Path)
    for name in ('stage1-manifest','data-dir','honest-pool','candidate-bindings','freeze-record','reference-cache','checkpoint','evaluation-manifest'):
        p.add_argument('--'+name,type=Path)
    p.add_argument('--model-path',default='meta-llama/Llama-3.1-8B-Instruct')
    p.add_argument('--device',default='cuda')
    p.add_argument('--model-revision')
    p.add_argument('--dtype',choices=['bfloat16'],default='bfloat16')
    p.add_argument('--rho',type=float)
    for name in ('seed','epochs','validate-every','joint-pairs','accumulation'):
        p.add_argument('--'+name,type=int)
    p.add_argument('--resume',action='store_true')
    args=p.parse_args(argv)
    required=['stage1_manifest','data_dir','honest_pool','candidate_bindings'] if args.prepare else ['output_dir']
    if not (args.prepare or args.dry_run): required+=['freeze_record','data_dir','model_revision']
    if args.train or args.calibrate or args.evaluate: required+=['reference_cache']
    if args.evaluate: required+=['checkpoint','evaluation_manifest']
    for name in required:
        if getattr(args,name) is None: p.error('--'+name.replace('_','-')+' required for this mode')
    from evaluation.selective_mask_runner import run_cli
    return run_cli(args)


if __name__=='__main__':
    raise SystemExit(main())
