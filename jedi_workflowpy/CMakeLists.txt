# Python_add_library(workflowpy
#   workflowpy.py)
# ecbuild_add_test( TARGET workflow_driver
#                   TYPE SCRIPT
#                   COMMAND ${Python_EXECUTABLE}
#                   ARGS ${CMAKE_CURRENT_SOURCE_DIR}/workflow_driver.py
# 		       ${CMAKE_CURRENT_SOURCE_DIR}/yamls/jedi_work.yaml)

set( PYTHON_LIBRARIES ${CMAKE_CURRENT_SOURCE_DIR}/workflowpy.py )
