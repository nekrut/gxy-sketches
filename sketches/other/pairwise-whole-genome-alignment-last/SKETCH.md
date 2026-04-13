---
name: pairwise-whole-genome-alignment-last
description: Use when you need to align one or more whole query genome assemblies
  to a single target genome assembly and visualise the result as dot plots, producing
  MAF (and optionally SAM/BAM/CRAM/chain/psl) one-to-one orthologous alignments. Handles
  genome-to-genome comparisons across bacteria, fungi, invertebrates and vertebrates
  using the LAST aligner with trained parameters.
domain: other
organism_class:
- eukaryote
- bacterial
- viral
- vertebrate
input_data:
- genome-fasta-target
- genome-fasta-query
source:
  ecosystem: nf-core
  workflow: nf-core/pairgenomealign
  url: https://github.com/nf-core/pairgenomealign
  version: 2.2.2
  license: MIT
tools:
- last
- lastdb
- last-train
- lastal
- last-split
- last-dotplot
- maf-convert
- samtools
- assembly-scan
- seqtk
- multiqc
tags:
- whole-genome-alignment
- synteny
- dotplot
- pairwise
- last
- maf
- orthology
- genome-comparison
test_data: []
expected_output: []
---

# Pairwise whole-genome alignment with LAST

## When to use this sketch
- You have at least two genome assemblies in FASTA format and want a pairwise alignment: one designated target (indexed once) plus one or more query genomes aligned against it.
- You need orthologous one-to-one (syntenic) alignments suitable for downstream synteny, rearrangement, or divergence analysis.
- You want publication-quality dot plots visualising pairwise genome similarity, with contigs diagonalised and N-gap regions highlighted.
- You need output in MAF, or exported to SAM/BAM/CRAM/chain/psl/axt/blasttab/gff for downstream tools.
- Scenarios: comparing closely related strains, cross-species synteny (e.g. human vs macaque), self-alignment to detect segmental duplications (`--m2m`), or aligning a new assembly to a reference.
- Works for bacterial, viral, fungal, invertebrate and vertebrate genomes; seed choice scales from very sensitive (`MAM8`) to fast/sparse (`RY128`) for large vertebrate genomes.

## Do not use when
- You are aligning short reads (Illumina) or long reads (ONT/PacBio) to a reference — use a read-mapping / variant-calling sketch instead (e.g. bwa-mem2, minimap2, nf-core/sarek, nf-core/bacass).
- You want multiple sequence alignment of >2 genomes simultaneously (use Cactus/Progressive Mauve style tools, not this pipeline).
- You need variant calling (SNV/indel/SV) — this pipeline stops at alignment and dot plots; feed its BAM/CRAM output into a dedicated variant caller.
- You need transcriptome-to-genome or protein-to-genome alignment.
- Target and query are identical species at population scale and you just want SNPs — a read-based haploid or diploid variant-calling workflow is more appropriate.

## Analysis outline
1. Assembly QC of each query genome with `assembly-scan` (GC content, contig length stats) — skippable via `--skip_assembly_qc`.
2. Detect poly-N regions (>9 bp) in target and query with `seqtk cutN`, emitting BED tracks for dot-plot annotation.
3. Index the target genome with `lastdb` using the selected seed (`--seed`), soft-masking (`--softmask`), both strands (`-S2`), and exclusion of lowercase from seeding (`-c`).
4. Train per-query alignment scoring parameters with `last-train --revsym` (skipped if a `--lastal_params` scoring file is supplied).
5. Align each query to the target with `lastal` using trained parameters and `--lastal_args` / `--lastal_extr_args`.
6. Progressively refine alignments through `last-split` to produce many-to-one, one-to-many and finally one-to-one MAF files; many-to-many is only kept when `--m2m` is set.
7. Render dot plots of each retained alignment tier with `last-dotplot` (fixed pixel width so target scale is comparable across queries); optionally filter isolated alignments with `maf-filter`.
8. Convert the one-to-one MAF to the formats listed in `--export_aln_to` via `maf-convert` + `samtools sort` for SAM/BAM/CRAM.
9. Aggregate assembly-scan stats, last-train parameters and lastal percent-identity tables into a `MultiQC` report.

