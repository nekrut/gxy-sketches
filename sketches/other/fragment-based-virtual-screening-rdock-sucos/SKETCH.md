---
name: fragment-based-virtual-screening-rdock-sucos
description: 'Use when you need to perform fragment-based virtual screening: docking
  a library of candidate small-molecule compounds (provided as SMILES) against a protein
  receptor (PDB) using rDock, where the binding cavity is defined from a set of known
  crystallographic fragments, and docked poses are rescored and filtered by 3D feature
  overlap (SuCOS) against a reference fragment. Typical use case: SARS-CoV-2 Mpro
  or similar targets from XChem fragment screens.'
domain: other
organism_class:
- other
input_data:
- protein-receptor-pdb
- fragments-sdf
- candidate-compounds-smiles
- reference-fragment-sdf
source:
  ecosystem: iwc
  workflow: Fragment-based virtual screening using rDock for docking and SuCOS for
    pose scoring
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/computational-chemistry/fragment-based-docking-scoring
  version: 0.1.5
  license: MIT
tools:
- rDock
- rbcavity
- rbdock
- SuCOS
- OpenBabel
- RDKit
- Frankenstein-ligand
tags:
- virtual-screening
- docking
- fragment-based
- drug-discovery
- cheminformatics
- pose-scoring
- rdock
- sucos
- computational-chemistry
test_data: []
expected_output:
- role: scored_and_filtered_poses
  description: Content assertions for `Scored and filtered poses`.
  assertions:
  - 'has_text: SuCOS_Score'
---

# Fragment-based virtual screening with rDock and SuCOS pose scoring

## When to use this sketch
- You have a protein receptor structure (PDB) and want to dock a library of candidate compounds into it.
- You already have a set of crystallographic fragment hits (SDF) bound in the target pocket, and you want to use them to (a) define the binding cavity via the 'Frankenstein ligand' technique and (b) rescore docked poses by 3D feature overlap against a chosen reference fragment.
- Candidate compounds are supplied as SMILES and need charge enumeration, 3D embedding, and docking.
- You want to filter docked poses by a SuCOS similarity threshold to the reference fragment, prioritising poses that recapitulate known fragment interactions.
- Typical setting: follow-up compound design against an XChem-style fragment screen (e.g. SARS-CoV-2 main protease).

## Do not use when
- You only need classical blind docking with no fragment-derived cavity or pose constraint — use a plain rDock/AutoDock Vina sketch instead.
- You want free-energy / MM-PBSA / alchemical binding affinity estimation — use a molecular-dynamics-based sketch.
- You want protein–protein or peptide docking — this sketch is for small-molecule docking only.
- You want ligand-based virtual screening (2D similarity, pharmacophore search) without a receptor — use a cheminformatics similarity sketch.
- Your input is already 3D-prepared and docked and you only need ML-based rescoring.

## Analysis outline
1. Convert receptor PDB to MOL2 at pH 7.4 with OpenBabel (`openbabel_compound_convert`).
2. Build a 'Frankenstein ligand' SDF from the supplied fragment set using `ctb_frankenstein_ligand` — a union molecule covering all fragment positions, used only to seed the cavity.
3. Define the rDock active site / cavity from the receptor MOL2 and Frankenstein ligand with `rxdock_rbcavity`.
4. Enumerate protonation/charge states of the candidate SMILES library with `enumerate_charges`.
5. Convert the enumerated SMILES to 3D SDF (OpenBabel, gen3d, pH 7.4).
6. Split the 3D SDF into a Galaxy collection of N-sized chunks with `split_file_to_collection` for parallel docking.
7. Dock each chunk into the cavity with `rxdock_rbdock`, generating a configurable number of poses per ligand.
8. Collapse the per-chunk docked-pose collections back into a single SDF (`collapse_collections`).
9. Score every docked pose against the chosen reference fragment with `sucos_docking_scoring`, adding a `SuCOS_Score` SDF tag per pose.
10. Sort poses descending by `SuCOS_Score` and filter with `rdock_sort_filter` using the expression `$SuCOS_Score >= <threshold>` (threshold composed via `compose_text_param`).

## Key parameters
- Number of poses: integer, number of docking poses generated per input compound by rDock (test uses 1; production typically 5–25).
- Collection size for docking: integer, number of ligands per parallel docking sub-job; controls parallelism granularity.
- SuCOS threshold: float in [0, 1]; poses with `SuCOS_Score` below this are discarded. 0 keeps everything; typical productive values are 0.4–0.6.
- rDock cavity (`rbcavity`): gridstep 0.5 Å, min_volume 100 Å³, radius 3.0 Å, sphere 1.0, vol_incr 0.0, weight 1.0.
- rDock docking (`rbdock`): seed 1, flex 3.0 on receptor OH/NH, no score filter (`no_filter`) — SuCOS, not rDock score, is the primary ranking criterion.
- OpenBabel protonation: pH 7.4 for both receptor and ligands.
- Charge enumeration pH window: min_ph 4.4, max_ph 10.4.
- Sort field: `SuCOS_Score`, descending, global sort across all poses.

## Test data
The bundled test profile uses a small SARS-CoV-2 main protease example shipped inside the workflow repo: `receptor.pdb` (Mpro structure), `all-fragments.sdf` (the set of crystallographic fragments used to build the Frankenstein ligand and define the cavity), `single-fragment.sdf` (one reference fragment used for SuCOS scoring), and `candidates.smi` (a very small SMILES library). Test parameters are Number of poses = 1, Collection size for docking = 2, SuCOS threshold = 0 (i.e. keep everything). The expected `Scored and filtered poses` output is an SDF where every record carries a `SuCOS_Score` property tag, confirming that docking, SuCOS rescoring, and the sort/filter step all ran end-to-end.

## Reference workflow
Galaxy IWC workflow `fragment-based-docking-scoring` v0.1.5 — `workflows/computational-chemistry/fragment-based-docking-scoring/fragment-based-docking-scoring.ga` in https://github.com/galaxyproject/iwc. Technique reference: Informatics Matters blog, 'Cavities and Frankenstein molecules' (2018-11-23).
