# Content assertions (no golden file checked in)
## spatial_scatterplot_montage
Content assertions for `Spatial Scatterplot Montage`.

- has_size: {'size': '181K', 'delta': '50K'}

## spatial_interaction_montage
Content assertions for `Spatial Interaction Montage`.

- has_size: {'size': '39K', 'delta': '20K'}

## merged_anndata
Content assertions for `Merged anndata`.

- has_h5_keys: {'keys': 'obs/Area,obs/CellID,obs/Eccentricity,obs/Extent,obs/MajorAxisLength,obs/MinorAxisLength,obs/Orientation,obs/Solidity,obs/X_centroid,obs/Y_centroid,obs/imageid,obs/imageid/categories,obs/imageid/codes'}

## multisample_barplot
Content assertions for `Multisample barplot`.

- has_size: {'size': '60K', 'delta': '30K'}

## background_subtracted_images
Content assertions for `Background subtracted images`.

- image: has_image_channels: {'channels': 7}

## background_subtracted_markers
Content assertions for `Background subtracted markers`.

- image: has_line: marker_name,background,exposure
- image: has_line: DNA_7,,

## primary_mask_quantification
Content assertions for `Primary Mask Quantification`.

- image: has_line: CellID,DNA_7,CD11B,SMA,CD16,ECAD,FOXP3,NCAM,X_centroid,Y_centroid,Area,MajorAxisLength,MinorAxisLength,Eccentricity,Solidity,Extent,Orientation

## segmented_multiplexed_mask
Content assertions for `Segmented Multiplexed Mask`.

- image: has_image_channels: {'channels': 1}

## phenotyped_adata
Content assertions for `phenotyped adata`.

- image: has_h5_keys: {'keys': 'obs/Area,obs/CellID,obs/Eccentricity,obs/Extent,obs/MajorAxisLength,obs/MinorAxisLength,obs/Orientation,obs/Solidity,obs/X_centroid,obs/Y_centroid,obs/imageid,obs/imageid/categories,obs/imageid/codes'}

## interaction_matrix_plot
Content assertions for `Interaction Matrix Plot`.

- image: has_size: {'size': '43K', 'delta': '20K'}

## interaction_matrix_anndata
Content assertions for `Interaction Matrix Anndata`.

- image: has_h5_keys: {'keys': 'obs/Area,obs/CellID,obs/Eccentricity,obs/Extent,obs/MajorAxisLength,obs/MinorAxisLength,obs/Orientation,obs/Solidity,obs/X_centroid,obs/Y_centroid,obs/imageid,obs/imageid/categories,obs/imageid/codes'}

## squidpy_spatial_scatterplots
Content assertions for `Squidpy Spatial Scatterplots`.

- image: has_size: {'size': '181K', 'delta': '50K'}

## vitessce_dashboard
Content assertions for `Vitessce Dashboard`.

- image: has_json_property_with_text: 1.0.17

