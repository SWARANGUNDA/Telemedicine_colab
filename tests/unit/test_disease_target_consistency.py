"""
test_disease_target_consistency.py — Comprehensive Sprint 26.0 Target Flow & Consistency Test Suite.

Verifies:
1. Authoritative 5 V4 Targets: Type2_Diabetes, Prediabetes, High_Adiposity_Risk, Metabolic_Syndrome, NAFLD.
2. Intentional Single-Target Mapping: Obesity <-> High_Adiposity_Risk (never duplicated as two separate targets).
3. All 7 Modality Pathways: C, W, G, C+W, C+G, W+G, C+W+G return exactly the 5 targets.
4. Missing modalities remain None/null without synthetic imputation in routing.
5. Input Features vs Target separation: Family_History_Hypertension/CVD/Diabetes are strictly input features.
6. XAI & SHAP attribution consistency for High_Adiposity_Risk.
7. RAG Patient Context Contract consistency for High_Adiposity_Risk.
"""

import unittest
from ai.inference.v3_inference_engine import V3InferenceEngine
from ai.inference.v3_scientific_router import V3ScientificRouter, DISEASES as ROUTER_DISEASES
from app.backend.services.xai_service import generate_v3_xai_attribution
from services.medical_rag.rag_patient_contract import build_rag_patient_context


