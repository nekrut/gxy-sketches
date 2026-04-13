---
name: atacseq-chromatin-accessibility-paired-end
description: 'Use when you need to profile open chromatin regions from paired-end
  ATAC-seq Illumina data: trim Nextera adapters, align with Bowtie2, filter mitochondrial/duplicate/low-MAPQ
  reads, call peaks with MACS2, and produce normalized bigWig coverage tracks plus
  fragment-size QC. Assumes a supported Bowtie2 reference genome.'
domain: epigenomics
organism_class:
- eukaryote
- vertebrate
input_data:
- short-reads-paired
- reference-genome-index
source:
  ecosystem: iwc
  workflow: 'ATAC-seq Analysis: Chromatin Accessibility Profiling'
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/epigenetics/atacseq
  version: '1.0'
  license: MIT
tools:
- cutadapt
- bowtie2
- bamtools
- picard-markduplicates
- samtools
- bedtools
- macs2
- deeptools
- multiqc
tags:
- atac-seq
- chromatin-accessibility
- peak-calling
- paired-end
- bigwig
- nextera
- macs2
test_data:
- role: pe_fastq_input__srr891268_chr22_enriched__forward
  url: https://zenodo.org/record/3862793/files/SRR891268_chr22_enriched_R1.fastq.gz
  sha1: 0fd546fe61d5dcdec0d91c91c6ad02b4de1b40fc
  filetype: fastqsanger.gz
- role: pe_fastq_input__srr891268_chr22_enriched__reverse
  url: https://zenodo.org/record/3862793/files/SRR891268_chr22_enriched_R2.fastq.gz
  sha1: 8572153e721ba209a716128854b4560664bdf23d
  filetype: fastqsanger.gz
expected_output:
- role: mapping_stats
  description: Content assertions for `mapping stats`.
  assertions:
  - 'SRR891268_chr22_enriched: that: has_text'
  - 'SRR891268_chr22_enriched: text: 7282 (2.59%) aligned concordantly 0 times'
  - 'SRR891268_chr22_enriched: that: has_text'
  - 'SRR891268_chr22_enriched: text: 121059 (43.09%) aligned concordantly exactly
    1 time'
  - 'SRR891268_chr22_enriched: that: has_text'
  - 'SRR891268_chr22_enriched: text: 152623 (54.32%) aligned concordantly >1 times'
- role: markduplicates_metrics
  description: Content assertions for `MarkDuplicates metrics`.
  assertions:
  - 'SRR891268_chr22_enriched: has_text: 0.02'
- role: bam_filtered_rmdup
  description: Content assertions for `BAM filtered rmDup`.
  assertions:
  - 'SRR891268_chr22_enriched: has_size: {''value'': 15810403, ''delta'': 1000000}'
- role: histogram_of_fragment_length
  description: Content assertions for `histogram of fragment length`.
  assertions:
  - 'SRR891268_chr22_enriched: has_size: {''value'': 47718, ''delta'': 4000}'
- role: macs2_narrowpeak
  description: Content assertions for `MACS2 narrowPeak`.
  assertions:
  - 'SRR891268_chr22_enriched: has_n_lines: {''n'': 236}'
- role: macs2_report
  description: Content assertions for `MACS2 report`.
  assertions:
  - 'SRR891268_chr22_enriched: that: has_text'
  - 'SRR891268_chr22_enriched: text: # tag size is determined as 47 bps'
  - 'SRR891268_chr22_enriched: that: has_text'
  - 'SRR891268_chr22_enriched: text: # total tags in treatment: 262080'
- role: coverage_from_macs2_bigwig
  description: Content assertions for `Coverage from MACS2 (bigwig)`.
  assertions:
  - 'SRR891268_chr22_enriched: has_size: {''value'': 2892925, ''delta'': 200000}'
- role: 1kb_around_summits
  description: Content assertions for `1kb around summits`.
  assertions:
  - 'SRR891268_chr22_enriched: has_n_lines: {''n'': 217}'
- role: nb_of_reads_in_summits_500bp
  description: Content assertions for `Nb of reads in summits +-500bp`.
  assertions:
  - 'SRR891268_chr22_enriched: has_line: 9548'
- role: bigwig_norm
  description: Content assertions for `bigwig_norm`.
  assertions:
  - 'SRR891268_chr22_enriched: has_size: {''value'': 1253177, ''delta'': 100000}'
