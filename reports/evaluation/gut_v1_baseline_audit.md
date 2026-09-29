# 📊 Gut Microbiome Expert v1 Baseline Audit Report

**Audit Date**: July 28, 2026  
**Baseline Version**: Gut Expert v1.0 (Frozen)  
**Overall Performance**: Macro F1 = **0.6489** | Micro F1 = **0.6562** | Hamming Loss = **0.1415** | Mean Brier = **0.0918**

---

## 1. Feature Schema & Order
The frozen `gut_v1` predictor schema ([gut_features.json](file:///c:/Users/swara/OneDrive/Desktop/TeleMed/expert_models/schemas/gut_features.json)) consists of exactly 10 features in the following strict order:

| Index | Feature Name | Dtype | Range | Required | Missing Policy | Category |
|---|---|---|---|---|---|---|
| 0 | `Akkermansia` | float64 | [0.0, 30.0] % | True | Impute Median | Beneficial |
| 1 | `Faecalibacterium` | float64 | [0.0, 40.0] % | True | Impute Median | Beneficial |
| 2 | `Bifidobacterium` | float64 | [0.0, 30.0] % | True | Impute Median | Beneficial |
| 3 | `Roseburia` | float64 | [0.0, 25.0] % | False | Preserve NaN / Impute | Beneficial |
| 4 | `Alistipes` | float64 | [0.0, 20.0] % | False | Preserve NaN / Impute | Beneficial |
| 5 | `Escherichia_Shigella` | float64 | [0.0, 25.0] % | False | Preserve NaN / Impute | Inflammatory |
| 6 | `Collinsella` | float64 | [0.0, 20.0] % | False | Preserve NaN / Impute | Inflammatory |
| 7 | `Prevotella` | float64 | [0.0, 40.0] % | False | Preserve NaN / Impute | Context-Dependent |
| 8 | `Blautia` | float64 | [0.0, 30.0] % | False | Preserve NaN / Impute | Context-Dependent |
| 9 | `Shannon_Diversity_Index` | float64 | [0.5, 6.0] | True | Impute Median | Diversity Index |

---

## 2. Taxa & Generation Method

### Included Taxa (9 Taxa total)
* **Beneficial (5)**: *Akkermansia*, *Faecalibacterium*, *Bifidobacterium*, *Roseburia*, *Alistipes*
* **Inflammatory (2)**: *Escherichia_Shigella*, *Collinsella*
* **Context-Dependent (2)**: *Prevotella*, *Blautia*

### Generation Method & Disease-Conditioned Rules
1. **Base Distribution**: Healthy relative abundances generated via Truncated Normal distributions.
2. **Latent Risk Score ($R \in [0, 1]$)**: Integrated clinical biomarkers (BMI, HbA1c, Fasting Glucose, BP, Lipids, Liver Enzymes) + family history + active disease label weights.
3. **Additive Disease Shifts**: Disease labels directly apply additive mean shifts ($\Delta$) to taxa relative abundances:
   - *Type 2 Diabetes*: `Faecalibacterium` ($-3.5\%$), `Collinsella` ($+2.5\%$), `Escherichia_Shigella` ($+3.0\%$), `Akkermansia` ($-2.0\%$).
   - *Obesity*: `Faecalibacterium` ($-2.0\%$), `Escherichia_Shigella` ($+2.0\%$), `Collinsella` ($+1.8\%$).
   - *NAFLD*: `Escherichia_Shigella` ($+2.5\%$), `Collinsella` ($+2.2\%$), `Faecalibacterium` ($-2.0\%$).
   - *Cumulative Cap*: Cumulative disease shifts scaled by `MAX_CUMULATIVE_SHIFT_FACTOR = 1.4`.

### Diversity Calculation
* `Shannon_Diversity_Index` is calculated via synthetic formula:
  $$ \text{Shannon} = 3.2 - 0.6 \times R + 0.035 \times \sum (\text{Beneficial}) - 0.06 \times \sum (\text{Inflammatory}) + \mathcal{N}(0, 0.2) $$

### Correlation Structure
* Inter-taxa correlation target matrix enforced via Gaussian copula transform (`correlation_strength = 0.8`).
* Positive correlation among beneficial taxa ($r = +0.25$ to $+0.40$), negative correlation between beneficial and inflammatory taxa ($r = -0.20$ to $-0.30$).

### Missingness & Zero Handling
* **Zeros**: No true structural zero sampling. Abundance distributions bounded at 0.0, but zero inflation was not explicitly modeled.
* **Missingness**: Missing values imputed via preprocessor median or preserved for native GBDT handling.

---

## 3. Data Split & Preprocessing

* **Master Patient Split**: 20,000 total patients divided into:
  - **Train**: 14,000 patients (70%)
  - **Validation**: 3,000 patients (15%)
  - **Test**: 3,000 patients (15%)
* **Preprocessor**: `ExpertPreprocessor(scale_numeric=False, preserve_nans=True)`.

---

## 4. Model Architecture & Hyperparameters

* **Selected Architecture**: Multi-Output **CatBoostClassifier**
* **Hyperparameters**:
  - `iterations`: 500
  - `depth`: 6
  - `learning_rate`: 0.05
  - `loss_function`: `Logloss`
  - `random_seed`: 42
* **Probability Calibration**: Isotonic Regression fitted per disease target on the Validation split.
* **Threshold Tuning**: Performed on the Validation split by maximizing F1 score per target.

---

## 5. Baseline Performance & Per-Disease Metrics (Untouched Test Set)

| Target Disease | ROC-AUC | PR-AUC | Precision | Recall | Specificity | F1 Score | Brier Score | Calibrated Threshold |
|---|---|---|---|---|---|---|---|---|
| **Type2_Diabetes** | 0.9359 | 0.6981 | 0.6531 | 0.6427 | 0.9316 | **0.6479** | 0.0807 | 0.34 |
| **Prediabetes** | 0.8324 | 0.4383 | 0.4499 | 0.6748 | 0.8056 | **0.5399** | 0.1227 | 0.29 |
| **Obesity** | 0.9372 | 0.8130 | 0.7082 | 0.7974 | 0.8865 | **0.7502** | 0.0917 | 0.34 |
| **Metabolic_Syndrome** | 0.9322 | 0.7361 | 0.6540 | 0.7666 | 0.8977 | **0.7058** | 0.0882 | 0.26 |
| **NAFLD** | 0.9307 | 0.6362 | 0.6202 | 0.5825 | 0.9432 | **0.6008** | 0.0756 | 0.32 |
| **MACRO AVERAGE** | **-** | **-** | **-** | **-** | **-** | **0.6489** | **0.0918** | **-** |

### Confusion Matrices (Test Set, N=3,000)
- **Type2_Diabetes**: `TN=2328, FP=171, FN=179, TP=322`
- **Prediabetes**: `TN=1956, FP=472, FN=186, TP=386`
- **Obesity**: `TN=1977, FP=253, FN=156, TP=614`
- **Metabolic_Syndrome**: `TN=2151, FP=245, FN=141, TP=463`
- **NAFLD**: `TN=2441, FP=147, FN=172, TP=240`

---

## 6. Key SHAP Feature Drivers
Global SHAP importance ranking across all 5 disease targets:
1. `Faecalibacterium` (Primary beneficial driver; depletion strongly pushes disease risk)
2. `Shannon_Diversity_Index` (Global health indicator; low diversity increases risk)
3. `Escherichia_Shigella` (Primary inflammatory driver; enrichment increases risk)
4. `Collinsella` (Secondary dysbiotic driver)
5. `Akkermansia` (Gut barrier integrity marker)
