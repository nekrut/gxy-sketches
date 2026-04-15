---
name: dual-rnaseq-host-pathogen
description: Use when you need to simultaneously quantify host (eukaryotic) and pathogen
  (typically bacterial) gene expression from a single dual RNA-seq FASTQ dataset,
  producing per-organism count tables, TPMs, and RNA-class breakdowns after building
  a chimeric host+pathogen reference.
domain: rna-seq
organism_class:
- eukaryote
- bacterial
- mixed-host-pathogen
input_data:
- short-reads-paired
- short-reads-single
- host-fasta
- host-gff
- pathogen-fasta
- pathogen-gff
source:
  ecosystem: nf-core
  workflow: nf-core/dualrnaseq
  url: https://github.com/nf-core/dualrnaseq
  version: 1.0.0
  license: MIT
  slug: dualrnaseq
tools:
- name: fastqc
- name: bbduk
- name: cutadapt
- name: salmon
- name: star
- name: htseq
- name: tximport
- name: gffread
- name: multiqc
tags:
- dual-rnaseq
- host-pathogen
- infection
- chimeric-reference
- transcript-quantification
- bacterial-rnaseq
test_data: []
expected_output: []
---

# Dual RNA-seq (host + pathogen simultaneous quantification)

## When to use this sketch
- Reads come from an infection / co-culture experiment where a single FASTQ library contains RNA from BOTH a eukaryotic host (e.g. Human, Mouse) and a bacterial pathogen (e.g. *Salmonella*, *Chlamydia*, *M. leprae*, *E. coli*).
- You need per-organism gene/transcript counts, TPMs, and mapping statistics split cleanly between host and pathogen.
- You already have (or can point to) a host genome FASTA + GFF3 and a pathogen genome FASTA + GFF3; iGenomes is NOT used here and GTF is not accepted.
- You want a chimeric reference built automatically so that cross-mapping between host and pathogen is controlled.
- Either paired-end or single-end Illumina short reads; the whole library must be uniformly one or the other.

## Do not use when
- The sample is purely host RNA-seq with no pathogen component — use a standard bulk RNA-seq sketch (e.g. nf-core/rnaseq) instead.
- The sample is purely bacterial RNA-seq with no host — use a bacterial-only RNA-seq / prokaryote quantification sketch.
- You need variant calling, assembly, or metagenomic profiling of unknown pathogens — this pipeline quantifies against a known reference, it does not discover organisms.
- You need single-cell dual RNA-seq — this sketch is bulk-only.
- You only have GTF annotation and cannot convert to GFF3 — the pipeline requires GFF3 for both host and pathogen.

## Analysis outline
1. Raw read QC with FastQC.
2. Optional adapter/quality trimming with either Cutadapt (known adapters, e.g. TruSeq) or BBDuk (`$baseDir/data/adapters.fa`, quality-trim via `qtrim`/`trimq`).
3. Post-trim FastQC.
4. Build a chimeric host+pathogen reference: concatenate host and pathogen FASTA, merge and normalize GFF3 attributes/features; extract host and pathogen transcriptomes with gffread-style logic using the configured gene features and attributes.
5. Choose ONE of three quantification strategies (multiple can be run in the same invocation):
   - **Salmon selective alignment** (`--run_salmon_selective_alignment`): index the chimeric transcriptome with the host genome as decoy, then `salmon quant` directly from reads.
   - **STAR + Salmon alignment-based** (`--run_salmon_alignment_based_mode`): STAR aligns to the chimeric genome producing transcriptome BAMs, then `salmon quant --alignments`.
   - **STAR + HTSeq** (`--run_star --run_htseq_uniquely_mapped`): STAR genome alignment, then HTSeq-count on uniquely mapped reads against a chimeric GFF.
6. Summarize Salmon transcript estimates to host gene level with tximport.
7. Split quantification into per-organism tables (`host_quant.sf`/`pathogen_quant.sf`, `*_combined_quant_annotations.tsv`) and compute per-sample mapping statistics, replicate scatterplots, and RNA-class breakdowns when `--mapping_statistics` is set.
8. Aggregate all QC and tool logs with MultiQC.

