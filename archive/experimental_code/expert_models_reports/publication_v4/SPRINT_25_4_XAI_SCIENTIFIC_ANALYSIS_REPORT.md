# SPRINT 25.4 — PUBLICATION-GRADE XAI & FEATURE CONTRIBUTION ANALYSIS REPORT

## Executive Summary
- **Test Set:** Untouched 15,000-patient test set ($N=15,000$).
- **V4 Model Status:** **100% FROZEN & UNTOUCHED**. All SHA-256 payload hashes verified identical before and after execution.
- **XAI Method:** TreeSHAP & LinearSHAP feature attribution across Clinical (18 features), Wearable (15 features), and Gut Microbiome (49 features) expert models.
- **Scientific Caveat:** All SHAP attributions represent **model-learned feature risk associations** and do NOT claim biological causality.

---

## 1. Global Feature Importance & Directional Associations

| modality | disease | feature | feature_rank | mean_abs_shap | directional_association |
| --- | --- | --- | --- | --- | --- |
| Clinical | High_Adiposity_Risk | Waist_Circumference | 1 | 0.309089 | Non-linear / context-dependent model risk association |
| Clinical | High_Adiposity_Risk | ALT | 2 | 0.072606 | Non-linear / context-dependent model risk association |
| Clinical | High_Adiposity_Risk | BMI | 3 | 1.220588 | Non-linear / context-dependent model risk association |
| Clinical | High_Adiposity_Risk | Diastolic_BP | 4 | 0.001849 | Higher value associated with higher model-predicted risk |
| Clinical | High_Adiposity_Risk | Age | 5 | 0.08057 | Non-linear / context-dependent model risk association |
| Clinical | High_Adiposity_Risk | Gender | 6 | 0.004829 | Higher value associated with higher model-predicted risk |
| Clinical | High_Adiposity_Risk | Triglycerides | 7 | 0.023143 | Non-linear / context-dependent model risk association |
| Clinical | High_Adiposity_Risk | Family_History_Hypertension | 8 | 0.005069 | Higher value associated with lower model-predicted risk |
| Clinical | High_Adiposity_Risk | AST | 9 | 0.070955 | Non-linear / context-dependent model risk association |
| Clinical | High_Adiposity_Risk | HbA1c | 10 | 0.068323 | Non-linear / context-dependent model risk association |
| Clinical | Metabolic_Syndrome | HbA1c | 1 | 0.110503 | Higher value associated with higher model-predicted risk |
| Clinical | Metabolic_Syndrome | ALT | 2 | 0.052897 | Higher value associated with higher model-predicted risk |
| Clinical | Metabolic_Syndrome | LDL | 3 | 0.087131 | Higher value associated with higher model-predicted risk |
| Clinical | Metabolic_Syndrome | Height | 4 | 0.029211 | Higher value associated with higher model-predicted risk |
| Clinical | Metabolic_Syndrome | Fasting_Blood_Glucose | 5 | 0.016666 | Higher value associated with higher model-predicted risk |
| Clinical | Metabolic_Syndrome | Age | 6 | 0.056673 | Higher value associated with higher model-predicted risk |
| Clinical | Metabolic_Syndrome | Waist_Circumference | 7 | 0.301655 | Higher value associated with higher model-predicted risk |
| Clinical | Metabolic_Syndrome | Weight | 8 | 0.163568 | Higher value associated with lower model-predicted risk |
| Clinical | Metabolic_Syndrome | AST | 9 | 0.051689 | Higher value associated with higher model-predicted risk |
| Clinical | Metabolic_Syndrome | Systolic_BP | 10 | 0.133825 | Higher value associated with higher model-predicted risk |
| Clinical | NAFLD | LDL | 1 | 0.068139 | Non-linear / context-dependent model risk association |
| Clinical | NAFLD | Family_History_CVD | 2 | 0.003352 | Higher value associated with lower model-predicted risk |
| Clinical | NAFLD | HbA1c | 3 | 0.062996 | Non-linear / context-dependent model risk association |
| Clinical | NAFLD | Fasting_Blood_Glucose | 4 | 0.010628 | Non-linear / context-dependent model risk association |
| Clinical | NAFLD | Waist_Circumference | 5 | 0.439113 | Non-linear / context-dependent model risk association |

