#include <cstdlib>
#include <iostream>
#include <string>
#include "g2_sidecar_transaction.h"

static void require(bool condition, const char *message) {
  if (!condition) {
    std::cerr << "g2-sidecar-transaction test failed: " << message << std::endl;
    std::exit(EXIT_FAILURE);
  }
}

int main() {
  G2SidecarEventBuffer buffer;

  // Normal pair: both side payloads remain buffered until HF completes the pair.
  require(buffer.stage(1, "LF", "nLF\\n", "mLF\\n") == G2SidecarStageResult::Staged,
          "LF must stage");
  require(buffer.active(), "buffer must be active after LF");
  require(buffer.eventId() == 1, "buffer must retain event id");
  require(buffer.neutronPair() == "nLF\\n", "HF payload must not appear before HF");
  require(buffer.mixedPair() == "mLF\\n", "mixed HF payload must not appear before HF");
  require(buffer.stage(1, "HF", "nHF\\n", "mHF\\n") == G2SidecarStageResult::Complete,
          "matching HF must complete pair");
  require(buffer.neutronPair() == "nLF\\nnHF\\n", "neutron pair order must be LF then HF");
  require(buffer.mixedPair() == "mLF\\nmHF\\n", "mixed pair order must be LF then HF");

  // Empty neutron payloads are valid (zero-neutron fragments); mixed summaries still pair.
  buffer.reset();
  require(!buffer.active(), "reset must clear active state");
  require(buffer.stage(2, "LF", "", "mLF\\n") == G2SidecarStageResult::Staged,
          "zero-neutron LF must stage");
  require(buffer.stage(2, "HF", "", "mHF\\n") == G2SidecarStageResult::Complete,
          "zero-neutron HF must complete pair");
  require(buffer.neutronPair().empty(), "zero-neutron pair must remain empty");
  require(buffer.mixedPair() == "mLF\\nmHF\\n", "zero-neutron mixed summaries must be retained");

  // Fail-closed ordering and identity checks.
  buffer.reset();
  require(buffer.stage(3, "HF", "", "mHF\\n") == G2SidecarStageResult::Invalid,
          "HF without LF must be rejected");
  require(buffer.stage(4, "LF", "", "mLF\\n") == G2SidecarStageResult::Staged,
          "new LF must stage after reset");
  require(buffer.stage(5, "HF", "", "wrong-event\\n") == G2SidecarStageResult::Invalid,
          "event-id mismatch must be rejected");
  require(buffer.active() && buffer.eventId() == 4, "mismatch must not destroy pending LF");
  require(buffer.stage(4, "LF", "", "duplicate\\n") == G2SidecarStageResult::Invalid,
          "duplicate LF must be rejected");
  require(buffer.stage(4, "HF", "", "mHF\\n") == G2SidecarStageResult::Complete,
          "correct HF must still complete after rejected attempts");
  require(buffer.stage(4, "HF", "", "duplicate-HF\\n") == G2SidecarStageResult::Invalid,
          "duplicate HF must be rejected");
  require(buffer.stage(6, "LF", "", "next-event\\n") == G2SidecarStageResult::Invalid,
          "new LF must not overwrite an uncommitted completed pair");

  // Invalid context must never initialize or mutate the buffer.
  buffer.reset();
  require(buffer.stage(0, "LF", "", "") == G2SidecarStageResult::Invalid,
          "zero event id must be rejected");
  require(buffer.stage(7, "XX", "", "") == G2SidecarStageResult::Invalid,
          "unknown fragment side must be rejected");
  require(!buffer.active(), "invalid context must leave buffer inactive");
  return EXIT_SUCCESS;
}
