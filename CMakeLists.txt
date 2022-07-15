cmake_minimum_required(VERSION 3.15)
project(IncrementJedi VERSION 0.0.1 LANGUAGES Fortran)

set(CMAKE_Fortran_FLAGS "-g ${CMAKE_Fortran_FLAGS}")

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
