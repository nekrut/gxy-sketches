---
name: drug-response-prediction-benchmarking
description: Use when you need to benchmark or evaluate machine-learning drug response
  prediction models (IC50/EC50/AUC prediction from cell-line or patient-derived omics)
  under statistically sound train/test splits such as Leave-Pair-Out, Leave-Cell-Line-Out,
  Leave-Tissue-Out, or Leave-Drug-Out, with cross-validated hyperparameter tuning,
  naive baselines, randomization, and robustness tests. Suited to CTRP/GDSC/CCLE/BeatAML/PDX-style
  datasets and custom viability screens.
domain: other
organism_class:
- eukaryote
- human
input_data:
- drug-response-matrix
- cell-line-omics
- drug-fingerprints
source:
  ecosystem: nf-core
  workflow: nf-core/drugresponseeval
  url: https://github.com/nf-core/drugresponseeval
  version: 1.2.0
  license: MIT
tools:
- drevalpy
- curvecurator
- scikit-learn
- pytorch-lightning
- nextflow
tags:
- drug-response
- pharmacogenomics
- benchmarking
- cross-validation
- cell-lines
- ic50
- auc
- machine-learning
- baselines
- randomization-test
test_data: []
expected_output: []
---

# Drug response prediction model benchmarking

## When to use this sketch
- You have (or want to use) a drug–cell-line response dataset (GDSC1/2, CCLE, CTRPv1/v2, BeatAML2, PDX_Bruna, or a custom viability screen) and want to evaluate one or more drug response prediction models end-to-end.
- You need statistically rigorous evaluation splits: Leave-Pair-Out (LPO), Leave-Cell-Line-Out (LCO, personalized medicine), Leave-Tissue-Out (LTO, drug repurposing), or Leave-Drug-Out (LDO, drug development).
- You want fair cross-validated hyperparameter tuning plus comparison against naive baselines (mean-effects, drug-mean, cell-line-mean, tissue-mean) and optional randomization / robustness stress tests.
- You want to train on one dataset (e.g. GDSC2) and test generalization on another (cross-study prediction).
- You are providing a custom raw viability CSV and need consistent CurveCurator curve fitting before modeling.

## Do not use when
- You are doing variant calling, expression quantification, single-cell clustering, or any primary sequencing analysis — this pipeline does not touch FASTQ/BAM/VCF data. Use the appropriate rna-seq, variant-calling, or single-cell sketch.
- You only want to fit dose–response curves from raw viability plates without any ML evaluation — use a stand-alone CurveCurator workflow instead.
- You need survival modeling, clinical outcome prediction from patient records, or pathway enrichment rather than drug-response regression.
- You want to train a genuinely new model architecture not yet in the drevalpy catalog — you must first contribute it to the drevalpy PyPI package before running this pipeline.

## Analysis outline
1. (Optional, custom data only) Reformat `<dataset>_raw.csv` and fit dose-response curves with CurveCurator to produce standardized pEC50/IC50/AUC measures.
2. Download or load the chosen response dataset from Zenodo into `--path_data/<dataset_name>`.
3. Split the response matrix into `n_cv_splits` CV folds according to `test_mode` (LPO/LCO/LTO/LDO); carve out early-stopping splits for NN models.
4. Expand each (model × hyperparameter combo × fold) into a parallel channel (one entry per drug for Single-Drug models like MOLIR/SuperFELTR/SingleDrug*).
5. Train each combo on train+val and evaluate on the fold's validation set via drevalpy (scikit-learn / PyTorch-Lightning backends).
6. Per fold, pick best hyperparameters by minimizing/maximizing `optim_metric` (default RMSE).
7. Retrain with best hyperparameters on full train+val and predict the held-out test set; also predict any `cross_study_datasets`.
8. (Optional) Run randomization tests (SVCC/SVRC/SVCD/SVRD × permutation|invariant) and robustness tests (`n_trials_robustness` random seeds). Skipped for baselines.
9. (Optional) If `--final_model_on_full_data`, retune + retrain on the union of all folds and persist a production model.
10. Consolidate per-model predictions, compute RMSE/MSE/MAE/R²/Pearson/Spearman/Kendall/partial correlation overall, per drug, and per cell line.
11. Render the VISUALIZATION subworkflow (critical-difference plots, violins, heatmaps, comp-scatter, regression lines, per-setting HTML summaries, `index.html`).

