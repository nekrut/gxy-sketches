---
name: amplicon-asv-dada2-paired
description: Use when you need to turn paired-end 16S/18S/ITS amplicon Illumina reads
  into amplicon sequence variants (ASVs) with a sequence table, per-step read counts,
  and taxonomic assignments against a reference database (e.g. SILVA, GreenGenes,
  UNITE). Assumes already-demultiplexed, primer-trimmed paired FASTQs.
domain: amplicon
organism_class:
- bacterial
- eukaryote
input_data:
- short-reads-paired
- amplicon-fastq
- taxonomy-reference-fasta
source:
  ecosystem: iwc
  workflow: dada2 amplicon analysis pipeline - for paired end data
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/amplicon/dada2
  version: '0.3'
  license: MIT
tools:
- dada2
- dada2-filterAndTrim
- dada2-learnErrors
- dada2-dada
- dada2-mergePairs
- dada2-makeSequenceTable
- dada2-removeBimeraDenovo
- dada2-assignTaxonomy
tags:
- amplicon
- 16s
- 18s
- its
- asv
- dada2
- microbiome
- metabarcoding
- paired-end
test_data:
- role: paired_input_data__f3d0__forward
  url: https://zenodo.org/record/800651/files/F3D0_R1.fastq
  sha1: e031c5f2942d995970471f112a52093918cb7fec
- role: paired_input_data__f3d0__reverse
  url: https://zenodo.org/record/800651/files/F3D0_R2.fastq
  sha1: af06e2cfbe8bd6415023dd8aa49cc8c44541ec0c
- role: paired_input_data__f3d5__forward
  url: https://zenodo.org/record/800651/files/F3D5_R1.fastq
  sha1: 7000705a3f5610ffcb01c79d936779a48c35851f
- role: paired_input_data__f3d5__reverse
  url: https://zenodo.org/record/800651/files/F3D5_R2.fastq
  sha1: 3233317bde4fd33c640d28d3982afb8f32065b61
- role: paired_input_data__f3d145__forward
  url: https://zenodo.org/record/800651/files/F3D145_R1.fastq
  sha1: 752770a64e7998b6b7eddbe73bdfd44f1029d045
- role: paired_input_data__f3d145__reverse
  url: https://zenodo.org/record/800651/files/F3D145_R2.fastq
  sha1: 5007557c8f03c5ee7952293b9f39d7eabb538e01
- role: paired_input_data__f3d150__forward
  url: https://zenodo.org/record/800651/files/F3D150_R1.fastq
  sha1: 43e9efbe227ef441e197e68213a3cc05cb7d30e2
- role: paired_input_data__f3d150__reverse
  url: https://zenodo.org/record/800651/files/F3D150_R2.fastq
  sha1: dde2d7b349bd24d298f5f21bf1103ad3cf4e0a2e
- role: paired_input_data__mock__forward
  url: https://zenodo.org/record/800651/files/Mock_R1.fastq
  sha1: 664cb4f1feffc1b71a8871bc8d08cb25a488b717
- role: paired_input_data__mock__reverse
  url: https://zenodo.org/record/800651/files/Mock_R2.fastq
  sha1: 5d6e794e37b308a3562dbd93929ea54a561abd0a
expected_output:
- role: sequence_table
  path: expected_output/Sequence Table.dada2_sequencetable
  description: Content assertions for `Sequence Table`.
  assertions:
  - 'has_n_columns: {''n'': 6}'
  - 'has_n_lines: {''n'': 171}'
- role: counts
  path: expected_output/Counts.tabular
  description: Content assertions for `Counts`.
  assertions:
  - 'has_n_columns: {''n'': 8}'
  - 'has_n_lines: {''n'': 6}'
- role: taxonomy
  description: Content assertions for `Taxonomy`.
  assertions:
  - 'has_text: Firmicutes'
  - 'has_n_columns: {''n'': 7}'
  - 'has_n_lines: {''n'': 171}'
---

# DADA2 paired-end amplicon ASV analysis

