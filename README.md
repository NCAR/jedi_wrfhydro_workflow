# Increment JEDI with data from WRF-Hydro
## Description
Code is based on the project AddJediIncr by Clara Draper and Mike Barlage,
https://github.com/ClaraDraper-NOAA/AddJediIncr


Increment JEDI analysis to WRF-Hydro restart files, implemented by Soren Rasmussen (NCAR).
Used in conjunction with [WRF-Hydro/NWM JEDI Implementation](https://github.com/JCSDA-internal/wrf_hydro_nwm_jedi)

<!-- Currently, only option is to add snow depth increment to the Noah-MP land surface model. -->

## Run

1. Load needed modules

2. Build
`$ make` or `$ make build`

3. Run
`$ ./jedi_increment RESTART.FILE RESTART.FILE.INCREMENTED`
