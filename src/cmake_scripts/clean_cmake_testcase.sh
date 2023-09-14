#!/bin/bash

binary_dir=${1}
version=${2}

rm -f ${binary_dir}/testcase-data-${version}.tar.gz
rm -rf ${binary_dir}/jedi_wrfhydro_workflow-testcase-data-${version}
