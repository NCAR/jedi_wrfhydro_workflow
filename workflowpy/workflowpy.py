import argparse
# from hydrodartpy import setup_experiment
import sys
import os
import yaml

# -- todo ---
# * read resource info using CLI
# * make parse_arguments less brittle
def pprint(string):
    delim = '---'
    print(delim,'\n',string)
    # print(delim)

class node:
    def __init__(self):
        self.nodes = 1
        self.ppn = 36

class workflow:
    def __init__(self, args):
        self.start()
        self.parse_arguments(args)
        self.get_resource_info()
        self.setup_experiment()
        self.cycle()
        self.end()

    def cycle(self):
        pprint("Starting Cycling Process")
        print("Ending Cycling Process")


    def get_resource_info(self):
        pprint("TODO: Obtaining resource info")
        # read node file? Use `$ pbsnode`?
        print("Single Cheyenne Node Hardcoded")
        self.node = node()

    def setup_experiment(self):
        self.read_yaml()
        self.create_dir_structure()

    def create_dir_structure(self):
        if not os.path.isdir(self.base_dir):
            os.mkdir(self.base_dir)

    def parse_arguments(self, args):
        if len(args) > 1:
            self.yaml = args[1]

    def read_yaml(self):
        f = open(self.yaml, 'r')
        self.setup = yaml.safe_load(f)
        self.base_dir = self.setup['experiment']['output_dir']
        pprint("Read Yaml")

    def start(self):
        pprint("Starting Workflowpy")

    def end(self):
        pprint("Exiting Workflowpy")




    # Arguments to this script.
    # # python setup_experiment.py --help
    # the_desc = "Setup a WRF-Hydro-DART experiment."
    # the_epilog = """
    # Additional Examples:
    # regular: python setup_experiment.py experiment_config_files/test_exp.yaml
    # debug:  ipython --pdb -c "%run setup_experiment.py experiment_config_files/test_exp.yaml"
    # """
    # parser = argparse.ArgumentParser(
    #     description=the_desc,
    #     formatter_class=argparse.RawDescriptionHelpFormatter,
    #     epilog=the_epilog
    # )

    # # Single positional argument is config_file
    # parser.add_argument(
    #     'config_file',
    #     metavar='config_file.yaml',
    #     type=str,
    #     nargs=1,
    #     help='The YAML experiment configuration file of arbitrary name.'
    # )
    # args = parser.parse_args()

    # return_code = setup_experiment(config_file=args.config_file[0])

    # sys.exit(return_code)

    print("fin")

# if __name__ == "__main__":
