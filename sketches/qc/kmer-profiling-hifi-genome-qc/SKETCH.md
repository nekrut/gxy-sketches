---
name: kmer-profiling-hifi-genome-qc
description: Use when you have PacBio HiFi long reads and need to profile k-mer content
  to estimate genome size, heterozygosity, repeat content, and homozygous read coverage
  before running a genome assembly. Produces a Meryl k-mer database, GenomeScope2
  plots/summary, HiFi read statistics (rdeval), and a Mash distance heatmap across
  HiFi datasets. This is VGP assembly workflow 1 and its outputs parameterize downstream
  VGP assembly/polishing/evaluation steps.
domain: qc
organism_class:
- eukaryote
- vertebrate
- diploid
input_data:
- long-reads-pacbio-hifi
- kmer-length
- ploidy
source:
  ecosystem: iwc
  workflow: K-mer profiling and reads statistics VGP1
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/VGP-assembly-v2/kmer-profiling-hifi-VGP1
  version: '0.9'
  license: CC-BY-4.0
  slug: VGP-assembly-v2--kmer-profiling-hifi-VGP1
tools:
- name: meryl
  version: 1.4.1+galaxy0
- name: genomescope2
  version: 2.1.0+galaxy0
- name: rdeval
  version: 0.0.9+galaxy0
- name: mash
- name: imagemagick
  version: 7.1.2-2+galaxy1
tags:
- vgp
- kmer
- genomescope
- meryl
- hifi
- pacbio
- genome-profiling
- coverage-estimation
- heterozygosity
- pre-assembly-qc
test_data:
- role: collection_of_pacbio_data__m54306u_210519_154448
  url: https://zenodo.org/records/17246010/files/Collection%20of%20Pacbio%20Data_m54306U_210519_154448.hifi_reads.fastq.gz.fastqsanger.gz
  sha1: 61278426af8c39957816c1646afcfe917466bb0b
- role: collection_of_pacbio_data__m54306u_210521_004211
  url: https://zenodo.org/records/17246010/files/Collection%20of%20Pacbio%20Data_m54306U_210521_004211.hifi_reads.fastq.gz.fastqsanger.gz
  sha1: 3b1293432d3f93b1168dce65bef7d6d2d0883006
- role: collection_of_pacbio_data__m54306ue_210629_211205
  url: https://zenodo.org/records/17246010/files/Collection%20of%20Pacbio%20Data_m54306Ue_210629_211205.hifi_reads.fastq.gz.fastqsanger.gz
  sha1: 8c46ed5c64acd2031a0727816cc7fee8f8763adb
- role: collection_of_pacbio_data__m54306ue_210719_083927
  url: https://zenodo.org/records/17246010/files/Collection%20of%20Pacbio%20Data_m54306Ue_210719_083927.hifi_reads.fastq.gz.fastqsanger.gz
  sha1: 9cecd396e3fbfc91d31197f1d226fe6bebcd71ec
- role: collection_of_pacbio_data__m64055e_210624_223222
  url: https://zenodo.org/records/17246010/files/Collection%20of%20Pacbio%20Data_m64055e_210624_223222.hifi_reads.fastq.gz.fastqsanger.gz
  sha1: b9ac2600bd4f2e52dff44d7132c95c2311fbb62b
expected_output:
- role: data_for_interactive_heatmap
  description: Content assertions for `Data for Interactive HeatMap`.
  assertions:
  - "has_text: m54306U_210521_004211\tm54306U_210519_154448\t0.0215695"
- role: merged_meryl_database
  description: Content assertions for `Merged Meryl Database`.
  assertions:
  - 'has_size: {''value'': ''14000000'', ''delta'': ''2000000''}'
- role: genomescope_summary
  description: Content assertions for `GenomeScope summary`.
  assertions:
  - 'has_text: 97.6946%'
- role: genomescope_model_parameters
  description: Content assertions for `GenomeScope Model Parameters`.
  assertions:
  - 'has_text: 0.283605968625878'
- role: montage_genomescope
  description: Content assertions for `Montage Genomescope`.
  assertions:
  - 'has_size: {''value'': ''1200000'', ''delta'': ''200000''}'
- role: estimated_genome_size_file
  description: Content assertions for `Estimated Genome Size File`.
  assertions:
  - 'has_text: 1287751'
- role: merged_read_statistics
  description: Content assertions for `Merged Read Statistics`.
  assertions:
  - "has_text: reads\t594\t618"
- role: rdeval_report
  description: Content assertions for `Rdeval report`.
  assertions:
  - 'has_size: {''value'': ''1170000'', ''delta'': ''200000''}'
- role: heatmap
  description: Content assertions for `HeatMap`.
  assertions:
  - 'has_size: {''value'': ''100000'', ''delta'': ''20000''}'
---

# K-mer profiling and HiFi read QC (VGP Workflow 1)

