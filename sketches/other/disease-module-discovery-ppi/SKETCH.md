---
name: disease-module-discovery-ppi
description: Use when you need to infer and evaluate network-medicine disease modules
  from a list of disease-associated seed genes/proteins against a human protein-protein
  interaction (PPI) network, for hypothesis generation, drug target discovery, or
  drug repurposing. Expects seed IDs (Entrez/Symbol/Ensembl/UniProt) and either a
  user PPI or a built-in network (STRING, BioGRID, HIPPIE, IID, NeDRex).
domain: other
organism_class:
- human
input_data:
- seed-gene-list
- ppi-network
source:
  ecosystem: nf-core
  workflow: nf-core/diseasemodulediscovery
  url: https://github.com/nf-core/diseasemodulediscovery
  version: dev
  license: MIT
tools:
- domino
- diamond
- robust
- robust-bias-aware
- rwr
- gprofiler2
- digest
- graph-tool
- drugst.one
- nedrex
- pyvis
- multiqc
tags:
- network-medicine
- disease-module
- ppi
- active-module-identification
- drug-repurposing
- interactome
- hypothesis-generation
test_data: []
expected_output: []
---

# Disease module discovery on PPI networks

## When to use this sketch
- You have a list of disease-associated seed genes or proteins (e.g. GWAS hits, differentially expressed genes, known disease genes) and want to find their local neighborhood / active module in the human interactome.
- You want to compare multiple active module identification methods (DOMINO, DIAMOnD, ROBUST, ROBUST bias-aware, RWR, 1st neighbors) on the same seeds/network.
- You want functional validation of the inferred module (pathway ORA via g:Profiler, functional coherence via DIGEST, topology stats) and optional drug repurposing suggestions via Drugst.One.
- You want robustness checks via seed leave-one-out and/or degree-preserving network rewiring.
- You can accept either supplying your own PPI edge list or one of the pipeline's built-in human PPI networks (STRING, BioGRID, HIPPIE, IID, NeDRex).

## Do not use when
- Your task is variant calling, RNA-seq quantification, assembly, or any read-level analysis — this pipeline takes gene/protein IDs, not sequencing data.
- You need organism-specific modules outside human; the built-in networks and NeDRex/Drugst.One annotations are human-only.
- You want de novo network construction from co-expression or single-cell data — bring a pre-built PPI.
- You only need generic pathway enrichment of a gene list without any network context — use a standalone g:Profiler/Enrichr workflow instead.
- You want drug-target binding affinity prediction or docking — Drugst.One here does centrality-based prioritization, not structural docking.

## Analysis outline
1. Parse input PPI network(s) with graph-tool into `.gt` and tool-specific formats (DOMINO `.sif`, DIAMOnD `.csv`, ROBUST `.tsv`, RWR `.csv`).
2. Validate seed file(s); drop seeds not present in the network and report the dropped set.
3. Run selected active module identification methods in parallel: DOMINO, DIAMOnD, ROBUST, ROBUST bias-aware, RWR, 1st neighbors, plus a seeds-only baseline.
4. Export each module as `.gt`, `.graphml`, and node/edge TSVs with per-tool node annotations (rank, p_hyper, significance, component_id, is_seed, spd).
5. Evaluate modules: g:Profiler ORA (module=foreground, network=background); DIGEST reference-free and reference-based functional coherence with 1000 random modules; graph-tool topology summary; pairwise Jaccard/shared-node overlaps.
6. Optionally run seed perturbation (leave-one-out → robustness + seed rediscovery rate) and network perturbation (degree-preserving rewire with graph-tool `random_rewire`).
7. Export modules to Drugst.One and, if enabled, call the Drugst.One API for drug prioritization (TrustRank / degree / closeness / harmonic) and optional network proximity.
8. Annotate modules via NeDRexDB and emit BioPAX OWL files (validated locally or against baderlab server).
9. Visualize modules (graph-tool PNG/SVG/PDF and pyvis HTML) and aggregate everything in a MultiQC report.

## Key parameters
- `--seeds`: path(s) to plain-text seed files, one ID per line, comma-separated for multiple sets.
- `--network`: path(s) to PPI edge list (csv/tsv/gt/graphml/dot/gml) OR a built-in keyword: `string_min900`, `string_min700`, `string_physical_min900`, `string_physical_min700`, `biogrid`, `hippie_high_confidence`, `hippie_medium_confidence`, `iid`, `nedrex`, `nedrex_high_confidence`.
- `--input`: CSV samplesheet with `seeds,network[,perturbed_networks]` columns for specific pairings.
- `--id_space`: `entrez` (default), `symbol`, `ensembl`, or `uniprot` — must match IDs in seeds and network.
- Method toggles: `--skip_domino`, `--skip_diamond`, `--skip_robust`, `--skip_robust_bias_aware`, `--skip_rwr`, `--skip_firstneighbor`.
- DIAMOnD: `--diamond_n` (default 200 added nodes), `--diamond_alpha` (default 1, seed weight).
- RWR: `--rwr_r` (restart probability, default 0.8), `--rwr_scaling`, `--rwr_symmetrical`.
- Robustness: `--run_seed_perturbation`, `--run_network_perturbation`, `--n_network_perturbations` (default 100), `--perturbed_networks` to reuse cached rewires.
- Evaluation toggles: `--skip_evaluation`, `--skip_gprofiler`, `--skip_digest`, `--skip_digest_reference_free`, `--skip_digest_reference_based`.
- Drugs: `--skip_drug_predictions`, `--drugstone_algorithms` (default `trustrank`; also `degree`, `closeness`), `--result_size` (default 50), `--includeIndirectDrugs`, `--includeNonApprovedDrugs`, `--run_proximity` with `--drug_to_target` and `--shortest_paths`.
- Visualization/annotation: `--skip_visualization`, `--visualization_max_nodes` (500), `--skip_drugstone_export`, `--drugstone_max_nodes` (500), `--skip_annotation`, `--validate_online`, `--add_variants`.
- Must use `-r dev` while the pipeline is pre-release.

## Test data
The bundled `test` profile runs on a tiny Entrez-space toy PPI (`entrez_ppi.csv`) with one small seed list (`entrez_seeds_1.csv`) hosted under `nf-core/test-datasets/diseasemodulediscovery/small/`. It exercises DIAMOnD plus the seeds-only baseline (DOMINO, ROBUST variants, RWR, and 1st-neighbor are skipped to keep runtime short), enables `run_seed_perturbation`, `run_network_perturbation` (3 rewires), `validate_online` BioPAX checks, and `run_proximity` using a bundled `subset_drug_target_geneid.tsv`. A successful run produces per-method module files under `modules/{gt,graphml,tsv_nodes,tsv_edges}/`, g:Profiler and DIGEST evaluation folders, Drugst.One drug prediction TSVs, a BioPAX OWL per module with a validator HTML report, and a unified `multiqc/multiqc_report.html` summarizing topology, overlaps, perturbation Jaccards, and rediscovery rates. The `test_full` profile scales this up to five thyroid-cancer cell-line seed sets against a UniProt-space reviewed-protein PPI from the same test-datasets repo.

## Reference workflow
nf-core/diseasemodulediscovery (dev, template 3.5.1, RePo4EU consortium). Methods and citation: Kersting et al., *Inferring and Evaluating Network Medicine-Based Disease Modules with Nextflow*, bioRxiv 2025, doi:10.1101/2025.11.20.687681. Source: https://github.com/nf-core/diseasemodulediscovery.
