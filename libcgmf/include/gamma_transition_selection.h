#ifndef CGMF_GAMMA_TRANSITION_SELECTION_H
#define CGMF_GAMMA_TRANSITION_SELECTION_H

// Pure electromagnetic selection-rule predicate for an explicitly specified
// multipolarity. This does not infer multipolarity or transition probability.
namespace cgmf {

enum class GammaTransitionMultipolarity {
  E1,
  M1,
  E2
};

inline bool isAllowedGammaTransition(
    double initial_energy,
    double initial_spin,
    int initial_parity,
    double final_energy,
    double final_spin,
    int final_parity,
    GammaTransitionMultipolarity multipolarity) {

  if (initial_spin < 0.0 || final_spin < 0.0) return false;
  if ((initial_parity != 1 && initial_parity != -1) ||
      (final_parity != 1 && final_parity != -1)) return false;

  // A real emitted photon must carry positive energy.
  if (!(final_energy < initial_energy)) return false;

  int order = 0;
  int expected_parity_product = 0;
  switch (multipolarity) {
    case GammaTransitionMultipolarity::E1:
      order = 1;
      expected_parity_product = -1;
      break;
    case GammaTransitionMultipolarity::M1:
      order = 1;
      expected_parity_product = 1;
      break;
    case GammaTransitionMultipolarity::E2:
      order = 2;
      expected_parity_product = 1;
      break;
    default:
      return false;
  }

  // |Ji-Jf| <= L <= Ji+Jf. This also excludes 0 -> 0 for L >= 1.
  const double delta_spin = initial_spin > final_spin
      ? initial_spin - final_spin : final_spin - initial_spin;
  if (delta_spin > static_cast<double>(order)) return false;
  if (static_cast<double>(order) > initial_spin + final_spin) return false;

  return initial_parity * final_parity == expected_parity_product;
}

}  // namespace cgmf

#endif  // CGMF_GAMMA_TRANSITION_SELECTION_H
