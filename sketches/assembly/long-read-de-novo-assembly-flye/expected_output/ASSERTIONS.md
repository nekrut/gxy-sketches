# Content assertions (no golden file checked in)
## flye_assembly_consensus
Content assertions for `Flye assembly (consensus)`.

- has_text: >contig_1
- has_size: {'min': '80k', 'max': '86k'}

## flye_assembly_assembly_graph
Content assertions for `Flye assembly (assembly_graph)`.

- has_text: digraph {
- has_n_lines: {'min': 20, 'max': 24}

## flye_assembly_graphical_fragment_assembly
Content assertions for `Flye assembly (Graphical Fragment Assembly)`.

- has_text: edge_1
- has_n_lines: {'min': 6, 'max': 8}

## flye_assembly_assembly_info
Content assertions for `Flye assembly (assembly_info)`.

- has_text: seq_name

## quast_html_report
Content assertions for `Quast: HTML report`.

- has_size: {'min': '250k', 'max': '400k'}

## flye_assembly_statistics
Content assertions for `Flye assembly statistics`.

- has_text: Scaffold L50

## bandage_image_assembly_graph_image
Content assertions for `Bandage Image: Assembly Graph Image`.

- has_size: {'min': '30k', 'max': '50k'}