## When to use this sketch
- User has demultiplexed, paired-end Illumina amplicon FASTQs (16S rRNA, 18S, ITS, or similar metabarcoding marker).
- Goal is an exact amplicon sequence variant (ASV) table plus taxonomic assignments, not OTU clustering.
- Primers have already been removed (or the user is willing to truncate reads to trim them) and amplicon length is compatible with paired-end merging.
- A DADA2-formatted taxonomy reference (e.g. SILVA, GreenGenes2, UNITE, RDP) is available or can be cached server-side.
- Read-count tracking through each denoising step is desired for QC.

## Do not use when
- Reads are single-end only → use a DADA2 single-end amplicon sketch instead.
- Long-read amplicons (PacBio CCS, Nanopore full-length 16S) → use a long-read amplicon / LotuS / minimap-based sketch.
- Shotgun metagenomics data (not marker-gene amplicons) → use a metagenomics taxonomic profiling sketch (Kraken2, MetaPhlAn, etc.).
- OTU-level clustering with VSEARCH/USEARCH or mothur is explicitly requested.
- Raw multiplexed reads still containing barcodes/primers that cannot simply be truncated — demultiplex and primer-trim (e.g. cutadapt) first.

## Analysis outline
1. Sort the paired input collection so downstream per-sample collections stay aligned (Apply Rules).
2. `dada2: plotQualityProfile` on raw reads to visually pick truncation lengths.
3. `dada2: filterAndTrim` — quality filter and truncate forward/reverse reads to user-chosen lengths.
4. `dada2: plotQualityProfile` on filtered reads to confirm quality.
5. Unzip the filtered paired collection into separate forward and reverse datasets.
6. `dada2: learnErrors` — learn an error model independently for forward and reverse reads.
7. `dada2: dada` — denoise forward and reverse reads using their error models, with optional pooling.
8. `dada2: mergePairs` — merge denoised forward/reverse reads into full amplicons.
9. `dada2: makeSequenceTable` — build the ASV-by-sample sequence table.
10. `dada2: removeBimeraDenovo` — remove chimeras with the consensus method.
11. `dada2: seqCounts` — tabulate per-sample read counts across every step for QC.
12. `dada2: assignTaxonomy` — assign taxonomy against a cached reference database (e.g. SILVA).

## Key parameters
- Forward read truncation length (`filterAndTrim truncLen` forward): set from the raw quality profile; e.g. 240 for V4 16S.
- Reverse read truncation length (`filterAndTrim truncLen` reverse): set from the raw quality profile; e.g. 160 for V4 16S.
- `filterAndTrim`: `maxEE=2`, `truncQ=2`, `maxN=0`, `minLen=20`, `rmPhiX=true` (DADA2 tutorial defaults).
- `learnErrors`: `nbases=8` (1e8), `errfoo=loessErrfun`.
- `dada` pooling: `FALSE` (per-sample) by default; set `TRUE` or `pseudo` for higher sensitivity on rare variants at the cost of runtime.
- `mergePairs`: `minOverlap=12`, `maxMismatch=0`.
- `removeBimeraDenovo`: `method=consensus`.
- `assignTaxonomy`: `minBoot=50`; select a cached reference such as `silva_132` (or newer SILVA, GreenGenes2, UNITE as appropriate for the marker).

## Test data
Five paired-end FASTQ samples from the DADA2 MiSeq SOP tutorial mouse-gut dataset (F3D0, F3D5, F3D145, F3D150, and a Mock community), hosted on Zenodo record 800651. The test runs with forward truncation 240, reverse truncation 160, pooling disabled, and the cached `silva_132` reference. Expected outputs are: a sequence table (`dada2_sequencetable`) with 6 columns and 171 lines, a per-step counts tabular file with 8 columns and 6 lines (one header plus five samples), and a taxonomy tabular file with 7 columns, 171 lines, and at least 131 rows assigned to phylum `Firmicutes` — consistent with a Firmicutes-dominated mouse gut community.

## Reference workflow
Galaxy IWC `workflows/amplicon/dada2/dada2_paired.ga`, release 0.3 (DADA2 tool suite v1.34.0+galaxy0), following the canonical DADA2 tutorial at https://benjjneb.github.io/dada2/tutorial.html.
