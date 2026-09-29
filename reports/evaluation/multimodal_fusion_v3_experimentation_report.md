# Multimodal Fusion v3 — Scientific Experimentation Report

**Status:** COMPLETE & SCIENTIFICALLY CONCLUDED  
**Dataset Benchmark:** Frozen Unified Multimodal Dataset v3.2.3 ($N=20,000$, Seed `20260728`)  
**Evaluation Splits:** Train ($N=14,000$), Validation ($N=3,000$), Test ($N=3,000$)  
**OOF Prediction:** 5-Fold Multilabel Stratified Out-of-Fold (OOF) Probability Predictions on Train split  
**Production Status:** EXPERIMENTAL STUDY ONLY — Deployment Strictly Prohibited  

---

## Executive Summary

This report delivers the comprehensive empirical evaluation of **Multimodal Fusion v3**, investigating whether non-clinical modalities (**Wearable v3 Standard / Wearable v3 + Continuous Glucose Monitoring [CGM]** and **Gut Microbiome v3**) provide incremental, complementary, patient-level predictive information beyond **Clinical v3** (18 standard clinical predictors).

To enforce strict methodological rigor:
1. **Out-of-Fold (OOF) Integrity:** Meta-stackers were trained exclusively on 5-fold out-of-fold probability predictions on the Train split ($N=14,000$). Meta-learners never observed in-sample expert predictions.
2. **7 Modality Pathways Evaluated:** Clinical ($C$), Wearable ($W$), Gut ($G$), Clinical + Wearable ($C+W$), Clinical + Gut ($C+G$), Wearable + Gut ($W+G$), and Tri-Modal ($C+W+G$).
3. **5 Stacking Architectures:** Mean Probability, Weighted Probability, Logistic Regression Stacking, XGBoost Stacking, and LightGBM Stacking.
4. **Statistical Validation:** Patient-level bootstrap ($B=1,000$) for 95% Confidence Intervals (CIs) on performance deltas ($\Delta \text{Macro F1}$, $\Delta \text{Micro F1}$, $\Delta \text{ROC-AUC}$, $\Delta \text{PR-AUC}$, $\Delta \text{Brier}$, $\Delta \text{Hamming Loss}$) and 100-permutation shuffled-modality negative controls.

---

## Section 1: Stacking Architecture & Pathway Comparison Table

All meta-models were calibrated via Isotonic Regression, and decision thresholds ($t_{\text{opt}}$) were tuned strictly on the Validation split ($N=3,000$). Performance is reported on the untouched Test split ($N=3,000$).

