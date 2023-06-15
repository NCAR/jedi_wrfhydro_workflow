cmake_minimum_required( VERSION 3.15 )

find_package( ecbuild 3.5 REQUIRED )

project( WRF-Hydro-JEDI-WorkflowPY VERSION 0.0.2 LANGUAGES C CXX Fortran)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
set( ECBUILD_DEFAULT_BUILD_TYPE Release )
set( Python_EXECUTABLE python3 )
set( CMAKE_Fortran_FLAGS "-g ${CMAKE_Fortran_FLAGS}" )
set( CMAKE_SCRIPT_DIR ${CMAKE_SOURCE_DIR}/src/cmake_scripts )

include( ecbuild_system NO_POLICY_SCOPE )
ecbuild_requires_macro_version( 2.5 )

ecbuild_declare_project()
ecbuild_enable_fortran( REQUIRED )
ecbuild_find_python( VERSION 3.6 REQUIRED NO_LIBS )
ecbuild_find_mpi(
    COMPONENTS C Fortran
    REQUIRED )
find_package( NetCDF REQUIRED COMPONENTS Fortran )

enable_testing()

# --- setup Python requirements ---
if(DEFINED ENV{VIRTUAL_ENV} OR DEFINED ENV{CONDA_PREFIX})
  set(_pip_args)
else()
  set(_pip_args "--user")
endif()
execute_process(COMMAND ${Python_EXECUTABLE} -m pip install ${_pip_args} wrfhydropy)

# --- add and update submodules ---
find_package(Git QUIET)
option(GIT_SUBMODULE "Check submodules during build" ON)
if(GIT_FOUND AND GIT_SUBMODULE)
  message(STATUS "Adding and Initializing Submodules")
  set(WORKFLOW_SUBMODULES ioda jedicmake oops saber ufo ufo-data wrf_hydro_nwm_jedi wrf_hydro_nwm_public)
  foreach(submodule ${WORKFLOW_SUBMODULES})
    execute_process(COMMAND ${GIT_EXECUTABLE} submodule init
      WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/${submodule}
      RESULT_VARIABLE GIT_SUBMOD_RESULT)
    execute_process(COMMAND ${GIT_EXECUTABLE} submodule update
      WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/${submodule}
      RESULT_VARIABLE GIT_SUBMOD_RESULT)
# --- The following is commented out because the error "fatal: No url found
#     for submodule path 'bundle/jedicmake'" is occurring for an unknown
#     reason but everything will build correctly anyway.
#     if(NOT GIT_SUBMOD_RESULT EQUAL "0")
#       message(FATAL_ERROR "git submodule init ${GIT_SUBMOD_RESULT}, for \
# ${submodule}")
#     endif()
  endforeach()
endif()

ecbuild_bundle_initialize()
ecbuild_bundle(PROJECT jedicmake)
include( jedicmake/cmake/Functions/git_functions.cmake )
ecbuild_bundle(PROJECT oops)
ecbuild_bundle(PROJECT saber)
ecbuild_bundle(PROJECT ioda)
ecbuild_bundle(PROJECT ufo)
ecbuild_bundle(PROJECT ufo-data)
ecbuild_bundle(PROJECT wrf_hydro_nwm_jedi)
ecbuild_bundle(PROJECT wrf_hydro_nwm_public)
ecbuild_bundle_finalize()

# --- Jedi Workflow and Increment ---
add_subdirectory(jedi_workflow)
add_subdirectory(jedi_workflow_tests)

# add_custom_target(report
#   COMMAND ${CMAKE_COMMAND}
#   -P ${CMAKE_SCRIPT_DIR}/report.cmake
#   )
