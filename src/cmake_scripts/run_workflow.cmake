execute_process(COMMAND
  ${Python_EXECUTABLE}
  ${CMAKE_SOURCE_DIR}/src/jedi_workflowpy/jedi_workflowpy.py
  ${WORKFLOW_YAML_PATH}
  WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
  COMMAND_ECHO STDOUT)
