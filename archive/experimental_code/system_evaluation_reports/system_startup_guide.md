# System Startup & Deployment Guide

Quick start guide for running the Telemedicine Web Platform backend and frontend locally.

---

## 📋 PREREQUISITES
- Python 3.10+
- Node.js 18+ & npm

---

## 🚀 1. START FASTAPI BACKEND SERVER

Open a terminal in the root workspace directory (`TeleMed`):

```bash
# Start FastAPI backend server on http://localhost:8000
python -m uvicorn web_platform.backend.main:app --reload --port 8000
```

Verify backend health status:
[http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 🎨 2. START REACT + VITE FRONTEND SPA

Open a second terminal in the `web_platform/frontend` directory:

```bash
# Navigate to frontend folder
cd web_platform/frontend

# Install dependencies (first time only)
npm install

# Start Vite development server
npm run dev
```

Open the web platform in your browser:
[http://localhost:5173](http://localhost:5173)

---

## 🧪 3. RUN AUTOMATED TEST SUITES

Run backend & pipeline integration test suites:

```bash
# Phase 6 & 7 Web API Integration Tests
python -m unittest web_platform/test_phase6.py

# Phase 7 Master Evaluation & Latency Benchmarks
python -m system_evaluation.run_phase7_evaluation
```
