#include "mchf.h"

#include <cassert>

int main() {
  MCPoint unset;
  assert(!unset.isValid());
  assert(!unset.isUnmappable());
  assert(unset.getStatus() == MCPointStatus::Uninitialized);

  MCPoint state(0, 1, 2, 3, 4.5);
  assert(state.isValid());
  assert(!state.ifDiscrete());

  state.setDiscrete();
  assert(state.isValid());
  assert(state.ifDiscrete());

  state.markUnmappable();
  assert(!state.isValid());
  assert(state.isUnmappable());
  assert(state.getStatus() == MCPointStatus::Unmappable);

  MCPoint copied = state;
  assert(copied.isUnmappable());

  MCHistory history;
  history.set(gammaray, 0.0, state, copied);
  assert(history.getMCPoint().isUnmappable());
  assert(history.getDaughterMCPoint().isUnmappable());

  // A fresh valid assignment must explicitly restore the state to Valid.
  state.set(1, -1, 0, 0, 0.25);
  assert(state.isValid());
  assert(!state.isUnmappable());
  assert(!state.ifDiscrete());
  return 0;
}
