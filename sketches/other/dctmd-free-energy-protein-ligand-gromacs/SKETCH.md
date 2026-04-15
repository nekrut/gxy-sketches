---
name: dctmd-free-energy-protein-ligand-gromacs
description: Use when you need to compute free energy and friction profiles for a
  protein-ligand dissociation pathway using dissipation-corrected targeted molecular
  dynamics (dcTMD) with GROMACS. Takes an apoprotein PDB and a ligand SDF, parameterises
  the complex, runs an ensemble of nonequilibrium constant-velocity pulling simulations,
  and applies the Wolf/Stock friction correction.
domain: other
organism_class:
- protein-ligand-complex
input_data:
- protein-pdb
- ligand-sdf
source:
  ecosystem: iwc
  workflow: dcTMD calculations with GROMACS
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/computational-chemistry/gromacs-dctmd
  version: 0.1.7
  license: MIT
  slug: computational-chemistry--gromacs-dctmd
tools:
- name: gromacs
- name: gmx_setup
- name: gmx_solvate
  version: 2022+galaxy0
- name: gmx_em
  version: 2022+galaxy0
- name: gmx_sim
  version: 2022+galaxy0
- name: gmx_makendx
  version: 2022+galaxy0
- name: ambertools-antechamber
- name: acpype
- name: rdkit
- name: openbabel
- name: biomd-neqgamma
  version: 0.1.5.2+galaxy1
tags: []
test_data: []
expected_output: []
---

# dcTMD free energy calculation for protein-ligand dissociation (GROMACS)

## When to use this sketch
- You have a protein (PDB, apo) and a small-molecule ligand (SDF) and want a free energy / PMF profile along a ligand unbinding pathway.
- You want the Wolf & Stock dissipation-corrected targeted MD (dcTMD) approach: an ensemble of constant-velocity pulling trajectories plus nonequilibrium friction correction, rather than umbrella sampling or metadynamics.
- You need both the free energy profile and the friction coefficient γ(x) along the pulling coordinate.
- You can supply atom indices defining the protein pull group and a PBC reference atom, and a pulling rate / number of steps appropriate for your system.
- Your force field of choice is a standard GROMACS-supported protein force field (AMBER, OPLS, CHARMM27, GROMOS) with GAFF for the ligand.

## Do not use when
- You want equilibrium free energy methods (umbrella sampling, metadynamics, thermodynamic integration, FEP) — use a dedicated absolute/relative binding free energy workflow instead.
- You only need a plain classical MD trajectory of a protein-ligand complex without a pulling coordinate — use a standard GROMACS protein-ligand MD workflow.
- Your ligand is a peptide, nucleic acid, or covalently bound moiety — GAFF + antechamber parameterisation here assumes a drug-like small molecule.
- You need automated pathway separation / clustering of dcTMD trajectories; this workflow explicitly leaves pathway separation to the user.
- You want coarse-grained or implicit-solvent free energy calculations.

## Analysis outline
1. Ligand preparation: compute formal charge with RDKit Descriptors, optionally protonate at a target pH and convert SDF to PDB with OpenBabel.
2. Ligand parameterisation: assign GAFF atom types and BCC charges with AmberTools AnteChamber, then build a GROMACS-compatible ITP/GRO with ACPYPE.
3. Protein parameterisation: run `gmx pdb2gmx` (GROMACS initial setup) with the chosen protein force field and water model to produce protein TOP/GRO and position restraints ITP.
4. Merge protein and ligand topologies into a single complex TOP/GRO (gmx_merge_topology_files).
5. Solvate the complex and add NaCl to the requested concentration, neutralising the system (gmx_solvate).
6. Energy minimisation with steepest descent, Verlet cut-off scheme, PME electrostatics (gmx_em).
7. Build an index group for the ligand heavy atoms via `gmx make_ndx` (selection `13 & ! a H*`), renamed to `pullgrp`, and append the protein pull-group atom indices as a second index group.
8. NVT equilibration: short MD run (gmx_sim) at the requested temperature using the protein position restraints.
9. Assemble the TMD MDP: start from the packaged `tmd.mdp`, inject `pull_coord1_rate`, `dt`, `nsteps`, and `pull-group1-pbcatom` lines via the compose-text-parameter / add-line-to-file helpers.
10. Production TMD ensemble: run `gmx mdrun` (gmx_sim, custom MDP, GPU) N times using the merged NDX, the equilibrated GRO and the complex TOP — each replicate is one constant-velocity pulling trajectory producing an XVG of pull force vs. time.
11. dcTMD friction correction: feed the collection of pull XVG files to `biomd_neqgamma` to compute the free energy profile ΔG(x) and the friction profile γ(x).

