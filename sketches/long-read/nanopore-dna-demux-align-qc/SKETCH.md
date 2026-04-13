---
name: nanopore-dna-demux-align-qc
description: Use when you have raw or basecalled Oxford Nanopore DNA reads (optionally
  multiplexed with a Nanopore barcode kit) and need a reproducible demultiplexing,
  QC and reference alignment pipeline producing sorted BAMs and per-sample QC reports.
  Optional downstream short and structural variant calling against a user-supplied
  reference.
domain: long-read
organism_class:
- eukaryote
- bacterial
- viral
input_data:
- long-reads-ont-fastq
- reference-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/nanoseq
  url: https://github.com/nf-core/nanoseq
  version: 3.1.0
  license: MIT
tools:
- qcat
- nanolyse
- nanoplot
- fastqc
- minimap2
- graphmap2
- samtools
- bedtools
- medaka
- deepvariant
- pepper-margin-deepvariant
- sniffles
- cutesv
- multiqc
tags:
- nanopore
- ont
- long-read
- dna
- demultiplexing
- alignment
- qc
- variant-calling
test_data: []
expected_output: []
---

# Nanopore DNA demultiplexing, QC and alignment

## When to use this sketch
- Input is Oxford Nanopore DNA sequencing data (pre-basecalled FASTQ, or a `fastq_pass/` directory from a run), possibly multiplexed with a native or rapid barcode kit (e.g. `NBD103/NBD104`, `SQK-PBK004`, `RBK004`).
- You want an end-to-end nf-core pipeline that handles: optional qcat demultiplexing, optional lambda/contaminant removal with NanoLyse, NanoPlot + FastQC read QC, reference alignment with minimap2 (or graphmap2) using `-ax map-ont` presets, sorted/indexed BAMs, bigWig coverage tracks, and a MultiQC summary.
- Each sample may point at its own reference FASTA (local path or an iGenomes key) in the samplesheet.
- Optionally you also want haploid/diploid small-variant calls (medaka, DeepVariant, or PEPPER-Margin-DeepVariant) and structural variant calls (Sniffles or cuteSV) against the same reference.

## Do not use when
- Data is Nanopore **cDNA** or **directRNA** and you want transcript discovery, quantification, differential expression, m6A or xPore modification analysis, or JAFFAL fusion calling — use a dedicated nanopore-rna-seq sketch (same pipeline, `--protocol cDNA` or `--protocol directRNA`).
- Data is Illumina short-read — use a short-read variant-calling or alignment sketch.
- You need PacBio HiFi / CLR specific workflows.
- You need de novo assembly of a genome from the reads — this pipeline does not assemble.
- You only have raw FAST5 and need GPU basecalling as part of the workflow; nanoseq expects already-basecalled FASTQ (or a `fastq_pass` directory).

## Analysis outline
1. Parse samplesheet (`group,replicate,barcode,input_file,fasta,gtf`) and resolve per-sample references.
2. (Optional) Demultiplex pre-basecalled FASTQ with **qcat** using `--barcode_kit`.
3. (Optional) Remove contaminants (default lambda phage) with **NanoLyse** when `--run_nanolyse` is set.
4. Raw read QC with **NanoPlot** and **FastQC** (per sample).
5. Build aligner index once per unique reference and align reads with **minimap2** (`-ax map-ont` for DNA) or **graphmap2**.
6. Sort, index and collect flagstat/idxstats/stats with **samtools**.
7. Generate **bigWig** (and for RNA protocols bigBed) coverage tracks with bedtools + UCSC `bedGraphToBigWig`.
8. (Optional, DNA only) Small variant calling with **medaka** (default), **DeepVariant**, or **PEPPER-Margin-DeepVariant** when `--call_variants` is set.
9. (Optional, DNA only) Structural variant calling with **Sniffles** (default) or **cuteSV**.
10. Aggregate all QC and alignment stats into a single **MultiQC** report.

## Key parameters
- `--input samplesheet.csv` — 6-column CSV: `group,replicate,barcode,input_file,fasta,gtf`.
- `--protocol DNA` — critical; selects `minimap2 -ax map-ont` and enables DNA-side variant calling branches. Use `cDNA`/`directRNA` only for the RNA sketch.
- `--input_path` — path to non-demultiplexed FASTQ or `fastq_pass/*` when demultiplexing is needed.
- `--barcode_kit` — e.g. `NBD103/NBD104`, `SQK-PBK004`, `RBK004`; required when running qcat.
- `--skip_demultiplexing` — set when `input_file` entries already point at per-sample FASTQ/BAM.
- `--aligner minimap2` (default) or `graphmap2`.
- `--call_variants` together with `--variant_caller {medaka,deepvariant,pepper_margin_deepvariant}` and `--structural_variant_caller {sniffles,cutesv}`.
- `--skip_quantification --skip_fusion_analysis --skip_modification_analysis` — turn off RNA-only branches for pure DNA runs (the test profile does exactly this).
- `--skip_bigwig` / `--skip_bigbed` — skip coverage track generation to save time/space.
- `-profile docker|singularity|conda` — container/environment selection; DeepVariant and PEPPER-Margin-DeepVariant require Docker or Singularity.

## Test data
The bundled `test` profile runs a minimal non-demultiplexed Nanopore DNA dataset (`sample_nobc_dx.fastq.gz`) hosted in `nf-core/test-datasets` on branch `nanoseq`, together with a tiny samplesheet (`samplesheet_nobc_dx.csv`) describing one group to be split with the `NBD103/NBD104` native barcode kit. The run is capped at 2 CPUs / 6 GB / 12 h and sets `--protocol DNA`, skipping quantification, bigWig, bigBed, fusion and modification analysis. Expected outputs are: per-barcode FASTQ files under `qcat/fastq/`, NanoPlot and FastQC reports, coordinate-sorted/indexed BAMs under `minimap2/` with accompanying `samtools stats/flagstat/idxstats`, and a consolidated `multiqc/multiqc_report.html` — verifying that demultiplexing, QC and alignment paths all complete on the minimal dataset.

## Reference workflow
nf-core/nanoseq v3.1.0 — https://github.com/nf-core/nanoseq (DSL2, Nextflow ≥22.10.1). Primary citation: Chen et al., *A systematic benchmark of Nanopore long read RNA sequencing*, bioRxiv 2021. Run with `nextflow run nf-core/nanoseq -r 3.1.0 --input samplesheet.csv --protocol DNA --barcode_kit <KIT> -profile <docker|singularity|...>`.
