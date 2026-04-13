---
name: bulk-rnaseq-paired-end-star-quantification
description: Use when you need to process bulk paired-end Illumina RNA-seq from a
  eukaryote with an available reference genome and GTF annotation, producing gene-level
  count tables, FPKM/TPM estimates, and stranded/unstranded coverage tracks. Handles
  stranded and unstranded libraries and is aimed at standard differential-expression
  / expression-quantification preprocessing.
domain: rna-seq
organism_class:
- eukaryote
input_data:
- short-reads-paired
- reference-genome-indexed
- gtf-annotation
source:
  ecosystem: iwc
  workflow: 'RNA-Seq Analysis: Paired-End Read Processing and Quantification'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/transcriptomics/rnaseq-pe
  version: '1.3'
  license: MIT
tools:
- fastp
- star
- featurecounts
- stringtie
- cufflinks
- bedtools
- samtools
- multiqc
- fastqc
- rseqc
- picard
tags:
- rna-seq
- bulk
- paired-end
- quantification
- coverage
- fpkm
- tpm
- star
- featurecounts
- stringtie
- cufflinks
test_data:
- role: gtf_file_of_annotation
  url: https://zenodo.org/records/13987631/files/Saccharomyces_cerevisiae.R64-1-1.113.gtf
  sha1: afc40f49d008ba2a68b0ee0db130669b07cd445e
  filetype: gtf
- role: collection_paired_fastq_files__srr5085167__forward
  url: https://zenodo.org/records/13987631/files/SRR5085167_forward.fastqsanger.gz
  sha1: f910a2a7764249b690e28d8dcf4d7097d3c533f6
- role: collection_paired_fastq_files__srr5085167__reverse
  url: https://zenodo.org/records/13987631/files/SRR5085167_reverse.fastqsanger.gz
  sha1: 7558d21e69e0d7117a20305becdfdfc49769753e
expected_output:
- role: multiqc_stats
  description: Content assertions for `MultiQC stats`.
  assertions:
  - 'that: has_text_matching'
  - "expression: SRR5085167\t0.10[0-9]*\t16.45[0-9]*\t43.38[0-9]*\t0.32[0-9]*\t0.30[0-9]*\t\
    93.75\t0.11[0-9]*\t34.29\t0.19[0-9]*"
  - 'that: has_text_matching'
  - "expression: SRR5085167_forward\t*36.33[0-9]*\t46.0\t75.0\t75\t27.27[0-9]*\t0.39[0-9]*"
  - 'that: has_text_matching'
  - "expression: SRR5085167_reverse\t*35.31[0-9]*\t46.0\t75.0\t75\t45.45[0-9]*\t0.39[0-9]*"
- role: stranded_coverage
  description: Content assertions for `Stranded Coverage`.
  assertions:
  - 'SRR5085167_forward: has_size: {''value'': 635210, ''delta'': 30000}'
  - 'SRR5085167_reverse: has_size: {''value'': 618578, ''delta'': 30000}'
- role: gene_abundance_estimates_from_stringtie
  description: Content assertions for `Gene Abundance Estimates from StringTie`.
  assertions:
  - 'SRR5085167: has_text_matching: {''expression'': ''YAL038W\tCDC19\tchrI\t\\+\t71786\t73288\t92.5[0-9]*\t3273.[0-9]*\t[0-9]*.[0-9]*''}'
- role: unstranded_coverage
  description: Content assertions for `Unstranded Coverage`.
  assertions:
  - 'SRR5085167: has_size: {''value'': 1140004, ''delta'': 50000}'
- role: mapped_reads
  description: Content assertions for `Mapped Reads`.
  assertions:
  - 'SRR5085167: has_size: {''value'': 56913572, ''delta'': 2500000}'
