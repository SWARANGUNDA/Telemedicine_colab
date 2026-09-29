# TeleMed AI: Active Production Components & Component Authority Matrix

This document provides an explicit, authoritative distinction between the active production implementation (V4 Architecture) and preserved historical assets (V1/V2/V3 Research Phases).

---

## 1. Active vs Historical Component Index

| Domain | Active Production Component (V4) | Preserved Historical Component | Key Reason for Active Status |
|---|---|---|---|
| **Clinical Expert Model** | `ai/models/clinical/clinical_v4_expert_payload.joblib` | `archive/legacy_models/expert_models_saved_models/clinical_v1..v3/` | V4 trained on 100k cohort with CatBoost (ROC-AUC 0.9996). |
| **Wearable CGM Expert Model** | `ai/models/wearable_cgm/wearable_v4_expert_payload.joblib` | `archive/legacy_models/expert_models_saved_models/wearable_v1..v3/` | V4 trained on 15D temporal CGM features (ROC-AUC 0.9961). |
| **Gut Microbiome Expert Model** | `ai/models/gut_microbiome/gut_v4_expert_payload.joblib` | `archive/legacy_models/expert_models_saved_models/gut_v1..v3/` | V4 trained on 20 taxa relative abundance (ROC-AUC 0.9972). |
| **7-Pathway Fusion Router** | `ai/inference/v3_scientific_router.py` | `archive/v3/v3_scientific_router.py` | Authoritative dynamic router handling all 7 modality combinations. |
| **Multimodal Fusion Stacker** | `ai/models/fusion/v4_multimodal_fusion_payload.joblib` | `archive/legacy_models/fusion_engine_saved_models/fusion_v1..v2/` | V4 logistic regression probability stacker across all 7 pathways. |
| **Intake Engine (IMDIE)** | `services/multimodal_intake/engine.py` | `archive/v1/` / `archive/v2/` | 15-stage pipeline supporting PDF, OCR, TXT, CSV, JSON parsing. |
| **Explainable AI (XAI)** | `ai/explainability/unified_xai_engine.py` | `archive/v3/unified_xai_engine.py` | TreeSHAP explainer generating feature attributions and waterfall plots. |
| **Medical RAG Engine** | `services/medical_rag/rag_service.py` | `archive/v3/` | Zero-hallucination grounded RAG with strict 6-level evidence tagging. |
| **Backend REST & WS API** | `app/backend/main.py` | `archive/v3/` | Security-hardened FastAPI application with RBAC and sliding rate limits. |
| **Frontend Web Application** | `app/frontend/src/` | `archive/v1/` | React 18 + Vite SPA with custom vanilla CSS design system (zero Tailwind). |
| **Primary Dataset** | `ai/datasets/final/` (`clinical_v4.csv`, etc.) | `archive/v1/` (20k cohort) | 100,000 patient multimodal synthetic cohort with 70/15/15 split. |
| **Test Regression Suite** | `tests/{unit,integration,security,e2e,ml}/` | `archive/old_tests/` | Unified 16-suite test regression with 142/142 tests passing. |

---

## 2. Machine Learning Architecture: 7-Pathway Dynamic Routing

TeleMed implements an evidence-based clinical late-fusion architecture capable of evaluating patients across any combination of available input modalities:

```
                                  Patient Intake Data
                                           │
                   ┌───────────────────────┼───────────────────────┐
                   ▼                       ▼                       ▼
           Clinical Reports         Wearable / CGM         Gut Microbiome
             (18 Features)           (15 Features)            (20 Taxa)
                   │                       │                       │
                   ▼                       ▼                       ▼
            Clinical Expert         Wearable Expert           Gut Expert
           (CatBoost Payload)      (CatBoost Payload)     (LightGBM Payload)
                   │                       │                       │
                   └───────────────────────┼───────────────────────┘
                                           │
                                           ▼
                             Dynamic Pathway Router
                        (ai/inference/v3_scientific_router.py)
                                           │
         ┌────────────┬────────────┬───────┴───┬────────────┬────────────┐
         ▼            ▼            ▼           ▼            ▼            ▼
     [Pathway 1]  [Pathway 2]  [Pathway 3] [Pathway 4]  [Pathway 5]  [Pathway 6]  [Pathway 7]
       C Only       W Only       G Only       C+W          C+G          W+G         C+W+G
                                                                    (Stacker)    (Stacker)
                                           │
                                           ▼
                                5-Disease Risk Outcomes
                     (T2D, Prediabetes, Obesity, MetSyn, NAFLD)
                                           │
                   ┌───────────────────────┴───────────────────────┐
                   ▼                                               ▼
          Unified TreeSHAP XAI                            Grounded Medical RAG
   (ai/explainability/unified_xai_engine.py)        (services/medical_rag/rag_service.py)
```

### Pathway Definitions:
1. **Pathway 1 (C)**: Clinical Laboratory Anchor (ROC-AUC 0.9996).
2. **Pathway 2 (W)**: Standalone Wearable CGM Biosensor (ROC-AUC 0.9961).
3. **Pathway 3 (G)**: Standalone Gut Microbiome (ROC-AUC 0.9972).
4. **Pathway 4 (C+W)**: Clinical Anchor with Wearable Continuous Telemetry.
5. **Pathway 5 (C+G)**: Clinical Anchor with Microbiome Diversity Profiling.
6. **Pathway 6 (W+G)**: Remote Multiomics Triage Stacker (+0.0364 NAFLD ROC-AUC gain).
7. **Pathway 7 (C+W+G)**: Comprehensive Multimodal Triple-Expert Stacker.

---

## 3. Microservice & Backend Architecture

### `services/multimodal_intake` (IMDIE)
- **Extraction**: `extractor.py` handles PDF (pdfplumber / pypdf), scanned images (Tesseract OCR), TXT, CSV, JSON.
- **Normalization**: `normalizer.py` executes unit conversion (e.g. mg/dL to mmol/L) and physiological bound validation.
- **Scoring**: `quality_scorer.py` evaluates feature completeness, range validity, and noise penalties.

### `services/medical_rag` (Grounded Clinical RAG)
- **Vector Retrieval**: Dense cosine similarity over authoritative medical guidelines (ADA 2024, WHO 2023, AASLD 2023, AHA 2022, ISAPP 2023).
- **Evidence Level Hierarchy**: Enforces strict provenance distinction:
  - `PATIENT_MEASURED`: Raw lab/sensor inputs.
  - `ML_PREDICTION`: Model risk probabilities.
  - `MODEL_XAI`: Feature SHAP attributions.
  - `CLINICAL_GUIDELINE`: Authoritative clinical practice guidelines.
  - `EMERGING_RESEARCH`: Observational multiomics literature.
  - `LLM_EXPLANATION`: Grounded natural language synthesis.
