find_program(NCCMP_EXE "nccmp")
if (NOT NCCMP_EXE)
  message(FATAL_ERROR "nccmp is missing, load into PATH")
endif()

execute_process(COMMAND
  nccmp -dfqsS tests/RESTART.2017010100_DOMAIN1.test1 tests/RESTART.2017010100_DOMAIN1.test2
  WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
  COMMAND_ECHO STDOUT)