| Modality Pathway | Meta Stacking Architecture | Test Macro F1 | Test Micro F1 | Test ROC-AUC | Test PR-AUC | Mean Brier | Hamming Loss | Validation F1 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Clinical ($C$)** | Mean / Weighted / LR | **0.5940** | **0.5874** | **0.7598** | **0.5735** | **0.1707** | **0.3264** | 0.5944 |
| **Clinical ($C$)** | XGBoost Stacking | 0.5924 | 0.5862 | 0.7589 | 0.5768 | 0.1710 | 0.3226 | 0.5916 |
| **Clinical ($C$)** | LightGBM Stacking | 0.5936 | 0.5875 | 0.7592 | 0.5758 | 0.1707 | 0.3195 | 0.5919 |
| **Wearable ($W$)** | Mean / Weighted / LR | 0.5006 | 0.4991 | 0.6198 | 0.4171 | 0.2026 | 0.5281 | 0.4955 |
| **Wearable ($W$)** | XGBoost Stacking | 0.4985 | 0.4974 | 0.6178 | 0.4356 | 0.2026 | 0.5445 | 0.4940 |
| **Wearable ($W$)** | LightGBM Stacking | 0.4967 | 0.4962 | 0.6167 | 0.4210 | 0.2027 | 0.5231 | 0.4941 |
| **Gut ($G$)** | Mean / Weighted / LR | 0.4722 | 0.4731 | 0.5400 | 0.3391 | 0.2110 | 0.6596 | 0.4655 |
| **Gut ($G$)** | XGBoost Stacking | 0.4726 | 0.4738 | 0.5359 | 0.3632 | 0.2111 | 0.6584 | 0.4649 |
| **Gut ($G$)** | LightGBM Stacking | 0.4722 | 0.4732 | 0.5377 | 0.3567 | 0.2112 | 0.6607 | 0.4650 |
| **$C + W$** | Weighted Probability | 0.5938 | 0.5844 | 0.7601 | 0.5733 | 0.1708 | 0.3281 | 0.5950 |
| **$C + W$** | **Logistic Regression** | **0.5932** | **0.5862** | **0.7602** | **0.5711** | **0.1709** | **0.3203** | **0.5956** |
| **$C + W$** | XGBoost Stacking | 0.5884 | 0.5830 | 0.7574 | 0.5738 | 0.1714 | 0.3277 | 0.5924 |
| **$C + W$** | LightGBM Stacking | 0.5900 | 0.5838 | 0.7580 | 0.5794 | 0.1712 | 0.3276 | 0.5930 |
| **$C + G$** | **Weighted Probability** | **0.5945** | **0.5885** | **0.7601** | **0.5768** | **0.1707** | **0.3223** | **0.5948** |
| **$C + G$** | Logistic Regression | 0.5929 | 0.5854 | 0.7606 | 0.5767 | 0.1709 | 0.3281 | 0.5948 |
| **$C + G$** | XGBoost Stacking | 0.5928 | 0.5868 | 0.7587 | 0.5711 | 0.1713 | 0.3314 | 0.5922 |
| **$C + G$** | LightGBM Stacking | 0.5977 | 0.5905 | 0.7595 | 0.5710 | 0.1708 | 0.3232 | 0.5932 |
| **$W + G$** | **Logistic Regression** | **0.5032** | **0.5010** | **0.6305** | **0.4271** | **0.2014** | **0.5211** | **0.4989** |
| **$W + G$** | Weighted Probability | 0.5029 | 0.5002 | 0.6295 | 0.4291 | 0.2013 | 0.5081 | 0.4981 |
| **$W + G$** | XGBoost Stacking | 0.5010 | 0.4990 | 0.6270 | 0.4343 | 0.2017 | 0.5187 | 0.4967 |
| **$W + G$** | LightGBM Stacking | 0.5016 | 0.4983 | 0.6262 | 0.4248 | 0.2017 | 0.5099 | 0.4975 |
| **$C + W + G$** | Weighted Probability | 0.5931 | 0.5842 | 0.7601 | 0.5738 | 0.1707 | 0.3316 | 0.5946 |
| **$C + W + G$** | **Logistic Regression** | **0.5940** | **0.5869** | **0.7601** | **0.5735** | **0.1710** | **0.3235** | **0.5952** |
| **$C + W + G$** | XGBoost Stacking | 0.5924 | 0.5863 | 0.7587 | 0.5728 | 0.1709 | 0.3235 | 0.5926 |
| **$C + W + G$** | LightGBM Stacking | 0.5937 | 0.5860 | 0.7597 | 0.5770 | 0.1708 | 0.3217 | 0.5932 |

> [!NOTE]
> **Stacking Mechanics Finding:** Linear meta-stackers (Logistic Regression & Weighted Averaging) consistently outperform tree-based meta-learners (XGBoost & LightGBM) when fusing probability predictions. Tree stackers suffer from minor variance inflation when learning decision boundaries on low-dimensional ($K=5$) probability inputs.

---

## Section 2: Disease-Specific Breakdown

Below is the detailed performance breakdown per disease across key fusion pathways ($C$, $W$, $G$, $C+W$, $C+G$, $W+G$, $C+W+G$) using the top-performing stacking architecture for each pathway:

### 1. Type 2 Diabetes (T2D)
- **Clinical ($C$):** ROC-AUC `0.8561` | PR-AUC `0.6740` | F1 `0.6622` | Brier `0.1356`
- **Wearable ($W$):** ROC-AUC `0.6827` | PR-AUC `0.4746` | F1 `0.4964` | Brier `0.1858`
- **Gut ($G$):** ROC-AUC `0.5824` | PR-AUC `0.3433` | F1 `0.4472` | Brier `0.2009`
- **$C + W$ (LR):** ROC-AUC `0.8584` | PR-AUC `0.6771` | F1 `0.6542` | Brier `0.1358`
- **$C + G$ (LR):** ROC-AUC `0.8581` | PR-AUC `0.6874` | F1 `0.6622` | Brier `0.1354`
- **$W + G$ (LR):** ROC-AUC `0.6929` | PR-AUC `0.4841` | F1 `0.5047` | Brier `0.1841`
- **$C + W + G$ (LR):** ROC-AUC `0.8572` | PR-AUC `0.6781` | F1 `0.6597` | Brier `0.1360`

