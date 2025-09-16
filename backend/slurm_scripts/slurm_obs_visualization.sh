#!/bin/bash
# usage: slurm_obs_visualization.sh <h5ad_path> <outdir> <dim_red> <obs_keys>

python slurm_scripts/run_obs_visualization.py "$1" "$2" "$3" "$4"