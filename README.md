# JEDI Workflow
A framework providing a workflow between [WRF-Hydro/NWM JEDI](https://github.com/JCSDA-internal/wrf_hydro_nwm_jedi) and [WRF-Hydro](https://github.com/NCAR/wrf_hydro_nwm_public).


# Build Steps
```console
$ mkdir build
$ cd build
$ ecbuild ../bundle
$ make -j 4
```
The workflow uses Github Submodules to obtain all the required repositories.
All executables will now be in the `build/bin` directory.
The user can choose to call `jedi_workflowpy.py` from the `build/bin`
  directory or from the `src/jedi_workflowpy` directory.
See this section for [building on Cheyenne.](#Cheyenne-Specific-Build-Instructions).

# Experiment Setup
Before running expirements a number of directories, YAML files, and JSON files will need to be setup.
For further instructions on this process see the [expirement setup document](docs/expirement_setup.md "Expirement Setup").


# Run Workflow
```console
$ python3 [path_to]/jedi_workflowpy.py jedi_workflow.yaml
```


# Cheyenne Specific Build Instructions
## Setup Environment
### Using Modules
```console
$ source gnu_env.sh
$ cat gnu_env.sh
#!/bin/bash
module purge
export JEDI_OPT=/glade/work/jedipara/cheyenne/opt/modules
module use $JEDI_OPT/modulefiles/core
module load jedi/gnu-openmpi
module load atlas/ecmwf-0.29.0
```

### Using GNU Spack Stack 1.4.0
Note: this is for building and running the `develop` branch.
The `develop` branch ~~is~~ will be setup to build and run with Spack modules on up-to-date JEDI modules.

See [Spack Stack readthedocs](https://spack-stack.readthedocs.io/en/1.4.0/PreConfiguredSites.html#ncar-wyoming-cheyenne)
for more detail and information on how to load the Intel stack.
```console
module purge
export LMOD_TMOD_FIND_FIRST=yes
module use /glade/work/jedipara/cheyenne/spack-stack/modulefiles/misc
module load miniconda/3.9.12
module load ecflow/5.8.4
module load mysql/8.0.31

module use /glade/work/epicufsrt/contrib/spack-stack/spack-stack-1.4.0/envs/unified-env-v2/install/modulefiles/Core
module load stack-gcc/10.1.0
module load stack-openmpi/4.1.1
module load stack-python/3.9.12
module load jedi-base-env
```

<!-- Old Instructions for Spack -->
<!--  - Load Spack modules -->
<!-- module purge -->
<!-- module unuse /glade/u/apps/ch/modulefiles/default/compilers -->
<!-- export MODULEPATH_ROOT=/glade/work/jedipara/cheyenne/spack-stack/modulefiles -->
<!-- module use /glade/work/jedipara/cheyenne/spack-stack/modulefiles/compilers -->
<!-- module use /glade/work/jedipara/cheyenne/spack-stack/modulefiles/misc -->
<!-- module load ecflow/5.8.4 -->
<!-- module load miniconda/3.9.12 -->
<!-- ulimit -s unlimited -->
<!-- # GNU specific modules -->
<!-- module use /glade/work/jedipara/cheyenne/spack-stack/spack-stack-v1/envs/skylab-2.0.0-gnu-10.1.0/install/modulefiles/Core -->
<!-- module load stack-gcc/10.1.0 -->
<!-- module load stack-openmpi/4.1.1 -->
<!-- # Intel specific modules -->
<!-- # module use /glade/work/jedipara/cheyenne/spack-stack/spack-stack-v1/envs/skylab-2.0.0-intel-19.1.1.217/install/modulefiles/Core -->
<!-- # module load stack-intel/19.1.1.217 -->
<!-- # module load stack-intel-mpi/2019.7.217 -->
<!-- module load stack-python/3.9.12 -->
<!-- module load jedi-fv3-env/1.0.0 -->
<!-- module load bufr/11.7.1 -->
<!-- # module load jedi-ewok-env/1.0.0 -->
<!-- # module load nco/5.0.6 -->

<!-- # these are needed so WRF-Hydro can build without other modifications -->
<!-- export NETCDF_INC=${netcdf_fortran_ROOT}/include -->
<!-- export NETCDF_LIB=${netcdf_fortran_ROOT}/lib -->
<!-- ``` -->
<!--  - Create Python environment to get [wrfhydropy](https://github.com/NCAR/wrf_hydro_py) package -->
<!-- ```console -->
<!-- $ python3 -m venv ~/[local_path]/env -->
<!-- $ activate ~/[local_path]/env -->
<!-- $ python3 -m pip install wrfhydropy -->
<!-- ``` -->
<!-- Note: for future runs, instead of installing wrfhydopy again you can load the -->
<!--   virtual environment with the following command -->
<!--   `source ~/[local_path]/env/bin/activate`. -->
<!-- It would be good to add that line to the end of the `gnu_spack_env.sh` file, -->
<!--   so the python package gets loaded with `source gnu_spack_env.sh`. -->



<!-- ## Obtain and Build Source Code -->
<!--  - Clone repositories [JCSDA-internal/wrf_hydro_nwm_jedi](https://github.com/JCSDA-internal/wrf_hydro_nwm_jedi) and [NCAR/wrf_hydro_nwm_public](https://github.com/NCAR/wrf_hydro_nwm_public) -->
<!-- ```console -->
<!-- $ git clone git@github.com:JCSDA-internal/wrf_hydro_nwm_jedi.git -->
<!-- $ mkdir wrf_hydro_nwm_jedi/build -->
<!-- $ cd wrf_hydro_nwm_jedi/build -->
<!-- $ ecbuild ../bundle -->
<!-- $ make -j 4 -->
<!-- ``` -->





<!-- # Running -->
<!-- ## Prerequisites -->
<!--  - Python 3 and [wrf_hydro_py](https://github.com/NCAR/wrf_hydro_py) -->
<!--  - [WRF-Hydro/NWM JEDI](https://github.com/JCSDA-internal/wrf_hydro_nwm_jedi) -->
<!--  - [WRF-Hydro](https://github.com/NCAR/wrf_hydro_nwm_public) -->
<!--  - Prepare Experiment Configuration Files -->
<!--    - jedi_workflow.yaml -->
<!--    - jedi.yaml -->
<!--    - WRF-Hydro namelists, to be placed in the WRF-Hydro domain directory -->
<!-- 	 - hrldas_namelists.json -->
<!--      - hydro_namelists.json -->

<!-- ### Prepping YAMLs -->
<!--  - The starting time in `jedi.yaml` is propagated to JEDI and WRF-Hydro YAMLs -->
<!-- during the initilization phase and while the model runs. -->
<!--  - More to be added -->



# Basic JEDI Workflow workflow

```mermaid
graph TD
    A([Initialization])
    A --> B1([Read WRF-Hydro Restart])
    A --> B2([Run WRF-Hydro])
    C([Apply JEDI Filter])
    B1 --> C
    B2 --> C
    C --> D([Increment Restart])
    D --> F([Run WRF-Hydro<br/> Simulation])
    F --> G([Advance Model, <br/> Prep Forecast Files ])
    G -.-> G1([Outside Tool<br/> Able To Run Forecast])
    G --> H([Model Done?])
    H --> yes --> J([Finish])
    H --> no --> C
```


# Miscellaneous Information
## Note
The member directories that are created by wrfhydropy have restart files that
aren't used and may not correspond with the actuals files being used.
The yamls point to the real files being used and those reside in the top
directory, named after the project name.

<!-- ## YAMLs -->
<!-- JEDI Workflow YAML: if the `start_wrf-h_time` and `start_jedi_time` time are -->
<!-- equal, then WRF-Hydro is not run before starting the cycle, only a restart -->
<!-- file is used. -->

## Debugging
If the program fails while running `wrf_hydro_py`, examine the `foo.stdout`
and `foo.stderr` files in the member subdirectories.

<!-- If the program fails or is stopped during the `wrf_hydro_py`, WRF-Hydro may -->
<!-- need to be recompiled. -->

<!-- # Git Submodules -->
<!-- ## Add JEDI increment data to WRF-Hydro data -->
<!-- ### Description -->
<!-- Code is based on the [project AddJediIncr](https://github.com/ClaraDraper-NOAA/AddJediIncr) by Clara Draper and Mike Barlage. -->
<!-- Increment JEDI adds analysis to WRF-Hydro restart files. -->
<!-- Used in conjunction with [WRF-Hydro/NWM JEDI Implementation](https://github.com/JCSDA-internal/wrf_hydro_nwm_jedi). -->
