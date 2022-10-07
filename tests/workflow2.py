import os
import sys
from pathlib import Path
sys.path.append(str(Path(os.getcwd()).parents[1]) + '/src/jedi_workflowpy')
import jedi_workflowpy as wfp


# workflow = wfp.Workflow(sys.argv)
# workflow = wfp.Workflow.parse_arguments(foobar, sys.argv)

print("success")
# break_right_here()
