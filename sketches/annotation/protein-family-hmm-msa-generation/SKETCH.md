---
name: protein-family-hmm-msa-generation
description: Use when you need to generate protein family Hidden Markov Models (HMMs)
  and multiple sequence alignments (MSAs) from a FASTA file of amino acid sequences,
  or to update existing family HMMs/MSAs with new sequences. Typical for building
  Pfam-like family resources from metagenomic or reference proteomes.
domain: annotation
organism_class:
- eukaryote
- bacterial
- viral
- metagenome
input_data:
- protein-fasta
- existing-hmm-tarball-optional
- existing-msa-tarball-optional
source:
  ecosystem: nf-core
  workflow: nf-core/proteinfamilies
  url: https://github.com/nf-core/proteinfamilies
  version: 2.2.0
  license: MIT
  slug: proteinfamilies
tools:
- name: seqfu
  version: 2.9.0
- name: seqkit
  version: 2.9.0
- name: mmseqs2
- name: famsa
- name: mafft
- name: clipkit
  version: 2.4.1
- name: hmmer
- name: hh-suite3
- name: cmaple
  version: 1.1.0
- name: multiqc
tags:
- protein-families
- hmm
- msa
- clustering
- homology
- pfam
- hmmer
- mmseqs2
test_data: []
expected_output: []
---

# Protein family HMM & MSA generation

## When to use this sketch
- You have a (potentially very large) amino acid FASTA and want to discover protein families by clustering, then build a per-family HMM plus full MSA suitable for downstream homology search (Pfam-style output).
- You want to *update* an existing set of family HMMs/MSAs by feeding in new sequences: hits extend existing families, non-hits seed new ones.
- You plan to feed family representatives into `nf-core/proteinfold` for structure prediction or `nf-core/proteinannotator` for functional annotation.
- Inputs are diverse metagenomic/remote-homolog proteins where the default MMseqs2 identity of 0.9 would oversplit families; lower identity thresholds (~0.3) are appropriate.

## Do not use when
- You only need to *search* sequences against an existing HMM database (Pfam, TIGRFAM) — use hmmer/hmmsearch directly or `nf-core/proteinannotator` / `interproscan`.
- You want predicted 3D structures — use `nf-core/proteinfold`.
- Your input is nucleotide reads/contigs requiring gene calling first — run `nf-core/funcscan` or prodigal/pyrodigal upstream and feed the predicted proteins here.
- You want a phylogenetic tree of orthologs from precomputed gene families — use a dedicated phylogenomics pipeline (`nf-core/phyloplace`), not this one's optional CMAPLE step.
- You want single protein domain architecture annotation — again, annotator pipelines are more appropriate.

## Analysis outline
1. QC input amino-acid FASTAs with SeqFu (stats) and preprocess with SeqKit (gap removal, upcase, length filter, dedup, validation).
2. Cluster sequences with MMseqs2 (`cluster` for sensitivity or `linclust` for speed) at low identity to group remote homologs.
3. Filter clusters by `cluster_size_threshold` and split into per-cluster FASTA chunks.
4. Build seed MSAs for each cluster with FAMSA (default) or MAFFT.
5. Optionally trim gappy MSA columns with ClipKIT (`trim_ends_only` by default).
6. Build family HMMs with `hmmer hmmbuild`, then recruit additional sequences from the input FASTA via `hmmer hmmsearch` filtered by env-vs-query length, and compute full MSAs with `hmmer hmmalign`.
7. Optionally remove between-family redundancy (hmmsearch of family reps against all HMMs) and merge similar families.
8. Optionally remove in-family redundancy by strictly clustering members with MMseqs2 (identity/coverage 0.9) and re-aligning.
9. Reformat `.sto` full MSAs to `.fas` with HH-suite3 when sequence-level dedup is skipped.
10. Optionally infer per-family phylogenies with CMAPLE.
11. Extract family representatives, emit metadata CSV, aggregate with MultiQC, and optionally write downstream samplesheets for `nf-core/proteinfold` / `nf-core/proteinannotator`.

### Update mode (when samplesheet provides `existing_hmms_to_update` + `existing_msas_to_update`)
1. Untar existing HMM and MSA archives (filenames must match one-to-one by base).
2. Concatenate existing HMMs and run `hmmsearch` with the new input FASTA.
3. For hits, extract family sequences with SeqKit, concatenate with new hit sequences, optionally redundancy-filter with MMseqs2, re-align with FAMSA/MAFFT, optionally trim with ClipKIT, and rebuild HMMs with `hmmbuild`.
4. For non-hit sequences, fall through to the normal create-families path above.

## Key parameters
- `input`: CSV samplesheet with columns `sample,fasta,existing_hmms_to_update,existing_msas_to_update` (last two optional, `.tar.gz`).
- `clustering_tool`: `cluster` (sensitive, default) or `linclust` (scales to very large datasets).
- `cluster_seq_identity`: default `0.3` — low on purpose to capture remote homologs; raise for closer-homolog families.
- `cluster_coverage`: default `0.5`; `cluster_cov_mode`: default `0` (bidirectional).
- `cluster_size_threshold`: default `25` — minimum members to seed a family.
- `min_seq_length` / `max_seq_length`: default `30` / `5000` AA.
- `alignment_tool`: `famsa` (recommended) or `mafft`.
- `skip_msa_trimming` (default false), `trim_ends_only` (default true), `gap_threshold` (default `0.5`), `clipkit_out_format` (must differ from aligner output extension).
- `hmmsearch_evalue_cutoff`: default `0.001`; `hmmsearch_query_length_threshold`: default `0.9` (strict to avoid fragment recruitment).
- Redundancy: `skip_family_redundancy_removal`, `skip_family_merging`, `hmmsearch_family_redundancy_length_threshold` (1.0), `hmmsearch_family_similarity_length_threshold` (0.9, must be < redundancy threshold).
- In-family dedup: `skip_sequence_redundancy_removal`, `cluster_seq_identity_for_redundancy` / `cluster_coverage_for_redundancy` both default `0.9`.
- `skip_phylogenetic_inference` (default true), `skip_proteinfold_samplesheet` / `skip_proteinannotator_samplesheet` (default true).

## Test data
The `test` profile uses a single-sample CSV (`samplesheets/samplesheet.csv`) pointing at a small MGnifams amino-acid FASTA hosted under the pipeline's test-datasets repository, with `linclust` clustering at identity 0.5, coverage 0.9, and `cluster_size_threshold = 5` so that a handful of tiny families are produced quickly. The `test_full` profile uses `samplesheets/samplesheet_full.csv` with two samples, exercising both create and update modes simultaneously (one sample supplies existing HMM/MSA tarballs) and enabling phylogenetic inference plus downstream samplesheet generation. Expected outputs include per-sample family HMM files under `hmm/raw` and `hmm/filtered`, seed and full MSAs under `seed_msa/` and `full_msa/`, a `family_reps/<sample>/<sample>_reps.faa` FASTA of representative sequences, a `<sample>_meta_mqc.csv` metadata table (Sample, Family Id, Size, Representative Length, Representative Id, Sequence), a MultiQC HTML report, and — for `test_full` — CMAPLE treefiles plus `proteinfold/samplesheet.csv` and `proteinannotator/samplesheet.csv`.

## Reference workflow
nf-core/proteinfamilies v2.2.0 — https://github.com/nf-core/proteinfamilies (Karatzas et al., bioRxiv 2025, doi:10.1101/2025.08.12.670010).
