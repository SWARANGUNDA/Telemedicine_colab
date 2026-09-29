# Final V3 System Integration — Architecture & Implementation Proposal

**Status:** PROPOSED PLAN ONLY — NO CODE OR ARTIFACT MODIFICATIONS EXECUTED  
**Target Platform:** TeleMed Multimodal Cardiometabolic Risk Engine (v3 Integration)  
**Frozen Science Baseline:** Unified Multimodal Dataset v3.2.3 ($N=20,000$, Seed `20260728`)  
**Frozen Model Benchmarks:** Clinical Expert v3, Wearable Expert v3 (10D Standard / 15D CGM), Gut Expert v3 (20 Taxa RAW), Fusion v3 Experiments  

---

## Executive Overview

This proposal details the production integration plan to upgrade TeleMed from legacy v1/v2 pipelines to the **v3 Unified Multimodal Scientific Baseline**. 

In accordance with strict operational governance:
- **NO datasets will be generated or modified.**
- **NO models will be retrained, fine-tuned, or re-calibrated.**
- **NO legacy v1/v2 artifacts or models will be deleted or broken.**
- **NO backend/frontend application code will be altered until explicit approval is granted.**

---

## 1. Current Architecture Audit

Inspection of the existing TeleMed web platform and ML pipeline reveals the following core component architecture:

```
[React Frontend SPA] (Vite + React)
        ↓ HTTP / REST
[FastAPI Backend Engine] (web_platform/backend)
  ├── API Routes: intake_routes, predict_routes, xai_routes, rag_routes
  └── Services: inference_service, intake_service, xai_service, rag_service_wrapper
        ↓ Inter-Module Python Calls
[Multimodal Intake Engine] (multimodal_data_intake_engine)
  ├── Availability Detection, Normalization, Imputation, Quality Scoring
        ↓
[Fusion Engine] (fusion_engine)
  ├── Legacy v1/v2 inference loaders (clinical_v2, wearable_v1, gut_v2, fusion_v2)
  └── Unified XAI Engine (SHAP calculation)
        ↓
[Medical RAG Engine] (medical_rag_engine)
  ├── ChromaDB Vector Store + Ingestion + Retriever
  └── LLM Clinical Report Generator (Groq/OpenAI API + Offline Fallback)
```

### Identified Integration Gaps for v3 Support
1. **Inference Loader Mismatch:** `web_platform/backend/services/inference_service.py` and `fusion_engine/inference.py` are configured to load legacy v1/v2 model artifacts (`clinical_v2`, `wearable_v1`, `gut_v2`, `fusion_v2`).
2. **Schema Inconsistency:** Intake validators (`multimodal_data_intake_engine/config.py`) do not use the frozen v3.2.2 feature definitions (18 Clinical predictors, 10 Standard + 5 CGM Wearable predictors, 20 Gut taxa predictors).
3. **CGM Missingness Inflexibility:** Current wearable intake lacks explicit routing for the dual-mode Wearable v3 model (Standard 10D vs Standard + CGM 15D).
4. **Pathway Routing Naïvety:** The existing router assumes "more modalities = strictly better," which contradicts the empirically verified v3 scientific findings (where Clinical v3 standalone captures 99.96% of achievable ROC-AUC).

---

## 2. Verified v3 Artifact Inventory

All v3 artifacts are frozen and verified on disk under `expert_models/saved_models/`:

