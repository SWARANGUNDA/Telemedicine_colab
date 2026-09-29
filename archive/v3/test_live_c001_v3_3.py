"""
test_live_c001_v3_3.py — Live Endpoint Execution for TEST_C001 on v3.3 Pipeline
"""

import sys, json
sys.path.insert(0, ".")
from fastapi.testclient import TestClient
from web_platform.backend.main import app

client = TestClient(app)

c001_payload = {
    "patient_id": "TEST_C001",
    "clinical_data": {
        "Age": 48,
        "Gender": 1,
        "Height": 170.0,
        "Weight": 87.0,
        "BMI": 30.1,
        "Waist_Circumference": 102.0,
        "Systolic_BP": 142.0,
        "Diastolic_BP": 91.0,
        "Fasting_Blood_Glucose": 132.0,
        "HbA1c": 6.8,
        "LDL": 145.0,
        "HDL": 38.0,
        "Triglycerides": 210.0,
        "ALT": 58.0,
        "AST": 41.0
    }
}

print("=== SENDING TEST_C001 PAYLOAD TO /api/v3/predict ===")
resp = client.post("/api/v3/predict", json=c001_payload)
print(f"Status Code: {resp.status_code}")
data = resp.json()
print("\n=== LIVE V3.3 RESPONSE PAYLOAD ===")
print(json.dumps(data, indent=2))
