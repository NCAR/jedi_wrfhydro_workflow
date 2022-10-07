import argparse
import os
import sys
from pathlib import Path
sys.path.append(str(Path(os.getcwd()).parents[1]) + '/src/jedi_workflowpy')
import jedi_workflowpy

if __name__ == "__main__":
    print("success")