- role: genes_expression_from_cufflinks
  description: Content assertions for `Genes Expression from Cufflinks`.
  assertions:
  - 'SRR5085167: has_text_matching: {''expression'': ''YAL038W\t-\t-\tYAL038W\tCDC19\t-\tchrI:71785-73288\t-\t-\t3437.[0-9]*\t3211.[0-9]*\t3662.[0-9]*\tOK''}'
- role: transcripts_expression_from_cufflinks
  description: Content assertions for `Transcripts Expression from Cufflinks`.
  assertions:
  - 'SRR5085167: has_text_matching: {''expression'': ''YAL038W_mRNA\t-\t-\tYAL038W\tCDC19\t-\tchrI:71785-73288\t1503\t102.8[0-9]*\t3437.[0-9]*\t3211.[0-9]*\t3662.[0-9]*\tOK''}'
- role: counts_table
  description: Content assertions for `Counts Table`.
  assertions:
  - "SRR5085167: has_line: YAL038W\t1591"
---

# Bulk paired-end RNA-seq: alignment, quantification and coverage

## When to use this sketch
- Bulk (not single-cell) paired-end Illumina RNA-seq from a eukaryote whose reference genome is available as a STAR index in Galaxy and for which a matching GTF annotation exists.
- User wants gene-level counts suitable for downstream DE (DESeq2/edgeR/limma), optionally together with FPKM/TPM and genome-browser coverage tracks.
- Library can be stranded (forward or reverse) or unstranded; strandedness is a first-class input.
- User wants an integrated MultiQC report covering adapter trimming, alignment, assignment rates and optionally FastQC, Picard MarkDuplicates, RSeQC read distribution, gene-body coverage and samtools idxstats.

## Do not use when
- Reads are single-end — use a single-end bulk RNA-seq sketch instead.
- Data is 10x / droplet / plate single-cell RNA-seq — use a `single-cell-rnaseq-*` sketch.
- Goal is de novo transcriptome assembly without a reference genome — use a Trinity-based assembly sketch.
- Goal is small-RNA / miRNA quantification, direct RNA Nanopore, or isoform-level long-read quantification — use the relevant long-read or small-RNA sketch.
- Goal is variant calling from RNA-seq (e.g. RNA editing, GATK RNA-seq variants) — use an RNA-seq variant-calling sketch.
- Goal is differential expression itself — this sketch stops at count tables and FPKM; pair it with a DE sketch.

## Analysis outline
1. Adapter and quality trimming of paired-end reads with **fastp** (Q30 filter, min length 15, paired-overlap adapter detection; explicit R1/R2 adapters optional).
2. Spliced alignment to the reference genome with **RNA STAR** using ENCODE-like long-RNA parameters, with the GTF supplied via `sjdbGTFfile` and `quantMode=GeneCounts` for per-gene read counts; strand-split bedGraph coverage (`outWigType=bedGraph`, `outWigStrand=Stranded`, normalized).
3. Optional gene-level counting with **featureCounts** against the GTF (`-t exon -g gene_id`, paired-end fragment mode, chimeras excluded), selected by user flag as an alternative to STAR GeneCounts.
4. Strandedness mapping: a `map_param_value` step converts the user's `stranded - forward / stranded - reverse / unstranded` choice into the matching flags for featureCounts (0/1/2), Cufflinks (`fr-unstranded/fr-secondstrand/fr-firststrand`) and StringTie (`--fr/--rf`/unset), and picks the correct STAR bedGraph column per sample.
5. Count-table post-processing: a subworkflow extracts the strand-appropriate column from STAR `ReadsPerGene.out.tab` to build an HTSeq-style two-column count table, or passes through featureCounts output.
6. Optional **Cufflinks** FPKM for genes and transcripts with bias correction, multi-read correction, reference annotation and an optional mask GTF (e.g. chrM) to exclude regions from normalization.
7. Optional **StringTie** with `-e -B` (guided by reference GTF) to produce gene abundance estimates (FPKM/TPM).
8. BAM filtering to uniquely mapped reads (`bamtools filter` on `NH:i:1`), then **bedtools genomecoveragebed** scaled to 1e6/uniquely-mapped-reads to build both combined and per-strand normalized bedGraphs, converted to bigWig via `wigToBigWig`.
9. For stranded libraries, a relabelling subworkflow rewrites STAR's `_str1/_str2` bedGraph element identifiers into `_forward/_reverse` according to the library strandedness before merging into a single stranded coverage collection.
10. Optional extended QC subworkflow: **FastQC** on raw reads, **Picard MarkDuplicates**, **samtools idxstats**, **RSeQC** `read_distribution` and `geneBody_coverage` (on a samtools-view subsample of 200k reads and a GTF-to-BED12 conversion).
11. **MultiQC** aggregation — a minimal report over fastp + STAR + featureCounts always, and a full report including FastQC/Picard/RSeQC/samtools when additional-QC is enabled.

