---
name: small-rna-seq-mirna-quantification
description: Use when you need to quantify mature miRNAs, precursor hairpins and isomiRs
  from single-end small RNA-seq (smRNA-Seq) Illumina libraries, optionally discovering
  novel miRNAs. Covers adapter/UMI trimming, miRBase/MirGeneDB alignment, edgeR normalization
  and miRTrace QC for human or other species with miRBase support.
domain: rna-seq
organism_class:
- eukaryote
- vertebrate
input_data:
- short-reads-single-end
- reference-fasta
- mirbase-mature-fasta
- mirbase-hairpin-fasta
- mirna-gff3
source:
  ecosystem: nf-core
  workflow: nf-core/smrnaseq
  url: https://github.com/nf-core/smrnaseq
  version: 2.4.1
  license: MIT
tools:
- fastqc
- fastp
- umi_tools
- umicollapse
- bowtie1
- bowtie2
- samtools
- mirtrace
- mirtop
- seqcluster
- edger
- mirdeep2
- multiqc
tags:
- mirna
- small-rna
- smrnaseq
- isomir
- mirbase
- mirgenedb
- quantification
- edger
- mirdeep2
test_data: []
expected_output: []
---

# Small RNA-Seq miRNA quantification

## When to use this sketch
- Single-end Illumina smRNA-Seq libraries (<= ~50 nt inserts) targeting mature miRNAs and precursor hairpins.
- You want per-sample counts for mature miRNAs and hairpins, isomiR annotation (mirtop/mirGFF3), and a TMM-normalized expression matrix plus MDS/heatmap QC from edgeR.
- Species is supported by miRBase or MirGeneDB (e.g. `hsa`, `mmu`, `rno`); you have or can fetch `mature.fa`, `hairpin.fa` and a miRBase GFF3.
- Library was prepared with a known small-RNA kit whose 3' adapter and 5'/3' clip offsets map onto one of the built-in protocol profiles: `illumina`, `nextflex`, `qiaseq`, or `cats`.
- Optional goals fit naturally: UMI deduplication (e.g. QIAseq), contamination filtering against rRNA/tRNA/cDNA/ncRNA/piRNA, novel miRNA discovery with miRDeep2, or genome-level alignment QC against a host reference.

## Do not use when
- You have bulk mRNA-seq, total RNA-seq or ribo-depleted long-insert libraries — use a standard `rna-seq` bulk quantification sketch instead.
- You need single-cell small RNA profiles — no sibling sketch; this pipeline assumes bulk libraries.
- You are doing piRNA-, tRF- or circRNA-focused analysis as the primary endpoint — this pipeline treats them only as contaminants to filter out.
- You need differential expression testing and contrasts beyond QC-level edgeR normalization — export the `mature`/`hairpin` count tables and run a dedicated DE workflow downstream.
- Reads are paired-end with biologically meaningful R2: only R1 is used; R2 is discarded.
- Your species is not in miRBase/MirGeneDB — use a de novo small-RNA annotation approach instead.

## Analysis outline
1. Raw read QC with FastQC.
2. Optional UMI barcode extraction with `umi_tools extract` (pattern via `umitools_bc_pattern`).
3. 3' adapter trimming and length/quality filtering with fastp (protocol-specific adapter + clip offsets).
4. Optional fastq-level UMI deduplication with UMICollapse, followed by a second fastp length filter.
5. Trimmed-read QC with FastQC and small-RNA-specific QC with miRTrace (uses `mirtrace_species`).
6. Optional Bowtie2 contamination filtering against user-supplied rRNA/tRNA/cDNA/ncRNA/piRNA/other FASTAs (miRNA sequences are first subtracted from the contaminant sets).
7. Bowtie1 alignment of cleaned reads to miRBase/MirGeneDB `mature.fa`; unmapped reads are then aligned to `hairpin.fa`.
8. SAMtools sort/index/idxstats on mature and hairpin BAMs to produce per-feature counts.
9. edgeR script (`edgeR_miRBase.r`) computes TMM-normalized CPM tables and MDS / sample-distance / heatmap PDFs for mature and hairpin counts.
10. seqcluster collapses reads and mirtop parses the hairpin BAM against the miRBase GFF3 to emit mirGFF3, a joined isomiR TSV and a per-miRNA count table.
11. Optional Bowtie1 alignment of cleaned reads to the host genome FASTA for alignment-rate QC.
12. Optional miRDeep2 (`mapper.pl` + `miRDeep2.pl`) for known and novel miRNA discovery against the genome; exit-255 failures are tolerated.
13. MultiQC aggregates FastQC, fastp, miRTrace, SAMtools, Bowtie1/2 and mirtop stats into a single HTML report.

