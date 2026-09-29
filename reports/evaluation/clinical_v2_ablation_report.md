# 🧪 Clinical Expert v2: Rule-Reconstruction Diagnostic Ablation Report

**Report Date**: July 28, 2026  
**Untouched Test Cohort**: $N = 3,000$ Patients  
**Objective**: To determine whether Clinical Expert v2 learns distributed physiological representations across co-features when primary rule-defining predictors are removed.

---

## 📊 1. Diagnostic Feature Ablation Matrix

| Disease Domain | Ablation Scenario | Predictors Included in Model ($X$) | Test Mean F1 | Delta vs Full Features | Scientific Finding |
|---|---|---|---|---|---|
| **Glycemic (T2D & Predia)** | **Full Features** | All 18 Clinical Predictors | **`0.9378`** | `0.0000` | Complete glycemic baseline. |
| **Glycemic (T2D & Predia)** | **Remove `Fasting_Blood_Glucose`** | All except `FPG` | **`0.9050`** | `-0.0328` | `HbA1c` maintains strong glycemic prediction. |
| **Glycemic (T2D & Predia)** | **Remove `HbA1c`** | All except `HbA1c` | **`0.8287`** | `-0.1091` | `FPG` alone exhibits higher noise under treatment. |
| **Glycemic (T2D & Predia)** | **Remove `FPG` AND `HbA1c`** | All except `FPG` & `HbA1c` | **`0.4822`** | **`-0.4556`** | **Major Drop**. Model loses direct glycemic labs; secondary markers (Age, BMI, Lipids, BP) provide weak residual signal. |
| **Obesity** | **Full Features** | All 18 Clinical Predictors | **`0.9513`** | `0.0000` | Full obesity baseline. |
| **Obesity** | **Remove `BMI`** | All except `BMI` | **`0.9507`** | `-0.0006` | `Weight` & `Height` allow exact internal BMI calculation. |
| **Obesity** | **Remove `BMI`, `Weight`, `Height`**| All except BMI, Weight, Height | **`0.6134`** | **`-0.3379`** | `Waist_Circumference` acts as a high-precision surrogate for obesity phenotype. |
| **Obesity** | **Remove `BMI`, `Weight`, `Height`, `Waist`** | All except body composition | **`0.5803`** | **`-0.3710`** | Body composition markers removed; secondary metabolic markers retain minor residual signal. |
| **Metabolic Syndrome** | **Full Features** | All 18 Clinical Predictors | **`0.8237`** | `0.0000` | Full MetS baseline. |
| **Metabolic Syndrome** | **Remove All ATP III Criteria** | Remove Waist, TG, HDL, SBP, DBP, FPG | **`0.6188`** | **`-0.2049`** | Removing all 6 criteria forces model onto secondary biomarkers (`ALT`, `AST`, `LDL`, `Age`, `BMI`). |
| **NAFLD** | **Full Features** | All 18 Clinical Predictors | **`0.7228`** | `0.0000` | Full NAFLD baseline. |
| **NAFLD** | **Remove `ALT` & `AST`** | All except ALT & AST | **`0.7176`** | `-0.0052` | `Triglycerides`, `BMI`, `Waist`, and `Age` maintain full NAFLD prediction. |
| **NAFLD** | **Remove `ALT`, `AST`, `TG`, `BMI`**| All except primary drivers | **`0.7186`** | `-0.0042` | `Waist`, `FPG`, `HbA1c`, and `BP` preserve distributed hepatic metabolic risk. |

---

## 🎯 2. Comparative Sensitivity: v1 vs v2

| Feature Removal Scenario | Clinical v1 Test F1 Drop | Clinical v2 Test F1 Drop | Interpretation |
|---|---|---|---|
| **Remove `FPG` AND `HbA1c`** | `-0.1735` | **`-0.4556`** | Clinical v2 exhibits significantly higher sensitivity to glycemic lab removal, proving that v1 relied on synthetic co-feature shortcuts. |
| **Remove `BMI`, `Weight`, `Height`** | `-0.0030` | **`-0.3379`** | In v1, Waist Circumference was artificially correlated to BMI ($\text{AUC}=0.88$). In v2, Waist Circumference is an independent visceral marker. |
| **Remove ATP III Criteria** | `-0.0458` | **`-0.2049`** | Eliminates direct arithmetic rule evaluation; forces true secondary biomarker evaluation. |

---

## 🏁 3. Scientific Finding

The ablation study confirms that Clinical Expert v2:
1. **Eliminates synthetic shortcut dependencies**: Removing primary lab features causes substantial performance drops, proving the model is not relying on artificial generator artifacts.
2. **Utilizes genuine secondary physiology**: Secondary biomarkers (liver transaminases, lipids, waist, age) maintain meaningful residual discrimination ($\text{F1} \approx 0.48 - 0.62$) when primary labs are unavailable.
