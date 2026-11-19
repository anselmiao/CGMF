# copy reference files to local
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/histories.cgmf.parallel.0.reference
          ${CMAKE_CURRENT_SOURCE_DIR}/histories.cgmf.parallel.1.reference
     DESTINATION ${CMAKE_CURRENT_BINARY_DIR})

file(READ ${CMAKE_CURRENT_BINARY_DIR}/histories.cgmf.parallel.0.reference CONTENTS)
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/histories.cgmf.serial.0.reference "${CONTENTS}")
file(READ ${CMAKE_CURRENT_BINARY_DIR}/histories.cgmf.parallel.1.reference CONTENTS)
file(APPEND ${CMAKE_CURRENT_BINARY_DIR}/histories.cgmf.serial.0.reference "${CONTENTS}")


# cgmf.x arguments
set(args     -n 40 -e 2.53e-8 -i 92235 -f histories.cgmf.serial)
set(args.mpi -n 20 -e 2.53e-8 -i 92235 -f histories.cgmf.parallel)


if(NOT ${util}.x.MPI)
  # cgmf.x serial tests
  add_test(NAME cgmf_u235nf-th-events_init
           COMMAND ${CMAKE_COMMAND} -E remove
                   histories.cgmf.serial.0)
  set_tests_properties(cgmf_u235nf-th-events_init PROPERTIES
                       FIXTURES_SETUP cgmf_u235nf-th-events_init)

  add_test(NAME cgmf_u235nf-th-events_exec
           COMMAND ${util}.x ${args}
           COMMAND_EXPAND_LISTS)
  set_tests_properties(cgmf_u235nf-th-events_exec PROPERTIES
                       FIXTURES_SETUP cgmf_u235nf-th-events_exec
                       FIXTURES_REQUIRED cgmf_u235nf-th-events_init)

  # The discrete-start index correction changes rank-0 histories.
  # Keep a strict full-file regression using the reviewed SHA-256 baseline.
  add_test(NAME cgmf_u235nf-th-events_diff
           COMMAND ${CMAKE_COMMAND}
                   -DINPUT=${CMAKE_CURRENT_BINARY_DIR}/histories.cgmf.serial.0
                   -DEXPECTED_SHA256=2b504cc64d3170fb2736c5c29e0a9119b72c53a6fef21a5689211f2a8f926a5a
                   -P ${CMAKE_SOURCE_DIR}/utils/cgmf/tests/checkHistorySha256.cmake)
  set_tests_properties(cgmf_u235nf-th-events_diff PROPERTIES
                       FIXTURES_REQUIRED cgmf_u235nf-th-events_exec)

else(${util}.x.MPI)
  # cgmf.mpi.x mpi tests
  set(numprocs.mpi 2)
  add_test(NAME cgmf_u235nf-th-events_mpi-init
           COMMAND ${CMAKE_COMMAND} -E remove
                   histories.cgmf.parallel.0 histories.cgmf.parallel.1)
  set_tests_properties(cgmf_u235nf-th-events_mpi-init PROPERTIES
                       FIXTURES_SETUP cgmf_u235nf-th-events_mpi-init)


  add_test(NAME cgmf_u235nf-th-events_mpi-exec
           COMMAND ${MPIEXEC_EXECUTABLE} ${MPIEXEC_NUMPROC_FLAG}
                   ${numprocs.mpi} ${MPIEXEC_PREFLAGS}
                   $<TARGET_FILE:${util}.x> ${MPIEXEC_POSTFLAGS} ${args.mpi}
           COMMAND_EXPAND_LISTS)
  set_tests_properties(cgmf_u235nf-th-events_mpi-exec PROPERTIES
                       FIXTURES_SETUP cgmf_u235nf-th-events_mpi-exec
                       FIXTURES_REQUIRED cgmf_u235nf-th-events_mpi-init)

  add_test(NAME cgmf_u235nf-th-events_mpi-diff-0
           COMMAND ${CMAKE_COMMAND}
                   -DINPUT=${CMAKE_CURRENT_BINARY_DIR}/histories.cgmf.parallel.0
                   -DEXPECTED_SHA256=5a39d3f29c2645c854167c7f47204a77839992ed35b67c79a137fc2aab691972
                   -P ${CMAKE_SOURCE_DIR}/utils/cgmf/tests/checkHistorySha256.cmake)
  set_tests_properties(cgmf_u235nf-th-events_mpi-diff-0 PROPERTIES
                       FIXTURES_REQUIRED cgmf_u235nf-th-events_mpi-exec)

  add_test(NAME cgmf_u235nf-th-events_mpi-diff-1
           COMMAND ${CMAKE_COMMAND} -E compare_files
                   histories.cgmf.parallel.1.reference histories.cgmf.parallel.1)
  set_tests_properties(cgmf_u235nf-th-events_mpi-diff-1 PROPERTIES
                       FIXTURES_REQUIRED cgmf_u235nf-th-events_mpi-exec)

endif()