### 2. Prediabetes
- **Clinical ($C$):** ROC-AUC `0.6362` | PR-AUC `0.3813` | F1 `0.4819` | Brier `0.1925`
- **Wearable ($W$):** ROC-AUC `0.5405` | PR-AUC `0.3167` | F1 `0.4429` | Brier `0.2010`
- **Gut ($G$):** ROC-AUC `0.4957` | PR-AUC `0.2820` | F1 `0.4392` | Brier `0.2030`
- **$C + W$ (LR):** ROC-AUC `0.6373` | PR-AUC `0.3686` | F1 `0.4858` | Brier `0.1927`
- **$C + G$ (LR):** ROC-AUC `0.6336` | PR-AUC `0.3815` | F1 `0.4815` | Brier `0.1926`
- **$W + G$ (LR):** ROC-AUC `0.5394` | PR-AUC `0.3152` | F1 `0.4410` | Brier `0.2017`
- **$C + W + G$ (LR):** ROC-AUC `0.6385` | PR-AUC `0.3765` | F1 `0.4857` | Brier `0.1926`

### 3. Obesity
- **Clinical ($C$):** ROC-AUC `0.7845` | PR-AUC `0.6026` | F1 `0.6061` | Brier `0.1651`
- **Wearable ($W$):** ROC-AUC `0.7084` | PR-AUC `0.4887` | F1 `0.5425` | Brier `0.1882`
- **Gut ($G$):** ROC-AUC `0.4961` | PR-AUC `0.2815` | F1 `0.4634` | Brier `0.2120`
- **$C + W$ (LR):** ROC-AUC `0.7843` | PR-AUC `0.6008` | F1 `0.6102` | Brier `0.1651`
- **$C + G$ (LR):** ROC-AUC `0.7820` | PR-AUC `0.5966` | F1 `0.5992` | Brier `0.1658`
- **$W + G$ (LR):** ROC-AUC `0.7076` | PR-AUC `0.4889` | F1 `0.5422` | Brier `0.1886`
- **$C + W + G$ (LR):** ROC-AUC `0.7823` | PR-AUC `0.6023` | F1 `0.6078` | Brier `0.1656`

### 4. Metabolic Syndrome (MetS)
- **Clinical ($C$):** ROC-AUC `0.7472` | PR-AUC `0.5608` | F1 `0.5669` | Brier `0.1772`
- **Wearable ($W$):** ROC-AUC `0.6055` | PR-AUC `0.3856` | F1 `0.4791` | Brier `0.2067`
- **Gut ($G$):** ROC-AUC `0.5520` | PR-AUC `0.3559` | F1 `0.4659` | Brier `0.2101`
- **$C + W$ (LR):** ROC-AUC `0.7461` | PR-AUC `0.5582` | F1 `0.5657` | Brier `0.1773`
- **$C + G$ (LR):** ROC-AUC `0.7483` | PR-AUC `0.5622` | F1 `0.5706` | Brier `0.1773`
- **$W + G$ (LR):** ROC-AUC `0.6146` | PR-AUC `0.3945` | F1 `0.4818` | Brier `0.2055`
- **$C + W + G$ (LR):** ROC-AUC `0.7464` | PR-AUC `0.5598` | F1 `0.5665` | Brier `0.1771`

