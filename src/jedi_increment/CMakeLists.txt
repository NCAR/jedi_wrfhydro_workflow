add_library(jedi_disag jedi_disag_mod.f90)
add_library(var_names input_var_names.f90)

add_executable(jedi_snow_increment jedi_snow_incr.f90)

target_link_libraries(jedi_snow_increment
  PUBLIC jedi_disag var_names)
