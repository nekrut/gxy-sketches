---
name: metagenome-mhc-epitope-prediction
description: Use when you need to predict MHC class I or class II binding peptides
  (epitopes) from microbiome-derived proteins, starting from metagenomic assemblies,
  MAGs/bins, or NCBI taxon IDs, and compare binding profiles across conditions and
  HLA alleles.
domain: other
organism_class:
- bacterial
- microbial-community
- prokaryote
input_data:
- metagenome-assembly-fasta
- metagenome-bins
- ncbi-taxon-ids
- hla-allele-list
source:
  ecosystem: nf-core
  workflow: nf-core/metapep
  url: https://github.com/nf-core/metapep
  version: 1.0.0
  license: MIT
tools:
- prodigal
- entrez
- epytope
- syfpeithi
- mhcflurry
- mhcnuggets
- pandas
- multiqc
tags:
- immunopeptidomics
- epitope-prediction
- mhc
- hla
- metagenomics
- microbiome
- vaccine-design
- neoantigen
test_data: []
expected_output: []
---

# Metagenome-derived MHC epitope prediction

## When to use this sketch
- You want to enumerate candidate T-cell epitopes from a microbial community (gut, skin, environmental) rather than from a single isolate or from human tumor data.
- Input is one or more of: metagenomic assembly contigs (FASTA), metagenomic bins/MAGs (folder or archive of FASTAs), or NCBI strain-level taxon IDs with optional assembly IDs and abundances.
- You want to score peptides against user-specified HLA/MHC alleles (class I or class II) using PSSM (SYFPEITHI) or ML predictors (MHCflurry, MHCnuggets).
- You need to compare multiple conditions (e.g., healthy vs. disease microbiomes, or different communities) and obtain per-entity binding ratios and score distributions per allele.
- Peptide length range of interest is within ~8-14 aa (default 9-11) and you care about weighting peptides by contig/taxon abundance.

## Do not use when
- You are predicting neoantigens from human tumor variants - use a tumor neoantigen pipeline instead.
- You only have raw metagenomic reads and have not assembled or binned them - run an assembly/binning workflow first (e.g. nf-core/mag) and feed the outputs here.
- You want functional or taxonomic profiling of a microbiome without epitope prediction - use a metagenomics profiling workflow instead.
- You need proteomics-based (mass-spec) immunopeptidome identification rather than in-silico prediction.
- Your target is a single bacterial isolate genome - running this pipeline works but a simpler per-proteome epitope prediction is more appropriate.

## Analysis outline
1. Parse samplesheet (condition, type, microbiome_path, alleles, weights_path) and build the relational data model (conditions, microbiomes, entities, alleles tables).
2. For `type: taxa` rows, download proteins for each taxon/assembly ID from NCBI Entrez (requires `NCBI_EMAIL` and `NCBI_KEY` nextflow secrets); for `type: assembly` or `type: bins`, predict ORFs/proteins with Prodigal (`meta` mode by default).
3. Generate all k-mer peptides from the protein set within `[min_pep_len, max_pep_len]`, deduplicating across proteins/entities and building the peptides and proteins_peptides association tables.
4. Split unique peptides into prediction chunks (`prediction_chunk_size`, capped by `max_task_num`) and report peptide/protein stats.
5. Run epitope prediction per chunk with the chosen `pred_method` (SYFPEITHI, MHCflurry, MHCnuggets class I, or MHCnuggets class II) via the Epytope framework, filtering to allele-length combinations actually supported by the method.
6. Merge prediction buffers into `predictions.tsv.gz` and join back through the data model to compute per-entity binding ratios and per-allele score distributions, weighted by contig/taxon abundance.
7. Render downstream plots (entity binding ratio boxplots per allele, prediction score violin plots per allele) and a MultiQC report.

## Key parameters
- `--input` samplesheet CSV with columns `condition,type,microbiome_path,alleles,weights_path`; `type` is one of `taxa|assembly|bins`; `alleles` is a space-separated list like `A*01:01 B*07:02`.
- `--pred_method` one of `syfpeithi` (default, PSSM, class I), `mhcflurry` (class I, ML), `mhcnuggets-class-1`, `mhcnuggets-class-2` (class II).
- `--min_pep_len` / `--max_pep_len` peptide length window (defaults 9 and 11). Pipeline auto-reduces to lengths supported by the chosen method+allele unless `--allow_inconsistent_pep_lengths` is set (SYFPEITHI only).
- `--syfpeithi_score_threshold` binder cutoff (default 0.5); `--mhcflurry_mhcnuggets_score_threshold` (default 0.426 ≈ IC50 500 nM).
- `--prodigal_mode` `meta` (default, for mixed communities) vs `single` (single isolate).
- `--prediction_chunk_size` (default 4,000,000 peptides) and `--downstream_chunk_size` (default 7,500,000) - reduce if memory is tight (full-size runs can peak around 150 GB).
- `--show_supported_models` run-only-this flag that dumps each predictor's supported alleles and lengths and exits; use before composing the samplesheet.
- Nextflow secrets `NCBI_EMAIL` and `NCBI_KEY` are required whenever any row has `type: taxa`.

## Test data
The bundled `test` profile uses a samplesheet from `nf-core/test-datasets/metapep/samplesheets/v1.0/samplesheet.csv` that mixes several small conditions: taxa-based entries (tiny taxid lists scored against HLA-A*01:01 and B*07:02) and an assembly-based entry (`test_minigut.contigs.fa.gz` with per-contig weights). Because the taxa rows hit Entrez, this profile needs valid `NCBI_EMAIL` / `NCBI_KEY` secrets; a second `test_assembly_only` profile runs the assembly path alone for CI without credentials. A successful run populates `db_tables/` (conditions, alleles, entities, proteins, peptides, proteins_peptides, predictions), writes per-allele `entity_binding_ratios.*.pdf` and `prediction_score_distribution.*.pdf` into `figures/`, and produces a MultiQC report under `multiqc/`. The `test_full` profile swaps in a full-size assembly samplesheet and switches `pred_method` to `mhcflurry`.

## Reference workflow
nf-core/metapep v1.0.0 (https://github.com/nf-core/metapep), MIT licensed. Citation: Zenodo DOI 10.5281/zenodo.14202996. Core tooling: Prodigal, Entrez, Epytope (FRED2), SYFPEITHI, MHCflurry, MHCnuggets.
