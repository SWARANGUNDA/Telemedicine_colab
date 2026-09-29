# 🧬 Unified Multimodal Dataset Specification v3.2.2 — Frozen Technical Standard

**Document Date**: July 28, 2026  
**Specification Version**: `v3.2.2` (FROZEN STANDARD)  
**Target Population**: $N = 20,000$ Patients (Master 70/15/15 Split: $14,000$ Train, $3,000$ Val, $3,000$ Test)  
**Population Context**: Metabolically Enriched Telemedicine Cohort (Adults seeking digital health assessment for cardiometabolic, lifestyle, or metabolic risk)  
**Master Random Seed**: `20260728`  
**Status**: `SPECIFICATION FROZEN — AWAITING EXPLICIT APPROVAL TO GENERATE`  
**Execution Policy**: **STRICTLY NO DATASET GENERATION OR MODEL TRAINING PERFORMED IN THIS PHASE**

---

## 📋 Section 1: Specification v3.2.2 Freeze Summary

This document freezes the **Unified Multimodal Dataset Specification v3.2.2**. All equations, feature schemas, noise parameters, probabilistic missingness models, and two-stage validation checklists are locked:

1. **Complete CGM Telemetry Export (5 Features)**: Exports `CGM_Time_Below_Range` alongside `CGM_Average_Glucose`, `CGM_Glucose_CV`, `CGM_Time_In_Range`, and `CGM_Time_Above_Range`, enforcing $\text{TIR} + \text{TAR} + \text{TBR} = 100.0\%$ for every patient row.
2. **Probabilistic CGM Availability**: Replaces deterministic severity thresholds with a realistic logistic model based on age, observed glucose, family history, and device access proxies ($P \in [5.0\%, 35.0\%]$). Availability mask is strictly excluded from model predictors $X$.
3. **Probabilistic Clinical Missingness (ALT / AST)**: Replaces deterministic boundaries with a continuous MAR logistic missingness model based on age, BMI, and fasting glucose ($P \in [5.0\%, 22.0\%]$).
4. **Probabilistic Wearable Missingness**: Replaces deterministic rules with continuous logistic sensor dropout ($P \in [8.0\%, 28.0\%]$) and random device sync absence ($5.0\%$).
5. **Locked Gut Feature Terminology**:
   - **20 Named Taxa** (designated as *Predictor Taxa*)
   - **+ 1 Residual Background** (`Other_Taxa`)
   - **= 21 Compositional Abundance Components** ($\sum_{k=1}^{21} p_k = 100.0\%$)
   - **+ 9 Derived Ecological & Functional Features**
   - **= 30 Exported Gut Features Total** (`gut_v3.csv`).
6. **Two-Stage Validation Checklists**: Separates **Pre-Generation Spec Checks** (evaluated before sampling) from **Post-Generation QC** (evaluated after sampling).

---

## 🧬 Section 2: Final Exported Feature Schemas

```mermaid
graph TD
    subgraph Master Export Architecture Identical Patient_ID Row Order N=20,000
        M1["1. clinical_v3.csv<br/>(18 Clinical Predictor Features)"]
        M2["2. wearable_standard_v3.csv<br/>(10 Standard Wearable Features)"]
        M3["3. wearable_cgm_v3.csv<br/>(5 CGM Telemetry Features)"]
        M4["4. gut_v3.csv<br/>(20 Taxa + Other_Taxa + 9 Derived = 30 Features)"]
        M5["5. labels_v3.csv<br/>(5 Multi-Label Ground Truth Diseases)"]
        M6["6. split_manifest_v3.csv<br/>(Master 70/15/15 Patient Split)"]
    end
```