### A. Clinical Expert v3
- **Payload Artifact:** `expert_models/saved_models/clinical_v3/clinical_v3_payload.joblib` (1.90 MB)
- **Metrics JSON:** `expert_models/saved_models/clinical_v3/clinical_v3_metrics.json`
- **Predictors (18):** `Age`, `Gender`, `Height`, `Weight`, `BMI`, `Waist_Circumference`, `Systolic_BP`, `Diastolic_BP`, `Fasting_Blood_Glucose`, `HbA1c`, `Triglycerides`, `HDL`, `LDL`, `ALT`, `AST`, `Family_History_Diabetes`, `Family_History_Hypertension`, `Family_History_CVD`.
- **Preprocessor:** `StandardScaler` fitted on Train fold ($N=14,000$).
- **Calibrator & Thresholds:** Isotonic Regression per target; $t_{\text{opt}} \in \{ \text{T2D: } 0.29, \text{ Prediabetes: } 0.25, \text{ Obesity: } 0.29, \text{ MetS: } 0.26, \text{ NAFLD: } 0.30 \}$.

### B. Wearable Expert v3
- **Payload Artifact:** `expert_models/saved_models/wearable_v3/wearable_v3_payload.joblib` (1.85 MB)
- **Metrics JSON:** `expert_models/saved_models/wearable_v3/wearable_v3_metrics.json`
- **Predictors:** 
  - **Experiment A (10D Standard):** `Average_Daily_Steps`, `Active_Minutes`, `Sedentary_Time_Minutes`, `Resting_Heart_Rate`, `Heart_Rate_Variability_RMSSD`, `Sleep_Duration_Hours`, `Sleep_Efficiency_Score`, `Autonomic_Stress_Score`, `Activity_Energy_Expenditure`, `Exercise_Frequency_Days`.
  - **Experiment B (15D + CGM):** Standard 10D + `CGM_Average_Glucose`, `CGM_Glucose_CV`, `CGM_Time_In_Range`, `CGM_Time_Above_Range`, `CGM_Time_Below_Range`.
- **Calibrator & Thresholds:** Isotonic; Exp A $t_{\text{opt}} \in [0.10, 0.27]$; Exp B $t_{\text{opt}} \in [0.21, 0.26]$.

### C. Gut Expert v3
- **Payload Artifact:** `expert_models/saved_models/gut_v3/gut_v3_payload.joblib` (1.87 MB)
- **Metrics JSON:** `expert_models/saved_models/gut_v3/gut_v3_metrics.json`
- **Predictors (20 Taxa RAW):** `Akkermansia`, `Faecalibacterium`, `Roseburia`, `Bifidobacterium`, `Bacteroides`, `Prevotella`, `Ruminococcus`, `Blautia`, `Collinsella`, `Escherichia_Shigella`, `Coprococcus`, `Alistipes`, `Subdoligranulum`, `Enterococcus`, `Eubacterium`, `Parabacteroides`, `Lactobacillus`, `Klebsiella`, `Streptococcus`, `Eggerthella`.
- **Calibrator & Thresholds:** Isotonic; $t_{\text{opt}} \in \{ \text{T2D: } 0.20, \text{ Prediabetes: } 0.10, \text{ Obesity: } 0.19, \text{ MetS: } 0.10, \text{ NAFLD: } 0.26 \}$.

### D. Multimodal Fusion v3
- **Metrics JSON:** `expert_models/saved_models/fusion_v3/fusion_v3_metrics.json` (54 KB)
- **Proven Stacking Method:** Logistic Regression / Weighted Averaging on 5 OOF disease probabilities.

### E. Immutable Targets (5)
1. `Type2_Diabetes`
2. `Prediabetes`
3. `Obesity`
4. `Metabolic_Syndrome`
5. `NAFLD`

---

## 3. Proposed Final System Architecture

The v3 integration adopts an asynchronous, modular architecture separating feature validation, model inference, scientific routing, SHAP attribution, and LLM text generation:

