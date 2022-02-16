import argparse
from copy import deepcopy
import datetime
import os
from pathlib import Path
import pickle
import re
import subprocess
import shutil
import sys
import wrfhydropy
import yaml
# rm after dev finished
import logging

dry=False
# -- todo ---
# * update yamls along the way, in advance_ensemble
# * exit if incrementing fails
# * wrfhydropy
# * read resource info using CLI
# * make parse_arguments less brittle
# ** hard coded for specific case
class workflow:
    def __init__(self, args):
        pprint('Starting Workflowpy', 0)
        self.init(args)
        self.cycle()
        self.end()


    def cycle(self):
        pprint("Starting Cycling Process", 1)
        print(" starting at", self.time.start)
        while self.time.current < self.time.end:
            self.run_filter()
            self.increment_restart()
            self.run_ensemble()
            self.advance_model()
        print(" Ending Cycling Process")


    def end(self):
        pprint("Exiting Workflowpy", 1)
        sys.exit()


    def run_ensemble(self):
        pprint('Running ensemble WRF-Hydro', 2)

        cd(self.workflow_work_dir)
        ensemble = wrfhydropy.EnsembleSimulation()
        ensemble.add(self.simulation)
        ensemble.replicate_member(1)

        job = wrfhydropy.Job(
            self.name,
            self.time.current_s,
            self.time.future_s,
            exe_cmd = self.wrf_h_exe,
            restart_dir = self.workflow_work_dir,
            restart_file_time = self.time.current_s,
            restart = True
            # str(self.time.current).replace(' ','_'),
            # str(self.time.future).replace(' ','_')
        )

        current_work_dir = self.name+shorten(self.time.current_s)
        os.mkdir(current_work_dir)
        cd(current_work_dir)

        ensemble.add(job)
        ensemble.compose()

        if (dry):
            print("WARNING: PRETENDING TO RUN RIGHT NOW")
            cmd = [self.wrf_h_exe] #, f_name]
            self.run(cmd)
        else:
            ensemble.run()


    def increment_restart(self):
        if (self.jedi_increment):
            pprint('Incrementing restarts', 2)
            cd(self.workflow_work_dir)
            cmd = [self.increment_exe,
                   self.lsm_file.filename,
                   # self.lsm_file.incrementfilename]
                   self.jedi_output_file]
            self.run(cmd)
        else:
            pprint('Not incrementing restarts', 2)


    def run_filter(self):
        pprint('Running JEDI filter', 2)
        cd(self.workflow_work_dir)
        cmd = [self.jedi_exe, self.jedi_yaml.fullpath]
        self.run(cmd)


    def advance_model(self):
        pprint("Advancing to " + str(self.time.future), 2)
        self.time.advance()
        self.lsm_file.advance()
        self.hydro_file.advance()

        cd(self.workflow_work_dir)
        shutil.copy(self.lsm_file.previousfilename, self.lsm_file.filename)
        shutil.copy(self.hydro_file.previousfilename, self.hydro_file.filename)

        put_yaml_key(self.jedi_setup, 'filename_lsm', self.lsm_file.fullpath)
        put_yaml_key(self.jedi_setup, 'filename_hydro',
                     self.hydro_file.fullpath)
        with open(self.jedi_yaml.fullpath, 'w') as f:
            yaml.dump(self.jedi_setup, f)

    def get_resource_info(self):
        pprint("TODO: Obtaining resource info", 2)
        # read node file? Use `$ pbsnode`?
        print("Single Cheyenne Node Hardcoded")
        self.node = node()

    # make sure everything is in proper format
    # make sure directories exist
    def setup_experiment(self):
        # check directories, create if they don't exist
        check_dir(self.workflow_work_dir)
        # collect starting files
        self.lsm_file.moveto(self.workflow_work_dir)
        self.hydro_file.moveto(self.workflow_work_dir)
        self.jedi_yaml.moveto(self.workflow_work_dir)

        # update jedi yaml with copied files
        with open(self.jedi_yaml.fullpath, 'r') as f:
            self.jedi_setup = yaml.safe_load(f)
        put_yaml_key(self.jedi_setup, 'filename_lsm', self.lsm_file.fullpath)
        put_yaml_key(self.jedi_setup, 'filename_hydro',
                     self.hydro_file.fullpath)

        # make obsfile output local
        for key,val in self.jedi_setup['observations'][0].items():
            if key == 'obs space':
                for key2,val2 in val.items():
                    if key2 == 'obsdataout':
                        val[key2]['obsfile'] = \
                            os.path.basename(val[key2]['obsfile'])
                        self.jedi_output_file = val[key2]['obsfile']
        with open(self.jedi_yaml.fullpath, 'w') as f:
            yaml.dump(self.jedi_setup, f)

        self.setup_wrfhydropy()

    # setup simulation
    def setup_wrfhydropy(self):
        config = self.wrf_h_config

        model = wrfhydropy.Model(
            source_dir = self.wrf_h_build_dir,
            compiler = 'gfort',
            compile_options={'WRF_HYDRO_NUDGING': 0},
            model_config=config
        )
        if (self.workflow_wrf_dir.exists()):
            with open(self.workflow_wrf_dir / 'WrfHydroModel.pkl', 'rb') as f:
                model = pickle.load(f)
        else:
            model.compile(str(self.workflow_wrf_dir))
        hydro_f = self.wrf_h_domain_dir + 'hydro_namelists.json'
        hrldas_f = self.wrf_h_domain_dir + 'hrldas_namelists.json'
        print('Using', hydro_f)
        print('Using', hrldas_f)
        domain = \
            wrfhydropy.Domain(self.wrf_h_domain_dir,
                              config,
                              self.wrf_h_version,
                              hydro_f,
                              hrldas_f)
                              # 'hydro_namelists.json',
                              # 'hrldas_namelists.json')
        simulation = wrfhydropy.Simulation()
        simulation.add(model)
        simulation.add(domain)
        # self.simulation_pickle_f = self.workflow_work_dir + '/sim.pickle'
        # simulation.pickle(self.simulation_pickle_f)
        self.simulation = simulation
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
        else:
            print("ERROR: didn't pass jedi workflow yaml")
            sys.exit()

    # TODO: what if end_time in different format?
    def read_yamls(self):
        pprint("Reading yamls", 2)
        f = open(self.yaml, 'r')
        self.setup = yaml.safe_load(f)
        self.read_yaml_time()
        self.read_jedi_yaml()
        self.read_increment_exe()
        self.read_yaml_wrf_hydro()
        self.read_yaml_dirs()
        # self.read_yaml_file_names()
        self.name = self.setup['experiment']['name']
        f.close()

    def read_yaml_wrf_hydro(self):
        self.wrf_h_yaml = self.setup['experiment']['wrf_hydro']
        self.wrf_h_build_dir = check_wrf_h_build_path(self.wrf_h_yaml['build_dir'])
        self.wrf_h_run_dir = check_wrf_h_run_path(self.wrf_h_yaml['build_dir']
                                                  + '/trunk/NDHMS/Run')
        self.wrf_h_exe = self.wrf_h_run_dir + self.wrf_h_yaml['exe']
        self.wrf_h_domain_dir = self.wrf_h_yaml['domain_dir']
        if not os.path.isfile(self.wrf_h_exe):
            exit("wrf_hydro.exe no found in " + self.wrf_h_build_dir)
        self.wrf_h_version = self.wrf_h_yaml['version']
        self.wrf_h_config = self.wrf_h_yaml['config']

    def read_increment_exe(self):
        self.increment_exe = self.setup['experiment']['increment']['exe']

    def read_jedi_yaml(self):
        self.jedi_yaml = yaml_filename(self.setup['experiment']['jedi']['yaml'])
        f = open(self.jedi_yaml.fullpath, 'r')
        jedi_setup = yaml.safe_load(f)
        filename_lsm = get_yaml_key(jedi_setup, 'filename_lsm')
        self.lsm_file = filename(filename_lsm, self.time.dt)
        # should recursive search to filename_lsm
        filename_hydro = get_yaml_key(jedi_setup, 'filename_hydro')
        self.hydro_file = filename(filename_hydro, self.time.dt,
                                   '%Y-%m-%d_%H:%M')
                                   # self.model_dt, '%Y-%m-%d_%H:%M:%S')
        jedi = self.setup['experiment']['jedi']
        self.jedi_build_dir = check_path(jedi['build_dir'])
        self.jedi_increment = jedi['increment']


        full_exe_path = self.jedi_build_dir + 'bin/'+ jedi['exe']
        if (os.path.exists(jedi['exe'])):
            self.jedi_exe = jedi['exe']
        elif (os.path.exists(full_exe_path)):
            self.jedi_exe = full_exe_path
        else:
            exit("Couldn't find jedi executable in build dir or full path if given")

        f.close()


    def read_yaml_dirs(self):
        self.workflow_work_dir = self.setup['experiment']['workflow_work_dir']
        self.workflow_wrf_dir = Path(self.workflow_work_dir +
                                     '/wrf_hydro_exe/')


    def read_yaml_time(self):
        time = self.setup['experiment']['time']
        self.time = workflowpy_time(time)


    def run(self, cmd):
        print('$', ' '.join(map(str,cmd)))
        if dry:
            return
        out = subprocess.run(cmd,  # capture_output=True
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             check=False)
        if out.stdout != None:
            print("output")
            print(out.stdout.decode("utf-8"))
        if out.stderr != None:
            print("error")
            print(out.stderr.decode("utf-8"))
        print("---")
        # print("| ", out.stderr)

    def init(self, args):
        pprint("Initializing Workflowpy", 1)
        self.parse_arguments(args)
        self.get_resource_info() # todo: one node hard coded
        self.read_yamls()
        self.print_setup()
        self.setup_experiment()  # need to create structure
        pprint("Finished Initializing Workflowpy", 1)

    def print_setup(self):
        pprint("Setup", 2)
        print("Working dir: ", self.workflow_work_dir)
        print("WRF-Hydro exe:, ", self.wrf_h_exe)



