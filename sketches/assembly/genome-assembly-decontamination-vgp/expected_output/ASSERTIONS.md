# Content assertions (no golden file checked in)
## masking_action_report
Content assertions for `Masking Action Report`.

- has_text: seq_00010	745809	FIX	100001..100058

## taxonomy_report
Content assertions for `Taxonomy Report`.

- has_text: seq_00017	85779	0,13059,0,0,0,0,0	3864	|	Bacteroides massiliensis

## contaminants_sequences
Content assertions for `Contaminants sequences`.

- has_text: >seq_00238
- has_n_lines: {'n': 14}

## mitochondrial_scaffolds
Content assertions for `Mitochondrial Scaffolds`.

- has_text: seq_00500

## adaptor_report
Content assertions for `Adaptor Report`.

- has_text: seq_00010	745809	ACTION_TRIM	100001..100058

## final_decontaminated_assembly
Content assertions for `Final Decontaminated Assembly`.

- not_has_text: seq_00500
- not_has_text: seq_00238
- has_text: seq_00024

