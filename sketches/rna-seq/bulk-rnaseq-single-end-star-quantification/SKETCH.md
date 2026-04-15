---
name: bulk-rnaseq-single-end-star-quantification
description: Use when you need to process bulk single-end RNA-seq Illumina FASTQ data
  against a reference genome with a GTF annotation to produce gene-level count tables,
  FPKM/TPM expression values, and normalized genome coverage tracks. Covers stranded
  or unstranded libraries for any eukaryote with a STAR-indexed genome.
domain: rna-seq
organism_class:
- eukaryote
input_data:
- short-reads-single
- reference-genome-indexed
- gtf-annotation
source:
  ecosystem: iwc
  workflow: 'RNA-Seq Analysis: Single-End Read Processing and Quantification'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/transcriptomics/rnaseq-sr
  version: '1.3'
  license: MIT
  slug: transcriptomics--rnaseq-sr
tools:
- name: fastp
  version: 1.1.0+galaxy0
- name: star
- name: featurecounts
  version: 2.1.1+galaxy0
- name: stringtie
  version: 2.2.3+galaxy0
- name: cufflinks
  version: 2.2.1.4
- name: bedtools
- name: samtools
- name: rseqc
- name: picard
- name: fastqc
- name: multiqc
  version: 1.33+galaxy0
tags:
- rna-seq
- bulk
- single-end
- star
- gene-counts
- fpkm
- coverage
- bigwig
- transcriptomics
test_data:
- role: gtf_file_of_annotation
  url: https://zenodo.org/records/13987631/files/Saccharomyces_cerevisiae.R64-1-1.113.gtf
  sha1: afc40f49d008ba2a68b0ee0db130669b07cd445e
  filetype: gtf
- role: collection_of_fastq_files__srr5085167
  url: https://zenodo.org/records/13987631/files/SRR5085167_forward.fastqsanger.gz
  sha1: f910a2a7764249b690e28d8dcf4d7097d3c533f6
expected_output:
- role: multiqc_stats
  description: Content assertions for `MultiQC stats`.
  assertions:
  - 'has_text_matching: {''expression'': ''SRR5085167\t0.11[0-9]*\t18.3[0-9]*\t69.6[0-9]*\t0.3[0-9]*\t0.3[0-9]*\t94.62\t0.12[0-9]*\t34.43\t0.2[0-9]*\t36.[0-9]*\t46.0\t75.0\t75\t27.27[0-9]*\t0.39[0-9]*''}'
- role: counts_table
  description: Content assertions for `Counts Table`.
  assertions:
  - "SRR5085167: has_line: YAL038W\t1775"
- role: mapped_reads
  description: Content assertions for `Mapped Reads`.
  assertions:
  - 'SRR5085167: has_size: {''value'': 31570787, ''delta'': 3000000}'
- role: gene_abundance_estimates_from_stringtie
  description: Content assertions for `Gene Abundance Estimates from StringTie`.
  assertions:
  - 'SRR5085167: has_text_matching: {''expression'': ''YAL038W\tCDC19\tchrI\t\\+\t71786\t73288\t57.[0-9]*\t3575.[0-9]*\t3084.[0-9]*''}'
- role: genes_expression_from_cufflinks
  description: Content assertions for `Genes Expression from Cufflinks`.
  assertions:
  - 'SRR5085167: has_text_matching: {''expression'': ''YAL038W\t-\t-\tYAL038W\tCDC19\t-\tchrI:71785-73288\t-\t-\t3375.8[0-9]*\t3161.3[0-9]*\t3590.3[0-9]*\tOK''}'
- role: transcripts_expression_from_cufflinks
  description: Content assertions for `Transcripts Expression from Cufflinks`.
  assertions:
  - 'SRR5085167: has_text_matching: {''expression'': ''YAL038W_mRNA\t-\t-\tYAL038W\tCDC19\t-\tchrI:71785-73288\t1503\t57.56[0-9]*\t3375.8[0-9]*\t3161.3[0-9]*\t3590.3[0-9]*\tOK''}'