def get_yaml_key(yaml_tree, get_key):
    found = False
    for key, val in yaml_tree.items():
        if (key == get_key):
            return(val)
        elif (type(val) == dict) and found == False:
            found = get_yaml_key(val, get_key)
    return found
def put_yaml_key(yaml_tree, put_key, put_val):
    found = False
    for key, val in yaml_tree.items():
        if (key == put_key):
            yaml_tree[put_key] = put_val
            return True
        elif (type(val) == dict) and found == False:
            found = put_yaml_key(val, put_key, put_val)
    return found


def exit(message):
    print("Error: ", message)
    sys.exit()
def pprint(string, level):
    delim = '-' + '-' * (level) * 2
    print(delim,'\n',string)
    # print(delim)
def shorten(string):
    return string[:-4]
def pwd():
    return os.getcwd()
def cd(goto):
    os.chdir(goto)
def check_dir(dir_path):
    if not os.path.isdir(dir_path):
        print('creating', dir_path)
        os.makedirs(dir_path)
    else:
        print(dir_path, 'exists')
def check_path(path):
    if (path[-1] != '/'):
        path += '/'
    return path
def check_wrf_h_run_path(path: str) -> str:
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

def check_wrf_h_build_path(path: str) -> str:
    path = check_path(path)
    if path.endswith('trunk/NDHMS/'):
        pass
    elif path.endswith('trunk/'):
        path += 'NDHMS/'
    else:
        path += 'trunk/NDHMS/'
    if not os.path.isdir(path):
        exit("WRF-Hydro path: " + path + " not found")
    return path

