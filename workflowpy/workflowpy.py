import argparse
import datetime
import subprocess
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
def pwd():
    return os.getcwd()
def cd(goto):
    os.chdir(goto)
def check_path(path):
    if (path[-1] != '/'):
        path += '/'
    return path


class node:
    def __init__(self):
        self.nodes = 1
        self.ppn = 36


class workflow:
    def __init__(self, args):
        self.start()
        self.parse_arguments(args)
        self.get_resource_info()
        self.print_setup()
        self.setup_experiment()
        self.cycle()
        self.end()

    def cycle(self):
        pprint("Starting Cycling Process")
        print("starting at", self.start_time)
        self.ens_time = self.start_time
        while self.ens_time < self.end_time:
            self.run_jedi()
            self.increment_restarts()
            self.run_ensemble()
            self.advance_ensemble()
        print(" Ending Cycling Process")


    def run_jedi(self):
        pprint('Running JEDI')
        cd(self.jedi_working_dir)

        print("where", pwd())
        # ARTLESS: RUN WHERE?
        cd(self.jedi_output_dir)

        cmd = self.jedi_exe + ' ' + self.jedi_yaml
        print('$', cmd)
        print("PRETENDING TO RUN IN", pwd())
        sys.exittt()

    def run_ensemble(self):
        f_name = self.experiment_file_base + \
            self.ens_time.strftime('%H') + '.nc'
        f = open(f_name, 'w')
        f.close()
        # TODO: Run Ensemble
        # print('$', self.command)
        # subprocess.call([str(self.command)], shell=True)

    def advance_ensemble(self):
        self.ens_time += self.model_ts
        print("advancing to", self.ens_time)

    def get_resource_info(self):
        pprint("TODO: Obtaining resource info")
        # read node file? Use `$ pbsnode`?
        print("Single Cheyenne Node Hardcoded")
        self.node = node()

    # make sure everything is in proper format
    # make sure directories exist
    def setup_experiment(self):
        # make working dir, artless can remove
        if not os.path.isdir(self.jedi_working_dir):
            os.mkdir(self.jedi_working_dir)
        if not os.path.isdir(self.jedi_output_dir):
            os.mkdir(self.jedi_output_dir)
        # make sure JEDI executable is found
        exe = False
        check_exe = self.jedi_build_dir + self.jedi_exe
        if os.path.exists(check_exe):
            exe = check_exe
        check_exe = self.jedi_build_dir + 'bin/' + self.jedi_exe
        if os.path.exists(check_exe):
            exe = check_exe
        if exe == False:
            print("ERROR: unable to find JEDI executable")
        self.jedi_exe = exe
        # self.create_dir_structure()

    # def create_dir_structure(self):
    #     if not os.path.isdir(self.base_dir):
    #         os.mkdir(self.base_dir)

    def parse_arguments(self, args):
        if len(args) > 1:
            self.yaml = args[1]
        self.read_yaml()

    # TODO: what if end_time in different format?
    def read_yaml(self):
        f = open(self.yaml, 'r')
        self.setup = yaml.safe_load(f)
        self.read_jedi_yaml()
        # self.read_yaml_dirs()
        self.read_yaml_file_names()
        self.read_yaml_time()
        self.read_yaml_command()
        # ens_size = int(config['ensemble']['size'])
        f.close()
        pprint("Read Yaml")

    def read_jedi_yaml(self):
        self.jedi_yaml = self.setup['experiment']['jedi']['yaml']
        f = open(self.jedi_yaml, 'r')
        self.jedi_setup = yaml.safe_load(f)
        background = self.jedi_setup['cost function']['background']
        # the following two should be restart files
        self.input_lsm_f = background['filename_lsm']
        self.input_hydro_f = background['filename_hydro']

        jedi = self.setup['experiment']['jedi']
        self.jedi_build_dir = check_path(jedi['build_dir'])
        self.jedi_working_dir = check_path(jedi['working_dir'])
        # self.jedi_output_dir = os.path.dirname(self.jedi_yaml) \
        #     + '/' + self.jedi_output_dir + '/'
        self.jedi_output_dir = check_path(jedi['output_dir'])
        self.jedi_exe = jedi['exe']

        print("ARTLESS: tmp jedi_output_dir")
        # self.jedi_output_dir = check_path(jedi['output'])
        f.close()

    def read_yaml_command(self):
        python = '/glade/u/apps/opt/conda/envs/npl/bin/python3 '
        command = self.setup['experiment']['command']
        # ARTLESS
        self.command = python +  self.jedi_output_dir+'/'+str(command)

    def read_yaml_dirs(self):
        dirs = self.setup['experiment']['dirs']
        self.base_dir = dirs['output_dir']
        # self.build_dir = dirs['build_dir']
        self.experiment_dir = dirs['experiment_dir']
        self.experiment_output_dir = dirs['experiment_output_dir']
        self.init_ensemble_dir = dirs['initial_ensemble_dir']

    def read_yaml_file_names(self):
        f_names = self.setup['experiment']['file_names']
        self.experiment_file_base = f_names['experiment_file_base']

    def read_yaml_time(self):
        time = self.setup['experiment']['time']
        self.start_time = datetime.datetime.strptime(time['start_time'],
                                                   '%Y-%m-%d_%H:%M:%S')
        self.end_time = datetime.datetime.strptime(time['end_time'],
                                                   '%Y-%m-%d_%H:%M:%S')
        self.assim_window_hr = time['assim_window']['hours']
        self.model_ts = datetime.timedelta(hours=time['advance_model_hours'])
        # skip_missing_obs_hours = time['skip_missing_obs_hours']
        # skip_missing_obs_days = time['skip_missing_obs_days']


    def start(self):
        pprint("Starting Workflowpy")

    def end(self):
        pprint("Exiting Workflowpy")

    def print_setup(self):
        pprint("Directories")
        print("Working dir: ", self.jedi_working_dir) #self.run_dir) # ARTLESS
        print("Output dir: ", self.jedi_output_dir) # self.obs_dir) ARTLESS
        # print("ens_size: ", self.ens_size)


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

# if __name__ == "__main__":
