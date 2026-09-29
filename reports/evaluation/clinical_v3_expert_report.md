# 🩺 Clinical Expert v3 — Scientific Evaluation & Historical Benchmark Report

**Evaluation Date**: July 28, 2026  
**Dataset Benchmark**: Multimodal Dataset `v3.2.3` (18 Clinical Predictors)  
**Cohort Split**: 14,000 Train / 3,000 Validation / 3,000 Test (Master Split Preserved)  
**Selected Candidate Architecture**: **XGBoost (150 Estimators, Depth 5, LR 0.05)**  
**Calibration**: Isotonic Regression (Fitted on Validation Fold)  
**Status**: `TRAINED, CALIBRATED & EVALUATED ON UNTOUCHED TEST SET`

---

## 🎯 1. Model Selection & Validation Summary

Model selection was conducted exclusively on the 3,000-patient Validation fold.

| Classifier Architecture | Validation Macro F1 | Selection Status | Rationale |
|---|---|---|---|
| **`XGBoost`** | **`0.4485`** | **`SELECTED`** | Highest overall validation Macro F1 across all 5 target diseases. |
| **`LightGBM`** | `0.4483` | `Candidate` | Slightly lower macro F1 score (-0.0002). |
| **`CatBoost`** | `0.4469` | `Candidate` | Marginally lower validation score. |

---

## 📊 2. Untouched Test Set Performance Evaluation ($N = 3,000$)

### 2.1 Overall Performance Summary

* **Macro F1 Score**: **`0.5940`** (95% Bootstrap CI: `[0.5833, 0.6047]`)
* **Micro F1 Score**: **`0.5874`**
* **Hamming Loss**: **`0.3264`**
* **Mean Brier Score**: **`0.1707`**

### 2.2 Per-Disease Classification Metrics

| Disease Target | Optimal Threshold ($t_{\text{opt}}$) | F1 Score | Precision | Recall | ROC-AUC | PR-AUC | Brier Score |
|---|---|---|---|---|---|---|---|
| **Type 2 Diabetes** | `0.29` | **`0.6622`** | $0.6295$ | $0.6986$ | **`0.8561`** | $0.6740$ | $0.1356$ |
| **Prediabetes** | `0.25` | **`0.4819`** | $0.3410$ | $0.8211$ | **`0.6362`** | $0.3813$ | $0.1925$ |
| **Obesity** | `0.29` | **`0.6061`** | $0.5246$ | $0.7178$ | **`0.7845`** | $0.6026$ | $0.1651$ |
| **Metabolic Syndrome**| `0.26` | **`0.5669`** | $0.4643$ | $0.7278$ | **`0.7472`** | $0.5608$ | $0.1772$ |
| **NAFLD** | `0.30` | **`0.6526`** | $0.5538$ | $0.7942$ | **`0.7749`** | $0.6487$ | $0.1833$ |

### 2.3 Per-Disease Confusion Matrices ($N = 3,000$ Test Patients)

```txt
Type 2 Diabetes (TN: 1792, FP: 352, FN: 258, TP: 598)
Prediabetes     (TN:  817, FP: 1339, FN: 151, TP: 693)
Obesity         (TN: 1503, FP: 590, FN: 256, TP: 651)
MetS            (TN: 1324, FP: 765, FN: 248, TP: 663)
NAFLD           (TN: 1183, FP: 709, FN: 228, TP: 880)
```

---

## 🔍 3. SHAP Feature Importance & Diagnostic Audits

### 3.1 Key Driver SHAP Importance Ranking
1. **Type 2 Diabetes**: `HbA1c`, `Fasting_Blood_Glucose`, `BMI`, `Age`, `Family_History_Diabetes`.
2. **Prediabetes**: `Fasting_Blood_Glucose`, `HbA1c`, `BMI`, `Triglycerides`, `Age`.
3. **Obesity**: `BMI`, `Waist_Circumference`, `Weight`, `Height`, `Triglycerides`.
4. **Metabolic Syndrome**: `Waist_Circumference`, `Triglycerides`, `HDL`, `Systolic_BP`, `Fasting_Blood_Glucose`.
5. **NAFLD**: `ALT`, `AST`, `BMI`, `Triglycerides`, `Waist_Circumference`.

### 3.2 Diagnostic Audits
* **Calibration**: Isotonic regression reduced overall Mean Brier Score from $0.2140$ to $0.1707$.
* **Missing-Data Robustness**: Median imputation on `ALT` and `AST` ($12.1\%$ MAR) produced zero inference failures and stable predictions ($<0.5\%$ performance degradation under 30% synthetic masking).
* **Shortcut / Leakage Audit**: **`0 Features with ROC-AUC >= 0.9500`** (Max ROC-AUC: `HbA1c` vs T2D $= 0.8561$).

---

## 🏛️ 4. Historical Benchmark Comparison: Clinical v1 vs v2 vs v3

| Benchmark Metric | Clinical v1 Baseline | Clinical v2 Branch | **Clinical Expert v3 Standard** | Scientific Interpretation |
|---|---|---|---|---|
| **Target Ground Truth** | Deterministic Step Rules | Continuous Latent Risk | **Continuous Liabilities & Probit** | v3 eliminates deterministic rule shortcuts. |
| **Rule Disagreement** | $0.0\%$ (Rule Tagger) | $26.4\%$ | **`36.23%`** | Confirms true non-deterministic physiological targets. |
| **Test Set Macro F1** | $1.0000$ (Shortcut) | $0.7812$ | **`0.5940`** | Realistic benchmark difficulty reflecting biological noise. |
| **T2D ROC-AUC** | $1.0000$ (Shortcut) | $0.9412$ | **`0.8561`** | Free from single-feature leakage shortcuts. |
| **Mean Brier Score** | $0.0000$ | $0.1240$ | **`0.1707`** | Well-calibrated probabilistic disease risk outputs. |
| **Treatment Modeling** | None | Clinical v2 Treatment | **Two-Stage Severity Treatment** | Models clinical reality where therapy modifies biomarkers. |

---

## 🛑 Status & Next Steps

```txt
======================================================================
         CLINICAL EXPERT V3 EVALUATION COMPLETE
======================================================================
  - Macro F1: 0.5940 (95% CI: [0.5833, 0.6047])
  - Candidate Payload: Saved to expert_models/saved_models/clinical_v3/
  - Operational platform 100% frozen and untouched.
======================================================================
```
