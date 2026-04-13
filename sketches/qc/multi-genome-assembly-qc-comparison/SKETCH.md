---
name: multi-genome-assembly-qc-comparison
description: Use when you need to benchmark and compare the quality of multiple genome
  assemblies (with or without annotations) side-by-side, producing completeness, contiguity,
  contamination, and phylogenetic-context summary plots. Accepts local FASTA/GFF or
  NCBI accessions.
domain: qc
organism_class:
- eukaryote
- bacterial
- vertebrate
- invertebrate
- plant
input_data:
- genome-fasta
- gff-annotation
- ncbi-accession
- long-reads-optional
source:
  ecosystem: nf-core
  workflow: nf-core/genomeqc
  url: https://github.com/nf-core/genomeqc
  version: dev
  license: MIT
tools:
- busco
- quast
- tidk
- merqury
- fcs-gx
- fcs-adaptor
- tiara
- agat
- gffread
- orthofinder
- multiqc
tags:
- genome-quality
- assembly-qc
- busco
- quast
- contamination-screening
- comparative-genomics
- annotation-qc
- phylogenetic-summary
test_data: []
expected_output: []
---

# Multi-genome assembly QC and comparison

## When to use this sketch
- You have two or more genome assemblies (draft or reference-grade) and want a uniform, side-by-side QC report rather than ad-hoc stats.
- Inputs are any mix of local FASTA files and/or NCBI RefSeq/GenBank accessions (`GCF_*` / `GCA_*`).
- You optionally have matching GFF/GTF annotations and want annotation-level metrics (gene counts, overlapping genes, longest-isoform proteomes) in addition to assembly metrics.
- You want contamination screening (foreign organisms, adaptors, organelle/domain classification) as part of QC.
- You need a phylogenetically-ordered summary figure (BUSCO- or OrthoFinder-based tree with per-species stat tracks) for a paper or report.
- You want results aggregated into a single MultiQC report plus an interactive Shiny app for adjusting the tree/stat figure.

## Do not use when
- You are calling variants against a reference — use a variant-calling sketch instead.
- You need to *produce* an assembly from raw reads — this pipeline evaluates finished assemblies, it does not assemble.
- You want rigorous phylogenetic inference: the orthology tree here is for QC context only, not publishable phylogenies.
- Your question is about read-level QC of FASTQ files — use a read-QC sketch (FastQC/fastp) instead.
- You only have a single assembly and need no cross-sample comparison — lighter single-sample QC tools (QUAST + BUSCO alone) are sufficient.
- You need structural variant detection, methylation, or expression analysis.

## Analysis outline
1. Parse the samplesheet and, for rows with `ncbi` accessions, fetch FASTA (+GFF for RefSeq) via `ncbi-genome-download`.
2. Standardize inputs: decompress FASTA/GFF, validate and normalize annotations with AGAT (or gffread).
3. Contiguity and composition stats with QUAST (N50, N90, GC%, sequence counts).
4. Genome completeness with BUSCO against a user-selected lineage; plot BUSCO marker positions as ideograms (RIdeogram).
5. Optional telomeric repeat scan with tidk.
6. Optional read-based completeness/QV with Merqury (requires matching long-read FASTQ).
7. Optional contamination screening: FCS-GX (foreign organism), FCS-adaptor (vectors/adaptors), Tiara (domain/organelle classification); emit cleaned FASTA.
8. Annotation-mode only: AGAT `sp_statistics` for gene/feature counts, a GenomicRanges-based overlapping-genes module, AGAT `sp_keep_longest_isoform`, then gffread to extract longest-isoform proteomes.
9. Annotation-mode only: OrthoFinder on the longest-isoform proteomes to build a rooted species tree.
10. Tree-summary module paints per-species QC stats alongside the BUSCO or OrthoFinder tree and packages a Shiny app for interactive tweaking.
11. MultiQC aggregates all per-tool reports into one HTML summary.

## Key parameters
- `input`: CSV samplesheet with columns `species,ncbi,fasta,gff,fastq,taxid` (any subset; the workflow auto-routes rows by which fields are populated).
- `outdir`: results directory (absolute path required for cloud).
- `busco_lineage`: BUSCO ODB10 lineage name — **must be set explicitly**; leaving it on `auto` is documented as unreliable. Examples: `hymenoptera_odb10`, `mycoplasmatales_odb10`, `vertebrata_odb10`.
- `busco_mode`: `proteins` (default when annotations are present) or `genome`; hardcoded to `genome` in genome-only mode.
- `groups`: NCBI taxonomic group filter for `ncbi-genome-download` (`all`, `bacteria`, `fungi`, `vertebrate_mammalian`, `plant`, …).
- `gxdb` / `gxdb_manifiest` / `ramdisk`: FCS-GX database path / manifest / optional tmpfs location; presence of `gxdb` + per-row `taxid` activates the decontamination subworkflow.
- `skip_tidk`, `kvalue` (meryl/Merqury k-mer size, default 21), `repeat` (custom telomere motif).
- `val_tool`: `agat` (default) or `gffread` for GFF validation.
- `skip_plots_genome_anno` / `skip_plots_genome_only`: which stat tracks to omit from the tree summary (`ch_plot`, `len_plot`, `gene_plot`, `n50_plot`, `pies_plot`, `ortho_plot`, `nseqs_plot`).
- `save_assembly`, `save_sorted_seqs`, `save_validated_annotation`, `save_longest_isoform`, `save_extracted_seqs`, `save_orthofinder_results`: publication toggles for intermediate artifacts.
- `tree_scale`: fine-tunes tree width so tips don't collide with stat tracks (very sensitive, adjust in 2× steps).

## Test data
The default `test` profile points `input` at the `genomeqc/samplesheet/input_bacteria.csv` test samplesheet hosted on nf-core/test-datasets and pins `busco_lineage = mycoplasmatales_odb10` for speed. It exercises the bacterial genome+annotation path on small NCBI-fetched assemblies and is expected to complete end-to-end producing: QUAST reports, BUSCO short summaries plus RIdeogram PNGs, AGAT annotation stats, gffread-extracted longest-isoform proteomes, an OrthoFinder rooted species tree, a `tree_summary/tree_plot.pdf`, a MultiQC HTML report, and the Shiny app launcher under `shiny/app/shiny_app.sh`. Sibling profiles (`test_local`, `test_genomeonly`, `test_nofastq`) cover local-file, genome-only, and annotation-without-reads variants; the full-size AWS profile (`test_full`) runs Hymenoptera genomes with `hymenoptera_odb10`.

## Reference workflow
nf-core/genomeqc (dev branch, template 3.5.2) — https://github.com/nf-core/genomeqc. Authored by Chris Wyatt and Fernando Duarte (UCL). See `docs/usage.md` and `docs/output.md` for parameter and output details; see `CITATIONS.md` for per-tool citations (BUSCO, QUAST, tidk, Merqury, AGAT, gffread, OrthoFinder, FCS-GX, FCS-adaptor, Tiara, RIdeogram, MultiQC).