- role: bigwig_norm2
  description: Content assertions for `bigwig_norm2`.
  assertions:
  - 'SRR891268_chr22_enriched: has_size: {''value'': 1248419, ''delta'': 100000}'
- role: multiqc_on_input_dataset_s_stats
  description: 'Content assertions for `MultiQC on input dataset(s): Stats`.'
  assertions:
  - "has_line: Sample\tMACS2_mqc_generalstats_macs2_d\tMACS2_mqc_generalstats_macs2_peak_count\t\
    Picard: Mark Duplicates_mqc_generalstats_picard_mark_duplicates_PERCENT_DUPLICATION\t\
    Bowtie 2 / HiSAT2_mqc_generalstats_bowtie_2_hisat2_overall_alignment_rate\tCutadapt_mqc_generalstats_cutadapt_percent_trimmed"
  - 'has_text_matching: {''expression'': ''SRR891268_chr22_enriched\t200.0\t236\t2.7[0-9]*\t98.[0-9]*\t4.7[0-9]*''}'
- role: multiqc_webpage
  description: Content assertions for `MultiQC webpage`.
  assertions:
  - 'that: has_text'
  - 'text: <a href="#cutadapt_filtered_reads" class="nav-l2">Filtered Reads</a>'
  - 'that: has_text'
  - 'text: <td>% Aligned</td>'
  - 'that: has_text'
  - 'text: <td>% BP Trimmed</td>'
---

# ATAC-seq chromatin accessibility profiling (paired-end)

## When to use this sketch
- You have paired-end Illumina ATAC-seq FASTQ files (Nextera library prep) and want peaks plus coverage tracks.
- Your reference genome is available as a pre-built Bowtie2 index in the hosting Galaxy (e.g. hg19, hg38, mm10, dm6, ce11) and you know its effective genome size.
- You need the standard ENCODE-style filtering recipe: drop mitochondrial reads, discordant pairs, MAPQ<30, and PCR duplicates before peak calling.
- You want both a raw MACS2 bedGraph-derived bigWig and normalized coverage tracks (per million mapped reads and per million reads in peaks) for browser visualization or downstream differential accessibility.
- You want an integrated MultiQC report covering adapter trimming, alignment, chrM fraction, duplication, fragment-size distribution, MACS2 peak count, and FRiP-like metrics.

## Do not use when
- Data are single-end ATAC-seq — this workflow hard-codes paired-collection inputs and dovetail/fragment-length logic that assumes mates.
- You are analyzing ChIP-seq or CUT&RUN — use a ChIP-seq sketch; those pipelines typically need a matched input/control and use different MACS2 settings (no `--shift -100 --extsize 200`, possibly broad peaks).
- You need differential accessibility across conditions — this sketch ends at per-sample peaks and bigWigs; feed the outputs into a DiffBind/DESeq2 consensus-peak sketch.
- You have long-read (Nanopore/PacBio) or scATAC-seq data — use dedicated long-read or single-cell ATAC sketches.
- Your genome has no Bowtie2 index plus matching `len` file registered for bedtools slopBed on the Galaxy server (workflow will fail at the slop step).
- You want to keep mitochondrial reads or reads with MAPQ<30 — the filter step is hard-coded.

## Analysis outline
1. Trim Nextera R1/R2 adapters and quality-trim bases (Q<30), dropping reads shorter than 15 bp — `cutadapt`.
2. Align paired reads to the reference with `bowtie2 --very-sensitive`, allowing dovetailing and fragments up to 1 kb.
3. Collect per-chromosome read counts on the raw BAM — `samtools idxstats` (used to compute chrM fraction for QC).
4. Filter the BAM to `mapQuality>=30`, `isProperPair`, and exclude reads/mates on `chrM`/`MT` — `bamtools filter`.
5. Remove PCR duplicates with `picard MarkDuplicates` (`REMOVE_DUPLICATES=true`).
6. Compute the insert-size histogram (upper limit 500 bp) to check the characteristic nucleosomal laddering — `pe_histogram`.
7. Convert the cleaned BAM to BED with `bedtools bamtobed` so MACS2 sees both mates as independent Tn5 cut sites.
8. Call peaks with `MACS2 callpeak` in nomodel mode with `--shift -100 --extsize 200` to build ±100 bp pileups centered on the 5' cut sites; enable `--call-summits`.
9. Convert the MACS2 treatment pileup bedGraph to bigWig — `wigToBigWig`.
10. Expand each summit ±500 bp with `bedtools slop` and merge overlaps with `bedtools merge` to define 1 kb summit-centered intervals.
11. Count reads in the cleaned BAM overlapping those 1 kb intervals — `bedtools coverage`; sum to get reads-in-peaks.
12. Count total reads in the cleaned BAM — `samtools view -c`; derive per-sample scale factors `1e6/total_reads` and `1e6/reads_in_peaks`.
13. Produce two normalized bigWigs at the chosen bin size by scaling the raw coverage bigWig with `deepTools bigwigAverage` (used per-sample, not as an average).
14. Aggregate cutadapt, Bowtie2, chrM bargraph, MarkDuplicates, fragment-size line plot, MACS2, and reads-in-peaks bargraph into a single `MultiQC` HTML report.

