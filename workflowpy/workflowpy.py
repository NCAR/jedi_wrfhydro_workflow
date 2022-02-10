import argparse
from copy import deepcopy
import datetime
import subprocess
import re
import shutil
import sys
import os
import wrfhydropy
import yaml

# -- todo ---
# * update yamls along the way, in advance_ensemble
# * wrfhydropy
# * read resource info using CLI
# * make parse_arguments less brittle
def exit(message):
    print("Error: ", message)
    sys.exit()
def pprint(string):
    delim = '---'
    print(delim,'\n',string)
    # print(delim)
def pwd():
    return os.getcwd()
def cd(goto):
    os.chdir(goto)
def check_dir(dir_path):
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
def check_path(path):
    if (path[-1] != '/'):
        path += '/'
    return path
def check_wrf_h_path(path: str) -> str:
    path = check_path(path)
    if path.endswith('trunk/NDHMS/Run/'):
        pass
    elif path.endswith('trunk/NDHMS/'):
        path += 'Run/'
    elif path.endswith('trunk/'):
        path += 'NDHMS/Run/'
    else:
        path += 'trunk/NDHMS/Run/'
    if not os.path.isdir(path):
        exit("WRF-Hydro path: " + path + " not found")
    return path


class filename:
    def __init__(self, fullpath, dt):
        self.fullpath = fullpath
        self.filename = os.path.basename(fullpath)
        self.previousfilename = ''
        self.dirname = os.path.basename(fullpath) + '/'
        reg_s = '[1-9][0-9]{3}[0-1][0-9][0-3][0-9][0-2][0-4]'
        s = re.search(reg_s, self.filename)
        self.filebase = self.filename[:s.start()]
        self.fileend = self.filename[s.end():]
        date_s = self.filename[s.start():s.end()]
        self.incrementfilename = self.filename + '.increment'
        self.date = datetime.datetime.strptime(date_s,'%Y%m%d%H')
        self.dt = dt

    def advance(self):
        self.previousfilename = self.filename
        self.date += self.dt
        self.filename = self.filebase + \
            self.date.strftime('%Y%m%d%H') + \
            self.fileend
        self.fullpath = self.dirname + self.filename
        self.incrementfilename = self.filename + '.increment'

    def moveto(self, topath):
        self.dirname = check_path(topath)
        shutil.copy(self.fullpath, self.dirname)
        self.fullpath = self.dirname + self.filename

    def append(self, postfix):
        self.fullpath += postfix
        self.filename += postfix
        self.fileend += postfix


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
        print(" starting at", self.start_time)
        self.ens_time = self.start_time
        while self.ens_time < self.end_time:
            self.run_filter()
            self.increment_restart()
            self.run_ensemble()
            self.advance_model()
        print(" Ending Cycling Process")


    def end(self):
        pprint("Exiting Workflowpy")
        sys.exittt()


    def run_ensemble(self):
        pprint('Running ensemble WRF-Hydro')
        # cd(self.jedi_output_dir)
        cd(self.workflow_work_dir)
        f_name = self.experiment_file_base + \
            self.ens_time.strftime('%H') + '.nc'
        #     f = open(f_name, 'w')
        #     f.close()
        cmd = [self.wrf_h_exe, f_name]
        self.run(cmd)
        # shutil.copy(self.lsm_filename, self.input_lsm_f_name +'.increment')


    def increment_restart(self):
        pprint('Incrementing restarts')
        cd(self.workflow_work_dir)
        cmd = [self.increment_exe,
               self.lsm_file.filename,
               self.lsm_file.incrementfilename]
        self.run(cmd)

    def run_filter(self):
        pprint('Running JEDI filter')
        cd(self.workflow_work_dir)
        # TODO: RUN WHERE?
        # cd(self.jedi_output_dir)
        cmd = [self.jedi_exe, self.jedi_yaml]
        self.run(cmd)

        # TODO
        shutil.copy(self.lsm_file.filename, self.lsm_file.incrementfilename)
        print("NEED TO MV NEW FILE, UPDATE YAMLS")
        # sys.exittt()

        # sys.exittt()
