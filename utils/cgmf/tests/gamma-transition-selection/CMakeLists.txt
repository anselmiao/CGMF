add_executable(gamma-transition-selection-test gamma-transition-selection.cpp)
target_include_directories(gamma-transition-selection-test PRIVATE
  ${CMAKE_SOURCE_DIR}/libcgmf/include)
add_test(NAME gamma-transition-selection COMMAND gamma-transition-selection-test)