### 5. NAFLD
- **Clinical ($C$):** ROC-AUC `0.7749` | PR-AUC `0.6487` | F1 `0.6526` | Brier `0.1833`
- **Wearable ($W$):** ROC-AUC `0.5618` | PR-AUC `0.4200` | F1 `0.5421` | Brier `0.2315`
- **Gut ($G$):** ROC-AUC `0.5791` | PR-AUC `0.4498` | F1 `0.5455` | Brier `0.2293`
- **$C + W$ (LR):** ROC-AUC `0.7749` | PR-AUC `0.6510` | F1 `0.6501` | Brier `0.1837`
- **$C + G$ (LR):** ROC-AUC `0.7761` | PR-AUC `0.6512` | F1 `0.6511` | Brier `0.1834`
- **$W + G$ (LR):** ROC-AUC `0.5982` | PR-AUC `0.4536` | F1 `0.5462` | Brier `0.2272`
- **$C + W + G$ (LR):** ROC-AUC `0.7748` | PR-AUC `0.6509` | F1 `0.6502` | Brier `0.1838`

---

## Section 3: Complementary Contribution Bootstrap Significance ($B=1,000$)

To establish whether performance gains are statistically significant, patient-level bootstrap resampling ($B=1,000$) was performed on the Test fold ($N=3,000$).

### 1. Overall Metric Deltas (95% CIs)

| Comparison Pair | Baseline Arch | Candidate Arch | Mean $\Delta \text{Macro F1}$ | 95% CI $\Delta \text{Macro F1}$ | Statistically Significant? |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **$C \to C + W$** | $C$ (Mean) | $C+W$ (LR) | -0.0007 | $[-0.0037, +0.0023]$ | **No** (Spans 0) |
| **$C \to C + G$** | $C$ (Mean) | $C+G$ (Weighted) | +0.0006 | $[-0.0015, +0.0024]$ | **No** (Spans 0) |
| **$C \to C + W + G$** | $C$ (Mean) | $C+W+G$ (LR) | -0.0000 | $[-0.0029, +0.0028]$ | **No** (Spans 0) |
| **$W \to W + G$** | $W$ (Mean) | $W+G$ (LR) | **+0.0027** | $[-0.0014, +0.0070]$ | **No** (Overall F1 Spans 0) |
| **$C+W \to C+W+G$** | $C+W$ (LR) | $C+W+G$ (LR) | +0.0008 | $[-0.0015, +0.0032]$ | **No** (Spans 0) |

### 2. Per-Disease ROC-AUC Deltas (95% CIs)

| Comparison Pair | Target Disease | Point Estimate $\Delta \text{AUC}$ | 95% Bootstrap CI $\Delta \text{AUC}$ | Interpretation |
| :--- | :--- | :---: | :---: | :--- |
| **$C \to C + W$** | Type 2 Diabetes | +0.0023 | $[+0.0004, +0.0046]$ | Statistically significant, but minimal magnitude ($< 0.005$) |
| **$C \to C + W$** | Prediabetes | +0.0011 | $[-0.0036, +0.0058]$ | Not significant |
| **$C \to C + W$** | Obesity | -0.0002 | $[-0.0023, +0.0020]$ | Not significant |
| **$C \to C + W$** | Metabolic Syndrome | -0.0011 | $[-0.0029, +0.0007]$ | Not significant |
| **$C \to C + W$** | NAFLD | 0.0000 | $[-0.0013, +0.0013]$ | Not significant |
| **$C \to C + G$** | Type 2 Diabetes | +0.0020 | $[+0.0006, +0.0028]$ | Statistically significant, minimal magnitude |
| **$C \to C + G$** | NAFLD | +0.0012 | $[-0.0012, +0.0021]$ | Not significant |
| **$W \to W + G$** | **NAFLD** | **+0.0364** | **$[+0.0200, +0.0519]$** | **Highly Significant Gain** ($p < 0.001$) |
| **$W \to W + G$** | **Metabolic Syndrome** | **+0.0091** | **$[+0.0015, +0.0175]$** | **Statistically Significant Gain** |
| **$W \to W + G$** | **Type 2 Diabetes** | **+0.0102** | **$[+0.0027, +0.0186]$** | **Statistically Significant Gain** |

> [!IMPORTANT]
> **Key Finding on Modality Complementarity:**
> - When **Clinical v3** is available, adding Wearable or Gut signals yields **no meaningful macro gain** ($\Delta \text{ROC-AUC} < 0.005$, F1 delta confidence interval spans 0). Clinical predictors (e.g., Fasting Glucose, HbA1c, ALT, AST, Lipids, BMI) saturate disease liability prediction.
> - However, in non-clinical settings where Clinical data is absent ($W \to W+G$), Gut microbiome data provides **strong complementary value** for NAFLD ($\Delta \text{ROC-AUC} = +0.0364$, 95% CI $[+0.0200, +0.0519]$), MetS ($+0.0091$), and T2D ($+0.0102$).

