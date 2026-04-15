---
name: single-cell-donor-demultiplexing-rescue
description: Use when you need to demultiplex a pooled multi-donor single-cell RNA-seq
  experiment that has BOTH a cell-hashing (HTO) readout AND donor genotype data, and
  you want to run hashing- and genotype-based deconvolution jointly and rescue cells
  via donor matching. Assumes 10x-style count matrices, an aligned BAM, a donor VCF,
  and a cell-barcodes list per sample.
domain: single-cell
organism_class:
- eukaryote
- vertebrate
- diploid
input_data:
- 10x-scrna-matrix
- hto-matrix
- scrna-bam
- donor-vcf
- cell-barcodes
- reference-fasta
source:
  ecosystem: nf-core
  workflow: nf-core/hadge
  url: https://github.com/nf-core/hadge
  version: 0.2.0
  license: MIT
  slug: hadge
tools:
- name: cellsnp-lite
- name: vireo
  version: 0.5.8
- name: popscle-demuxlet
- name: popscle-freemuxlet
- name: souporcell
- name: htodemux
- name: multiseqdemux
- name: bff
- name: demuxem
- name: gmm-demux
  version: 0.2.2.3
- name: hasheddrops
- name: scanpy-hashsolo
- name: multiqc
tags:
- single-cell
- demultiplexing
- cell-hashing
- hto
- genotype
- donor
- pooled
- multiplexing
- rescue
- mudata
- anndata
test_data: []
expected_output: []
---

# Single-cell donor demultiplexing (hashing + genotype rescue)

## When to use this sketch
- Pooled scRNA-seq library with cells from multiple donors that needs to be split back into per-donor assignments.
- You have BOTH a cell-hashing (HTO) readout and donor genotype data (or at least a common-variants VCF) and want to combine them for maximum cell recovery.
- Donors are genetically distinct enough for SNP-based deconvolution (e.g. unrelated human individuals).
- You want an automatic head-to-head comparison of multiple hashing and SNP tools plus a donor-matching/rescue step that re-labels cells where hashing failed.
- Input is 10x-Genomics-style: RNA count matrix (.tar.gz), HTO count matrix (.tar.gz), position-sorted BAM with CB/UB tags, barcodes.tsv, and a donor/common-variants VCF.

## Do not use when
- You only have hashing data and no genotypes — run the pipeline with `--mode hashing` (hashing-only sibling workflow) instead of `rescue`.
- You only have genotypes and no HTO library — run with `--mode genetic` instead.
- You already have per-tool demultiplexing outputs and only need to reconcile donors across methods — use `--mode donor_match` with `--demultiplexing_result`, `--vireo_filtered_variants`, `--cell_genotype`, and `--gt_donors`.
- Donors are genetically identical (monozygotic, isogenic lines, clonal) — SNP tools will fail; use a pure hashing workflow.
- Bulk RNA-seq, SMART-seq2 without UMIs, or non-10x chemistries where CB/UB tags are absent.
- You need cell calling / empty-droplet removal, QC, clustering, or annotation — those are downstream of this sketch.

## Analysis outline
1. Parse samplesheet (`sample,rna_matrix,hto_matrix,bam,vcf,n_samples,barcodes`) and untar the RNA and HTO 10x matrices.
2. Extract HTO names from the HTO matrix `features.tsv.gz`.
3. Genotype-based deconvolution branch:
   1. Pile up single-cell SNPs with `cellsnp-lite` against the common-variants VCF.
   2. Genotype-free / prior-assisted donor assignment with `vireo` (`--vireo_force_learn_gt` on by default).
   3. Reference-based assignment with `popscle demuxlet` (uses `dsc-pileup`).
   4. Reference-free clustering with `popscle freemuxlet`.
   5. Clustering + optional remap with `souporcell` (requires `--fasta`).
4. Merge per-tool genetic assignments/classifications into a single summary table.
5. Hashing-based deconvolution branch (tools selected via `--hash_tools`):
   1. `htodemux` and `multiseqdemux` (Seurat, CLR-normalised HTO assay).
   2. `bff` (cellhashR) with `bff_methods=COMBINED`.
   3. `demuxem` (EM over HTO + RNA).
   4. `gmm-demux` (Gaussian mixture over HTO).
   5. `hasheddrops` (DropletUtils) and `scanpy.external.pp.hashsolo`.
