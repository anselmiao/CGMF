# ¹³²I ENSDF adopted decay-scheme audit

**Date:** 2026-11-21  
**Scope:** Source audit of the ¹³²I 1.387 h isomer and the proposed 22-keV intermediate state for targeted discrete-level candidate B.  
**Source:** NNDC ENSDF, *Adopted Levels, Gammas*, evaluated February 2005; NDS 104, 497 (2005), literature cutoff 10-Feb-2005. This report does not authorize production-data changes.

## 1. Primary evaluated record

The adopted ENSDF page identifies:
- ground state: 0.0 keV, (4^+), (T_{1/2}=2.295) h;
- intermediate level: (22(11)) keV, ((5^+)), no adopted half-life;
- isomer: (120(20)) keV, ((8^-)), (T_{1/2}=1.387(15)) h.

The 22-keV level's spin/parity is inferred from the E3 transition from the ((8^-)) isomer and systematics. The 120-keV isomer's ((8^-)) assignment is also based on systematics of neighboring nuclei. Both assignments are parenthesized in the adopted table and must not be upgraded to unique, firmly measured Jπ in the candidate manifest.

## 2. Isomer decay competition

ENSDF adopts:
- beta-minus branch: (14(2)\%);
- isomeric-transition branch: (86(2)\%).

The cited evaluation attributes the branch determination to 1974Di03, *Identification and Decay Characteristics of ¹³²mI*, Phys. Rev. C 10, 1172 (1974). The adopted level XREF for the 120-keV state is B = ¹³²I IT decay (1.387 h), not a direct ²⁵²Cf spontaneous-fission population record.

Consequently, the 86% IT fraction is a total isomeric-transition decay fraction. It is not the emitted 98-keV photon fraction, and it is not a prompt fission gamma yield.

## 3. 120-keV to 22-keV transition

The adopted gamma table gives:
- (E_\gamma=98.0(10)) keV;
- relative photon intensity (I_\gamma=100) (normalized within the transition data);
- multipolarity E3;
- total theoretical internal-conversion coefficient (\alpha=21.6);
- partial coefficients: K=6.97, L=11.5, M=2.54, N+...=0.598.

Thus the transition must be represented with separate photon and conversion channels. It is incorrect to treat relative photon intensity 100 as 100% of all isomer decays.

For a single E3 transition with the adopted total conversion coefficient, the conditional fractions within that transition are:
- gamma photon: (1/(1+\alpha)=1/22.6\approx4.425\%);
- internal conversion: (\alpha/(1+\alpha)=21.6/22.6\approx95.575\%).

Combining these with the adopted 86% IT branch gives approximate total-isomer decay fractions:
- beta-minus: 14%;
- 98-keV gamma photon: (0.86/22.6\approx3.81\%);
- conversion electrons: (0.86\times21.6/22.6\approx82.19\%).

These derived percentages are conditional arithmetic using the adopted central values; uncertainties and any unlisted weak channels are not propagated here.

## 4. The 22-keV level to ground-state entry: uncertainty retained

The adopted gamma table's row for the tentative 22? (5+) level prints a parenthesized (Eγ=(22 11)) keV entry to the 4+ ground state. It does **not** provide a relative photon intensity or multipolarity for this entry. The level-scheme graphic marks the decay with a dashed arrow, and its legend identifies dashed arrows as uncertain gamma decay.

The correct transcription is therefore:
- retain Eγ=(22 11) keV as an uncertain adopted-table observation;
- do not transcribe 29.11 keV (that value is not present in this adopted table row);
- do not assign a multipolarity or a relative photon intensity;
- do not convert this uncertain entry into an admitted CGMF prompt gamma branch.

This correction changes the source record's energy/uncertainty fields, but not the admission decision: the 22-keV level remains catalog-only and the putative ground-state branch remains uncertain.

## 5. Prompt versus delayed classification

The 120-keV state has a 1.387-hour half-life. Its 98-keV E3 transition is an isomeric-transition decay, not a prompt fragment de-excitation on the CGMF prompt-cascade timescale. The ENSDF adopted record's XREF B is the IT decay dataset. The adopted page's note on ²⁵²Cf spontaneous fission reports only one prompt gamma at 228.5 keV, most likely from the 279-keV level; it does not establish prompt population of this 120-keV isomer.

Thus the 120-keV isomer and its delayed E3 decay remain `CATALOG_ONLY` for the prompt CGMF discrete-level scheme. This is a data-admission decision, not a claim that the isomer cannot be populated in any other experiment or decay context.

## 6. Consequences for B0 schema

The current generic field `gamma_branches[].probability` is semantically insufficient if it is interpreted as an unconditional decay probability. The data model must distinguish at least:
1. total decay-mode fractions (beta, IT, alpha, etc.);
2. transition probability conditional on a decay mode;
3. relative photon intensity within a gamma dataset;
4. internal-conversion coefficient and derived conversion-electron fraction;
5. transition energy and uncertainty;
6. multipolarity/mixing-ratio evidence and assignment confidence;
7. prompt/delayed classification and source dataset identity.

The candidate manifest now stores the ¹³²I decay-mode fractions and the 98-keV E3 photon/ICC record separately. The parenthesized (22 11)-keV ground-state entry is retained as an uncertain observed-transition record, not as an accepted gamma branch.

## 7. Status ledger

| Claim | Status |
|---|---|
| ENSDF adopted energies, half-life and decay-mode percentages transcribed | `SOURCE_VERIFIED` |
| 98.0(10)-keV E3 assignment and ICC transcribed | `SOURCE_VERIFIED` |
| 29.11-keV line lacks multipolarity in adopted gamma table | `SOURCE_VERIFIED` |
| 22-keV level Jπ uniquely established | `BLOCKED` |
| 22-keV-to-ground gamma branch established for CGMF | `BLOCKED` |
| 120-keV isomer admitted to prompt CGMF scheme | `REJECTED_FOR_PROMPT_SCOPE` |
| 120-keV isomer retained in source catalog | `CATALOG_ONLY` |
| Production `data/discreteLevels.dat` changed | `NO` |
| A/B physical comparison | `NOT_STARTED` |

## References

- NNDC ENSDF, ¹³²I Adopted Levels, Gammas: https://www.nndc.bnl.gov/ensdf/getadopted.jsp?nuc=132I
- NNDC ENSDF A=132 dataset index (lists ¹³²I IT DECAY (1.387 H), revised 2005-04): https://www.nndc.bnl.gov/ensdf/DatasetFetchServlet?datasource=ensdf&mass=132&nucmass=isMass&searchType=ensdfIndex
- 1974Di03, M. Diksic, L. Yaffe, D. G. Sarantites, “Identification and Decay Characteristics of ¹³²mI,” Phys. Rev. C 10, 1172 (1974), DOI: https://doi.org/10.1103/PhysRevC.10.1172
