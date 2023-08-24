# Expirement Setup
There are two YAML files required to run the workflow: `jedi_workflow.yaml` and a YAML file for the chosen DA method within JEDI (e.g., LETKF).
The workflow and Jedi will read these documents to configure the experiment.

## YAML Files
### `jedi_workflow.yaml` file
This is the base yaml that will be passed to `jedi_workflow.py` at runtime.
For more information on this document see [the documentation](jedi_workflow_yaml.md "jedi workflow yaml doc")

### `jedi.yaml` file
Currently, there are multiple choices of the DA method within the JEDI system that users can pick, such as `LETKF-OI`, `hofx`, or `3dvar`.
We are going to explore and explain one sample of `LETKF-OI` .yaml file as part of this documentation. This file is also named as `jedi_workflow_LETKFOI.yaml` in our workflow testcase set.
For more information see [the documentation](YAML_files.md "jedi yaml config")

## JSON Files
There are four JSON files that are used by WRF-Hydro during runtime. This section is to be expanded upon.
