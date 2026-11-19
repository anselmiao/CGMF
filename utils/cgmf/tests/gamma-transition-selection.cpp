#include "gamma_transition_selection.h"

#include <cassert>
#include <limits>

using cgmf::GammaTransitionMultipolarity;
using cgmf::isAllowedGammaTransition;

int main() {
  // E1: opposite parity, |Delta J| <= 1, and positive photon energy.
  assert(isAllowedGammaTransition(2.0, 1.5, 1, 1.0, 0.5, -1,
                                  GammaTransitionMultipolarity::E1));
  assert(!isAllowedGammaTransition(2.0, 1.5, 1, 1.0, 0.5, 1,
                                  GammaTransitionMultipolarity::E1));
  assert(!isAllowedGammaTransition(2.0, 2.5, 1, 1.0, 0.5, -1,
                                  GammaTransitionMultipolarity::E1));
  assert(!isAllowedGammaTransition(1.0, 1.5, 1, 1.0, 0.5, -1,
                                  GammaTransitionMultipolarity::E1));

  // M1: same parity and rank-1 angular-momentum triangle.
  assert(isAllowedGammaTransition(2.0, 1.5, -1, 1.0, 0.5, -1,
                                  GammaTransitionMultipolarity::M1));
  assert(!isAllowedGammaTransition(2.0, 1.5, -1, 1.0, 0.5, 1,
                                  GammaTransitionMultipolarity::M1));

  // E2: same parity; rank 2 permits a two-unit spin change.
  assert(isAllowedGammaTransition(3.0, 2.5, 1, 1.0, 0.5, 1,
                                  GammaTransitionMultipolarity::E2));
  assert(!isAllowedGammaTransition(3.0, 3.5, 1, 1.0, 0.5, 1,
                                  GammaTransitionMultipolarity::E2));
  assert(!isAllowedGammaTransition(3.0, 0.0, 1, 1.0, 0.0, 1,
                                  GammaTransitionMultipolarity::E2));

  // Invalid parity labels and negative spins are rejected.
  assert(!isAllowedGammaTransition(2.0, 1.0, 0, 1.0, 0.0, -1,
                                   GammaTransitionMultipolarity::E1));
  assert(!isAllowedGammaTransition(2.0, -0.5, 1, 1.0, 0.5, -1,
                                   GammaTransitionMultipolarity::E1));
  const double nan = std::numeric_limits<double>::quiet_NaN();
  assert(!isAllowedGammaTransition(2.0, nan, 1, 1.0, 0.5, -1,
                                   GammaTransitionMultipolarity::E1));
  assert(!isAllowedGammaTransition(2.0, 1.5, 1, 1.0, nan, -1,
                                   GammaTransitionMultipolarity::E1));
  return 0;
}
