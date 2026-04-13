---
name: long-read-methylation-calling
description: Use when you need to extract 5mC/5hmC (or m6A) DNA methylation calls
  from long-read sequencing data (Oxford Nanopore pod5/modBAM or PacBio HiFi modBAM),
  align to a reference genome, and produce bedMethyl/bedgraph tracks. Optionally extends
  to SNV calling, haplotype phasing, and differential methylation region (DMR) analysis
  at haplotype or population scale.
domain: epigenomics
organism_class:
- eukaryote
- vertebrate
- plant
input_data:
- long-reads-ont-pod5
- long-reads-ont-modbam
- long-reads-pacbio-hifi-modbam
- reference-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/methylong
  url: https://github.com/nf-core/methylong
  version: 2.0.0
  license: MIT
tools:
- dorado
- jasmine
- ccsmeth
- minimap2
- pbmm2
- samtools
- porechop
- modkit
- pb-CpG-tools
- clair3
- whatshap
- dss
- fibertools-rs
- fastqc
- multiqc
tags:
- methylation
- 5mC
- 5hmC
- m6A
- long-read
- nanopore
- pacbio
- bedmethyl
- dmr
- fiberseq
- phasing
test_data: []
expected_output: []
---

# Long-read DNA methylation calling (ONT and PacBio HiFi)

## When to use this sketch
- You have long-read sequencing data with modification information and want per-site 5mC/5hmC methylation calls against a reference genome.
- Inputs are any of: ONT pod5 (needs basecalling), ONT unaligned modBAM with MM/ML tags, ONT raw BAM, or PacBio HiFi (un)aligned BAM — optionally needing modcalling.
- You want bedMethyl / bedgraph tracks ready for downstream epigenomic analysis.
- You optionally need SNV calls, read-based haplotype phasing, and DMR analysis (haplotype-level or population-scale between two sample groups).
- You want Fiber-seq style m6A + nucleosome inference from long reads.
- The reference is any organism with a FASTA assembly (bacterial, plant, or vertebrate) — the pipeline is organism-agnostic as long as long reads are available.

## Do not use when
- You have short-read bisulfite or EM-seq data — use a short-read WGBS/methylation sketch instead.
- You only need variant calling from long reads without methylation — use a long-read variant-calling sketch (e.g. clair3/DeepVariant-based).
- You need de novo assembly of a genome from long reads — use a long-read assembly sketch.
- You want per-read modification basecalling only, with no pileup/alignment — run `dorado` directly.
- Your methylation target is RNA modifications — this pipeline is DNA-only.

## Analysis outline
1. Ingest samplesheet (`group,sample,path,ref,method`) and auto-detect pod5 vs BAM input.
2. QC raw reads with `fastqc`.
3. (ONT) Optional basecalling of pod5 → modBAM with `dorado basecaller` (default model `sup`, mods `5mC_5hmC`).
4. (PacBio) Optional modcalling of unmodified HiFi BAM with `jasmine` (default) or `ccsmeth` (using bundled 5mCpG models).
5. (ONT only) Preprocess modBAM: `samtools sort` → `samtools fastq` → `porechop` adapter/barcode trim → `samtools import` → `modkit repair` to restore MM/ML tags. Skippable with `--no_trim`; use `--reset` (`samtools reset`) first if input was previously aligned.
6. Align to reference: ONT with `dorado aligner` (default) or `minimap2 -x lr:hq`; PacBio with `pbmm2` (default) or `minimap2 -x map-hifi`. Sort, index, and `samtools flagstat`.
7. Methylation pileup (≥5× coverage): ONT via `modkit pileup`; PacBio via `pb-CpG-tools` (default, model or count mode) or `modkit pileup`. Optional `--bedgraph` conversion and `--all_contexts` / `--denovo` toggles.
8. (Optional) SNV calling per sample with `clair3`, filtered to `SNV_PASS.vcf`.
9. (Optional) Read-based phasing with `whatshap phase` and `whatshap haplotag`.
10. (Optional) Haplotype-level DMRs: re-pileup per HP tag with `modkit pileup`, then call DMRs with `DSS` (default) or `modkit dmr pair`.
11. (Optional) Population-scale DMRs between `--dmr_a` and `--dmr_b` groups with `DSS` or `modkit dmr`.
12. (Optional) Fiber-seq: ONT path `modkit call-mods` → `ft add-nucleosomes` → `ft extract`; PacBio path `ft predict-m6a` → `ft extract`.
13. Aggregate QC and flagstats with `multiqc`.

## Key parameters
- `--input` / `--outdir` — samplesheet CSV (`group,sample,path,ref,method`) and results directory (required).
- `--ont_aligner` — `dorado` (default) or `minimap2`.
- `--pacbio_aligner` — `pbmm2` (default) or `minimap2`.
- `--dorado_model` — e.g. `sup` (default); change to match the ONT chemistry/kit.
- `--dorado_modification` — e.g. `5mC_5hmC` (default), or `5mCG_5hmCG 6mA` for fiber-seq.
- `--pacbio_modcall` — run modcalling on unmodified HiFi BAM input.
- `--pacbio_modcaller` — `jasmine` (default) or `ccsmeth` (uses `ccsmeth_cm_model` / `ccsmeth_ag_model`).
- `--reset` — strip prior alignments before re-aligning (needed for previously-aligned modBAM input).
- `--no_trim` — skip ONT porechop/repair preprocessing.
- `--pileup_method` — `pbcpgtools` (default, PacBio) or `modkit`.
- `--pileup_count` — switch pb-CpG-tools from `model` to `count` mode.
- `--denovo` — pb-CpG-tools reference-free CG site discovery.
- `--bedgraph` — emit per-context bedgraphs (min 5× coverage).
- `--all_contexts` — pileup CpG + CHG + CHH (plant-style).
- `--m6a` / `--fiberseq` — enable m6A motif pileup and Fiber-seq subworkflow.
- `--skip_snvs` — disable clair3 + whatshap and the haplotype DMR branch.
- `--haplotype_dmrer`, `--population_dmrer` — `dss` (default) or `modkit`.
- `--dmr_population_scale`, `--dmr_a`, `--dmr_b` — enable and define the two groups for population DMR contrasts.

## Test data
The `test` profile pulls a small samplesheet from `nf-core/test-datasets` (branch `methylong/v2.0.0`, `test_data/test_samplesheet.csv`), containing a minimal mix of ONT (and/or PacBio) modBAM samples with an accompanying reference FASTA, and forces `ont_aligner = minimap2` to stay inside a 4-CPU / 15 GB / 1 h resource envelope. Running `-profile test` exercises alignment, `modkit` pileup, and MultiQC, producing per-sample `alignment/*.bam`, `pileup/*.bed.gz`, flagstat summaries, and a consolidated `multiqc/multiqc_report.html`. The `test_full` profile runs the same structure on a larger public dataset with `bedgraph=true`, `no_trim=true`, `pacbio_aligner=pbmm2`, `pileup_method=pbcpgtools`, and `reset=true` to cover the PacBio + pb-CpG-tools branch end-to-end.

## Reference workflow
nf-core/methylong v2.0.0 — https://github.com/nf-core/methylong (MIT). See `docs/usage.md`, `docs/output.md`, and `nextflow_schema.json` for the authoritative parameter list; DOI 10.5281/zenodo.15366449.
