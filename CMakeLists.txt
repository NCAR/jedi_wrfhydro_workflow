cmake_minimum_required( VERSION 3.15 )

project( WRF-Hydro-JEDI-WorkflowPY VERSION 0.0.2 LANGUAGES C CXX Fortran)

set( ECBUILD_DEFAULT_BUILD_TYPE Release )
set( Python_EXECUTABLE python3 )
set( CMAKE_Fortran_FLAGS "-g ${CMAKE_Fortran_FLAGS}" )
set( CMAKE_SCRIPT_DIR ${CMAKE_SOURCE_DIR}/src/cmake_scripts )

include( ecbuild_system NO_POLICY_SCOPE )
ecbuild_requires_macro_version( 2.5 )

ecbuild_declare_project()
ecbuild_enable_fortran( REQUIRED )
ecbuild_find_python( REQUIRED )
ecbuild_find_mpi(
    COMPONENTS C Fortran
    REQUIRED )
find_package( NetCDF REQUIRED COMPONENTS Fortran )

enable_testing()
add_subdirectory(src)
add_subdirectory(tests)

add_custom_target(report
  COMMAND ${CMAKE_COMMAND}
  -P ${CMAKE_SCRIPT_DIR}/report.cmake
  )

# not going this route
# add_custom_target(workflow
#   COMMAND ${CMAKE_COMMAND}
#   -DPython_EXECUTABLE=${Python_EXECUTABLE}
#   -DWORKFLOW_YAML_PATH=${WORKFLOW_YAML_PATH}
#   -P ${CMAKE_SCRIPT_DIR}/run_workflow.cmake
#   )
# add_dependencies(run jedi_snow_increment)
# add_dependencies(workflow jedi_snow_increment)
