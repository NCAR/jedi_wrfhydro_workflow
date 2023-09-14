#!/bin/bash

# Bash script is meant to be used by CMake. It downloads and extracts the
# testcase to the CMake build directory.

binary_dir=${1}
version=${2}

# download testcase if not present
tarball=testcase-data-${version}.tar.gz
if [ ! -f ${binary_dir}/${tarball} ]
then
    cd ${binary_dir}
    wget -nv https://github.com/NCAR/jedi_wrfhydro_workflow/archive/refs/tags/${tarball}
fi

cd ${binary_dir}
# extract testcase
if [ ! -d jedi_wrfhydro_workflow-testcase-data-${version} ]
then
   tar zxf ${tarball}
fi
