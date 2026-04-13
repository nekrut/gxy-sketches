---
name: slamseq-transcriptional-output
description: Use when you need to quantify newly synthesized RNA from SLAMseq (4SU
  metabolic labeling) data and identify direct transcriptional targets by calling
  T>C conversion-containing reads and running differential expression on the converted-read
  counts. Assumes single-end SLAMseq / QuantSeq-style 3' end libraries with a 3' UTR
  BED annotation.
domain: rna-seq
organism_class:
- vertebrate
- eukaryote
input_data:
- short-reads-single
- reference-fasta
- utr-bed
source:
  ecosystem: nf-core
  workflow: nf-core/slamseq
  url: https://github.com/nf-core/slamseq
  version: 1.0.0
  license: MIT
tools:
- trim-galore
- slamdunk
- nextgenmap
- varscan2
- samtools
- deseq2
- multiqc
tags:
- slamseq
- 4sU
- metabolic-labeling
- nascent-rna
- t-to-c-conversion
- quantseq
- nascent-transcription
- direct-targets
test_data: []
expected_output: []
---

# SLAMseq direct transcriptional output analysis

## When to use this sketch
- Input is a SLAMseq (or related 4-thiouridine metabolic labeling) experiment where reads carry T>C conversions in newly synthesized transcripts.
- Library design is 3' end counting (QuantSeq-style), single-end FASTQ, with a 3' UTR BED annotation available.
- Goal is to quantify nascent / labeled transcription per gene and call direct transcriptional targets between a control condition (e.g. DMSO) and one or more treatment conditions (e.g. drug, knockdown) within each cell line or `group`.
- Experimental design includes replicates per condition and one condition explicitly flagged as the control for DESeq2 contrasts.
- You want an end-to-end path: adapter trimming → conversion-aware mapping → T>C SNP masking → per-UTR/per-gene total and converted counts → DESeq2 on T>C counts with size factors from total counts.

## Do not use when
- Standard (non-labeled) bulk RNA-seq differential expression — use a conventional `rna-seq` sketch (STAR/Salmon + DESeq2) instead.
- TT-seq, GRO-seq, PRO-seq or other run-on based nascent RNA protocols — these need different mappers and peak/interval strategies.
- scSLAM-seq or other single-cell labeling protocols — require dedicated single-cell conversion-aware tools.
- You only want half-life estimation from pulse/chase time courses without a differential contrast; this sketch focuses on the direct-target DESeq2 contrast output.
- Bacterial or viral systems, or any organism without a 3' UTR annotation BED suitable for Slamdunk counting windows.

## Analysis outline
1. Parse the sample design TSV (`group`, `condition`, `control`, `reads`, optional `name`/`type`/`time`) to build per-group contrasts against the control condition.
2. Adapter and quality trimming of single-end FASTQ with Trim Galore! (skippable via `--skip_trimming`).
3. Conversion-aware mapping of trimmed reads to the reference FASTA with Slamdunk (NextGenMap backend), using `--trim5`, `--polyA`, `--read_length`, and optional `--endtoend` / `--quantseq` flags.
4. Alignment filtering and optional multimapper recovery against 3' UTR intervals (`slamdunk filter`), using `--mapping` BED if provided otherwise falling back to `--bed`.
5. SNP calling with VarScan2 via `slamdunk snp` (controlled by `--min_coverage` and `--var_fraction`) to mask genomic T>C SNPs; bypassed if a `--vcf` is supplied.
6. Per-UTR total and T>C converted read quantification with `slamdunk count`, using `--conversions` and `--base_quality` to define T>C reads.
7. Collapse per-UTR tcount tables to gene-level total and converted counts.
8. Slamdunk QC summary (rates, UTR rates, conversions per read/UTR position, PCA on T>C counts) aggregated for MultiQC.
9. DESeq2 differential transcriptional output per `group`: size factors estimated from total read counts, dispersion and Wald tests run on T>C converted counts, one contrast per non-control `condition` vs the control, with MA plots highlighted at `--pvalue`.
10. MultiQC report combining FastQC/Trim Galore!, Slamdunk, and DESeq2 outputs.

## Key parameters
- `--input`: TSV design file with required columns `group`, `condition`, `control` (1 for control replicates, 0 otherwise), `reads`; optional `name`, `type` (`pulse`|`chase`, default `pulse`), `time` (4SU minutes, default `0`).
- `--genome` (iGenomes key, e.g. `GRCh38`, `GRCm38`) or explicit `--fasta` plus `--bed` (3' UTR counting windows); `--mapping` BED optional for multimapper recovery; `--vcf` optional to bypass `slamdunk snp`.
- `--trim5`: 5' hard-trim length (test profile uses `12` for typical SLAMseq/QuantSeq adapters).
- `--polyA`: max trailing A run before poly-A trimming.
- `--multimappers`: enable UTR-guided multimapper reconciliation.
- `--quantseq`: disables conversion-aware scoring — leave OFF for real SLAMseq (otherwise T>C counts collapse to zero and DESeq2 is meaningless).
- `--endtoend`: end-to-end NGM mapping mode.
- `--conversions`: minimum T>C conversions to call a read labeled (Slamdunk default 1).
- `--base_quality`: min base quality for a T>C conversion (test profile uses `27`).
- `--min_coverage`, `--var_fraction`: SNP calling thresholds for T>C masking (test profile uses `var_fraction=0.2`).
- `--read_length`: sample read length (test profile uses `100`).
- `--pvalue`: adjusted p-value cutoff used to highlight significant genes in DESeq2 MA plots.
- `--skip_deseq2`: run only quantification and QC without differential analysis.

## Test data
The bundled `test` profile pulls a minimal human chr8 SLAMseq dataset from `nf-core/test-datasets` (branch `slamseq`): a sample design TSV (`sampleInfo.tsv`) describing a small set of single-end FASTQ files, a gzipped `hg38_chr8.fa.gz` reference, and a 3' UTR BED (`hg38_refseq_3UTR.chr8.bed`). It runs with `trim5=12`, `multimappers=true`, `var_fraction=0.2`, `base_quality=27`, `read_length=100`, capped at 2 CPUs / 6 GB. A successful run is expected to produce trimmed FASTQs, per-sample filtered BAM/BAI in `results/slamdunk/bam/`, Slamdunk VCFs in `results/slamdunk/vcf/`, per-UTR tcount TSVs and per-gene CSVs under `results/slamdunk/count/`, per-group DESeq2 output directories (`PCA.pdf`, `<condition>/DESeq2.txt`, `<condition>/MAPlot.pdf`) under `results/deseq2/`, and a combined `results/multiqc/Project_multiqc_report.html` showing Slamdunk rates, UTR rates and PCA panels.

## Reference workflow
nf-core/slamseq v1.0.0 (https://github.com/nf-core/slamseq), DOI 10.5281/zenodo.3826585. Core tooling: Trim Galore!, Slamdunk (NextGenMap mapper, VarScan2 SNP caller, pysam-based counting), SAMtools, DESeq2, MultiQC.
