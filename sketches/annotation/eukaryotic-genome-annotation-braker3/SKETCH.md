---
name: eukaryotic-genome-annotation-braker3
description: Use when you need to produce structural gene annotations (GFF3) for a
  soft-masked eukaryotic genome assembly using BRAKER3, combining RNA-seq BAM evidence
  and homologous protein sequences, with BUSCO/OMArk completeness QC and JBrowse visualization.
  Appropriate for fungi, plants, and animals where both RNA-seq and protein evidence
  are available.
domain: annotation
organism_class:
- eukaryote
input_data:
- soft-masked-genome-fasta
- rna-seq-bam
- protein-fasta
source:
  ecosystem: iwc
  workflow: Genome annotation with Braker3
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/genome_annotation/annotation-braker3
  version: '0.1'
  license: MIT
  slug: genome_annotation--annotation-braker3
tools:
- name: braker3
  version: 3.0.8+galaxy2
- name: augustus
- name: genemark-etp
- name: busco
  version: 5.8.0+galaxy1
- name: omark
  version: 0.3.1+galaxy1
- name: gffread
  version: 2.2.1.4+galaxy0
- name: jbrowse
  version: 1.16.11+galaxy1
tags:
- genome-annotation
- gene-prediction
- eukaryote
- braker3
- busco
- omark
- rna-seq-evidence
- protein-evidence
test_data:
- role: soft_masked_genome_sequence
  url: https://zenodo.org/records/14770765/files/genome.fasta
  filetype: fasta
- role: alignments_from_rna_seq
  url: https://zenodo.org/records/14770765/files/RNASeq.bam
  filetype: bam
- role: protein_sequences
  url: https://zenodo.org/records/14770765/files/protein_sequences.fasta
  filetype: fasta
expected_output:
- role: busco_summary_genome
  description: Content assertions for `BUSCO Summary (Genome)`.
  assertions:
  - 'has_n_lines: {''n'': 32}'
- role: busco_table_genome
  description: Content assertions for `BUSCO Table (Genome)`.
  assertions:
  - 'has_n_lines: {''n'': 2460}'
- role: busco_missing_genes_genome
  description: Content assertions for `BUSCO Missing Genes (Genome)`.
  assertions:
  - 'has_n_lines: {''n'': 1620}'
- role: busco_gff_genome
  description: Content assertions for `BUSCO GFF (Genome)`.
  assertions:
  - 'has_n_lines: {''n'': 5257}'
- role: braker3_annotation_gff
  description: Content assertions for `Braker3 Annotation GFF`.
  assertions:
  - 'has_text: scaffold_100'
- role: predicted_proteins
  description: Content assertions for `Predicted Proteins`.
  assertions:
  - 'has_n_lines: {''n'': 9474, ''delta'': 1000}'
- role: busco_missing_genes_predicted_proteins
  description: Content assertions for `BUSCO Missing Genes (Predicted Proteins)`.
  assertions:
  - 'has_n_lines: {''n'': 2248, ''delta'': 20}'
- role: busco_table_predicted_proteins
  description: Content assertions for `BUSCO Table (Predicted Proteins)`.
  assertions:
  - 'has_n_lines: {''n'': 2463, ''delta'': 20}'
- role: busco_summary_predicted_proteins
  description: Content assertions for `BUSCO Summary (Predicted Proteins)`.
  assertions:
  - 'has_n_lines: {''n'': 19}'
- role: busco_gff_predicted_proteins
  description: Content assertions for `BUSCO GFF (Predicted Proteins)`.
  assertions:
  - 'has_n_lines: {''n'': 1}'
- role: omark_detailed_summary
  description: Content assertions for `OMArk Detailed Summary`.
  assertions:
  - 'has_n_lines: {''n'': 63}'
  - 'has_text: Mucorineae'
---

# Eukaryotic genome annotation with BRAKER3

## When to use this sketch
- You have a soft-masked eukaryotic genome assembly (FASTA) and need structural gene models (CDS/exon/gene GFF3).
- You have both RNA-seq alignments (BAM, already mapped to this genome) and a protein FASTA of homologous proteins to use as extrinsic evidence.
- You want BRAKER3's combined GeneMark-ETP + AUGUSTUS prediction mode (RNA-seq + protein evidence together), not one evidence type alone.
- You also want integrated QC of the predicted gene set via BUSCO (genome and proteome mode) and OMArk, plus an interactive JBrowse view.
- Suitable for fungi (toggle `--fungus`), plants, and animals.

