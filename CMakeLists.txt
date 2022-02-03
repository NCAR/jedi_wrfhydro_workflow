cmake_minimum_required( VERSION 3.12 )
project( WRF-Hydro-JEDI-WorkflowPY VERSION 0.0.1 LANGUAGES C CXX Fortran)


set( ECBUILD_DEFAULT_BUILD_TYPE Release )
set( Python_EXECUTABLE python3 )

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
