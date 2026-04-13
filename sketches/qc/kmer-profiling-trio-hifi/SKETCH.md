---
name: kmer-profiling-trio-hifi
description: Use when you need to profile genome size, heterozygosity, and repeat
  content from PacBio HiFi reads of a diploid eukaryote and also build haplotype-partitioned
  parental k-mer databases from Illumina reads of both parents (trio binning prep).
  Produces Meryl databases and GenomeScope profiles for child, maternal, and paternal
  reads as a pre-assembly QC step in the VGP pipeline.
domain: qc
organism_class:
- eukaryote
- vertebrate
- diploid
input_data:
- long-reads-pacbio-hifi
- short-reads-paired
- parental-illumina-reads
source:
  ecosystem: iwc
  workflow: kmer-profiling-hifi-trio-VGP2
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/VGP-assembly-v2/kmer-profiling-hifi-trio-VGP2
  version: 0.1.6
  license: CC-BY-4.0
tools:
- meryl
- genomescope2
tags:
- vgp
- kmer
- genomescope
- meryl
- trio
- haplotype-phasing
- genome-size
- heterozygosity
- pre-assembly-qc
test_data:
- role: maternal_reads__forward
  url: https://zenodo.org/record/6603774/files/paternal.fastq?download=1
  filetype: fastqsanger
- role: maternal_reads__reverse
  url: https://zenodo.org/record/6603774/files/paternal.fastq?download=1
  filetype: fastqsanger
- role: paternal_reads__forward
  url: https://zenodo.org/record/6603774/files/maternal.fastq?download=1
  filetype: fastqsanger
- role: paternal_reads__reverse
  url: https://zenodo.org/record/6603774/files/maternal.fastq?download=1
  filetype: fastqsanger
- role: pacbio_hifi_reads__pacbio_dataset
  url: https://zenodo.org/record/6603774/files/child.fastq?download=1
  filetype: fastqsanger
expected_output:
- role: genomescope_summary_child
  description: Content assertions for `GenomeScope summary (child)`.
  assertions:
  - 'has_text: 43,763 bp'
- role: meryl_database_child
  description: 'Content assertions for `Meryl database : Child`.'
  assertions:
  - 'has_size: {''value'': 205051, ''delta'': 1000}'
- role: meryl_database_paternal
  description: 'Content assertions for `Meryl database : paternal`.'
  assertions:
  - 'has_size: {''value'': 40338, ''delta'': 1000}'
- role: meryl_database_maternal
  description: 'Content assertions for `Meryl database : maternal`.'
  assertions:
  - 'has_size: {''value'': 49534, ''delta'': 1000}'
---

# K-mer profiling of a HiFi trio (VGP)

## When to use this sketch
- You have PacBio HiFi reads from a child/proband and short-read Illumina data from both parents, and want trio-based k-mer profiling before genome assembly.
- You need pre-assembly QC metrics: estimated genome size, heterozygosity rate, repeat fraction, and read-set coverage/quality.
- You need Meryl k-mer databases (child, maternal, paternal) to feed downstream VGP steps (e.g. hifiasm trio mode, Merqury evaluation, haplotype-resolved assembly).
- Target organism is a diploid (or user-specified ploidy) eukaryote where haplotype phasing via parental k-mers makes sense.

## Do not use when
- You have no parental data — use a non-trio k-mer profiling sketch that runs Meryl + GenomeScope on the child reads only.
- You want to actually assemble contigs — this sketch only produces k-mer databases and GenomeScope profiles; pass the Meryl DBs into a separate HiFi assembly sketch (e.g. hifiasm-trio).
- You want Merqury-based assembly QV/completeness scoring of an existing assembly — that is a downstream sketch that consumes the Meryl DBs produced here.
- Your input is short-read-only or ONT-only for the child — this workflow assumes HiFi for the child track.
- Your organism is haploid (bacterial/viral) — k-mer profiling with GenomeScope ploidy=2 is not meaningful; use a haploid QC sketch.

## Analysis outline
1. Ingest three read collections: child HiFi FASTQ, paternal Illumina FASTQ, maternal Illumina FASTQ, plus k-mer length and ploidy parameters.
2. Count k-mers for paternal Illumina reads with Meryl (`count`) to produce a paternal meryldb.
3. Count k-mers for maternal Illumina reads with Meryl (`count`) to produce a maternal meryldb.
4. Run Meryl in `trio-mode` over child HiFi + both parental read sets to emit child, paternal-specific and maternal-specific meryldbs plus their histograms.
5. Union-sum the per-element paternal and maternal meryldbs with Meryl `groups union-sum` to get one merged database per parent.
6. Derive k-mer histograms from the merged paternal and maternal meryldbs with Meryl `histogram`.
7. Run GenomeScope2 on the child histogram to estimate genome size, heterozygosity, repeats, and model parameters (linear, log, transformed linear, transformed log plots + summary + model).
8. Run GenomeScope2 on the paternal and maternal histograms to produce parental k-mer profiles (linear and log plots + summary).
9. Collect outputs: three Meryl DBs (child, maternal, paternal) and three GenomeScope profile sets as workflow outputs; render them in the workflow report.

## Key parameters
- `K-mer length`: integer, default `21` (standard VGP choice for vertebrate genomes; lower only for tiny test data).
- `Ploidy`: integer, default `2` for diploid vertebrates; set to match the target organism's ploidy.
- Meryl `count_operation`: `count` for per-parent counting; `trio-mode` for the combined child+parents step; `union-sum` to merge per-element meryldbs; `histogram` to produce the GenomeScope input.
- GenomeScope2 output options: enable `model_output` and `summary_output`; `testing` flag is enabled only for the child profile (emits extra `model_params` tabular).
- Inputs must be Galaxy dataset collections (type `list`) of `fastqsanger` — parental inputs no longer need to be paired lists since v0.1.

## Test data
The test profile uses three small FASTQ collections hosted on Zenodo record 6603774: a child HiFi collection (`child.fastq`) and two Illumina parental collections that point at `paternal.fastq` and `maternal.fastq` (the maternal/paternal role labels are intentionally swapped in the test job as a smoke test of role handling). K-mer length is overridden to `9` and ploidy to `1` to keep the run tractable on the tiny inputs. Expected assertions: the child GenomeScope summary text contains size strings such as `43,763 bp`; the child, paternal, and maternal Meryl databases have approximate sizes of ~205051, ~40338, and ~49534 bytes respectively (±1000); the three GenomeScope linear PNG plots match reference images within a 15000-byte similarity delta.

## Reference workflow
Galaxy IWC `VGP-assembly-v2/kmer-profiling-hifi-trio-VGP2`, release 0.1.6 (CC-BY-4.0), by the Vertebrate Genomes Project and Galaxy. Tools: Meryl 1.3+galaxy6/7 (`meryl_count_kmers`, `meryl_groups_kmers`, `meryl_histogram_kmers`, and the `trio-mode` meryl tool), GenomeScope 2.0.1+galaxy0, and `pick_value` 0.2.0 for default parameter handling. This is Workflow #2 of the VGP assembly pipeline; its Meryl outputs feed the downstream VGP trio assembly and Merqury QC workflows.
