---
name: de-novo-transcriptome-assembly-bulk-rnaseq
description: Use when you need to build a de novo transcriptome assembly from paired-end
  bulk RNA-seq short reads for a non-model organism that lacks a reference genome.
  Produces a non-redundant transcriptome FASTA, a transcript-to-gene map, quality
  metrics (BUSCO, rnaQUAST, TransRate) and per-sample Salmon transcript-level quantification.
domain: rna-seq
organism_class:
- eukaryote
- non-model
input_data:
- short-reads-paired
source:
  ecosystem: nf-core
  workflow: nf-core/denovotranscript
  url: https://github.com/nf-core/denovotranscript
  version: 1.2.1
  license: MIT
tools:
- fastqc
- fastp
- sortmerna
- trinity
- rnaspades
- evidentialgene-tr2aacds
- busco
- rnaquast
- transrate
- salmon
- multiqc
tags:
- de-novo
- transcriptome
- assembly
- bulk-rnaseq
- non-model
- trinity
- rnaspades
- evigene
- busco
- salmon
test_data: []
expected_output: []
---

# De novo transcriptome assembly from bulk RNA-seq

## When to use this sketch
- You have paired-end Illumina bulk RNA-seq FASTQs and want a transcriptome assembled without a reference genome.
- The organism is non-model (no usable reference transcriptome/genome), e.g. invertebrates, plants, or any eukaryote where you need to build the transcript set yourself.
- You want a consensus assembly built from multiple assemblers (Trinity + rnaSPAdes) with redundancy reduction via EvidentialGene tr2aacds.
- You want both an assembly quality report (BUSCO, rnaQUAST, optional TransRate) and per-sample transcript-level quantification (Salmon) in a single run.
- You have an existing transcriptome FASTA and only want to re-run QC + Salmon quantification against it (use `--skip_assembly` with `--transcript_fasta`).

## Do not use when
- A well-curated reference genome/transcriptome already exists for the organism — use a reference-based bulk RNA-seq sketch (`nf-core/rnaseq`-style STAR/Salmon alignment + quantification) instead.
- Input data is single-cell (10x, Smart-seq) — use a single-cell RNA-seq sketch.
- Input data is long reads (PacBio Iso-Seq, ONT cDNA/direct-RNA) — use a long-read isoform sketch, not this short-read pipeline.
- You only need differential expression from an existing count matrix — run a downstream DESeq2/edgeR-style sketch.
- Target is a bacterial or viral genome assembly from DNA-seq — use a genome assembly sketch.

## Analysis outline
1. Raw read QC with FastQC.
2. Adapter and quality trimming with fastp; re-run FastQC on trimmed reads.
3. Optional rRNA/mtRNA depletion with SortMeRNA (`--remove_ribo_rna`); FastQC again on cleaned reads.
4. Pool trimmed reads across all samples into single R1/R2 files (cat) for joint assembly.
5. De novo assembly with any combination of Trinity (normalized, default), Trinity without normalization, and rnaSPAdes (medium/soft/hard filtered); concatenate all assembler outputs.
6. Redundancy reduction with EvidentialGene `tr2aacds.pl` to produce the final non-redundant `okay.mrna` transcriptome; derive a `tx2gene.tsv` from `okayset/*.pubids` via gawk.
7. Assess assembly completeness with BUSCO (lineage auto or user-specified).
8. Compute assembly metrics (N50, lengths, optional reference comparisons) with rnaQUAST.
9. Reference-free contig/read-mapping scores with TransRate (skipped under conda/mamba profiles).
10. Per-sample pseudo-alignment and transcript-level quantification with Salmon against the final assembly.
11. Aggregate FastQC, fastp, SortMeRNA, BUSCO, and Salmon into a MultiQC HTML report.

## Key parameters
- `input`: CSV samplesheet with columns `sample,fastq_1,fastq_2`; rows sharing a `sample` value are concatenated across lanes/runs.
- `outdir`: results directory (absolute path on cloud storage).
- `assemblers`: comma-separated subset of `trinity,trinity_no_norm,rnaspades` (default `trinity,rnaspades`).
- `extra_trinity_args`, `extra_tr2aacds_args`, `extra_fastp_args`: pass-through tool arguments (e.g. `--trim_front1 15 --trim_front2 15` for fastp).
- `soft_filtered_transcripts` / `hard_filtered_transcripts`: include additional rnaSPAdes filter tiers as EvidentialGene input.
- `ss`: rnaSPAdes strand-specific mode, `rf` or `fr`; leave unset for standard unstranded FR libraries.
- `remove_ribo_rna` (+ `ribo_database_manifest`, `save_non_ribo_reads`): enable SortMeRNA rRNA depletion.
- `busco_mode` (default `transcriptome`), `busco_lineage` (default `auto`, or e.g. `arthropoda_odb10`), `busco_lineages_path`, `busco_config`.
- `fasta`, `gtf`: optional reference genome + annotation to enrich rnaQUAST metrics.
- `transrate_reference`: optional related-species protein/transcript FASTA for TransRate comparative metrics (requires a container profile, not conda).
- `lib_type`: Salmon library type, default `A` (auto-infer).
- `qc_only`: run only QC steps; `skip_assembly` + `transcript_fasta`: skip assembly and quantify against a provided transcriptome FASTA.
- `skip_fastp`, `skip_fastqc`, `save_trimmed_fail`, `save_merged`, `adapter_fasta`: finer QC controls.

## Test data
The pipeline ships a minimal `test` profile that pulls a small paired-end samplesheet and a pre-assembled `assembled_mrna_2k.fa` transcriptome from the `nf-core/test-datasets` `denovotranscript` branch, along with a `Panulirus_ornatus_pep.fa` TransRate reference and the `arthropoda_odb10` BUSCO lineage; fastp is invoked with `--trim_front1 15 --trim_front2 15`. A `test_full` profile uses a larger samplesheet and `assembled_mrna_80k.fa` under 20 CPUs / 200 GB / 20 h limits. Expected outputs under `<outdir>/` include FastQC reports (`fastqc/raw|trim|final`), `fastp/` trimmed FASTQs and reports, an `evigene/okayset/*.okay.mrna` final transcriptome FASTA plus `tx2gene/*tx2gene.tsv`, Trinity and rnaSPAdes intermediate assemblies, `busco/short_summary*.{txt,json}`, `rnaquast/short_report.{txt,tsv,pdf}` with `basic_metrics.txt`, a `transrate/` directory with `assemblies.csv`, per-sample `salmon/<SAMPLE>/quant.sf`, and a top-level `multiqc/multiqc_report.html`.

## Reference workflow
nf-core/denovotranscript v1.2.1 (https://github.com/nf-core/denovotranscript, DOI 10.5281/zenodo.13324371, MIT).
