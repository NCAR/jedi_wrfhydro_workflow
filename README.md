# JEDI Workflow
A framework providing a workflow between WRF-Hydro/NWM JEDI and WRF-Hydro.

## Prerequisites
 - Python 3 and [wrf_hydro_py](https://github.com/NCAR/wrf_hydro_py)
 - [WRF-Hydro/NWM JEDI](https://github.com/JCSDA-internal/wrf_hydro_nwm_jedi)
 - [Add JEDI Increment](https://github.com/scrasmussen/add_jedi_increment)
 - [WRF-Hydro](https://github.com/NCAR/wrf_hydro_nwm_public)
 - Prepare Experiment Configuration Files
   - jedi_workflow.yaml
   - jedi.yaml
   - WRF-Hydro namelists, to be placed in the WRF-Hydro domain directory
	 - hrldas_namelists.json
     - hydro_namelists.json

### Prepping YAMLs
 - The starting time in `jedi.yaml` is propagated to JEDI and WRF-Hydro YAMLs
during the initilization phase and while the model runs.
 - More to be added


## Running
`$ python3 jedi_workflowpy.py jedi_workflow.yaml`


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


## YAMLs
JEDI Workflow YAML: if the `start_wrf-h_time` and `start_jedi_time` time are
equal, then WRF-Hydro is not run before starting the cycle, only a restart
file is used.

## Debugging
If the program fails while running `wrf_hydro_py`, examine the `foo.stdout`
and `foo.stderr` files in the member subdirectories.

If the program fails or is stopped during the `wrf_hydro_py`, WRF-Hydro may
need to be recompiled.


# Add JEDI increment data to WRF-Hydro data
## Description
Code is based on the [project AddJediIncr](https://github.com/ClaraDraper-NOAA/AddJediIncr) by Clara Draper and Mike Barlage.

Increment JEDI adds analysis to WRF-Hydro restart files.
Used in conjunction with [WRF-Hydro/NWM JEDI Implementation](https://github.com/JCSDA-internal/wrf_hydro_nwm_jedi).

## Prerequisites

Load needed Fortran compiler, MPI and NETCDF modules.
For testing `nccmp` will be useful.

## CMake Build
Note: `jedi_increment` will be `build/src`.
```
$ mkdir build
$ cd build
$ cmake ../
$ make -j
```

## Run

`$ ./jedi_increment RESTART.FILE RESTART.FILE.INCREMENTED`

## Test
If you chose to build with CMake you will now be able to run CTest with added
  report functionality.
CTest will run `jedi_increment` with two data sets that have modified `SNOWH`
  or `SNEQV` variables.
The command `$ make report` will compare the two modified RESTART files.

```
$ ctest
Test project /glade/u/home/soren/src/jedi/add_jedi_increment/build
    Start 1: hello_world
1/3 Test #1: hello_world ......................   Passed    0.03 sec
    Start 2: increment_SNOWH_test
2/3 Test #2: increment_SNOWH_test .............   Passed    0.73 sec
    Start 3: increment_SNEQV_test
3/3 Test #3: increment_SNEQV_test .............   Passed    0.72 sec

100% tests passed, 0 tests failed out of 3

Total Test time (real) =   1.49 sec

$ make report
nccmp -dfqsS tests/RESTART.2017010100_DOMAIN1.test1 tests/RESTART.2017010100_DOMAIN1.test2
Variable Group Count     Sum  AbsSum     Min        Max       Range    Mean      StdDev
ZSNSO    /      3600    -360     360    -0.1 -0.0999999 2.38419e-07    -0.1 6.21742e-08
SNICE    /       720 17661.5 17661.5 22.0679    28.0961     6.02827 24.5299     1.33927
SNEQVO   /       720 17661.5 17661.5 22.0679    28.0961     6.02827 24.5299     1.33927
SNEQV    /       720 17661.5 17661.5 22.0679    28.0961     6.02827 24.5299     1.33927
SNOWH    /       720      72      72     0.1        0.1 5.96046e-08     0.1 1.50763e-08
```
