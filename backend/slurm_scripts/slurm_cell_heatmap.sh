#!/bin/bash
# usage: slurm_cell_heatmap.sh <h5ad_path> <outdir> <groupby> <options_json>

python slurm_scripts/run_cell_heatmap.py "$1" "$2" "$3" "$4"

