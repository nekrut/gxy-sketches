---
name: long-read-genome-assembly
description: Use when you need to de novo assemble a haploid or inbred-diploid eukaryotic/small
  genome from long reads (Oxford Nanopore and/or PacBio HiFi), with optional polishing,
  scaffolding against a reference, annotation liftover, and assembly QC. Not for polyploid
  phasing or HiC scaffolding.
domain: assembly
organism_class:
- eukaryote
- haploid
- diploid-inbred
input_data:
- long-reads-ont
- long-reads-hifi
- short-reads-paired
- reference-fasta
- reference-gff
source:
  ecosystem: nf-core
  workflow: nf-core/genomeassembler
  url: https://github.com/nf-core/genomeassembler
  version: 1.1.0
  license: MIT
tools:
- flye
- hifiasm
- medaka
- pilon
- ragtag
- links
- longstitch
- busco
- quast
- merqury
- minimap2
- liftoff
- porechop
- lima
- trimgalore
- jellyfish
- genomescope2
- nanoq
tags:
- long-read
- ont
- pacbio
- hifi
- de-novo-assembly
- polishing
- scaffolding
- annotation-liftover
test_data: []
expected_output: []
---

# Long-read genome assembly (ONT / PacBio HiFi)

## When to use this sketch
- User wants a de novo genome assembly from long reads: Oxford Nanopore (ONT) and/or PacBio HiFi.
- Target genome is haploid, inbred/homozygous diploid, or a non-phased draft of a small/medium eukaryote or prokaryote.
- User wants an end-to-end recipe: read QC, assembly, optional polishing, optional scaffolding against a closely related reference, optional annotation liftover, and assembly QC (BUSCO / QUAST / merqury).
- User may have a closely related reference genome (FASTA + GFF) to scaffold onto and lift annotations from.
- User may have Illumina short reads to use for polishing (pilon) and/or k-mer-based QC (merqury).

## Do not use when
- You need phased, haplotype-resolved assembly of an outbred diploid or polyploid — this pipeline explicitly does not phase polyploids. Prefer a dedicated trio/HiC phasing workflow.
- You need HiC-based scaffolding — not implemented here; use an HiC scaffolding pipeline (e.g. SALSA/YaHS).
- You only have Illumina short reads — use a short-read assembler (SPAdes / Unicycler) instead.
- You want bacterial hybrid short+long assembly with annotation — prefer a dedicated bacterial assembly pipeline (e.g. nf-core/bacass).
- You want metagenome-assembled genomes — use a metagenomics assembly workflow (metaFlye + binning).
- Your task is variant calling against an existing reference rather than building a new assembly — use a variant-calling sketch.

## Analysis outline
1. Parse samplesheet (one row per sample) with ONT reads, HiFi reads, optional reference FASTA/GFF, and optional paired short reads.
2. ONT read prep: optionally concatenate multi-file runs (`collect`), adapter-trim with `porechop`, QC with `nanoq`, estimate genome size/ploidy via `jellyfish` k-mer counts → `genomescope2`.
3. HiFi read prep: optionally adapter-trim with `lima` using provided PacBio primer FASTA.
4. Short read prep (if provided): trim with `TrimGalore`, build k-mer db with `meryl` for merqury.
5. Assembly: run `flye` (ONT or HiFi), or `hifiasm` (HiFi, optionally with `--ul` integrating ONT), or run both and scaffold one onto the other with `ragtag` (`flye_on_hifiasm` / `hifiasm_on_hifiasm`).
6. Polishing (optional): `medaka` using the ONT reads (for ONT-containing assemblies) and/or `pilon` using short-read alignments.
7. Scaffolding (optional): long-read scaffolding with `LINKS` and/or `longstitch` (tigmint + ntLink + ARKS); reference-guided scaffolding with `RagTag` if a reference FASTA is given.
8. Annotation liftover (optional): `liftoff` carries the reference GFF across to the new assembly after each stage (assembly / polish / scaffold).
9. QC at every stage: `QUAST` (contiguity), `BUSCO` against the chosen lineage, `merqury` QV from short-read k-mers, plus read-to-assembly alignments via `minimap2` + `samtools`.
10. Aggregate all QC into a per-run HTML report under `report/`.

## Key parameters
- `input` — samplesheet CSV with columns `sample,ontreads,hifireads,ref_fasta,ref_gff,shortread_F,shortread_R,paired`.
- `ont` / `hifi` / `short_reads` — booleans declaring which read types are present.
- `assembler` — one of `flye`, `hifiasm`, `flye_on_hifiasm`, `hifiasm_on_hifiasm`. Default `flye`. Pre-set profiles `ont_flye`, `hifi_flye`, `ont_hifiasm`, `hifi_hifiasm`, `hifiont_hifiasm`, `hifiont_flye_on_hifiasm`, `hifiont_hifiasm_on_hifiasm` bundle sensible combinations.
- `flye_mode` — `--nano-hq` (default), `--nano-raw`, `--nano-corr`, `--pacbio-raw`, `--pacbio-corr`, `--pacbio-hifi`. Pick based on chemistry / basecaller.
- `hifiasm_ont` / `hifiasm_args` — enable `hifiasm --ul` for ONT ultralong integration; pass extra args (e.g. `-f 0` for tiny test data).
- `genome_size` — expected size in bp; required by some downstream tools and helpful for flye.
- `kmer_length` (default 21) for jellyfish; `meryl_k` (default 21) for merqury.
- `polish_medaka` / `medaka_model` — enable medaka polishing and pick the basecaller-matched model.
- `polish_pilon` — enable pilon; requires `short_reads=true`.
- `scaffold_links` / `scaffold_longstitch` / `scaffold_ragtag` — toggle scaffolders; `scaffold_ragtag` requires a reference.
- `use_ref` (default true), `lift_annotations` (default true) — control reference-guided scaffolding and liftoff.
- `busco` (default true), `busco_lineage` (default `brassicales_odb10`), `busco_db` (optional local DB path), `quast` (default true), `merqury` (default true, short reads required).
- `qc_reads` — `ONT` or `HIFI`, which long reads to use for alignment-based QC when both are present.
- `skip_assembly` — run QC only on a pre-existing `assembly` column in the samplesheet.

## Test data
The pipeline's `test` profile pulls a minimal samplesheet from nf-core/test-datasets (`genomeassembler/samplesheet/test_samplesheet.csv`) containing one sample with both ONT and HiFi reads against a ~2 Mb target (`genome_size = 2000000`), running `assembler = flye_on_hifiasm` with `hifiasm_args = "-f 0"` and BUSCO/QUAST/jellyfish disabled for speed. Expected outputs per sample include a flye assembly FASTA, a hifiasm primary contig FASTA, and a RagTag scaffolded FASTA/AGP under `<sample>/assembly/`. The `test_full` profile adds medaka + pilon polishing, LINKS/longstitch/RagTag scaffolding, short reads, and full BUSCO/QUAST/merqury QC, producing polished assemblies under `polish/`, scaffolded assemblies under `scaffold/`, per-stage QUAST/BUSCO/merqury reports under `QC/`, and an aggregated `report/report.html`.

## Reference workflow
nf-core/genomeassembler v1.1.0 — https://github.com/nf-core/genomeassembler (DOI 10.5281/zenodo.14986998). See `docs/usage.md` for samplesheet format and `docs/output.md` for the full output tree.
