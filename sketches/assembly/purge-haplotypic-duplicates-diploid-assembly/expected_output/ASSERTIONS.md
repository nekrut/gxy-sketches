# Content assertions (no golden file checked in)
## cutoffs_for_primary_assembly
Content assertions for `Cutoffs for primary assembly`.

- has_text: 1	15	15	16	16	48

## purged_primary_assembly
Content assertions for `Purged Primary Assembly`.

- has_n_lines: {'n': 156}

## purged_primary_assembly_gfa
Content assertions for `Purged Primary Assembly (gfa)`.

- has_n_lines: {'n': 157}

## cutoffs_for_alternate_assembly
Content assertions for `Cutoffs for alternate assembly`.

- has_text: 1	15	15	16	16	48

## purged_alternate_assembly
Content assertions for `Purged Alternate Assembly`.

- has_n_lines: {'n': 144}
- has_text: contig_2.alt

## purged_alternate_assembly_gfa
Content assertions for `Purged Alternate assembly (gfa)`.

- has_n_lines: {'n': 145}

## assembly_statistics_for_purged_assemblies
Content assertions for `Assembly statistics for purged assemblies`.

- has_text: # contigs	78	72

## nx_plot
Content assertions for `Nx Plot`.

- has_size: {'value': 61000, 'delta': 5000}

## merqury_on_phased_assemblies_stats
Content assertions for `Merqury on Phased assemblies: stats`.

- output_merqury.completeness: has_text: both	all	1212740	1300032	93.2854

## compleasm_on_purged_primary_hap1_assembly_translated_proteins
Content assertions for `Compleasm on purged primary/hap1 assembly: Translated Proteins`.

- has_n_lines: {'n': 40390}

## compleasm_on_purged_alternate_hap2_assembly_translated_proteins
Content assertions for `Compleasm on purged alternate/hap2 assembly: Translated Proteins`.

- has_n_lines: {'n': 40354}

## name_mapping_alternate_assembly
Content assertions for `Name mapping Alternate assembly`.

- has_text: h2tg000050l_path_1	contig_1.alt

