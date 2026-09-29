"""
normalizer.py — Unit Normalization Module (Module 4).

Normalizes different laboratory and physical units into the single standard
internal representation before prediction.

Examples:
- HbA1c: mmol/mol ➔ %
- Glucose / Lipids: mmol/L ➔ mg/dL
- Weight: lbs ➔ kg
- Height: feet/inches ➔ cm
"""

import logging
import re
from typing import Any, Dict, Tuple, Union

logger = logging.getLogger("imdie.normalizer")


def parse_numeric_and_unit(raw_value: Any) -> Tuple[Union[float, str, None], str]:
    """Parse raw string or numeric value into float value and unit string."""
    if raw_value is None:
        return None, ""

    if isinstance(raw_value, dict) and "raw_value" in raw_value:
        raw_value = raw_value["raw_value"]

    if raw_value is None:
        return None, ""

    if isinstance(raw_value, (int, float)):
        return float(raw_value), ""

    val_str = str(raw_value).strip()

    # Word-to-number mapping for extreme edge cases (e.g. "eighty kg")
    word_num_map = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100
    }
    for w_name, w_val in word_num_map.items():
        if re.search(rf"\b{w_name}\b", val_str, re.IGNORECASE):
            val_str = re.sub(rf"\b{w_name}\b", str(w_val), val_str, flags=re.IGNORECASE)

    # Strip leading words e.g. "Approx 178 cm", "< 120 mg/dL", "~80 kg", "Result: 109"
    val_str_clean = re.sub(r'^(?:approx|approx\.|about|~|<|>|result[:\s]*)\s*', '', val_str, flags=re.IGNORECASE).strip()

    # Strip thousand-separator commas from numeric values (e.g. "9,400" → "9400")
    val_str_clean = re.sub(r'(\d),(\d)', r'\1\2', val_str_clean)

    # Handle scientific/k multiplier e.g. "8.4k", "2.45 kcal ×10³/day" or "2.45 x 10^3"
    k_match = re.search(r"^([-+]?[0-9]*\.?[0-9]+)\s*(?:kcal\s*)?(?:[x×]\s*10\^?3|k)\b", val_str_clean, re.IGNORECASE)
    if k_match:
        mult_val = float(k_match.group(1)) * 1000.0
        return mult_val, ""

    # Handle feet/inches format e.g. "5 ft 10 in" or "5'10\""
    ft_in_match = re.search(r"(\d+)\s*(?:ft|')\s*(\d+)?\s*(?:in|\")?", val_str_clean, re.IGNORECASE)
    if ft_in_match:
        feet = float(ft_in_match.group(1))
        inches = float(ft_in_match.group(2)) if ft_in_match.group(2) else 0.0
        cm_val = (feet * 12.0 + inches) * 2.54
        return round(cm_val, 1), "cm"

    # Match numeric float and trailing unit string
    match = re.search(r"^([-+]?[0-9]*\.?[0-9]+)\s*([A-Za-z%/_\-][A-Za-z0-9%/_\-²]*)?", val_str_clean)
    if match:
        num = float(match.group(1))
        unit = match.group(2).strip().lower() if match.group(2) else ""
        return num, unit

    # Categorical string like "Male", "Female", "P00001", or binary flags
    return val_str_clean, ""


