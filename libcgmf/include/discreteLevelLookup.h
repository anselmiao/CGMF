#ifndef CGMF_DISCRETE_LEVEL_LOOKUP_H
#define CGMF_DISCRETE_LEVEL_LOOKUP_H

namespace cgmf {

// Return the matching database index, or -1 when the ZAID is not loaded.
// The search is deliberately restricted to the number of parsed entries.
inline int findDiscreteLevelIndex(const int *zaidIndex,
                                  int numNuclei,
                                  int targetZAID) {
  if (zaidIndex == 0 || numNuclei <= 0) return -1;

  for (int index = 0; index < numNuclei; ++index) {
    if (zaidIndex[index] == targetZAID) return index;
  }

  return -1;
}

} // namespace cgmf

#endif // CGMF_DISCRETE_LEVEL_LOOKUP_H