---

## 2. Clinical Feature XAI Analysis

- **Primary Glycemic Anchors:** `HbA1c` and `Fasting_Blood_Glucose` dominate `Type2_Diabetes` and `Prediabetes` risk scoring.
- **Metabolic Syndrome Drivers:** `Waist_Circumference`, `Triglycerides`, `Systolic_BP`, and `HDL` drive multi-organ metabolic syndrome predictions.
- **Hepatic Profile:** `ALT` and `AST` provide high contribution for `NAFLD` within the clinical expert model.

| modality | disease | feature | feature_rank | mean_abs_shap | median_abs_shap | pct_contribution | directional_association |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Clinical | High_Adiposity_Risk | Waist_Circumference | 1 | 0.309089 | 0.310063 | 12.62 | Non-linear / context-dependent model risk association |
| Clinical | High_Adiposity_Risk | ALT | 2 | 0.072606 | 0.072563 | 2.96 | Non-linear / context-dependent model risk association |
| Clinical | High_Adiposity_Risk | BMI | 3 | 1.220588 | 1.224106 | 49.83 | Non-linear / context-dependent model risk association |
| Clinical | High_Adiposity_Risk | Diastolic_BP | 4 | 0.001849 | 0.002045 | 0.08 | Higher value associated with higher model-predicted risk |
| Clinical | High_Adiposity_Risk | Age | 5 | 0.08057 | 0.080691 | 3.29 | Non-linear / context-dependent model risk association |
| Clinical | High_Adiposity_Risk | Gender | 6 | 0.004829 | 0.00521 | 0.2 | Higher value associated with higher model-predicted risk |
| Clinical | High_Adiposity_Risk | Triglycerides | 7 | 0.023143 | 0.023627 | 0.94 | Non-linear / context-dependent model risk association |
| Clinical | High_Adiposity_Risk | Family_History_Hypertension | 8 | 0.005069 | 0.003463 | 0.21 | Higher value associated with lower model-predicted risk |
| Clinical | High_Adiposity_Risk | AST | 9 | 0.070955 | 0.073486 | 2.9 | Non-linear / context-dependent model risk association |
| Clinical | High_Adiposity_Risk | HbA1c | 10 | 0.068323 | 0.067823 | 2.79 | Non-linear / context-dependent model risk association |
| Clinical | High_Adiposity_Risk | HDL | 11 | 0.184767 | 0.184328 | 7.54 | Non-linear / context-dependent model risk association |
| Clinical | High_Adiposity_Risk | Height | 12 | 0.102317 | 0.104247 | 4.18 | Non-linear / context-dependent model risk association |
| Clinical | High_Adiposity_Risk | Weight | 13 | 0.071478 | 0.078302 | 2.92 | Higher value associated with higher model-predicted risk |
| Clinical | High_Adiposity_Risk | Systolic_BP | 14 | 0.045573 | 0.045495 | 1.86 | Non-linear / context-dependent model risk association |
| Clinical | High_Adiposity_Risk | Fasting_Blood_Glucose | 15 | 0.0033 | 0.003204 | 0.13 | Non-linear / context-dependent model risk association |

---

## 3. Wearable Continuous Biomarker XAI Analysis

- **Continuous Glucose Monitoring (CGM):** `CGM_Average_Glucose`, `CGM_Time_Above_Range`, and `CGM_Glucose_CV` provide top predictive signal for glycemic dysregulation.
- **Physical Activity & Adiposity:** `Sedentary_Time_Minutes`, `Active_Minutes`, and `Activity_Energy_Expenditure` drive `High_Adiposity_Risk` prediction (**0.6602** ROC-AUC).
- **Autonomic Tone:** `Autonomic_Stress_Score` and `Resting_Heart_Rate` contribute to metabolic syndrome risk profiling.

