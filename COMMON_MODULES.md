# Common modules across sketches

This document is a design-level survey of the 258 sketches in `sketches/`. It identifies recurring tool sequences ("modules") that appear across multiple workflows, surfaces redundant tools that fill the same role, and recommends a canonical, modern choice for each.

It is not a refactor — sketch files are unchanged. The intent is to inform a future pass that factors shared steps out of individual sketches.

## Methodology

1. Parsed YAML frontmatter from every `sketches/**/SKETCH.md` (258 sketches, 14 domains) and extracted the `tools:` field.
2. Computed (a) tool frequency across the corpus and (b) pairwise tool co-occurrence.
3. Probed candidate modules by querying for sketches that declare a candidate tool set (e.g. `bwa-mem ∧ picard-markduplicates`).
4. Spot-checked sketch bodies in the densest clusters (qc, rna-seq, variant-calling, epigenomics, assembly) to confirm the tools are actually used in sequence rather than as alternatives.
5. Modernity calls below reflect 2026-era community defaults from nf-core, Galaxy IWC, and the broader ecosystem.

## Tool frequency (top 40)

| Count | Tool | Role |
| ----- | ---- | ---- |
| 138 | multiqc | Aggregate QC report |
|  74 | samtools | BAM/CRAM/SAM utilities |
|  70 | fastqc | Raw read QC |
|  45 | fastp | Read trimming + QC |
|  31 | bowtie2 | Short-read aligner |
|  29 | bedtools | Interval arithmetic |
|  22 | bcftools | VCF utilities + calling |
|  22 | star | Splice-aware RNA aligner |
|  19 | minimap2 | Long-read / general aligner |
|  18 | picard | BAM manipulation (incl. MarkDuplicates) |
|  17 | bwa-mem | Short-read aligner (legacy build) |
|  15 | cutadapt | Adapter trimming |
|  15 | trim-galore | Cutadapt + FastQC wrapper |
|  15 | snpeff | Variant annotation |
|  13 | bwa-mem2 | Short-read aligner (modern build) |
|  12 | busco | Assembly completeness |
|  12 | snpsift | VCF filtering |
|  12 | kraken2 | Taxonomic classification |
|  12 | quast | Assembly quality |
|  11 | bwa | Short-read aligner (legacy `aln`/`mem`) |
|  11 | qualimap | BAM QC |
|  11 | deeptools | Coverage / BigWig / heatmaps |
|  11 | picard-markduplicates | Duplicate marking |
|  10 | gfastats | Assembly stats (VGP) |
|   9 | qiime2 | Amplicon/metabarcoding suite |
|   9 | macs2 | Peak calling |
|   9 | featurecounts | Read summarization |
|   9 | preseq | Library complexity |
|   9 | lofreq | Low-frequency variant caller |
|   8 | trimmomatic | Read trimming (legacy) |
|   8 | seqtk | FASTQ/FASTA utilities |
|   8 | ivar | Amplicon trimming + consensus |
|   8 | tooldistillator | Galaxy bacterial QC aggregator |
|   8 | deseq2 | Differential expression |
|   7 | gffread | GFF/GTF utilities |
|   7 | diamond | Protein search |
|   7 | bandage | Assembly graph visualization |
|   7 | compleasm | Assembly completeness (modern BUSCO replacement) |
|   7 | merqury | k-mer assembly evaluation |
|   7 | umi-tools | UMI deduplication |

The QC stack (`fastqc`/`fastp`/`multiqc`) and read-mapping stack (`samtools` + an aligner) dominate. MultiQC alone is referenced in 138/258 (54 %) sketches, which makes it the single strongest cross-cutting module signal.

## Catalogue of common modules

Each module below is presented as: **purpose → canonical sequence (preferred tools) → alternatives observed → representative sketches**.

### M1. Short-read raw QC + report
Run on raw FASTQ before anything else; aggregated into a single MultiQC report.
- **Canonical:** `fastqc → multiqc`
- **Alternatives:** none — this is essentially universal. 65 sketches declare the pair.
- **Examples:** `qc/short-read-fastqc-multiqc`, `qc/sequencing-read-qc-report`, `rna-seq/bulk-rnaseq-paired-end-star-quantification`, `epigenomics/atac-seq-peak-calling-differential`, `variant-calling/germline-exome-variant-calling-human`.