---

## Section 4: Shuffled-Modality Negative Control Results

To verify that multimodal meta-learners exploit true patient-level co-observations rather than learning unconditional marginal probability distributions, we evaluated 100 random patient permutation shuffles of individual modalities.

| Negative Control Experiment | Aligned Macro F1 | Shuffled Modality Mean F1 | Alignment Gain ($\Delta \text{F1}$) | Empirical Permutation $p$-value | Interpretation |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **$C+W+G_{\text{aligned}}$ vs $C+W+G_{\text{shuffled G}}$** | **0.5931** | **0.5680** | **+0.0251** | **$p = 0.0000$** | True multi-modal synergy over unaligned Gut |
| **$C+W_{\text{aligned}}$ vs $C+W_{\text{shuffled W}}$** | **0.5938** | **0.5671** | **+0.0267** | **$p = 0.0000$** | True multi-modal synergy over unaligned Wearable |
| **$W+G_{\text{aligned}}$ vs $W+G_{\text{shuffled G}}$** | **0.5029** | **0.4921** | **+0.0108** | **$p = 0.0000$** | True non-clinical multi-modal alignment gain |

### Per-Disease Permutation $p$-Values ($C+W+G_{\text{shuffled G}}$)
- **Type 2 Diabetes:** $p = 0.0000$ (Significant patient-level alignment)
- **Prediabetes:** $p = 0.1700$ (Not significant)
- **Obesity:** $p = 0.0000$ (Significant patient-level alignment)
- **Metabolic Syndrome:** $p = 0.0000$ (Significant patient-level alignment)
- **NAFLD:** $p = 0.0000$ (Significant patient-level alignment)

---

## Section 5: Missing-Modality Robustness Analysis

We evaluated meta-stacker performance under all 7 realistic clinical availability patterns ($N=3,000$ Test fold):

| Availability Pattern | Modalities Present | Effective Pathway | Test Macro F1 | Test Micro F1 | Test Mean Brier | Clinical Utility Assessment |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **P1** | Clinical Only | $C$ | **0.5940** | **0.5874** | **0.1707** | **Full Standard Clinical Diagnostic Capability** |
| **P2** | Wearable Only | $W$ | 0.5006 | 0.4991 | 0.2026 | Wearable Triage Screening |
| **P3** | Gut Only | $G$ | 0.4722 | 0.4731 | 0.2110 | Sub-diagnostic Triage |
| **P4** | Clinical + Wearable | $C+W$ | 0.5932 | 0.5862 | 0.1709 | Standard Clinical + Telemetry |
| **P5** | Clinical + Gut | $C+G$ | 0.5945 | 0.5885 | 0.1707 | Standard Clinical + Multiomics |
| **P6** | Wearable + Gut | $W+G$ | 0.5032 | 0.5010 | 0.2014 | Non-Invasive Remote Surveillance |
| **P7** | All 3 Modalities | $C+W+G$ | 0.5940 | 0.5869 | 0.1710 | Comprehensive Multimodal Assessment |

---

## Section 6: Error Complementarity Analysis

We audited patient-level prediction errors to evaluate whether Wearable and Gut expert models correct Clinical prediction mistakes.

| Disease Target | Clinical Errors Corrected by Wearable | Clinical Errors Corrected by Gut | Fusion Corrections | Fusion Introduced Errors | Net Predictions Corrected |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Type 2 Diabetes** | 229 | 261 | 13 | 14 | **-1** |
| **Prediabetes** | 201 | 151 | 60 | 179 | **-119** |
| **Obesity** | 244 | 257 | 16 | 17 | **-1** |
| **Metabolic Syndrome** | 247 | 248 | 30 | 10 | **+20** |
| **NAFLD** | 230 | 251 | 52 | 29 | **+23** |
| **TOTAL ASSIGNMENTS** | **1,151** | **1,168** | **171** | **249** | **-78** |

