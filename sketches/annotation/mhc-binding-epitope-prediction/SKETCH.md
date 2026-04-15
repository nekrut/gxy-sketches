---
name: mhc-binding-epitope-prediction
description: Use when you need to predict MHC class I or class II binding epitopes
  from somatic variants (VCF), protein FASTA, or peptide lists for a given set of
  HLA alleles, e.g. generating putative neoantigens from annotated tumor variants,
  scanning proteins for binding hotspots, or re-scoring immunopeptidomics peptide
  hits. Handles human HLA typing in MHCgnomes-compatible notation.
domain: annotation
organism_class:
- vertebrate
- human
input_data:
- vcf-annotated
- protein-fasta
- peptide-tsv
- hla-allele-list
source:
  ecosystem: nf-core
  workflow: nf-core/epitopeprediction
  url: https://github.com/nf-core/epitopeprediction
  version: 3.1.0
  license: MIT
  slug: epitopeprediction
tools:
- name: epytope
- name: mhcflurry
- name: mhcnuggets
- name: mhcnuggetsii
- name: netmhcpan
- name: netmhciipan
- name: snpsift
- name: multiqc
tags:
- neoantigen
- immunology
- hla
- mhc
- epitope
- immunopeptidomics
- peptide-binding
- cancer-immunotherapy
test_data: []
expected_output: []
---

# MHC binding epitope prediction

## When to use this sketch
- You have annotated somatic variants (VCF from SnpEff or Ensembl VEP) and want putative neo-epitopes scored against a patient's HLA alleles.
- You have one or more proteins (FASTA) and want to scan them for MHC class I or class II binding hotspots / darkspots.
- You have a peptide list (TSV) from immunopeptidomics or another source and want allele-specific binding affinity and percentile-rank predictions.
- Target organism is human and HLA alleles are known (class I: HLA-A/B/C; class II: DRB1/DQ/DP).
- You want a harmonized, per-sample prediction table combining multiple predictors (mhcflurry, mhcnuggets, netMHCpan, netMHCIIpan).

## Do not use when
- You need to *call* variants from raw sequencing reads first — run a variant-calling sketch upstream and feed the annotated VCF in here.
- You need protein sequences generated from a tumor RNA-seq assembly or fusion caller — pre-process those into FASTA/peptides externally.
- You need TCR–peptide or pMHC structural modeling — this pipeline only does sequence-based binding affinity / rank prediction.
- You are working with non-human MHC (e.g. murine H-2) — not supported by the shipped predictors and allele parsing.
- You only want to export mutated protein sequences for downstream mass spectrometry search: use `--fasta_output` mode of this pipeline; MHC binding is skipped in that mode.

## Analysis outline
1. Parse samplesheet (`sample,alleles,mhc_class,filename`) and auto-detect input type per row (VCF / FASTA / peptide TSV).
2. Normalize HLA alleles to a uniform nomenclature via MHCgnomes.
3. For VCF input: read annotated variants (SnpEff/VEP), fetch transcript/protein info from Ensembl BioMart (`--genome_reference`), and use epytope (FRED2) to enumerate all mutated peptides within `[min_peptide_length_class*, max_peptide_length_class*]`; optionally also emit wild-type counterparts (`--wild_type`).
4. For protein FASTA input: sliding-window peptide generation via epytope with the same length bounds.
5. For peptide TSV input: read peptides directly from column `--peptide_col_name` (default `sequence`).
6. Optionally self-filter peptides against a reference proteome (`--proteome_reference`) to drop self-peptides.
7. Split the peptide set into chunks (`--peptides_split_minchunksize` / `--peptides_split_maxchunks`) for parallel prediction.
8. Run the selected predictor(s) from `--tools` per chunk: mhcflurry, mhcnuggets (class I), mhcnuggetsii (class II), netmhcpan, netmhciipan.
9. Merge per-chunk predictor outputs into one harmonized per-sample TSV with columns `sequence, allele, BA, rank, binder, predictor` (+ metadata); optionally pivot to wide format and/or keep only binders.
10. Aggregate QC and binder statistics into a MultiQC report.
11. Optionally (`--fasta_output`) emit a FASTA of wild-type + mutated protein sequences flanking each variant (MHC prediction step is skipped in this mode).