# def run_filter(run_dir: pathlib.Path,nproc: int, cmd: str,
# ):
#     # TODO (JLM): right now hostname is just the master node.
#     cmd_to_run = cmd.format(
#         **{'hostname':hostname,
#            'nproc': nproc,
#            'cmd': './filter'
#            }
#     )
#     proc = subprocess.run(shlex.split(cmd_to_run), cwd=str(run_dir))
#     if proc.returncode != 0:
#         raise ValueError('Filter did not return 0')


    def advance_model(self):
        self.ens_time += self.model_dt
        pprint("Advancing to " + str(self.ens_time))
        self.lsm_file.advance()
        shutil.copy(self.lsm_file.previousfilename, self.lsm_file.filename)
        # self.jedi_yaml = self.setup['experiment']['jedi']['yaml']
        # f = open(self.jedi_yaml, 'r')
        # self.jedi_setup = yaml.safe_load(f)
        # f.close()

    def get_resource_info(self):
        pprint("TODO: Obtaining resource info")
        # read node file? Use `$ pbsnode`?
        print("Single Cheyenne Node Hardcoded")
        self.node = node()

    # make sure everything is in proper format
    # make sure directories exist
    def setup_experiment(self):
        check_dir(self.workflow_work_dir)
        check_dir(self.jedi_working_dir)
        check_dir(self.jedi_output_dir)

        # collect starting files
        self.lsm_file.moveto(self.workflow_work_dir)
        # shutil.copy(self.input_hydro_f_path, self.workflow_work_dir)
        shutil.copy(self.jedi_yaml, self.workflow_work_dir)
        self.jedi_yaml = self.workflow_work_dir + '/' + \
            os.path.basename(self.jedi_yaml) # TODO: improve

        # update jedi yaml with copied files
        f = open(self.jedi_yaml, 'r')
        jedi_setup = yaml.safe_load(f)
        background = jedi_setup['cost function']['background']
        background['filename_lsm'] = self.lsm_file.fullpath
        # background['filename_hydro'] = self.workflow_work_dir + '/' + \
        #     self.input_hydro_f_name
        f.close()

        self.write_jedi_yaml(jedi_setup)

        # make sure JEDI executable is found
        # handeled by CMAKE
        # exe = False
        # check_exe = self.jedi_build_dir + self.jedi_exe
        # if os.path.exists(check_exe):
        #     exe = check_exe
        # check_exe = self.jedi_build_dir + 'bin/' + self.jedi_exe
        # if os.path.exists(check_exe):
        #     exe = check_exe
        # if exe == False:
        #     print("ERROR: unable to find JEDI executable")
        # self.jedi_exe = exe
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
        self.read_yaml_time()
        self.read_jedi_yaml()
        self.read_wrf_hydro_yaml()
        self.read_yaml_dirs()
        self.read_yaml_file_names()
        # self.read_yaml_command() Don't need??
        # ens_size = int(config['ensemble']['size'])
        f.close()
        pprint("Read Yaml")

    def read_wrf_hydro_yaml(self):
        self.wrf_h_yaml = self.setup['experiment']['wrf_hydro']
        self.wrf_h_build_dir = check_wrf_h_path(self.wrf_h_yaml['build_dir'])
        self.wrf_h_exe = self.wrf_h_build_dir + self.wrf_h_yaml['exe']
        if not os.path.isfile(self.wrf_h_exe):
            exit("wrf_hydro.exe no found in " + self.wrf_h_build_dir)

    def read_jedi_yaml(self):
        self.jedi_yaml = self.setup['experiment']['jedi']['yaml']
        f = open(self.jedi_yaml, 'r')
        jedi_setup = yaml.safe_load(f)
        background = jedi_setup['cost function']['background']
        # the following two should be restart files
        self.lsm_file = filename(background['filename_lsm'], self.model_dt)
        # self.hydro_f = filename(background['filename_hydro'], self.model_dt)


        jedi = self.setup['experiment']['jedi']
        self.jedi_build_dir = check_path(jedi['build_dir'])
        self.jedi_working_dir = check_path(jedi['working_dir'])
        # self.jedi_output_dir = os.path.dirname(self.jedi_yaml) \
        #     + '/' + self.jedi_output_dir + '/'
        self.jedi_output_dir = check_path(jedi['output_dir'])
        self.jedi_exe = jedi['exe']

        print("TODO/NOTE: tmp jedi_output_dir")
        # self.jedi_output_dir = check_path(jedi['output'])
        f.close()

    def read_yaml_command(self):
        python = '/glade/u/apps/opt/conda/envs/npl/bin/python3 '
        command = self.setup['experiment']['command']
        # TODO: double check '/' needed
        self.command = python +  self.jedi_output_dir+'/'+str(command)

    def read_yaml_dirs(self):
        self.workflow_work_dir = self.setup['experiment']['workflow_work_dir']
        # dirs = self.setup['experiment']['dirs']
        # self.base_dir = dirs['output_dir']
        # # self.build_dir = dirs['build_dir']
        # self.experiment_dir = dirs['experiment_dir']
        # self.experiment_output_dir = dirs['experiment_output_dir']
        # self.init_ensemble_dir = dirs['initial_ensemble_dir']

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
        self.model_dt = datetime.timedelta(hours=time['advance_model_hours'])
        # skip_missing_obs_hours = time['skip_missing_obs_hours']
        # skip_missing_obs_days = time['skip_missing_obs_days']


    def run(self, cmd):
        print('$', ' '.join(map(str,cmd)))
        # out = subprocess.run(cmd,  # capture_output=True
        #                      stdout=subprocess.PIPE,
        #                      stderr=subprocess.STDOUT)
        # print("| ", out.stdout)

    def start(self):
        pprint("Starting Workflowpy")
        self.increment_exe = os.getenv('JEDI_INCREMENT')
        self.increment_exe = os.getenv('FOOBAR')
        self.increment_exe = \
            '/glade/u/home/soren/src/jedi/incrementJedi/bin/jedi_increment'
        print("increment exe", self.increment_exe)
        print("FIX AT SOME POINT")

    def print_setup(self):
        pprint("Directories")
        print("Working dir: ", self.jedi_working_dir) #self.run_dir) # CHANGE
        print("Output dir: ", self.jedi_output_dir) # self.obs_dir)  # BACK?
        # print("ens_size: ", self.ens_size)


    def write_jedi_yaml(self, yaml_output):
        f = open(self.jedi_yaml, 'w')
        yaml.dump(yaml_output, f)
        f.close()




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
