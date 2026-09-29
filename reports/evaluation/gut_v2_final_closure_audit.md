# 🔬 Gut Microbiome Expert v2 Final Scientific Closure Audit Report

**Audit Date**: July 28, 2026  
**Status**: `COMPLETED & FROZEN`  
**Operational Recommendation**: **`RETAIN GUT v1`** (Keep `gut_v2` as an experimental conservative benchmark)

---

## 🔍 1. Validation vs Test Performance Discrepancy Investigation

### Quantitative Explanation of the +0.1105 F1 Increase
During initial reporting, the candidate selection ablation matrix listed `Val Macro F1 = 0.3826` (evaluated using **raw uncalibrated probabilities at default 0.50 threshold**), whereas the final test evaluation reported `Test Macro F1 = 0.4931` (evaluated using **Isotonic-calibrated probabilities at validation-tuned decision thresholds**).

When evaluated under identical post-processing steps, the Validation and Test performance match almost perfectly:

| Pipeline Stage | Validation Fold (N=3,000) | Test Fold (N=3,000) | Discrepancy |
|---|---|---|---|
| **Raw Probabilities (Default 0.50 Threshold)** | **0.3758** | **0.3751** | **`0.0007` (Negligible)** |
| **Calibrated Probabilities (Tuned Thresholds)** | **0.5000** | **0.4931** | **`0.0069` (Negligible)** |

### Strict Split Integrity & Leakage Verification
- **Target Ordering**: Identical (`Type2_Diabetes`, `Prediabetes`, `Obesity`, `Metabolic_Syndrome`, `NAFLD`) across all folds.
- **Feature Schema & Order**: Strict 24-feature order enforced by `ExpertPreprocessor`.
- **Prevalence Audit**: Class prevalence is identical across Train, Validation, and Test sets:
  - *Type2_Diabetes*: Train = 16.70%, Val = 16.63%, Test = 16.70%
  - *Prediabetes*: Train = 19.04%, Val = 19.10%, Test = 19.07%
  - *Obesity*: Train = 25.65%, Val = 25.70%, Test = 25.67%
  - *Metabolic_Syndrome*: Train = 20.16%, Val = 20.13%, Test = 20.13%
  - *NAFLD*: Train = 13.74%, Val = 13.73%, Test = 13.73%
- **Test Set Isolation**: **100% Verified**. No test-set threshold optimization, model selection, or feature engineering was performed.

### Per-Disease Validation vs Test Breakdown

| Target Disease | Val F1 (Tuned) | Test F1 (Tuned) | Val ROC-AUC | Test ROC-AUC | Val PR-AUC | Test PR-AUC | Val Brier | Test Brier |
|---|---|---|---|---|---|---|---|---|
| **Type2_Diabetes** | 0.5228 | 0.5308 | 0.8278 | 0.8395 | 0.5873 | 0.6060 | 0.0988 | 0.0995 |
| **Prediabetes** | 0.3237 | 0.3231 | 0.5644 | 0.5453 | 0.2171 | 0.2120 | 0.1534 | 0.1536 |
| **Obesity** | 0.5991 | 0.5706 | 0.8107 | 0.7988 | 0.6703 | 0.6572 | 0.1385 | 0.1396 |
| **Metabolic_Syndrome** | 0.5538 | 0.5444 | 0.8149 | 0.8026 | 0.6071 | 0.6029 | 0.1189 | 0.1195 |
| **NAFLD** | 0.5007 | 0.4966 | 0.8341 | 0.8359 | 0.5434 | 0.5403 | 0.0879 | 0.0886 |
| **MACRO AVERAGE** | **0.5000** | **0.4931** | **0.7704** | **0.7644** | **0.5250** | **0.5233** | **0.1195** | **0.1202** |

---

## ⚖️ 2. Candidate Model Re-Audit & Feature Parsimony

Comparing top candidates on the Validation fold:

| Candidate Configuration | Feat Count | Val Macro F1 (Raw) | Val Macro F1 (Tuned) | Val Mean Brier | Model Parsimony / Complexity |
|---|---|---|---|---|---|
| `Set_B_Expanded_Taxa_Only` (CatBoost RAW) | **20** | **0.3824** | **0.5012** | **0.1182** | **Optimal (Simpler, Non-Redundant)** |
| `Set_D_Expanded_Taxa_Plus_Functional` (XGBoost RAW) | 24 | 0.3826 | 0.5000 | 0.1193 | Redundant (Includes Derived Indices) |
| `Set_F_Reduced_NonRedundant` (CatBoost CLR) | 25 | 0.3802 | 0.4984 | 0.1180 | Higher Complexity (CLR + Indices) |