## Key parameters
- Cutadapt adapters: Nextera R1 `CTGTCTCTTATACACATCTCCGAGCCCACGAGAC`, Nextera R2 `CTGTCTCTTATACACATCTGACGCTGCCGACGA`; `quality_cutoff=30`; `minimum_length=15`.
- Bowtie2: `--very-sensitive`, paired `-I 0 -X 1000`, `--fr`, `--dovetail` enabled.
- BAM filter: `mapQuality>=30`, `isProperPair=true`, `reference!=chrM`, `mateReference!=MT`.
- MarkDuplicates: `REMOVE_DUPLICATES=true`, `VALIDATION_STRINGENCY=LENIENT`, `OPTICAL_DUPLICATE_PIXEL_DISTANCE=100`.
- MACS2 callpeak: `format=BED` (not BAMPE), `--nomodel`, `--shift -100`, `--extsize 200`, `--qvalue 0.05`, `--call-summits`, `--keep-dup all` (duplicates already removed), user-supplied `effective_genome_size` (e.g. 2.7e9 human, 1.87e9 mouse, 1.2e8 fly, 9e7 worm).
- Summit window: `bedtools slop -b 500` then `bedtools merge` → 1 kb summit-centered intervals.
- Coverage normalization: `deepTools bigwigAverage` with per-sample `scaleFactor = 1e6 / N`, where `N` is either total reads in the cleaned BAM or reads-in-peaks; `binSize` is user-supplied (50 bp is a good default, larger for smaller files).
- Required workflow inputs: `reference_genome` (text dbkey matching both a Bowtie2 index and a bedtools slopBed len file), `effective_genome_size` (integer), `bin_size` (integer).

## Test data
The source workflow ships a single-sample test using a paired-end FASTQ collection `SRR891268_chr22_enriched` (human GM12878 ATAC-seq reads enriched for chr22, hosted on Zenodo record 3862793, R1/R2 gzipped fastqsanger). The run uses `reference_genome=hg19`, `effective_genome_size=2700000000`, and `bin_size=1000`. Expected outputs include a Bowtie2 mapping report showing ~43% concordant-once and ~54% concordant->1 alignment, MarkDuplicates reporting ~2% duplication, a ~15.8 MB cleaned BAM, a fragment-length histogram (~47 kB), 236 MACS2 narrowPeak lines, a MACS2 report noting `tag size is determined as 47 bps` and `total tags in treatment: 262080`, ~217 merged 1 kb summit intervals with 9548 reads overlapping them, a ~2.9 MB raw coverage bigWig, and two ~1.25 MB normalized bigWigs. The MultiQC stats table should show MACS2 d=200, 236 peaks, ~2.7% duplication, ~98% alignment, and ~4.7% bases trimmed by Cutadapt.

## Reference workflow
Galaxy IWC `workflows/epigenetics/atacseq` — "ATAC-seq Analysis: Chromatin Accessibility Profiling" v1.0 (MIT, Lucille Delisle). Aligned with the Galaxy Training Network ATAC-seq tutorial (`training-material/topics/epigenetics/tutorials/atac-seq`). Version 1.0 (2024-11-28) is the first release where Bowtie2 is run with dovetail + 1 kb fragment length as documented; versions <0.8 did not actually remove PCR duplicates and <0.9 mis-scaled the normalized bigWigs — use ≥1.0.
