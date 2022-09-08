cmake_minimum_required( VERSION 3.15 )
project( WRF-Hydro-JEDI-WorkflowPY VERSION 0.0.2 LANGUAGES C CXX Fortran)


set( ECBUILD_DEFAULT_BUILD_TYPE Release )
set( Python_EXECUTABLE python3 )
set( CMAKE_Fortran_FLAGS "-g ${CMAKE_Fortran_FLAGS}" )

include( ecbuild_system NO_POLICY_SCOPE )
ecbuild_requires_macro_version( 2.5 )

ecbuild_declare_project()
ecbuild_enable_fortran( REQUIRED )
ecbuild_find_python( REQUIRED )

# set( JEDI_OUTPUT_DIR /glade/work/soren/src/jedi/run/run_090321 )
# ecbuild_add_option( FEATURE JEDI_OUTPUT_DIR )
  # )


add_subdirectory( workflowpy )
add_subdirectory( tests )



# add_executable(w jedi_workflow.py)
# artless: ecbuild/share/ecbuild/cmake/ has documentation


if (DEFINED ENV{NETCDF})
  message("NETCDF defined as $ENV{NETCDF}")
  set(NETCDF_FLAGS "-I$(NETCDF)/include -L$(NETCDF)/lib -lnetcdff")
  set(CMAKE_Fortran_FLAGS "${NETCDF_FLAGS} ${CMAKE_Fortran_FLAGS}")
else ()
  message(SEND_ERROR "Error: NETCDF environment variable is not defined")
endif()

if (DEFINED ENV{NETCDF_LIBRARIES})
  message("NETCDF_LIBRARIES defined as $ENV{NETCDF_FLAGS}")
  set(CMAKE_EXE_LINKER_FLAGS "-L$ENV{NETCDF_LIBRARIES} -lnetcdff ${CMAKE_EXE_LINKER_FLAGS}")
  message("CMAKE_EXE_LINKER_FLAGS are ${CMAKE_EXE_LINKER_FLAGS}")
else ()
  message(SEND_ERROR "Error: NETCDF environment variable is not defined")
endif()

enable_testing()
add_subdirectory(src)
add_subdirectory(tests)

add_custom_target(report
  COMMAND ${CMAKE_COMMAND}
  -P ${CMAKE_SOURCE_DIR}/src/report.cmake
  )
