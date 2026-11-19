add_executable(mcpoint-status-test mcpoint-status.cpp)
target_include_directories(mcpoint-status-test PRIVATE
  ${CMAKE_SOURCE_DIR}/libcgmf/include)
add_test(NAME mcpoint-status COMMAND mcpoint-status-test)
