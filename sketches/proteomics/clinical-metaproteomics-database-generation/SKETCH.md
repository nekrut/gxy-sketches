---
name: clinical-metaproteomics-database-generation
description: Use when you need to build a compact, sample-specific protein sequence
  database for clinical metaproteomics searches, distilling a large host+microbial+contaminant
  FASTA down to only sequences supported by the actual MS/MS spectra via MetaNovo
  de novo tag matching. Produces a FASTA suitable for downstream database search engines.
domain: proteomics
organism_class:
- human
- microbiome
- mixed-host-microbial
input_data:
- protein-fasta-human
- protein-fasta-microbial
- protein-fasta-contaminants
- mgf-msms-spectra
source:
  ecosystem: iwc
  workflow: Generate a Clinical Metaproteomics Database
  url: https://github.com/galaxyproject/iwc/tree/main/workflows/proteomics/clinicalmp/clinicalmp-database-generation
  version: '0.1'
  license: CC-BY-4.0
tools:
- fasta_merge_files_and_filter_unique_sequences
- metanovo
- directag
- compomics
tags:
- metaproteomics
- clinical
- database-generation
- metanovo
- tmt
- host-microbiome
- mgf
- fasta
- galaxy-p
test_data:
- role: human_swissprot_protein_database
  url: https://zenodo.org/records/14181725/files/HUMAN-SwissProt-Protein-Database.fasta?download=1
  sha1: 79c3abb625d59ad68874ad09b66b25c4131b187f
  filetype: fasta
- role: species_uniprot_protein_database
  url: https://zenodo.org/records/14181725/files/Species_UniProt_FASTA.fasta?download=1
  sha1: a9eb443bc36eee24fdc124ddad0aee51b17acce7
  filetype: fasta
- role: contaminants_crap_protein_database
  url: https://zenodo.org/records/14181725/files/Contaminants(cRAP)-Protein-Database.fasta?download=1
  sha1: be5d772342f1e8d6f79cfe07ffcdfaf7bae85654
  filetype: fasta
- role: tandem_mass_spectrometry_ms_ms_datasets__ptrc_skubitz_plex2_f15_9aug19_rage_rep_19_06_08_mgf
  url: https://zenodo.org/records/14181725/files/PTRC_Skubitz_Plex2_F15_9Aug19_Rage_Rep-19-06-08.mgf?download=1
  sha1: 74b0db7ef696b05fa115190ffd0c854b8c420aca
- role: tandem_mass_spectrometry_ms_ms_datasets__ptrc_skubitz_plex2_f13_9aug19_rage_rep_19_06_08_mgf
  url: https://zenodo.org/records/14181725/files/PTRC_Skubitz_Plex2_F13_9Aug19_Rage_Rep-19-06-08.mgf?download=1
  sha1: 6320f5feb043422ddff8285f0496e4d9a016287c
- role: tandem_mass_spectrometry_ms_ms_datasets__ptrc_skubitz_plex2_f11_9aug19_rage_rep_19_06_08_mgf
  url: https://zenodo.org/records/14181725/files/PTRC_Skubitz_Plex2_F11_9Aug19_Rage_Rep-19-06-08.mgf?download=1
  sha1: 63d72e72e02c7c10fbb3248bfeed1d77c2ffc897
- role: tandem_mass_spectrometry_ms_ms_datasets__ptrc_skubitz_plex2_f10_9aug19_rage_rep_19_06_08_mgf
  url: https://zenodo.org/records/14181725/files/PTRC_Skubitz_Plex2_F10_9Aug19_Rage_Rep-19-06-08.mgf?download=1
  sha1: 7d8d9cfaf29b048929ff2f1f14b0ea474cae02c0
expected_output:
- role: human_uniprot_microbial_proteins_crap_for_metanovo
  description: Content assertions for `Human UniProt Microbial Proteins cRAP for MetaNovo`.
  assertions:
  - 'that: has_text'
  - 'text: >sp|'
- role: metanovo_compact_database
  description: Content assertions for `Metanovo Compact database`.
  assertions:
  - 'that: has_text'
  - 'text: >sp|'
- role: metanovo_compact_csv_database
  description: Content assertions for `Metanovo Compact CSV database`.
  assertions:
  - 'that: has_text'
  - 'text: index'
- role: human_uniprot_microbial_proteins_from_metanovo_crap
  description: Content assertions for `Human UniProt Microbial Proteins from MetaNovo
    cRAP`.
  assertions:
  - 'that: has_text'
  - 'text: >sp|'
---

# Clinical metaproteomics database generation