## When to use this sketch
- You have one or more PacBio HiFi FASTQ datasets for a eukaryote (typically a vertebrate) and want to profile them before assembly.
- You need a Meryl k-mer database to feed downstream assembly evaluation (Merqury) and VGP workflows 2+ (assembly, purge_dups, scaffolding, polishing).
- You want GenomeScope2-based estimates of genome size, heterozygosity, repeat content, and homozygous k-mer/read coverage to parameterize later steps.
- You want per-sample HiFi read statistics (read count, N50, length distribution, estimated coverage) via rdeval, plus a QC cross-check that multiple HiFi libraries come from the same individual via Mash pairwise distances.
- Diploid or low-ploidy eukaryotes where GenomeScope2's mixture model is appropriate (ploidy=1..4).

## Do not use when
- You have Illumina short reads only — use a short-read k-mer profiling sketch (Meryl/GenomeScope from Illumina) instead.
- You have Oxford Nanopore reads without HiFi-quality accuracy — rdeval HiFi QC and the k-mer spectra assumptions will be misleading; profile with a long-read-specific QC sketch.
- You already have an assembly and want to evaluate it against a k-mer db — this sketch only builds the db and profiles reads; run a Merqury/Merfin evaluation sketch next.
- You want the actual contig assembly — this is the pre-assembly profiling step; chain into VGP workflow 2 (hifiasm assembly) afterwards.
- You need variant calling, annotation, or metagenomic profiling — wrong domain entirely.

## Analysis outline
1. Accept a list collection of PacBio HiFi FASTQ(.gz) files plus species name, assembly name, k-mer length, and ploidy as workflow parameters.
2. Count k-mers per input file with `meryl count` using the user-supplied k (Meryl 1.4.1).
3. Merge per-sample Meryl databases with `meryl union-sum` into a single Merged Meryl Database (tagged for downstream Merqury use).
4. Generate a k-mer frequency histogram from the merged db with `meryl histogram`.
5. Run GenomeScope2 on the histogram with the given k-mer length and ploidy, producing linear/log/transformed plots, summary, model, and model parameters.
6. Montage the GenomeScope linear and log plots into a single PNG for reporting (ImageMagick).
7. Parse the GenomeScope model to extract the homozygous k-mer coverage (`kmercov` line) as a float parameter.
8. Parse the GenomeScope summary to extract the haploid estimated genome size as an integer parameter.
9. Run rdeval on the HiFi read collection using the estimated genome size to compute per-sample read statistics; join them into a Merged Read Statistics TSV and emit an HTML rdeval report.
10. Conditionally (only when the input collection contains >1 sample, checked via a helper subworkflow) run a Mash subworkflow: `mash sketch` (k=21, sketch size 1000) per sample, `mash paste` to combine, `mash dist` all-vs-all, reshape and draw a `heatmap2` pairwise-distance heatmap to flag cross-contamination or mislabelled libraries.

## Key parameters
- `K-mer length`: integer, default 21. Use 21 for vertebrate-sized genomes; increase for larger/more repetitive genomes only with reason.
- `Ploidy`: integer, default 2. Must match the organism (1 haploid, 2 diploid, up to 4 for GenomeScope2's tetraploid model).
- Meryl `count_operation`: `count`; merge operation: `union-sum` — do not change, Merqury expects this layout.
- GenomeScope2: `kmer_length` and `ploidy` wired from workflow inputs; outputs include `model_output` and `summary_output`; other advanced fields left at tool defaults.
- Mash sketch: fixed `kmer_size=21`, `sketch_size=1000`, `prob_threshold=0.01`, single-end reads mode — these are tuned for HiFi-vs-HiFi library comparison and should not be edited.
- rdeval: `expected_gsize` wired from the parsed GenomeScope estimated genome size; `stats_flavor=stats`, output type `rd_file` so the downstream `rdeval report` step can consume it.
- Mash QC subworkflow runs only when the `Has multiple samples` gate evaluates true (i.e. the input collection has ≥2 elements).

## Test data
Five PacBio HiFi FASTQ.gz samples hosted on Zenodo (record 17246010): `m54306U_210519_154448`, `m54306U_210521_004211`, `m54306Ue_210629_211205`, `m54306Ue_210719_083927`, and `m64055e_210624_223222`, supplied as a list collection with Species Name "Test Species", Assembly Name "toLidId", k-mer length 21, and ploidy 2. A successful run produces a Merged Meryl Database ~14 MB (±2 MB), a GenomeScope summary containing the model fit `97.6946%`, GenomeScope model parameters containing `0.283605968625878`, an Estimated Genome Size File containing `1287751` bp, a GenomeScope montage PNG ~1.2 MB, Merged Read Statistics whose `reads` row reads `594\t618`, an rdeval HTML report ~1.17 MB, and — because there are multiple HiFi libraries — a Mash heatmap PNG ~100 kB plus a melted Mash-distance TSV where the `m54306U_210521_004211` vs `m54306U_210519_154448` pairwise distance is `0.0215695`.

## Reference workflow
Galaxy IWC `workflows/VGP-assembly-v2/kmer-profiling-hifi-VGP1`, release 0.9, "K-mer profiling and reads statistics VGP1" (CC-BY-4.0), authored by the Vertebrate Genomes Project and Galaxy. This is step 1 of the VGP assembly v2 pipeline; downstream workflows (VGP2+) consume the Merged Meryl Database, Homozygous Read Coverage, and Estimated Genome Size produced here.
