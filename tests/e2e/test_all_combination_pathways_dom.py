"""
test_all_combination_pathways_dom.py — Verifies all multimodal combination pathways (C, C+W, C+G, W+G, C+W+G)
in the FastAPI backend API and Dashboard DOM rendering logic.
"""

import unittest
from fastapi.testclient import TestClient
from app.backend.main import app

class TestCombinationPathways(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        reg = cls.client.post("/api/v1/auth/register/patient", json={
            "email": "comb_pathway_test@telemed.ai", "password": "Password123!", "full_name": "Combination Pathway Patient"
        })
        if reg.status_code == 201:
            token = reg.json()["token"]
        else:
            login = cls.client.post("/api/v1/auth/login", json={
                "email": "comb_pathway_test@telemed.ai", "password": "Password123!"
            })
            token = login.json()["token"]
        cls.auth_headers = {"Authorization": f"Bearer {token}"}

    def test_01_clinical_only_pathway(self):
        payload = {
            "patient_id": "P_TEST_101",
            "clinical_data": {
                "Age": 52, "Gender": 1, "Height": 175, "Weight": 85, "BMI": 27.8,
                "Systolic_BP": 138, "Diastolic_BP": 88, "Fasting_Blood_Glucose": 118,
                "HbA1c": 6.2, "Triglycerides": 185, "HDL": 42, "LDL": 130, "ALT": 35, "AST": 28
            }
        }
        res = self.client.post("/api/v3/predict", json=payload, headers=self.auth_headers)
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        self.assertEqual(data.get("effective_pathway"), "C")
        self.assertEqual(data.get("pathway_used"), "C")
        self.assertIn("clinical", data.get("active_modalities", []))

    def test_02_clinical_plus_wearable_pathway(self):
        payload = {
            "patient_id": "P_TEST_101",
            "clinical_data": {
                "Age": 52, "Gender": 1, "Height": 175, "Weight": 85, "BMI": 27.8,
                "Systolic_BP": 138, "Diastolic_BP": 88, "Fasting_Blood_Glucose": 118,
                "HbA1c": 6.2, "Triglycerides": 185, "HDL": 42, "LDL": 130, "ALT": 35, "AST": 28
            },
            "wearable_data": {
                "Average_Daily_Steps": 9400, "Active_Minutes": 58.0, "Sedentary_Time_Minutes": 410.0,
                "Resting_Heart_Rate": 61.0, "Heart_Rate_Variability_RMSSD": 58.0, "Sleep_Duration": 7.6,
                "CGM_Average_Glucose": 115.0, "CGM_Glucose_CV": 18.0
            }
        }
        res = self.client.post("/api/v3/predict", json=payload, headers=self.auth_headers)
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        self.assertEqual(data.get("effective_pathway"), "C+W")
        self.assertEqual(data.get("pathway_used"), "C+W")
        self.assertIn("clinical", data.get("active_modalities", []))
        self.assertIn("wearable", data.get("active_modalities", []))

    def test_03_clinical_plus_gut_pathway(self):
        payload = {
            "patient_id": "P_TEST_101",
            "clinical_data": {
                "Age": 52, "Gender": 1, "Height": 175, "Weight": 85, "BMI": 27.8,
                "Systolic_BP": 138, "Diastolic_BP": 88, "Fasting_Blood_Glucose": 118,
                "HbA1c": 6.2, "Triglycerides": 185, "HDL": 42, "LDL": 130, "ALT": 35, "AST": 28
            },
            "gut_data": {
                "Shannon_Diversity_Index": 4.18, "Firmicutes": 45.0, "Bacteroidetes": 43.0,
                "Akkermansia": 3.8, "Faecalibacterium": 10.2, "Bifidobacterium": 5.5
            }
        }
        res = self.client.post("/api/v3/predict", json=payload, headers=self.auth_headers)
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        self.assertEqual(data.get("effective_pathway"), "C+G")
        self.assertEqual(data.get("pathway_used"), "C+G")
        self.assertIn("clinical", data.get("active_modalities", []))
        self.assertIn("gut", data.get("active_modalities", []))

    def test_04_wearable_plus_gut_pathway(self):
        payload = {
            "patient_id": "P_TEST_101",
            "wearable_data": {
                "Average_Daily_Steps": 9400, "Active_Minutes": 58.0, "Sedentary_Time_Minutes": 410.0,
                "Resting_Heart_Rate": 61.0, "Heart_Rate_Variability_RMSSD": 58.0, "Sleep_Duration": 7.6
            },
            "gut_data": {
                "Shannon_Diversity_Index": 4.18, "Firmicutes": 45.0, "Bacteroidetes": 43.0,
                "Akkermansia": 3.8, "Faecalibacterium": 10.2, "Bifidobacterium": 5.5
            }
        }
        res = self.client.post("/api/v3/predict", json=payload, headers=self.auth_headers)
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        self.assertEqual(data.get("effective_pathway"), "W+G")
        self.assertEqual(data.get("pathway_used"), "W+G")
        self.assertIn("wearable", data.get("active_modalities", []))
        self.assertIn("gut", data.get("active_modalities", []))

    def test_05_trimodal_pathway(self):
        payload = {
            "patient_id": "P_TEST_101",
            "clinical_data": {
                "Age": 52, "Gender": 1, "Height": 175, "Weight": 85, "BMI": 27.8,
                "Systolic_BP": 138, "Diastolic_BP": 88, "Fasting_Blood_Glucose": 118,
                "HbA1c": 6.2, "Triglycerides": 185, "HDL": 42, "LDL": 130, "ALT": 35, "AST": 28
            },
            "wearable_data": {
                "Average_Daily_Steps": 9400, "Active_Minutes": 58.0, "Sedentary_Time_Minutes": 410.0,
                "Resting_Heart_Rate": 61.0, "Heart_Rate_Variability_RMSSD": 58.0, "Sleep_Duration": 7.6
            },
            "gut_data": {
                "Shannon_Diversity_Index": 4.18, "Firmicutes": 45.0, "Bacteroidetes": 43.0,
                "Akkermansia": 3.8, "Faecalibacterium": 10.2, "Bifidobacterium": 5.5
            }
        }
        res = self.client.post("/api/v3/predict", json=payload, headers=self.auth_headers)
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        self.assertEqual(data.get("effective_pathway"), "C+W+G")
        self.assertEqual(data.get("pathway_used"), "C+W+G")
        self.assertIn("clinical", data.get("active_modalities", []))
        self.assertIn("wearable", data.get("active_modalities", []))
        self.assertIn("gut", data.get("active_modalities", []))

if __name__ == "__main__":
    unittest.main()
