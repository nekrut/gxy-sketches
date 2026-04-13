---
name: rna-somatic-variant-calling-tumor-normal
description: Use when you need to detect somatic SNVs and small indels in bulk tumor
  RNA-seq data (cancer research) with a matched DNA normal, optionally plus a tumor
  DNA sample. Runs a multi-caller consensus (Mutect2, Strelka2, SAGE) with RNA-specific
  preprocessing (SplitNCigarReads), VEP annotation, HISAT2 realignment around candidate
  sites, and RNA-aware filtering (RNA editing, PoN, blacklists).
domain: variant-calling
organism_class:
- vertebrate
- diploid
- eukaryote
input_data:
- short-reads-paired
- rna-seq-paired
- reference-fasta
- gtf
source:
  ecosystem: nf-core
  workflow: nf-core/rnadnavar
  url: https://github.com/nf-core/rnadnavar
  version: dev
  license: MIT
tools:
- fastp
- fastqc
- star
- bwa-mem
- gatk4
- mutect2
- strelka2
- sage
- vep
- vcf2maf
- vt
- hisat2
- bcftools
- samtools
- mosdepth
tags:
- cancer
- somatic
- rna-seq
- tumor-normal
- consensus
- maf
- rna-mutect
- snv
- indel
test_data: []
expected_output: []
---

# RNA somatic variant calling with matched DNA normal

## When to use this sketch
- Cancer / tumor study where the primary variant source is **bulk tumor RNA-seq**, and you want somatic SNV/indel calls (not expression, not fusions).
- You have a **matched DNA normal** sample per patient (mandatory) and optionally a tumor DNA sample; all three link by the same `patient` ID with `status` 0=normal DNA, 1=tumor DNA, 2=tumor RNA.
- Human or mouse samples; short-read Illumina FASTQ (or pre-aligned BAM/CRAM).
- You want a multi-caller **consensus** (Mutect2 + Strelka2 + SAGE) to reduce false positives, plus RNA-aware filtering (RNA editing sites, RNA PoN, blacklists) and optional HISAT2 realignment around candidate variant loci — the RNA-MuTect-style refinement.
- Whole-genome, whole-exome (`--wes`), or targeted panels against a reference configured via iGenomes or explicit `--fasta`/`--gtf`.

## Do not use when
- You only have **tumor DNA + normal DNA** (no RNA) — use an nf-core/sarek somatic sketch instead; this pipeline requires an RNA tumor sample tied to a DNA normal.
- You only have **bulk RNA-seq for expression / DE analysis** — use an nf-core/rnaseq quantification sketch.
- You want **germline** short variants from RNA or DNA — this pipeline is somatic-only.
- You need **structural variants, CNVs, fusions, or allele-specific expression** — out of scope; no Manta/Arriba/STAR-Fusion here despite `manta` appearing in the tools regex.
- Your organism is **bacterial/haploid** — see a haploid-variant-calling sketch.
- You have **single-cell RNA-seq** — use a scRNA sketch.

## Analysis outline
1. **QC & trim** raw FASTQs with FastQC and fastp (`--trim_fastq`), optionally sharding with `split_fastq` for parallelism.
2. **Align** DNA samples with BWA-MEM / BWA-MEM2 / DragMap and **RNA samples with STAR** (2-pass by default), producing BAM/CRAM.
3. **GATK preprocessing** per GATK RNA-seq short-variant best practices: MarkDuplicates → (RNA only) SplitNCigarReads → BaseRecalibrator → ApplyBQSR; samtools stats + mosdepth for alignment QC.
4. **Somatic variant calling** per tumor (RNA and optionally DNA) vs matched DNA normal with Mutect2, Strelka2, and SAGE over genome intervals (or a WES/panel BED).
5. **Normalize** VCFs with `vt decompose`/`normalize` (`norm` tool) for consistent representation across callers.
6. **Annotate** with Ensembl VEP, then **convert VCF→MAF** with vcf2maf.
7. **Consensus** across callers into a combined MAF (per-caller and merged consensus outputs).
8. **MAF filtering**: gnomAD population AF, whitelist/blacklist BEDs, quality filters; for RNA samples an extra RNA-specific filter pass (RNA edit sites, RNA PoN, optional second-reference PoN via liftover with `chain`).
9. **HISAT2 realignment** (RNA only): extract reads over candidate variant regions, realign with HISAT2, re-call, and re-merge — an `_realign` suffixed `Tumor_Sample_Barcode` row is added per mutation; rescue step can promote variants supported after realignment.
10. **MultiQC** report aggregating FastQC, fastp, samtools, mosdepth, GATK metrics and per-step logs.

