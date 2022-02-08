# Add JEDI increment data to WRF-Hydro data
## Description
Code is based on the [project AddJediIncr](https://github.com/ClaraDraper-NOAA/AddJediIncr) by Clara Draper and Mike Barlage.

Increment JEDI adds analysis to WRF-Hydro restart files.
Used in conjunction with [WRF-Hydro/NWM JEDI Implementation](https://github.com/JCSDA-internal/wrf_hydro_nwm_jedi).

<!-- Currently, only option is to add snow depth increment to the Noah-MP land surface model. -->

## Run

1. Load needed modules

2. Build

`$ make` or `$ make build`

3. Run

`$ ./jedi_increment RESTART.FILE RESTART.FILE.INCREMENTED`