- role: stranded_coverage
  description: Content assertions for `Stranded Coverage`.
  assertions:
  - 'SRR5085167_forward: has_size: {''value'': 555489, ''delta'': 50000}'
  - 'SRR5085167_reverse: has_size: {''value'': 526952, ''delta'': 50000}'
- role: unstranded_coverage
  description: Content assertions for `Unstranded Coverage`.
  assertions:
  - 'SRR5085167: has_size: {''value'': 978542, ''delta'': 90000}'
---

# Bulk single-end RNA-seq quantification and coverage

## When to use this sketch
- Bulk single-end Illumina RNA-seq FASTQ data from any eukaryote (yeast, mouse, human, fly, plant, etc.) where a STAR-indexed reference genome and a matching GTF annotation are available.
- You need gene-level count tables (STAR GeneCounts or featureCounts) suitable for downstream differential expression (DESeq2/edgeR).
- You also want FPKM/TPM expression values (Cufflinks and/or StringTie) and strand-aware or unstranded normalized genome coverage bigWig tracks for visualization.
- The library is either unstranded, forward-stranded, or reverse-stranded and you know (or will determine via MultiQC/RSeQC) which.
- You want an integrated QC report bundling fastp, STAR, featureCounts, FastQC, Picard MarkDuplicates, RSeQC read distribution and gene body coverage, and samtools idxstats.

## Do not use when
- Reads are paired-end — use the sibling `bulk-rnaseq-paired-end-star-quantification` sketch instead.
- Data are single-cell / 10x Genomics — use a single-cell RNA-seq sketch (`scrna-10x-*`).
- You need de novo transcript assembly without a reference genome — use a Trinity/assembly sketch.
- You need isoform-level quantification with pseudoalignment (Salmon/Kallisto) — use a `rnaseq-salmon-quant` sketch.
- You are calling variants from RNA-seq — use an `rnaseq-variant-calling` sketch.
- Data are long-read (ONT/PacBio) RNA — use a long-read RNA sketch.

## Analysis outline
1. Adapter and quality trimming of single-end FASTQ with **fastp** (min length 15, Q30 filter, optional user-supplied adapter sequence).
2. Splice-aware alignment to the reference genome with **RNA STAR** using ENCODE long-RNA parameters, with `--sjdbGTFfile` for the annotation and `--quantMode GeneCounts` to produce per-gene read counts.
3. STAR additionally emits strand-specific bedGraph signal tracks (`outWigType bedGraph`, normalized, split by strand) during the same run.
4. Optional gene-level quantification with **featureCounts** against the GTF (feature=exon, attribute=gene_id) selected by a boolean parameter; otherwise use STAR's `ReadsPerGene.out.tab`.
5. Strandedness parameter is fanned out via `map_param_value` into the correct flags for featureCounts (`0/1/2`), Cufflinks (`fr-unstranded/fr-secondstrand/fr-firststrand`), and StringTie (`''/--fr/--rf`).
6. Optional FPKM calculation with **Cufflinks** (bias correction, multi-read correction, mask GTF for rRNA/chrM regions) and/or **StringTie** (gene abundance estimation, GTF guide).
7. Filter STAR BAM to uniquely mapped reads (`NH:i:1`) with **bamtools filter**, then compute a per-million-uniquely-mapped scaling factor from the STAR log and generate a normalized unstranded coverage bedGraph with **bedtools genomecov** (`-bg -split -scale`), converted to bigWig with **wig_to_bigWig**.
8. Re-label and merge STAR's strand1/strand2 bedGraphs according to library strandedness, then convert to a stranded bigWig collection.
9. Post-process STAR ReadsPerGene into an HTSeq-compatible 2-column counts table via awk (column selected by strandedness), or pass through featureCounts output.
10. Optional extended QC subworkflow runs **FastQC**, **Picard MarkDuplicates**, **samtools idxstats**, **RSeQC** `read_distribution` and `geneBody_coverage` (on a 200k-read `samtools view` subsample), then aggregates everything plus fastp/STAR/featureCounts into a combined **MultiQC** HTML report. A smaller MultiQC runs when additional QC is disabled.