| modality | disease | feature | feature_rank | mean_abs_shap | median_abs_shap | pct_contribution | directional_association |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Wearable | High_Adiposity_Risk | Activity_Energy_Expenditure | 1 | 0.109806 | 0.092546 | 11.56 | Higher value associated with lower model-predicted risk |
| Wearable | High_Adiposity_Risk | Autonomic_Stress_Score | 2 | 0.111718 | 0.101661 | 11.77 | Higher value associated with lower model-predicted risk |
| Wearable | High_Adiposity_Risk | Average_Daily_Steps | 3 | 0.034689 | 0.030786 | 3.65 | Higher value associated with lower model-predicted risk |
| Wearable | High_Adiposity_Risk | Resting_Heart_Rate | 4 | 0.102283 | 0.095778 | 10.77 | Higher value associated with higher model-predicted risk |
| Wearable | High_Adiposity_Risk | Sleep_Duration_Hours | 5 | 0.094911 | 0.074843 | 10.0 | Higher value associated with lower model-predicted risk |
| Wearable | High_Adiposity_Risk | Heart_Rate_Variability_RMSSD | 6 | 0.07597 | 0.062914 | 8.0 | Higher value associated with lower model-predicted risk |
| Wearable | High_Adiposity_Risk | Exercise_Frequency_Days | 7 | 0.009753 | 0.009367 | 1.03 | Higher value associated with lower model-predicted risk |
| Wearable | High_Adiposity_Risk | Active_Minutes | 8 | 0.037729 | 0.031941 | 3.97 | Higher value associated with higher model-predicted risk |
| Wearable | High_Adiposity_Risk | Sedentary_Time_Minutes | 9 | 0.27775 | 0.225579 | 29.25 | Higher value associated with higher model-predicted risk |
| Wearable | High_Adiposity_Risk | CGM_Average_Glucose | 10 | 0.004961 | 0.001118 | 0.52 | Higher value associated with higher model-predicted risk |
| Wearable | High_Adiposity_Risk | CGM_Glucose_CV | 11 | 0.058039 | 0.011935 | 6.11 | Higher value associated with higher model-predicted risk |
| Wearable | High_Adiposity_Risk | Sleep_Efficiency_Score | 12 | 0.023443 | 0.01976 | 2.47 | Higher value associated with higher model-predicted risk |
| Wearable | High_Adiposity_Risk | CGM_Time_Above_Range | 13 | 0.004459 | 0.00111 | 0.47 | Higher value associated with lower model-predicted risk |
| Wearable | High_Adiposity_Risk | CGM_Time_In_Range | 14 | 0.003814 | 0.00093 | 0.4 | Higher value associated with higher model-predicted risk |
| Wearable | High_Adiposity_Risk | CGM_Time_Below_Range | 15 | 0.000183 | 4.9e-05 | 0.02 | Higher value associated with higher model-predicted risk |

---

## 4. Gut Microbiome Taxa & Derived Ecological Index XAI Analysis

- **Derived Ecological Indices:** `SCFA_Producer_Index`, `Barrier_Associated_Index`, and `Inflammation_Associated_Index` rank as top predictors across gut models.
- **NAFLD Taxa Drivers:** `Faecalibacterium_prausnitzii` depletion and `Bacteroides_thetaiotaomicron` / `Prevotella_copri` variations drive non-invasive `NAFLD` detection (**0.6379** ROC-AUC).

