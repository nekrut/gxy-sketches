---
name: viral-integration-detection-human
description: Use when you need to detect viral integration sites in human host short-read
  RNA-seq or DNA-seq data by identifying chimeric reads spanning host-virus junctions
  (e.g. HPV, HBV, EBV insertions in tumor samples). Maps reads against a combined
  human + viral reference and reports candidate insertion sites with evidence counts
  and IGV views.
domain: structural-variants
organism_class:
- vertebrate
- human
- diploid
input_data:
- short-reads-paired
- host-reference-fasta
- host-gtf
- viral-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/viralintegration
  url: https://github.com/nf-core/viralintegration
  version: 0.1.1
  license: MIT
  slug: viralintegration
tools:
- name: fastqc
  version: 0.11.9
- name: star
- name: trimmomatic
  version: '0.39'
- name: polyastripper
- name: samtools
- name: ctat-vif
- name: multiqc
  version: '1.14'
tags:
- viral-integration
- chimeric-reads
- hpv
- hbv
- ebv
- ctat-vif
- insertion-site
- cancer
test_data: []
expected_output: []
---

# Viral integration site detection in human samples

## When to use this sketch
- User wants to find sites where a viral genome has integrated into a human host genome (e.g. HPV16 in cervical cancer, HBV in hepatocellular carcinoma, EBV in lymphoma).
- Input is paired- or single-end Illumina short reads (RNA-seq or WGS) from human samples suspected of viral infection/integration.
- You need evidence-level output: chimeric read counts, candidate insertion coordinates on the human genome, gene annotation at the junction, and an interactive IGV view of supporting reads.
- A viral sequence database is available (default: CTAT-VIF human virus database) or the user supplies a FASTA of viruses of interest.

## Do not use when
- The goal is purely viral identification/quantification without locating host insertion sites — use a metagenomics or viral-profiling sketch.
- The host is not human / not in iGenomes — this pipeline is parameterized around human references (GRCh37/GRCh38).
- You want de novo viral assembly from environmental samples — use a viral assembly sketch.
- You need germline or somatic SNV/indel calling against a host reference — use a variant-calling sketch instead.
- Long-read (ONT/PacBio) data is the primary input — STAR-based chimeric detection here is short-read only.

## Analysis outline
1. Parse samplesheet CSV (`sample,fastq_1,fastq_2`), concatenating lanes per sample.
2. Raw read QC with FastQC.
3. Align reads to the human reference genome with STAR (index built from `--fasta` + `--gtf` or `--genome`).
4. Quality and adapter trim unaligned reads with Trimmomatic, then strip polyA tails with PolyAStripper.
5. Concatenate the human FASTA with the viral FASTA (`cat_fasta`) and build a combined STAR index.
6. Align the cleaned unmapped reads to the human+virus combined reference with STAR; sort and index with SAMtools.
7. Call `insertion_site_candidates` (CTAT-VIF) on the combined alignments and abridge the TSV of chimeric-evidence candidates.
8. Generate the Virus Report: per-sample viral read-count TSV/PNG, preliminary genome-wide abundance plot, and a `VirusDetect.igvjs.html` interactive viewer.
9. Extract chimeric genomic target FASTA/GTF around each candidate, realign reads with STAR, sort/index, and remove duplicate alignments.
10. Run `chimeric_contig_evidence_analyzer` to count split and spanning reads supporting each junction.
11. Emit refined insertion-site TSVs (`vif.refined.tsv`, `vif.refined.wRefGeneAnnots.tsv`, `vif.refined.distilled.tsv`), a refined genome-wide abundance plot, and `vif.html` IGV viewer.
12. Aggregate QC across FastQC/Trimmomatic/STAR stages with MultiQC.

## Key parameters
- `--input`: samplesheet.csv with columns `sample,fastq_1,fastq_2` (required). Re-used sample names are concatenated.
- `--viral_fasta`: FASTA of viral genomes to search for integration. Defaults to the Broad CTAT-VIF human virus database (`virus_db.fasta`). Override with e.g. HPV16-only FASTA for targeted studies.
- `--genome` / `--fasta` + `--gtf`: human reference. Typical choices `GRCh38` or `GRCh37` via iGenomes; or explicit FASTA + GTF paths.
- `--min_reads`: minimum chimeric read support to keep an insertion candidate. Default `5`, minimum `1`. Lower for low-coverage data, raise to reduce false positives.
- `--max_hits`: maximum multi-mapping hits per read considered. Default `50`.
- `--remove_duplicates`: default `true`. Set `false` only if duplicates carry biological signal (rare).
- `--outdir`: results directory (absolute path required on cloud).
- Profiles: `-profile docker|singularity|conda|<institute>`; resource caps via `--max_cpus`, `--max_memory`, `--max_time`.

## Test data
The built-in `test` profile (`conf/test.config`) runs against a tiny samplesheet shipped in `assets/samplesheet.csv`, using GRCh38 chromosome 18 (`GRCh38_chr18.fa` + matching GTF from `nf-core/test-datasets` branch `viralintegration`) as the host reference and the HPV16 FASTA (`HPV16.fa` from the CTAT-VirusIntegrationFinder repo) as the viral reference. It is capped at 2 CPUs / 6 GB / 6 h so it completes on GitHub Actions. Running with `-profile test,docker` is expected to produce FastQC reports, per-sample `*.VirusDetect.igvjs.html` with viral read-count plots, refined insertion-site tables (`*.vif.refined.tsv`, `*.vif.refined.wRefGeneAnnots.tsv`), a `*.vif.html` IGV viewer, and a MultiQC report summarizing QC across FastQC, Trimmomatic, and STAR stages.

## Reference workflow
nf-core/viralintegration v0.1.1 (https://github.com/nf-core/viralintegration), based on the Broad Institute CTAT-VirusIntegrationFinder (CTAT-VIF). DOI: 10.5281/zenodo.7783480.
