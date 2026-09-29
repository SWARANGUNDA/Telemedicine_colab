# V3 Frozen Baseline Manifest & Cryptographic Signature

**Status:** OFFICIAL FROZEN SCIENTIFIC & SYSTEM BASELINE  
**Pipeline Version:** Unified Multimodal Scientific Baseline `v3.2.3`  
**Freeze Date:** July 28, 2026  
**Master Dataset Seed:** `20260728` ($N=20,000$, 14k Train / 3k Val / 3k Test)  
**System Disclaimer:** Academic & Research Prototype Engine Using Synthetic Multimodal Data. Not a Clinically Validated Diagnostic System.  

---

## 1. Frozen Dataset Artifacts & Cryptographic Signatures

All datasets are frozen under `data/multimodal_v3/`:

| Dataset Filename | Relative Path | File Size (Bytes) | Exact SHA-256 Hash |
| :--- | :--- | :---: | :--- |
| `clinical_v3.csv` | `data/multimodal_v3/clinical_v3.csv` | 1,773,130 | `0c05dc94aaf1e1c7736b71e3bdb3d1dc90284ce844b7623b077eeea9682e8242` |
| `wearable_standard_v3.csv` | `data/multimodal_v3/wearable_standard_v3.csv` | 1,189,650 | `3ff8aff4f6dd6bcc2671a9cc7ce3d465bd37240475c0fc49fe830ead147b3444` |
| `wearable_cgm_v3.csv` | `data/multimodal_v3/wearable_cgm_v3.csv` | 357,475 | `e0ad3ee19b4e5dc4771f393301c868a8df99ad59a0ec6acc43e88258d7052393` |
| `gut_v3.csv` | `data/multimodal_v3/gut_v3.csv` | 3,969,131 | `ced96863e237b3ae13d66266709673f14278202d1197137a53aa234d0d34b891` |
| `labels_v3.csv` | `data/multimodal_v3/labels_v3.csv` | 360,072 | `e18ae98083a647f344ca2e19eb88344e70672a090244fc5cecf31077817cc7fc` |
| `split_manifest_v3.csv` | `data/multimodal_v3/split_manifest_v3.csv` | 271,018 | `e1942e303a5878372198bfca0299469bedc26621f6dc61f422b245dc0213ec56` |

---

## 2. Frozen Model Payload Artifacts & Cryptographic Signatures

All trained models and stacker payloads are frozen under `expert_models/saved_models/`:

| Model Payload Artifact | Relative Path | File Size (Bytes) | Exact SHA-256 Hash |
| :--- | :--- | :---: | :--- |
| **Clinical Expert v3** | `expert_models/saved_models/clinical_v3/clinical_v3_payload.joblib` | 1,900,516 | `f4ecb3f7df25500155d92dcbe0dda0da9b18e3ec00320d1f1bb68637a68041b1` |
| **Clinical v3 Metrics** | `expert_models/saved_models/clinical_v3/clinical_v3_metrics.json` | 2,040 | `fb14fa3d1c6e26eae0e174eca68199f1e647adaebde18f7b08c1528b7730a416` |
| **Wearable Expert v3** | `expert_models/saved_models/wearable_v3/wearable_v3_payload.joblib` | 1,848,995 | `1dfe6d7fd4e384063896de5fc2b2b1388d74d96e0e336d9adc39155b4d76d9ad` |
| **Wearable v3 Metrics** | `expert_models/saved_models/wearable_v3/wearable_v3_metrics.json` | 4,563 | `fc72f23c4bcfb190378b99e40785bf6b9d693c4ccc7293d20c1f7daade60f1e6` |
| **Gut Expert v3** | `expert_models/saved_models/gut_v3/gut_v3_payload.joblib` | 1,868,627 | `b0896d2f8d30dc3edcb7dadfd2ed324f03c4d6bc18fbba3d03cd54cbe6f40059` |
| **Gut v3 Metrics** | `expert_models/saved_models/gut_v3/gut_v3_metrics.json` | 3,072 | `61ac6fd2f519640aa9a16d1a34e7efc8ec32f0741c7eb7fda71e97e9fc864ff0` |
| **Fusion v3 Metrics** | `expert_models/saved_models/fusion_v3/fusion_v3_metrics.json` | 54,440 | `849f03b3e86f5a227be45a2e95242c6037b2595df8d3f45ec4bdba990e3f55ff` |
| **W+G LR Stacker** | `expert_models/saved_models/fusion_v3/wg_logistic_regression_stacker.joblib` | 6,591 | `10a9da990c5550542d4938fc80a666752b4a98513afda85a029dccb220a7153f` |

---

## 3. Model Architecture, Preprocessor & Threshold Specification

### A. Clinical Expert v3
- **Algorithm:** XGBoost Multilabel Classifier (150 estimators, depth 5, LR 0.05).
- **Features (18):** `Age`, `Gender`, `Height`, `Weight`, `BMI`, `Waist_Circumference`, `Systolic_BP`, `Diastolic_BP`, `Fasting_Blood_Glucose`, `HbA1c`, `Triglycerides`, `HDL`, `LDL`, `ALT`, `AST`, `Family_History_Diabetes`, `Family_History_Hypertension`, `Family_History_CVD`.
- **Preprocessor:** `StandardScaler` fitted on Train set ($N=14,000$).
- **Calibrator:** `IsotonicRegression` per target fitted on Validation set ($N=3,000$).
- **Tuned Thresholds ($t_{\text{opt}}$):** `{T2D: 0.29, Prediabetes: 0.25, Obesity: 0.29, Metabolic_Syndrome: 0.26, NAFLD: 0.30}`.