```
                  ┌───────────────────────────────┐
                  │      Patient Input (JSON)     │
                  └───────────────┬───────────────┘
                                  │
                  ┌───────────────▼───────────────┐
                  │   Intake & Feature Validation │
                  │  (Schema Verification & Mask) │
                  └───────────────┬───────────────┘
                                  │
                  ┌───────────────▼───────────────┐
                  │ Modality Availability Router  │
                  │  (Detects C, W_std, CGM, G)   │
                  └───────────────┬───────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
┌────────▼────────┐      ┌────────▼────────┐      ┌────────▼────────┐
│  Clinical v3    │      │   Wearable v3   │      │     Gut v3      │
│ (18 Predictors) │      │ (10D or 15D CGM)│      │  (20 Taxa RAW)  │
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │ Raw Probabilities
                  ┌───────────────▼───────────────┐
                  │ Scientific Evidence Router    │
                  │ (Clinical Anchor / W+G Remote)│
                  └───────────────┬───────────────┘
                                  │
                  ┌───────────────▼───────────────┐
                  │ Calibration & Threshold Engine│
                  │ (Isotonic + Frozen t_opt)     │
                  └───────────────┬───────────────┘
                                  │ Calibrated Risk & Binary Classes
         ┌────────────────────────┴────────────────────────┐
         │                                                 │
┌────────▼────────┐                               ┌────────▼────────┐
│ Unified v3 SHAP │                               │ Medical RAG LLM │
│ Attribution     │                               │ Explanation     │
└────────┬────────┘                               └────────┬────────┘
         │                                                 │
         └────────────────────────┬────────────────────────┘
                                  │
                  ┌───────────────▼───────────────┐
                  │ Complete Clinical UI Report   │
                  └───────────────────────────────┘
```

---

## 4. Dynamic Modality Routing Table

The system dynamically detects input completeness and executes the optimal pathway:

| Modality Combination Present | Modality Mask Code | Executed Expert Models | Decision Strategy & Rationale |
| :--- | :---: | :--- | :--- |
| **Clinical Only** | `C` | Clinical v3 | **Primary Diagnostic Engine:** Clinical v3 captures 99.96% of achievable ROC-AUC. |
| **Wearable Only** | `W` | Wearable v3 (10D or 15D) | **Remote Triage Pathway:** Non-invasive telemetry screening ($W$ T2D ROC-AUC `0.6827`). |
| **Gut Only** | `G` | Gut v3 | **Sub-diagnostic Triage:** Gut v3 standalone ($G$ NAFLD ROC-AUC `0.5791`). |
| **Clinical + Wearable** | `C+W` | Clinical v3 + Wearable v3 | **Clinical Anchor with Telemetry:** Clinical v3 provides primary diagnosis; Wearable provides continuous glucose/activity tracking. |
| **Clinical + Gut** | `C+G` | Clinical v3 + Gut v3 | **Clinical Anchor:** Clinical v3 provides primary diagnosis. |
| **Wearable + Gut** | `W+G` | Wearable v3 + Gut v3 | **RECOMMENDED REMOTE MULTIOMICS:** Statistically significant synergy for NAFLD ($\Delta \text{AUC} = +0.0364$, $p < 0.0001$). |
| **Clinical + Wearable + Gut** | `C+W+G` | Clinical v3 (+ W, G secondary) | **Full Panel:** Clinical v3 is used as primary diagnostic anchor to prevent subclinical prediabetes calibration degradation. |

---

## 5. Missing-Data Handling Strategy

The system explicitly distinguishes between **Entire Modality Unavailable** and **Partial Feature Missingness Inside an Available Modality**:

```
Input JSON
 ├── Check Modality Presence
 │    ├── Modality Absent -> Omit expert from routing; flag modality as "UNAVAILABLE"
 │    └── Modality Present -> Check Feature Completeness
 │         ├── All Features Present -> Execute Expert directly
 │         └── Features Missing -> Apply Frozen Modality Imputer (Train Medians)
```

1. **Entire Modality Missing:** The missing modality is excluded from expert inference. No dummy or synthetic values are fabricated to simulate missing modalities.
2. **Individual Feature Missingness Inside Available Modality:** Missing features are imputed using the frozen training medians from `split_manifest_v3.csv` Train set.
3. **Audit Trail:** Every prediction output explicitly includes `missing_features_imputed` and `modalities_supplied` vs `modalities_used`.

