#!/usr/bin/env python
## You can load conda environment by running >> conda activate /glade/work/mazrooei/miniconda3/envs/myxr
import time
t_start = time.perf_counter()
import sys
from datetime import datetime
import argparse
parser=argparse.ArgumentParser(
    description='This code compares a variable between two NWM restart files and creates maps and histogram plots.',
    usage='./Compare_RESTART_files.py ./RESTART_20160312.nc ./RESTART_20161212.nc SNOWH')
parser.add_argument('infile_RST1', type=str, help='The first NWM Rastert file')
parser.add_argument('infile_RST2', type=str, help='The second NWM Rastert file')
parser.add_argument('varname', type=str, help='Name of the variable to plot')
parser.print_help()
args = parser.parse_args()

import os
file_RST1 = args.infile_RST1
file_RST2 = args.infile_RST2
if not os.path.exists(file_RST1):
    print('error: input file1 not found')
    sys.exit()
elif not os.path.exists(file_RST2):
    print('error: input file2 not found')
    sys.exit()

print(str(datetime.now()) + ' | Loading python packages . . .')
import pathlib
import xarray as xr
import matplotlib.pyplot as plt

varname = args.varname

def preprocess_rst(ds):
    ds = ds.drop_vars(set(ds.data_vars).difference(set([varname])))
    return ds

print(str(datetime.now()) + ' | Opening file1: '  + file_RST1)
ds_rst1 = xr.open_mfdataset(file_RST1, preprocess=preprocess_rst)
# display(ds_rst1)
print(str(datetime.now()) + ' | Opening file2: '  + file_RST2)
ds_rst2 = xr.open_mfdataset(file_RST2, preprocess=preprocess_rst)
# display(ds_rst2)

var1 = ds_rst1[varname]
var2 = ds_rst2[varname]
name1 = pathlib.Path(var1.encoding["source"]).name.replace('_DOMAIN1','').replace('RESTART.','RST_')
name2 = pathlib.Path(var2.encoding["source"]).name.replace('_DOMAIN1','').replace('RESTART.','RST_')
plot_dims = [v for v in var1.dims if v not in ['south_north', 'west_east'] ]
if len(plot_dims)>1:
    plot_dims.remove('Time')
plot_dims_sizes = [var1.sizes[d] for d in plot_dims]
n_dims = len(plot_dims_sizes)

## PLOT maps
print(str(datetime.now()) + ' | Ploting maps')
for j in range(n_dims):
    n_rows = plot_dims_sizes[j]
    fig, axs = plt.subplots(n_rows,3,figsize=(21,5*n_rows), squeeze=False)
    for i in range(n_rows):
        var1.isel({plot_dims[0]:i}).plot(ax=axs[i,0], cmap='gist_ncar_r')
        axs[i,0].set_title(name1+' '+var1.name+' '+plot_dims[j]+'='+str(i))
        var2.isel({plot_dims[0]:i}).plot(ax=axs[i,1], cmap='gist_ncar_r')
        axs[i,1].set_title(name2+' '+var2.name+' '+plot_dims[j]+'='+str(i))
        (var2-var1).isel({plot_dims[0]:i}).plot(ax=axs[i,2], center=0)
        axs[i,2].set_title('Diff ( '+name2+' - '+name1+' ) '+var2.name+' '+plot_dims[j]+'='+str(i))

## PLOT histograms
print(str(datetime.now()) + ' | Ploting histograms')
for j in range(n_dims):
    n_rows = plot_dims_sizes[j]
    fig, axs = plt.subplots(n_rows, 1, figsize=(21,5*n_rows), squeeze=False)
    for i in range(n_rows):
        n,x,_ = var1.isel({plot_dims[j]:i}).plot.hist(bins = 200, alpha=0)
        bin_centers = 0.5*(x[1:]+x[:-1])
        axs[i,j].plot(bin_centers,n, label=name1, color='blue')
        n,x,_ = var2.isel({plot_dims[j]:i}).plot.hist(bins = 200, alpha=0)
        bin_centers = 0.5*(x[1:]+x[:-1])
        axs[i,j].plot(bin_centers,n, label=name2, color='red', linestyle='dashed')
        axs[i,j].legend(loc='upper right', prop={'size': 12})
        axs[i,j].set_title(plot_dims[j]+'='+str(i))

t_finish = time.perf_counter()
print(str(datetime.now()) + " | took " + str(round(t_finish - t_start, 2)) + " seconds")
plt.show()
