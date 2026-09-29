# TeleMed AI: Historical Archive & Research Evolution Index

This directory permanently preserves all historical research artifacts, legacy model iterations, intermediate datasets, exploratory notebooks, and milestone audit reports generated across Phases 1 through 6.

---

## 1. Archive Directory Catalog

```
archive/
├── v1/                                # Phase 1 Historical Foundation (20k Cohort)
│   ├── Clinical_Dataset.csv           # Initial 20,000-sample clinical laboratory dataset
│   ├── Wearable_Dataset.csv           # Initial 20,000-sample wearable sensor dataset
│   ├── Gut_Microbiome_Dataset.csv     # Initial 20,000-sample 16S rRNA taxonomic dataset
│   ├── Clinical_Dataset_Generation_Algorithm.docx # Original algorithm specification
│   └── gut_microbiome_dataset_generator/ # V1 microbiome synthetic generator
│
├── v2/                                # Phase 2 Exploratory Architecture
│   └── (Intermediate scripts and exploratory pipelines)
│
├── v3/                                # Phase 3 & 4 Late-Fusion Research Scripts
│   ├── v3_scientific_router.py        # Prototype 7-pathway scientific router
│   ├── unified_xai_engine.py          # Prototype unified XAI layer
│   ├── test_live_c001_v3_3.py         # Historical live validation test
│   └── generate_multimodal_v3_dataset.py # V3 dataset generator prototype
│
├── legacy_models/                     # Historical Model Checkpoints
│   ├── expert_models_saved_models/    # V1, V2, V3 expert model payloads
│   │   ├── clinical_v1..v3/           # Historical clinical model checkpoints
│   │   ├── wearable_v1..v3/           # Historical wearable model checkpoints
│   │   ├── gut_v1..v3/                # Historical gut model checkpoints
│   │   └── fusion_v3/                 # Historical W+G logistic stacker checkpoint
│   └── fusion_engine_saved_models/    # Historical fusion meta-learners
│       ├── fusion_v1/                 # Initial late-fusion meta-learner models
│       └── fusion_v2/                 # Intermediate fusion checkpoint
│
├── legacy_datasets/                   # Historical Split & Schema Tables
│   ├── expert_models_splits/          # Patient split index for 20k cohort
│   └── (Intermediate cohort tables)
│
├── experimental_code/                 # Exploratory Research & Scratch Scripts
│   ├── demo_patient_cases/            # Synthetic test cases (A, B, C, D, E)
│   ├── fusion_oof_probabilities/      # Out-of-fold cross-validation probability matrices
│   └── system_evaluation_reports/     # Historical system startup and validation guides
│
├── old_tests/                         # Historical Sprint Verification Scripts
│   ├── web_platform_reports/          # Sprint 24.5 - 25.1 freeze audit reports & scripts
│   ├── create_known_c001_fixtures.py  # Fixture creation scripts
│   ├── debug_upload_response.py       # Upload response debug scripts
│   └── verify_e2e_c001_full_pipeline.py # Historical pipeline verifier
│
├── old_reports/                       # Historical Phase Reports & Interim Audits
│   ├── phase1/                        # Phase 1 dataset distribution reports
│   └── phase2/                        # Phase 2 model validation reports
│
└── miscellaneous/                     # Preserved Supporting Assets
    ├── catboost_info/                 # CatBoost training telemetry logs
    ├── test_videos/                   # Screen recordings of UI acceptance tests
    └── scratch/                       # Diagnostic scripts and inspection outputs
```

---

## 2. Research Lineage & Dataset Evolution

| Generation Phase | Cohort Size | Clinical Features | Wearable Features | Gut Taxa | Target Diseases | Primary Validation Outcome |
|---|---|---|---|---|---|---|
| **Phase 1 (V1)** | 20,000 | 19 | 10 | 10 | 5 | Established single-modality baseline ROC-AUCs. |
| **Phase 3 (V3)** | 20,000 | 18 | 15 (CGM) | 20 (Raw) | 5 | Discovered Clinical Anchor effect & W+G synergy for NAFLD. |
| **Phase 6/Final (V4)** | 100,000 | 18 | 15 (CGM) | 20 (Raw) | 5 | Publication-grade cohort with CatBoost + LightGBM (ROC-AUC > 0.996). |