## Key parameters
- `--input samplesheet.csv`: CSV with `patient,sample,status,lane,fastq_1,fastq_2` (status 0=normal DNA, 1=tumor DNA, 2=tumor RNA). BAM/CRAM or MAF entry points also supported via `bam,bai` / `cram,crai` / `caller,maf`.
- `--step`: entry point — `mapping` (default), `markduplicates`, `splitncigar`, `prepare_recalibration`, `recalibrate`, `variant_calling`, `norm`, `consensus`, `annotate`, `filtering`, `realignment`.
- `--tools`: comma list; for a full RNA somatic run use `sage,strelka,mutect2,vep,norm,consensus,rescue,realignment,filtering,rna_filtering`. Minimum useful: `mutect2,strelka,sage` at `variant_calling`.
- `--skip_tools`: e.g. `realignment`, `splitncigar`, `baserecalibrator` (recommended with DragMap).
- `--genome GRCh38` (default) or explicit `--fasta`, `--fasta_fai`, `--dict`, `--gtf`, `--dbsnp`, `--germline_resource`, `--known_indels`, `--pon`.
- `--aligner` one of `bwa-mem` (default), `bwa-mem2`, `dragmap`; STAR is always used for RNA when `--rna true`.
- `--wes` + `--intervals <bed>` for exome/panel; `--no_intervals` to disable chunking (required for Mutect2-less runs).
- `--joint_mutect2`: multi-sample Mutect2 across tumors from the same patient.
- `--split_fastq 50000000` (default) for fastp-based sharding; set `0` to disable.
- SAGE resources: `--sage_highconfidence`, `--sage_actionablepanel`, `--sage_knownhotspots`, `--sage_ensembl_dir`, `--sage_resource_dir`.
- VEP: `--vep_cache`, `--vep_cache_version`, `--vep_species`, `--vep_genome`, `--vep_include_fasta`; optional plugins `--vep_dbnsfp`, `--vep_loftee`, `--vep_spliceai`.
- RNA filtering inputs: `--rnaedits` (BED of RNA edit sites, comma-separated), `--rna_pon`, `--rna_pon2` (+ `--chain`, `--fasta2`, `--refname`, `--refname2` for cross-reference PoN liftover), `--blacklist`, `--whitelist`.
- Variant-caller priority for consensus: `--defaultvariantcallers sage,strelka,mutect2`.

## Test data
The bundled `-profile test` runs on a paired-end FASTQ triplet (one DNA normal, one DNA tumor, one RNA tumor, all tied to the same patient) from `tests/csv/3.0/fastq_triplet.csv`, against a tiny chr7 slice of GRCh38 (`GRCh38.d1.vd1.chr7.mini.fa`) with a matching chr7 GENCODE v36 GTF, a chr7-trimmed dbSNP 146 VCF, and a chr7-trimmed gnomAD germline resource. It runs in WES mode with `--no_intervals`, `split_fastq 50000` and `--tools strelka,filtering`, producing a filtered MAF end-to-end in under an hour on 4 cpus / 15 GB. The `test_full` profile additionally exercises `sage,strelka,mutect2,vep,norm,consensus,rescue,realignment,filtering,rna_filtering` using SAGE hotspot/high-confidence BEDs and a stripped VEP cache from `nf-core/test-datasets:rnadnavar`, starting from pre-recalibrated CRAMs (`trbc_recalibrated.csv`). Expected outputs include per-caller VCFs under `variant_calling/{mutect2,strelka,sage}/`, a merged `consensus/*.consensus.maf`, and a final `filtering/*.filtered.maf` (plus `filtering/rna/*.rna_filtered.maf` when `rna_filtering` is enabled), all summarized in a MultiQC report.

## Reference workflow
nf-core/rnadnavar (dev, template 3.5.1, Nextflow ≥25.04.0) — https://github.com/nf-core/rnadnavar. Based on the RNA-MuTect approach of Yizhak et al., *Science* 2019 (doi:10.1126/science.aaw0726) and GATK RNA-seq short-variant best practices; see `CITATIONS.md` for Mutect2, Strelka2, SAGE, STAR, VEP, vcf2maf, vt and HISAT2 references.