## Key parameters
- `--input`: glob for FASTQ(.gz); paired-end must use `{1,2}` notation. `--single_end` flips to single-end mode (no mixing allowed).
- `--fasta_host`, `--gff_host`, optional `--gff_host_tRNA` — host reference; `--fasta_pathogen`, `--gff_pathogen` — pathogen reference. Alternatively use `--genome_host` / `--genome_pathogen` keyed into a `genomes.config` block (with `--genomes_ignore` when supplying your own).
- Mode switches (at least one required): `--run_salmon_selective_alignment`, `--run_salmon_alignment_based_mode`, `--run_star`, `--run_htseq_uniquely_mapped`.
- Trimming: `--run_cutadapt` (with `--a`, `--A`, `--quality_cutoff`) OR `--run_bbduk` (with `--qtrim`, `--trimq`, `--minlen`, `--adapters`). Off by default.
- Pathogen annotation knobs (critical — bacterial GFFs vary): `--gene_feature_gff_to_create_transcriptome_pathogen` (default `['gene','sRNA','tRNA','rRNA']`), `--gene_attribute_gff_to_create_transcriptome_pathogen` (default `locus_tag`), `--gene_feature_gff_to_quantify_pathogen`, `--pathogen_gff_attribute`. Inspect the GFF with `awk -F'\t' '{print $3}' file.gff3 | sort | uniq -c` first.
- Host annotation knobs: `--gene_feature_gff_to_create_transcriptome_host` (default `['exon','tRNA']`), `--gene_attribute_gff_to_create_transcriptome_host` (default `transcript_id`), `--host_gff_attribute` (default `gene_id`).
- Salmon: `--libtype` (use `A` to auto-detect, or stranded codes like `ISF`/`SF`/`IU`), `--incompatPrior 0.0`, `--kmer_length` (default 21, drop to ~19 for short reads), `--keepDuplicates`, `--generate_salmon_uniq_ambig`.
- STAR: `--sjdbOverhang` (set to read length − 1), `--outFilterMultimapNmax`, `--alignIntronMin/Max`, `--quantTranscriptomeBan Singleend` (required for Salmon alignment-based transcriptome BAMs).
- HTSeq: `--stranded` (`yes`/`no`/`reverse`), `--minaqual 10`.
- `--mapping_statistics` to emit per-sample plots/tables and `--rna_classes_to_replace_host` to group host RNA biotypes.

## Test data
The bundled `test` profile (`conf/test.config`) runs three paired-end samples (`sample_R1`, `sample_R2`, `sample_R3`) from the `nf-core/test-datasets` dualrnaseq branch, against a subset Human GRCh38 host (`GRCh38.p13_sub.fasta` + `Human_gencode.v33_sub.gff3`) and a subset *Salmonella* Typhimurium SL1344 pathogen (`SL1344_sub.fasta` + `SL1344_sub.gff3`). It enables BBDuk trimming (`qtrim=rl`), Salmon selective alignment (`libtype=ISF`), and `mapping_statistics=true`. Expected outputs include per-sample Salmon quant directories under `results/salmon/<sample>/`, combined `host_quant_salmon.tsv` and `pathogen_quant_salmon.tsv`, a `host_combined_gene_level.tsv` from tximport, mapping-statistic TSVs/PDFs under `results/mapping_statistics/salmon/`, and a MultiQC HTML report. The `test_full` profile additionally exercises single-end mode on three HUVEC Karp (*Orientia tsutsugamushi*) libraries with pathogen features `[CDS,tRNA,rRNA,ncRNA]` and `libtype=A`.

## Reference workflow
nf-core/dualrnaseq v1.0.0 — https://github.com/nf-core/dualrnaseq (Mika-Gospodorz & Hayward, MIT). See `docs/usage.md` and `docs/output.md` in that repository for full parameter and output descriptions.