## Key parameters
- `input`: samplesheet CSV with columns `sample,alleles,mhc_class,filename`. `alleles` may be a `;`-separated HLA string or a path to a `.txt` file (one allele per row). `mhc_class` is `I` or `II`. `filename` is `.vcf`/`.vcf.gz`, `.fasta`, or `.tsv`.
- `tools`: comma-separated predictors. Default `mhcnuggets`. Options: `mhcflurry`, `mhcnuggets`, `mhcnuggetsii`, `netmhcpan`, `netmhciipan`. Use `mhcnuggetsii` / `netmhciipan` for MHC class II.
- `min_peptide_length_classI` / `max_peptide_length_classI`: class I length window (defaults 8 / 12; typical neoantigen range 8–11).
- `min_peptide_length_classII` / `max_peptide_length_classII`: class II length window (defaults 8 / 25; typical 12–25).
- `genome_reference`: Ensembl BioMart reference for VCF transcript lookup. Default `grch37`; set `grch38` for GRCh38 or an Ensembl archive URL for a pinned version.
- `proteome_reference`: optional FASTA used to self-filter peptides derived from variants.
- `peptide_col_name`: column in peptide TSV holding sequences (default `sequence`).
- `wild_type`: also predict wild-type counterparts of mutated peptides (useful for differential binding / neoantigen ranking).
- `binder_only`: keep only peptides predicted as binders by at least one predictor in the final table.
- `wide_format_output`: pivot predictors × alleles into `<predictor>_<metric>` columns.
- `fasta_output` (+ `fasta_peptide_flanking_region_size`, default 25): emit variant-proteome FASTA and skip prediction entirely; VCF must be VEP-annotated with at least `--pick --protein --uniprot --hgvs --vcf`.
- `split_by_variants`, `peptides_split_maxchunks` (default 100), `peptides_split_minchunksize` (default 5000): parallelization knobs; raise chunk count for large VCFs / proteomes.
- `netmhcpan_path` / `netmhciipan_path`: required tarball paths when using NetMHCpan 4.x / NetMHCIIpan (not redistributable); `netmhc_system` in {`linux`,`darwin`} when running via conda. Note: conda profile is currently unsupported — use `-profile docker` or `-profile singularity`.
- Interpretation rule of thumb: select candidates by percentile `rank` (strong binder < 0.5, weak binder < 2), not raw `BA`, except for MHCnuggets where `BA` is preferred.

## Test data
The `test` profile uses a minimal samplesheet (`sample_sheet_variants.csv`) from nf-core/test-datasets containing annotated VCF input(s) paired with HLA class I alleles, and runs only `mhcnuggets` with peptide lengths restricted to 9–10 aa to keep runtime low. The `test_full` profile uses `sample_sheet_full_test.csv` covering both class I and class II samples and runs `mhcflurry,mhcnuggets,mhcnuggetsii` (NetMHC tools excluded because the tarballs are not redistributable), with class I lengths 9–10 and class II lengths 14–15. Expected outputs are per-sample harmonized prediction TSVs under `predictions/<sample>.tsv` with columns `sequence, allele, BA, rank, binder, predictor`, predictor-specific raw tables under `mhcflurry/`, `mhcnuggets/`, `mhcnuggetsii/` (and, for VCF inputs, intermediate epytope per-chromosome peptide tables under `epytope/<sample>_chr*.tsv`), plus a `multiqc/multiqc_report.html` summarizing binder/non-binder counts and score distributions.

## Reference workflow
nf-core/epitopeprediction v3.1.0 (https://github.com/nf-core/epitopeprediction), DOI 10.5281/zenodo.3564666. Uses epytope (FRED2) for peptide generation and wraps MHCflurry, MHCnuggets, NetMHCpan 4.x, and NetMHCIIpan 4.x for binding prediction.
