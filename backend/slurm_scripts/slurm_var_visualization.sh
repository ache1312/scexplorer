#!/bin/bash
# usage: slurm_var_visualization.sh <h5ad_path> <outdir> <dim_red> <var_keys>

python slurm_scripts/run_var_visualization.py "$1" "$2" "$3" "$4"
