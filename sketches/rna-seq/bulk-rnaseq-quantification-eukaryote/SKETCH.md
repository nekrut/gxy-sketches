---
name: bulk-rnaseq-quantification-eukaryote
description: Use when you need to quantify gene and transcript expression from bulk
  RNA-seq short reads against a eukaryotic reference genome with a GTF/GFF annotation,
  producing per-gene and per-transcript count/TPM matrices plus an extensive QC report.
  Default path is STAR alignment + Salmon transcriptome quantification.
domain: rna-seq
organism_class:
- eukaryote
input_data:
- short-reads-paired
- short-reads-single
- reference-fasta
- gtf
source:
  ecosystem: nf-core
  workflow: nf-core/rnaseq
  url: https://github.com/nf-core/rnaseq
  version: 3.24.0
  license: MIT
tools:
- fastqc
- trim-galore
- fastp
- sortmerna
- star
- salmon
- rsem
- hisat2
- kallisto
- samtools
- picard
- stringtie
- rseqc
- qualimap
- dupradar
- deseq2
- multiqc
tags:
- rnaseq
- bulk
- gene-expression
- star
- salmon
- tximport
- quantification
- eukaryote
- illumina
test_data: []
expected_output: []
---

# Bulk RNA-seq gene/transcript quantification (eukaryote)

## When to use this sketch
- Bulk (not single-cell) RNA-seq from Illumina short reads, single- or paired-end.
- Eukaryotic organism with a reference genome FASTA and matching GTF/GFF annotation (human, mouse, zebrafish, plant, fungi, etc.).
- Goal is a gene- and/or transcript-level count and TPM matrix suitable for downstream differential expression (e.g. DESeq2, edgeR, nf-core/differentialabundance).
- Comparable samples across conditions; the workflow also produces sample-similarity QC (PCA, clustering) via DESeq2.
- Optional add-ons supported here: UMI-based dedup (UMI-tools / UMICollapse), rRNA depletion (SortMeRNA / Bowtie2 / RiboDetector), contaminant host filtering (BBSplit), contamination screening (Kraken2/Bracken or Sylph), spike-ins via `--additional_fasta`.

