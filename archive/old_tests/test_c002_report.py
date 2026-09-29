"""
test_c002_report.py — Test Real PDF Report Text Extraction for Sunrise Diagnostic Centre (TEST_C002).
"""

import unittest
from services.multimodal_intake.extractor import extract_key_value_pairs_from_text
from services.multimodal_intake.mapper import map_extracted_features
from services.multimodal_intake.normalizer import normalize_mapped_dict

SUNRISE_REPORT_TEXT = """
SYNTHETIC TEST DATA ONLY - NOT VALID FOR CLINICAL USE Page 1
Sunrise Diagnostic Centre
CLINICAL CHEMISTRY & ANTHROPOMETRY REPORT
Patient ID TEST_C002 Report ID SYN-CLN-0002
Age / Gender 52 years / Male Collection date 2026-07-02
RESULTS
Measurement Result Reference / note
Height 170 cm Recorded
Weight 91 kg Recorded
BMI 31.5 kg/m2 18.5-24.9
Waist circumference 108 cm Recorded
Systolic BP 146 mmHg <120
Diastolic BP 94 mmHg <80
Fasting blood glucose 154 mg/dL 70-99
HbA1c 7.4 % 4.0-5.6
LDL cholesterol 152 mg/dL <100
HDL cholesterol 34 mg/dL 40+
Triglycerides 245 mg/dL <150
ALT 62 U/L 7-56
AST 45 U/L 10-40
Family history: diabetes Yes Reported
Family history: obesity Yes Reported
Family history: hypertension Yes Reported
Family history: NAFLD Yes Reported
Laboratory note: This report is fictional synthetic data created for software testing. It is not a diagnostic result and must not be used for patient care.
"""


class TestC002SunriseReport(unittest.TestCase):

    def test_c002_extraction(self):
        raw = extract_key_value_pairs_from_text(SUNRISE_REPORT_TEXT, source_file="sunrise_c002.pdf")
        mapped = map_extracted_features(raw)
        norm = normalize_mapped_dict(mapped)
        clin = norm.get("CLINICAL", {})

        print("\nExtracted Clinical Dict for TEST_C002:")
        for k, v in clin.items():
            print(f"  {k}: {v}")

        self.assertEqual(clin.get("Patient_ID"), "TEST_C002")
        self.assertEqual(clin.get("Age"), 52.0)
        self.assertEqual(clin.get("Gender"), "Male")
        self.assertEqual(clin.get("Height"), 170.0)
        self.assertEqual(clin.get("Weight"), 91.0)
        self.assertEqual(clin.get("BMI"), 31.5)
        self.assertEqual(clin.get("Waist_Circumference"), 108.0)
        self.assertEqual(clin.get("Systolic_BP"), 146.0)
        self.assertEqual(clin.get("Diastolic_BP"), 94.0)
        self.assertEqual(clin.get("Fasting_Blood_Glucose"), 154.0)
        self.assertEqual(clin.get("HbA1c"), 7.4)
        self.assertEqual(clin.get("LDL"), 152.0)
        self.assertEqual(clin.get("HDL"), 34.0)
        self.assertEqual(clin.get("Triglycerides"), 245.0)
        self.assertEqual(clin.get("ALT"), 62.0)
        self.assertEqual(clin.get("AST"), 45.0)


if __name__ == "__main__":
    unittest.main()