## Key parameters
- `--target <fasta>`: path/URL to the target genome FASTA (required). `--targetName` sets the label used in output filenames (default `target`).
- `--input <samplesheet.csv>`: CSV with header `sample,fasta`, one row per query genome.
- `--outdir <dir>`: required output directory.
- `--seed`: LAST seed family. `YASS` (default) for general long-weak similarities; `NEAR` for very similar sequences; `MAM4`/`MAM8` for sensitive weak similarity (slower, more RAM); `RY4`…`RY128` for sparse seeding on large/vertebrate genomes (full-size test uses `RY128`).
- `--softmask`: `tantan` (default, re-mask with LAST's internal tantan) or `original` (trust the FASTA's existing lowercase masking).
- `--lastal_args`: passed to both `last-train` and `lastal`. Default `-C2 -D1e9`; drop `-D1e9` for tiny genomes (viral test profile uses `-C2`).
- `--lastal_extr_args`: extra flags given only to `lastal` (not understood by `last-train`).
- `--lastal_params`: path to a pre-computed scoring matrix; skips `last-train` and uses identical parameters for every query.
- `--last_split_mismap`: mismap probability cutoff for `last-split` (default `1e-5`).
- `--m2m`: also emit the many-to-many alignment. Required for self-alignments; expensive on large genomes.
- `--export_aln_to`: comma-separated list from `axt,bam,bed,blast,blasttab,blasttab+,chain,cram,gff,html,psl,sam,tab` (default `no_export`). Text formats are gzipped; SAM/BAM/CRAM are coordinate-sorted with full target headers so files can be merged.
- Dot-plot controls: `--dotplot_width` (default 1000 px), `--dotplot_height` (default 10000 px), `--dotplot_font_size` (14), `--dotplot_options` (raw `last-dotplot` args), `--dotplot_filter` (apply `maf-filter`), and `--skip_dotplot_{m2m,m2o,o2m,o2o}` to suppress individual tiers — critical for large/repetitive vertebrate genomes where all but the one-to-one plot saturate.
- `--skip_assembly_qc`: skip the `assembly-scan` QC stage if already done upstream.
- Fixed by the pipeline: `lastdb -R01 -S2 -c`, `last-train --revsym`, MAF as canonical alignment format.

## Test data
The `test` profile aligns SARS-CoV-2 query genomes (listed in `pairgenomealign/tests/testsamplesheet.csv`) against the nf-core sarscov2 reference FASTA (`modules/data/genomics/sarscov2/genome/genome.fasta`), overrides `lastal_args` to just `-C2` because the genomes are small, and sets `export_aln_to = 'sam'`; it is expected to finish on 4 CPUs / 15 GB RAM within an hour and to emit per-query `*.o2o_aln.maf.gz`, an exported SAM, dot-plot PNGs, and a MultiQC report. A lighter `test_small` profile runs two fungal NCBI genomes in under five minutes and produces meaningful dot plots. The `test_full` profile aligns primate query genomes to `Homo_sapiens_GRCh38.p14` (downloaded from NCBI) using `seed = 'RY128'`, and is the large-scale reference run whose example outputs populate the nf-core results page (~1h42m wall, ~285 CPU-hours).

## Reference workflow
nf-core/pairgenomealign v2.2.2 (MIT; https://github.com/nf-core/pairgenomealign). Cite Plessy et al., Genome Res. 2024 (doi:10.1101/gr.278295.123) and the LAST papers (Kiełbasa 2011, Frith & Noé 2014, Frith & Kawaguchi 2015, Hamada 2017, Frith 2023).
