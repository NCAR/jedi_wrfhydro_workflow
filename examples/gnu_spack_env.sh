#!/bin/bash

module purge
module unuse /glade/u/apps/ch/modulefiles/default/compilers
export MODULEPATH_ROOT=/glade/work/jedipara/cheyenne/spack-stack/modulefiles
module use /glade/work/jedipara/cheyenne/spack-stack/modulefiles/compilers
module use /glade/work/jedipara/cheyenne/spack-stack/modulefiles/misc
module load ecflow/5.8.4
module load miniconda/3.9.12
# GNU
ulimit -s unlimited
module use /glade/work/jedipara/cheyenne/spack-stack/spack-stack-v1/envs/skylab-1.0.0-gnu-10.1.0/install/modulefiles/Core
module load stack-gcc/10.1.0
module load stack-openmpi/4.1.1
module load stack-python/3.9.12
module load jedi-fv3-env/1.0.0
module load bufr/11.7.1
# module load jedi-ewok-env/1.0.0
# module load nco/5.0.6

# these are needed so WRF-Hydro can build without other modifications
export NETCDF_INC=${netcdf_fortran_ROOT}/include
export NETCDF_LIB=${netcdf_fortran_ROOT}/lib

module list

