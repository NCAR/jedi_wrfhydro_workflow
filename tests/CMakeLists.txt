ecbuild_add_test( TARGET workflow1_load_workflowpy
                  TYPE SCRIPT
                  COMMAND ${Python_EXECUTABLE}
                  ARGS ${CMAKE_CURRENT_SOURCE_DIR}/workflow1.py
		       ${CMAKE_CURRENT_SOURCE_DIR}/yamls/jedi_work.yaml)

ecbuild_add_test( TARGET workflow2_read_yaml_incomplete
                  TYPE SCRIPT
                  COMMAND ${Python_EXECUTABLE}
                  ARGS ${CMAKE_CURRENT_SOURCE_DIR}/workflow2.py
		       ${CMAKE_CURRENT_SOURCE_DIR}/yamls/jedi_work.yaml)

add_subdirectory(jedi_increment)
