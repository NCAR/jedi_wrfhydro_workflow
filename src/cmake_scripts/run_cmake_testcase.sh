#!/bin/bash

# Bash script is meant to be used by CMake. It runs the workflow testcase

binary_dir=${1}
version=${2}

cd ${binary_dir}/jedi_wrfhydro_workflow-testcase-data-${version}
# run testcases
make
