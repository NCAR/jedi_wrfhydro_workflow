set(workflow_testdata_version "v1.0.3")

# add Makefile target to setup testcase
add_custom_target(testcase
  DEPENDS testcase_setup testcase_run)

add_custom_target(testcase_setup
  COMMAND bash
  ${CMAKE_CURRENT_SOURCE_DIR}/setup_cmake_testcase.sh ${CMAKE_BINARY_DIR} ${workflow_testdata_version})

add_custom_target(testcase_run
  DEPENDS testcase_setup
  COMMAND bash
  ${CMAKE_CURRENT_SOURCE_DIR}/run_cmake_testcase.sh ${CMAKE_BINARY_DIR} ${workflow_testdata_version})

add_custom_target(testcase_clean
  COMMAND bash
  ${CMAKE_CURRENT_SOURCE_DIR}/clean_cmake_testcase.sh ${CMAKE_BINARY_DIR} ${workflow_testdata_version})
