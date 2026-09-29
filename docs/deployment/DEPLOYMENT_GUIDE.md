# TeleMed AI — Production Deployment Guide

Instructions for building and deploying the TeleMed Web Platform frontend and FastAPI backend server.

---

## 1. Prerequisites
- **Python**: 3.10+
- **Node.js**: 18+ & `npm`
- **Tesseract OCR**: Installed and added to system `PATH` (for PDF OCR parsing)

---

## 2. Backend FastAPI Launch
```bash
cd web_platform/backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 3. Frontend Production Build & Serve
```bash
cd web_platform/frontend
npm install
npm run build
```
Serve the generated `dist/` directory via NGINX or static asset hosting.
