add_library(jedi_disag jedi_disag_mod.f90)
add_library(var_names input_var_names.f90)

add_executable(jedi_snow_increment jedi_snow_incr.f90)

target_link_libraries(jedi_snow_increment
  PUBLIC jedi_disag var_names NetCDF::NetCDF_Fortran MPI::MPI_Fortran)

add_custom_command(TARGET jedi_snow_increment POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy
  ${CMAKE_CURRENT_BINARY_DIR}/jedi_snow_increment
  ${CMAKE_BINARY_DIR}/bin/jedi_snow_increment
  )
