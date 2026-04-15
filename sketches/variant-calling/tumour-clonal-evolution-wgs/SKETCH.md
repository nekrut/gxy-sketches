---
name: tumour-clonal-evolution-wgs
description: 'Use when you have matched tumour-normal WGS with pre-computed somatic
  VCFs and allele-specific copy-number calls, and you need to reconstruct tumour evolution:
  annotate variants and drivers, QC the CNA calls, and perform subclonal and mutational-signature
  deconvolution (single-sample, multi-region, or longitudinal cohorts).'
domain: variant-calling
organism_class:
- human
- diploid
input_data:
- somatic-vcf
- allele-specific-cna
- tumour-normal-wgs
- reference-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/tumourevo
  url: https://github.com/nf-core/tumourevo
  version: dev
  license: MIT
  slug: tumourevo
tools:
- name: ensembl-vep
- name: cnaqc
  version: 1.1.3
- name: tinc
  version: 0.1.0
- name: pyclone-vi
  version: 0.1.6
- name: mobster
- name: viber
- name: ctree
- name: sparsesignatures
  version: a995bb98b7122825523ffed7ae131cb006e56cbe-0
- name: sigprofiler
- name: bcftools
tags:
- cancer
- wgs
- tumour-evolution
- subclonal-deconvolution
- mutational-signatures
- driver-annotation
- copy-number-qc
- clone-tree
- multi-region
test_data: []
expected_output: []
---

# Tumour clonal evolution from WGS (downstream of variant and CNA calling)

## When to use this sketch
- You already have somatic variant calls (VCF from Mutect2, Strelka, or Platypus) and allele-specific copy-number calls (from ASCAT, Sequenza, or Battenberg) for human tumour-normal WGS, and want downstream evolutionary analysis.
- You need any of: VEP annotation, driver-gene annotation against IntOGen/Compendium Cancer Genes, CNAqc-based QC of copy-number segments, TINC tumour-in-normal contamination assessment, subclonal deconvolution (PyClone-VI, MOBSTER, VIBER), clone-tree inference (ctree), or mutational-signature extraction (SparseSignatures, SigProfiler).
- Cohort may be single-sample, multi-region, or longitudinal; multiple samples from the same patient are automatically analysed jointly for subclonal deconvolution.
- Sample sheet groups samples by `dataset`, `patient`, `tumour_sample`, `normal_sample`, pointing at VCF+TBI and CNA segments/purity-ploidy files.

## Do not use when
- You still need to *call* somatic SNVs/indels from BAM/CRAM — use an upstream somatic variant-calling workflow (e.g. nf-core/sarek) first.
- You still need to *call* allele-specific copy number — run ASCAT/Sequenza/Battenberg first (e.g. via nf-core/sarek).
- You are working on bacterial, viral, or non-cancer germline variants — pick a haploid or germline variant-calling sketch instead.
- You want bulk RNA-seq expression-based clonality or scRNA-based clone inference — this pipeline is DNA/WGS only.
- You only need signature deconvolution on an existing mutation matrix without VCF/CNA inputs — use SigProfiler/SparseSignatures standalone.

## Analysis outline
1. Parse samplesheet and stage per-sample VCF+TBI, CNA segment file, and CNA purity/ploidy file per `dataset/patient/tumour_sample`.
2. Annotate variants with Ensembl VEP (offline cache; GRCh37 or GRCh38).
3. Annotate putative drivers against a cancer-gene compendium using the per-sample `cancer_type` (e.g. `PANCANCER`).
4. Standardise inputs via formatter subworkflow: `vcf2cnaqc` (VCF→RDS), `cna2cnaqc` (segments+purity→RDS).
5. (Optional) If variant calling was per-sample and tumour BAM/CRAM is provided, run the Lifter subworkflow: `get_positions` → `bcftools mpileup` → merge private/shared mutations across same-patient samples.
6. Run TINC to estimate tumour-in-normal (TIN) and tumour-in-tumour (TIT, ≈purity) contamination per sample.
7. Run CNAqc per sample to QC clonal simple CNAs (peak analysis) and compute CCFs; flag pass/fail per karyotype.
8. Join per-patient CNAqc objects into a multi-sample `mCNAqc` object with common segmentation (`join_cnaqc`); optionally filter to QC-passing segments only (`--filter`).
9. Export joint mutation/CN table as TSV (`cnaqc2tsv`) for python-based tools.
10. Subclonal deconvolution (tools selectable via `--tools`): MOBSTER (per-sample, neutral-tail model), PyClone-VI (per-patient, Bayesian clustering over CCFs), VIBER (per-patient, variational Binomial mixture).
11. Clone-tree inference with ctree from MOBSTER/VIBER/PyClone-VI fits (requires annotated drivers).
12. Mutational-signature deconvolution per dataset with SparseSignatures (NMF-LASSO) and/or SigProfiler (SBS96/DBS78/ID83 contexts).

