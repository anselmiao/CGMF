#include "discreteLevelLookup.h"

#include <cassert>

int main() {
  const int zaids[] = {35089, 40105, 53136};

  // First and last loaded entries must be found.
  assert(cgmf::findDiscreteLevelIndex(zaids, 3, 35089) == 0);
  assert(cgmf::findDiscreteLevelIndex(zaids, 3, 53136) == 2);

  // An absent ZAID returns -1 without probing past the loaded range.
  assert(cgmf::findDiscreteLevelIndex(zaids, 3, 99999) == -1);

  // A ZAID stored beyond numNuclei is not part of the loaded database.
  assert(cgmf::findDiscreteLevelIndex(zaids, 2, 53136) == -1);

  // Empty and invalid inputs are treated as not found.
  assert(cgmf::findDiscreteLevelIndex(zaids, 0, 35089) == -1);
  assert(cgmf::findDiscreteLevelIndex(zaids, -1, 35089) == -1);
  assert(cgmf::findDiscreteLevelIndex(0, 3, 35089) == -1);

  return 0;
}
