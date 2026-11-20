#ifndef CGMF_G2_SIDECAR_TRANSACTION_H
#define CGMF_G2_SIDECAR_TRANSACTION_H

#include <string>

enum class G2SidecarStageResult {
  Staged,
  Complete,
  Invalid
};

// Buffers one LF/HF pair. It deliberately performs no I/O and no recovery.
class G2SidecarEventBuffer {
 public:
  G2SidecarStageResult stage(unsigned long long eventId, const std::string &side,
                             const std::string &neutronPayload,
                             const std::string &mixedPayload) {
    if (eventId == 0 || (side != "LF" && side != "HF")) return G2SidecarStageResult::Invalid;
    if (side == "LF") {
      if (active_) return G2SidecarStageResult::Invalid;
      active_ = true;
      eventId_ = eventId;
      neutronLF_ = neutronPayload;
      mixedLF_ = mixedPayload;
      return G2SidecarStageResult::Staged;
    }
    if (!active_ || eventId_ != eventId || hasHF_) return G2SidecarStageResult::Invalid;
    hasHF_ = true;
    neutronHF_ = neutronPayload;
    mixedHF_ = mixedPayload;
    return G2SidecarStageResult::Complete;
  }

  bool active() const { return active_; }
  unsigned long long eventId() const { return eventId_; }
  std::string neutronPair() const { return neutronLF_ + neutronHF_; }
  std::string mixedPair() const { return mixedLF_ + mixedHF_; }

  void reset() {
    active_ = false;
    hasHF_ = false;
    eventId_ = 0;
    neutronLF_.clear();
    neutronHF_.clear();
    mixedLF_.clear();
    mixedHF_.clear();
  }

 private:
  bool active_ = false;
  bool hasHF_ = false;
  unsigned long long eventId_ = 0;
  std::string neutronLF_, neutronHF_;
  std::string mixedLF_, mixedHF_;
};

#endif
