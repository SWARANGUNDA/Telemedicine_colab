"""
main.py — CLI Entrypoint and Demo for IMDIE.

Demonstrates processing sample clinical lab reports, wearable export CSVs,
and gut microbiome sequencing reports through the complete 15-stage IMDIE pipeline.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from .engine import MultimodalIntakeEngine

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("imdie.main")


SAMPLE_CLINICAL_REPORT = """
=====================================================
          METABOLIC HEALTH & LAB REPORT              
=====================================================
Patient ID: P99821
Age: 52 years
Gender: Male
Height: 5 ft 10 in
Weight: 185 lbs
Systolic BP: 134 mmHg
Diastolic BP: 86 mmHg
Fasting Blood Glucose: 6.8 mmol/L
HbA1c: 6.3 %
LDL Cholesterol: 142 mg/dL
HDL Cholesterol: 38 mg/dL
Triglycerides: 210 mg/dL
ALT: 48 U/L
AST: 34 U/L
Family History Diabetes: 1
Family History Obesity: 1
=====================================================
"""

SAMPLE_WEARABLE_REPORT = """
Average_Daily_Steps: 6200
Active_Minutes: 18.5
Sedentary_Time_Minutes: 420
Resting_Heart_Rate: 72
Sleep_Duration: 6.8
Calories_Burned: 1950
Average_Glucose: 138 mg/dL
Glucose_Variability: 24.5
Time_In_Range: 55.0
Time_Above_Range: 42.0
"""

SAMPLE_GUT_REPORT = """
Akkermansia: 2.1 %
Faecalibacterium: 5.4 %
Bifidobacterium: 3.2 %
Roseburia: 2.8 %
Escherichia_Shigella: 6.8 %
Blautia: 7.2 %
Prevotella: 8.5 %
Collinsella: 4.1 %
Alistipes: 2.3 %
Shannon_Diversity_Index: 2.15
"""


def run_demo():
    """Run IMDIE demo on 3 multi-modal sample reports."""
    print("=" * 70)
    print("      INTELLIGENT MULTIMODAL DATA INTAKE ENGINE (IMDIE) DEMO      ")
    print("=" * 70)

    engine = MultimodalIntakeEngine()
    result = engine.process_reports([
        SAMPLE_CLINICAL_REPORT,
        SAMPLE_WEARABLE_REPORT,
        SAMPLE_GUT_REPORT
    ])

    print("\n--- 1. DATA QUALITY SCORES ---")
    for k, v in result["data_quality_scores"].items():
        print(f"  {k:20s}: {v}%")

    print("\n--- 2. EXPERT AVAILABILITY & STRATEGY ---")
    for exp, status in result["expert_availability"].items():
        print(f"  {exp:20s}: {status}")

    print(f"  Active Strategy     : {result['adaptive_prediction_strategy']['strategy_name']}")
    print(f"  Confidence Tier     : {result['prediction_confidence']['confidence_level']}")
    print(f"  Rationale           : {result['prediction_confidence']['confidence_reason']}")

    print("\n--- 3. ROUTED EXPERT PAYLOADS ---")
    for payload_name, p_data in result["expert_routing"].items():
        if payload_name == "Patient_ID":
            continue
        print(f"\n  [{payload_name}]")
        for f, val in p_data.items():
            if f != "Patient_ID":
                print(f"    {f:30s}: {val}")

    print("\n--- 4. MISSING FEATURE ASSISTANT GUIDANCE ---")
    for mod, report in result["missing_feature_assistant"].items():
        prompts = report["guidance_prompts"]
        if prompts:
            print(f"  [{mod}] Missing Features Detected:")
            for item in prompts:
                print(f"    • {item['feature']} ({item['category']}): {item['impact_statement']}")
        else:
            print(f"  [{mod}] All features present!")

    print("\n--- 5. AUDIT LOG SUMMARY ---")
    print(f"  Total pipeline steps executed: {result['audit_log']['total_steps']}")

    print("=" * 70)
    print("DEMO COMPLETED SUCCESSFULLY.")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Intelligent Multimodal Data Intake Engine (IMDIE)")
    parser.add_argument("--demo", action="store_true", help="Run demo with sample reports")
    parser.add_argument("--files", nargs="+", help="Paths to report files (PDF, CSV, JSON, TXT)")
    args = parser.parse_args()

    if args.demo or not args.files:
        run_demo()
    else:
        engine = MultimodalIntakeEngine()
        result = engine.process_reports(args.files)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
