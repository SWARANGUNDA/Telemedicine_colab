# TeleMed AI — Backend REST API Reference

## Base URL: `http://localhost:8000/api/v1`

---

## 1. Multimodal Inference Endpoint
### `POST /predict/v3`
Executes hierarchical stacking multimodal inference.
- **Request Body**:
  ```json
  {
    "clinical_features": { "age": 52, "hba1c": 6.8 },
    "wearable_features": { "resting_hr": 74 },
    "gut_features": { "firmicutes_bacteroidetes_ratio": 2.1 }
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "effective_pathway": "C+W+G",
    "overall_quality_score": 85.2,
    "predictions": {
      "type_2_diabetes": { "probability": 0.68, "risk_level": "HIGH" }
    }
  }
  ```

---

## 2. TreeSHAP Explainability Endpoint
### `POST /xai/v3`
Computes TreeSHAP feature attribution values.

---

## 3. Medical RAG Knowledge Base Endpoint
### `POST /rag/query`
Queries ChromaDB vector database for clinical guidelines.
