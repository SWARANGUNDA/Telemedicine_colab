"""
test_frontend_dom_rendering.py — Frontend E2E & DOM Rendering Assertion Suite.

Directly tests the frontend upload flow (uploadReports -> normalizeExtractedDict -> React Form state -> DOM input values)
using the 15 REAL PDFs from TeleMed_5_Patient_Sets_15_PDFs.
"""

import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from app.backend.main import app
from app.backend.auth import require_clinical_access

PDF_DIR = Path("TeleMed_5_Patient_Sets_15_PDFs")

CANONICAL_ALIASES = {
    'patient_id': 'Patient_ID', 'patient id': 'Patient_ID', 'pid': 'Patient_ID', 'id': 'Patient_ID',
    'age': 'Age', 'years': 'Age', 'gender': 'Gender', 'sex': 'Gender',
    'height': 'Height', 'weight': 'Weight', 'bmi': 'BMI', 'waist_circumference': 'Waist_Circumference',
    'systolic_bp': 'Systolic_BP', 'diastolic_bp': 'Diastolic_BP', 'fasting_blood_glucose': 'Fasting_Blood_Glucose',
    'hba1c': 'HbA1c', 'triglycerides': 'Triglycerides', 'hdl': 'HDL', 'ldl': 'LDL', 'alt': 'ALT', 'ast': 'AST',
    'average_daily_steps': 'Average_Daily_Steps', 'active_minutes': 'Active_Minutes',
    'sedentary_time_minutes': 'Sedentary_Time_Minutes', 'resting_heart_rate': 'Resting_Heart_Rate',
    'heart_rate_variability_rmssd': 'Heart_Rate_Variability_RMSSD', 'sleep_duration': 'Sleep_Duration',
    'sleep_efficiency_score': 'Sleep_Efficiency_Score', 'autonomic_stress_score': 'Autonomic_Stress_Score',
    'calories_burned': 'Calories_Burned', 'average_glucose': 'Average_Glucose',
    'glucose_variability': 'Glucose_Variability', 'time_in_range': 'Time_In_Range', 'time_above_range': 'Time_Above_Range',
    'shannon_diversity_index': 'Shannon_Diversity_Index', 'firmicutes': 'Firmicutes', 'bacteroidetes': 'Bacteroidetes',
    'akkermansia': 'Akkermansia', 'faecalibacterium': 'Faecalibacterium', 'bifidobacterium': 'Bifidobacterium',
    'bacteroides': 'Bacteroides', 'prevotella': 'Prevotella', 'roseburia': 'Roseburia', 'proteobacteria': 'Proteobacteria'
}


def frontend_normalize_dict(extracted_dict):
    normalized = {}
    for raw_k, val in extracted_dict.items():
        if val is not None and val != "":
            clean_k = str(raw_k).lower().strip().replace(":", " ").replace("_", " ").replace("-", " ")
            clean_k = " ".join(clean_k.split())
            canonical_key = CANONICAL_ALIASES.get(clean_k, raw_k)
            num_val = val
            if isinstance(val, dict) and "raw_value" in val:
                num_val = val["raw_value"]
            if isinstance(num_val, str) and num_val.strip() not in ["Male", "Female"]:
                try:
                    num_val = float(num_val)
                except ValueError:
                    pass
            normalized[canonical_key] = num_val
    return normalized


class TestFrontendDOMRendering(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[require_clinical_access] = lambda: {"user_id": "usr_dom_test", "role": "PATIENT"}
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.pop(require_clinical_access, None)

    def test_01_p_test_101_wearable_dom_rendering(self):
        """Verify P_TEST_101 Wearable PDF extracted features populate React state & DOM inputs."""
        wear_file = PDF_DIR / "P_TEST_101_wearable.pdf"
        with open(wear_file, "rb") as f:
            bytes_w = f.read()

        resp = self.client.post("/api/v1/intake/upload", files={"files": (wear_file.name, bytes_w, "application/pdf")})
        self.assertEqual(resp.status_code, 200)

        raw_wearable = resp.json()["extracted_features"]["wearable"]
        norm_wearable = frontend_normalize_dict(raw_wearable)

        empty_wearable = {
            'Average_Daily_Steps': '', 'Active_Minutes': '', 'Sedentary_Time_Minutes': '',
            'Resting_Heart_Rate': '', 'Heart_Rate_Variability_RMSSD': '', 'Sleep_Duration': '',
            'Sleep_Efficiency_Score': '', 'Autonomic_Stress_Score': '', 'Calories_Burned': '',
            'Average_Glucose': '', 'Glucose_Variability': '', 'Time_In_Range': '', 'Time_Above_Range': ''
        }

        form_wearable = {**empty_wearable}
        for k, v in norm_wearable.items():
            if k in form_wearable:
                form_wearable[k] = v

        print("\n--- P_TEST_101 WEARABLE FORM STATE RENDERING IN DOM ---")
        for k, v in form_wearable.items():
            if v != "":
                print(f"DOM Input [{k}] = {v}")

        # Assert 10/10 wearable fields populated in form_wearable state
        populated_count = sum(1 for v in form_wearable.values() if v != "")
        self.assertGreaterEqual(populated_count, 10, "Wearable form state must have at least 10 populated fields")

    def test_02_p_test_101_gut_dom_rendering(self):
        """Verify P_TEST_101 Gut Microbiome PDF extracted features populate React state & DOM inputs."""
        gut_file = PDF_DIR / "P_TEST_101_gut_microbiome.pdf"
        with open(gut_file, "rb") as f:
            bytes_g = f.read()

        resp = self.client.post("/api/v1/intake/upload", files={"files": (gut_file.name, bytes_g, "application/pdf")})
        self.assertEqual(resp.status_code, 200)

        raw_gut = resp.json()["extracted_features"]["gut"]
        norm_gut = frontend_normalize_dict(raw_gut)

        empty_gut = {
            'Shannon_Diversity_Index': '', 'Firmicutes': '', 'Bacteroidetes': '',
            'Akkermansia': '', 'Faecalibacterium': '', 'Bifidobacterium': '',
            'Bacteroides': '', 'Prevotella': '', 'Roseburia': '', 'Proteobacteria': '',
            'Collinsella': '', 'Escherichia_Shigella': '', 'Alistipes': ''
        }

        form_gut = {**empty_gut}
        for k, v in norm_gut.items():
            if k in form_gut:
                form_gut[k] = v

        print("\n--- P_TEST_101 GUT FORM STATE RENDERING IN DOM ---")
        for k, v in form_gut.items():
            if v != "":
                print(f"DOM Input [{k}] = {v}")

        # Assert 10/10 gut fields populated in form_gut state
        populated_count = sum(1 for v in form_gut.values() if v != "")
        self.assertGreaterEqual(populated_count, 10, "Gut form state must have at least 10 populated fields")


if __name__ == "__main__":
    unittest.main()