### B. Wearable Expert v3 (15D Payload)
- **Algorithm:** LightGBM Multilabel Classifier (150 estimators, depth 5, LR 0.05).
- **Features (15):** `Average_Daily_Steps`, `Active_Minutes`, `Sedentary_Time_Minutes`, `Resting_Heart_Rate`, `Heart_Rate_Variability_RMSSD`, `Sleep_Duration_Hours`, `Sleep_Efficiency_Score`, `Autonomic_Stress_Score`, `Activity_Energy_Expenditure`, `Exercise_Frequency_Days`, `CGM_Average_Glucose`, `CGM_Glucose_CV`, `CGM_Time_In_Range`, `CGM_Time_Above_Range`, `CGM_Time_Below_Range`.
- **Preprocessor:** `StandardScaler` fitted on Train set ($N=14,000$). Missing CGM/telemetry features imputed using stored payload medians.
- **Calibrator:** `IsotonicRegression` per target fitted on Validation set ($N=3,000$).
- **Tuned Thresholds ($t_{\text{opt}}$):** `{T2D: 0.22, Prediabetes: 0.22, Obesity: 0.26, Metabolic_Syndrome: 0.21, NAFLD: 0.26}`.

### C. Gut Expert v3
- **Algorithm:** XGBoost Multilabel Classifier (150 estimators, depth 5, LR 0.05).
- **Features (20 Taxa RAW Relative Abundance):** `Akkermansia`, `Faecalibacterium`, `Roseburia`, `Bifidobacterium`, `Bacteroides`, `Prevotella`, `Ruminococcus`, `Blautia`, `Collinsella`, `Escherichia_Shigella`, `Coprococcus`, `Alistipes`, `Subdoligranulum`, `Enterococcus`, `Eubacterium`, `Parabacteroides`, `Lactobacillus`, `Klebsiella`, `Streptococcus`, `Eggerthella`.
- **Preprocessor:** `StandardScaler` fitted on Train set ($N=14,000$).
- **Calibrator:** `IsotonicRegression` per target fitted on Validation set ($N=3,000$).
- **Tuned Thresholds ($t_{\text{opt}}$):** `{T2D: 0.20, Prediabetes: 0.10, Obesity: 0.19, Metabolic_Syndrome: 0.10, NAFLD: 0.26}`.

### D. W+G Logistic Regression Meta-Stacker
- **Algorithm:** 5-fold OOF `LogisticRegression` meta-stacker + `IsotonicRegression` calibrators fitted on Train/Val splits.
- **Inputs:** Pairwise calibrated probability vector $[P_{\text{Wearable}}, P_{\text{Gut}}]$ per disease.
- **Test Performance:** NAFLD ROC-AUC = `0.5983` ($\Delta \text{AUC} = +0.0364$, $p < 0.0001$).

---

## 4. Frozen Dynamic Routing Rules

| Modality Pattern | Effective Pathway | Primary Decision Anchor | Operational Rule |
| :---: | :---: | :--- | :--- |
| `C` | `C` | `Clinical_v3` | Clinical v3 standalone captures 99.94% of max ROC-AUC. |
| `W` | `W` | `Wearable_v3` | Standalone wearable screening (15D payload, median CGM imputation). |
| `G` | `G` | `Gut_v3` | Standalone gut screening (20 Taxa RAW). |
| `C+W` | `C+W` | `Clinical_v3` | Clinical anchor provides primary diagnosis; Wearable logged for tracking. |
| `C+G` | `C+G` | `Clinical_v3` | Clinical anchor provides primary diagnosis. |
| `W+G` | `W+G` | `W+G LR Stacker` | Executed for remote triage without clinical labs (NAFLD gain $+0.0364$). |
| `C+W+G` | `C+W+G` | `Clinical_v3` | Clinical anchor provides primary diagnosis to prevent prediabetes degradation. |

---

## 5. Automated Test Suite Verification (13/13 PASS)

Test execution command: `python test_v3_e2e_integration.py -v`  
Result: **`Ran 13 tests in 3.107s — OK`**

- `test_01_payload_loading` — PASS ✓
- `test_02_clinical_only_pathway` — PASS ✓
- `test_03_wearable_only_pathway` — PASS ✓
- `test_04_gut_only_pathway` — PASS ✓
- `test_05_wearable_plus_gut_remote_triage_pathway` — PASS ✓
- `test_06_clinical_anchor_tri_modal_pathway` — PASS ✓
- `test_07_cgm_missing_imputation` — PASS ✓
- `test_08_api_predict_endpoint` — PASS ✓
- `test_09_api_xai_endpoint` — PASS ✓
- `test_10_api_report_endpoint` — PASS ✓
- `test_11_malformed_request_handling` — PASS ✓
- `test_12_deterministic_reproducibility` — PASS ✓
- `test_13_exact_wg_stacker_equivalence` — PASS ✓

---

## 6. Freeze Governance Policy

1. **No Retraining or Parameter Mutation:** All payload joblibs, scalers, calibrators, thresholds, and datasets listed above are permanently frozen.
2. **No Deletion of Legacy Artifacts:** Legacy v1 and v2 artifacts, models, datasets, and routes are preserved in parallel for historical comparison and rollback.
3. **No Automatic v2 Fallback:** Backend errors in `/api/v3/*` endpoints return explicit HTTP 500 JSON error responses without falling back to older models.