## Do not use when
- Bacterial or archaeal RNA-seq: use a prokaryotic-bulk-rnaseq sketch instead (this pipeline's `-profile prokaryotic` swaps to Bowtie2+Salmon with CDS-based counting; splice-aware STAR is inappropriate).
- Single-cell or single-nucleus RNA-seq (10x, Smart-seq3, etc.): use a scRNA-seq sketch (nf-core/scrnaseq).
- Long-read RNA-seq (ONT/PacBio cDNA or direct RNA): use a long-read transcriptomics sketch (nf-core/nanoseq, nf-core/rnasplice long-read path).
- Variant calling from RNA-seq, fusion detection, or splicing/isoform-switch analysis as the primary goal: use dedicated sketches (nf-core/rnavar, nf-core/rnafusion, nf-core/rnasplice).
- De novo transcriptome assembly without a reference genome.
- Differential expression statistics themselves: this workflow stops at normalized counts and exploratory QC; run nf-core/differentialabundance or custom DESeq2/edgeR downstream.

## Analysis outline
1. Merge re-sequenced FASTQs per sample (`cat`) and lint with `fq lint`.
2. Auto-infer strandedness by sub-sampling reads and pseudo-aligning with Salmon when `strandedness=auto`.
3. Raw-read QC with FastQC.
4. Optional UMI extraction with UMI-tools.
5. Adapter/quality trimming with Trim Galore! (default) or fastp.
6. Optional contaminant-genome filtering with BBSplit and rRNA removal with SortMeRNA (default), Bowtie2, or RiboDetector.
7. Genome alignment and transcriptome quantification via one of: STAR→Salmon (default), STAR→RSEM, HISAT2 (alignment only, no quant), or Bowtie2→Salmon (prokaryotic profile).
8. Sort/index BAMs with SAMtools; optional UMI dedup (UMI-tools or UMICollapse) or Picard MarkDuplicates.
9. Transcript assembly/quantification with StringTie; bigWig coverage tracks via BEDTools + bedGraphToBigWig.
10. Post-alignment QC: RSeQC modules, Qualimap RNA-seq, dupRadar, Preseq, featureCounts biotype QC, DESeq2 PCA/heatmap (or the single-pass `--use_rustqc` replacement).
11. Optional pseudo-alignment and quantification in parallel with Salmon or Kallisto (`--pseudo_aligner`).
12. Optional contaminant screening on unmapped or trimmed reads with Kraken2/Bracken or Sylph.
13. Aggregate everything into a MultiQC report; tximport produces gene- and transcript-level count/TPM matrices and `SummarizedExperiment` RDS objects.

## Key parameters
- `--input <samplesheet.csv>`: CSV with columns `sample,fastq_1,fastq_2,strandedness` (+ optional `seq_platform`, `seq_center`). Same `sample` value across rows = technical replicates, auto-merged.
- `--outdir <dir>`: results directory (absolute path on cloud).
- `--fasta <genome.fa[.gz]>` and `--gtf <annotation.gtf[.gz]>` (or `--gff`): reference genome + annotation. Keep the source consistent (all Ensembl, all GENCODE, etc.).
- `--gencode`: set when using GENCODE FASTA/GTF (switches `featurecounts_group_type` to `gene_type` and passes `--gencode` to Salmon indexing).
- `strandedness` per sample: `forward`, `reverse`, `unstranded`, or `auto` (auto-infer via Salmon sub-sampling, governed by `--stranded_threshold 0.8` and `--unstranded_threshold 0.1`).
- `--aligner`: `star_salmon` (default, recommended), `star_rsem`, `hisat2` (no quantification), or `bowtie2_salmon` (prokaryotic).
- `--pseudo_aligner salmon|kallisto`: run Salmon/Kallisto pseudo-alignment in addition (or alone with `--skip_alignment`).
- `--trimmer trimgalore|fastp`; tune with `--extra_trimgalore_args` / `--extra_fastp_args`; `--min_trimmed_reads 10000` drops under-sequenced samples.
- `--with_umi` plus `--umitools_extract_method`, `--umitools_bc_pattern[2]`, `--umi_dedup_tool umitools|umicollapse` for UMI workflows.
- `--remove_ribo_rna` with `--ribo_removal_tool sortmerna|bowtie2|ribodetector` and `--ribo_database_manifest` for rRNA depletion.
- `--skip_alignment` + BAM columns in the samplesheet enables the two-step reprocessing workflow (requires BAMs produced by an earlier run with `--save_align_intermeds`).
- `--save_reference` to persist generated STAR/Salmon/RSEM/HISAT2/Kallisto indices for reuse.
- `--extra_star_align_args`, `--extra_salmon_quant_args` for custom tool tuning (e.g. 3' tag protocols need `--extra_salmon_quant_args '--noLengthCorrection'`).
- `--contaminant_screening sylph|kraken2|kraken2_bracken` with `--kraken_db` or `--sylph_db`/`--sylph_taxonomy` for contaminant detection.
- `-profile docker|singularity|conda|test|arm64|prokaryotic|rapid_quant` selects the container/engine and preset; always test with `-profile test` before production.

## Test data
The bundled `test` profile (`conf/test.config`) points at the nf-core `test-datasets` rnaseq branch and uses a minimal samplesheet (`samplesheet_test.csv`) of paired- and single-end libraries subsampled to run in minutes. Reference files are a small `genome.fasta`, a `genes_with_empty_tid.gtf.gz` (to exercise GTF filtering) plus a GFF, a pre-built `transcriptome.fasta`, a GFP `additional_fasta` spike-in, a BBSplit FASTA list, a pre-built HISAT2 index, a pre-built Salmon index, and a SARS-CoV-2 Kraken2 database for contaminant screening. Running `nextflow run nf-core/rnaseq -profile test,docker --outdir results` is expected to complete end-to-end and produce: per-sample STAR BAMs under `star_salmon/`, merged gene/transcript count and TPM TSVs (`salmon.merged.gene_counts.tsv`, `salmon.merged.transcript_tpm.tsv`, etc.), `tx2gene.tsv`, `salmon.merged.gene.SummarizedExperiment.rds`, DESeq2 QC PCA/clustering PDFs, FastQC/RSeQC/Qualimap/dupRadar/featureCounts biotype outputs, and a consolidated `multiqc/star_salmon/multiqc_report.html`. The full-size benchmark (`conf/test_full.config`) runs against human GRCh37 with public samples to validate the production configuration.

## Reference workflow
nf-core/rnaseq v3.24.0 (DOI [10.5281/zenodo.1400710](https://doi.org/10.5281/zenodo.1400710), MIT). See `docs/usage.md` and `docs/output.md` for authoritative parameter and output descriptions, and `nextflow_schema.json` for the complete parameter list.