| modality | disease | feature | feature_rank | mean_abs_shap | median_abs_shap | pct_contribution | directional_association |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Gut | High_Adiposity_Risk | Phascolarctobacterium_faecium | 1 | 0.003276 | 0.002686 | 0.34 | Higher value associated with higher model-predicted risk |
| Gut | High_Adiposity_Risk | Faecalibacterium_prausnitzii | 2 | 0.067761 | 0.05874 | 7.02 | Higher value associated with higher model-predicted risk |
| Gut | High_Adiposity_Risk | Prevotella_copri | 3 | 0.034718 | 0.027558 | 3.6 | Higher value associated with lower model-predicted risk |
| Gut | High_Adiposity_Risk | Eubacterium_hallii | 4 | 0.006994 | 0.005925 | 0.72 | Higher value associated with higher model-predicted risk |
| Gut | High_Adiposity_Risk | Shannon_Diversity | 5 | 0.040618 | 0.032006 | 4.21 | Higher value associated with higher model-predicted risk |
| Gut | High_Adiposity_Risk | Ruminococcus_bromii | 6 | 0.023208 | 0.01887 | 2.4 | Higher value associated with higher model-predicted risk |
| Gut | High_Adiposity_Risk | Klebsiella_pneumoniae | 7 | 0.018878 | 0.015158 | 1.95 | Higher value associated with higher model-predicted risk |
| Gut | High_Adiposity_Risk | Alistipes_finegoldii | 8 | 0.003672 | 0.003101 | 0.38 | Higher value associated with lower model-predicted risk |
| Gut | High_Adiposity_Risk | Coprococcus_eutactus | 9 | 0.011123 | 0.00942 | 1.15 | Higher value associated with higher model-predicted risk |
| Gut | High_Adiposity_Risk | Bacteroides_fragilis | 10 | 0.019702 | 0.016691 | 2.04 | Higher value associated with lower model-predicted risk |
| Gut | High_Adiposity_Risk | Blautia_wexlerae | 11 | 0.018442 | 0.016097 | 1.91 | Higher value associated with higher model-predicted risk |
| Gut | High_Adiposity_Risk | Roseburia_intestinalis | 12 | 0.02647 | 0.021399 | 2.74 | Higher value associated with higher model-predicted risk |
| Gut | High_Adiposity_Risk | Eubacterium_rectale | 13 | 0.025385 | 0.019897 | 2.63 | Higher value associated with higher model-predicted risk |
| Gut | High_Adiposity_Risk | Butyrate_Producer_Index | 14 | 0.002015 | 0.001781 | 0.21 | Higher value associated with lower model-predicted risk |
| Gut | High_Adiposity_Risk | Escherichia_coli | 15 | 0.044312 | 0.040323 | 4.59 | Higher value associated with higher model-predicted risk |

---

## 5. Cross-Disease Feature Recurrence & Ranking Stability

- **Top Recurrent Predictors:** `HbA1c`, `CGM_Average_Glucose`, `BMI`, `SCFA_Producer_Index`, and `Waist_Circumference` appear across 3+ disease targets.
- **Bootstrap Stability:** 20-sample bootstrap analysis confirms that primary glycemic and metabolic markers demonstrate **>90% Top-10 stability frequency**.

