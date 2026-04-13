---
name: mitogenome-assembly-pacbio-hifi
description: Use when you need to assemble and annotate a mitochondrial genome from
  PacBio HiFi long reads for a eukaryotic species (animal/vertebrate/invertebrate).
  MitoHiFi automatically fetches a close reference mitogenome from NCBI given only
  the species Latin name, then assembles and annotates the organelle genome.
domain: assembly
organism_class:
- eukaryote
- vertebrate
- invertebrate
- animal
input_data:
- long-reads-pacbio-hifi
source:
  ecosystem: iwc
  workflow: Mitogenome Assembly VGP0
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/VGP-assembly-v2/Mitogenome-assembly-VGP0
  version: 0.2.2
  license: CC-BY-4.0
tools:
- mitohifi
- hifiasm
- mitofinder
- ncbi-entrez
tags:
- mitogenome
- organelle
- pacbio
- hifi
- vgp
- long-read
- annotation
test_data:
- role: collection_of_pacbio_data__pacbio_01_fasta_gz
  url: https://zenodo.org/records/10454765/files/pacbio_01.fasta.gz?download=1
  sha1: 2a202c392647de30904c8886bf42c0f948b28797
expected_output:
- role: mitogenome_contigs_statistics
  description: 'Content assertions for `Mitogenome: Contigs Statistics`.'
  assertions:
  - "has_text: 15316\t36\tTrue"
- role: mitogenome_coverage_image
  description: 'Content assertions for `Mitogenome coverage: Image`.'
  assertions:
  - 'has_size: {''value'': 19000, ''delta'': 2000}'
- role: mitogenome_annotation_image
  description: 'Content assertions for `Mitogenome annotation: Image`.'
  assertions:
  - 'has_size: {''value'': 68000, ''delta'': 5000}'
- role: mitogenome_annotation_genbank
  description: 'Content assertions for `Mitogenome annotation: GenBank`.'
  assertions:
  - 'has_n_lines: {''n'': 480}'
---

# Mitogenome assembly from PacBio HiFi reads

## When to use this sketch
- You have PacBio HiFi long reads for a eukaryote and want only the mitochondrial genome (not the nuclear assembly).
- You want automatic reference discovery: you provide the Latin species name and an email, and the workflow pulls a related mitogenome from NCBI.
- You need an annotated mitogenome (GenBank + annotation/coverage plots + contig stats) as a stand-alone product or as part of the VGP assembly suite.
- The target organism has a defined NCBI genetic code (e.g. 2 for vertebrate mitochondrial, 5 for invertebrate mitochondrial).

## Do not use when
- Input reads are Illumina short reads or Oxford Nanopore — MitoHiFi expects PacBio HiFi. For short-read mitogenome assembly, use a NOVOPlasty/GetOrganelle-style sketch instead.
- You want a full nuclear genome assembly — use the main VGP nuclear assembly sketches (e.g. VGP hifiasm/HiC workflows).
- You want a chloroplast/plastid assembly — MitoHiFi is mitochondrion-specific; use a plastid-specific tool.
- No related mitogenome exists in NCBI for the species and no manual reference is available — MitoHiFi's `find_reference` step will fail.

## Analysis outline
1. **Collect inputs** — species Latin name, assembly name label, HiFi FASTQ/FASTA collection, contact email (NCBI requirement), and NCBI genetic code.
2. **Find reference mitogenome** — run MitoHiFi in `find_reference` mode with the species name and email to retrieve a related mitogenome FASTA + GenBank from NCBI.
3. **Assemble and annotate** — run MitoHiFi in `mitohifi` mode on the PacBio HiFi reads using the fetched reference FASTA/GenBank; internally this runs hifiasm, filters mitochondrial contigs by BLAST against the reference, circularizes, and annotates with MitoFinder.
4. **Rename and tag outputs** — assign human-readable names to the contigs statistics table, coverage PNG, annotation PNG, and annotated GenBank.
5. **Compress** — gzip the final mitogenome FASTA for export.

## Key parameters
- `operation_mode: find_reference` for step 1; `operation_mode: mitohifi` for step 2.
- `input_option.input: pacbio` — tells MitoHiFi the reads are HiFi.
- `min_length: 15000` — minimum length of candidate reference mitogenome (find_reference step).
- `exact_species: false` — allow related species as reference fallback.
- `organism_selection: animal` — this sketch targets metazoans; use a plant profile elsewhere.
- `genetic_code` — NCBI translation table number; must match the organism (e.g. 2 = vertebrate mitochondrial, 5 = invertebrate mitochondrial).
- `query_blast: 70` — BLAST percent identity threshold for selecting mitochondrial contigs from the hifiasm assembly.
- `bloom_filter: 0` — disabled.
- `email` — a valid address is mandatory for NCBI Entrez queries.

## Test data
The source test profile uses a single PacBio HiFi read collection, `pacbio_01.fasta.gz`, hosted on Zenodo (record 10454765), for the hawkmoth *Theretra latreillii lucasii* with assembly label `MW539688`, genetic code `2`, and a placeholder email for the NCBI query. The run is expected to produce a contigs-statistics TSV containing the line `15316\t36\tTrue` (a ~15.3 kb circularized mitogenome with 36 features), a mitogenome coverage PNG of roughly 19 kB (±2 kB), a mitogenome annotation PNG of roughly 68 kB (±5 kB), and a GenBank annotation file of exactly 480 lines.

## Reference workflow
Galaxy IWC — VGP-assembly-v2 / Mitogenome-Assembly-VGP0, version 0.2.2 (CC-BY-4.0). Core tool: MitoHiFi 3.2.3+galaxy0 (bgruening toolshed repo).