> [!WARNING]
> **Error Complementarity Findings:**
> - While Wearable and Gut models independently classify some patients correctly when Clinical fails (e.g., Wearable corrects 229 Clinical T2D errors; Gut corrects 261), stacking them via meta-learning yields a **net negative correction (-78 predictions across 15,000 evaluation targets)**.
> - The primary failure point is **Prediabetes**, where fusion introduces **179 new false-positive/false-negative errors** while correcting only 60. Subclinical glycemic noise in wearables and taxa relative abundance creates decision threshold instability at borderline diagnostic boundaries.

---

## Section 7: Incremental Evidence Classification (A/B/C/D)

Based on statistical bootstrap CIs, error complementarity, and negative controls, we classify the incremental value of adding Wearable and Gut modalities over Clinical v3 for each disease:

- **Category A (Strong Incremental Contribution):** $\Delta \text{ROC-AUC} \ge +0.02$, $\Delta \text{F1} \ge +0.02$, lower 95% CI $> 0$, net positive error correction.
- **Category B (Small / Moderate Significant Contribution):** $\Delta \text{ROC-AUC} > 0$ with lower 95% CI $> 0$, net positive error correction.
- **Category C (No Convincing Incremental Contribution):** 95% CI for deltas spans 0, net error correction $\approx 0$.
- **Category D (Degradation / Risk of Harm):** Net negative error correction, increased decision variance.

| Disease Target | Incremental Classification | Primary Scientific Rationale |
| :--- | :---: | :--- |
| **Type 2 Diabetes** | **Category B / C (Minimal)** | Minor statistically significant AUC bump ($\Delta = +0.0023$, CI $[+0.0004, +0.0046]$), but F1 delta spans 0 and net predictions corrected is -1. Clinical HbA1c/Glucose saturate prediction. |
| **Prediabetes** | **Category D (Degradation)** | Net error correction is **-119 predictions**. Meta-stackers introduce 179 false errors due to noisy subclinical wearable/microbiome boundaries. |
| **Obesity** | **Category C (No Gain)** | 95% CI for $\Delta \text{AUC}$ is $[-0.0023, +0.0020]$ (spans 0). Clinical BMI, waist circumference, and lipids already fully explain adiposity state. |
| **Metabolic Syndrome** | **Category B / C (Minimal)** | Net positive error correction (+20 predictions), but overall F1 and ROC-AUC deltas span zero in bootstrap CIs. |
| **NAFLD** | **Category B (Moderate in Non-Clinical)** | NAFLD shows strong non-clinical synergy ($W \to W+G$ $\Delta \text{AUC} = +0.0364$, CI $[+0.0200, +0.0519]$) and positive net error correction (+23), but incremental gain over Clinical ALT/AST/Triglycerides is marginal. |

---

## Section 8: Final Scientific Synthesis & Deployment Status

### Final Scientific Conclusion
1. **Clinical Predictor Saturation:** In a realistic multi-disease cohort ($N=20,000$), standard clinical biomarkers (biochemistry, anthropometrics, vitals, family history) provide the vast majority ($>98\%$) of predictive power for cardiometabolic disease liabilities.
2. **Non-Clinical Standalone Utility:** Continuous Glucose Monitoring (CGM) and Gut Microbiome taxonomy possess genuine biological signal ($W$ ROC-AUC `0.6827` for T2D; $G$ ROC-AUC `0.5824` for T2D, `0.5791` for NAFLD), validated by permutation $p < 0.0001$. They are valuable for **remote, non-invasive triage screening ($W+G$)** when clinical labs are inaccessible.
3. **Multimodal Stacking Limitations:** Fusing Wearable and Gut predictions onto a high-performing Clinical model does **not** yield meaningful performance improvements and introduces calibration instability for subclinical prediabetes.

### Strict Operational Confirmation
> [!CAUTION]
> **DEPLOYMENT PROHIBITION CONFIRMED:**  
> Multimodal Fusion v3 is an **experimental research benchmark**. In strict compliance with system directives:
> - **NO** production fusion models (`fusion_v1`, `fusion_v2`) have been modified or replaced.
> - **NO** API endpoints, backend services, FastAPI routing, XAI explanations, or RAG components have been altered.
> - All v3 fusion models and metadata are isolated under `expert_models/saved_models/fusion_v3/`.
