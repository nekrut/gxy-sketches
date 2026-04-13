---
name: rna-outlier-detection-mendelian
description: Use when you have aligned RNA-seq BAMs from a cohort (ideally >=30-50
  samples) of human patients and want to detect aberrant gene expression, aberrant
  splicing, and mono-allelic expression to prioritize candidate disease genes in rare/Mendelian
  disease diagnostics. Requires RNA BAMs plus optional matched DNA VCFs for the MAE
  module.
domain: rna-seq
organism_class:
- vertebrate
- diploid
- human
input_data:
- rna-bam
- reference-fasta
- gene-annotation-gtf
- dna-vcf
source:
  ecosystem: nf-core
  workflow: nf-core/drop
  url: https://github.com/nf-core/drop
  version: 1.0.0
  license: MIT
tools:
- OUTRIDER
- FRASER
- FRASER2
- GATK-ASEReadCounter
- DESeq2
- GenomicAlignments
- Rsubread
- bcftools
- samtools
- MultiQC
tags:
- rna-seq
- outlier-detection
- aberrant-expression
- aberrant-splicing
- mono-allelic-expression
- rare-disease
- mendelian
- drop
- outrider
- fraser
- mae
test_data: []
expected_output: []
---

# RNA outlier detection for rare / Mendelian disease (DROP)

## When to use this sketch
- You have a cohort of aligned human RNA-seq BAMs (typically patients with suspected rare / Mendelian disease) and want to identify, per sample, which genes are expression outliers, which splice junctions are aberrant, and which heterozygous sites show mono-allelic expression.
- You are running a diagnostic or research outlier-detection analysis where the statistical power comes from comparing each sample against a cohort distribution (recommended >=30, ideally >=50 samples per DROP group).
- Inputs are already aligned (coordinate-sorted, indexed) BAMs against hg19/hs37d5 or hg38/GRCh38. You have a matching gene annotation (GTF described via a gene_annotation YAML) and the reference FASTA (UCSC- and/or NCBI-style contig naming).
- You want the three classical DROP modules – aberrant expression (OUTRIDER), aberrant splicing (FRASER / FRASER2), and mono-allelic expression (GATK ASEReadCounter + DESeq2-based test) – wired together with integrated MultiQC reporting.
- You may optionally supply matched DNA VCFs (with tabix indices) per sample to enable the MAE subworkflow and VCF-BAM sample-identity QC.

## Do not use when
- You only need standard differential expression between two conditions → use a bulk RNA-seq quantification/DE pipeline (e.g. nf-core/rnaseq + DESeq2/edgeR), not an outlier pipeline.
- You start from raw FASTQ and need alignment/quantification from scratch → run nf-core/rnaseq first (or similar) to produce the BAMs, then feed them here.
- You want fusion gene detection → use a fusion-calling pipeline (e.g. nf-core/rnafusion).
- You are working with single-cell RNA-seq → use nf-core/scrnaseq or a scRNA outlier-specific tool; DROP assumes bulk library-level counts.
- You have fewer than ~20 samples per DROP group; OUTRIDER/FRASER autoencoder fits will be unstable. Either expand the cohort or import external counts via the `GENE_COUNTS_FILE`/`SPLICE_COUNTS_DIR` columns.
- Your organism is non-human / non-vertebrate; DROP is tuned to human gene annotation, HPO integration, and gnomAD-style allele frequencies.
- You need germline or somatic variant calling from the RNA or DNA data → use a dedicated variant-calling workflow (e.g. nf-core/sarek, GATK RNA-seq short variant workflow).

## Analysis outline
1. Parse the TSV samplesheet, grouping RNA samples by `DROP_GROUP` and routing each group to the enabled subworkflows.
2. Index any BAM/CRAM inputs that lack `.bai`/`.tbi`, and convert CRAM→BAM if needed (samtools).
3. Aberrant expression: count reads per gene over the provided GTF annotation using Bioconductor `GenomicAlignments` (honoring `PAIRED_END`, `STRAND`, `COUNT_MODE`, `COUNT_OVERLAPS`), then fit OUTRIDER with the chosen covariation-removal method (autoencoder / PCA / PEER) to detect gene-level expression outliers per sample.
4. Aberrant splicing: count split and non-split reads at splice junctions with `GenomicAlignments` + `Rsubread`, filter introns by expression/quantile/delta-psi, then fit FRASER or FRASER2 (PCA or PCA-BB-Decoder) and call per-sample aberrant splicing events.
5. Mono-allelic expression: for each RNA sample with a matched DNA VCF, run GATK `ASEReadCounter` against the UCSC- or NCBI-named FASTA (chosen by the `GENOME` column) to count allelic reads at heterozygous SNVs, then apply the DESeq2-based MAE test (tMAE) with optional gnomAD AF annotation and cohort-frequency filtering.
6. MAE QC: compare DNA vs RNA genotypes at a reference VCF (`mae_qc_vcf`) via bcftools to flag sample swaps using `mae_dna_rna_match_cutoff`.
7. Optionally export per-group gene-count and splice-count matrices under `processed_results/exported_counts/` so they can be reused as external counts in future runs.
8. Collect per-subworkflow result tables and HTML summaries and produce a unified MultiQC report across all DROP groups.

