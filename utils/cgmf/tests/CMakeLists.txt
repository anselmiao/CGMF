add_subdirectory(cf252sf-events)
add_subdirectory(cf254sf-events)

add_subdirectory(pu238sf-events)
add_subdirectory(pu240sf-events)
add_subdirectory(pu242sf-events)
add_subdirectory(pu244sf-events)

add_subdirectory(pu239nf-th-events)
add_subdirectory(pu239nf-10MeV-events)
add_subdirectory(pu239nf-15MeV-events)

add_subdirectory(pu241nf-th-events)
add_subdirectory(pu241nf-10MeV-events)
add_subdirectory(pu241nf-18MeV-events)

add_subdirectory(u233nf-th-events)
add_subdirectory(u233nf-10MeV-events)
add_subdirectory(u233nf-18MeV-events)

add_subdirectory(u234nf-th-events)
add_subdirectory(u234nf-10MeV-events)
add_subdirectory(u234nf-18MeV-events)

add_subdirectory(u235nf-th-events)
add_subdirectory(u235nf-10MeV-events)
add_subdirectory(u235nf-18MeV-events)

add_subdirectory(u238nf-th-events)
add_subdirectory(u238nf-10MeV-events)
add_subdirectory(u238nf-18MeV-events)

add_subdirectory(np237nf-th-events)
add_subdirectory(np237nf-10MeV-events)
add_subdirectory(np237nf-18MeV-events)

add_subdirectory(cf252sf-yields)
add_subdirectory(u235nf-10MeV-yields)
add_subdirectory(pu239nf-16MeV-yields)

add_subdirectory(u235nf-time-events)
add_subdirectory(pu239nf-start-events)

add_subdirectory(gamma-transition-selection)

add_executable(gamma-transmission-zero-energy-test
  gamma-transmission-zero-energy.cpp
  ${CMAKE_SOURCE_DIR}/libcgmf/src/gtrans.cpp)
target_include_directories(gamma-transmission-zero-energy-test PRIVATE
  ${CMAKE_SOURCE_DIR}/libcgmf/include)
add_test(NAME gamma-transmission-zero-energy COMMAND gamma-transmission-zero-energy-test)
add_subdirectory(mcpoint-status)

add_subdirectory(g2-sidecar-transaction)