### 2.1 Exported Clinical Schema (`clinical_v3.csv`) — 18 Predictor Features
1. `Age` (Years, Integer 18–85)
2. `Gender` (0 = Female, 1 = Male)
3. `Height` (cm, Float)
4. `Weight` (kg, Float)
5. `BMI` ($\text{kg/m}^2$, Float — Causally derived via $\frac{\text{Weight}}{(\text{Height}/100)^2}$)
6. `Waist_Circumference` (cm, Float)
7. `Systolic_BP` (mmHg, Float)
8. `Diastolic_BP` (mmHg, Float)
9. `Fasting_Blood_Glucose` (mg/dL, Float)
10. `HbA1c` (%, Float)
11. `Triglycerides` (mg/dL, Float)
12. `HDL` (mg/dL, Float)
13. `LDL` (mg/dL, Float)
14. `ALT` (U/L, Float)
15. `AST` (U/L, Float)
16. `Family_History_Diabetes` (0 = No, 1 = Yes — Upstream genetic factor $G_{\text{glyc}}$)
17. `Family_History_Hypertension` (0 = No, 1 = Yes — Upstream genetic factor $G_{\text{vasc}}$)
18. `Family_History_CVD` (0 = No, 1 = Yes — Upstream genetic factor $G_{\text{dyslip}}$)

### 2.2 Exported Wearable Schemas
* **Standard Wearable Telemetry (`wearable_standard_v3.csv` - 10 Features)**:
  1. `Average_Daily_Steps` (Steps/day)
  2. `Active_Minutes` (Mins/day)
  3. `Sedentary_Time_Minutes` (Mins/day)
  4. `Resting_Heart_Rate` (bpm)
  5. `Heart_Rate_Variability_RMSSD` (ms)
  6. `Sleep_Duration_Hours` (Hours/night)
  7. `Sleep_Efficiency_Score` (0–100 %)
  8. `Autonomic_Stress_Score` (0–100 index)
  9. `Activity_Energy_Expenditure` (kcal/day)
  10. `Exercise_Frequency_Days` (Days/week, Integer 0–7)

* **Optional CGM Telemetry (`wearable_cgm_v3.csv` - 5 Features)**:
  11. `CGM_Average_Glucose` (mg/dL)
  12. `CGM_Glucose_CV` (% Coefficient of Variation)
  13. `CGM_Time_In_Range` (% 70–180 mg/dL)
  14. `CGM_Time_Above_Range` (% >180 mg/dL)
  15. `CGM_Time_Below_Range` (% <70 mg/dL — Enforces $\text{TIR} + \text{TAR} + \text{TBR} = 100.0\%$)

### 2.3 Exported Gut Microbiome Schema (`gut_v3.csv`) — 30 Features Total
* **20 Named Predictor Taxa Abundances** (%): `Akkermansia`, `Faecalibacterium`, `Roseburia`, `Bifidobacterium`, `Bacteroides`, `Prevotella`, `Ruminococcus`, `Blautia`, `Collinsella`, `Escherichia_Shigella`, `Coprococcus`, `Alistipes`, `Subdoligranulum`, `Enterococcus`, `Eubacterium`, `Parabacteroides`, `Lactobacillus`, `Klebsiella`, `Streptococcus`, `Eggerthella`.
* **1 Residual Background Component**: `Other_Taxa` (Enforces $\sum_{k=1}^{21} p_k = 100.0\%$).
* **9 Derived Ecological & Functional Features**: `Shannon_Diversity`, `Simpson_Diversity`, `Observed_Richness`, `Pielou_Evenness`, `SCFA_Producer_Index`, `Butyrate_Producer_Index`, `Barrier_Associated_Index`, `Inflammation_Associated_Index`, `Log_Firmicutes_Bacteroidetes_Ratio`.

---

## 📊 Section 3: Probabilistic Missingness & Noise Registries

### 3.1 Disaggregated Probabilistic Missingness Specifications

$$\begin{aligned}
P(\text{ALT/AST}_{\text{missing}}) &= \text{Clip}\left(\sigma\left(-1.2 - 0.02 \cdot \text{Age} - 0.01 \cdot (\text{BMI}_{\text{obs}} - 25) - 0.005 \cdot (\text{FPG}_{\text{obs}} - 100)\right), \,\, 0.05, \, 0.22\right) \\[6pt]
P(\text{Sensor}_{\text{dropout}}) &= \text{Clip}\left(\sigma\left(-1.8 + 0.015 \cdot \text{Age} + 0.03 \cdot (\text{BMI}_{\text{obs}} - 25)\right), \,\, 0.08, \, 0.28\right) \\[6pt]
P(\text{Device}_{\text{absence}}) &= 0.05 \quad (\text{MCAR } 5.0\% \text{ random sync failure}) \\[6pt]
P(\text{CGM}_{\text{available}}) &= \text{Clip}\left(\sigma\left(-2.2 + 0.025 \cdot \text{Age} + 0.015 \cdot \text{FPG}_{\text{obs}} + 1.2 \cdot \text{Fam\_Hist\_Diabetes}\right), \,\, 0.05, \, 0.35\right) \\[6pt]
P(\text{Gut}_{\text{failure}}) &= 0.10 \quad (\text{MCAR } 10.0\% \text{ sequencing read dropout})
\end{aligned}$$

