---
name: cutandrun-histone-profiling
description: Use when you need to profile protein-DNA interactions or histone modifications
  (e.g. H3K27me3, H3K4me3) from paired-end CUT&RUN, CUT&Tag, or TIPseq Illumina data,
  with spike-in normalisation against an E. coli (or other) reference and peak calling
  against matched IgG controls.
domain: epigenomics
organism_class:
- vertebrate
- eukaryote
input_data:
- short-reads-paired
- reference-fasta
- bowtie2-index
- gtf
- igg-control
source:
  ecosystem: nf-core
  workflow: nf-core/cutandrun
  url: https://github.com/nf-core/cutandrun
  version: 3.2.2
  license: MIT
  slug: cutandrun
tools:
- name: fastqc
  version: 0.12.1
- name: trim-galore
- name: bowtie2
- name: samtools
- name: picard
- name: bedtools
- name: deeptools
- name: seacr
- name: macs2
- name: preseq
- name: multiqc
tags:
- cut-and-run
- cut-and-tag
- tipseq
- histone
- chromatin
- peak-calling
- spike-in
- igg-control
- epigenomic-profiling
test_data: []
expected_output: []
---

# CUT&RUN / CUT&Tag histone & chromatin profiling

## When to use this sketch
- Paired-end Illumina CUT&RUN, CUT&Tag, or TIPseq libraries targeting histone marks (H3K27me3, H3K4me3, H3K9me3, etc.) or chromatin-associated factors.
- Experiments that include matched IgG (or other negative) controls to use as background for peak calling.
- Runs where you want E. coli (or S. cerevisiae / D. melanogaster) spike-in normalisation between samples.
- Vertebrate/eukaryotic targets where an iGenomes key (e.g. `GRCh38`, `GRCm38`) or custom FASTA + Bowtie2 index is available.
- Biological replicates per group, where you want consensus peaks and reproducibility / FRiP QC.

## Do not use when
- The data is single-end — this pipeline explicitly does not support single-end reads.
- You are doing bulk ATAC-seq (use an ATAC-seq sketch) or ChIP-seq with crosslinking and sonication (use a ChIP-seq sketch); CUT&RUN/Tag peak shapes and background models differ.
- You need bulk or single-cell RNA-seq quantification (use an rna-seq / single-cell sketch).
- You are calling SNVs/indels against a reference — this pipeline does no variant calling.
- Your assay is scCUT&Tag at the single-cell level; this pipeline treats libraries as bulk.

## Analysis outline
1. Validate samplesheet (`group, replicate, fastq_1, fastq_2, control`) and merge re-sequenced FASTQs with `cat`.
2. Pre-trim read QC with `FastQC`.
3. Adapter and quality trimming with `Trim Galore!` (Cutadapt), followed by post-trim FastQC.
4. Align paired reads to target genome and to spike-in genome with `Bowtie 2` in `--end-to-end` mode.
5. Quality filter, sort, and index alignments with `samtools`; optionally drop mitochondrial reads.
6. Mark/remove duplicates with `Picard MarkDuplicates` (controls by default; targets only if `--dedup_target_reads`); optionally remove linear-amplification (T7) duplicates for TIPseq via a custom read-1 5' start-site filter.
7. Estimate library complexity with `preseq`.
8. Compute spike-in scale factors and build coverage tracks: BAM → bedGraph (`bedtools genomecov`) → bigWig (`bedGraphToBigWig`) via `deepTools bamCoverage`, normalised by `Spikein`, `RPKM`, `CPM`, `BPM`, or `None`.
9. Call peaks with `SEACR` and/or `MACS2` against the IgG control (or top-fraction mode if no control).
10. Merge replicate peaks into consensus peaks with `bedtools merge`, applying a replicate threshold.
11. Fragment-based QC with `deepTools` (PCA, fingerprint, correlation) on binned BAM coverage.
12. Peak-based QC: peak counts, peak reproducibility (`bedtools intersect`), and FRiP score.
13. Generate gene- and peak-centred coverage heatmaps with `deepTools computeMatrix` / `plotHeatmap`.
14. Emit an IGV session (`igv_session.xml`) bundling bigWigs, peaks, FASTA and GTF.
15. Aggregate all QC into a `MultiQC` HTML report.

## Key parameters
- `input`: samplesheet CSV with columns `group,replicate,fastq_1,fastq_2,control`; the `control` field references another `group` (typically `igg_ctrl`).
- `genome`: iGenomes key (e.g. `GRCh38`, `GRCm38`) — or supply `fasta`, `bowtie2`, `gtf`, `gene_bed`, `blacklist` manually.
- `spikein_genome`: default `K12-MG1655` (E. coli); use `R64-1-1` for yeast spike-in, `BDGP6` for fly.
- `peakcaller`: `seacr`, `macs2`, or comma-separated (first is primary, e.g. `seacr,MACS2`).
- `use_control`: `true` to normalise peaks against IgG; `igg_scale_factor` (default `0.5`) scales the control track.
- `normalisation_mode`: one of `Spikein` (default), `RPKM`, `CPM`, `BPM`, `None`; `normalisation_c` default `10000`.
- `minimum_alignment_q_score`: default `20`; `remove_mitochondrial_reads` + `mito_name` (e.g. `chrM`) to drop mtDNA.
- `end_to_end`: `true` (Bowtie2 end-to-end alignment).
- `dedup_target_reads`: default `false` (dedup only on controls); set `true` if PCR duplication is suspected in targets.
- `remove_linear_duplicates`: `true` for TIPseq to strip T7 linear-amplification duplicates.
- SEACR: `seacr_norm` (`non`/`norm`), `seacr_stringent` (`stringent`/`relaxed`), `seacr_peak_threshold` (default `0.05`, only used without controls).
- MACS2: `macs2_qvalue` (`0.01`), `macs2_pvalue` (overrides q), `macs_gsize` (default `2.7e9`), `macs2_narrow_peak` (default `true`; set `false` for broad histone marks), `macs2_broad_cutoff` (`0.1`).
- Consensus: `consensus_peak_mode` (`group`/`all`), `replicate_threshold` (default `1`).
- QC: `dt_qc_bam_binsize` (`500`), `min_frip_overlap` (`0.2`), `min_peak_overlap` (`0.2`), `dt_heatmap_gene_bodylen` (`5000`).

## Test data
The pipeline's `test` profile uses a very small downsampled GSE145187 CUT&Tag samplesheet (`test-GSE145187-small.csv`) aligned against a chr20-only hg38 reference FASTA + Bowtie2 index, hg38 chr20 GTF and gene BED, the shipped `hg38-blacklist.bed`, and the E. coli U00096.3 spike-in FASTA/Bowtie2 index. Mitochondrial and linear-amplification duplicate removal are both enabled. Running the workflow is expected to produce trimmed FASTQs, target and spike-in Bowtie2 BAMs, MarkDuplicates-processed BAMs, bedGraph and bigWig coverage tracks, SEACR (and optionally MACS2) peak BED files, consensus peak BEDs per group, deepTools PCA/fingerprint/correlation/heatmap plots, an `igv_session.xml`, and a final `MultiQC` report aggregating FastQC, Trim Galore, Bowtie2, Picard, preseq, deepTools, and peak/FRiP QC. The `test_full` profile swaps in the complete GSE145187 samplesheet against full `GRCh38` and runs both SEACR and MACS2.

## Reference workflow
nf-core/cutandrun v3.2.2 — https://github.com/nf-core/cutandrun (MIT). Pipeline covers CUT&RUN, CUT&Tag, and TIPseq with SEACR/MACS2 peak calling, IgG-aware background handling, and spike-in normalisation.