## Do not use when
- The genome has not been repeat-masked — run a masking workflow (e.g. RepeatModeler/RepeatMasker) first; BRAKER3 expects soft-masked input.
- You only have RNA-seq OR only protein evidence — BRAKER3 can still run in single-evidence mode, but pick a dedicated BRAKER2/BRAKER1 sketch if one exists.
- You are annotating a prokaryote — use a bacterial annotation sketch (e.g. Prokka/Bakta) instead.
- You are annotating a viral genome — use a viral annotation sketch.
- You need functional annotation (GO terms, InterPro, KEGG) — this sketch only produces structural models; chain a functional annotation sketch afterwards.
- You only need to assess assembly quality without predicting genes — use a standalone BUSCO/assembly-QC sketch.

## Analysis outline
1. Provide a soft-masked genome FASTA, an RNA-seq BAM aligned to that genome, and a homologous protein FASTA as inputs.
2. Run BUSCO on the raw genome (`mode=geno`, miniprot) against a chosen lineage to benchmark assembly completeness.
3. Run BRAKER3 with genome + BAM + protein evidence to predict gene models, emitting GFF3.
4. Extract predicted protein sequences from the GFF3 with gffread (`-y pep.fa`).
5. Run BUSCO on the predicted proteome (`mode=prot`) against the same lineage to benchmark annotation completeness.
6. Run OMArk on the predicted proteome against the LUCA OMAmer database for an orthology-based completeness/contamination check.
7. Build a JBrowse instance displaying the genome with the BRAKER3 annotation track for interactive review.

## Key parameters
- BRAKER3 `softmasking: true` — required; input genome must be soft-masked.
- BRAKER3 `evidences.bam` + `evidences.prot_seq` — both wired in for combined ETP mode.
- BRAKER3 `genemark.fungus` — set true for fungal genomes (passes `--fungus`), false otherwise.
- BRAKER3 `output_format: gff3`, `augustus.rounds: 5`, `alternatives_from_evidence: true`.
- BUSCO `lineage_dataset` — pick the closest clade (e.g. `mucorales_odb10` for Mucoromycota fungi, `eudicots_odb10`, `vertebrata_odb10`, etc.) and reuse it for both genome and proteome BUSCO runs.
- BUSCO `busco_mode: geno` for the assembly QC step and `busco_mode: prot` for the predicted proteome QC step; `cached_db` version `v5`.
- gffread `fa_outputs: -y pep.fa` to emit translated predicted proteins.
- OMArk `database: LUCA-v2.0.0.h5`.
- Workflow-level toggle `Include BUSCO` gates both BUSCO steps via a `when` expression.

## Test data
The reference test uses a small fungal (Mucorales) dataset hosted on Zenodo record 14770765: a soft-masked genome FASTA (`genome.fasta`), an RNA-seq alignment BAM (`RNASeq.bam`), and a homologous protein FASTA (`protein_sequences.fasta`). It is run with `BUSCO lineage = mucorales_odb10`, `BUSCO database = v5`, `Fungus genome = false`, and `Include BUSCO = true`. Expected outputs include a BRAKER3 GFF3 containing `AUGUSTUS`-sourced features on `scaffold_100`, a predicted-protein FASTA of roughly 9,474 lines (±1000), BUSCO summary/table/missing/GFF artifacts for both the genome and the predicted proteome with fixed or near-fixed line counts, and an OMArk detailed summary of 63 lines that mentions `Mucorineae`.

## Reference workflow
Galaxy IWC — `workflows/genome_annotation/annotation-braker3` (Genome annotation with Braker3), release 0.1 (2025-12-05). Uses BRAKER3 `3.0.8+galaxy2`, BUSCO `5.8.0+galaxy1`, OMArk `0.3.1+galaxy1`, gffread `2.2.1.4+galaxy0`, and JBrowse `1.16.11+galaxy1`.