---

## 6. Wearable + CGM Dual-Mode Routing Strategy

Wearable v3 operates in two distinct, frozen model modes:

```
Wearable Input Received
 ├── Count CGM Features (CGM_Average_Glucose, Glucose_CV, TIR, TAR, TBR)
 │    ├── 0 CGM Features -> Route to Wearable Exp A (10D Standard Model)
 │    ├── All 5 CGM Features -> Route to Wearable Exp B (15D + CGM Model)
 │    └── 1 to 4 CGM Features -> Impute missing CGM features via Train Medians -> Route to Exp B
 └── 0 Wearable Features -> Modality marked UNAVAILABLE
```

- **No Prediction Shortcuts:** CGM missingness masks are never passed as predictors to the ML models.

---

## 7. Fusion / Pathway Selection Strategy (Option A vs. Option B Analysis)

### Option A: Execute Exact Frozen Meta-Stacking Stacker for Every Combination
- *Mechanism:* Run the trained 5-way stacking model for $C+W$, $C+G$, and $C+W+G$.
- *Consequences:* Fusing noisy subclinical wearable/microbiome predictions into Clinical v3 introduces calibration instability for prediabetes (introducing 179 new false errors).

### Option B: Evidence-Based Scientific Routing (RECOMMENDED)
- *Mechanism:* Use Clinical v3 as the primary diagnostic anchor whenever Clinical data is present. When Clinical data is absent, use $W+G$ stacked fusion for remote triage.
- *Scientific Justification:* Clinical v3 captures 99.96% of achievable ROC-AUC. Option B maximizes diagnostic precision while capitalizing on non-clinical multiomics synergy ($W+G$ NAFLD gain $+0.0364$).

---

## 8. API Request & Response Contract Design

### A. Endpoint: `POST /api/v3/predict`

#### Request Payload Schema
```json
{
  "patient_id": "P_TEST_001",
  "clinical_data": {
    "age": 52,
    "gender": 1,
    "height": 175.0,
    "weight": 84.5,
    "bmi": 27.59,
    "waist_circumference": 92.0,
    "systolic_bp": 134.0,
    "diastolic_bp": 86.0,
    "fasting_blood_glucose": 112.5,
    "hba1c": 6.1,
    "triglycerides": 165.0,
    "hdl": 42.0,
    "ldl": 132.0,
    "alt": 38.0,
    "ast": 32.0,
    "family_history_diabetes": 1,
    "family_history_hypertension": 1,
    "family_history_cvd": 0
  },
  "wearable_data": {
    "average_daily_steps": 6200,
    "active_minutes": 35,
    "sedentary_time_minutes": 540,
    "resting_heart_rate": 72,
    "heart_rate_variability_rmssd": 34.2,
    "sleep_duration_hours": 6.5,
    "sleep_efficiency_score": 78.0,
    "autonomic_stress_score": 45.0,
    "activity_energy_expenditure": 420.0,
    "exercise_frequency_days": 2,
    "cgm_average_glucose": 118.4,
    "cgm_glucose_cv": 18.5,
    "cgm_time_in_range": 82.0,
    "cgm_time_above_range": 15.0,
    "cgm_time_below_range": 3.0
  },
  "gut_data": null
}
```

