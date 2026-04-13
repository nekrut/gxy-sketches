---
name: ploidy-aware-germline-variant-calling-short-read
description: Use when you need germline SNV/indel calling and functional annotation
  from paired-end Illumina WGS data for an organism of arbitrary ploidy (haploid,
  diploid, or polyploid), using FreeBayes with a user-specified ploidy parameter.
  Produces annotated VCF and per-sample flattened TSV tables via SnpEff/SnpSift against
  a custom SnpEff database built on-the-fly from the supplied reference and GTF.
domain: variant-calling
organism_class:
- eukaryote
- haploid
- diploid
- polyploid
input_data:
- short-reads-paired
- reference-fasta
- gene-annotation-gtf
- ploidy-integer
source:
  ecosystem: iwc
  workflow: Paired end variant and ploidy-aware genotype calling
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/variant-calling/ploidy-aware-genotype-calling
  version: 0.1.1
  license: MIT
tools:
- fastp
- bwa-mem
- samtools
- picard-markduplicates
- freebayes
- bcftools
- snpeff
- snpsift
- multiqc
tags:
- germline
- wgs
- short-read
- freebayes
- ploidy
- snpeff
- veupath
- illumina
test_data: []
expected_output: []
---

# Ploidy-aware germline variant calling from paired-end short reads

## When to use this sketch
- User has paired-end Illumina WGS FASTQ data for one or more samples and wants germline SNVs and small indels called against a reference genome.
- The organism's ploidy is known and needs to be explicitly passed to the variant caller (e.g. haploid protist, diploid vertebrate/plant, or polyploid such as triploid/tetraploid crops or Plasmodium-like parasites).
- A reference FASTA **and** a matching gene annotation GTF are available, and the user wants functional annotation (coding/splicing effects) plus a flattened per-sample variants table.
- User explicitly wants FreeBayes-style haplotype-based calling with a configurable `-p`/ploidy rather than a caller locked to diploid assumptions.
- VEuPathDB-style eukaryotic pathogens (Plasmodium, Trypanosoma, Leishmania, Toxoplasma, etc.) are a prototypical fit.

## Do not use when
- You have long reads (ONT/PacBio) — use a long-read variant-calling sketch instead.
- You are calling somatic/tumor-normal variants — use a somatic caller sketch (Mutect2/Strelka/Varscan somatic).
- You need structural variants or CNVs — use a structural-variants sketch.
- You are doing single-sample bacterial haploid calling where a lighter `bcftools call -p 1` pipeline is sufficient — prefer a dedicated haploid-bacterial sketch.
- You lack a GTF/annotation and only need an unannotated VCF — strip the SnpEff steps or use a calling-only sketch.
- Input is single-end, amplicon, RNA-seq, or target-capture data requiring BED-restricted calling.

## Analysis outline
1. **Read QC and trimming** — `fastp` on the paired collection; emit HTML + JSON reports.
2. **Mapping** — `bwa-mem` of trimmed pairs against the reference FASTA, coordinate-sorted BAM output.
3. **Proper-pair filtering** — `samtools view` with inclusive flag filter `1,2` (paired + properly paired) to retain only mapped read pairs.
4. **Alignment stats** — `samtools stats` on the filtered BAM for QC aggregation.
5. **Duplicate removal** — `picard MarkDuplicates` with `remove_duplicates=true` to produce the analysis-ready BAM and a metrics file.
6. **QC aggregation** — `MultiQC` combining fastp JSON, samtools stats, and MarkDuplicates metrics into a single HTML report.
7. **SnpEff database build** — `snpEff build` from the supplied reference FASTA + GTF, standard codon table, on-the-fly custom database.
8. **Variant calling** — `FreeBayes` in merged batch mode across all per-sample BAMs, with the user-supplied ploidy wired into `population_model.P` and theta `T=0.001`.
9. **Normalization** — `bcftools norm` with `-m -both` to split multi-allelics into biallelic records, left-align indels, and check reference consistency (`check_ref=w`).
10. **Functional annotation** — `SnpEff eff` against the freshly built custom database; annotations restricted to coding/splicing by excluding `-no-downstream -no-intergenic -no-intron -no-utr -no-upstream`; classic/formatEff output.
11. **Field extraction** — `SnpSift extractFields` to flatten the annotated VCF into a tabular report (CHROM, POS, FILTER, REF, ALT, DP, AF, RO, AO, SRP, SAP, and per-effect IMPACT/FUNCLASS/EFFECT/GENE/CODON/AA/TRID).
12. **Collection collapse** — `Collapse Collection` to merge the per-sample TSVs into a single annotated variants table tagged `VariantsAsTSV`.

## Key parameters
- `Set Ploidy for FreeBayes Variant Calling`: integer, default `2`. Set to `1` for haploid pathogens, `2` for standard diploids, `3`/`4` for polyploid plants or pooled samples. Wired into FreeBayes `population_model.P`.
- FreeBayes `population_model.T` (theta): `0.001` (default expected mutation rate).
- FreeBayes batch mode: `processmode=merge` — joint calling across all samples in the collection against one reference.
- `samtools view` inclusive filter flags: `1,2` (paired, properly paired).
- `picard MarkDuplicates`: `remove_duplicates=true`, `duplicate_scoring_strategy=SUM_OF_BASE_QUALITIES`, `validation_stringency=LENIENT`.
- `bcftools norm`: `multiallelics=- both`, `normalize_indels=true`, `check_ref=w`, `output_type=v`.
- `SnpEff build`: `input_type=gtf`, `genome_version=snpeff_db`, `codon_table=Standard`, reference from history FASTA.
- `SnpEff eff`: `annotations=[-formatEff,-classic]`, `filterOut=[-no-downstream,-no-intergenic,-no-intron,-no-utr,-no-upstream]`, `spliceSiteSize=2`, `udLength=0`, custom DB from step 7.
- `SnpSift extractFields` field list: `CHROM POS FILTER REF ALT DP AF RO AO SRP SAP EFF[*].IMPACT EFF[*].FUNCLASS EFF[*].EFFECT EFF[*].GENE EFF[*].CODON EFF[*].AA EFF[*].TRID`, one effect per line, `.` for empty.
- Input collection type: Galaxy `list:paired` with `fastqsanger`/`fastqsanger.gz`.

## Test data
The workflow's test profile supplies a `list:paired` collection of Illumina paired-end FASTQ samples, a reference genome FASTA, a matching gene annotation GTF, and an integer ploidy parameter. A successful run is expected to produce: a per-sample fastp HTML report, a combined MultiQC HTML report aggregating fastp/samtools-stats/MarkDuplicates, a normalized FreeBayes VCF annotated by SnpEff (tagged `VariantsasVCF`), a SnpEff HTML summary, and a single merged annotated variants TSV (tagged `VariantsAsTSV`) with one row per variant-effect across all samples. Ploidy must be set to match the test organism so that FreeBayes genotypes carry the expected number of alleles.

## Reference workflow
Galaxy IWC — `workflows/variant-calling/ploidy-aware-genotype-calling` ("Paired end variant and ploidy-aware genotype calling"), release 0.1.1, MIT licensed, authored by Saim Momin and Wolfgang Maier. Tagged `VeuPath`, `Diploid`, `FreeBayes` upstream.
