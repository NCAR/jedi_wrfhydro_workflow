# The dart workflow is here
# https://github.com/NCAR/DART/blob/main/models/wrf_hydro/hydro_dart_py/hydrodartpy/core/run_filter_experiment.py
# with main function here
# https://github.com/NCAR/DART/blob/2caa99d587b1394c601816236db361a8ef18e91a/models/wrf_hydro/hydro_dart_py/hydrodartpy/core/run_filter_experiment.py#L428
# The call to advance ensemle points here:
# https://github.com/NCAR/DART/blob/main/models/wrf_hydro/hydro_dart_py/hydrodartpy/core/advance_ensemble.py
# https://github.com/NCAR/wrf_hydro_py/blob/master/wrfhydropy/core/ensemble.py

# Below model could mean ensemble and could be called "Forecast" generically
# Below filter means Analysis more generically

# Basic workflow
#  * Establish config (reading an experiment yaml for this workflow)
#  * Establish computing resources (i.e. read a pbs nodefile)
#  * Set the initial time and restarts
#  * Cycling loop:
#    - prep observations:
#        determine how many assimilation windows until next obs?
#    - (parameter advance - if joint param-state estimation)
#    - if there are obs in the current window:
#      + prepare run dir and config file for filter
#      + run filter
#      + manage filter output
#    - advance model (to start of window with next available obs
#        obtained above)
#    - update prev and current time


# Deep Thoughts
# =============
# * Keep in mind, JEDI workflows may advance an ensemble or a
#     single/deterministic model run. Instead of the function call
#     "advance_ensemble" you could init a class Forecast object with
#     the same or similar arguments that would then have a run() method
#     which would take the final argument on how many times to advance.
#     It seems like v2.0 of this workflow could make the individual
#     functions in the DART workflow into objects with methods that take
#     the arguments that actually change in the loop. This would probably
#     help provide the flexibility to do different kinds of Forecasts but
#     also different kinds of Analysis as well (3DVar vs LETKF, etc).
# * Practical code for the model side is available in the DART code
#     referenced above. That workflow advances an ensemble using wrfhydropy
#     discussed in the previous bullet. Note that it passes the teams_dict
#     to the advance (which is actually static). The teams dict is based
#     the ensemble size and the PBS nodefile, discussed below. I suppose
#     an ensemble of size 1 would work exactly the same. There's no reason
#     not to do that.
# * Scheduling. This is the main consideration in designing the workflow.
#     We spent a long time on this because the workflow developed by Tim
#     on the DART team just did not suit our purposes. The crux is both
#     relatively fast model advance (even from restart) and short assimilation
#     windows: if you queue the individual advances, the scheduler waits are
#     same order of magnitude as the model advances/forecasts even when there
#     is no queue. That's PBS being PBS. The mantra is "remove dependence on
#     PBS as much as possible". The way to do this is to handle multiple mpi
#     calls ourselves on the "main" job node. This is what teams in wrfhydropy
#     does for the model
#     https://wrfhydropy.readthedocs.io/en/documentation/examples/ex_04_ensembles.html#Teams-run
#     Essentially, the ensemble members are mapped on to separate teams of
#     mpi workers that partition the resources. The resuorces of the job are
#     supplied in the PBS nodefile. This is a slightly tricky business, and it
#     can be difficult to port across compilers. That's why all execution
#     commands in wrfhydropy are supplied by the user, so they adapt to the
#     compiler of choice. I generally think intel is the way to go, but there
#     are some quirks where MPT might be preferred. You can discuss with
#     Sidartha Gosh at CISL. I dont think we ever ran the case where a single
#     member exceeds the use of a single node. But we certainly had multiple
#     members on a single node. I do have some code for the former case from
#     Sidd but I never tried it.
#     On the JEDI or DART side, parallelism is handled internally to the code,
#     so mpiexec/run can use all the resources available to the ensemble
#     and is almost always requires much less than that.
# * Snow partition function. This would come in the "manage filter output"
#     step and potentially the "prepare run dir for filter" if the
#     Analysis step overwrites the restart files provided to it.
#     After filter runs, you need the prior/forecast states in the restart
#     to be provided to Forecast, but you need to insert the
#     posteriors/analysis in to that file as either or both of
#     SNEQV_post and SNOWH_post (eventually there shold be a
#     SNOW_T_BULK_post as well). Then, as currently configured, the
#     noahmp code snow_update will see these posterior states and do its
#     thing. If the posterior states are identical to the prior states (
#     e.g. far away from observations) the code will see that and skip
#     its further machinations.
# * You can get started with this by just doing the parts required for
#     advancing the model.