6. Merge per-tool hashing assignments/classifications into a single summary table.
7. Join genetic + hashing calls into one combined table and AnnData/MuData (`*_genetic.h5ad`, `*_hashing.h5ad`, `*_genetic_and_hashing.h5mu`).
8. Donor match: for every hashing × genetic pair, compute Pearson correlation between binarised assignment vectors, pick the best-scoring pair, and relabel HTOs to donor identities.
9. Find informative / donor-specific variants from vireo output and emit a subset donor-genotype VCF (`_donor_specific.vcf.gz`, `_vireo.vcf.gz`).
10. Aggregate run QC with `MultiQC`.

## Key parameters
- `--mode rescue` — required for joint hashing+genetic+donor-matching (alternatives: `genetic`, `hashing`, `donor_match`).
- `--input samplesheet.csv` — one row per pooled experiment.
- `--outdir <dir>` and `-profile docker|singularity|conda|<institute>`.
- `--hash_tools htodemux,hasheddrops,multiseq,gmm-demux,bff,hashsolo[,demuxem]` — comma-separated subset of the seven supported hashing tools.
- `--genetic_tools demuxlet,freemuxlet,vireo,souporcell[,cellsnp]` — comma-separated subset of the SNP tools.
- `--fasta <ref.fa>` — mandatory when `souporcell` is in `--genetic_tools`; otherwise set `--genome` (e.g. `GRCh38`) to auto-download.
- `--common_variants <vcf[.gz]>` — optional BAM pre-filter to reads overlapping known SNPs.
- `--match_donor true` (default) with `--find_variants true`, `--subset_gt_donors true`, `--variant_count 10`, `--variant_pct 0.9` — donor-matching and informative-variant filtering thresholds.
- Per-sample fields in the samplesheet: `n_samples` (number of multiplexed donors) and `barcodes` (target cell list, e.g. Cell Ranger `barcodes.tsv`).
- Tool-critical defaults worth knowing: `souporcell_ploidy: 2`, `vireo_genotag: GT`, `cellsnp_celltag: CB` / `cellsnp_umitag: Auto`, `gmmdemux_threshold: 0.8`, `htodemux_quantile: 0.99`, `multiseqdemux_quantile: 0.7`, `hasheddrops_isCellFDR: 0.01`, `hashsolo_priors: 0.01,0.8,0.19` (NEGATIVE,SINGLET,DOUBLET).
- `--generate_anndata true` and `--generate_mudata true` to emit `.h5ad` / `.h5mu` summaries.

## Test data
The bundled `test` profile (`conf/test.config`) runs the full `rescue` mode on a tiny downsampled human chr21 dataset: the samplesheet `samplesheet_rescue.csv` from `nf-core/test-datasets` (branch `hadge`) points at chr21 10x RNA and HTO `.tar.gz` matrices, a chr21 BAM, a chr21 donor VCF, a `barcodes.tsv`, and `n_samples=2`, with the GRCh38 chr21 `genome.fasta` supplied via `--fasta`. It is configured with `hash_tools=hasheddrops,bff,gmm-demux` and `genetic_tools=freemuxlet,vireo,souporcell` to exercise both branches plus donor matching within a 4 CPU / 15 GB / 1 h resource budget. A successful run should populate `genetic/`, `hashing/`, `donor_match/`, `find_variants/`, and `summary/` output folders, produce per-tool assignment/classification CSVs that merge into `*_(assignment|classification).csv`, emit `*_genetic.h5ad`, `*_hashing.h5ad`, and `*_genetic_and_hashing.h5mu`, write a best-pair donor map (`*_best_donor_match.csv`, `*_score_record.csv`), and generate a MultiQC HTML report under `multiqc/`. Sibling profiles `test_genetic`, `test_hashing`, and `test_donor_match` exercise the other three modes on the same backing data.

## Reference workflow
nf-core/hadge v0.2.0 (https://github.com/nf-core/hadge) — community pipeline combining 11 hashing/genotype deconvolution methods with a donor-matching rescue step, released under MIT.
