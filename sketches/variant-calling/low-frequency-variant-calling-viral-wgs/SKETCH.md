---
name: low-frequency-variant-calling-viral-wgs
description: Use when you need sensitive low-frequency variant calling (including
  sub-consensus minor variants) from paired-end Illumina WGS reads against a small
  viral or microbial reference supplied as a GenBank file, with functional annotation
  via a custom SnpEff database built from that GenBank. Typical applications include
  monkeypox (MPXV), SARS-CoV-2, and other small-genome viral surveillance.
domain: variant-calling
organism_class:
- viral
- haploid
input_data:
- short-reads-paired
- reference-genbank
source:
  ecosystem: iwc
  workflow: Generic variation analysis on WGS PE data
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/variant-calling/generic-variant-calling-wgs-pe
  version: 0.1.1
  license: MIT
  slug: variant-calling--generic-variant-calling-wgs-pe
tools:
- name: fastp
  version: 0.23.2+galaxy0
- name: bwa-mem
  version: 0.7.17.2
- name: samtools
  version: 1.13+galaxy1
- name: picard-markduplicates
  version: 2.18.2.2
- name: lofreq
  version: 2.1.5+galaxy0
- name: snpeff
  version: 4.3+T.galaxy1
- name: multiqc
  version: 1.11+galaxy0
tags:
- viral
- wgs
- low-frequency
- minor-variants
- lofreq
- snpeff
- genbank
- mpxv
- sars-cov-2
test_data: []
expected_output:
- role: fasta_sequences_for_genbank_file
  path: expected_output/Fasta sequences for genbank file.fasta
  description: Expected output `Fasta sequences for genbank file` from the source
    workflow test.
  assertions: []
---

# Low-frequency variant calling from viral WGS PE reads

## When to use this sketch
- You have paired-end Illumina WGS reads from a small-genome organism (virus or similar) and want SNVs + indels called against a reference genome.
- The reference is available as a GenBank file with gene annotations, and you want functional effect annotation (synonymous/missense/etc.) in the final VCF.
- You care about low-allele-frequency / sub-consensus variants (e.g. intra-host diversity, mixed populations, viral quasispecies), not just a consensus genotype.
- The sample is effectively haploid and the genome is small enough that LoFreq's per-site statistical model is appropriate (viruses, small bacteria/plasmids).
- Example use cases: monkeypox virus (MPXV) surveillance, SARS-CoV-2 intra-host variant profiling, small viral outbreak investigations.

## Do not use when
- You need diploid/polyploid genotyping of eukaryotes — use a GATK HaplotypeCaller- or DeepVariant-based sketch instead.
- You only want a consensus sequence / lineage call — use a consensus-calling or lineage-typing sketch.
- Input reads are long reads (ONT/PacBio) — use a long-read variant calling sketch (medaka, clair3).
- You are calling variants in a large bacterial genome where you only want high-confidence fixed SNPs — a bcftools/ploidy=1 sketch is simpler and faster.
- Your reference is only available as plain FASTA with no annotations and you do not need SnpEff annotation — the GenBank-driven database build step is unnecessary overhead.
- You are doing amplicon/primer-based sequencing where primer trimming and strand-aware calling matter (e.g. ARTIC) — use an amplicon-specific sketch.

## Analysis outline
1. **Adapter/quality trim** paired reads with `fastp` (produces JSON report for MultiQC).
2. **Build a SnpEff database** from the input GenBank with `SnpEff build` (`input_type=gb`), emitting both the SnpEff DB and a FASTA extracted from the GenBank to use as the mapping reference.
3. **Map reads** to the GenBank-derived FASTA with `bwa-mem` (coordinate-sorted BAM; soft-clipping of supplementary alignments kept, `-T 30`, `-h 5`).
4. **Filter alignments** with `samtools view` to keep only properly paired mapped read pairs (inclusive flags 1+2).
5. **Mark and remove duplicates** with Picard `MarkDuplicates` (`remove_duplicates=true`).
6. **Collect QC** with `samtools stats` on the filtered BAM and combine fastp + samtools + Picard metrics via `MultiQC`.
7. **Realign reads around indels** with `lofreq viterbi` to improve indel calling.
8. **Insert indel qualities** into the BAM with `lofreq indelqual` using the `dindel` strategy.
9. **Call variants** with `lofreq call` against the reference, with indel calling enabled.
10. **Soft-filter variants** with `lofreq filter` (strand-bias FDR filtering, `--print-all`).
11. **Annotate effects** with `SnpEff eff` using the custom database from step 2.

## Key parameters
- `fastp`: paired-collection mode, quality and length filtering enabled (defaults), JSON+HTML reports on.
- `SnpEff build`: `input_type=gb`, `codon_table=Standard`, `remove_version=true`, FASTA export on — the extracted FASTA is the mapping reference, keeping coordinates consistent with annotations.
- `bwa-mem`: `-T 30` (min alignment score), `-h 5`, `-Y` (soft-clip supplementary), coordinate-sorted output.
- `samtools view` post-filter: inclusive flags `1,2` (paired + properly paired), quality 0, BAM out.
- `Picard MarkDuplicates`: `remove_duplicates=true`, `duplicate_scoring_strategy=SUM_OF_BASE_QUALITIES`, `validation_stringency=LENIENT`.
- `lofreq viterbi`: default BQ2 handling (`keep`, `defqual=2`).
- `lofreq indelqual`: `strategy=dindel`.
- `lofreq call`: `min_cov=5`, `min_bq=30`, `min_alt_bq=30`, `min_mq=0`, `max_mq=255`, `extended_baq=true`, `sig=0.0005`, `bonf=0`, `--call-indels`, whole genome.
- `lofreq filter`: strand-bias filter `mtc=fdr`, `sb_alpha=0.001`, compound SB on, indels excluded from SB; `--print-all` (soft filter).
- `SnpEff eff`: `genomeSrc=custom` (uses DB from step 2), `-formatEff -classic`, filters out downstream/intergenic/intron/upstream/UTR effects, generates HTML stats.

## Test data
The workflow's test profile provides one paired-end sample, `ERR3485802` (public Illumina WGS run, monkeypox virus), as a `list:paired` collection of gzipped FASTQs, plus a GenBank reference file (`GenBank genome.genbank`) and a text parameter `Name for genome database` set to `mpxv`. Running the workflow is expected to produce: a FASTA extracted from the GenBank (`Fasta sequences for genbank file.fasta`, compared with `contains`), per-sample LoFreq raw variants (`called_variants.vcf`), LoFreq strand-bias soft-filtered variants (`soft_filtered_variants.vcf`), SnpEff-annotated variants (`SnpEff variants.vcf`) — all VCFs compared by diff with a 6-line tolerance to absorb header/date differences — and a `samtools stats` tabular report (`mapped_reads_stats.tabular`).

## Reference workflow
Galaxy IWC — `workflows/variant-calling/generic-variant-calling-wgs-pe`, workflow *Generic variation analysis on WGS PE data*, release **0.1.1** (MIT). Authored by Anton Nekrutenko. Originally developed for MPXV but tagged `generic` and applicable to other small-genome viral WGS datasets.