## Key parameters
- `--input`: CSV samplesheet with columns `dataset,patient,tumour_sample,normal_sample,vcf,tbi,cna_segments,cna_extra,cna_caller,cancer_type` (+ optional `tumour_alignment`, `tumour_alignment_index`).
- `--genome`: `GRCh38` (default) or `GRCh37`; `--fasta`: reference FASTA path.
- `--tools`: comma-separated subset of `mobster,viber,pyclone-vi,sparsesignatures,sigprofiler` (default runs all five).
- `--filter`: when `true`, drop QC-failing segments from the joint mCNAqc object before deconvolution.
- VEP: `--vep_cache`, `--vep_cache_version` (e.g. `110`), `--vep_genome`, `--vep_species` (`homo_sapiens`), `--download_cache_vep`.
- Driver annotation: `--drivers_table` (default Compendium Cancer Genes TSV from nf-core test-datasets).
- CNAqc: `cnaqc_karyotypes` (default `c("1:0","1:1","2:0","2:1","2:2")`), `cnaqc_method` (`ENTROPY`/`ROUGH`), `cnaqc_muts_per_karyotype=25`, `cnaqc_purity_error=0.05`, `cnaqc_matching_strategy=rightmost`, `cnaqc_cutoff_qc_pass=0.1`.
- PyClone-VI: `pyclonevi_density` (`beta-binomial`), `pyclonevi_n_restarts=100`, `pyclonevi_n_grid_point=100`, `pyclonevi_n_cluster=20`.
- MOBSTER: `mobster_k="1:5"`, `mobster_tail=TRUE`, `mobster_pi_cutoff=0.02`, `mobster_min_vaf=0.05`, `mobster_n_cutoff=10`.
- VIBER: `viber_k=10`, `viber_samples=10`, `viber_max_iter=5000`, `viber_alpha_0=1e-6`, `viber_pi_cutoff=0.02`.
- SparseSignatures: `sparsesignatures_K="3:10"`, `sparsesignatures_nmf_runs=10`, `sparsesignatures_cross_validation_repetitions=50`, `sparsesignatures_lambda_values_beta="c(0.01,0.05,0.1,0.2)"`.
- SigProfiler: `sigprofiler_context_type="96,DINUC,ID"`, `sigprofiler_minimum_signatures=1`, `sigprofiler_maximum_signatures=25`, `sigprofiler_nmf_replicates=100`, `download_sigprofiler_genome=true` or provide `genome_installed_path`.
- TINC: `tinc_normal_contamination_lv=3`.

## Test data
The `test` profile uses a minimal human samplesheet hosted on the nf-core `tumourevo` test-datasets branch, with VCFs and CNA segment/purity files subsetted to chromosome 17 against a `chr17_genome.fasta` reference. It runs with GRCh38, a pre-packaged VEP cache tarball (`vep.tar.gz`, cache version 110, `Homo_sapiens`), and the Compendium Cancer Genes driver table. Only `pyclone-vi` and `sparsesignatures` are exercised (`--tools pyclone-vi,sparsesignatures`), with reduced parameters (`pyclonevi_n_restarts=50`, `sparsesignatures_K="2:3"`, `sparsesignatures_iterations=5`, short LASSO/CV settings) so the run finishes on 4 CPUs / 15 GB / 1 h. Expected outputs include annotated VCFs under `variant_annotation/vep/`, driver-annotated RDS under `driver_annotation/annotate_driver/`, CNAqc per-sample and `join_cnaqc` per-patient RDS objects, a `pyclonevi` best-fit TSV and cluster table per patient, and SparseSignatures NMF-LASSO output + exposure plots per dataset.

## Reference workflow
nf-core/tumourevo (dev), https://github.com/nf-core/tumourevo — downstream tumour-evolution pipeline integrating VEP, CNAqc, TINC, PyClone-VI, MOBSTER, VIBER, ctree, SparseSignatures, and SigProfiler.
