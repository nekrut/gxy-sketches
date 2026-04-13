---
name: ab-initio-eukaryotic-genome-annotation-helixer
description: Use when you need to produce a structural gene annotation (GFF3) for
  a eukaryotic genome assembly (fungi, land plant, invertebrate, or vertebrate) without
  RNA-seq or protein evidence, using Helixer's GPU-accelerated deep-learning ab initio
  predictor, and then assess genome and proteome completeness with BUSCO and OMArk.
domain: annotation
organism_class:
- eukaryote
- fungi
- plant
- invertebrate
- vertebrate
input_data:
- genome-fasta-masked
source:
  ecosystem: iwc
  workflow: Genome annotation with Helixer
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/genome_annotation/annotation-helixer
  version: '0.3'
  license: MIT
tools:
- helixer
- gffread
- busco
- omark
- jcvi-gff-stats
- jbrowse
tags:
- genome-annotation
- ab-initio
- helixer
- deep-learning
- busco
- omark
- eukaryote
- gff3
- proteome-qc
test_data:
- role: genome_sequence_masked
  url: https://zenodo.org/records/13890774/files/genome_masked.fa?download=1
  filetype: fasta
expected_output:
- role: helixer_output
  description: Content assertions for `helixer output`.
  assertions:
  - 'has_text: Helixer'
- role: busco_sum_genome
  description: Content assertions for `busco sum genome`.
  assertions:
  - 'has_text: mucorales_odb10'
- role: busco_gff_genome
  description: Content assertions for `busco gff genome`.
  assertions:
  - 'has_text: miniprot'
- role: busco_missing_genome
  description: Content assertions for `busco missing genome`.
  assertions:
  - 'has_text: 10at4827'
- role: busco_table_genome
  description: Content assertions for `busco table genome`.
  assertions:
  - 'has_text: 10at4827'
- role: gffread_peptides
  description: Content assertions for `gffread peptides`.
  assertions:
  - 'has_text: _sample_000145.1'
- role: summary
  description: Content assertions for `summary`.
  assertions:
  - 'has_n_lines: {''n'': 27}'
- role: busco_table_predicted_proteins
  description: Content assertions for `busco table predicted proteins`.
  assertions:
  - 'has_n_lines: {''n'': 2452}'
- role: busco_sum_predicted_proteins
  description: Content assertions for `busco sum predicted proteins`.
  assertions:
  - 'has_n_lines: {''n'': 19}'
- role: busco_gff_predicted_proteins
  description: Content assertions for `busco gff predicted proteins`.
  assertions:
  - 'has_text: ##gff-version 3'
- role: busco_missing_predicted_proteins
  description: Content assertions for `busco missing predicted proteins`.
  assertions:
  - 'has_n_lines: {''n'': 2450}'
- role: omark_detail_sum
  description: Content assertions for `omark detail sum`.
  assertions:
  - 'has_n_lines: {''n'': 63}'
  - 'has_text: melanogaster subgroup'
---

# Ab initio eukaryotic genome annotation with Helixer

## When to use this sketch
- You have a soft-masked eukaryotic genome assembly (FASTA) and need a structural gene annotation (GFF3) quickly, without any RNA-seq, transcriptome, or homology evidence.
- The target organism falls into one of Helixer's supported lineages: `fungi`, `invertebrate`, `vertebrate`, or `land_plant`.
- GPU compute is available (Helixer is a deep-learning predictor that expects a GPU) and you want a single-tool, evidence-free pass rather than a multi-evidence pipeline.
- You also want integrated annotation QC: BUSCO on both the genome and predicted proteins, OMArk on the proteome, JCVI GFF statistics, and an interactive JBrowse visualization.

## Do not use when
- The genome is **prokaryotic / bacterial / archaeal** — use a Prokka/Bakta-style bacterial annotation sketch instead.
- You have RNA-seq or protein evidence and want an evidence-driven pipeline — use a MAKER/BRAKER/Funannotate-style sketch.
- You only need *functional* annotation (GO/InterPro/eggNOG) on an already-existing GFF — use a functional-annotation sketch (e.g. EggNOG-mapper / InterProScan).
- The organism class is outside Helixer's four trained lineages (e.g. protists, most algae, archaea).
- The assembly is unmasked — run a repeat-masking sketch (RepeatModeler/RepeatMasker) first.

