add_executable(g2-sidecar-transaction-test ../g2-sidecar-transaction.cpp)
target_include_directories(g2-sidecar-transaction-test PRIVATE
  ${CMAKE_SOURCE_DIR}/libcgmf/include)
add_test(NAME g2-sidecar-transaction COMMAND g2-sidecar-transaction-test)
