---
name: low-coverage-genotype-imputation-human
description: "Use when you need to impute genotypes for low-pass (\u22480.1x\u2013\
  1x) short-read human (or other diploid vertebrate) sequencing samples against a\
  \ phased reference panel such as 1000 Genomes. Covers panel preparation, chunked\
  \ imputation with GLIMPSE/QUILT/STITCH/Beagle5/Minimac4, and optional concordance\
  \ validation against a truth VCF."
domain: variant-calling
organism_class:
- vertebrate
- diploid
- human
input_data:
- short-reads-aligned-bam-cram
- reference-fasta
- phased-reference-panel-vcf
source:
  ecosystem: nf-core
  workflow: nf-core/phaseimpute
  url: https://github.com/nf-core/phaseimpute
  version: 1.1.0
  license: MIT
tools:
- glimpse1
- glimpse2
- quilt
- stitch
- beagle5
- minimac4
- shapeit5
- bcftools
- samtools
tags:
- imputation
- phasing
- low-pass
- low-coverage
- reference-panel
- glimpse
- quilt
- stitch
- 1000G
- diploid
test_data: []
expected_output: []
---

# Low-coverage genotype imputation against a phased reference panel

## When to use this sketch
- You have low-pass whole-genome sequencing (typically 0.1x–1x, up to ~4x) of diploid samples aligned as BAM/CRAM and want dense, phased genotype calls across the genome.
- A phased population reference panel is available (e.g. 1000 Genomes Phase 3, HRC, TOPMed) as per-chromosome VCF.gz + index, or you need the pipeline to phase/normalize it first with SHAPEIT5 + bcftools.
- You want parallel chunk-wise imputation over chromosomes with one of: GLIMPSE1, GLIMPSE2, QUILT, STITCH, BEAGLE5, or Minimac4, followed by per-sample ligation into a single VCF.
- You optionally want to benchmark imputation accuracy by downsampling high-coverage samples (`--steps simulate`) and/or running GLIMPSE2 concordance against a truth VCF (`--steps validate`).
- Target organism is human or another diploid vertebrate (dog test profile is shipped); polyploid / bacterial / viral data are out of scope.

## Do not use when
- You need *de novo* variant calling from high-coverage data — use a germline short-variant calling sketch (e.g. nf-core/sarek) instead.
- Your organism is haploid bacterial/viral — use a haploid variant-calling sketch.
- You only need statistical phasing of already-called dense genotypes with no imputation — use a pure SHAPEIT/Beagle phasing sketch.
- You are working with single-cell or long-read (ONT/PacBio) data as primary input; this pipeline expects short-read BAM/CRAM (or pre-called VCF/BCF for GLIMPSE/BEAGLE/Minimac4).
- You want genotype imputation from SNP array intensity/genotype data only without the low-pass sequencing workflow — BEAGLE5 supports this path but other tools here assume read-level input.

## Analysis outline
1. **Contig QC (`CHECKCHR`)**: validate that contig names in `--input`, `--input_truth`, `--panel`, `--posfile`, `--chunks`, `--map`, and `--fasta` are consistent; optionally rename (`--rename_chr`).
2. **Panel preparation (`--steps panelprep`)**: normalize the reference panel and drop multiallelic sites with `bcftools norm`; optionally strip related/benchmark samples (`--remove_samples`); optionally recompute AC/AN with `vcffixup` (`--compute_freq`); optionally phase with SHAPEIT5 (`--phase`).
3. **Panel conversion & chunking**: emit sites VCF with `bcftools query`, `.hap`/`.legend`/`.samples` with `bcftools convert --haplegendsample`, and genomic chunks with `GLIMPSE1_CHUNK` / `GLIMPSE2_CHUNK` (default 4 Mb windows).
4. **Optional simulation (`--steps simulate`)**: downsample high-coverage BAM/CRAM to target `--depth` with `samtools view -s` to build synthetic low-pass inputs and a matching truth VCF.
5. **Imputation (`--steps impute --tools ...`)**: run GLIMPSE1/GLIMPSE2/QUILT/STITCH/BEAGLE5/Minimac4 per chunk per sample (or per `--batch_size` batch); GLIMPSE1 uses `bcftools mpileup` to derive GLs from BAM/CRAM when needed.
6. **Ligation & concat**: stitch imputed chunks back together with GLIMPSE ligate / `bcftools concat` to produce one phased VCF per sample and one concatenated VCF per batch, plus `bcftools stats`.
7. **Validation (`--steps validate`)**: compute imputation accuracy per allele-frequency bin with `GLIMPSE2_CONCORDANCE` against a truth VCF (or BAM/CRAM+legend), aggregated across samples/tools, reported through MultiQC.

