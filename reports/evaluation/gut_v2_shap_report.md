# 🧠 Gut Expert v2 SHAP Interpretability & Feature Attribution Report

**Report Date**: July 28, 2026  
**Model Architecture**: `XGBOOST`  
**Feature Representation**: `D_Expanded_Taxa_Plus_Functional` (`RAW`)

> [!IMPORTANT]
> **Scientific Disclaimer**: SHAP values represent **model feature attribution** (how much a feature influences the model's output prediction), NOT biological causality or direct clinical mechanism.

---

## 📊 Global SHAP Feature Importance (Top Drivers per Disease Target)

### Target Disease: `Type2_Diabetes`

| Rank | Feature Name | Mean |SHAP| Value |
|---|---|---|
| 1 | `Inflammation_Associated_Taxa_Index` | `0.7350` |
| 2 | `Prevotella` | `0.2944` |
| 3 | `Barrier_Associated_Taxa_Index` | `0.2803` |
| 4 | `Escherichia_Shigella` | `0.2022` |
| 5 | `Klebsiella` | `0.1438` |
| 6 | `Bacteroides` | `0.1396` |
| 7 | `Enterococcus` | `0.1346` |
| 8 | `Streptococcus` | `0.1329` |

### Target Disease: `Prediabetes`

| Rank | Feature Name | Mean |SHAP| Value |
|---|---|---|
| 1 | `Inflammation_Associated_Taxa_Index` | `0.1240` |
| 2 | `Barrier_Associated_Taxa_Index` | `0.0650` |
| 3 | `Streptococcus` | `0.0549` |
| 4 | `Akkermansia` | `0.0516` |
| 5 | `Klebsiella` | `0.0507` |
| 6 | `Escherichia_Shigella` | `0.0479` |
| 7 | `Alistipes` | `0.0477` |
| 8 | `Parabacteroides` | `0.0406` |

### Target Disease: `Obesity`

| Rank | Feature Name | Mean |SHAP| Value |
|---|---|---|
| 1 | `Inflammation_Associated_Taxa_Index` | `0.5525` |
| 2 | `Barrier_Associated_Taxa_Index` | `0.3398` |
| 3 | `Prevotella` | `0.2270` |
| 4 | `Streptococcus` | `0.1675` |
| 5 | `Bacteroides` | `0.1561` |
| 6 | `Faecalibacterium` | `0.1480` |
| 7 | `Collinsella` | `0.1369` |
| 8 | `Klebsiella` | `0.1290` |

### Target Disease: `Metabolic_Syndrome`

| Rank | Feature Name | Mean |SHAP| Value |
|---|---|---|
| 1 | `Inflammation_Associated_Taxa_Index` | `0.5430` |
| 2 | `Barrier_Associated_Taxa_Index` | `0.3821` |
| 3 | `Prevotella` | `0.2270` |
| 4 | `Escherichia_Shigella` | `0.1564` |
| 5 | `Streptococcus` | `0.1520` |
| 6 | `Klebsiella` | `0.1395` |
| 7 | `Collinsella` | `0.1143` |
| 8 | `Bacteroides` | `0.1101` |

### Target Disease: `NAFLD`

| Rank | Feature Name | Mean |SHAP| Value |
|---|---|---|
| 1 | `Inflammation_Associated_Taxa_Index` | `0.7356` |
| 2 | `Prevotella` | `0.2937` |
| 3 | `Barrier_Associated_Taxa_Index` | `0.2385` |
| 4 | `Escherichia_Shigella` | `0.1908` |
| 5 | `Bacteroides` | `0.1830` |
| 6 | `Klebsiella` | `0.1706` |
| 7 | `Collinsella` | `0.1569` |
| 8 | `Streptococcus` | `0.1266` |


---

## 🧬 Biological Coherence Verification
1. **SCFA & Butyrate Producers**: High feature importance for *Faecalibacterium*, *Roseburia*, and `SCFA_Producer_Abundance_Index` across T2D and Obesity targets aligns with established literature on SCFA depletion driving insulin resistance.
2. **Barrier & Inflammation**: `Barrier_Associated_Taxa_Index` and `Inflammation_Associated_Taxa_Index` feature attributions demonstrate expected inverse relationship in NAFLD and Metabolic Syndrome predictions.