### Parsimony Decision
The $+0.0002$ difference between `Set D` ($0.3826$) and `Set B` ($0.3824$) is statistically negligible. Following Occam's razor and scientific parsimony, **`Set B` (Taxa-Only 20 Genera Relative Abundance)** or **`Set F` (CLR non-redundant)** represents a cleaner, non-redundant architecture that avoids collinear derived proxy features.

---

## 🧬 3. Corrected Derived-Feature Conclusion

* **Taxa-Only (`Set B`)**: Val Macro F1 = **0.3824**
* **Taxa + Functional Indices (`Set D`)**: Val Macro F1 = **0.3826**
* **Indices-Only (`Set G`)**: Val Macro F1 = **0.3452**

### Scientific Conclusion
The $+0.0002$ difference between Taxa-Only and Taxa+Indices is statistical noise. Derived functional proxy indices do **NOT** provide meaningful incremental predictive value over the raw 20-taxa relative abundances. The expanded 20-taxa relative abundance representation contains virtually **ALL** of the underlying biological predictive signal.

---

## 🧠 4. SHAP Dominance & Redundancy Analysis

When derived indices are included in GBDT models, `Inflammation_Associated_Taxa_Index` dominates SHAP importance (ranking #1 across all 5 disease targets). 

### Redundancy Explanation
Because `Inflammation_Associated_Taxa_Index` is an unweighted linear sum of 5 pathobiont genera (*Escherichia_Shigella*, *Collinsella*, *Enterococcus*, *Klebsiella*, *Streptococcus*), decision trees split on this aggregated composite feature because it concentrates variance into a single variable. 
- **Model Attribution vs Causality**: High SHAP attributions reflect decision tree splitting utility, **NOT independent biological causality**.
- In the `Taxa-Only` model (`Set B`), tree splits are distributed naturally across individual pathobiont genera (*Escherichia_Shigella*, *Klebsiella*, *Collinsella*), preserving true taxon-level interpretability.

---

## 🎯 5. Prediabetes Limitation Documented

In Gut v2, the continuous latent factor generator models early dysglycemia (Prediabetes) as a subtle metabolic state with weak dysbiotic shift (Cohen's $d < 0.35$).
* **Prediabetes Test ROC-AUC**: `0.5453`
* **Prediabetes Test PR-AUC**: `0.2120`
* **Prediabetes Test F1 Score**: `0.3231`

### Scientific Interpretation
Gut microbiome relative abundance alone provides limited discrimination for early prediabetes without continuous glucose monitoring (wearables) or glycemic lab markers (HbA1c/Fasting Glucose). The low F1 score is a legitimate reflection of subtle biology in a non-leakage dataset, not a flaw to be artificially tuned away.

---

## 📐 6. Dual-Dimension Reframing of Gut v1 vs Gut v2

| Dimension | Gut v1 Baseline | Gut v2 Experimental | Scientific Interpretation |
|---|---|---|---|
| **Predictive Performance (Macro F1)** | **`0.6489`** | `0.4931` | **Gut v1 achieves higher classification scores** due to direct additive disease-conditioned shift rules. |
| **Methodological & Biological Rigor** | Artificial Direct Rules | **High Scientific Rigor** | **Gut v2 is methodology superior**: zero target leakage, continuous latent biological factors, background community (`Other_Taxa`), multinomial sequencing noise, realistic zero inflation. |

Lower standalone performance in Gut v2 reflects the removal of artificially deterministic label-conditioned generation rules rather than a failure of expanded microbiome feature engineering.

---

## 🏁 7. Final Operational & Artifact Decision

```txt
======================================================================
  FINAL DECISION: RETAIN GUT v1 FOR PRODUCTION / DEMO PLATFORM
======================================================================
```

1. **Operational Platform**: **RETAIN `gut_v1`** as the frozen official baseline expert. The web platform, REST API, and fusion engine remain 100% unchanged.
2. **Experimental Benchmark**: **PRESERVE `gut_v2`** separately under `expert_models/saved_models/gut_v2/` and `Gut_Dataset_v2.csv` as an experimental, non-leakage, scientifically conservative benchmark.
3. **Execution Freeze**: No multimodal fusion retraining (`fusion_v2`), web application edits, or `gut_v1` modifications have been or will be made.
