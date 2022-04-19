import argparse
from copy import deepcopy
import operator
import os
from pathlib import Path
import pickle
import subprocess
import shutil
import sys
import wrfhydropy
import workflowTime as wt
# rm after dev finished
import logging
import workflowFile as wf
import xarray as xr

dry=False
# -- todo ---
# * exit if incrementing fails
# * wrfhydropy
# * read resource info using CLI
# * make parse_arguments less brittle
# ** hard coded for specific case
class Workflow:
    def __init__(self, args):
        pprint('Starting Workflowpy', 0)
        self.init(args)
        self.precycle()
        self.cycle()
        self.end()


    def precycle(self):
        if self.time.pre_wrf_h: # else read from restart
            pprint("Starting Pre-Cycle Process", 1)
            self.run_ensemble()
            self.time.pre_wrf_h_done()
            self.setup_experiment(precyclerun=True)
            self.prep_next_cycle(precyclerun=True)
            pprint("Ending Pre-Cycle Process", 1)


    def cycle(self):
        pprint("Starting Cycling Process", 1)
        print(" starting at", self.time.start)
        while self.time.current < self.time.end:
            self.run_filter()
            self.increment_restart()
            self.run_ensemble()
            self.prep_next_cycle()
        print(" Ending Cycling Process")


    def run_filter(self):
        pprint('Running JEDI filter', 2)
        cd(self.workflow_work_dir)
        cmd = [self.jedi_exe, self.jedi_yaml.fullpath]
        self.run(cmd)


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
            pprint('Not running jedi increment on restarts', 2)


    def run_ensemble(self):
        pprint('Running ensemble WRF-Hydro', 2)
        cd(self.workflow_work_dir)
        ensemble = wrfhydropy.EnsembleSimulation()
        ensemble.add(self.simulation)
        ensemble.replicate_member(self.ensemble_n_members)
        print("Setup:")
        print("   exe_cmd: ", self.wrf_h_exe)
        print("   restart_dir: ", self.workflow_work_dir)
        print("   restart_file_time: ", self.time.current_s)
        print("   starting:", self.time.current_s)
        print("   ending:", self.time.future_s)

        job = wrfhydropy.Job(
            self.name,
            self.time.current_s,
            self.time.future_s,
            exe_cmd = self.wrf_h_exe,
            restart_dir = self.workflow_work_dir,
            restart_file_time = self.time.current_s,
            restart = True,
            restart_freq_hr = 24)
            # entry_cmd = 'echo "--STARTING JOB--"',
            # exit_cmd = 'echo "---ENDING JOB---"'
        # )

        # setup experiment 182
        # print("job = ", job)

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


    def prepare_ensemble_yamls(self):
        restart_f = self.simulation.base_hydro_namelist['hydro_nlist']['restart_file']
        restart_f_add =  restart_f+'_mem001'
        restart_f_minus =  restart_f+'_mem002'
        restarts = [restart_f, restart_f_add, restart_f_minus]
        print(restarts)
        print(pwd())
        print("debug: exiting")
        sys.exit()


    def prepare_LETKF_OI(self):
        restart_f = self.simulation.base_hydro_namelist['hydro_nlist']['restart_file']
        restart_f_add =  restart_f+'_mem001'
        restart_f_minus =  restart_f+'_mem002'
        modify_restart_vars(restart_f, restart_f_add, operator.add,
                            self.LETKF_OI.vars)
        modify_restart_vars(restart_f, restart_f_minus, operator.sub,
                            self.LETKF_OI.vars)
        # restart_tuple = ('base_hydro_namelist', 'hydro_nlist', 'restart_file')
        # restarts = [restart_f, restart_f_add, restart_f_minus]
        # ensemble.set_member_diffs(restart_tuple, restarts)



    def prep_next_cycle(self, precyclerun=False):
        pprint("Advancing to " + str(self.time.future), 2)
        if not precyclerun:
            print("DEBUG:::lsm_file_fullpath", self.lsm_file.fullpath)
            print("DEBUG:::hydro_file_fullpath", self.hydro_file.fullpath)
            self.lsm_file.copy_from_ens_member_dir(self.workflow_work_dir)
            self.hydro_file.copy_from_ens_member_dir(self.workflow_work_dir)
            self.time.advance()
            self.lsm_file.advance_wwd(self.workflow_work_dir)
            self.hydro_file.advance_wwd(self.workflow_work_dir)
        print("DEBUG3:::lsm_file_fullpath", self.lsm_file.fullpath)
        self.jedi_yaml.put_key('filename_lsm', self.lsm_file.fullpath)
        self.jedi_yaml.put_key('filename_hydro', self.hydro_file.fullpath)
        self.wrf_h_hydro_patches_json.put_key('restart_file', self.hydro_file.fullpath)
        self.wrf_h_hrldas_patches_json.put_time(self.time.current)
        # update obs times
        if not precyclerun:
            self.advance_obs_and_update_jedi_yaml()
        self.jedi_yaml.put_key('window begin',
                               str(self.jedi_obs[0].f_in.date_stringify()))
        self.jedi_yaml.put_key('date',
                               str(self.jedi_obs[0].f_in.date_stringify()))

        self.jedi_yaml.write()
        self.wrf_h_hrldas_patches_json.write()
        self.wrf_h_hydro_patches_json.write()

        print('filename_lsm =', self.lsm_file.fullpath)
        print('filename_hydro =', self.hydro_file.fullpath)
        print('hrldas_namelist.json =', self.wrf_h_hrldas_patches_json.fullpath)
        print('hydro_namelist.json =', self.wrf_h_hydro_patches_json.fullpath)
        if not precyclerun:
            for obs in self.jedi_obs:
                print('jedi_obs_in =', obs.f_in.fullpath)
                print('jedi_obs_out =', obs.f_out.fullpath)
                shutil.copy(obs.f_in.fullpath, obs.f_out.fullpath)
            # self.prepare_LETKF_OI() # DEBUG: ADD BACK IN
        cd(self.workflow_work_dir)



    def jedi_obs_init(self):
        self.jedi_obs = []
        for obs in self.jedi_yaml.yaml['observations']:
            self.jedi_obs.append(wf.Obs(self.obs_dir, obs, self.time))


    def advance_obs_and_update_jedi_yaml(self):
        for obs in self.jedi_obs:
            obs.advance()
        # need to match obs in yaml to obs in list
        for i, obs in enumerate(self.jedi_yaml.yaml['observations']):
            obs['obs space']['obsdatain']['obsfile'] = \
                self.jedi_obs[i].f_in.fullpath
            obs['obs space']['obsdataout']['obsfile'] = \
                self.jedi_obs[i].f_out.fullpath


    def get_resource_info(self):
        pprint("TODO: Obtaining resource info", 2)
        # read node file? Use `$ pbsnode`?
        print("Single Cheyenne Node Hardcoded")
        self.node = node()


    # make sure everything is in proper format
    # make sure directories exist
    # update dates to workflow date
    def setup_experiment(self, precyclerun=False):
        self.lsm_file.set_date(self.time.current)
        self.hydro_file.set_date(self.time.current)

        # collect starting files
        if (not precyclerun):
            self.lsm_file.copy_from_restart_dir(self.workflow_work_dir)
            self.hydro_file.copy_from_restart_dir(self.workflow_work_dir)
        # else:
        #     self.lsm_file.copy_from_ens_member_dir(self.workflow_work_dir)
        #     self.hydro_file.copy_from_ens_member_dir(self.workflow_work_dir)

        # update jedi yaml with copied files
        self.jedi_yaml.put_key('filename_lsm', self.lsm_file.fullpath)
        self.jedi_yaml.put_key('filename_hydro', self.hydro_file.fullpath)
        self.wrf_h_hydro_patches_json.put_key('restart_file', self.hydro_file.fullpath)
        self.wrf_h_hrldas_patches_json.put_key('restart_filename_requested',
                                       self.lsm_file.fullpath)
        self.wrf_h_hrldas_patches_json.put_time(self.time.current)

        self.ensemble_n_members = 1
        self.jedi_obs_init()
        self.jedi_yaml.write()
        self.wrf_h_hydro_patches_json.write()
        self.wrf_h_hrldas_patches_json.write()
        self.setup_wrfhydropy()


    # setup simulation
    def setup_wrfhydropy(self):
        config = self.wrf_h_config

        model = wrfhydropy.Model(
            source_dir = self.wrf_h_build_dir,
            compiler = 'gfort',
            compile_options={'WRF_HYDRO_NUDGING': 0},
            model_config=config,
            hydro_namelist_config_file  = self.wrf_h_hydro_json.fullpath,
            hrldas_namelist_config_file = self.wrf_h_hrldas_json.fullpath)
            # compile_options_config_file = '/glade/u/home/afox/work/jedi/workflow/CO_state_domain/compile_options.json'
            # compile_options_config_file = compile_options.json # DEBUG ADD IN?
        # )
        if (self.workflow_wrf_dir.exists()):
            with open(self.workflow_wrf_dir / 'WrfHydroModel.pkl', 'rb') as f:
                model = pickle.load(f)
        else:
            model.compile(str(self.workflow_wrf_dir))
        print('Using', self.wrf_h_hydro_patches_json.fullpath)
        print('Using', self.wrf_h_hrldas_patches_json.fullpath)
        print('Model:')
        domain = \
            wrfhydropy.Domain(self.wrf_h_domain_dir,
                              config,
                              self.wrf_h_version,
                              self.wrf_h_hydro_patches_json.fullpath,
                              self.wrf_h_hrldas_patches_json.fullpath)
        simulation = wrfhydropy.Simulation()
        simulation.add(model)
        simulation.add(domain)
        self.simulation = simulation
        # add ens_member directory to filename
        self.lsm_file.set_ens_member_dir(self.workflow_work_dir, self.name)
        self.hydro_file.set_ens_member_dir(self.workflow_work_dir, self.name)


    def parse_arguments(self, args):
        if len(args) > 1:
            self.workflow_yaml_f = args[1]
        else:
            print("ERROR: didn't pass jedi workflow yaml")
            sys.exit()


    # TODO: what if end_time in different format?
    def read_yamls(self):
        pprint("Reading yamls", 2)
        self.workflow_yaml = wf.YAML_Filename(self.workflow_yaml_f)
        # read various keys from the workflow yaml file
        self.name = self.workflow_yaml.yaml['experiment']['name']
        self.yaml_read_dir_keys()
        self.collect_yamls_and_jsons()
        self.yaml_read_time_key()
        self.yaml_read_jedi_key()
        self.yaml_read_increment_exe_key()
        self.yaml_read_wrf_hydro_key()
        # self.yaml_read_ensemble_key()


    # read ensemble key
    def yaml_read_ensemble_key(self):
        ensemble = self.workflow_yaml.yaml['experiment']['ensemble']
        self.ensemble_n_members = ensemble['num_members']
        self.ensemble_method = ensemble['method']
        self.LETKF_OI = LETKF_OI(ensemble) if ensemble['method'] == 'LETKF_OI' else None


    # create yaml objects and move them
    def collect_yamls_and_jsons(self):
        wrf_h_yaml = self.workflow_yaml.yaml['experiment']['wrf_hydro']
        self.wrf_h_hrldas_patches_json = wf.JSON_Filename(wrf_h_yaml['hrldas_patches_json'])
        self.wrf_h_hydro_patches_json = wf.JSON_Filename(wrf_h_yaml['hydro_patches_json'])
        self.wrf_h_hrldas_json = wf.JSON_Filename(wrf_h_yaml['hrldas_json'])
        self.wrf_h_hydro_json = wf.JSON_Filename(wrf_h_yaml['hydro_json'])        
        self.jedi_yaml = wf.YAML_Filename(
            self.workflow_yaml.yaml['experiment']['jedi']['yaml'])
        self.wrf_h_hrldas_patches_json.copy_to(self.workflow_work_dir)
        self.wrf_h_hydro_patches_json.copy_to(self.workflow_work_dir)
        self.wrf_h_hrldas_json.copy_to(self.workflow_work_dir)
        self.wrf_h_hydro_json.copy_to(self.workflow_work_dir)        
        self.jedi_yaml.copy_to(self.workflow_work_dir)


    def yaml_read_wrf_hydro_key(self):
        wrf_h_yaml = self.workflow_yaml.yaml['experiment']['wrf_hydro']
        self.wrf_h_build_dir = check_wrf_h_build_path(
            wrf_h_yaml['build_dir'])
        wrf_h_run_dir = check_wrf_h_run_path(wrf_h_yaml['build_dir']
                                             + '/trunk/NDHMS/Run')
        self.wrf_h_exe = wrf_h_run_dir + wrf_h_yaml['exe']
        self.wrf_h_domain_dir = check_path(wrf_h_yaml['domain_dir'])
        if not os.path.isfile(self.wrf_h_exe):
            exit("wrf_hydro.exe no found at " + self.wrf_h_exe)
        self.wrf_h_version = wrf_h_yaml['version']
        self.wrf_h_config = wrf_h_yaml['config']


    def yaml_read_increment_exe_key(self):
        self.increment_exe = \
            self.workflow_yaml.yaml['experiment']['increment']['exe']


    def yaml_read_jedi_key(self):
        filename_lsm = get_yaml_key(self.jedi_yaml.yaml, 'filename_lsm')
        filename_hydro = get_yaml_key(self.jedi_yaml.yaml, 'filename_hydro')
        self.lsm_file = wf.NC_Filename(self.restarts_dir, filename_lsm,
                                       self.time)
        self.hydro_file = wf.NC_Filename(self.restarts_dir, filename_hydro,
                                         self.time, '%Y-%m-%d_%H:%M')
        jedi = self.workflow_yaml.yaml['experiment']['jedi']
        self.jedi_exe = jedi['exe']
        self.jedi_increment = jedi['increment']
        if (not os.path.exists(self.jedi_exe)):
            exit("Couldn't find jedi executable")


    def yaml_read_dir_keys(self):
        self.workflow_work_dir = \
            self.workflow_yaml.yaml['experiment']['workflow_work_dir']
        self.workflow_wrf_dir = Path(self.workflow_work_dir + '/wrf_hydro_exe/')
        check_dir(self.workflow_work_dir)
        self.restarts_dir = \
            self.workflow_yaml.yaml['experiment']['init']['restarts_dir']
        self.obs_dir = \
            self.workflow_yaml.yaml['experiment']['init']['obs_dir']


    def yaml_read_time_key(self):
        time = self.workflow_yaml.yaml['experiment']['time']
        self.time = wt.WorkflowpyTime(time)


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


    def init(self, args):
        # TODO GATHER/SETUP?
        # TODO READ/GATHER/SETUP?
        pprint("Initializing Workflowpy", 1)
        self.parse_arguments(args)
        self.ensemble_n_members = 1
        self.get_resource_info() # todo: one node hard coded
        self.read_yamls()
        self.setup_experiment()  # need to create structure
        self.print_setup()
        pprint("Finished Initializing Workflowpy", 1)


    def print_setup(self):
        pprint("Setup", 2)
        print("Working dir: ", self.workflow_work_dir)
        print("WRF-Hydro exe:, ", self.wrf_h_exe)
        print("Running WRF-Hydro before cycle phase:", self.time.pre_wrf_h)
        print('filename_lsm =', self.lsm_file.fullpath)
        print('filename_hydro =', self.hydro_file.fullpath)
        print('hrldas_namelist.json =', self.wrf_h_hrldas_patches_json.fullpath)
        print('hydro_namelist.json =', self.wrf_h_hydro_patches_json.fullpath)
        for obs in self.jedi_obs:
            print('jedi_obs_in =', obs.f_in.fullpath)
            print('jedi_obs_out =', obs.f_out.fullpath)


    def end(self):
        pprint("Exiting Workflowpy", 1)
        sys.exit()


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

def modify_restart_vars(f_in, f_out, math_op, vars_d):
    ds = xr.open_dataset(f_in, engine='netcdf4')
    for var in vars_d:
        ds[var] = math_op(ds[var], vars_d[var])
    ds.to_netcdf(f_out)
    ds.close()

class node:
    def __init__(self):
        self.nodes = 1
        self.ppn = 36

class LETKF_OI:
    def __init__(self, yaml):
        self.vars = yaml['LETKF_OI']['vars']
        for var in self.vars:
            if type(self.vars[var]) == str:
                self.vars[var] = eval(self.vars[var])


if __name__ == '__main__':
    Workflow(sys.argv)
    print('fin')
