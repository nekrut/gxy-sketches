---
name: functional-annotation-protein-dna-sequences
description: "Use when you need to assign functional annotations (GO terms, KEGG orthologs,\
  \ InterPro domains, EC numbers, pathway membership) to protein or nucleotide sequences\
  \ \u2014 including predicted proteins, CDS, whole genomes, or metagenomic contigs\
  \ \u2014 and optionally assess KEGG pathway completeness. Works on any organism\
  \ and supports batched collections of FASTA inputs."
domain: annotation
organism_class:
- eukaryote
- bacterial
- viral
- metagenome
input_data:
- protein-fasta
- nucleotide-fasta
- fasta-collection
source:
  ecosystem: iwc
  workflow: Functional annotation of sequences
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/genome_annotation/functional-annotation/functional-annotation-of-sequences
  version: '0.3'
  license: MIT
tools:
- eggnog-mapper
- interproscan
- kegg-pathways-completeness
- prodigal
- diamond
tags:
- functional-annotation
- go-terms
- kegg
- interpro
- orthology
- pathway-completeness
- metagenomics
test_data:
- role: sequence_collection__test_sequence
  url: https://zenodo.org/record/8414802/files/protein_sequences.fasta
  sha1: 0e1026d6917ac03bcd174a85b18e69c2a6470f98
  filetype: fasta
expected_output:
- role: kegg_pathways_table
  description: Content assertions for `kegg pathways table`.
  assertions:
  - 'that: has_text'
  - "text: module_accession\tcompleteness\tpathway_name\tpathway_class\tmatching_ko\t\
    missing_ko"
- role: kegg_contig_table
  description: Content assertions for `kegg contig table`.
  assertions:
  - 'that: has_text'
  - "text: contig\tmodule_accession\tcompleteness\tpathway_name\tpathway_class\tmatching_ko\t\
    missing_ko"
---

# Functional annotation of protein or nucleotide sequences

## When to use this sketch
- You have FASTA sequences (proteins, CDS, a whole genome, or metagenomic contigs/bins) and need functional annotation: GO terms, KEGG KOs, EC numbers, InterPro domains, Pfam/PANTHER/SUPERFAMILY signatures.
- You want orthology-based annotation via eggNOG-mapper and/or domain/signature scanning via InterProScan, and can mix-and-match either or both.
- You need KEGG pathway completeness estimates from the KOs recovered by eggNOG (useful for MAGs, bins, or draft genomes).
- Input comes as a Galaxy-style collection so multiple samples/bins run in parallel.
- The organism is arbitrary — eukaryote, prokaryote, viral, or mixed community.

## Do not use when
- You need structural annotation (gene calling, CDS/tRNA/rRNA prediction, GFF production) — use a structural-annotation sketch (e.g. Prokka/Bakta for bacteria, MAKER/Funannotate for eukaryotes) first, then feed predicted proteins here.
- You only want taxonomic profiling of a metagenome — use a metagenomic-profiling sketch instead.
- You need variant-level annotation (e.g. SnpEff on VCFs) — that is a different class.
- You want homology search against a custom BLAST database — use a dedicated BLAST/DIAMOND sketch.

## Analysis outline
1. Accept a Galaxy collection of FASTA files and choose sequence type: `proteins`, `CDS`, `genome`, or `metagenome`.
2. For `genome`/`metagenome` inputs, eggNOG-mapper internally calls Prodigal to predict genes before DIAMOND search.
3. Run **eggNOG-mapper 2.1.13** (DIAMOND, sensitive mode, eggNOG 5.0.2) to produce seed orthologs and per-gene annotation tables (GO, KEGG KO, EC, COG, predicted name).
4. Optionally run **InterProScan 5.59-91.0** on the same collection against a broad set of member databases (Pfam, PANTHER, SUPERFAMILY, TIGRFAM, Gene3D, Hamap, PRINTS, SMART, CDD, PROSITE profiles/patterns, PIRSF/PIRSR, MobiDBLite, SFLD, FunFam, AntiFam, Coils), emitting TSV + XML with GO terms and pathway cross-refs.
5. Extract the KEGG KO column (column 12) from the eggNOG annotations, drop empty (`-`) rows, split comma-separated KOs and strip the `ko:` prefix with awk.
6. Collapse per-sample KO lists and paste them against collection element identifiers to build a contig/sample → KO table.
7. Run **KEGG Pathways Completeness 1.3.0** on that table to produce a per-module completeness table and a per-contig pathway table.

## Key parameters
- `eggNOG mode select`: one of `proteins` | `CDS` | `genome` | `metagenome` — must match the input FASTA semantics. `genome`/`metagenome` trigger Prodigal gene prediction.
- `InterProScan mode select`: `Protein` or `DNA/RNA` (mapped to `-t p` or `-t n`).
- eggNOG-mapper: `m=diamond`, `sensmode=sensitive`, `seed_ortholog_evalue=0.001`, `matrix=BLOSUM62`, `gap_costs=--gapopen 11 --gapextend 1`, `go_evidence=non-electronic`, `target_orthologs=all`, `eggnog_data=5.0.2`.
- InterProScan: `database=5.59-91.0`, `goterms=true`, `pathways=true`, `oformat=[TSV, XML]`, licensed databases off.
- KEGG pathways completeness: input is the KO table; per-contig output enabled (`m=true`).
- Toggles: `Run eggNOG + completeness calculation` (bool) and `Run InterProScan` (bool) let each branch be skipped independently.

## Test data
The primary test uses a Galaxy list collection with a single protein FASTA (`test-sequence`, downloaded from Zenodo record 8414802 `protein_sequences.fasta`, SHA-1 `0e1026d6917ac03bcd174a85b18e69c2a6470f98`), with `eggNOG mode=proteins`, `InterProScan mode=Protein`, and both branches enabled. Expected outputs are an InterProScan TSV and XML (compared by approximate size against reference files on Zenodo 13951790), plus a `kegg pathways table` and `kegg contig table` that must contain the canonical headers `module_accession\tcompleteness\tpathway_name\tpathway_class\tmatching_ko\tmissing_ko` and `contig\tmodule_accession\t...`. A secondary metagenome test runs two binette MAG FASTAs (`50contig_reads_binette_bin1/2.fasta` from Zenodo 18635101) with `eggNOG mode=metagenome`, InterProScan disabled, and asserts the KEGG tables have the expected headers and roughly 4 lines. A third test exercises InterProScan-only mode on the protein FASTA.

## Reference workflow
Galaxy IWC `genome_annotation/functional-annotation/functional-annotation-of-sequences`, release 0.3 (MIT), by Romane Libouban and Anthony Bretaudeau (IRISA). Core tools: eggNOG-mapper 2.1.13+galaxy0, InterProScan 5.59-91.0+galaxy3, kegg_pathways_completeness 1.3.0+galaxy0.