def normalize_feature_value(feature_name: str, raw_value: Any) -> Any:
    """Normalize a single feature's value into standard TeleMed units."""
    if isinstance(raw_value, dict) and "raw_value" in raw_value:
        raw_val_str = str(raw_value["raw_value"]).strip()
        if feature_name == "Patient_ID":
            return raw_val_str

    if feature_name == "Patient_ID":
        return str(raw_value).strip() if raw_value is not None else "P_GUEST"

    # Gender normalization (e.g. "M" -> "Male", "F" -> "Female")
    if feature_name == "Gender":
        g_val = str(raw_value["raw_value"] if isinstance(raw_value, dict) and "raw_value" in raw_value else raw_value).strip().lower()
        if g_val in ["m", "male", "man", "boy"]:
            return "Male"
        elif g_val in ["f", "female", "woman", "girl"]:
            return "Female"

    # Binary flags (Family_History_Diabetes, Family_History_Hypertension, Family_History_CVD)
    if str(feature_name).startswith("Family_History_"):
        fh_val = raw_value
        if isinstance(fh_val, dict) and "raw_value" in fh_val:
            fh_val = fh_val["raw_value"]
        raw_str = str(fh_val).strip().lower()
        if raw_str in ["yes", "y", "true", "1", "1.0", "reported", "present"]:
            return 1
        elif raw_str in ["no", "n", "false", "0", "0.0", "absent"]:
            return 0

    val, unit = parse_numeric_and_unit(raw_value)
    if val is None or isinstance(val, str):
        return val

    # 1. Glucose (Fasting_Blood_Glucose, Average_Glucose): Canonical = mg/dL
    if feature_name in ["Fasting_Blood_Glucose", "Average_Glucose"]:
        if unit in ["mmol/l", "mmol"]:
            return round(val * 18.0182, 1)

    # 2. Glucose Variability: Canonical = % / SD in mg/dL
    elif feature_name == "Glucose_Variability":
        if unit in ["mmol/l", "mmol"]:
            return round(val * 18.0182, 1)

    # 3. HbA1c: Canonical = %
    elif feature_name == "HbA1c":
        if unit in ["mmol/mol"]:
            return round((val / 10.929) + 2.15, 2)

    # 3. Cholesterol & Triglycerides (LDL, HDL, Triglycerides): Canonical = mg/dL
    elif feature_name in ["LDL", "LDL_Cholesterol", "HDL", "HDL_Cholesterol", "Triglycerides"]:
        if unit in ["mmol/l", "mmol"]:
            if feature_name == "Triglycerides":
                return round(val * 88.57, 1)
            else:
                return round(val * 38.67, 1)

    # 4. Weight: Canonical = kg
    elif feature_name in ["Weight", "Weight_kg"]:
        if unit in ["lbs", "lb", "pound", "pounds"]:
            return round(val * 0.453592, 1)

    # 5. Height: Canonical = cm
    elif feature_name in ["Height", "Height_cm"]:
        if unit in ["m", "meter", "meters"]:
            return round(val * 100.0, 1)
        elif unit in ["in", "inch", "inches"]:
            return round(val * 2.54, 1)

    # 6. Waist Circumference: Canonical = cm
    elif feature_name in ["Waist_Circumference", "Waist_Circumference_cm"]:
        if unit in ["in", "inch", "inches"]:
            return round(val * 2.54, 1)

    # 7. Wearable Active Minutes & Sedentary Time: Canonical = Minutes
    elif feature_name in ["Active_Minutes", "Sedentary_Time_Minutes"]:
        if unit in ["h", "hr", "hrs", "hour", "hours", "hours/day"]:
            return round(val * 60.0, 1)

    # 8. Sleep Duration: Canonical = Hours
    elif feature_name in ["Sleep_Duration", "Sleep_Duration_Hours"]:
        if unit in ["m", "min", "mins", "minute", "minutes"]:
            return round(val / 60.0, 2)

    # 9. Microbiome Relative Abundances: Canonical = %
    elif feature_name in ["Akkermansia", "Faecalibacterium", "Bifidobacterium", "Roseburia",
                          "Alistipes", "Escherichia_Shigella", "Collinsella", "Prevotella", "Blautia"]:
        if unit in ["fraction", "dec", "relative"] or (unit == "" and 0.0 < val <= 1.0):
            return round(val * 100.0, 2)

    # Default: return parsed float rounded to appropriate precision
    if isinstance(val, float):
        if feature_name in ["Age", "Systolic_BP", "Diastolic_BP", "Fasting_Blood_Glucose",
                            "LDL", "LDL_Cholesterol", "HDL", "HDL_Cholesterol", "Triglycerides", "ALT", "AST",
                            "Average_Daily_Steps", "Active_Minutes", "Sedentary_Time_Minutes"]:
            return int(round(val))
        return round(val, 2)

    return val


def normalize_mapped_dict(mapped_dict: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Normalize units for all mapped feature dictionaries."""
    normalized: Dict[str, Dict[str, Any]] = {}
    for modality, features in mapped_dict.items():
        normalized[modality] = {}
        for feature, val in features.items():
            normalized[modality][feature] = normalize_feature_value(feature, val)
    return normalized
