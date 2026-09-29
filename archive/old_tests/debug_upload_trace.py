"""
debug_upload_trace.py — Trace real PDF uploads step-by-step through API response structure.
"""

from pathlib import Path
from fastapi.testclient import TestClient
from web_platform.backend.main import app

client = TestClient(app)

# 1. Login patient
login = client.post("/api/v1/auth/login", json={"email": "comb_pathway_test@telemed.ai", "password": "Password123!"})
if login.status_code != 200:
    reg = client.post("/api/v1/auth/register/patient", json={
        "email": "comb_pathway_test@telemed.ai", "password": "Password123!", "full_name": "Trace Patient"
    })
    token = reg.json()["token"]
else:
    token = login.json()["token"]

headers = {"Authorization": f"Bearer {token}"}

gut_pdf_path = Path("TeleMed_5_Patient_Sets_15_PDFs/P_TEST_101_gut_microbiome.pdf")
wear_pdf_path = Path("TeleMed_5_Patient_Sets_15_PDFs/P_TEST_101_wearable.pdf")

print("\n--- 1. UPLOADING GUT PDF ONLY ---")
with open(gut_pdf_path, "rb") as f:
    res = client.post("/api/v1/intake/upload", files=[("files", (gut_pdf_path.name, f, "application/pdf"))], headers=headers)

print("Status Code:", res.status_code)
gut_json = res.json()
print("Top-level Keys in /upload Response:", list(gut_json.keys()))
print("extracted_features keys:", list(gut_json.get("extracted_features", {}).keys()))
print("extracted_features.clinical:", gut_json.get("extracted_features", {}).get("clinical"))
print("extracted_features.wearable:", gut_json.get("extracted_features", {}).get("wearable"))
print("extracted_features.gut:", gut_json.get("extracted_features", {}).get("gut"))
print("data_quality_scores:", gut_json.get("data_quality_scores"))

print("\n--- 2. UPLOADING WEARABLE PDF ONLY ---")
with open(wear_pdf_path, "rb") as f:
    res_w = client.post("/api/v1/intake/upload", files=[("files", (wear_pdf_path.name, f, "application/pdf"))], headers=headers)

print("Status Code:", res_w.status_code)
wear_json = res_w.json()
print("Top-level Keys in /upload Response:", list(wear_json.keys()))
print("extracted_features keys:", list(wear_json.get("extracted_features", {}).keys()))
print("extracted_features.clinical:", wear_json.get("extracted_features", {}).get("clinical"))
print("extracted_features.wearable:", wear_json.get("extracted_features", {}).get("wearable"))
print("extracted_features.gut:", wear_json.get("extracted_features", {}).get("gut"))
print("data_quality_scores:", wear_json.get("data_quality_scores"))
