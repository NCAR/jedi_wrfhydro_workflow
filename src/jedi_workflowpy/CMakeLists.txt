# Python_add_library(workflowpy
#   workflowpy.py)
# ecbuild_add_test( TARGET workflow_driver
#                   TYPE SCRIPT
#                   COMMAND ${Python_EXECUTABLE}
#                   ARGS ${CMAKE_CURRENT_SOURCE_DIR}/workflow_driver.py
# 		       ${CMAKE_CURRENT_SOURCE_DIR}/yamls/jedi_work.yaml)

set( PYTHON_LIBRARIES ${CMAKE_CURRENT_SOURCE_DIR}/workflowpy.py )

configure_file(${CMAKE_CURRENT_SOURCE_DIR}/jedi_workflowpy.py
  ${CMAKE_BINARY_DIR}/bin/jedi_workflowpy.py )
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/workflowFile.py
  ${CMAKE_BINARY_DIR}/bin/workflowFile.py   )
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/workflowTime.py
  ${CMAKE_BINARY_DIR}/bin/workflowTime.py )
