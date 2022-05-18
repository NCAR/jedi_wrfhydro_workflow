#!/bin/bash
#PBS -N jedi_workflow_test
#PBS -A [PROJECT_CODE]
#PBS -l walltime=00:10:00
#PBS -q regular
#PBS -j oe
#PBS -l select=1:ncpus=36:mpiprocs=36:mem=108GB

# Load Environment
module purge
export JEDI_OPT=/glade/work/jedipara/cheyenne/opt/modules
module use $JEDI_OPT/modulefiles/core
module load jedi/gnu-openmpi

# Jedi workflow setup
workflow=/path/to/jedi_workflow_dir/jedi_workflowpy.py
workflow_yaml=/path/to/jedi_workflow.yaml

# Run Jedi Workflow
echo "start time: " `date`
python3 ${workflow} ${workflow_yaml}
echo "end time: " `date`

# Steps
# 1. Prep this file and experiment yamls, files and setup
# 2. Enter `qsub sub_script.sh` into the command line