## When to use this sketch
- You are analyzing clinical MS/MS data (e.g. tumor, stool, BAL, plasma) where both human host and microbial proteins may be present and you need a tractable search database.
- You already have a large candidate FASTA (human reference proteome + broad microbial UniProt subset + cRAP contaminants) that is too big to search directly.
- You want to prune that candidate FASTA down to only proteins with de novo peptide tag evidence in your own MGF spectra before running a conventional database search.
- Spectra are TMT-labeled tryptic peptides acquired on high-resolution instruments (precursor ppm, fragment in Da/ppm).
- This is step 1 of the Galaxy-P clinical metaproteomics series; downstream steps (discovery, verification, quantification) consume the FASTA produced here.

## Do not use when
- You have a single organism and a well-defined reference proteome — use a standard target-decoy search workflow directly, no MetaNovo reduction needed.
- You are doing shotgun metagenomics or 16S taxonomic profiling (nucleotide, not protein) — use a metagenomics sketch instead.
- You need the downstream discovery / quantification stages of clinical MP — use the sibling `clinical-metaproteomics-discovery` / `clinical-metaproteomics-quantification` sketches.
- Your input is RAW Thermo files that have not been converted — convert to MGF first (msconvert) before entering this workflow.
- You only need to merge FASTA files without spectrum-driven reduction — run `fasta_merge_files_and_filter_unique_sequences` on its own.

## Analysis outline
1. Collect three input FASTAs: Human SwissProt, a species-level UniProt microbial FASTA, and the cRAP contaminants FASTA.
2. Merge the three FASTAs and deduplicate by sequence using `FASTA Merge Files and Filter Unique Sequences` to produce the large "Human + UniProt Microbial + cRAP" candidate database for MetaNovo.
3. Run `MetaNovo` on the MGF spectrum collection against the merged candidate FASTA: DirecTag generates de novo sequence tags, which are matched back to candidate proteins; only proteins supported by tag evidence are retained. Outputs a compact FASTA and a CSV index.
4. Merge the MetaNovo compact FASTA with Human SwissProt and cRAP again (and dedupe by sequence) to produce the final search-ready database that guarantees host and contaminant coverage alongside the spectrum-supported microbial subset.

## Key parameters
- **Merge uniqueness criterion**: `sequence` (dedupe identical sequences across sources).
- **Merge accession parser**: `^>([^ ]+).*$` (standard UniProt-style header).
- **MetaNovo enzyme**: Trypsin, no P rule; specificity `specific`; max missed cleavages `2`.
- **MetaNovo precursor tolerance**: `10 ppm`; fragment tolerance: `0.01 Da`.
- **MetaNovo fixed mods**: Carbamidomethylation of C, TMT 10-plex of K, TMT 10-plex of peptide N-term.
- **MetaNovo variable mods**: Oxidation of M.
- **Import peptide length**: min `8`, max `50`; exclude unknown PTMs.
- **Charge range**: `2`–`5`; fragment ions b/y.
- **DirecTag tag length**: `4`; max tag count `5`; TIC cutoff `85`; intensity classes `3`.
- **FDR levels**: PSM / peptide / protein all set to `1` (MetaNovo internal; real FDR is applied in the downstream discovery workflow).
- **Chunk size**: `100000` spectra per processing chunk.
- **Gene mapping**: enabled and auto-updated.

## Test data
The IWC test profile pulls three FASTA inputs from Zenodo record 14181725: `HUMAN-SwissProt-Protein-Database.fasta`, `Species_UniProt_FASTA.fasta` (a pre-selected microbial subset), and `Contaminants(cRAP)-Protein-Database.fasta`. The MS/MS collection is four TMT-labeled tryptic MGF fractions from the PTRC Skubitz Plex2 sarcoma study (`PTRC_Skubitz_Plex2_F10/F11/F13/F15_9Aug19_Rage_Rep-19-06-08.mgf`). Expected outputs are the merged pre-MetaNovo candidate FASTA (`Human UniProt Microbial Proteins cRAP for MetaNovo`), the MetaNovo compact FASTA (`Metanovo Compact database`), the MetaNovo CSV index (`Metanovo Compact CSV database`), and the final merged post-MetaNovo FASTA (`Human UniProt Microbial Proteins from MetaNovo cRAP`). The IWC assertions verify the FASTAs contain SwissProt-style `>sp|` headers and that the CSV contains an `index` column; no checksum comparison is performed because MetaNovo output ordering is non-deterministic.

## Reference workflow
Galaxy IWC `workflows/proteomics/clinicalmp/clinicalmp-database-generation` ("Generate a Clinical Metaproteomics Database"), release 0.1, CC-BY-4.0, by Subina Mehta (Galaxy-P). Companion GTN tutorial: `training.galaxyproject.org/training-material/topics/proteomics/tutorials/clinical-mp-1-database-generation/tutorial.html`. Key tool versions: `fasta_merge_files_and_filter_unique_sequences` 1.2.0, `metanovo` 1.9.4+galaxy4.
