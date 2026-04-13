---
name: hic-pretext-contact-map-assembly-curation
description: Use when you need to build a Hi-C contact map in Pretext format for manual
  curation of a genome assembly (one or two haplotypes) with annotation tracks for
  PacBio HiFi coverage, assembly gaps, telomeres, and optional gene completeness.
  Produces .pretext files openable in PretextView.
domain: assembly
organism_class:
- eukaryote
- vertebrate
- diploid
input_data:
- assembly-fasta
- hi-c-paired-reads
- pacbio-hifi-reads
source:
  ecosystem: iwc
  workflow: PretextMap Generation from 1 or 2 haplotypes
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/VGP-assembly-v2/hi-c-contact-map-for-assembly-manual-curation
  version: '2.3'
  license: MIT
tools:
- bwa-mem2
- samtools
- pairtools
- pretextmap
- pretextgraph
- pretextsnapshot
- teloscope
- compleasm
- minimap2
- gfastats
- cutadapt
- multiqc
tags:
- hi-c
- pretext
- scaffolding
- manual-curation
- vgp
- contact-map
- telomere
- coverage
test_data:
- role: haplotype_1
  url: https://zenodo.org/records/18664706/files/Haplotype_1.fasta
  sha1: a0ee25fd9f7cf223ca40ff530e1201589fade212
  filetype: fasta
- role: haplotype_2
  url: https://zenodo.org/records/18664706/files/Haplotype_2.fasta
  sha1: 166cb118625113e39593bedb10aaea028c20f77d
  filetype: fasta
- role: hi_c_reads__hi_c_set_1__forward
  url: https://zenodo.org/records/18664706/files/HiC_forward_1.fastqsanger.gz
  sha1: 2dafed5cc07885dfe59c8a85311dfb4343deb9c3
- role: hi_c_reads__hi_c_set_1__reverse
  url: https://zenodo.org/records/18664706/files/HiC_reverse_1.fastqsanger.gz
  sha1: 3c31935d0d706a62ecc1f82f27ee01c402e64416
- role: pacbio_reads__pacbio_set_1
  url: https://zenodo.org/records/18664706/files/PacBio_reads_1.fastq.gz
  sha1: 84fe8fad10155f9edd1365ba13bb5f30f0d1d881
expected_output:
- role: assembly_for_curation
  description: Content assertions for `Assembly for curation`.
  assertions:
  - 'has_text: >scaffold_10.H1'
- role: gaps_bed
  description: Content assertions for `Gaps Bed`.
  assertions:
  - 'has_text: scaffold_10.H1'
- role: telomere_report
  description: Content assertions for `Telomere Report`.
  assertions:
  - 'has_text: scaffold_10.H1'
- role: gaps_bedgraph
  description: Content assertions for `Gaps Bedgraph`.
  assertions:
  - 'has_text: scaffold_10.H1'
- role: bigwig_coverage
  description: Content assertions for `BigWig Coverage`.
  assertions:
  - 'has_size: {''value'': 10000, ''delta'': 5000}'
- role: p_telomeres_bed
  description: Content assertions for `P telomeres bed`.
  assertions:
  - "has_text: scaffold_1.H1\t488600\t500600\t12000"
- role: pretext_all_tracks
  description: Content assertions for `Pretext All tracks`.
  assertions:
  - 'has_size: {''value'': 1000000, ''delta'': 500000}'
- role: pretext_all_tracks_multimapping
  description: Content assertions for `Pretext All tracks - Multimapping`.
  assertions:
  - 'has_size: {''value'': 800000, ''delta'': 400000}'
- role: hi_c_duplication_stats_on_scaffolds_raw
  description: 'Content assertions for `Hi-C duplication stats on Scaffolds: Raw`.'
  assertions:
  - "has_text: total_dups\t3941"
- role: precuration_hi_c_alignments
  description: Content assertions for `Precuration Hi-C alignments`.
  assertions:
  - 'has_size: {''value'': 7427810, ''delta'': 50000}'
- role: hi_c_duplication_stats_on_scaffolds
  description: Content assertions for `Hi-C duplication stats on Scaffolds`.
  assertions:
  - 'has_text: EXCLUDED: 1042'
---

# Hi-C Pretext contact map for assembly manual curation

## When to use this sketch
- You have a draft genome assembly (one haplotype or a diploid pair of haplotypes as FASTA) and need a Pretext contact map for manual curation in PretextView.
- You have paired-end Hi-C reads (Illumina, e.g. Arima/OmniC) and PacBio HiFi reads for the same sample.
- You want annotation tracks overlaid on the Hi-C map: PacBio coverage, coverage gaps, assembly gaps, telomere (P/Q arm) positions, and optionally Compleasm gene completeness.
- You want both MAPQ-filtered and unfiltered (multimapping) versions of the Pretext map to assess ambiguous contacts.
- This is part of a VGP-style assembly pipeline, between scaffolding and curation.

## Do not use when
- You only need a plain Hi-C scaffolding step (use a dedicated YaHS / SALSA / 3D-DNA scaffolding sketch instead).
- You want to call structural variants or phase variants from Hi-C (use an SV or phasing sketch).
- You have no Hi-C data — this workflow is specifically for producing Pretext contact maps.
- You are working on bacterial or viral genomes; this pipeline assumes large eukaryotic (typically vertebrate) assemblies with telomeres, BUSCO lineages, and HiFi coverage.
- You want full de novo assembly from reads — use a VGP contigging / HiFi assembly sketch first and feed its output here.