## Key parameters
- `--input` (TSV samplesheet; required columns `RNA_ID`, `RNA_BAM_FILE`, `DROP_GROUP`, `STRAND`; MAE additionally needs `DNA_ID`, `DNA_VCF_FILE`, `GENOME`).
- `--genome` one of `hg19`, `hs37d5`, `hg38`, `GRCh38` – must match the BAM alignments.
- `--gene_annotation` YAML mapping annotation keys (e.g. `v29`, `gencode34`) to GTF paths; the key is referenced in the `GENE_ANNOTATION` samplesheet column.
- `--ucsc_fasta` / `--ucsc_fai` / `--ucsc_dict` and/or `--ncbi_fasta` / `--ncbi_fai` / `--ncbi_dict` – required for MAE; pick the style matching each sample's `GENOME` column.
- Subworkflow toggles: `--ae_skip`, `--as_skip`, `--mae_skip`; group filters `--ae_groups`, `--as_groups`, `--mae_groups`.
- Aberrant expression (OUTRIDER): `--ae_min_ids` (≥50 recommended), `--ae_fpkm_cutoff` (default 1), `--ae_implementation` (`autoencoder`|`pca`|`peer`), `--ae_padj_cutoff` (default 0.05), `--ae_z_score_cutoff`, `--ae_max_tested_dimension_proportion` (default 3), `--ae_use_grid_search_to_obtain_q`, optional `--ae_genes_to_test`.
- Aberrant splicing (FRASER/FRASER2): `--as_fraser_version` (default `FRASER2`), `--as_implementation` (`PCA`|`PCA-BB-Decoder`), `--as_min_expression_in_one_sample` (default 20), `--as_quantile_min_expression`, `--as_quantile_for_filtering` (0.95 for FRASER, 0.75 for FRASER2), `--as_min_delta_psi`, `--as_delta_psi_cutoff` (0.3 FRASER / 0.1 FRASER2), `--as_padj_cutoff` (default 0.1), `--as_long_read` for ONT/PacBio.
- Mono-allelic expression: `--mae_padj_cutoff` (default 0.05), `--mae_allelic_ratio_cutoff` (default 0.8), `--mae_add_af`, `--mae_max_af` (default 0.001), `--mae_max_var_freq_cohort` (default 0.05), `--mae_qc_vcf`(+`_tbi`), `--mae_dna_rna_match_cutoff` (default 0.05), `--mae_gatk_header_check`.
- `--random_seed` for reproducible autoencoder fits; `-profile docker|singularity|conda` for environment management.

## Test data
The pipeline's `test` profile runs against the Gagneur lab DROP demo data restricted to human chromosome 21 (hg19). Inputs are a small TSV samplesheet of RNA BAMs (HG00xxx 1000 Genomes samples) with matched DNA VCFs grouped into `outrider`/`outrider_external`, `fraser`/`fraser_external`, and `mae` DROP groups, a `gene_annotation.yaml` pointing at a chr21 GTF, the `chr21.fa`/`chr21_ncbi.fa` FASTAs (plus `.fai`), a `hpo_genes.tsv.gz` HPO term file, a `genes_to_test.yaml` candidate list, and the `qc_vcf_1000G.vcf.gz` for DNA/RNA matching QC. Aberrant splicing uses external counts pulled from a tarball of pre-computed FRASER `k_j`/`k_theta`/`n_psi3`/`n_psi5`/`n_theta` matrices. Cutoffs are deliberately loosened (`ae_padj_cutoff=1`, `as_padj_cutoff=1`, `mae_padj_cutoff=0.5`) so every sample yields results on the tiny input. Expected outputs are: per-group OUTRIDER result TSVs (`OUTRIDER_results.tsv`, `OUTRIDER_results_all.Rds`) and HTML summaries, FRASER2 `results_per_junction.tsv` and gene-level `results.tsv` plus HTML, MAE `MAE_results_{annotation}.tsv(.gz)` and `_rare` subset, a DNA/RNA matching QC table, and a top-level MultiQC report aggregating all DROP groups.

## Reference workflow
nf-core/drop v1.0.0 (https://github.com/nf-core/drop), a Nextflow rewrite of the Gagneur lab DROP (Detection of RNA Outliers Pipeline) snakemake workflow. OUTRIDER and FRASER are CC-BY-NC 4.0 – commercial use requires a license from the Gagneur lab.
