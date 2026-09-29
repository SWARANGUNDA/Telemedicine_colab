# ⚔️ Scientific Comparative Analysis: Clinical v1 vs Clinical v2

**Report Date**: July 28, 2026  
**Evaluation Cohort**: $N = 3,000$ Untouched Test Patients (Identical Master Split)  
**Primary Finding**: Clinical v2 successfully eliminates **Deterministic Rule Reconstruction** while retaining high, medically genuine predictive discrimination ($\text{Macro F1} = 0.8747$). Lower performance on v2 reflects the removal of synthetic shortcuts rather than model degradation.

---

## 📊 1. Overall Multimodal Performance Comparison

| Metric | Clinical v1 (Deterministic Benchmark) | Clinical v2 (Latent Physiological Benchmark) | Performance Delta ($\text{v2} - \text{v1}$) | Scientific Interpretation |
|---|---|---|---|---|
| **Macro F1 Score** | `0.9590` | **`0.8747`** | **`-0.0843`** | Reflects realistic continuous disease overlap and treatment control. |
| **Micro F1 Score** | `0.9575` | **`0.8464`** | `-0.1111` | Evaluated across all multi-label disease instances. |
| **Hamming Loss** | `0.0162` | **`0.1063`** | `+0.0901` | Multi-label classification error rate under realistic noise. |
| **Mean Brier Score** | `0.0185` | **`0.0676`** | `+0.0491` | Isotonic probability calibration remains well-calibrated. |
| **95% Bootstrap CI (Macro F1)**| `[0.9520, 0.9660]` | **`[0.8666, 0.8820]`** | N/A | Strictly disjoint confidence intervals reflecting benchmark transition. |

---

## 🎯 2. Per-Disease Performance Comparison

| Target Disease | Clinical v1 F1 | Clinical v2 F1 | Delta F1 | Clinical v1 ROC-AUC | Clinical v2 ROC-AUC | Delta ROC-AUC | Primary Driver of Delta |
|---|---|---|---|---|---|---|---|
| **Type2_Diabetes** | `1.0000` | **`0.9513`** | `-0.0487` | `1.0000` | **`0.9943`** | `-0.0057` | $5.16\%$ fully controlled T2D under medication presenting with normal labs. |
| **Prediabetes** | `1.0000` | **`0.9243`** | `-0.0757` | `1.0000` | **`0.9863`** | `-0.0137` | Continuous dysglycemia progression replaces sharp ADA step function. |
| **Obesity** | `1.0000` | **`0.9513`** | `-0.0487` | `1.0000` | **`0.9962`** | `-0.0038` | Single-visit observed weight/height noise introduces $2.58\%$ rule disagreement. |
| **Metabolic_Syndrome**| `0.9869` | **`0.8237`** | `-0.1632` | `0.9985` | **`0.9723`** | `-0.0262` | Antihypertensive & lipid treatments reduce observed SBP/TG below ATP III rules. |
| **NAFLD** | `0.8079` | **`0.7228`** | `-0.0851` | `0.8845` | **`0.7295`** | `-0.1550` | Hepatic risk generated independently of T2D label ($31.17\%$ NAFLD+ normal ALT). |

---

## 🔍 3. Label Determinism & Rule Reconstruction Audit

### Comparison of Rule Reconstruction Disagreement

| Diagnostic Rule / Target | Clinical v1 Disagreement Rate | Clinical v2 Disagreement Rate | Scientific Significance |
|---|---|---|---|
| **T2D Step Rule (`FPG >= 126 \| HbA1c >= 6.5`)** | **`0.00%`** (100% Reconstructed) | **`19.81%`** (FPG) / **`12.25%`** (HbA1c) | Model can no longer use a simple 2-split rule to achieve 1.0000 F1. |
| **Obesity Step Rule (`BMI >= 30.00`)** | **`0.00%`** (100% Reconstructed) | **`2.58%`** (517 false pos/neg) | Single-split $\text{BMI} \ge 30.00$ fails, requiring multi-feature evaluation. |
| **MetS ATP III Criteria Sum ($\ge 3/5$)** | **`1.31%`** ($98.69\%$ Reconstructed) | **`7.69%`** (1,538 patients disagree) | Observed rule evaluation drops to $92.31\%$ accuracy due to treatment & noise. |

---

## 🏁 4. Methodological Rigor & Scientific Conclusion

> **Conclusion**: Clinical v2 is **scientifically superior** to Clinical v1 as an ML research benchmark. Clinical v1's F1 = 0.9590 was an artifact of synthetic step-function taggers. Clinical v2 eliminates this artifact while proving that gradient boosted decision trees retain high, genuine multivariate discrimination ($\text{Macro F1} = 0.8747$).