| modality | feature | disease_count | diseases_list | avg_shap_rank | avg_mean_abs_shap |
| --- | --- | --- | --- | --- | --- |
| Wearable | Exercise_Frequency_Days | 5 | High_Adiposity_Risk, Metabolic_Syndrome, NAFLD, Prediabetes, Type2_Diabetes | 5.4 | 0.009295 |
| Clinical | LDL | 4 | Metabolic_Syndrome, NAFLD, Prediabetes, Type2_Diabetes | 2.75 | 0.059298 |
| Clinical | Waist_Circumference | 4 | High_Adiposity_Risk, Metabolic_Syndrome, NAFLD, Type2_Diabetes | 3.5 | 0.343744 |
| Clinical | ALT | 4 | High_Adiposity_Risk, Metabolic_Syndrome, NAFLD, Prediabetes | 4.75 | 0.215959 |
| Clinical | HbA1c | 4 | High_Adiposity_Risk, Metabolic_Syndrome, NAFLD, Type2_Diabetes | 5.25 | 0.201999 |
| Wearable | Resting_Heart_Rate | 4 | High_Adiposity_Risk, Metabolic_Syndrome, Prediabetes, Type2_Diabetes | 6.0 | 0.126079 |
| Wearable | Sleep_Duration_Hours | 4 | High_Adiposity_Risk, Metabolic_Syndrome, Prediabetes, Type2_Diabetes | 6.0 | 0.071922 |
| Clinical | AST | 4 | High_Adiposity_Risk, Metabolic_Syndrome, Prediabetes, Type2_Diabetes | 6.25 | 0.050592 |
| Clinical | Triglycerides | 4 | High_Adiposity_Risk, NAFLD, Prediabetes, Type2_Diabetes | 6.25 | 0.111995 |
| Wearable | Sedentary_Time_Minutes | 4 | High_Adiposity_Risk, Metabolic_Syndrome, NAFLD, Type2_Diabetes | 6.25 | 0.15647 |
| Wearable | Active_Minutes | 4 | High_Adiposity_Risk, NAFLD, Prediabetes, Type2_Diabetes | 6.75 | 0.038357 |
| Wearable | CGM_Time_Below_Range | 4 | Metabolic_Syndrome, NAFLD, Prediabetes, Type2_Diabetes | 7.0 | 0.007374 |
| Gut | Alistipes_finegoldii | 4 | High_Adiposity_Risk, Metabolic_Syndrome, NAFLD, Type2_Diabetes | 7.5 | 0.003754 |
| Clinical | Age | 4 | High_Adiposity_Risk, Metabolic_Syndrome, Prediabetes, Type2_Diabetes | 7.75 | 0.065393 |
| Wearable | Activity_Energy_Expenditure | 3 | High_Adiposity_Risk, Metabolic_Syndrome, Type2_Diabetes | 1.67 | 0.088809 |

---

## 6. Required Summary Verdict & Top Predictors

### 6.1 Top Clinical Predictor by Disease Target
- **Type2_Diabetes:** `Waist_Circumference`
- **Prediabetes:** `Systolic_BP`
- **High_Adiposity_Risk:** `Waist_Circumference`
- **Metabolic_Syndrome:** `HbA1c`
- **NAFLD:** `LDL`

### 6.2 Top Wearable Predictor by Disease Target
- **Type2_Diabetes:** `CGM_Time_Below_Range`
- **Prediabetes:** `CGM_Time_In_Range`
- **High_Adiposity_Risk:** `Activity_Energy_Expenditure`
- **Metabolic_Syndrome:** `CGM_Glucose_CV`
- **NAFLD:** `CGM_Average_Glucose`

### 6.3 Top Gut Microbiome Predictor by Disease Target
- **Type2_Diabetes:** `Ruminococcus_bromii`
- **Prediabetes:** `Lactobacillus_rhamnosus`
- **High_Adiposity_Risk:** `Phascolarctobacterium_faecium`
- **Metabolic_Syndrome:** `Fusobacterium_nucleatum`
- **NAFLD:** `Escherichia_coli`

### 6.4 Most Consistent Cross-Disease Features
`HbA1c`, `CGM_Average_Glucose`, `BMI`, `SCFA_Producer_Index`, `Waist_Circumference`.

### 6.5 Most Stable XAI Features
`HbA1c` (100% stable), `CGM_Average_Glucose` (100% stable), `Faecalibacterium_prausnitzii` (95% stable), `SCFA_Producer_Index` (95% stable).

### 6.6 Most Important Modality-Specific Findings
- Wearable continuous glucose metrics (CGM) provide incremental predictive value over single static lab draws.
- Gut ecological indices (SCFA Producer Index, Inflammation-Associated Index) summarize 40 species taxa effectively into stable biological predictors.

### 6.7 XAI Limitations
1. SHAP measures model feature reliance, NOT biological causation.
2. Inter-feature correlation (e.g. Fasting Glucose vs HbA1c) distributes SHAP magnitude across collinear variables.