### M2. Short-read trimming + post-trim QC
- **Canonical:** `fastp` (does QC + adapter + quality trimming in one pass) `→ multiqc`
- **Alternatives:** `trim-galore` (cutadapt+fastqc wrapper, 15 sketches — fine for ChIP/ATAC/methyl conventions); `cutadapt` standalone (15 sketches — keep for amplicon/UMI use cases that need explicit primer trimming); `trimmomatic` (8 sketches — legacy).
- **Recommendation:** prefer `fastp` for new sketches. Keep `cutadapt` only where primer/adapter specificity matters (amplicon, small-RNA, iCLIP). Retire `trimmomatic` references.
- **Examples:** `qc/short-read-fastq-qc-trim`, `assembly/bacterial-genome-assembly-short-read`, `epigenomics/chip-seq-peak-calling-paired-end`, `metagenomics/shotgun-metagenome-assembly-binning`.

### M3. Short-read alignment + post-processing
- **Canonical:** `bwa-mem2 → samtools sort/index → picard MarkDuplicates → samtools flagstat/stats`
- **Alternatives:** `bwa-mem` (17), `bwa` classic (11) — both supersede by `bwa-mem2`. `bowtie2` (31) is preferred for ChIP/ATAC/Bismark contexts (sensitive end-to-end / soft-clip behaviour matches those tools' defaults).
- **Recommendation:** new variant-calling sketches use `bwa-mem2`; epigenomics sketches keep `bowtie2`. Retire bare `bwa`.
- **Examples:** `variant-calling/germline-exome-variant-calling-human`, `variant-calling/haploid-wgs-variant-calling-paired-end`, `variant-calling/sars-cov-2-wgs-illumina-pe-variant-calling`.

### M4. BAM-level QC bundle
Often appended to M3 before variant calling.
- **Canonical:** `samtools stats → qualimap → picard CollectMultipleMetrics → preseq → multiqc`
- **Examples:** `variant-calling/germline-exome-variant-calling-human`, `variant-calling/ancient-dna-short-read-preprocessing-mapping`, `epigenomics/atac-seq-peak-calling-differential`, `epigenomics/bisulfite-methylation-bismark`.

### M5. Long-read alignment
- **Canonical:** `minimap2 → samtools sort/index`
- **Alternatives:** none competitive for ONT/PacBio at this point; `winnowmap` only when long repeats matter.
- **Examples:** `assembly/long-read-genome-assembly`, `epigenomics/long-read-methylation-calling`, `variant-calling/sars-cov-2-artic-ont-variant-calling`, `metagenomics/host-decontamination-long-reads`.

### M6. Long-read raw QC
Distinct from M1 because FastQC is uninformative for long reads.
- **Canonical:** `nanoplot → multiqc` (and `pycoqc` for ONT basecaller summaries)
- **Alternatives:** `longqc`.
- **Examples:** `qc/genome-skim-read-qc`, `qc/nanopore-host-depletion-preprocessing`, `assembly/long-read-genome-assembly`, `metagenomics/kraken2-krona-taxonomy-profiling-nanopore`.

### M7. Bulk RNA-seq quantification
- **Canonical:** two flavours, both legitimate:
  - **Alignment-based:** `fastp → STAR → samtools → featureCounts → multiqc`
  - **Pseudoalignment:** `fastp → salmon → tximport → multiqc`
- **Alternatives:** `hisat2` (declining), `tophat` (legacy — drop), `kallisto` (interchangeable with salmon).
- **Recommendation:** keep both flavours; recommend salmon for pure quantification, STAR when downstream needs splicing/variants/fusions.
- **Examples:** `rna-seq/bulk-rnaseq-paired-end-star-quantification`, `rna-seq/bulk-rnaseq-quantification-eukaryote`, `rna-seq/dual-rnaseq-host-pathogen`.

### M8. RNA-seq post-alignment QC
- **Canonical:** `rseqc → qualimap rnaseq → preseq → multiqc`
- **Examples:** `rna-seq/bulk-rnaseq-paired-end-star-quantification`, `rna-seq/bulk-rnaseq-quantification-eukaryote`, `rna-seq/cage-seq-tss-profiling`, `rna-seq/nascent-transcript-tre-calling`.

### M9. Differential expression
- **Canonical:** `featureCounts | salmon → DESeq2`
- **Alternatives:** `edgeR`, `limma-voom` (each appears in 1–2 sketches; keep both alongside DESeq2 as documented choices).
- **Examples:** `rna-seq/bulk-rnaseq-differential-expression`, `rna-seq/two-condition-rnaseq-differential-expression`, `rna-seq/slamseq-transcriptional-output`.

### M10. UMI-aware short-read processing
- **Canonical:** `umi-tools extract → align → umi-tools dedup` (or `fgbio GroupReadsByUmi → CallMolecularConsensusReads` for duplex/consensus).
- **Examples:** `rna-seq/allele-specific-expression-rnaseq-umi`, `rna-seq/ribosome-profiling-orf-translation`, `variant-calling/umi-consensus-reads-fgbio`, `variant-calling/untargeted-viral-consensus-metagenomic`.

### M11. ChIP/ATAC/CUT&RUN peak calling
- **Canonical:** `trim-galore → bowtie2 → picard MarkDuplicates → macs2 → deeptools → multiqc`
- **Alternatives:** `macs3` (modern successor — recommend migrating); `seacr` for CUT&RUN-specific.
- **Recommendation:** plan to swap `macs2` → `macs3` in new sketches.
- **Examples:** `epigenomics/chip-seq-peak-calling-paired-end`, `epigenomics/atacseq-chromatin-accessibility-paired-end`, `epigenomics/cutandrun-histone-profiling`, `epigenomics/chipseq-consensus-peaks-single-end`.

### M12. Bisulfite / methylation
- **Canonical:** `trim-galore → bismark → methyldackel → multiqc`
- **Examples:** `epigenomics/bisulfite-methylation-bismark`.

### M13. Long-read methylation
- **Canonical:** `dorado/guppy basecall (mod) → minimap2 → modkit`
- **Examples:** `epigenomics/long-read-methylation-calling`.

### M14. Germline short variant calling (human)
- **Canonical:** `bwa-mem2 → MarkDuplicates → BQSR → GATK HaplotypeCaller → GenotypeGVCFs → bcftools norm → VEP/snpEff`
- **Alternatives observed:** `deepvariant` (`variant-calling/deep-learning-germline-variant-calling-human`), `freebayes` (haploid/ploidy-aware sketches), `bcftools call`.
- **Recommendation:** keep GATK as default; surface DeepVariant as the modern option for human WGS.
- **Examples:** `variant-calling/germline-exome-variant-calling-human`, `variant-calling/rare-disease-wgs-family-prioritization`, `variant-calling/population-variant-catalogue-human-wgs`, `variant-calling/ploidy-aware-germline-variant-calling-short-read`.

### M15. Somatic variant calling (tumour/normal)
- **Canonical:** `bwa-mem2 → MarkDuplicates → BQSR → Mutect2 → FilterMutectCalls → bcftools norm → VEP`
- **Alternatives:** `strelka2`, `varscan2` (legacy — drop for new work), `hmftools` for full clinical WGTS.
- **Examples:** `variant-calling/somatic-variant-calling-tumor-normal-human`, `variant-calling/pacbio-hifi-tumor-normal-somatic`, `variant-calling/comprehensive-cancer-wgts-hmftools`, `variant-calling/rna-somatic-variant-calling-tumor-normal`.

### M16. Low-frequency / viral variant calling
- **Canonical (Illumina):** `fastp → bwa-mem2 → MarkDuplicates → lofreq → snpeff/snpsift → bcftools consensus`
- **Alternatives / amplicon:** `ivar trim → ivar variants → ivar consensus` (8 sketches, all amplicon viral).
- **Recommendation:** keep both — `lofreq` for shotgun viral / intrahost; `ivar` exclusively for amplicon protocols (ARTIC, etc.).
- **Examples:** `variant-calling/low-frequency-variant-calling-viral-wgs`, `variant-calling/viral-intrahost-low-frequency-variants`, `variant-calling/sars-cov-2-illumina-amplicon-ivar`, `variant-calling/sars-cov-2-artic-ont-variant-calling`.

### M17. Variant annotation + reporting
- **Canonical:** `bcftools norm → snpEff → snpSift → tabular report`
- **Alternatives:** `VEP` (preferred for human clinical contexts), `annovar` (license issues — avoid).
- **Recommendation:** snpEff/snpSift remains canonical for microbial/viral; default to VEP for human germline/somatic.
- **Examples:** `variant-calling/variant-report-tabulation-snpeff-vcf`, `variant-calling/sars-cov-2-variant-reporting`, `variant-calling/haploid-wgs-variant-calling-paired-end`, `variant-calling/germline-exome-variant-calling-human`.

### M18. Short-read de novo assembly (bacterial)
- **Canonical:** `fastp → spades (or shovill = spades + polish) → quast → busco/checkm2 → bandage`
- **Alternatives:** `unicycler` for hybrid; `skesa` for outbreak-scale typing.
- **Examples:** `assembly/bacterial-genome-assembly-short-read`, `assembly/bacterial-short-read-assembly-shovill`, `assembly/hybrid-denovo-assembly-bacterial`.

### M19. Long-read / HiFi de novo assembly
- **Canonical:** `hifiasm (HiFi) | flye (ONT) → purge_dups → minimap2 polish (medaka/racon for ONT) → quast → compleasm/busco → merqury`
- **Recommendation:** prefer `compleasm` over `busco` for new sketches (faster, miniprot-based, drop-in for completeness scoring); BUSCO is still acceptable but compleasm is the modern default in the VGP-style assemblies.
- **Examples:** `assembly/hifi-contig-assembly-vertebrate-vgp`, `assembly/long-read-genome-assembly`, `assembly/long-read-de-novo-assembly-flye`, `assembly/phased-diploid-assembly-hifi-hic`.

### M20. Assembly QC bundle (VGP-style)
- **Canonical:** `gfastats → compleasm → merqury → meryl k-mer DB`
- **Examples:** `assembly/hic-pretext-contact-map-assembly-curation`, `assembly/purge-haplotypic-duplicates-diploid-assembly`, `assembly/trio-phased-diploid-assembly-hifi`, `qc/multi-genome-assembly-qc-comparison`.

### M21. Taxonomic profiling (k-mer)
- **Canonical:** `kraken2 → bracken → krona`
- **Alternatives:** `centrifuge` (declining), `metaphlan4` (marker-gene, complementary not redundant).
- **Examples:** `metagenomics/kraken2-krona-taxonomy-profiling-nanopore`, `metagenomics/shotgun-metagenomic-taxonomic-profiling-multi-tool`, `qc/short-read-qc-and-taxonomic-screen`, `qc/host-read-decontamination`.

### M22. Host decontamination
- **Canonical (short read):** `fastp → bowtie2/bwa-mem2 vs host → samtools view -f 4 → seqkit/samtools fastq`
- **Canonical (long read):** `minimap2 vs host → samtools view -f 4`
- **Examples:** `qc/host-read-decontamination`, `metagenomics/host-decontamination-long-reads`, `qc/nanopore-host-depletion-preprocessing`, `metagenomics/coprolite-host-identification-ancient`.

### M23. Amplicon ASV (16S/ITS) — QIIME2
- **Canonical:** `qiime2 import → cutadapt (primer) → dada2 → qiime2 phylogeny/diversity/taxonomy`
- **Examples:** `amplicon/amplicon-16s-asv-illumina-paired`, `amplicon/amplicon-dada2-denoising-paired-qiime2`, `amplicon/amplicon-alpha-beta-diversity-qiime2`, `amplicon/amplicon-qiime2-phylogeny-rarefaction-taxonomy`.

### M24. Bacterial annotation + typing (Galaxy IWC stack)
- **Canonical:** `bakta (or prokka) → abricate → mlst/cgmlst → tooldistillator`
- **Recommendation:** prefer `bakta` over `prokka` for new bacterial annotation (actively maintained, modern DB layout); keep `prokka` only where existing reference outputs require parity.
- **Examples:** `annotation/bacterial-genome-annotation`, `annotation/amr-virulence-gene-detection-bacterial-assembly`, `annotation/cgmlst-bacterial-strain-typing`, `qc/bacterial-assembly-qc-contamination`.

### M25. Functional / protein search
- **Canonical:** `diamond blastp → eggnog-mapper / interproscan / hmmer`
- **Examples:** `annotation/functional-annotation-protein-dna-sequences`, `metagenomics/microbiome-functional-profiling-reads`, `metagenomics/metatranscriptome-denovo-assembly-annotation`, `annotation/ortholog-consensus-protein`.

### M26. Proteomics DDA/DIA quantification
- **Canonical:** `openms` suite (`FileConverter → FeatureFinder → IDMapper → ProteinQuantifier`) → `MSstats`
- **Alternatives:** `MaxQuant` (still common in DDA), `DIA-NN` (preferred modern DIA — currently only implicit; consider promoting).
- **Examples:** `proteomics/dia-proteomics-quantification`, `proteomics/label-free-proteomics-quantification`, `proteomics/tmt-isobaric-dda-proteomics`, `proteomics/immunopeptidomics-mhc-dda`.

## Redundancy resolution

Where multiple tools serve the same role, prefer the modern option for new sketches. The "keep" column lists contexts in which the legacy choice is still legitimate.

| Role | Legacy / less-modern | Preferred (2026) | Keep legacy when |
| ---- | -------------------- | ----------------- | ----------------- |
| Adapter / quality trimming | `trimmomatic`, `trim-galore` | `fastp` | ChIP/ATAC/Bismark sketches that follow nf-core conventions on `trim-galore`; primer trimming → `cutadapt` |
| Short-read alignment | `bwa` (aln), `bwa-mem` | `bwa-mem2` | Bowtie2 stays for ChIP/ATAC/Bismark; tooldistillator/Galaxy bacterial pipelines pinned to `bwa-mem` |
| Long-read alignment | `ngmlr`, `last` | `minimap2` | — |
| Splice-aware RNA align | `tophat`, `hisat2` | `STAR` (or `salmon` pseudoalign) | `hisat2` for very low-RAM contexts |
| Variant annotation (human) | `annovar` | `VEP` | Microbial / viral → `snpEff` is fine |
| Duplicate marking | `samtools markdup`, `picard MarkDuplicates` | `picard MarkDuplicates` (or `gatk4 MarkDuplicatesSpark`) | UMI-aware → `umi-tools dedup` / `fgbio` |
| Peak calling | `macs2` | `macs3` | CUT&RUN-specific → `seacr` |
| Assembly completeness | `busco` | `compleasm` | Lineages without compleasm DBs |
| Variant caller (human germline) | `samtools+bcftools call`, `varscan` | `gatk HaplotypeCaller` or `deepvariant` | Haploid / pooled / non-human → `freebayes`, `bcftools call`, `lofreq` |
| Somatic caller | `varscan2`, `mutect (v1)` | `mutect2` (+ `strelka2` ensemble) | — |
| Bacterial annotation | `prokka` | `bakta` | Reproducing published `prokka`-based reference outputs |
| FASTA/FASTQ utilities | `seqtk` | `seqkit` | Both are fine; prefer `seqkit` for new code (richer subcommands, active dev) |
| Krona-only taxonomy viewer | `krona` (still standard) | keep | — |

## Suggested next steps

1. **Encode modules as reusable sketch fragments.** Add a top-level `sketches/_modules/` (or `modules/`) directory containing one `MODULE.md` per entry above (M1–M26). Each module file would carry the canonical sequence, parameter notes, and alternatives — sketches then reference them by id rather than re-describing QC every time.
2. **Add a `modules:` field to `schema.py`.** Frontmatter would gain `modules: [m01-short-read-qc, m03-short-read-align, m14-germline-variant-call]`. The validator can then assert that any tool used in a module is also declared in `tools:`, and conversely that tool combinations matching a module are tagged.
3. **Targeted modernization pass.** Rewrite (in priority order):
   - 8 `trimmomatic` sketches → `fastp`,
   - 11 bare `bwa` sketches → `bwa-mem2` or `bowtie2` (per M3 rules),
   - new ChIP/ATAC sketches → `macs3`,
   - new bacterial annotation sketches → `bakta`.
   Mark each rewrite with a CHANGELOG entry so downstream agents know the canonical choice changed.
4. **Lint for module hygiene.** Extend `validate.py` to flag sketches that declare a trimming tool but no MultiQC, an aligner but no `samtools`, or a variant caller but no annotation tool — these are almost always incomplete sketches.
5. **Document the long-read QC gap.** `nanoplot` / `pycoqc` are referenced in markdown bodies but rarely in the `tools:` field; backfilling would make M6 discoverable via the same query path used for the other modules.