## Key parameters
- `input`: CSV samplesheet with columns `sample,fastq_1` (single-end; repeated `sample` rows are concatenated across lanes; `fastq_2` is accepted but ignored).
- `outdir`: results directory.
- Protocol profile: add one of `-profile illumina | nextflex | qiaseq | cats` alongside the container profile; this sets `three_prime_adapter`, `clip_r1`, `three_prime_clip_r1`. Without it the pipeline will fail.
- `three_prime_adapter` (default `AGATCGGAAGAGCACACGTCTGAACTCCAGTCA`): set to `auto-detect` only if you explicitly want fastp auto-detection.
- `mirtrace_species`: 3-letter miRBase code, e.g. `hsa`; or `mirgenedb_species` together with `--mirgenedb` for MirGeneDB.
- References: `genome` (iGenomes key) OR explicit `fasta` + `bowtie_index`; `mature`, `hairpin`, `mirna_gtf` (auto-downloaded from miRBase if unset) or the `mirgenedb_*` equivalents.
- Trimming: `fastp_min_length: 17`, `fastp_max_length: 100`, `min_trimmed_reads: 10`, `phred_offset: 33`.
- UMIs: `with_umi: true`, `umitools_extract_method: regex|string`, `umitools_bc_pattern` (e.g. QIAseq `.+(?P<discard_1>AACTGTAGGCACCATCAAT){s<=2}(?P<umi_1>.{12})(?P<discard_2>.*)`), optionally `--skip_fastp` when the UMI regex depends on the kit adapter.
- Contamination filtering: `filter_contamination: true` plus any of `rrna`, `trna`, `cdna`, `ncrna`, `pirna`, `other_contamination` FASTA paths.
- Skip switches: `skip_mirdeep`, `skip_fastqc`, `skip_fastp`, `skip_multiqc`.
- Housekeeping: `save_intermediates`, `save_reference`, `save_umi_intermeds`.

## Test data
The `test` profile runs on a single-end human smRNA-Seq samplesheet hosted in `nf-core/test-datasets` (branch `smrnaseq`, `samplesheet/v2.0/samplesheet.csv`) with a trimmed `genome.fa` and a prebuilt `bowtie_index.tar.gz`, `mirtrace_species = 'hsa'`, and `skip_mirdeep = true`; it layers the `illumina` protocol config on top so adapter/clip defaults are set. The README example samplesheet uses eight single-end FASTQs from an ngi-igenomes S3 bucket (`C1-N1`..`Ctl-N3`) to illustrate a typical multi-sample run. A successful run is expected to produce: FastQC + fastp + miRTrace reports, mature and hairpin BAMs with SAMtools idxstats, `mature_normalized_CPM.txt` / `hairpin_normalized_CPM.txt` plus MDS, heatmap and dendrogram PDFs under `mirna_quant/edger_qc/`, a mirtop `mirna.tsv` and `joined_samples_mirtop.tsv` under `mirna_quant/mirtop/`, and a unified `multiqc/multiqc_report.html`. The `test_full` profile runs the same pipeline against `samplesheet-full.csv` with `genome = 'GRCh37'` via iGenomes.

## Reference workflow
nf-core/smrnaseq v2.4.1 (https://github.com/nf-core/smrnaseq, DOI 10.5281/zenodo.10696391), MIT licensed. See `docs/usage.md` and `docs/output.md` for parameter and output details, and `conf/test.config` / `conf/test_full.config` for the reference test profiles.
