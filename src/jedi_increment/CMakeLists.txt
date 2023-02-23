add_library(jedi_disag STATIC jedi_disag_mod.f90)
add_library(var_names STATIC input_var_names.f90)

add_executable(jedi_increment jedi_incr.f90)

target_link_libraries(jedi_increment
  PUBLIC jedi_disag var_names NetCDF::NetCDF_Fortran MPI::MPI_Fortran)

add_custom_command(TARGET jedi_increment POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy
  ${CMAKE_CURRENT_BINARY_DIR}/jedi_increment
  ${CMAKE_BINARY_DIR}/bin/jedi_increment
  )