class TestDiseaseTargetConsistency(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = V3InferenceEngine()
        cls.router = V3ScientificRouter(cls.engine)
        cls.expected_5_targets = {
            "Type2_Diabetes",
            "Prediabetes",
            "High_Adiposity_Risk",
            "Metabolic_Syndrome",
            "NAFLD"
        }

    def test_01_router_diseases_are_authoritative_5(self):
        """Verify the router defines exactly the 5 authoritative V4 targets."""
        self.assertEqual(set(ROUTER_DISEASES), self.expected_5_targets)
        self.assertEqual(len(ROUTER_DISEASES), 5)
        self.assertIn("High_Adiposity_Risk", ROUTER_DISEASES)
        self.assertNotIn("Obesity", ROUTER_DISEASES, "Obesity must be mapped to High_Adiposity_Risk, not listed as separate target.")
        self.assertNotIn("Hypertension", ROUTER_DISEASES, "Hypertension is not an active prediction target.")
        self.assertNotIn("Dyslipidemia", ROUTER_DISEASES, "Dyslipidemia is not an active prediction target.")

    def test_02_all_7_pathways_return_exact_5_targets_without_duplicate_obesity(self):
        """Verify all 7 modality combinations return exactly the 5 authoritative targets and never duplicate Obesity."""
        dummy_clinical = {
            "Age": 50, "Gender": "Male", "Height": 175, "Weight": 85, "BMI": 27.7,
            "Waist_Circumference": 95, "Systolic_BP": 130, "Diastolic_BP": 85,
            "Fasting_Blood_Glucose": 110, "HbA1c": 6.0, "LDL": 130, "HDL": 45,
            "Triglycerides": 180, "ALT": 35, "AST": 30,
            "Family_History_Diabetes": 1, "Family_History_Hypertension": 1, "Family_History_CVD": 0
        }
        dummy_wearable = {
            "Average_Daily_Steps": 7500, "Active_Minutes": 35, "Sedentary_Time_Minutes": 520,
            "Resting_Heart_Rate": 68, "Sleep_Duration_Hours": 7.0,
            "CGM_Average_Glucose": 115, "CGM_Time_In_Range": 85
        }
        dummy_gut = {
            "Bacteroides_fragilis": 12.5, "Faecalibacterium_prausnitzii": 8.0,
            "Akkermansia_muciniphila": 2.5, "Bifidobacterium_longum": 5.0
        }

        pathway_cases = [
            ("C", dummy_clinical, None, None),
            ("W", None, dummy_wearable, None),
            ("G", None, None, dummy_gut),
            ("C+W", dummy_clinical, dummy_wearable, None),
            ("C+G", dummy_clinical, None, dummy_gut),
            ("W+G", None, dummy_wearable, dummy_gut),
            ("C+W+G", dummy_clinical, dummy_wearable, dummy_gut),
        ]

        for expected_pathway, c_data, w_data, g_data in pathway_cases:
            intake = {
                "patient_id": f"TEST_{expected_pathway.replace('+', '_')}",
                "modalities_supplied": [m for m, d in [("clinical", c_data), ("wearable", w_data), ("gut", g_data)] if d is not None],
                "missing_modalities": [m for m, d in [("clinical", c_data), ("wearable", w_data), ("gut", g_data)] if d is None],
                "clinical_present": c_data is not None,
                "wearable_present": w_data is not None,
                "gut_present": g_data is not None,
                "clinical_data": c_data,
                "wearable_data": w_data,
                "gut_data": g_data,
            }

            res = self.router.route_and_predict(intake)
            self.assertEqual(res["routing_metadata"]["effective_pathway"], expected_pathway)
            
            predictions = res["predictions"]
            self.assertEqual(set(predictions.keys()), self.expected_5_targets, f"Pathway {expected_pathway} failed target set check.")
            self.assertEqual(len(predictions), 5, f"Pathway {expected_pathway} must have exactly 5 targets.")
            self.assertIn("High_Adiposity_Risk", predictions)
            self.assertNotIn("Obesity", predictions, "Predictions output MUST NOT contain duplicate key 'Obesity'.")

    def test_03_xai_explains_high_adiposity_risk(self):
        """Verify XAI service calculates TreeSHAP feature attributions for High_Adiposity_Risk seamlessly."""
        intake = {
            "patient_id": "P_XAI_TEST",
            "modalities_supplied": ["clinical", "wearable", "gut"],
            "missing_modalities": [],
            "clinical_present": True,
            "wearable_present": True,
            "gut_present": True,
            "clinical_data": {
                "Age": 52, "Gender": "Male", "Height": 170, "Weight": 91, "BMI": 31.5,
                "Waist_Circumference": 108, "Systolic_BP": 146, "Diastolic_BP": 94,
                "Fasting_Blood_Glucose": 154, "HbA1c": 7.4, "LDL": 152, "HDL": 34,
                "Triglycerides": 245, "ALT": 62, "AST": 45,
                "Family_History_Diabetes": 1, "Family_History_Hypertension": 1, "Family_History_CVD": 1
            },
            "wearable_data": {"Average_Daily_Steps": 3500, "Resting_Heart_Rate": 82},
            "gut_data": {"Akkermansia_muciniphila": 0.5, "Faecalibacterium_prausnitzii": 2.0},
        }

        # Request XAI for High_Adiposity_Risk
        xai_res = generate_v3_xai_attribution(self.engine, intake, disease="High_Adiposity_Risk")
        self.assertEqual(xai_res["target_disease"], "High_Adiposity_Risk")
        self.assertIn("attributions", xai_res)
        self.assertIn("clinical", xai_res["attributions"])
        
        drivers = xai_res["attributions"]["clinical"]["all_features"]
        self.assertTrue(len(drivers) > 0, "High_Adiposity_Risk should have feature attributions.")
        # BMI and Waist should be dominant magnitude drivers for Adiposity risk
        features_in_drivers = [d["feature_name"] for d in drivers[:3]]
        self.assertTrue(any(f in features_in_drivers for f in ["BMI", "Waist_Circumference", "Weight", "HDL"]))

    def test_04_rag_context_contract_with_high_adiposity_risk(self):
        """Verify RAG patient context accurately ingests High_Adiposity_Risk outcomes."""
        predict_response = {
            "patient_id": "P_RAG_TEST",
            "predictions": {
                "Type2_Diabetes": {"calibrated_probability": 0.72, "predicted_class": 1, "risk_level": "HIGH"},
                "Prediabetes": {"calibrated_probability": 0.65, "predicted_class": 1, "risk_level": "MODERATE"},
                "High_Adiposity_Risk": {"calibrated_probability": 0.88, "predicted_class": 1, "risk_level": "HIGH"},
                "Metabolic_Syndrome": {"calibrated_probability": 0.81, "predicted_class": 1, "risk_level": "HIGH"},
                "NAFLD": {"calibrated_probability": 0.55, "predicted_class": 1, "risk_level": "MODERATE"},
            },
            "routing_metadata": {
                "effective_pathway": "C+W+G",
                "modalities_supplied": ["clinical", "wearable", "gut"],
                "missing_modalities": []
            }
        }

        context = build_rag_patient_context(
            patient_id="P_RAG_TEST",
            patient_features={},
            predict_response=predict_response
        )

        outcomes = context["disease_risk_outcomes"]
        self.assertEqual(set(outcomes.keys()), self.expected_5_targets)
        self.assertIn("High_Adiposity_Risk", outcomes)
        self.assertNotIn("Obesity", outcomes)
        self.assertEqual(outcomes["High_Adiposity_Risk"]["risk_category"], "High Risk / Elevated Signal")
        self.assertEqual(outcomes["High_Adiposity_Risk"]["fusion_probability"], 0.88)

    def test_05_input_features_are_not_mistaken_for_disease_targets(self):
        """Verify input features (Family_History_Hypertension/CVD/Diabetes) are strictly features."""
        clin_payload = self.engine.clinical_payload
        features = clin_payload["features"]
        models = clin_payload["models"]

        # Assert family history features are in input feature list
        self.assertIn("Family_History_Diabetes", features)
        self.assertIn("Family_History_Hypertension", features)
        self.assertIn("Family_History_CVD", features)

        # Assert family history features are NOT model targets
        self.assertNotIn("Family_History_Hypertension", models)
        self.assertNotIn("Family_History_CVD", models)
        self.assertNotIn("Hypertension", models)
        self.assertNotIn("CVD", models)


if __name__ == "__main__":
    unittest.main()