## Key parameters
- `Force field`: one of oplsaa, amber03, amber94, amber96, amber99, amber99sb, amberGS, charmm27, gromos43a1/43a2/45a3/53a5/53a6/54a7. Ligand is always GAFF.
- `Water model`: tip3p | tip4p | tips3p | tip5p | spc | spce | none — must be compatible with the chosen force field.
- `Salt concentration`: NaCl molarity for `gmx solvate -neutral` (mol/dm³).
- `Temperature`: NVT reference temperature in K (string, e.g. "300").
- `Number of equilibration steps`: NVT equilibration `nsteps` before TMD.
- `Step length (ps)`: integration `dt` for TMD (typically 0.001–0.002 ps with h-bonds constrained).
- `Number of steps`: `nsteps` for each TMD production run; together with `dt` and pulling rate this defines the total pulled distance.
- `Pulling rate`: `pull_coord1_rate` in nm/ps — dcTMD is nonequilibrium, so this is deliberately fast (e.g. 0.001 nm/ps in the test).
- `Number of simulations`: size of the TMD ensemble; dcTMD statistics and friction correction quality depend on this.
- `Protein pull group`: space-separated atom indices defining the fixed/reference group on the protein (typically binding-pocket Cα atoms).
- `Pull group pbcatom`: `pull-group1-pbcatom` reference atom index for PBC handling inside the protein pull group.
- `pH to protonate ligand`: OpenBabel protonation pH; set to -1.0 to skip.
- Fixed internals: EM uses steepest descent, emtol 1000 kJ/mol/nm, 50000 steps max, Verlet/PME, rcoulomb=rlist=rvdw=1.0 nm; production MD uses NVT, h-bonds constraints, write_freq=1000; friction correction uses T=300 K, vel=0.001, av=1, sigma=1 by default (edit for non-default temperature/velocity).
- The TMD MDP template is fetched at runtime from `workflows/computational-chemistry/gromacs-dctmd/tmd.mdp` in the iwc repo — parameters above are appended as footer lines, so anything not exposed as an input comes from that file.

## Test data
The packaged test runs the full pipeline against SARS-CoV-2 main protease (`test-data/mpro.pdb`) with a small-molecule inhibitor (`test-data/lig.sdf`), using amber99sb + TIP3P water, 0.1 M NaCl, 300 K, 50 equilibration steps, and an ensemble of 2 TMD replicates of 100 steps each at dt=0.001 ps and a 0.001 nm/ps pulling rate. The protein pull group is a list of 22 binding-pocket Cα indices with atom 606 as the PBC reference. Expected outputs include one XTC trajectory per replicate (first replicate ~138900 bytes ±500) and dcTMD results: a free energy profile file and a friction profile file, each with 101 lines and 5 columns. Note that these tiny step counts only exercise the plumbing — scientifically meaningful dcTMD runs require far longer TMD trajectories and a much larger ensemble.

## Reference workflow
iwc `workflows/computational-chemistry/gromacs-dctmd` v0.1.7 (Galaxy workflow `dcTMD calculations with GROMACS`, author Simon Bray). Method references: Wolf & Stock, J. Chem. Theory Comput. 2018 (doi:10.1021/acs.jctc.8b00835); Wolf, Lickert, Bray & Stock, Nat. Commun. 2020 (doi:10.1038/s41467-020-16655-1). Free energy / friction correction implemented by the `biomd_neqgamma` Galaxy tool.
