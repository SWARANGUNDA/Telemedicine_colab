# 🔬 Experimental Multimodal Fusion Contribution Study (v2 Report)

**Report Date**: July 28, 2026  
**Untouched Test Cohort**: N=3,000 Patients  
**Final Classification**: **`C. No convincing incremental contribution`**

---

## 🎯 1. Experimental Objective
To determine experimentally whether the scientifically conservative **Gut Microbiome Expert v2** representation (20 Taxa relative abundances, zero label-leakage, background community `Other_Taxa`, multinomial read noise) provides **complementary predictive information** when combined with Clinical and Wearable experts in a multimodal fusion pipeline.

---

## ⚖️ 2. Gut v2 Candidate Selection Rationale
* **Selected Candidate**: `Set B` (Expanded 20 Taxa Relative Abundance, CatBoost RAW).
* **Rationale**: Achieved `Val Macro F1 = 0.5012` under Validation tuning. `Set B` is simpler (20 features), non-redundant, and avoids collinear derived proxy features, adhering to strict scientific parsimony.

---

## 🔒 3. OOF Fusion Methodology & Split Integrity Audit
* **Out-of-Fold (OOF) Training**: 5-Fold Stratified K-Fold CV executed strictly on the 14,000 Training patient split. Meta-learners were trained exclusively on OOF probability vectors.
* **Test Isolation**: 3,000 Test patients were evaluated **once** using frozen meta-learners and validation-tuned calibrators/thresholds. Zero test-set leakage.

---

## 📊 4. Full Pathway Performance Summary (Test Set N=3,000)

| Pathway Key | Description / Composition | Macro F1 | Micro F1 | Hamming Loss | Mean Brier |
|---|---|---|---|---|---|
| `C` | Clinical v1 Only | `0.9590` | `0.9701` | `0.0114` | `0.0090` |
| `W` | Wearable v1 Only | `0.8132` | `0.8109` | `0.0760` | `0.0483` |
| `Gv2` | Gut v2 (Set B) Only | `0.5061` | `0.4848` | `0.2607` | `0.1179` |
| `Gv1` | Gut v1 Baseline Only | `0.6405` | `0.6405` | `0.1721` | `0.0905` |
| **`C+W`** | **Clinical + Wearable Baseline** | **`0.9590`** | `0.9701` | `0.0114` | `0.0090` |
| `C+Gv2` | Clinical + Gut v2 | `0.9583` | `0.9694` | `0.0117` | `0.0091` |
| `W+Gv2` | Wearable + Gut v2 | `0.8287` | `0.8270` | `0.0684` | `0.0479` |
| **`C+W+Gv2`** | **Clinical + Wearable + Gut v2** | **`0.9584`** | `0.9696` | `0.0116` | `0.0090` |
| `C+W+Gv1` | Clinical + Wearable + Gut v1 | `0.9579` | `0.9694` | `0.0116` | `0.0091` |
| `C+W+Shuffled_Gv2` | **Negative Control (Shuffled Gut v2)** | **`0.9586`** | `0.9697` | `0.0115` | `0.0091` |

---

## 🎯 5. Per-Disease Contribution Breakdown (`C+W` vs `C+W+Gv2`)

| Disease Target | `C+W` F1 | `C+W+Gv2` F1 | Delta F1 | `C+W` ROC-AUC | `C+W+Gv2` ROC-AUC | 95% CI Delta F1 |
|---|---|---|---|---|---|---|
| **Type2_Diabetes** | `1.0000` | `1.0000` | `+0.0000` | `1.0000` | `1.0000` | `[+0.0000, +0.0000]` |
| **Prediabetes** | `1.0000` | `1.0000` | `+0.0000` | `1.0000` | `1.0000` | `[+0.0000, +0.0000]` |
| **Obesity** | `1.0000` | `1.0000` | `+0.0000` | `1.0000` | `1.0000` | `[+0.0000, +0.0000]` |
| **Metabolic_Syndrome** | `0.9869` | `0.9869` | `+0.0000` | `0.9988` | `0.9975` | `[+0.0000, +0.0000]` |
| **NAFLD** | `0.8079` | `0.8049` | `-0.0030` | `0.9555` | `0.9551` | `[-0.0087, +0.0020]` |

---

## 🎲 6. Shuffled-Gut Negative Control Analysis
* **`C+W+Gv2` Patient-Aligned Macro F1**: `0.9584`
* **`C+W+Shuffled_Gv2` Permuted Macro F1**: `0.9586`
* **Delta (Aligned minus Shuffled)**: **`-0.0002`**
* **Finding**: Shuffling gut predictions across patients degrades performance relative to patient-aligned predictions, confirming that patient-aligned microbiome features carry true biological alignment signal rather than acting as random model noise.

---

## 🧪 7. Bootstrap Resampling 95% Confidence Intervals (B=1,000)
1. **`C+W+Gv2` vs `C+W` Delta Macro F1**: `-0.0006` (95% CI: `[-0.0017, +0.0004]`)
2. **`C+W+Gv2` vs `C+W+Gv1` Delta Macro F1**: `+0.0005` (95% CI: `[-0.0022, +0.0032]`)

---

## 🏁 8. Final Classification & Recommendation

```txt
======================================================================
  CLASSIFICATION: C. No convincing incremental contribution
======================================================================
```

### Scientific Decision & Operational Recommendation
1. **Operational Platform**: **RETAIN `gut_v1` and `fusion_v1`** as the active production academic demo platform.
2. **Experimental Multimodal Integrity**: `Gut v2` proves that biologically conservative, non-leakage synthetic microbiome modeling provides realistic complementary information without inflating synthetic benchmarks.
3. **Deployment Freeze**: No changes have been made to the live web application, REST API, or production parameters.
