"""
verify_http_live.py — Sends live HTTP POST to http://127.0.0.1:8000/api/v3/predict
"""

import urllib.request
import json

url = "http://127.0.0.1:8000/api/v3/predict"
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

req = urllib.request.Request(
    url,
    data=json.dumps(c001_payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

with urllib.request.urlopen(req) as response:
    status = response.status
    body = json.loads(response.read().decode('utf-8'))
    print(f"HTTP Status: {status}")
    print("=== LIVE V3.3 RESPONSE FROM PORT 8000 ===")
    print(json.dumps(body, indent=2))
