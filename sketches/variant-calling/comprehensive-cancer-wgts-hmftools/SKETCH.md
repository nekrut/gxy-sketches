---
name: comprehensive-cancer-wgts-hmftools
description: "Use when you need an end-to-end somatic and germline analysis of human\
  \ tumor samples from WGS and/or WTS data \u2014 covering SNV/indel calling, SV calling,\
  \ copy number, HLA typing, HRD, tissue-of-origin, neoepitopes, and a consolidated\
  \ clinical-style report. Handles tumor-only, matched tumor/normal, and optional\
  \ donor setups from FASTQ, BAM, or CRAM, using the Hartwig WiGiTS toolchain."
domain: variant-calling
organism_class:
- vertebrate
- diploid
- human
input_data:
- short-reads-paired
- short-reads-rna
- bam
- cram
- reference-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/oncoanalyser
  url: https://github.com/nf-core/oncoanalyser
  version: 2.3.0
  license: MIT
  slug: oncoanalyser
tools:
- name: bwa-mem2
- name: star
- name: redux
- name: sage
- name: pave
- name: esvee
- name: amber
- name: cobalt
- name: purple
- name: linx
- name: isofox
- name: virusbreakend
- name: lilac
- name: cider
- name: chord
- name: sigs
- name: cuppa
- name: peach
- name: orange
tags:
- cancer
- somatic
- germline
- wgs
- wts
- tumor-normal
- hmftools
- wigits
- hrd
- neoepitope
- cuppa
- orange-report
- human
test_data: []
expected_output: []
---

# Comprehensive cancer WGTS with WiGiTS (oncoanalyser)

## When to use this sketch
- Human cancer samples sequenced by whole-genome sequencing (WGS), whole-transcriptome sequencing (WTS), or both (WGTS).
- Need an integrated somatic variant callset: SNV/MNV/indel, SV, CNV, purity/ploidy, driver events, fusions, HLA typing, HRD status, tissue-of-origin, oncoviral integration, telomere length, and a consolidated ORANGE PDF report.
- Matched tumor/normal, tumor-only, or tumor/normal/donor setups on GRCh37_hmf or GRCh38_hmf.
- Inputs may be FASTQ, BAM, CRAM, or pre-computed REDUX BAM/CRAM; starting from any intermediate WiGiTS stage is supported via samplesheet file types.
- Analysis must conform to the Hartwig Medical Foundation WiGiTS interpretation framework (e.g. ORANGE/CUPPA-based clinical-style reporting).

## Do not use when
- Sample is a targeted/panel assay (TSO500 or custom panel) — use a `targeted-panel-cancer-hmftools` sketch with `--mode targeted`.
- You only need tumor fraction / MRD estimation on a longitudinal ccfDNA sample — use a `ctdna-tumor-fraction-wisp` sketch with `--mode purity_estimate`.
- Non-human organism or non-cancer germline variant calling — use a generic germline/somatic caller sketch instead.
- Only staging reference data — use `prepare-reference-hmftools` (`--mode prepare_reference`).
- Building custom panel normalisation resources — use `panel-resource-creation-hmftools` (`--mode panel_resource_creation`).
- Long-read (ONT/PacBio) cancer analysis — oncoanalyser is short-read (Illumina) only.

## Analysis outline
1. (Optional) Stage reference data once with `--mode prepare_reference --ref_data_types wgs,wts,dna_alignment,rna_alignment` and point subsequent runs at it via a `-config` file.
2. DNA alignment with BWA-MEM2; RNA alignment with STAR (skipped when starting from BAM/CRAM).
3. DNA post-processing with REDUX (duplicate marking, UMI consensus, jitter/MS tables); RNA post-processing with Picard MarkDuplicates.
4. Small variant calling with SAGE (somatic + germline) and transcript/coding annotation with PAVE.
5. Structural variant calling with ESVEE (prep → assemble → depth annotate → filter to somatic/germline VCFs).
6. Copy number inputs: AMBER (BAFs) and COBALT (read-depth ratios); joint purity/ploidy fit and variant annotation with PURPLE.
7. SV event clustering, fusion calling, and driver interpretation with LINX (somatic + germline) plus LINX cluster plots and linxreport HTML.
8. RNA transcript quantification, alt-splice, and fusion calling with ISOFOX when RNA is present.
9. Oncoviral detection with VIRUSBreakend + VirusInterpreter; telomere characterisation with TEAL.
10. Immune analysis: LILAC (HLA class I typing + allelic status), CIDER (IG/TCR CDR3), NEO (neoepitope prediction using PURPLE/LILAC/ISOFOX outputs).
11. Mutational signature fitting with SIGS; HRD prediction with CHORD; tissue-of-origin prediction with CUPPA; pharmacogenomics with PEACH.
12. Summary reporting: ORANGE PDF/JSON integrating all WiGiTS outputs.

