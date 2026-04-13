---
name: bacterial-genome-assembly-short-read
description: Use when you need to assemble, QC, and annotate a bacterial isolate genome
  from paired-end Illumina short reads. Produces a polished draft assembly with contamination
  screening, QUAST/BUSCO QC, and Prokka/Bakta annotation. Covers the short-read assembly
  path of nf-core/bacass.
domain: assembly
organism_class:
- bacterial
- haploid
input_data:
- short-reads-paired
source:
  ecosystem: nf-core
  workflow: nf-core/bacass
  url: https://github.com/nf-core/bacass
  version: 2.5.0
  license: MIT
tools:
- fastp
- fastqc
- unicycler
- kraken2
- kmerfinder
- quast
- busco
- prokka
- multiqc
tags:
- bacteria
- wgs
- isolate
- denovo-assembly
- annotation
- illumina
test_data: []
expected_output: []
---

# Bacterial genome assembly (short-read isolate)

## When to use this sketch
- Single bacterial isolate sequenced on Illumina paired-end short reads.
- You want a de novo draft assembly (contigs/scaffolds) of a small (~1-10 Mb) haploid prokaryote genome.
- You also want standard downstream: contamination screen (Kraken2/Kmerfinder), assembly QC (QUAST + BUSCO), and structural/functional annotation (Prokka by default).
- Works for cultured isolates where sample purity matters and each sample is expected to be a single organism.

## Do not use when
- You have only Oxford Nanopore long reads → use a long-read bacterial assembly sketch (Flye/Dragonflye/Canu/Miniasm).
- You have both short and long reads and want a finished/closed genome → use a hybrid bacterial assembly sketch (Unicycler or Dragonflye hybrid).
- You are assembling a metagenome or mixed community → use a metagenomic assembly sketch.
- You want variant calling against a reference instead of de novo assembly → use a haploid bacterial variant-calling sketch.
- You are assembling a eukaryote, virus, or phage → use the appropriate domain-specific sketch.

## Analysis outline
1. Parse samplesheet (TSV/CSV/YAML) with columns `ID`, `R1`, `R2`, `LongFastQ`, `Fast5`, `GenomeSize` (only `ID`, `R1`, `R2` needed here).
2. Short-read QC with FastQC on raw reads.
3. Adapter/quality trimming with fastp.
4. Optional taxonomic classification of reads with Kraken2 against a standard k2 database (sample purity check).
5. Optional contamination / species ID with Kmerfinder against the bacteria database.
6. De novo assembly with Unicycler (SPAdes frontend with polishing).
7. Assembly QC with QUAST (contigs, N50, length) and BUSCO (lineage `bacteria_odb10` by default).
8. Genome annotation with Prokka (default) or Bakta/DFAST/Liftoff as alternatives.
9. Aggregate all per-sample and per-tool reports into a single MultiQC HTML report plus a custom assembly metrics summary.

## Key parameters
- `--input samplesheet.tsv` — sample sheet with `ID,R1,R2,LongFastQ,Fast5,GenomeSize` columns; set LongFastQ/Fast5/GenomeSize to `NA` for short-read-only samples.
- `--assembly_type short` — required for this sketch.
- `--assembler unicycler` — the default and recommended assembler for short-read bacterial isolates.
- `--kraken2db <url-or-path>` — e.g. `https://genome-idx.s3.amazonaws.com/kraken/k2_standard_8gb_20210517.tar.gz`; omit and set `--skip_kraken2` if you do not need the purity check.
- `--kmerfinderdb <path-or-url>` — bacteria Kmerfinder DB; or `--skip_kmerfinder` to skip.
- `--annotation_tool prokka` (default) with optional `--prokka_args " --fast"` or `" --genus Escherichia"`; switch to `bakta` (requires `--baktadb` or `--baktadb_download`) or `dfast` (requires `--dfast_config`) for alternative annotation.
- `--busco_lineage bacteria_odb10` (default) and `--busco_mode genome`; set `--skip_busco` if BUSCO databases are unavailable.
- `--fastp_args`, `--save_trimmed`, `--skip_fastp`, `--skip_fastqc` — fine-tune QC/trimming.
- `--outdir <dir>` and `-profile docker|singularity|conda` — standard nf-core execution.

## Test data
The pipeline's `test` profile (`conf/test.config`) uses the samplesheet `bacass/bacass_short_reseq.tsv` from the nf-core test-datasets repository, containing a small number of paired-end Illumina FASTQ samples for a bacterial isolate. It runs in `--assembly_type short` mode with `--skip_kraken2`, `--skip_kmerfinder`, and `--skip_pycoqc`, plus `--prokka_args ' --fast'` to keep runtime short. Expected outputs include fastp-trimmed FASTQs, a Unicycler assembly (`*.scaffolds.fa`, `*.assembly.gfa`), QUAST and BUSCO reports, Prokka annotations (`*.gff`, `*.faa`, `*.txt`), and a consolidated `multiqc/multiqc_report.html` with a `summary_assembly_metrics_mqc.csv` table. The `test_full` profile additionally exercises Kraken2 and Kmerfinder databases on the `bacass_full.tsv` dataset.

## Reference workflow
nf-core/bacass v2.5.0 (https://github.com/nf-core/bacass), short-read path — `--assembly_type short` with default Unicycler assembler and Prokka annotation.
