jedi_workflow=../../src/jedi_workflowpy/jedi_workflowpy.py
jedi_workflow_yaml=jedi_workflow_LETKFOI_SWE.yaml

all: run


run:
	python3 $(jedi_workflow) $(jedi_workflow_yaml)
