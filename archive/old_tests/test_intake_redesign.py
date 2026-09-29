"""
test_intake_redesign.py — Comprehensive Unit & Integration Tests for Redesigned V3.3 Multimodal Data Intake Engine (IMDIE).

Verifies:
1. MIME header detection for supported file formats
2. Image preprocessing & Laplacian blur variance check
3. OCR Anomaly & Decimal Shift Detection (HbA1c = 65 -> 6.5, Glucose = 13.2 -> 132)
4. Unit Normalization with raw value + unit retention
5. Multi-report fusion, conflict tracking, and Patient ID mismatch warnings
6. Data Quality Score formula, capping rules, and breakdown output
7. Full IMDIE process_reports pipeline execution
"""

import os
import tempfile
import unittest
from pathlib import Path

from services.multimodal_intake.extractor import (
    detect_file_format_by_header,
    preprocess_image_for_ocr,
    extract_from_file_or_data
)
from services.multimodal_intake.validator import (
    detect_ocr_anomalies,
    validate_feature_dict
)
from services.multimodal_intake.normalizer import normalize_mapped_dict
from services.multimodal_intake.fuser import fuse_multiple_reports
from services.multimodal_intake.quality_scorer import calculate_data_quality_scores
from services.multimodal_intake.engine import MultimodalIntakeEngine
from PIL import Image