class workflowpy_time:
    in_fmt = '%Y-%m-%d_%H:%M:%S'
    out_fmt = '%Y%m%d%H%M%S'
    def __init__(self, time):
        self.start = datetime.datetime.strptime(time['start_time'],
                                                workflowpy_time.in_fmt)
        self.end = datetime.datetime.strptime(time['end_time'],
                                              workflowpy_time.in_fmt)
        self.assim_window_hr = time['assim_window']['hours']
        self.dt = datetime.timedelta(hours=time['advance_model_hours'])
        self.prev = self.start - self.dt
        self.current = self.start
        self.future = self.start + self.dt
        self.stringify()
    def advance(self):
        self.prev += self.dt
        self.current += self.dt
        self.future += self.dt
        self.stringify()
    def stringify(self):
        self.prev_s = self.prev.strftime(workflowpy_time.out_fmt)
        self.current_s = self.current.strftime(workflowpy_time.out_fmt)
        self.future_s = self.future.strftime(workflowpy_time.out_fmt)
        # self.t = t
        # self.dt = dt
        # self.next_t = t + dt
        # self.prev_t = t - dt

class yaml_filename:
    def __init__(self, fullpath):
        self.filename = os.path.basename(fullpath)
        self.fullpath = fullpath
    def moveto(self, topath):
        old_fullpath = self.fullpath
        dirname = check_path(topath)
        shutil.copy(self.fullpath, dirname)
        self.fullpath = dirname + self.filename
        print('copied', old_fullpath, 'to', self.fullpath)

class filename:
    def __init__(self, fullpath, dt, dt_format='%Y%m%d%H'):
        self.fullpath = fullpath
        self.filename = os.path.basename(fullpath)
        self.previousfilename = ''
        self.dirname = os.path.basename(fullpath) + '/'
        if dt_format == '%Y%m%d%H':
            reg_s = '[1-9][0-9]{3}[0-1][0-9][0-3][0-9][0-2][0-4]'
        elif dt_format == '%Y-%m-%d_%H:%M':
            reg_s = '[1-9][0-9]{3}-[0-1][0-9]-[0-3][0-9]_[0-2][0-4]:[0-6][0-9]'
        else:
            print('Error: reg_s in filenam class not defined')
            sys.exit()
        s = re.search(reg_s, self.filename)
        self.filebase = self.filename[:s.start()]
        self.fileend = self.filename[s.end():]
        date_s = self.filename[s.start():s.end()]
        self.incrementfilename = self.filename + '.increment'
        self.date = datetime.datetime.strptime(date_s, dt_format)
        self.dt_format = dt_format
        self.dt = dt

    def advance(self):
        self.previousfilename = self.filename
        self.date += self.dt
        self.filename = self.filebase + \
            self.date.strftime(self.dt_format) + \
            self.fileend
        self.fullpath = self.dirname + self.filename
        self.incrementfilename = self.filename + '.increment'

    def moveto(self, topath):
        old_fullpath = self.fullpath
        self.dirname = check_path(topath)
        shutil.copy(self.fullpath, self.dirname)
        self.fullpath = self.dirname + self.filename
        print('copied', old_fullpath, 'to', self.fullpath)

    def append(self, postfix):
        self.fullpath += postfix
        self.filename += postfix
        self.fileend += postfix


class node:
    def __init__(self):
        self.nodes = 1
        self.ppn = 36


if __name__ == '__main__':
    workflow(sys.argv)
    print('fin')
