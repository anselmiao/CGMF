# CGMF G2 Mixed History Sidecar v1

The opt-in environment variable `CGMF_G2_MIXED_HISTORY_SIDECAR` writes one JSON object per fission fragment to JSONL. It is independent of the existing `CGMF_G2_SIDECAR` neutron-only output.

## Record identity

- `schema`: `cgmf.g2.mixed-history.v1`
- `run_id`, `event_id`, `fragment_side`: same event context as the existing G2 neutron sidecar.
- Exactly one record is expected for each event/fragment pair: LF and HF, including fragments with zero neutron emissions.

## Initial fragment

`initial_fragment` contains initial Z/A, excitation in MeV, stored spin and parity index, and pre-fragment momentum in MeV/c.

## Ordered transitions

`transitions` preserves the order in the original mixed CGMF history array. It is not reconstructed by sorting grouped neutron and photon output arrays.

Each transition contains:
- `emission_index`: zero-based mixed-history position;
- `particle_type`: `neutron`, `gamma`, or `internal_conversion`;
- `energy_cm_MeV`: transition energy stored in the CGMF history;
- `parent_state` and `daughter_state`: nuclide, excitation (MeV), stored spin index, parity, and discrete/continuum flag;
- `timestamp_valid`: whether a discrete-level cascade timestamp was assigned at this mixed-history position;
- `timestamp_s`: present only when `timestamp_valid=true).

Neutron transitions additionally contain `neutron_index` and `neutron_kinematics`: CM/Lab energy (MeV), CM/Lab direction cosines, and fragment recoil momentum before/after emission (MeV/c).

Gamma transitions additionally contain `gamma_index` and `gamma_kinematics`: CM/Lab energy (MeV) and CM/Lab direction cosines. The photon age/timestamp is represented by `timestamp_s` only when valid.

Internal-conversion transitions are represented in the mixed history with their transition energy and parent/daughter state. They do not have a photon direction/boost record in the current CGMF data model.

## Timestamp semantics

The timestamp array is indexed by the mixed transition index, not by gamma multiplicity. Its storage capacity therefore follows `MAX_CASCADE`. A parallel validity array distinguishes a sampled discrete-level time from an unassigned value. A numeric zero without validity must never be interpreted as a measured zero delay.

Continuum transitions without a sampled discrete-level timestamp remain `timestamp_valid=false`.

## Compatibility and limits

- The existing `cgmf.g2.neutron-transition.v1` schema is unchanged.
- The new output is disabled unless its environment variable is set.
- Mixed and legacy sidecars must agree on every neutron key and its state/kinematics/recoil fields.
- This sidecar exposes CGMF's simulated event history. It is not an experimental measurement and does not by itself establish a physical mechanism.