#### Response Payload Schema
```json
{
  "patient_id": "P_TEST_001",
  "pipeline_version": "v3.2.3",
  "routing_metadata": {
    "modalities_supplied": ["clinical", "wearable"],
    "modalities_used": ["clinical", "wearable"],
    "missing_modalities": ["gut"],
    "effective_pathway": "C+W",
    "primary_decision_anchor": "Clinical_v3",
    "cgm_mode": "15D_CGM_ACTIVE",
    "imputed_features": []
  },
  "predictions": {
    "Type2_Diabetes": {
      "calibrated_probability": 0.224,
      "predicted_class": 0,
      "threshold_used": 0.29,
      "risk_level": "Moderate Risk"
    },
    "Prediabetes": {
      "calibrated_probability": 0.685,
      "predicted_class": 1,
      "threshold_used": 0.25,
      "risk_level": "High Risk"
    },
    "Obesity": {
      "calibrated_probability": 0.241,
      "predicted_class": 0,
      "threshold_used": 0.29,
      "risk_level": "Low Risk"
    },
    "Metabolic_Syndrome": {
      "calibrated_probability": 0.512,
      "predicted_class": 1,
      "threshold_used": 0.26,
      "risk_level": "High Risk"
    },
    "NAFLD": {
      "calibrated_probability": 0.384,
      "predicted_class": 1,
      "threshold_used": 0.30,
      "risk_level": "Moderate Risk"
    }
  }
}
```

---

## 9. Explainable AI (XAI) Architecture Design

- **Methodology:** TreeSHAP computed independently for each active v3 expert model ($C_{\text{v3}}, W_{\text{v3}}, G_{\text{v3}}$).
- **Attribution Aggregation:** Feature SHAP values are normalized within each modality and presented per-disease.
- **Strict Causality Decoupling:** SHAP contributions reflect **statistical model feature importance**, NOT biological causality. The UI and API explicitly label SHAP scores as *"Statistical Predictor Contributions."*

---

## 10. RAG + LLM Clinical Explanation Architecture

- **Strict Source of Truth:** Numerical probabilities, risk levels, and binary classifications originate **exclusively** from the ML pipeline.
- **LLM Guardrails:** The LLM prompt contract prohibits altering risk scores, inventing probabilities, or making independent medical diagnoses.
- **RAG Guidance:** Relevant clinical guidelines (ADA T2D, EASL NAFLD, AHA MetS) are retrieved from ChromaDB to contextualize the ML predictions into a clinician report.

---

## 11. Frontend UI Modifications Required

1. **Intake Form Upgrade (`IntakePage.jsx`):** Support 18 Clinical predictors, optional Wearable telemetry, optional CGM toggle (5 features), and 20 Gut taxa relative abundances.
2. **Modality Status Indicator Component (`ModalityBadge.jsx`):** Display active vs missing modalities ($C, W, G, \text{CGM}$) and the active scientific pathway.
3. **Risk Dashboard (`DashboardPage.jsx`):** Render risk gauges for all 5 targets with frozen $t_{\text{opt}}$ threshold indicators.
4. **XAI View (`XAIPage.jsx`):** Display top-5 positive and negative SHAP drivers per disease with explicit attribution disclaimers.

---

## 12. End-to-End Testing Strategy

1. **Unit Tests:** Verify individual feature scaling, median imputation, Isotonic probability calibration, and thresholding.
2. **Integration Tests:** Verify dynamic routing across all 7 modality availability patterns ($C, W, G, C+W, C+G, W+G, C+W+G$) and dual CGM modes (10D vs 15D).
3. **E2E Scenario Tests:** Validate E2E API responses for representative clinical profiles (Low Risk, T2D Positive, NAFLD Positive, Borderline Prediabetes, Malformed Requests).
4. **Reproducibility Verification:** Assert that identical input JSON produces identical float predictions across multiple executions.

---

## 13 & 14. Exact File Classification Inventory

### A. New Files to be Created (`CREATE`)
1. `expert_models/v3_inference_engine.py` — Core v3 loader, feature mapper, scaler, and Isotonic calibrator.
2. `multimodal_data_intake_engine/v3_schema_validator.py` — Schema validator for 18 Clinical, 10/15 Wearable, and 20 Gut features.
3. `fusion_engine/v3_scientific_router.py` — Dynamic modality router implementing Evidence-Based Routing.
4. `web_platform/backend/api/v3_routes.py` — Dedicated v3 REST API endpoints (`/api/v3/predict`, `/api/v3/xai`, `/api/v3/report`).
5. `web_platform/frontend/src/components/ModalityBadge.jsx` — Visual indicator for active modality pathways.
6. `test_v3_e2e_integration.py` — Comprehensive E2E test suite.

