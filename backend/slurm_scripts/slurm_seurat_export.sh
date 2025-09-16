#!/bin/bash
export R_HOME=/usr/lib/R
export LD_LIBRARY_PATH=/usr/lib/R/lib

# Execute the Python script with the provided arguments
python slurm_scripts/run_seurat_export.py "$1"