## Key parameters
- `--mode wgts` — selects the whole-genome/transcriptome workflow (vs `targeted`, `purity_estimate`, `prepare_reference`, `panel_resource_creation`).
- `--genome GRCh38_hmf` (or `GRCh37_hmf`) — Hartwig-curated human genome; custom genomes require `--force_genome` plus `--genome_version {37|38}` and `--genome_type {alt|no_alt}`.
- `--input samplesheet.csv` — columns `group_id,subject_id,sample_id,sample_type,sequence_type,filetype,[info,]filepath`; `sample_type ∈ {tumor,normal,donor}`, `sequence_type ∈ {dna,rna}`, `filetype ∈ {fastq,bam,bai,cram,crai,bam_redux,cram_redux,redux_jitter_tsv,redux_ms_tsv,...}`.
- `--outdir output/` — required output directory (absolute path on cloud storage).
- `-config reference_data.config` — strongly recommended to pin pre-staged `ref_data_hmf_data_path`, `genomes.<name>.{fasta,fai,dict,img,bwamem2_index,gridss_index,star_index}` to avoid re-downloading every run.
- `--max_fastq_records 10000000` (default) — fastp splits FASTQs to this chunk size before alignment; set to `0` to disable splitting.
- `--processes_exclude virusinterpreter,orange` / `--processes_manual alignment,redux,sage,amber,cobalt,esvee,pave,purple` — skip or hand-pick stages; it is the caller's responsibility to include prerequisites.
- UMI handling: `--fastp_umi_enabled`, `--fastp_umi_location`, `--fastp_umi_length`, `--fastp_umi_skip` (FASTQ side); `--redux_umi_enabled`, `--redux_umi_duplex_delim` (BAM side).
- `-profile docker|singularity|conda|test` — container/runtime backend; combine with institutional profiles as needed.
- `-revision 2.3.0` — pin pipeline version for reproducibility.

## Test data
The `test` profile runs a minimal WGTS FASTQ dataset (`fastq_eval.subject_a.wgts.tndna_trna.minimal.csv` from the oncoanalyser test-datasets repo), which contains a tumor DNA, normal DNA, and tumor RNA sample for a single subject against `GRCh38_hmf`, with `--max_fastq_records 0` to pass FASTQs through unsplit. Because the inputs are heavily downsampled, PURPLE is forced to a fixed fit (`-min_purity 1 -max_purity 1 -min_ploidy 2 -max_ploidy 2`) and resources are capped at 4 CPU / 30 GB / 1 h. A successful run produces a full per-`group_id` output tree (`alignments/`, `sage/`, `pave/`, `esvee/`, `amber/`, `cobalt/`, `purple/`, `linx/`, `isofox/`, `lilac/`, `chord/`, `cuppa/`, `peach/`, `orange/`, etc.) plus `pipeline_info/` — no local golden files are asserted; correctness is checked by the presence and structural validity of these outputs. A full-size equivalent (`full_size.hcc1395.wgts.tndna_trna.fastq.csv`) is available via the `test_full` profile.

## Reference workflow
nf-core/oncoanalyser v2.3.0 (https://github.com/nf-core/oncoanalyser), wrapping the Hartwig Medical Foundation WiGiTS toolchain (https://github.com/hartwigmedical/hmftools). DOI: 10.5281/zenodo.15189386.