## Key parameters
- `Strandedness`: one of `stranded - forward`, `stranded - reverse`, `unstranded`. Drives featureCounts `-s` (1/2/0), Cufflinks `--library-type`, StringTie `--fr`/`--rf`, the selected column of STAR `ReadsPerGene`, and the labelling of stranded coverage.
- fastp: `qualified_quality_phred=30`, `length_required=15`, paired-collection mode, adapter detection via overlap with optional `adapter_sequence1`/`adapter_sequence2`.
- STAR: indexed reference + history GTF, `sjdbOverhang=100`, `quantMode=GeneCounts`, ENCODE-style intron/align/filter parameters (`alignIntronMin=20`, `alignIntronMax=1e6`, `alignMatesGapMax=1e6`, `alignSJoverhangMin=8`, `outFilterMultimapNmax=20`, `outFilterMismatchNoverLmax=0.3`), `outWigType=bedGraph`, `outWigStrand=Stranded`, `outWigNorm=RPM`.
- featureCounts: `-t exon -g gene_id`, `PE_fragments`, `exclude_chimerics=true`, `min_overlap=1`.
- Uniquely-mapped filter: `bamtools filter` on tag `NH=1`.
- Coverage scaling factor: `1_000_000 / uniquely_mapped_reads` parsed from STAR `Log.final.out`.
- Cufflinks: `--multi-read-correct`, `--no-effective-length-correction`, bias correction against cached reference, optional mask GTF.
- StringTie: `-e -B` with reference GTF (`use_guide=yes`, `input_estimation=true`).
- Boolean switches exposed to the user: `Use featureCounts for generating count tables`, `Compute Cufflinks FPKM`, `Compute StringTie FPKM`, `Generate additional QC reports`.

## Test data
The source workflow's test profile runs a single paired-end yeast sample, SRR5085167, downsampled and hosted on Zenodo record 13987631 (`SRR5085167_forward.fastqsanger.gz` + `SRR5085167_reverse.fastqsanger.gz`) together with the Ensembl *Saccharomyces cerevisiae* R64-1-1 release 113 GTF. It is run against the `sacCer3` STAR index as a forward-stranded library (adapters `AGATCGGAAGAG` / `GATCGTCGGACT`) with additional QC, featureCounts, Cufflinks and StringTie all enabled. Expected outputs: a MultiQC stats row for SRR5085167 with fastp/STAR/featureCounts fields matching specific numeric ranges; a mapped BAM of roughly 57 MB; a counts table containing the line `YAL038W\t1591`; unstranded bigWig coverage around 1.14 MB and stranded forward/reverse bigWigs near 635 kB / 619 kB; a StringTie gene-abundance row for `YAL038W` / `CDC19` on `chrI:71786-73288`; and Cufflinks gene and transcript expression rows for the same `YAL038W` / `CDC19` locus with `OK` status.

## Reference workflow
Galaxy IWC `workflows/transcriptomics/rnaseq-pe` — “RNA-Seq Analysis: Paired-End Read Processing and Quantification”, release 1.3 (MIT), authored by Lucille Delisle and Pavankumar Videm.
