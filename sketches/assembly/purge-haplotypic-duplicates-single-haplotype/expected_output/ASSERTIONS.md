# Content assertions (no golden file checked in)
## removed_haplotigs
Content assertions for `Removed haplotigs`.

- has_n_lines: {'n': 14}

## purged_assembly
Content assertions for `Purged assembly`.

- has_n_lines: {'n': 158}

## purged_assembly_gfa
Content assertions for `Purged assembly (GFA)`.

- has_n_lines: {'n': 160}

## assembly_statistics_for_both_assemblies
Content assertions for `Assembly statistics for both assemblies`.

- has_text: # scaffolds	79	79

## cutoffs
Content assertions for `Cutoffs`.

- has_text: 48

## purged_assembly_statistics
Content assertions for `Purged assembly statistics`.

- has_text: # scaffolds	79

## nx_plot
Content assertions for `Nx Plot`.

- has_size: {'value': 57000, 'delta': 5000}

## size_plot
Content assertions for `Size Plot`.

- has_size: {'value': 84000, 'delta': 5000}

## merqury_on_phased_assemblies_stats
Content assertions for `Merqury on Phased assemblies: stats`.

- output_merqury.completeness: has_text: 95.7636

## compleasm_on_purged_assembly_translated_proteins
Content assertions for `Compleasm on purged Assembly: Translated Proteins`.

- has_n_lines: {'n': 40374}

