# Add JEDI increment data to WRF-Hydro data
## Description
Code is based on the [project AddJediIncr](https://github.com/ClaraDraper-NOAA/AddJediIncr) by Clara Draper and Mike Barlage.

Increment JEDI adds analysis to WRF-Hydro restart files.
Used in conjunction with [WRF-Hydro/NWM JEDI Implementation](https://github.com/JCSDA-internal/wrf_hydro_nwm_jedi).

<!-- Currently, only option is to add snow depth increment to the Noah-MP land surface model. -->

## Prerequisites

Load needed Fortran compiler, MPI and NETCDF modules.
For testing `nccmp` will be useful.

## Build
Build with CMake or Makefile.
Running with CMake has the added benefit of being able to run CTest.

#### CMake
Note: `jedi_increment` will be `build/src`.
```
$ mkdir build
$ cd build
$ cmake ../
$ make -j
```

#### Makefile
`$ make` or `$ make build`

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
