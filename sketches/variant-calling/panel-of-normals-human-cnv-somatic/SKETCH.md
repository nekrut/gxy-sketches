---
name: panel-of-normals-human-cnv-somatic
description: Use when you need to build reference artifacts (panels of normals, ploidy
  and CNV models) from a cohort of aligned human normal samples for downstream CNV
  and somatic variant calling with CNVkit, GATK gCNV, GENS, or Mutect2. Use this before
  running case-mode tumor analyses that require a matched PoN.
domain: variant-calling
organism_class:
- vertebrate
- diploid
- human
input_data:
- bam
- cram
- reference-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/createpanelrefs
  url: https://github.com/nf-core/createpanelrefs
  version: dev
  license: MIT
  slug: createpanelrefs
tools:
- name: cnvkit
- name: gatk4
- name: germlinecnvcaller
- name: gens
- name: mutect2
- name: fastqc
- name: multiqc
tags:
- panel-of-normals
- pon
- cnv
- copy-number
- somatic
- gatk
- cnvkit
- mutect2
- gens
- reference-building
test_data: []
expected_output: []
---

# Human panel-of-normals and CNV reference builder

## When to use this sketch
- You have a cohort of aligned human normal samples (BAM and/or CRAM) and want to generate reference artifacts to support downstream CNV/somatic calling in case mode.
- You need one or more of: a CNVkit reference `.cnn`, a GATK germline CNV caller (gCNV) ploidy + shard model, a GENS read-count panel of normals, or a GATK Mutect2 panel-of-normals VCF.
- You are working against a supported human reference (e.g. `GATK.GRCh38`, `GRCh37`, or an iGenomes key) and can provide / let the pipeline fetch the FASTA, `.fai`, and `.dict`.
- You want a single orchestrated run that QCs inputs (FastQC) and emits a MultiQC summary alongside the reference outputs.

## Do not use when
- You are actually calling variants in tumor/case samples — this pipeline only builds references; use a somatic or germline caller pipeline (e.g. nf-core/sarek) in case mode with the PoN produced here.
- Your organism is non-human or haploid/bacterial — see `haploid-variant-calling-bacterial` or other organism-specific sketches.
- You only need raw read QC — use a dedicated QC sketch.
- You want to build a PoN from raw FASTQ without prior alignment — align first (e.g. with sarek/bwa) then feed BAMs/CRAMs here.
- You need SV panels from long-read structural variant callers other than GENS `lrs` mode.

## Analysis outline
1. Parse samplesheet CSV (`sample,bam,bai,cram,crai`) and auto-detect BAM vs CRAM per row.
2. Run FastQC on inputs for basic read/alignment QC.
3. Stage or build reference helpers (`.fai` via samtools faidx, `.dict` via GATK CreateSequenceDictionary) unless supplied.
4. For `cnvkit`: run CNVkit batch in reference-building mode on BAM inputs to emit target/antitarget coverages and a cohort `.cnn` reference (whole-genome method by default; override to hybrid for exomes/panels).
5. For `germlinecnvcaller`: PreprocessIntervals → AnnotateIntervals (optionally with mappability / segmental duplications) → FilterIntervals → CollectReadCounts → DetermineGermlineContigPloidy (with `gcnv_ploidy_priors`) → IntervalListTools scatter → GermlineCNVCaller per shard, producing cohort ploidy and CNV models.
6. For `gens`: PreprocessIntervals (bin length 100 by default) → CollectReadCounts (or mosdepth coverage if `lrs`) → CreateReadCountPanelOfNormals to emit an HDF5 PoN.
7. For `mutect2`: Mutect2 per-normal in PoN mode → GenomicsDBImport across the cohort → CreateSomaticPanelOfNormals to emit the final PoN VCF.
8. Aggregate tool logs and FastQC into a MultiQC HTML report in `<outdir>/multiqc/`.

## Key parameters
- `--input`: CSV with columns `sample,bam,bai,cram,crai`; CNVkit requires BAM, gCNV accepts BAM or CRAM.
- `--tools`: comma list from `cnvkit,germlinecnvcaller,gens,mutect2` (at least one required).
- `--genome` or `--fasta` (+ optional `--fai`, `--dict`): reference genome; iGenomes keys like `GATK.GRCh38` resolve bundled files.
- CNVkit: `--cnvkit_targets` (optional BED); override `CNVKIT_BATCH` `ext.args` to switch from WGS to hybrid capture for exome/panel cohorts.
- gCNV: `--gcnv_analysis_type` (`wgs` default, `wes`), `--gcnv_bin_length` (1000 for WGS, 0 for WES), `--gcnv_padding` (0 WGS / 250 WES), `--gcnv_ploidy_priors` (mandatory), optional `--gcnv_target_bed`/`--gcnv_target_interval_list`, `--gcnv_exclude_bed`/`--gcnv_exclude_interval_list`, `--gcnv_mappable_regions`, `--gcnv_segmental_duplications`, `--gcnv_scatter_content` (default 5000), `--gcnv_model_name`.
- GENS: `--gens_analysis_type` (`srs` default / `lrs`), `--gens_bin_length` (default 100), `--gens_min_interval_median_percentile` (default 5), `--gens_readcount_format` (`HDF5`/`TSV`), `--gens_pon_name`, optional `--gens_interval_list`.
- Mutect2: optional `--mutect2_target_bed`, `--mutect2_pon_name`.
- Execution: `-profile docker|singularity|conda|...`, `--outdir`.

## Test data
The bundled `test` profile points at `tests/csv/1.0.0/bam.csv` from the pipeline repo and a small `GRCh38.chr21.testdata` iGenomes reference hosted under `nf-core/test-datasets/modules/data`, running only `--tools cnvkit` with `gcnv_scatter_content=2` so it completes in minutes on a laptop-sized runner (4 CPU / 15 GB / 1 h resource cap). A successful run produces a CNVkit panel `.cnn`, per-sample `*.targetcoverage.cnn` / `*.antitargetcoverage.cnn` under `results/reference/cnvkit/`, FastQC reports, and a MultiQC HTML summary. The `test_full` profile exercises all four tools (`cnvkit,germlinecnvcaller,gens,mutect2`) against a Sarek-recalibrated CRAM cohort on `GATK.GRCh38` and additionally emits gCNV ploidy/shard models, a GENS HDF5 PoN, and a Mutect2 PoN VCF under `results/`.

## Reference workflow
nf-core/createpanelrefs (dev, template 3.5.1) — https://github.com/nf-core/createpanelrefs. Originally by @maxulysse; wraps CNVkit, GATK4 (gCNV, CollectReadCounts, Mutect2, CreateSomaticPanelOfNormals), GENS tooling, FastQC and MultiQC.