## Analysis outline
1. **Helixer** (`genouest/helixer 0.3.3+galaxy1`) — predict gene structures directly from the masked genome FASTA for the chosen lineage, producing a GFF3.
2. **GFFRead** (`devteam/gffread 2.2.1.4+galaxy0`) — extract predicted protein sequences (`-y pep.fa`) from the Helixer GFF3 plus the genome FASTA.
3. **BUSCO on genome** (`iuc/busco 5.8.0+galaxy1`, `mode=geno`, `miniprot`) — assess assembly completeness against the chosen ODB10 lineage.
4. **JCVI Genome annotation statistics** (`iuc/jcvi_gff_stats 0.8.4`) — per-feature counts and length distributions over the Helixer GFF.
5. **BUSCO on predicted proteins** (`iuc/busco 5.8.0+galaxy1`, `mode=prot`) — completeness of the proteome extracted by GFFRead.
6. **OMArk** (`iuc/omark 0.3.1+galaxy1`, database `LUCA-v2.0.0.h5`) — orthology-based completeness, consistency, and contamination of the predicted proteome.
7. **JBrowse** (`iuc/jbrowse 1.16.11+galaxy1`) — package the genome + Helixer track as an interactive HTML browser for manual review.

## Key parameters
- `Helixer.lineages`: one of `fungi | invertebrate | vertebrate | land_plant` — must match the organism; drives the trained model.
- `Helixer.size`: `8` (model size used by this workflow).
- `Helixer.option_overlap.use_overlap`: `true` — enables overlapping subsequence prediction for higher recall.
- `Helixer.post_processing`: `window_size=100`, `edge_threshold=0.1`, `peak_threshold=0.8`, `min_coding_length=100` — CDS post-processing defaults; tune only if gene-length distributions look wrong.
- `BUSCO.lineage_dataset`: an ODB10 lineage (e.g. `mucorales_odb10`, `embryophyta_odb10`, `vertebrata_odb10`) appropriate for the organism — used for both the genome and protein BUSCO runs.
- `BUSCO(genome).busco_mode`: `geno` with `use_augustus=miniprot`.
- `BUSCO(proteins).busco_mode`: `prot`.
- `GFFRead.fa_outputs`: `-y pep.fa` (protein FASTA output).
- `OMArk.database`: `LUCA-v2.0.0.h5` (broad eukaryotic reference).
- Input genome **must be soft-masked** before Helixer.

## Test data
The test profile runs the workflow on a small masked eukaryotic (fungal) genome FASTA fetched from Zenodo (`genome_masked.fa`), with `Helixer lineage = fungi` and `BUSCO lineage = mucorales_odb10`. Expected results include a Helixer GFF3 (header containing `Helixer`), a BUSCO genome summary referencing `mucorales_odb10` and a BUSCO genome GFF produced via `miniprot`, `busco_missing`/`busco_table` files mentioning the BUSCO gene `10at4827`, a GFFRead protein FASTA containing the predicted transcript `_sample_000145.1`, a 27-line JCVI `summary` file, BUSCO-on-proteins tables of exactly 2452 and 2450 lines with a 19-line short summary, a GFF3 header on the protein BUSCO GFF, and an OMArk detail summary of 63 lines that references `melanogaster subgroup` (OMArk's closest-reference output). All outputs are validated by content assertions rather than byte-identical golden files.

## Reference workflow
Galaxy IWC — `workflows/genome_annotation/annotation-helixer` ("Genome annotation with Helixer"), release **0.3** (2025-07-18), MIT. Pinned tool versions: Helixer 0.3.3+galaxy1, GFFRead 2.2.1.4+galaxy0, BUSCO 5.8.0+galaxy1, OMArk 0.3.1+galaxy1, JCVI gff-stats 0.8.4, JBrowse 1.16.11+galaxy1.
