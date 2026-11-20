#include "cgm.h"
#include "gdr.h"

#include <cassert>
#include <cmath>

int main() {
  GDR parameters[1];
  parameters[0].setGDR("E2", 15.0, 4.0, 1.0);
  gdrParameterSave(1, parameters);

  const double standard = gdrGammaTransmission(SL, 2, 0.0, E2, 0.0, 0.0);
  const double generalized = gdrGammaTransmission(GL, 2, 0.0, E2, 10.0, 0.0);
  assert(std::isfinite(standard) && standard == 0.0);
  assert(std::isfinite(generalized) && generalized == 0.0);

  return 0;
}