## Key parameters
- `--models`: comma-separated list of drevalpy model names (e.g. `ElasticNet,RandomForest,MOLIR,SRMF,DIPK`). Single-Drug models are invalid under LDO.
- `--baselines`: comma-separated baselines; `NaiveMeanEffectsPredictor` is always included. Randomization/robustness are not run for baselines.
- `--dataset_name`: one of `CTRPv1|CTRPv2|CCLE|GDSC1|GDSC2|BeatAML2|PDX_Bruna|TOYv1|TOYv2` or a custom name whose data lives under `<path_data>/<dataset_name>/`.
- `--test_mode`: `LPO`, `LCO`, `LTO`, `LDO`, or a comma-separated combination. Choose by application: LCO for personalized medicine, LTO for repurposing, LDO for drug development, LPO only for missing-value imputation.
- `--measure`: response target column; one of `LN_IC50|IC50|pEC50|EC50|AUC|response`. With refitting (default) the `_curvecurator` suffix is appended.
- `--no_refitting`: set to keep the authors' original fitted measures instead of CurveCurator re-fits (hurts cross-dataset comparability).
- `--n_cv_splits`: number of outer CV folds (default 10, minimum 2).
- `--optim_metric`: hyperparameter selection metric (default `RMSE`).
- `--cross_study_datasets`: comma-separated datasets to evaluate generalization on (e.g. `CTRPv1,CCLE`).
- `--randomization_mode` (`None|SVCC|SVRC|SVCD|SVRD,…`) and `--randomization_type` (`permutation|invariant`).
- `--n_trials_robustness`: number of random-seed retrains for the robustness test (0 disables).
- `--response_transformation`: `None|standard|minmax|robust`.
- `--no_hyperparameter_tuning`: skip grid search (quick runs / debugging only).
- `--final_model_on_full_data`: persist a production model trained on all folds.
- `--path_data`: cache directory for downloaded datasets and features; `--zenodo_link` points at the dataset bundle.
- `--run_id` and `--outdir`: result subdirectory layout.

## Test data
The pipeline's `test` profile runs on `TOYv1` (2,711 curves, 36 drugs, 90 cell lines — a subset of CTRPv2) with `TOYv2` as a cross-study dataset, `n_cv_splits = 2`, and data pulled from the nf-core/test-datasets `drugresponseeval` branch. The `test_full` profile additionally sets `models = ElasticNet`, `n_cv_splits = 5`, `randomization_mode = SVRC`, and `n_trials_robustness = 2`, exercising full CV, randomization, and robustness paths. Both profiles always include the `NaiveMeanEffectsPredictor` baseline. Expected outputs under `results/<run_id>/` include per-model prediction CSVs, cross-study prediction CSVs, randomization/robustness CSVs, the four overview tables (`evaluation_results.csv`, `evaluation_results_per_drug.csv`, `evaluation_results_per_cell_line.csv`, `true_vs_pred.csv`), and an HTML `report/` bundle with critical-difference, violin, heatmap, scatter, and per-setting summary pages linked from `index.html`.

## Reference workflow
nf-core/drugresponseeval v1.2.0 (https://github.com/nf-core/drugresponseeval), wrapping the `drevalpy` PyPI package. See Bernett et al., *From Hype to Health Check: Critical Evaluation of Drug Response Prediction Models with DrEval*, bioRxiv 2025.05.26.655288; pipeline DOI 10.5281/zenodo.14779984; data DOI 10.5281/zenodo.12633909.
