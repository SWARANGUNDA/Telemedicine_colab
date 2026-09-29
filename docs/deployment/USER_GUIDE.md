# TeleMed AI — Patient User Guide

Welcome to **TeleMed AI Platform**. This guide explains how to submit health records, view risk assessments, explore clinical drivers, and consult with physicians.

---

## 1. Submitting Health Records (Intake Wizard)
1. **Step 1: Upload Documents**: Drag and drop clinical lab reports (PDF/images), wearable sensor data (Fitbit/Apple Health CSVs), or gut microbiome sequencing files (Ayumetrix PDF/JSON).
2. **Step 2: Feature Verification**: Review auto-extracted biomarker values (e.g., `HbA1c`, `Fasting Glucose`, `Firmicutes/Bacteroidetes Ratio`). Edit values if needed.
3. **Step 3: Run Analysis**: Click **Run AI Pipeline** to trigger multimodal inference.

---

## 2. Viewing AI Analysis & Reports
- **Interactive Pipeline**: Track real-time progress through OCR validation, feature normalization, model inference, and TreeSHAP calculation.
- **XAI Explainability**: Inspect top drivers increasing or lowering your risk score.
- **Clinical Report**: View and print your official clinical report for doctor consultation.
