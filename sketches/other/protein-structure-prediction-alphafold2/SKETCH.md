---
name: protein-structure-prediction-alphafold2
description: Use when you need to predict 3D structures of protein monomers (or multimers)
  from amino acid FASTA sequences using AlphaFold2 with MSA-based homology search
  against reference databases (UniRef, BFD, MGnify, PDB). Produces ranked PDB models
  plus pLDDT/PAE confidence metrics.
domain: other
organism_class:
- eukaryote
- bacterial
- viral
input_data:
- protein-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/proteinfold
  url: https://github.com/nf-core/proteinfold
  version: 2.0.0
  license: MIT
tools:
- alphafold2
- hhblits
- jackhmmer
- hhsearch
- multiqc
tags:
- protein
- structure-prediction
- alphafold
- msa
- 3d-structure
- pdb
- plddt
test_data: []
expected_output: []
---

# Protein 3D structure prediction with AlphaFold2

## When to use this sketch
- You have one or more protein amino acid sequences in FASTA format and want predicted 3D structures as PDB files.
- You want MSA-based prediction (AlphaFold2) against standard reference databases (UniRef30, UniRef90, BFD/small BFD, MGnify, PDB70, PDB mmCIF) for maximum accuracy.
- You need per-residue confidence (pLDDT), Predicted Aligned Error (PAE) matrices, and optionally pTM/ipTM scores for monomers or multimers.
- You want to batch-fold many sequences (e.g. an entire proteome) with `--split_fasta` to parallelise per-sequence inference.
- GPU acceleration is available, or you are willing to run on CPU for small inputs.

## Do not use when
- You need structures that include nucleic acids, small-molecule ligands, PTMs, or covalent modifications — use an all-atom sketch built around `alphafold3`, `boltz`, `helixfold3`, or `rosettafold-all-atom` instead.
- You need protein–RNA/DNA complex modelling without ligands — use a `rosettafold2na` sketch.
- You must avoid the heavy MSA database download (hundreds of GB) and want language-model-only inference — use an `esmfold` sketch (no MSA required).
- You want a cloud MMseqs2 MSA server instead of local HHblits/Jackhmmer — use a `colabfold` sketch (`--use_msa_server`).
- You only want structural similarity search of existing PDBs — that is a Foldseek-only task, not a folding task.

## Analysis outline
1. Build a samplesheet CSV with `id,fasta` columns; optionally enable `--split_fasta` to explode multi-entry FASTAs into one sequence per job.
2. Stage reference databases under `--alphafold2_db` (BFD or small_bfd, UniRef30, UniRef90, MGnify, PDB70, PDB mmCIF + obsolete, params). The pipeline will download them if `--db` is omitted.
3. Run MSA search: Jackhmmer vs UniRef90/MGnify, HHblits vs UniRef30 + BFD, HHsearch vs PDB70 templates. In `split_msa_prediction` mode this runs as a separate upstream step so the MSA can be reused.
4. Run AlphaFold2 inference with the chosen `alphafold2_model_preset` (`monomer`, `monomer_ptm`, `monomer_casp14`, or `multimer`) and selected params release.
5. Rank and publish top models as `alphafold2/top_ranked_structures/<id>.pdb` plus per-sequence `*_plddt.tsv`, `*_pae.tsv`, and `*_ptm.tsv` / `*_iptm.tsv` where applicable.
6. Generate per-sequence HTML reports under `reports/`, optional cross-mode comparison under `compare/`, and a MultiQC summary.
7. Optionally run Foldseek `easy-search` (`--skip_foldseek false`) on the top-ranked PDB against a structural database such as `pdb100` for homolog discovery.

## Key parameters
- `--mode alphafold2` — select the AlphaFold2 workflow (can be combined comma-separated with other modes).
- `--alphafold2_mode` — `standard` (MSA + inference in one job) or `split_msa_prediction` (default; MSA as a separate step, better for reuse/parallelism).
- `--alphafold2_model_preset` — `monomer_ptm` (default, gives pTM + PAE), `monomer`, `monomer_casp14`, or `multimer` for complexes.
- `--alphafold2_params_prefix` — params release, default `alphafold_params_2022-12-06`.
- `--alphafold2_max_template_date` — cutoff date for PDB templates (default `2038-01-19`, i.e. effectively unrestricted).
- `--full_dbs` / `--alphafold2_full_dbs` — toggle full BFD vs reduced `small_bfd` (trade accuracy for disk/runtime).
- `--uniref30_prefix` — one of `UniRef30_2023_02` (default), `UniRef30_2022_02`, `UniRef30_2021_03`.
- `--alphafold2_random_seed` — fix seed for reproducible inference.
- `--use_gpu true` — enable GPU inference (strongly recommended for anything beyond toy sequences).
- `--split_fasta true` — split multi-sequence FASTAs into per-sequence jobs for parallel folding.
- `--alphafold2_db <DIR>` — path to pre-staged reference data (expected subdirs: `bfd/`, `small_bfd/`, `uniref30/`, `uniref90/`, `mgnify/`, `pdb70/`, `pdb_mmcif/`, `params/`).
- `--save_intermediates true` — keep raw per-model pickles and MSA files under `alphafold2/.../raw/`.
- Foldseek add-on: `--skip_foldseek false --foldseek_db pdb100 --foldseek_db_path <DIR>`.

## Test data
The `test` profile uses a tiny samplesheet from `nf-core/test-datasets` (`proteinfold/testdata/samplesheet/v2.0/samplesheet.csv`) containing CASP-style target sequences (e.g. `T1024`, `T1026`) as remote FASTA URLs, paired with a stub `assets/dummy_db_dir` so that database staging is mocked (`stubRun = true`, `RUN_ALPHAFOLD2` swapped for a lightweight `biocontainers/gawk` container). The `test_full` profile uses the same samplesheet but points `--alphafold2_db` at `s3://proteinfold-dataset/test-data/mini_dbs` and enables `--use_gpu true`. Running either profile is expected to produce `alphafold2/top_ranked_structures/<id>.pdb`, per-sequence `*_plddt.tsv` / `*_pae.tsv` (and `*_ptm.tsv` under `monomer_ptm`), per-sequence HTML reports under `reports/`, and a MultiQC report under `multiqc/`.

## Reference workflow
nf-core/proteinfold v2.0.0 — https://github.com/nf-core/proteinfold (AlphaFold2 mode; DOI 10.5281/zenodo.13135393).
