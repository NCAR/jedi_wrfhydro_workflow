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
    def move_to(self, topath):
        old_fullpath = self.fullpath
        dirname = check_path(topath)
        shutil.move(self.fullpath, dirname)
        self.fullpath = dirname + self.filename
        print('moved', old_fullpath, 'to', self.fullpath)
    def copy_to(self, topath):
        old_fullpath = self.fullpath
        self.dirname = check_path(topath)
        shutil.copy(self.fullpath, self.dirname)
        self.fullpath = self.dirname + self.filename
        print('copied', old_fullpath, 'to', self.fullpath)


class YAML_Filename(Filename):
    def __init__(self, fullpath):
        self.filename = os.path.basename(fullpath)
        self.fullpath = fullpath
        self.read()

    def read(self):
        with open(self.fullpath, 'r') as f:
            self.yaml = yaml.safe_load(f)

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


class JSON_Filename(Filename):
    def __init__(self, fullpath):
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
    def __init__(self, obs, dt):
        self.name = obs['obs space']['name']
        dt_format = '%Y-%m-%dT%H:%M:%SZ'
        for key,val in obs['obs space'].items():
            if key == 'obsdatain':
                self.f_in = NC_Filename(val['obsfile'],
                                        dt,
                                        dt_format)
            if key == 'obsdataout':
                self.f_out = NC_Filename(val['obsfile'],
                                         dt,
                                         dt_format)

    def advance(self):
        self.f_in.advance()
        self.f_out.advance()


class NC_Filename(Filename):
    def __init__(self, fullpath, dt, dt_format='%Y%m%d%H'):
        self.fullpath = fullpath
        self.dirname = os.path.dirname(fullpath) + '/'
        self.filename = os.path.basename(fullpath)
        self.previousfilename = ''
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
        self.incrementfilename = self.filename + '.increment'
        self.date = datetime.datetime.strptime(date_s, dt_format)
        self.dt_format = dt_format
        self.dt = dt

    def advance(self):
        self.previousfilename = self.filename
        self.date += self.dt
        self.filename = \
            self.filebase + \
            self.date.strftime(self.dt_format) + \
            self.fileend
        self.fullpath = self.dirname + self.filename
        self.incrementfilename = self.filename + '.increment'

    def date_stringify(self):
        return self.date.strftime(self.dt_format)

    def copy_previous(self, topath):
        old_fullpath = self.fullpath
        self.dirname = check_path(topath)
        shutil.copy(self.fullpath, self.dirname)
        self.fullpath = self.dirname + self.filename
        print('copied', old_fullpath, 'to', self.fullpath)

    def append(self, postfix):
        self.fullpath += postfix
        self.filename += postfix
        self.fileend += postfix
