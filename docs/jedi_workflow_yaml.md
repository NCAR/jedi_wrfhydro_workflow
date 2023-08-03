# README for jedi_workflow.yaml
This yaml file tells the workflow information about the model run. Here is an example [yaml file](../examples/jedi_workflow.yaml "jedi_workflow.yaml"). Further details about the yaml key-value options are described below.


# Experiment Key Section
```yaml
expirement:
  name: 'foo'
  num_p: 36
  compiler: gnu
  workflow_work_dir: path/to/work_dir
```
- `name`: The `name` key holds the expirement name that the output directory structure will be based on.
In this example the directory `foo_sub_gnu_1p` will be created in the `workflow_work_dir` directory.
The daily outputs will be written to a `fooYYYYMMDDhh` subdirectory.
- `num_p`: this is the number of processors that wrfhydropy will use to run MPI.
- `compiler`: available compilers are `GNU` and `Intel`.
- `workflow_work_dir`: where the workflow will create the directory with the worklow's output.

The expirement section also has the following keys
- `init`: has key-value pairs that point to restart and observation directories.
- `jedi`: has key-value pairs that choose the JEDI method to be used.
- `increment`: variable name that will be incremented, either `snowh` or `sneqv`.
- `wrf_hydro`: points to WRF-Hydro source and domain directory, the YAML files, and version and config values.
- `time`: key-value pairs describing the start and end times of the Jedi workflow.

# Init Key Section
```yaml
init:
  restart_dir: /path/to/restarts
  obs_dir: /path/to/obs
```
- `restart_dir`: this points to the restarts that WRF-Hydro can use to start the model.
- `obs_dir`: this points to the observations that Jedi uses.

# Jedi Key Section
```yaml
method: jedi-method-name
LETKF-OI:
hofx:
3dvar:
```
- `method`: the options are LETKF-OI, hofx, or 3dvar. Based on this choice that method in Jedi will be run.

## LETKF-OI, hofx, 3dvar Sections
```yaml
exe: /path/to/wrf_hydro_nwm_method.x
yaml: /path/to/method.yaml
increment: True or False
```
The LETKF-OI key also have the following.
```yaml
vars:
  SNOWH: 0.02121
  SNEQV: 21.21*0.25
```

# Increment Key Section
```yaml
exe: /path/to/jedi_increment
var: snowh or sneqv
```
The `var` value to increment can be `snowh` or `sneqv`.

# WRF-Hydro Key Section
```yaml
wrf_hydro:
  src_dir: /path/to/wrf_hydro
  domain_dir: /path/to/domain
  hydro_json: /path/to/json
  hrldas_json: /path/to/json
  hydro_patches: /path/to/json
  hrldas_patches: /path/to/json
  version: vX.Y.Z
  config: config_str
```
- `src_dir`: this is the path to WRF-Hydro source directory that wrfhydropy will build to use the executable.
- `domain_dir`: directory to the domains that WRF-Hydro will use. These will be symlinked during runtime.
- `hydro_json`: hydro json options.
- `hrldas_json`: hrldas json options.
- `hydro_patches`: hydro json patches to hydro json.
- `hrldas_patches`: hrldas json patches to hrldas json.
- `version`: version number, e.g. 'v5.2.0'
- `config`: configuration choice for jsons

# Time Key Section
```yaml
time:
  start_wrf-h_time: YYYY-MM-DD_hh:mm:ss
  start_jedi_time:  YYYY-MM-DD_hh:mm:ss
  end_time:         YYYY-MM-DD_hh:mm:ss
  assim_window:
    hours: 24
  advance_model_hours: 24
```
- `start_wrf-h_time`: start time in YYYY-MM-DD_hh:mm:ss format.
- `start_jedi_time`: start time in YYYY-MM-DD_hh:mm:ss format.
- `end_time`: end time in YYYY-MM-DD_hh:mm:ss format.
- `hours`: This currently needs to be 24.
- `advance_model_hours`: This currently needs to be 24.

Note: the Jedi and WRF-Hydro start times currently need to be the same.
