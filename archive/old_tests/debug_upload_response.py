import requests
from pathlib import Path
import json

base_url = "http://127.0.0.1:8000/api/v1"

p_gut = Path("TeleMed_5_Patient_Sets_15_PDFs/P_TEST_101_gut_microbiome.pdf")
p_wear = Path("TeleMed_5_Patient_Sets_15_PDFs/P_TEST_101_wearable.pdf")

print("--- TESTING GUT PDF UPLOAD ---")
with open(p_gut, "rb") as f:
    res_gut = requests.post(f"{base_url}/intake/upload", files=[("files", (p_gut.name, f, "application/pdf"))])
print("Gut upload status:", res_gut.status_code)
gut_json = res_gut.json()
print("Gut JSON keys:", list(gut_json.keys()))
print("Gut data_quality_scores:", json.dumps(gut_json.get("data_quality_scores"), indent=2))
print("Gut extracted_features:", json.dumps(gut_json.get("extracted_features"), indent=2))

print("\n--- TESTING WEARABLE PDF UPLOAD ---")
with open(p_wear, "rb") as f:
    res_wear = requests.post(f"{base_url}/intake/upload", files=[("files", (p_wear.name, f, "application/pdf"))])
print("Wear upload status:", res_wear.status_code)
wear_json = res_wear.json()
print("Wear data_quality_scores:", json.dumps(wear_json.get("data_quality_scores"), indent=2))
print("Wear extracted_features:", json.dumps(wear_json.get("extracted_features"), indent=2))
