# Content assertions (no golden file checked in)
## mmseqs2_taxonomy_tabular
Content assertions for `MMseqs2 Taxonomy Tabular`.

- has_text: Bacteria
- has_n_columns: {'n': 4}

## eggnog_annotations
Content assertions for `Eggnog Annotations`.

- has_text: #query
- has_n_columns: {'n': 21}

## mmseqs2_taxonomy_kraken
Content assertions for `MMseqs2 Taxonomy Kraken`.

- has_text: cellular root
- has_n_columns: {'n': 6}

## argnorm_amrfinderplus_report
Content assertions for `Argnorm AMRfinderplus Report`.

- has_text: Protein identifier

## resfinder
Content assertions for `Resfinder`.

- has_text: Isolate ID
- has_n_columns: {'n': 13}

## abricate_virulence_report
Content assertions for `Abricate Virulence Report`.

- has_text: #FILE
- has_n_columns: {'n': 15}

## multiqc_report
Content assertions for `MultiQC Report`.

- that: has_text
- text: AMRFinderPlus
- that: has_text
- text: ABRicate
- that: has_text
- text: starAMR
- that: has_text
- text: QUAST
- that: has_text
- text: MMseqs2 taxonomy
- that: has_text
- text: EggnogMapper

