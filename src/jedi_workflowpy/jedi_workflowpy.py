import argparse
from copy import deepcopy
import operator
import os
from pathlib import Path
import pickle
import re
import subprocess
import shutil
import sys
import time as py_time
import wrfhydropy
import workflowTime as wt
# rm after dev finished
import logging
import workflowFile as wf
import xarray as xr


dry=False
# -- todo ---
# * exit if
#   - incrementing fails
#   -  wrfhydropy fails
# * read resource info using CLI
# * make parse_arguments less brittle
# * hard coded for GNU compiler
class Workflow:
    def __init__(self, args):
        pprint('Starting Workflowpy', 0)
        self.init(args)
        self.precycle()
        self.cycle()
        self.end()


    def init(self, args):
        pprint("Initializing Workflowpy", 1)
        self.start_time = py_time.time()
        self.parse_arguments(args)
        self.get_resource_info() # todo: one node hard coded
        self.read_yamls()
        self.setup_experiment()
        self.print_setup()
        pprint("Finished Initializing Workflowpy", 1)


    def precycle(self):
        if self.time.pre_wrf_h: # else read from restart
            pprint("Starting Pre-Cycle Process", 1)
            self.run_ensemble()
            self.time.pre_wrf_h_done()
            self.setup_experiment(precyclerun=True)
            self.prep_cycle(advance=False)
            pprint("Ending Pre-Cycle Process", 1)


    def cycle(self):
        pprint("Starting Cycling Process", 1)
        print(" starting at", self.time.start)
        while self.time.current < self.time.end:
            self.run_filter()
            self.increment_restart()
            self.run_ensemble()
            self.prep_cycle(advance=True)
        print(" Ending Cycling Process")


    def setup_experiment(self, precyclerun=False):
        self.lsm_file.set_date(self.time.current)
        self.hydro_file.set_date(self.time.current)
        self.jedi_obs_init()

        # -- collect starting files
        # if precyclerun setup, then the model has been run and files are
        #   retrieved from the past simulation
        if (precyclerun):
            self.lsm_file.copy_from_past_ens_member_dir(self.workflow_work_dir)
            self.hydro_file.copy_from_past_ens_member_dir(self.workflow_work_dir)
        else:
            self.lsm_file.copy_from_restart_dir(self.workflow_work_dir)
            self.hydro_file.copy_from_restart_dir(self.workflow_work_dir)

        self.prep_cycle(advance=False)

        self.setup_wrfhydropy()


    def run_filter(self):
        pprint('Running JEDI filter', 2)
        cd(self.workflow_work_dir)
        cmd = [self.jedi_exe, self.jedi_yaml.fullpath]
        self.run(cmd)


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
            print("Error: exiting")
            print(out.stderr.decode("utf-8"))
            sys.exit()


    def increment_restart(self):
        if (self.jedi_increment):
            pprint('Incrementing restarts', 2)
            cd(self.workflow_work_dir)
            cmd = [self.increment_exe,
                   self.lsm_file.filename,
                   self.lsm_file.incrementfilename]
                   # self.jedi_output_file]
            self.run(cmd)
        else:
            pprint('Not running jedi increment on restarts', 2)


    def run_ensemble(self):
        pprint('Running ensemble WRF-Hydro', 2)
        cd(self.workflow_work_dir)
        ensemble = wrfhydropy.EnsembleSimulation()
        ensemble.add(self.simulation)
        ensemble.replicate_member(1)

        if self.num_p > 1:
            cmd = f'mpiexec -np {str(self.num_p)} {self.wrf_h_exe}'
        else:
            cmd = self.wrf_h_exe

        job = wrfhydropy.Job(
            self.name,
            self.time.current_s,
            self.time.future_s,
            exe_cmd = cmd,
            restart_dir = self.workflow_work_dir,
            restart_file_time = self.time.current_s,
            restart = True,
            restart_freq_hr = self.advance_model_hrs)

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


    def prep_cycle(self, advance):
        cd(self.workflow_work_dir)
        if advance:
            pprint("Advancing to " + str(self.time.future), 2)
            self.time.advance()
            self.lsm_file.advance()
            self.hydro_file.advance()
            self.lsm_file.copy_from_old_ens_member_dir(
                self.workflow_work_dir)
            self.hydro_file.copy_from_old_ens_member_dir(
                self.workflow_work_dir)
            self.advance_obs()
            self.update_jedi_yaml_obs()
            for obs in self.jedi_obs:
                print('jedi_obs_in =', obs.f_in.fullpath)
                print('jedi_obs_out =', obs.f_out.fullpath)
                shutil.copy(obs.f_in.fullpath, obs.f_out.fullpath)

        if self.jedi_method == 'LETKF-OI':
            self.setup_LETKF_OI()
        else:
            self.jedi_yaml.put_key('filename_lsm', self.lsm_file.fullpath)
            self.jedi_yaml.put_key('filename_hydro', self.hydro_file.fullpath)

        self.jedi_yaml.put_key('window begin',
                               str(self.jedi_obs[0].f_in.date_stringify()))
        self.jedi_yaml.put_key('date',
                               str(self.jedi_obs[0].f_in.date_stringify()))

        self.wrf_h_hydro_json.put_key('restart_file', self.hydro_file.fullpath)
        self.wrf_h_hydro_json.put_key('restart_filename_requested',
                                      self.hydro_file.fullpath)
        self.wrf_h_hrldas_json.put_time(self.time.current)

        self.jedi_yaml.write()
        self.wrf_h_hrldas_json.write()
        self.wrf_h_hydro_json.write()
        cd(self.workflow_work_dir)


    # setup simulation
    def setup_wrfhydropy(self):
        model = wrfhydropy.Model(
            source_dir = self.wrf_h_src_dir,
            compiler = self.compiler,
            compile_options={'WRF_HYDRO_NUDGING': 0},
            hydro_namelist_config_file = self.wrf_h_hydro_json.fullpath,
            hrldas_namelist_config_file = self.wrf_h_hrldas_json.fullpath,
            model_config=self.wrf_h_config
        )
        if (self.workflow_wrf_dir.exists()):
            with open(self.workflow_wrf_dir / 'WrfHydroModel.pkl', 'rb') as f:
                model = pickle.load(f)
        else:
            model.compile(str(self.workflow_wrf_dir))

        print('Using HRLDAS', self.wrf_h_hrldas_json.fullpath)
        print('Using HYDRO', self.wrf_h_hydro_json.fullpath)
        if self.patches:
              print('And HRLDAS patches', self.wrf_h_hrldas_patches_json.fullpath)
              print('And HYDRO patches', self.wrf_h_hydro_patches_json.fullpath)

        if self.patches:
            domain = \
            wrfhydropy.Domain(self.wrf_h_domain_dir,
                              self.wrf_h_config,
                              self.wrf_h_version,
                              hydro_namelist_patch_file = self.wrf_h_hydro_patches_json.fullpath,
                              hrldas_namelist_patch_file = self.wrf_h_hrldas_patches_json.fullpath)
        else:
            print("WARNING: THIS IS UNTESTED")
            domain = \
            wrfhydropy.Domain(self.wrf_h_domain_dir,
                              self.wrf_h_config,
                              self.wrf_h_version)
        simulation = wrfhydropy.Simulation()
        simulation.add(model)
        simulation.add(domain)
        self.simulation = simulation


    def setup_LETKF_OI(self):
        # copy modified copies of restart file
        restart_f_add =  self.lsm_file.fullpath + '_mem001'
        restart_f_minus =  self.lsm_file.fullpath + '_mem002'
        self.modify_restart_vars(self.lsm_file.fullpath, restart_f_add,
                                 operator.add, self.LETKF_OI.vars)
        self.modify_restart_vars(self.lsm_file.fullpath, restart_f_minus,
                                 operator.sub, self.LETKF_OI.vars)
        self.jedi_yaml.put_key_LETKF_OI(self.lsm_file.fullpath,
                                        self.hydro_file.fullpath)
        # passing sub-yamls since recursive put_key method doesn't handle
        # multiple entries at all
        self.jedi_yaml.put_key('date',
                               str(self.jedi_obs[0].f_in.date_stringify()),
                               self.jedi_yaml.yaml['background']['members'][0])
        self.jedi_yaml.put_key('date',
                               str(self.jedi_obs[0].f_in.date_stringify()),
                               self.jedi_yaml.yaml['background']['members'][1])
        self.jedi_yaml.put_key('date',
                               str(self.jedi_obs[0].f_in.date_stringify()),
                               self.jedi_yaml.yaml['output increment'])
        time = self.time.current.strftime('%Y-%m-%dT%H:%M:%SZ.PT0S')
        self.lsm_file.incrementfilename = 'letkf.lsm.ens.0.'+time
        self.lsm_file.copy_to(to_file='letkf.lsm.ens.0.'+time, update_path=False)
        self.lsm_file.copy_to(to_file='letkf_inc.lsm.ens.0.'+time, update_path=False)
        self.hydro_file.copy_to(to_file='letkf.hyd.ens.0.'+time, update_path=False)
        self.hydro_file.copy_to(to_file='letkf_inc.hyd.ens.0.'+time, update_path=False)


    def jedi_obs_init(self):
        self.jedi_obs = []
        for obs in self.jedi_yaml.yaml['observations']['observers']:
            self.jedi_obs.append(wf.Obs(self.obs_dir, obs, self.time))
        self.update_jedi_yaml_obs()


    def advance_obs(self):
        for obs in self.jedi_obs:
            obs.advance()


    def update_jedi_yaml_obs(self):
        # need to match obs in yaml to obs in list
        for i, obs in enumerate(self.jedi_yaml.yaml['observations']['observers']):
            obs['obs space']['obsdatain']['obsfile'] = \
                self.jedi_obs[i].f_in.fullpath
            obs['obs space']['obsdataout']['obsfile'] = \
                self.jedi_obs[i].f_out.fullpath


    def get_resource_info(self):
        pprint("TODO: Obtaining resource info", 2)
        # read node file? Use `$ pbsnode`?
        print("Single Cheyenne Node Hardcoded")
        self.node = node()


    def modify_restart_vars(self, f_in, f_out, math_op, vars_d):
        ds = xr.open_dataset(f_in)
        for var in vars_d:
            ds[var] = math_op(ds[var], vars_d[var])
        ds.to_netcdf(f_out)
        ds.close()


    def parse_arguments(self, args):
        if len(args) > 1:
            self.workflow_yaml_f = args[1]
        else:
            print("ERROR: didn't pass jedi workflow yaml")
            sys.exit()


    def read_yamls(self):
        pprint("Reading yamls", 2)
        self.workflow_yaml = wf.YAML_Filename(self.workflow_yaml_f)
        self.read_yaml_experiment()
        self.read_yaml_init()
        self.read_yaml_time()
        self.read_jedi_yaml()
        self.read_increment_exe()
        self.collect_yamls_and_jsons()
        self.read_yaml_wrf_hydro()

    def read_yaml_experiment(self):
        experiment = self.workflow_yaml.yaml['experiment']
        self.name = experiment['name']
        self.num_p = experiment['num_p']
        self.compiler = self.parse_compiler(experiment['compiler'])
        self.workflow_work_dir = experiment['workflow_work_dir']
        self.workflow_wrf_dir = Path(self.workflow_work_dir + '/wrf_hydro_exe/')
        check_dir(self.workflow_work_dir)

    def parse_compiler(self, compiler):
        if compiler.lower() in ['gfort','gfortran','gnu']:
            return 'gfort'
        elif compiler.lower() in ['ifort','mpifort','mpiifort','intel']:
            return 'ifort'
        else:
            print('Error: ', compiler, 'does not match permitted options')
            sys.exit()

    # create yaml objects and move them
    def collect_yamls_and_jsons(self):
        wrf_h_yaml = self.workflow_yaml.yaml['experiment']['wrf_hydro']
        self.wrf_h_hrldas_json = wf.JSON_Filename(wrf_h_yaml['hrldas_json'])
        self.wrf_h_hydro_json = wf.JSON_Filename(wrf_h_yaml['hydro_json'])
        if 'hrldas_patches_json' in wrf_h_yaml:
            self.patches = True
            self.wrf_h_hrldas_patches_json = \
                wf.JSON_Filename(wrf_h_yaml['hrldas_patches_json'])
        else:
            self.patches = False
            self.wrf_h_hrldas_patches_json = \
                self.wrf_h_hrldas_json

        if 'hydro_patches_json' in wrf_h_yaml:
            self.wrf_h_hydro_patches_json = \
                wf.JSON_Filename(wrf_h_yaml['hydro_patches_json'])
        else:
            self.wrf_h_hydro_patches_json = \
                self.wrf_h_hydro_json

        self.wrf_h_hrldas_json.copy_to(self.workflow_work_dir)
        self.wrf_h_hydro_json.copy_to(self.workflow_work_dir)
        if self.patches:
            self.wrf_h_hrldas_patches_json.copy_to(self.workflow_work_dir)
            self.wrf_h_hydro_patches_json.copy_to(self.workflow_work_dir)

        self.jedi_yaml.copy_to(self.workflow_work_dir)


    def read_yaml_wrf_hydro(self):
        wrf_h_yaml = self.workflow_yaml.yaml['experiment']['wrf_hydro']
        self.wrf_h_src_dir = check_wrf_h_build_path(
            wrf_h_yaml['src_dir'])
        self.wrf_h_exe = str(self.workflow_wrf_dir) + '/wrf_hydro.exe'
        self.wrf_h_domain_dir = check_path(wrf_h_yaml['domain_dir'])
        self.wrf_h_version = wrf_h_yaml['version']
        self.wrf_h_config = wrf_h_yaml['config']


    def read_increment_exe(self):
        self.increment_exe = \
            self.workflow_yaml.yaml['experiment']['increment']['exe']


    def read_jedi_yaml(self):
        self.read_jedi_method(self.workflow_yaml.yaml['experiment']['jedi'])
        filename_lsm = get_yaml_key(self.jedi_yaml.yaml, 'filename_lsm')
        filename_hydro = get_yaml_key(self.jedi_yaml.yaml, 'filename_hydro')
        if self.jedi_method == 'LETKF-OI':
            filename_lsm = re.sub('_mem[0-9]*$','',filename_lsm)
        self.lsm_file = wf.NC_Filename(self.restarts_dir, filename_lsm,
                                       self.time, self.name)
        self.hydro_file = wf.NC_Filename(self.restarts_dir, filename_hydro,
                                         self.time, self.name, '%Y-%m-%d_%H:%M')
        if (not os.path.exists(self.jedi_exe)):
            exit("Couldn't find jedi executable")

    def read_jedi_method(self, jedi):
        self.jedi_method = jedi['method']
        mode_list = ['LETKF-OI', 'hofx', '3dvar']
        if self.jedi_method not in mode_list:
            print("Error: jedi method", jedi['method'],
                  'not in', mode_list)
            sys.exit()

        jedi_method_yaml = jedi[self.jedi_method]
        self.jedi_exe = jedi_method_yaml['exe']
        self.jedi_yaml = wf.YAML_Filename(jedi_method_yaml['yaml'])
        self.jedi_increment = jedi_method_yaml['increment']

        if self.jedi_method == 'LETKF-OI':
            self.LETKF_OI = LETKF_OI(jedi_method_yaml['vars'])
        elif self.jedi_method == 'hofx':
            pass
        elif self.jedi_method == '3dvar':
            pass


    def read_yaml_init(self):
        self.restarts_dir = \
            self.workflow_yaml.yaml['experiment']['init']['restarts_dir']
        self.obs_dir = \
            self.workflow_yaml.yaml['experiment']['init']['obs_dir']


    def read_yaml_time(self):
        time = self.workflow_yaml.yaml['experiment']['time']
        self.time = wt.WorkflowpyTime(time)
        self.advance_model_hrs = time['advance_model_hours']




    def print_setup(self):
        pprint("Setup", 2)
        print("Working dir: ", self.workflow_work_dir)
        print("WRF-Hydro exe:, ", self.wrf_h_exe)
        print("Running WRF-Hydro before cycle phase:", self.time.pre_wrf_h)
        print('filename_lsm =', self.lsm_file.fullpath)
        print('filename_hydro =', self.hydro_file.fullpath)
        print('hrldas_namelist.json =', self.wrf_h_hrldas_json.fullpath)
        print('hydro_namelist.json =', self.wrf_h_hydro_json.fullpath)
        if self.patches:
            print('hrldas_namelist_patches.json =', self.wrf_h_hrldas_patches_json.fullpath)
            print('hydro_namelist_patches.json =', self.wrf_h_hydro_patches_json.fullpath)
        for obs in self.jedi_obs:
            print('jedi_obs_in =', obs.f_in.fullpath)
            print('jedi_obs_out =', obs.f_out.fullpath)


    def end(self):
        pprint("Exiting Workflowpy", 1)
        end_time = py_time.time() - self.start_time
        print("Runtime took", end_time, "seconds")
        sys.exit()


def get_yaml_key(yaml_tree, get_key):
    found = False
    for key, val in yaml_tree.items():
        if (key == get_key):
            return(val)
        elif (type(val) == dict) and found == False:
            found = get_yaml_key(val, get_key)
        elif (type(val) == list) and found == False:
            for item in val:
                if type(item) == dict:
                    found = get_yaml_key(item, get_key)
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


class node:
    def __init__(self):
        self.nodes = 1
        self.ppn = 36

class LETKF_OI:
    def __init__(self, vars):
        self.vars = vars
        for var in vars:
            if type(vars[var]) == str:
                self.vars[var] = eval(vars[var])

if __name__ == '__main__':
    Workflow(sys.argv)
    print('fin')