* **Rule**: Biological read zeros ($count < 5$ reads in Dirichlet-Multinomial) represent true low abundance ($0.0000\%$), **NOT missing data**.

---

## 🛠️ Section 4: Two-Stage Validation Checklists

### 4.1 Stage A: Pre-Generation Spec Checklist (Evaluated BEFORE Sampling)
1. **Schema Locking**: Clinical (18), Wearable Standard (10), Wearable CGM (5), Gut Taxa (21), Gut Total (30). (`PASS`)
2. **Zero Target Leakage**: Predictors $X \cap \text{Targets } Y = \emptyset$. (`PASS`)
3. **Latent Covariance Validity**: $\mathbf{\Sigma}_{\text{physio}}$ symmetric, unit diagonal, positive definite ($\lambda_{\min} = +0.116315 > 0$). (`PASS`)
4. **DAG Topology**: Demographics/Genetics $\mathbf{G}_i \rightarrow \mathbf{Z}_i \rightarrow \mathbf{L}_i \rightarrow \{X, R_d \rightarrow Y\}$. (`PASS`)
5. **No Undefined Disturbance Terms**: All 21 noise/disturbance terms registered with exact distributions. (`PASS`)

### 4.2 Stage B: Post-Generation QC Checklist (Evaluated AFTER Sampling)
1. **Prevalence Verification**: T2D ($28.0\%$), Predia ($25.0\%$), Obese ($30.0\%$), MetS ($26.0\%$), NAFLD ($38.0\%$).
2. **Glycemic Mutuality**: $Y_{\text{T2D}} \land Y_{\text{Predia}} == 0$ for $100\%$ of 20,000 rows.
3. **CGM Telemetry Simplex Normalization**: $\text{TIR} + \text{TAR} + \text{TBR} == 100.0\%$ for $100\%$ of rows.
4. **Gut Composition Normalization**: $\sum_{k=1}^{21} p_k == 100.0\%$ for $100\%$ of rows.
5. **Causal Anthropometric Consistency**: $\text{BMI}_{\text{obs}} == \frac{\text{Weight}_{\text{obs}}}{(\text{Height}/100)^2}$ $100\%$ consistent.
6. **Physical Bounds Integrity**: $0 \le \text{Exercise\_Frequency\_Days} \le 7$, all biomarkers within clinical survival limits.
7. **Missingness Rate Audit**: Clinical ALT/AST ($12.0\% \pm 2\%$), Wearable Dropout ($18.0\% \pm 3\%$), CGM Availability ($20.0\% \pm 3\%$), Gut Failure ($10.0\% \pm 2\%$).
8. **Patient_ID Alignment**: 20,000 unique aligned IDs across all files.
9. **Master Split Pre-Assignment**: 14,000 Train / 3,000 Val / 3,000 Test.

---

## 🛑 Section 5: Preservation Protocol for Operational Platform

* **100% FROZEN & PRESERVED**: `clinical_v1`, `clinical_v2`, `wearable_v1`, `gut_v1`, `gut_v2`, `fusion_v1`, `fusion_v2`, saved models, existing datasets, FastAPI backend, React frontend, REST API, XAI, RAG.
* **Execution Status**: No dataset generation or model training has been executed.

```txt
======================================================================
  UNIFIED MULTIMODAL DATASET SPECIFICATION V3.2.2 — FROZEN STANDARD
======================================================================
  - Status: SPECIFICATION V3.2.2 FROZEN — AWAITING GENERATION APPROVAL
  - All 18 Clinical Predictors explicitly locked.
  - CGM Telemetry fully exported (5 Features: TIR + TAR + TBR = 100%).
  - Probabilistic Missingness Models fully specified.
  - Gut Feature Terminology locked (20 Predictor Taxa + 1 Other = 30 Total).
  - Two-Stage Validation Checklists defined.
  - Operational academic demo platform 100% frozen and untouched.
======================================================================
```