### B. Existing Files to be Modified (`MODIFY`)
1. `web_platform/backend/main.py` — Register `v3_routes` blueprint while preserving v1/v2 routes.
2. `web_platform/backend/services/inference_service.py` — Add v3 execution service wrapper.
3. `web_platform/backend/services/xai_service.py` — Add v3 SHAP attribution wrapper.
4. `web_platform/backend/services/rag_service_wrapper.py` — Update prompt contract for v3 disease output format.
5. `web_platform/frontend/src/pages/IntakePage.jsx` — Support v3 clinical, wearable, CGM, and gut input fields.
6. `web_platform/frontend/src/pages/DashboardPage.jsx` — Render v3 disease risk scores and threshold indicators.

### C. Frozen Files — STRICTLY DO NOT TOUCH (`PRESERVE / DO NOT TOUCH`)
1. `data/multimodal_v3/*` — All v3.2.3 dataset CSVs and split manifests.
2. `expert_models/saved_models/clinical_v3/*` — Frozen Clinical v3 payload and metrics.
3. `expert_models/saved_models/wearable_v3/*` — Frozen Wearable v3 payload and metrics.
4. `expert_models/saved_models/gut_v3/*` — Frozen Gut v3 payload and metrics.
5. `expert_models/saved_models/fusion_v3/*` — Frozen Fusion v3 metrics.
6. `expert_models/saved_models/clinical_v1/*`, `clinical_v2/*`, `gut_v1/*`, `gut_v2/*`, `wearable_v1/*` — Legacy research models.
7. `fusion_engine/saved_models/*` — Production v1/v2 fusion models.

---

## 15. Migration Plan from Current Demo System

```
Phase 1: Parallel v3 API Endpoints (/api/v3/predict) created alongside legacy endpoints.
Phase 2: Frontend v3 toggle added in UI settings allowing seamless switching between v1/v2 and v3.
Phase 3: E2E validation against Test set cases.
Phase 4: Default UI route updated to v3 while preserving /v1 and /v2 legacy diagnostic views.
```

---

## 16. Rollback Strategy

If any runtime failure occurs during v3 integration:
1. The backend router falls back to `/api/v2/predict` using `fusion_v2`.
2. Frontend maintains a fallback state handler that renders legacy v2 diagnostic reports if v3 endpoints return non-200 HTTP codes.
3. Zero risk to existing code because all v3 routes are isolated in `v3_routes.py`.

---

## 17. Risks & Limitations

1. **Prediabetes Subclinical Noise:** Wearable and gut features contain noise at subclinical prediabetes boundaries. Clinical v3 anchor routing mitigates this risk.
2. **Gut Sequencing Access:** Stool 16S sequencing is rare in routine care; the system defaults gracefully to $C$ or $C+W$ pathways.
3. **LLM Hallucination Risk:** Guardrails strictly enforce that LLM text generation receives read-only ML probabilities.

---

## 18. Step-by-Step Implementation Order

```
Step 1: Create expert_models/v3_inference_engine.py (Loads C, W, G v3 joblib payloads).
Step 2: Create multimodal_data_intake_engine/v3_schema_validator.py.
Step 3: Create fusion_engine/v3_scientific_router.py (Implements Option B routing).
Step 4: Create web_platform/backend/api/v3_routes.py & update main.py.
Step 5: Create test_v3_e2e_integration.py and verify all test scenarios pass.
Step 6: Update web_platform/frontend/src/pages/IntakePage.jsx & DashboardPage.jsx.
Step 7: Final E2E verification across browser & API.
```

---

### Confirmation
No changes have been made to any source file or dataset. Execution awaits explicit approval.