## Key parameters
- `--steps {simulate,panelprep,impute,validate,all}`: pick which phases to run; can be comma-combined (e.g. `panelprep,impute`).
- `--input samplesheet.csv`: columns `sample,file,index`; file is BAM/CRAM (all tools) or VCF/BCF (GLIMPSE1/2, BEAGLE5, Minimac4 only). QUILT/STITCH require BAM/CRAM.
- `--panel panel.csv`: columns `panel,chr,vcf,index`; per-chromosome phased reference panel (required for GLIMPSE1/2, BEAGLE5, Minimac4, and for `panelprep`).
- `--posfile posfile.csv`: columns include `panel,chr` plus `legend`/`hap`/`vcf` depending on tool — `legend` for GLIMPSE1/STITCH, `hap`+`legend` for QUILT, `vcf`+`index` for Minimac4 and validation.
- `--chunks chunks.csv`: columns `panel,chr,file` with GLIMPSE-style chunk TXT; required for GLIMPSE1, GLIMPSE2, QUILT.
- `--tools glimpse1|glimpse2|quilt|stitch|beagle5|minimac4` (comma-separated list allowed).
- `--genome GRCh38` *or* `--fasta` (+optional `--fasta_fai`): mandatory reference.
- `--map`: optional genetic map for recombination-aware imputation.
- Panelprep switches: `--normalize` (default true), `--phase`, `--compute_freq`, `--remove_samples NA12878,NA12891,...`, `--rename_chr`.
- `--depth` (simulate mode, default 1x) and `--genotype` truth samplesheet.
- `--batch_size` (default 100): samples per imputation batch; GLIMPSE1 and STITCH always process all samples jointly regardless.
- QUILT: `--buffer` (default 10000), `--ngen` (default 100). STITCH: `--k_val` K ancestral haplotypes (default 2). `--seed` (default 1) for STITCH/QUILT.
- Validation: `--input_truth`, `--bins "0 0.01 0.05 0.1 0.2 0.5"`, `--min_val_gl` (default 0.9), `--min_val_dp` (default 5).
- Chunk window size is tuned via process-level `ext.args` on `GLIMPSE_CHUNK`/`GLIMPSE2_CHUNK` (default `--window-size 4000000` / `--window-mb 4`).

## Test data
The default `-profile test` uses a tiny human-derived dataset shipped from nf-core/test-datasets (`phaseimpute` branch): a samplesheet of BAM inputs (`tests/csv/sample_bam.csv`), a small phased 1000GP-style reference panel restricted to chr21/chr22 (`tests/csv/panel.csv`), a region CSV, a GLIMPSE1 chunks CSV, a legend-style posfile, and a downsampled GRCh38 FASTA + `.fai`. It runs only `--steps impute --tools glimpse1` and is expected to finish in minutes on 4 CPU / 4 GB, producing per-sample imputed `vcf.gz` files under `imputation/glimpse1/samples/`, batch-concatenated VCFs under `imputation/glimpse1/concat/`, `bcftools stats` summaries, and a MultiQC report. Sibling profiles (`test_glimpse2`, `test_quilt`, `test_stitch`, `test_beagle5`, `test_minimac4`, `test_panelprep`, `test_sim`, `test_validate`, `test_batch`, `test_dog`, `test_all`, `test_all_fullchr`) exercise the other tools and steps; `test_full` runs all steps end-to-end on full chr21/chr22 with GLIMPSE2 against a 1000G-derived panel with NA12878/NA12891/NA12892 removed.

## Reference workflow
nf-core/phaseimpute v1.1.0 (MIT) — https://github.com/nf-core/phaseimpute. Cite via DOI 10.5281/zenodo.14329225 and the tool papers for GLIMPSE, GLIMPSE2, QUILT, STITCH, SHAPEIT5, BEAGLE5, Minimac4, and bcftools listed in the pipeline `CITATIONS.md`.