## Analysis outline
1. Optionally add haplotype suffixes (e.g. `.H1`, `.H2`) to scaffold names in each haplotype FASTA using Replace Text, then concatenate Hap1+Hap2 into a single curation FASTA.
2. Compute assembly summary with gfastats.
3. (Optional) Trim 5 bp from Hi-C reads with Cutadapt (for noisy Arima data); index the merged assembly with bwa-mem2.
4. Align Hi-C paired reads with bwa-mem2 using Hi-C options (`-5 -S -P -T 30`), then Samtools fixmate + sort, and Samtools merge across read sets.
5. Run pairtools parse → pairtools dedup to get duplication stats; optionally Samtools markdup to remove PCR duplicates; summarize with MultiQC.
6. (Optional) Trim HiFi adapters with Cutadapt; align HiFi reads to the merged assembly with minimap2 (map-hifi), merge BAMs with Samtools merge.
7. Compute PacBio coverage BigWig and a low-coverage "coverage gaps" bedgraph from the HiFi BAM.
8. Detect telomeres with Teloscope using canonical + custom IUPAC patterns; split into P-arm and Q-arm BEDs.
9. Extract assembly gaps to BED/bedgraph from the merged FASTA.
10. (Optional) Run Compleasm with a chosen BUSCO lineage to produce a gene-completeness GFF track.
11. Build Pretext contact maps with PretextMap twice: once with MAPQ filtering (default ≥10) and once unfiltered (multimapping).
12. Inject all tracks (coverage, coverage gaps, assembly gaps, telomeres P/Q, genes) into both Pretext maps with PretextGraph, and render PNG previews with PretextSnapshot.

## Key parameters
- `Will you use a second haplotype?`: true for diploid, false for single-haplotype curation.
- `Do you want to add suffixes to the scaffold names?` with `First/Second Haplotype suffix` (defaults `H1`, `H2`) — required when scaffold names don't already encode haplotype.
- `Minimum Mapping Quality` for filtered PretextMap (default `10`; set to `0` to keep all mapped Hi-C contacts).
- `Do you want to trim the Hi-C data?`: enable (trims 5 bp) for Arima Hi-C if the map looks noisy.
- `Remove duplicated Hi-C reads?`: true uses Samtools markdup with `remove=true` on the merged Hi-C BAM.
- `Remove adapters from HiFi reads?`: runs Cutadapt against PacBio adapter sequences; leave off if HiFi was already trimmed upstream.
- `Canonical telomeric pattern` (default `TTAGGG`) and `Telomeric Patterns to explore` (default `TTAGGG,CCCTAA`, IUPAC allowed) for Teloscope.
- `Generate gene annotations` + `Lineage for Compleasm` (e.g. `vertebrata_odb10`, `primates_odb10`, `aves_odb10`) and `Database for Compleasm` (default `v5`); disable for very large genomes that OOM.
- `Generate high resolution Hi-C maps`: enables high-res PretextMap (slower, more RAM).
- `Bin Size for Bigwig files` (default `100`) controls coverage track resolution.
- bwa-mem2 Hi-C alignment flags: `-5 -S -P -T 30` (used internally).
- pairtools parse `min_mapq=1`, `max_molecule_size=2000`, `walks_policy=mask`.

## Test data
The source workflow ships a planemo test profile hosted on Zenodo record 18664706 with two haplotype FASTAs (`Haplotype_1.fasta`, `Haplotype_2.fasta`), one paired Hi-C set (`HiC_forward_1` / `HiC_reverse_1`, fastqsanger.gz), and one PacBio HiFi set (`PacBio_reads_1.fastq.gz`). Scaffolds are renamed with `H1`/`H2` suffixes, Hi-C trimming is disabled, duplicate removal is enabled, Compleasm gene annotation is disabled, and MAPQ filter is 10 with telomere patterns `TTAGGG,CCCTAA`. Running the workflow is expected to produce a merged `Assembly for curation` FASTA containing `>scaffold_10.H1`, assembly `Gaps Bed`/`Gaps Bedgraph` and `Telomere Report` entries on `scaffold_10.H1`, a `P telomeres bed` line `scaffold_1.H1\t488600\t500600\t12000`, a `BigWig Coverage` file (~10 kB ±5 kB), a precuration Hi-C BAM (~7.4 MB), `Pretext All tracks` (~1 MB ±500 kB) and `Pretext All tracks - Multimapping` (~800 kB ±400 kB) files, and Hi-C duplication stats reporting `total_dups\t3941` and `EXCLUDED: 1042`. A second test variant adds a `Hi-C_set_2` + `PacBio_set_2` collection and enables Compleasm to additionally assert a `Compleasm Genes track` entry on `scaffold_1.H2`.

## Reference workflow
Galaxy IWC `VGP-assembly-v2/hi-c-contact-map-for-assembly-manual-curation` — *PretextMap Generation from 1 or 2 haplotypes*, version 2.3 (MIT), by Patrik Smeds and Delphine Lariviere.
