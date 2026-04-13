---
name: sars-cov-2-artic-ont-variant-calling
description: Use when you need to call and annotate SARS-CoV-2 variants from Oxford
  Nanopore reads generated with the ARTIC amplicon tiling protocol. Maps reads to
  NC_045512.2 with minimap2 (map-ont), trims ARTIC primers with ivar, and calls variants
  with medaka, then annotates with SnpEff. Does not attempt to rescue amplicons affected
  by primer-binding-site mutations.
domain: variant-calling
organism_class:
- viral
- haploid
input_data:
- long-reads-ont
- reference-fasta
- primer-bed
source:
  ecosystem: iwc
  workflow: 'COVID-19: variation analysis of ARTIC ONT data'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/sars-cov-2-variant-calling/sars-cov-2-ont-artic-variant-calling
  version: 0.3.2
  license: MIT
tools:
- fastp
- minimap2
- samtools
- ivar
- medaka
- bcftools
- bedtools
- snpeff
- lofreq
- qualimap
- multiqc
tags:
- sars-cov-2
- covid-19
- artic
- ont
- nanopore
- amplicon
- viral
- variant-calling
test_data:
- role: nc_045512_2_fasta_sequence_of_sars_cov_2
  url: https://zenodo.org/record/4555735/files/NC_045512.2_reference.fasta?download=1
  sha1: db3759c2e1d9ce8827ba4aa1749e759313591240
- role: primer_binding_sites_info_in_bed_format
  url: https://zenodo.org/record/4555735/files/ARTIC_nCoV-2019_v3.bed?download=1
  sha1: d0864546dca524fc5cd057f48ee7f5671faba83a
- role: ont_sequenced_reads__srr12447380
  url: https://www.be-md.ncbi.nlm.nih.gov/Traces/sra-reads-be/fastq?acc=SRR12447380
  sha1: e26a9711e1d1201ed49cd3e98bbc0837f4c90533
  filetype: fastqsanger.gz
expected_output: []
---

# SARS-CoV-2 ARTIC ONT variant calling

## When to use this sketch
- Input is Oxford Nanopore (ONT) sequencing of SARS-CoV-2 libraries prepared with the ARTIC amplicon tiling protocol (e.g. ARTIC nCoV-2019 v3).
- You have per-sample ONT FASTQ files (fastqsanger/fastqsanger.gz), the Wuhan-Hu-1 reference (NC_045512.2) and a BED file of ARTIC primer coordinates.
- You want an annotated VCF of SNVs/indels vs NC_045512.2 plus QC reports, suitable for lineage/clade assignment and submission workflows.
- You are comfortable with a haploid/consensus variant model that deliberately ignores amplicons whose primer-binding sites may carry mutations (ONT error rates make rescue unreliable).

## Do not use when
- Reads are Illumina paired-end ARTIC data — use the sibling `sars-cov-2-artic-illumina-pe-variant-calling` sketch, which uses lofreq and handles primer-binding-site variants.
- Reads are Illumina from non-amplicon (WGS/metatranscriptomic) SARS-CoV-2 libraries — use a sibling `sars-cov-2-wgs-variant-calling` sketch without ivar primer trimming.
- The organism is not SARS-CoV-2 — SnpEff database, reference, and primer scheme are hard-wired to NC_045512.2 / ARTIC.
- You need consensus FASTA generation or pangolin/nextclade lineage assignment as part of the run — that is handled by downstream consensus/reporting workflows.
- You need diploid or somatic variant calling — this is a haploid viral caller.

## Analysis outline
1. Length-filter raw ONT reads per sample with **fastp** (quality filtering disabled, poly-G trimming enabled; keeps reads between the configured min/max length).
2. Map filtered reads to NC_045512.2 with **minimap2** in `map-ont` preset, emitting BAM.
3. Filter the BAM with **samtools view** to retain primary, mapped alignments (MAPQ ≥ 1, excluding flags 4 and 256).
4. Left-align indels with **BamLeftAlign** (freebayes) against the reference.
5. Trim ARTIC primers from the left-aligned BAM with **ivar trim** using the primer BED (keeps reads ≥1 bp post-trim).
6. Run **QualiMap BamQC** and **samtools stats** on the trimmed BAM and aggregate with **MultiQC**.
7. Build pileup features with **medaka consensus** (model `r941_min_high_g351`) on the trimmed/realigned BAM.
8. Call variants twice with **medaka variant** against NC_045512.2: once with default padding (`pad=25`) for general calls, and once with padding equal to the maximum primer length (derived from the primer BED via Compute/Datamash/param_value_from_file) to recover calls inside primer binding sites.
9. Intersect the primer-binding-site call set with primer intervals using **bedtools intersect** to keep only variants that fall inside primer regions, then merge them into the general call set with **bcftools annotate**.
10. Annotate the combined VCF with **SnpEff** (`NC_045512.2` / `4.5covid19` database) and apply a strand-bias soft filter with **lofreq filter** (FDR α=0.001), fixing the header so it remains a valid per-sample VCF.

## Key parameters
- fastp: `disable_quality_filtering=true`, `length_required` (default 400), `length_limit` (default 700), `polyG` trimming on.
- minimap2: `analysis_type_selector=map-ont`, output BAM, no end filtering.
- samtools view: `quality=1`, `exclusive_filter=[4,256]`, keep retained reads as BAM.
- BamLeftAlign: `iterations=5`.
- ivar trim: `min_len=1`, `min_qual=0`, `window_width=4`, `primer_pos_wiggle=0`, `inc_primers=false`.
- medaka consensus: `model=r941_min_high_g351`, `chunk_len=800`, `chunk_ovlp=400`, `batch_size=100` (switch model for other flowcell/basecaller combinations — e.g. r9.4.1 vs r10, guppy version).
- medaka variant (general): `pad=25`, `pool_mode=No`, annotate with input BAM.
- medaka variant (primer-binding sites): `pad = max(primer_length)` computed from the BED.
- SnpEff: `genome_version=NC_045512.2`, `annotations=[-formatEff,-classic]`, filter out downstream/intergenic/upstream.
- lofreq filter: strand-bias MTC=fdr, `sb_alpha=0.001`, `--print-all` (soft filter, no hard drops).
- Reference must be NC_045512.2; if the primer BED uses the MN908947.3 accession it is renamed to NC_045512.2 by the workflow before intersection.

## Test data
The source workflow ships a single-sample test profile: one ONT FASTQ collection element `SRR12447380` (fastqsanger.gz, streamed from NCBI SRA), the NC_045512.2 reference FASTA and the ARTIC nCoV-2019 v3 primer BED (both hosted on Zenodo record 4555735). A successful run produces an annotated, strand-bias soft-filtered VCF per sample; the test asserts that the `annotated_softfiltered_variants` output for `SRR12447380` matches `test-data/final_snpeff_annotated_variants.vcf` via line-diff comparison (tolerating up to 6 differing header lines). Intermediate outputs exercised include length-filtered reads, minimap2 BAM, primer-trimmed realigned BAM, medaka variant VCFs (general and primer-binding-site), and MultiQC preprocessing/mapping reports.

## Reference workflow
Galaxy IWC `sars-cov-2-variant-calling/sars-cov-2-ont-artic-variant-calling`, workflow `COVID-19: variation analysis of ARTIC ONT data`, release 0.3.2 (MIT). Modeled after the ARTIC `minion` pipeline (https://artic.readthedocs.io/).
