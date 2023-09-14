import datetime
import json
import os
import shutil
import sys
import re
import yaml

def check_path(path):
    if (path[-1] != '/'):
        path += '/'
    return path


class Filename:
    def __init__(self, fullpath):
        self.filename = os.path.basename(fullpath)
        self.fullpath = fullpath
    def move_to(self, to_dir):
        old_fullpath = self.fullpath
        dirname = check_path(to_dir)
        shutil.move(self.fullpath, dirname)
        self.fullpath = dirname + self.filename
        print('moved', old_fullpath, 'to', self.fullpath, "")
    def copy_to(self, to_dir='', from_path = '', to_file='', update_path=True):
        old_fullpath = self.fullpath
        # setup from
        if from_path != '':
            self.fullpath = from_path
        # setup to
        if to_dir == '':
            to_dir = './'
        else:
            to_dir = check_path(to_dir)
        if to_file == '':
            to_file = os.path.basename(self.fullpath)

        shutil.copy(self.fullpath, to_dir + to_file)
        if update_path==True:
            self.dirname = to_dir
            self.fullpath = to_dir + to_file
        print('copied', old_fullpath, 'to', to_dir + to_file)


def tree_traversal_expand_vars(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, str):
                node[key] = os.path.expandvars(value)
            tree_traversal_expand_vars(value)
    elif isinstance(node, list):
        for item in node:
            tree_traversal_expand_vars(item)

class YAML_Filename(Filename):
    def __init__(self, fullpath):
        self.filename = os.path.basename(fullpath)
        self.fullpath = fullpath
        self.read()

    def read(self):
        with open(self.fullpath, 'r') as f:
            self.yaml = yaml.safe_load(f)
        tree_traversal_expand_vars(self.yaml) #

    def write(self):
        if (self.yaml):
            with open(self.fullpath, 'w') as f:
                yaml.dump(self.yaml, f)
        else:
            print("Warning: yaml variable does not exist, not written")

    def put_key(self, put_key, put_val, yaml_tree=False):
        if yaml_tree == False:
            yaml_tree = self.yaml
        found = False
        for key, val in yaml_tree.items():
            if (key == put_key):
                yaml_tree[put_key] = put_val
                return True
            elif (type(val) == dict) and found == False:
                found = self.put_key(put_key, put_val, val)
        return found

    def put_key_LETKF_OI(self, lsm_file, hydro_file):
        members = self.yaml['background']['members']
        for i,member in enumerate(members):
            member['filename_lsm'] = lsm_file + f'_mem{i+1:0{3}d}'
            member['filename_hydro'] = hydro_file

class JSON_Filename(Filename):
    def __init__(self, fullpath):
        if fullpath == None:
            self.fullpath = None
            return
        self.filename = os.path.basename(fullpath)
        self.fullpath = fullpath
        self.read()

    def read(self):
        with open(self.fullpath, 'r') as f:
            self.json = json.loads(f.read())

    def write(self):
        if (self.json):
            with open(self.fullpath, 'w') as f:
                json.dump(self.json, f)
        else:
            print("Warning: json variable does not exist, not written")

    def put_time(self, time):
        self.put_key('start_min', time.minute)
        self.put_key('start_hour', time.hour)
        self.put_key('start_day', time.day)
        self.put_key('start_month', time.month)
        self.put_key('start_year', time.year)

    def put_key(self, put_key, put_val, json_tree=False):
        if json_tree == False:
            json_tree = self.json
        found = False
        for key, val in json_tree.items():
            if (key == put_key):
                json_tree[put_key] = put_val
                return True
            elif (type(val) == dict) and found == False:
                found = self.put_key(put_key, put_val, val)
        return found


class Obs():
    def __init__(self, obs_dir, obs, time):
        dt_format = '%Y-%m-%dT%H:%M:%SZ'
        for key,val in obs['obs space'].items():
            if key == 'obsdatain':
                self.f_in = NC_Filename(obs_dir,
                                        val['obsfile'],
                                        time,
                                        obs['obs space']['name'],
                                        dt_format)
            if key == 'obsdataout':
                self.f_out = NC_Filename('.',
                                         val['obsfile'],
                                         time,
                                         obs['obs space']['name'],
                                         dt_format)

    def advance(self):
        self.f_in.advance()
        self.f_out.advance()


class NC_Filename(Filename):
    def __init__(self, restart_dir, fullpath, time, name, dt_format='%Y%m%d%H'):
        self.dirname = restart_dir + '/'
        self.restart_dir = restart_dir + '/'
        self.filename = os.path.basename(fullpath)
        self.fullpath = self.dirname + self.filename
        self.previousfilename = ''
        self.ens_base_dir = ''
        self.name = name
        if dt_format == '%Y%m%d%H':
            reg_s = '[1-9][0-9]{3}[0-1][0-9][0-3][0-9][0-2][0-4]'
        elif dt_format == '%Y-%m-%d_%H:%M':
            reg_s = '[1-9][0-9]{3}-[0-1][0-9]-[0-3][0-9]_[0-2][0-4]:[0-6][0-9]'
        elif dt_format == '%Y-%m-%dT%H:%M:%SZ':
            reg_s = '[1-9][0-9]{3}-[0-1][0-9]-[0-3][0-9]T[0-2][0-4]:[0-6][0-9]:[0-6][0-9]Z'
        else:
            print('Error: reg_s is not defined for dt_format =', dt_format)
            sys.exit()
        s = re.search(reg_s, self.filename)
        self.filebase = self.filename[:s.start()]
        self.fileend = self.filename[s.end():]
        date_s = self.filename[s.start():s.end()]
        self.incrementfilename = ''
        self.date = time.current
        self.dt_format = dt_format
        self.dt = time.dt
        self.set_date(self.date)

    def advance(self):
        date_s = re.sub('\-|\_|\:00', '', self.date_stringify())
        self.old_ens_member_dir = self.dirname + '/' + \
            self.name + date_s + '/' + \
            f"member_000"
        self.previousfilename = self.filename
        self.date += self.dt
        self.filename = \
            self.filebase + \
            self.date.strftime(self.dt_format) + \
            self.fileend
        self.fullpath = self.dirname + self.filename

    def date_stringify(self):
        return self.date.strftime(self.dt_format)

    def copy_previous(self, to_dir):
        old_fullpath = self.fullpath
        self.dirname = check_path(to_dir)
        shutil.copy(self.fullpath, self.dirname)
        self.fullpath = self.dirname + self.filename
        print('copy_previous: copied', old_fullpath, 'to', self.fullpath)

    def append(self, postfix):
        self.fullpath += postfix
        self.filename += postfix
        self.fileend += postfix

    def set_date(self, date):
        self.filename = \
            self.filebase + \
            date.strftime(self.dt_format) + \
            self.fileend
        self.fullpath = self.dirname + self.filename

    def copy_from_restart_dir(self, to_dir):
        self.dirname = check_path(to_dir)
        from_path = self.restart_dir + self.filename
        shutil.copy(from_path, to_dir)
        self.fullpath = to_dir + '/' + self.filename
        print('copy_from_restart_dir: copied', from_path, 'to', self.fullpath)

    def copy_from_old_ens_member_dir(self, to_dir, mem_num=1):
        # copy old time
        from_path = self.old_ens_member_dir + '/' + \
            self.filebase + \
            (self.date).strftime(self.dt_format) + \
            self.fileend
        self.copy_to(to_dir, from_path)
