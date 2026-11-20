# copy reference files to local
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/histories.cgmf.parallel.0.reference
          ${CMAKE_CURRENT_SOURCE_DIR}/histories.cgmf.parallel.1.reference
     DESTINATION ${CMAKE_CURRENT_BINARY_DIR})

file(READ ${CMAKE_CURRENT_BINARY_DIR}/histories.cgmf.parallel.0.reference CONTENTS)
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/histories.cgmf.serial.0.reference "${CONTENTS}")
file(READ ${CMAKE_CURRENT_BINARY_DIR}/histories.cgmf.parallel.1.reference CONTENTS)
file(APPEND ${CMAKE_CURRENT_BINARY_DIR}/histories.cgmf.serial.0.reference "${CONTENTS}")


# cgmf.x arguments
set(args     -n 40 -e 0.0 -i 94242 -f histories.cgmf.serial)
set(args.mpi -n 20 -e 0.0 -i 94242 -f histories.cgmf.parallel)


if(NOT ${util}.x.MPI)
  # cgmf.x serial tests
  add_test(NAME cgmf_pu242sf-events_init
           COMMAND ${CMAKE_COMMAND} -E remove
                   histories.cgmf.serial.0)
  set_tests_properties(cgmf_pu242sf-events_init PROPERTIES
                       FIXTURES_SETUP cgmf_pu242sf-events_init)

  add_test(NAME cgmf_pu242sf-events_exec
           COMMAND ${util}.x ${args}
           COMMAND_EXPAND_LISTS)
  set_tests_properties(cgmf_pu242sf-events_exec PROPERTIES
                       FIXTURES_SETUP cgmf_pu242sf-events_exec
                       FIXTURES_REQUIRED cgmf_pu242sf-events_init)

  # The discrete-start index correction changes rank-0 histories.
  # Keep a strict full-file regression using the reviewed SHA-256 baseline.
  add_test(NAME cgmf_pu242sf-events_diff
           COMMAND ${CMAKE_COMMAND}
                   -DINPUT=${CMAKE_CURRENT_BINARY_DIR}/histories.cgmf.serial.0
                   -DEXPECTED_SHA256=bfa266d2d13dec98ed2dc1d425fee94ff691e1f3b162e6075db68c9918c65402
                   -P ${CMAKE_SOURCE_DIR}/utils/cgmf/tests/checkHistorySha256.cmake)
  set_tests_properties(cgmf_pu242sf-events_diff PROPERTIES
                       FIXTURES_REQUIRED cgmf_pu242sf-events_exec)

else(${util}.x.MPI)
  # cgmf.mpi.x mpi tests
  set(numprocs.mpi 2)
  add_test(NAME cgmf_pu242sf-events_mpi-init
           COMMAND ${CMAKE_COMMAND} -E remove
                   histories.cgmf.parallel.0 histories.cgmf.parallel.1)
  set_tests_properties(cgmf_pu242sf-events_mpi-init PROPERTIES
                       FIXTURES_SETUP cgmf_pu242sf-events_mpi-init)


  add_test(NAME cgmf_pu242sf-events_mpi-exec
           COMMAND ${MPIEXEC_EXECUTABLE} ${MPIEXEC_NUMPROC_FLAG}
                   ${numprocs.mpi} ${MPIEXEC_PREFLAGS}
                   $<TARGET_FILE:${util}.x> ${MPIEXEC_POSTFLAGS} ${args.mpi}
           COMMAND_EXPAND_LISTS)
  set_tests_properties(cgmf_pu242sf-events_mpi-exec PROPERTIES
                       FIXTURES_SETUP cgmf_pu242sf-events_mpi-exec
                       FIXTURES_REQUIRED cgmf_pu242sf-events_mpi-init)

  add_test(NAME cgmf_pu242sf-events_mpi-diff-0
           COMMAND ${CMAKE_COMMAND}
                   -DINPUT=${CMAKE_CURRENT_BINARY_DIR}/histories.cgmf.parallel.0
                   -DEXPECTED_SHA256=d49d9157c3fb5bd4088e4ff02adf7b7a595eeaf05bd6a22cae96d7c40cebddc7
                   -P ${CMAKE_SOURCE_DIR}/utils/cgmf/tests/checkHistorySha256.cmake)
  set_tests_properties(cgmf_pu242sf-events_mpi-diff-0 PROPERTIES
                       FIXTURES_REQUIRED cgmf_pu242sf-events_mpi-exec)

  add_test(NAME cgmf_pu242sf-events_mpi-diff-1
           COMMAND ${CMAKE_COMMAND} -E compare_files
                   histories.cgmf.parallel.1.reference histories.cgmf.parallel.1)
  set_tests_properties(cgmf_pu242sf-events_mpi-diff-1 PROPERTIES
                       FIXTURES_REQUIRED cgmf_pu242sf-events_mpi-exec)

endif()