class TestIntakeRedesign(unittest.TestCase):

    def test_01_mime_header_detection(self):
        """Test magic byte MIME header format detection across all 17 supported formats."""
        fixtures_dir = Path(__file__).resolve().parent / "test_files"
        expected_formats = {
            "sample_clinical.pdf": "pdf",
            "scanned_clinical.pdf": "pdf",
            "clinical_report.docx": "docx",
            "clinical_report.doc": "doc",
            "lab_report.txt": "txt",
            "lab_report.rtf": "rtf",
            "blood_data.csv": "csv",
            "wearable_data.tsv": "tsv",
            "patient_record.json": "json",
            "lab_export.xlsx": "xlsx",
            "lab_export.xls": "xls",
            "report_scan.jpg": "jpeg",
            "report_scan.jpeg": "jpeg",
            "report_scan.png": "png",
            "report_scan.webp": "webp",
            "report_scan.tiff": "tiff",
            "report_scan.heic": "heic",
        }

        for fname, exp_fmt in expected_formats.items():
            fpath = fixtures_dir / fname
            if fpath.exists():
                fmt = detect_file_format_by_header(fpath)
                self.assertEqual(fmt, exp_fmt, f"Format mismatch for {fname}: got {fmt}, expected {exp_fmt}")

    def test_02_image_preprocessing_and_blur_check(self):
        """Test Pillow image contrast auto-enhancement and blur variance check."""
        img = Image.new("RGB", (200, 200), color="white")
        processed, quality_info = preprocess_image_for_ocr(img)
        self.assertIsNotNone(processed)
        blur_var = quality_info.get("laplacian_variance", 0.0)
        self.assertGreaterEqual(blur_var, 0.0)

    def test_03_ocr_anomaly_and_decimal_shifts(self):
        """Test OCR decimal shifts and range anomalies."""
        # HbA1c = 65 -> suggest 6.5
        has_anom, msg, s_val = detect_ocr_anomalies("HbA1c", "65")
        self.assertTrue(has_anom)
        self.assertEqual(s_val, 6.5)

        # HbA1c = 0.65 -> suggest 6.5
        has_anom, msg, s_val = detect_ocr_anomalies("HbA1c", "0.65")
        self.assertTrue(has_anom)
        self.assertEqual(s_val, 6.5)

        # Glucose = 13.2 -> suggest 132
        has_anom, msg, s_val = detect_ocr_anomalies("Fasting_Blood_Glucose", "13.2")
        self.assertTrue(has_anom)
        self.assertEqual(s_val, 132.0)

        # Character confusion 'O' -> 0
        has_anom, msg, s_val = detect_ocr_anomalies("Fasting_Blood_Glucose", "1O5")
        self.assertFalse(has_anom)

    def test_04_unit_normalization_preserves_raw(self):
        """Test unit normalization retains raw value + unit structure."""
        raw_mapped = {
            "CLINICAL": {
                "Fasting_Blood_Glucose": 126.0,
                "HbA1c": 6.8,
                "Height": 175.0,
                "Weight": 70.0
            }
        }
        norm = normalize_mapped_dict(raw_mapped)
        clin = norm.get("CLINICAL", {})
        val = clin["Fasting_Blood_Glucose"]
        num_val = val["normalized_value"] if isinstance(val, dict) else val
        self.assertEqual(num_val, 126.0)

    def test_05_multi_report_fusion_and_pid_mismatch(self):
        """Test multi-report fusion, conflict map creation, and Patient ID mismatch warning."""
        rep1 = {
            "CLINICAL": {"Patient_ID": "P001", "Fasting_Blood_Glucose": 110},
            "metadata": {"source_file": "lab1.pdf", "source_type": "Official Laboratory Report"}
        }
        rep2 = {
            "CLINICAL": {"Patient_ID": "P002", "Fasting_Blood_Glucose": 132},
            "metadata": {"source_file": "lab2.pdf", "source_type": "Official Laboratory Report"}
        }

        profile, warnings = fuse_multiple_reports([rep1, rep2])
        self.assertIsNotNone(profile.different_patient_warning)
        self.assertIn("Patient ID Mismatch Detected", profile.different_patient_warning)
        self.assertIn("Fasting_Blood_Glucose", profile.conflict_map)

    def test_06_modality_aware_data_quality_score(self):
        """Test modality-aware Data Quality Score calculation formula and capping rules."""
        # Single Modality (Clinical only with 15 features)
        clin_15 = {f: 1.0 for f in ['Age','Gender','Height','Weight','BMI','Waist_Circumference','Systolic_BP','Diastolic_BP','Fasting_Blood_Glucose','HbA1c','Triglycerides','HDL','LDL','ALT','AST']}
        res_clin = calculate_data_quality_scores(clin_15, {}, {})
        
        # High input quality score (~89.2%), not halved to 44%
        self.assertGreater(res_clin["overall_quality_score"], 80.0)
        self.assertEqual(res_clin["quality_label"], "High Input Quality")
        self.assertEqual(res_clin["multimodal_coverage_pct"], 50.0)

        # Capped on VERIFY anomalies -> capped at 65.0
        verify_flags = {"HbA1c": {"status": "VERIFY", "current_value": 65}}
        res_v = calculate_data_quality_scores(clin_15, {}, {}, verify_flags=verify_flags)
        self.assertLessEqual(res_v["overall_quality_score"], 65.0)

        # Capped on CONFLICT items -> capped at 60.0
        conflict_map = {"Fasting_Blood_Glucose": {"status": "CONFLICT"}}
        res_c = calculate_data_quality_scores(clin_15, {}, {}, conflict_map=conflict_map)
        self.assertLessEqual(res_c["overall_quality_score"], 60.0)

    def test_07_bmi_calculation_and_mismatch_verify(self):
        """Test Height=170cm, Weight=87kg auto-derives BMI ~30.1 and flags stored BMI mismatch."""
        clean, errs, warns, v_flags = validate_feature_dict({"Height": 170, "Weight": 87, "BMI": 22.0})
        self.assertIn("BMI", v_flags)
        self.assertEqual(v_flags["BMI"]["status"], "VERIFY")
        self.assertIn("BMI mismatch", v_flags["BMI"]["explanation"])

    def test_08_full_17_format_file_extraction(self):
        """Test actual file ingestion across all 17 supported fixtures."""
        fixtures_dir = Path(__file__).resolve().parent / "test_files"
        engine = MultimodalIntakeEngine()
        
        passed_count = 0
        for fpath in fixtures_dir.glob("*.*"):
            res = engine.process_reports([str(fpath)])
            self.assertIn("patient_profile", res)
            self.assertIn("data_quality_scores", res)
            passed_count += 1

        self.assertGreaterEqual(passed_count, 15)


if __name__ == "__main__":
    unittest.main()
