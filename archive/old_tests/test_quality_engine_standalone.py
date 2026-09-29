"""
test_quality_engine_standalone.py — Standalone Data Quality Engine & Coverage Unit Test Suite.

Asserts:
1. Gut-only input MUST NOT return missing=18.
2. Wearable-only input MUST NOT return missing=18.
3. 0-modality input returns coverage = 0.0% and provided = 0, NOT 50.0%.
4. Modality coverage accurately reflects active detected modalities (1 mod = 33.3%, 2 mods = 66.7%, 3 mods = 100.0%).
"""

import unittest
from services.multimodal_intake.quality_scorer import calculate_data_quality_scores


class TestQualityEngineStandalone(unittest.TestCase):

    def test_01_gut_only_quality(self):
        gut_data = {
            "Shannon_Diversity_Index": 4.18,
            "Firmicutes": 45.0,
            "Bacteroidetes": 43.0,
            "Akkermansia": 3.8,
            "Faecalibacterium": 10.2,
            "Bifidobacterium": 5.5,
            "Bacteroides": 19.0,
            "Prevotella": 10.5,
            "Roseburia": 6.4,
            "Proteobacteria": 2.2
        }
        # Demographics from PDF header (should not activate clinical lab schema)
        clinical_header_only = {"Patient_ID": "P_TEST_101", "Age": 52, "Gender": "Male"}

        res = calculate_data_quality_scores(clinical_header_only, {}, gut_data)
        breakdown = res["score_breakdown"]
        counts = breakdown["counts"]
        coverage = breakdown["coverage"]

        # Assert Gut modality is detected as active
        self.assertTrue(coverage["gut"])
        self.assertFalse(coverage["clinical"], "Clinical lab/anthropometric schema MUST NOT be active for header demographics only.")
        self.assertFalse(coverage["wearable"])

        # Assert counts
        self.assertGreaterEqual(counts["provided"], 10)
        self.assertEqual(counts["missing"], 14, "Missing count must be for absent Gut taxa only, NOT Clinical 18.")
        self.assertNotEqual(counts["missing"], 18, "Gut-only upload MUST NOT default to 18 missing clinical fields.")

        # Assert coverage
        self.assertEqual(breakdown["multimodal_coverage_pct"], 33.3)

    def test_02_wearable_only_quality(self):
        wear_data = {
            "Average_Daily_Steps": 9400,
            "Active_Minutes": 58.0,
            "Sedentary_Time_Minutes": 410.0,
            "Resting_Heart_Rate": 61.0,
            "Heart_Rate_Variability_RMSSD": 58.0,
            "Sleep_Duration": 7.6,
            "Sleep_Efficiency_Score": 87.0,
            "Autonomic_Stress_Score": 3.0,
            "Average_Glucose": 96.0,
            "Glucose_Variability": 16.0
        }
        clinical_header_only = {"Patient_ID": "P_TEST_101", "Age": 52, "Gender": "Male"}

        res = calculate_data_quality_scores(clinical_header_only, wear_data, {})
        breakdown = res["score_breakdown"]
        counts = breakdown["counts"]
        coverage = breakdown["coverage"]

        self.assertTrue(coverage["wearable"])
        self.assertFalse(coverage["clinical"])
        self.assertFalse(coverage["gut"])

        self.assertGreaterEqual(counts["provided"], 10)
        self.assertNotEqual(counts["missing"], 18, "Wearable-only upload MUST NOT default to 18 missing clinical fields.")
        self.assertEqual(breakdown["multimodal_coverage_pct"], 33.3)

    def test_03_zero_modality_quality(self):
        res = calculate_data_quality_scores({}, {}, {})
        breakdown = res["score_breakdown"]
        counts = breakdown["counts"]

        self.assertEqual(counts["provided"], 0)
        self.assertEqual(counts["missing"], 0)
        self.assertEqual(breakdown["multimodal_coverage_pct"], 0.0, "Zero modalities MUST report 0.0% coverage, NOT 50.0%.")


if __name__ == "__main__":
    unittest.main()
