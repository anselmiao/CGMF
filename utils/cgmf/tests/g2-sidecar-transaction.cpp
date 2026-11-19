#include <cassert>
#include <string>
#include "g2_sidecar_transaction.h"

int main() {
  G2SidecarEventBuffer buffer;
  assert(buffer.stage(1, "LF", "nLF\n", "mLF\n") == G2SidecarStageResult::Staged);
  assert(buffer.active());
  assert(buffer.stage(1, "HF", "nHF\n", "mHF\n") == G2SidecarStageResult::Complete);
  assert(buffer.neutronPair() == "nLF\nnHF\n");
  assert(buffer.mixedPair() == "mLF\nmHF\n");
  buffer.reset();
  assert(!buffer.active());

  assert(buffer.stage(2, "LF", "", "mLF\n") == G2SidecarStageResult::Staged);
  assert(buffer.stage(3, "HF", "", "mHF\n") == G2SidecarStageResult::Invalid);
  assert(buffer.active());
  buffer.reset();

  assert(buffer.stage(4, "HF", "", "mHF\n") == G2SidecarStageResult::Invalid);
  assert(buffer.stage(5, "LF", "", "mLF\n") == G2SidecarStageResult::Staged);
  assert(buffer.stage(5, "LF", "", "duplicate\n") == G2SidecarStageResult::Invalid);
  assert(buffer.stage(5, "HF", "", "mHF\n") == G2SidecarStageResult::Complete);
  buffer.reset();

  assert(buffer.stage(0, "LF", "", "") == G2SidecarStageResult::Invalid);
  assert(buffer.stage(6, "XX", "", "") == G2SidecarStageResult::Invalid);
  return 0;
}
