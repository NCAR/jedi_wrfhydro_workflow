jedi_workflow=../../src/jedi_workflowpy/jedi_workflowpy.py
jedi_swe_yaml=jedi_workflow_LETKFOI_SWE.yaml
jedi_snowh_yaml=jedi_workflow_LETKFOI_SNOWH.yaml

all: swe snowh

swe:
	python3 $(jedi_workflow) $(jedi_swe_yaml)

snowh:
	python3 $(jedi_workflow) $(jedi_snowh_yaml)