## Key parameters
- `Strandedness`: one of `stranded - forward`, `stranded - reverse`, `unstranded`. Critical — drives featureCounts `-s`, Cufflinks `--library-type`, StringTie `--fr/--rf`, coverage track labeling, and which STAR ReadsPerGene column is used.
- `Forward adapter`: optional explicit adapter (e.g. TruSeq `AGATCGGAAGAGCACACGTCTGAACTCCAGTCAC`, Nextera `CTGTCTCTTATACACATCTCCGAGCCCACGAGAC`); fastp auto-detects if empty.
- fastp: `qualified_quality_phred=30`, `length_required=15`, adapter trimming enabled.
- STAR: ENCODE long-RNA settings — `alignIntronMin=20`, `alignIntronMax=1000000`, `alignSJoverhangMin=8`, `alignSJDBoverhangMin=1`, `outFilterMultimapNmax=20`, `outFilterMismatchNoverLmax=0.3`, `outFilterMismatchNoverReadLmax=0.04`, `sjdbOverhang=100`, `quantMode=GeneCounts`, `outWigType=bedGraph` with `outWigNorm=RPM` and split strands, `outSAMattributes=NH HI AS nM`.
- featureCounts: `gff_feature_type=exon`, `gff_feature_attribute=gene_id`, `paired_end_status=single_end`, `min_overlap=1`.
- BAM uniqueness filter: `tag NH=1`.
- Coverage scaling factor: `1000000 / (STAR Uniquely mapped reads number)` applied to bedtools genomecov `-scale`.
- `Use featureCounts for generating count tables`: boolean, selects featureCounts vs STAR GeneCounts.
- `Compute Cufflinks FPKM` / `Compute StringTie FPKM`: booleans gating the two FPKM branches.
- `Generate additional QC reports`: boolean enabling the full FastQC/Picard/RSeQC/MultiQC subworkflow.
- Cufflinks mask GTF (optional): GTF of regions like chrM to exclude from FPKM normalization.
- Reference genome: selected from STAR's cached genome list (matches Cufflinks cached sequence source for bias correction).

## Test data
A single-end test run uses one *Saccharomyces cerevisiae* RNA-seq FASTQ (`SRR5085167_forward.fastqsanger.gz`) and the Ensembl R64-1-1 release 113 GTF (`Saccharomyces_cerevisiae.R64-1-1.113.gtf`), both from Zenodo record 13987631, aligned against the cached `sacCer3` STAR index. It runs with `Strandedness=stranded - forward`, fastp adapter `AGATCGGAAGAG`, featureCounts enabled, additional QC enabled, and both Cufflinks and StringTie FPKM enabled. Expected outputs include a MultiQC stats row for SRR5085167 with ~94.6% uniquely mapped reads, a `Counts Table` containing `YAL038W\t1775`, a STAR BAM `Mapped Reads` of ~31.5 MB, StringTie gene abundance with a CDC19/YAL038W row on chrI:71786-73288 and FPKM ~3575, Cufflinks gene and transcript FPKM ~3375.8 for YAL038W/CDC19, a `Stranded Coverage` collection with ~555 kB forward and ~527 kB reverse bedGraphs, and an ~979 kB `Unstranded Coverage` track.

## Reference workflow
Galaxy IWC — `workflows/transcriptomics/rnaseq-sr` ("RNA-Seq Analysis: Single-End Read Processing and Quantification"), release 1.3, MIT licensed, by Lucille Delisle and Pavankumar Videm.
