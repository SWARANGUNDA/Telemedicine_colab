# TeleMed AI Platform — StarUML (.mdj) Complete Architecture Package

This directory contains the official, implementation-accurate StarUML (`.mdj`) documentation package and architecture visualizations for the **TeleMed AI Platform (Frozen V4 Architecture)**.

## Project Details
- **Project Version:** V4.0 (Frozen Production Release)
- **Format:** Native StarUML JSON Project Files (`.mdj`)
- **Date Generated:** August 12, 2026
- **Architecture Integrity:** 100% verified against current Python/FastAPI backend, React frontend, SQLAlchemy ORM schema, and frozen V4 ML artifacts.

---

## Master StarUML Project File

Open [`telemed_v4_architecture.mdj`](telemed_v4_architecture.mdj) in StarUML to view the **entire consolidated system architecture**, packages, classes, use cases, components, sequence diagrams, and ER models in a single StarUML workspace!

---

## Index of StarUML Diagram Project Files (.mdj)

| File | Diagram Type | Format | Description |
| :--- | :--- | :---: | :--- |
| [`telemed_v4_architecture.mdj`](telemed_v4_architecture.mdj) | **Master System Project** | StarUML | Complete consolidated system architecture & all diagrams in one project. |
| [`01_use_case_diagram.mdj`](01_use_case_diagram.mdj) | Use-Case Diagram | StarUML | Patient, Doctor, and Administrator system interactions. |
| [`02_system_component_diagram.mdj`](02_system_component_diagram.mdj) | System Component Diagram | StarUML | High-level system architecture (Frontend, Backend, ML, DB, Redis, Celery, Prometheus). |
| [`03_backend_class_diagram.mdj`](03_backend_class_diagram.mdj) | Backend Class Diagram | StarUML | FastAPI routes, controllers, services, repositories, and ORM entity models. |
| [`04_intake_preprocessing_class_diagram.mdj`](04_intake_preprocessing_class_diagram.mdj) | Intake Class Diagram | StarUML | Intake engine, schema validation, feature normalizer (18 C, 15 W, 49 G features). |
| [`05_ml_pipeline_component_diagram.mdj`](05_ml_pipeline_component_diagram.mdj) | ML Pipeline Diagram | StarUML | 3 single-modality experts, 7 pathway combinations, Stacking Fusion, XAI & RAG. |
| [`06_deployment_diagram.mdj`](06_deployment_diagram.mdj) | Deployment Diagram | StarUML | Docker containerization, ports, services (FastAPI, Nginx, PostgreSQL, Redis, Celery). |
| [`07_patient_assessment_sequence.mdj`](07_patient_assessment_sequence.mdj) | Sequence Diagram | StarUML | Complete patient assessment flow from upload to report & persistence. |
| [`08_multimodal_prediction_sequence.mdj`](08_multimodal_prediction_sequence.mdj) | Sequence Diagram | StarUML | Dynamic modality execution and 7-pathway multimodal prediction flow. |
| [`09_xai_sequence.mdj`](09_xai_sequence.mdj) | Sequence Diagram | StarUML | TreeSHAP explainable AI attribution calculation and caching flow. |
| [`10_report_generation_sequence.mdj`](10_report_generation_sequence.mdj) | Sequence Diagram | StarUML | Medical RAG evidence retrieval and ReportLab PDF document export. |
| [`11_database_er_diagram.mdj`](11_database_er_diagram.mdj) | ER Diagram | StarUML | Database entity relationship diagram (PostgreSQL / SQLAlchemy ORM). |
| [`12_frontend_component_diagram.mdj`](12_frontend_component_diagram.mdj) | Frontend Component Diagram | StarUML | React SPA routing, page containers, contexts, components, API client. |
| [`13_auth_rbac_sequence.mdj`](13_auth_rbac_sequence.mdj) | Sequence Diagram | StarUML | JWT authentication and Role-Based Access Control (RBAC) authorization. |
| [`14_end_to_end_activity.mmd`](14_end_to_end_activity.mmd) | Activity Diagram | Mermaid | End-to-end platform workflow flowchart. |
| [`15_data_flow_diagram.mmd`](15_data_flow_diagram.mmd) | Data Flow Diagram | Mermaid | DFD Level 0 & Level 1 data flows across subsystems and stores. |
| [`16_v4_model_architecture.mdj`](16_v4_model_architecture.mdj) | Model Architecture | StarUML | Dedicated V4 multi-expert model ecosystem, feature schemas & 5 disease targets. |

---

## How to Open StarUML Files (`.mdj`)

1. Download and launch **StarUML** (v5.0+ or latest).
2. Go to **File -> Open...** (`Ctrl+O` or `Cmd+O`).
3. Select `telemed_v4_architecture.mdj` or any individual `.mdj` file from `docs/uml/`.
4. Browse the Model Explorer tree on the right panel to view models, elements, and diagrams.
5. To export diagrams as high-resolution images: **File -> Export Diagram As -> PNG / SVG / JPEG**.

---

## How to Render Mermaid Diagrams (`.mmd`)

Mermaid diagrams can be viewed directly in GitHub markdown or rendered via Mermaid CLI:

```bash
# Using Mermaid CLI (mmdc)
npx -y @mermaid-js/mermaid-cli -i docs/uml/14_end_to_end_activity.mmd -o docs/uml/14_end_to_end_activity.png
npx -y @mermaid-js/mermaid-cli -i docs/uml/15_data_flow_diagram.mmd -o docs/uml/15_data_flow_diagram.png
```
