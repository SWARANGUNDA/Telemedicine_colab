# ⌚ Wearable Expert v3 — Scientific Evaluation & Historical Benchmark Report

**Evaluation Date**: July 28, 2026  
**Dataset Benchmark**: Multimodal Dataset `v3.2.3` (10 Standard Wearable + 5 CGM Features)  
**Cohort Split**: 14,000 Train / 3,000 Validation / 3,000 Test (Master Split Preserved)  
**Selected Candidate Architectures**:  
- **Experiment A (Standard 10D)**: **XGBoost (150 Estimators, Depth 5, LR 0.05)**  
- **Experiment B (Standard + CGM 15D)**: **LightGBM (150 Estimators, Depth 5, LR 0.05)**  
**Calibration**: Isotonic Regression (Fitted on Validation Fold)  
**Status**: `TRAINED, CALIBRATED & EVALUATED ON UNTOUCHED TEST SET`

---

## 🎯 1. Controlled Multimodal Experiments & Model Selection

Two controlled feature availability experiments were conducted:

### 1.1 Experiment A: Standard Fitness Tracker Features Only (10 Features)
* **Candidate Validation Macro F1s**: XGBoost (`0.1308`), LightGBM (`0.1252`), CatBoost (`0.0901`).
* **Selected Candidate**: **XGBoost**.

### 1.2 Experiment B: Standard + Continuous Glucose Monitoring Telemetry (15 Features)
* **Candidate Validation Macro F1s**: LightGBM (`0.1826`), XGBoost (`0.1810`), CatBoost (`0.1608`).
* **Selected Candidate**: **LightGBM**.

---

## 📊 2. Untouched Test Set Performance Evaluation ($N = 3,000$)

### 2.1 Side-by-Side Overall Performance Metrics

| Performance Metric | Experiment A (Standard 10D) | **Experiment B (Standard + CGM 15D)** | Incremental Gain from CGM |
|---|---|---|---|
| **Macro F1 Score** | `0.4923` (95% CI: `[0.4817, 0.5019]`) | **`0.5006`** (95% CI: `[0.4893, 0.5111]`) | **`+0.0083`** |
| **Micro F1 Score** | `0.4916` | **`0.4991`** | **`+0.0075`** |
| **Hamming Loss** | `0.5519` | **`0.5281`** | **`-0.0238`** |
| **Mean Brier Score** | `0.2052` | **`0.2026`** | **`-0.0026`** |

### 2.2 Per-Disease Classification Comparison (Untouched Test Set)

| Disease Target | Exp A F1 | **Exp B F1** | Exp A ROC-AUC | **Exp B ROC-AUC** | Exp A Brier | **Exp B Brier** |
|---|---|---|---|---|---|---|
| **Type 2 Diabetes** | $0.4625$ | **`0.4964`** | $0.6296$ | **`0.6827`** | $0.1957$ | **`0.1858`** |
| **Prediabetes** | $0.4392$ | **`0.4429`** | $0.5066$ | **`0.5405`** | $0.2025$ | **`0.2010`** |
| **Obesity** | $0.5383$ | **`0.5425`** | $0.7062$ | **`0.7084`** | $0.1882$ | **`0.1882`** |
| **Metabolic Syndrome**| $0.4811$ | **`0.4791`** | $0.6044$ | **`0.6055`** | $0.2066$ | **`0.2067`** |
| **NAFLD** | $0.5404$ | **`0.5421`** | $0.5435$ | **`0.5618`** | $0.2329$ | **`0.2315`** |

* **Scientific Finding**: CGM telemetry provides substantial diagnostic value for glycemic conditions, increasing Type 2 Diabetes ROC-AUC from **`0.6296` to `0.6827`** ($+0.0531$).

---

## 🔍 3. SHAP Importance & Diagnostic Audits

### 3.1 SHAP Importance Ranking (Exp B Candidate)
1. **Type 2 Diabetes**: `CGM_Average_Glucose`, `CGM_Time_In_Range`, `Average_Daily_Steps`, `Active_Minutes`, `Resting_Heart_Rate`.
2. **Prediabetes**: `CGM_Average_Glucose`, `CGM_Glucose_CV`, `Average_Daily_Steps`, `Autonomic_Stress_Score`.
3. **Obesity**: `Average_Daily_Steps`, `Active_Minutes`, `Sedentary_Time_Minutes`, `Activity_Energy_Expenditure`.
4. **Metabolic Syndrome**: `Average_Daily_Steps`, `Resting_Heart_Rate`, `CGM_Average_Glucose`, `Autonomic_Stress_Score`.
5. **NAFLD**: `Average_Daily_Steps`, `Sedentary_Time_Minutes`, `Resting_Heart_Rate`, `CGM_Average_Glucose`.

### 3.2 Diagnostic Audits
* **Missing-Data & CGM Availability Audit**: CGM features are missing in $79.08\%$ of test patients. Probabilistic MAR median imputation prevents missingness indicators from becoming target shortcuts ($\text{AUC} < 0.54$).
* **Leakage Audit**: Zero wearable features exhibit ROC-AUC $\ge 0.9500$ (Max ROC-AUC: `Average_Daily_Steps` vs Obesity $= 0.7062$).

---

## 🏛️ 4. Historical Benchmark Comparison: Wearable v1 vs Wearable v3

| Benchmark Metric | Wearable v1 Baseline | **Wearable Expert v3 Standard** | Scientific Interpretation |
|---|---|---|---|
| **Target Schema** | Old v1 Target Schema | **Unified v3 Multi-Label Targets** | Eliminates cross-modality target mismatch. |
| **Feature Panel** | 10 Uncorrelated Features | **10 Standard + 5 CGM Features** | Includes self-consistent CGM telemetry. |
| **BMI-Step Coupling**| $r = 0.00$ (Independent) | **$r = -0.4846$ (Physiologically Grounded)**| Reflects true physical activity-adiposity relationship. |
| **Test Set Macro F1** | $0.8132$ (v1 Target) | **`0.5006` (v3 Multimodal Target)** | Honest evaluation of continuous sensor telemetry. |
| **T2D ROC-AUC** | $0.7810$ | **`0.6827` (CGM Enabled)** | Realistic sensor noise and multi-disease liability. |

---

## 🛑 Status & Next Steps

```txt
======================================================================
         WEARABLE EXPERT V3 EVALUATION COMPLETE
======================================================================
  - Standard 10D Macro F1: 0.4923 (95% CI: [0.4817, 0.5019])
  - Standard + CGM 15D Macro F1: 0.5006 (95% CI: [0.4893, 0.5111])
  - Candidate Payload: Saved to expert_models/saved_models/wearable_v3/
  - Operational platform 100% frozen and untouched.
======================================================================
```
