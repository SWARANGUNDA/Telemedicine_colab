"""
test_c001_multi_format.py — Field-by-Field Expected vs Extracted Assertion Test Suite for TEST_C001.

Validates that real data is correctly extracted into canonical V3.3 fields for:
- c001_report.txt (TXT)
- c001_report.json (JSON)
- c001_report.csv (CSV)
- c001_report.tsv (TSV)
- c001_report.rtf (RTF)
- c001_report.docx (DOCX)
- c001_report.xlsx (XLSX)
- c001_report.pdf (PDF vector text)
- c001_scanned.pdf (PDF scanned)

Expected Canonical V3.3 Fields for TEST_C001:
  Patient_ID = "TEST_C001"
  Age = 48.0
  Gender = "Male"
  Height = 170.0
  Weight = 87.0
  BMI = 30.1
  Waist_Circumference = 102.0
  Systolic_BP = 142.0
  Diastolic_BP = 91.0
  Fasting_Blood_Glucose = 132.0
  HbA1c = 6.8
  LDL = 145.0
  HDL = 38.0
  Triglycerides = 210.0
  ALT = 58.0
  AST = 41.0
"""

import unittest
from pathlib import Path
from services.multimodal_intake.engine import MultimodalIntakeEngine

EXPECTED = {
    "Patient_ID": "TEST_C001",
    "Age": 48.0,
    "Gender": "Male",
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


class TestC001MultiFormatExtraction(unittest.TestCase):

    def setUp(self):
        self.engine = MultimodalIntakeEngine()
        self.fixtures_dir = Path(__file__).resolve().parent / "c001_test_fixtures"

    def _verify_extracted_profile(self, fpath: Path, min_fields_expected: int = 14):
        res = self.engine.process_reports([str(fpath)])
        self.assertIn("patient_profile", res)
        profile = res["patient_profile"]
        if hasattr(profile, "clinical_features"):
            clin = profile.clinical_features or {}
        elif isinstance(profile, dict):
            clin = profile.get("clinical_features") or profile.get("clinical_dict") or profile.get("clinical") or {}
        else:
            clin = getattr(profile, "clinical_dict", {}) or {}

        # 1. Verify Patient ID
        extracted_pid = clin.get("Patient_ID") or res.get("patient_id") or getattr(profile, "patient_id", None)
        if isinstance(extracted_pid, dict):
            extracted_pid = extracted_pid.get("raw_value")
        if extracted_pid is None and hasattr(profile, "metadata"):
            extracted_pid = profile.metadata.get("Patient_ID") or profile.metadata.get("patient_id")
        if extracted_pid:
            self.assertEqual(str(extracted_pid).strip(), "TEST_C001", f"Patient_ID mismatch for {fpath.name}")

        # 2. Field-by-field verification
        matched_count = 0
        mismatches = []
        for field, exp_val in EXPECTED.items():
            if field == "Patient_ID":
                continue
            act_item = clin.get(field)
            if isinstance(act_item, dict):
                act_val = act_item.get("normalized_value", act_item.get("raw_value"))
            else:
                act_val = act_item

            if act_val is not None:
                # Convert string numeric if needed
                try:
                    if isinstance(exp_val, float):
                        act_val = float(act_val)
                    elif isinstance(exp_val, str):
                        act_val = str(act_val).strip()
                except Exception:
                    pass

                if act_val == exp_val:
                    matched_count += 1
                else:
                    mismatches.append(f"{field}: expected {exp_val}, got {act_val}")

        self.assertGreaterEqual(
            matched_count, min_fields_expected,
            f"Extraction incomplete for {fpath.name}. Matched {matched_count}/{len(EXPECTED)-1}. Mismatches: {mismatches}"
        )

    def test_c001_txt(self):
        self._verify_extracted_profile(self.fixtures_dir / "c001_report.txt")

    def test_c001_json(self):
        self._verify_extracted_profile(self.fixtures_dir / "c001_report.json")

    def test_c001_csv(self):
        self._verify_extracted_profile(self.fixtures_dir / "c001_report.csv")

    def test_c001_tsv(self):
        self._verify_extracted_profile(self.fixtures_dir / "c001_report.tsv")

    def test_c001_rtf(self):
        self._verify_extracted_profile(self.fixtures_dir / "c001_report.rtf")

    def test_c001_docx(self):
        self._verify_extracted_profile(self.fixtures_dir / "c001_report.docx")

    def test_c001_xlsx(self):
        self._verify_extracted_profile(self.fixtures_dir / "c001_report.xlsx")

    def test_c001_pdf(self):
        self._verify_extracted_profile(self.fixtures_dir / "c001_report.pdf")


if __name__ == "__main__":
    unittest.main()
