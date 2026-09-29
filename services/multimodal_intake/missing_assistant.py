"""
missing_assistant.py — Missing Feature Assistant Module (Modules 8 & 9).

Categorizes features into mandatory vs optional for each expert model.
Instead of simply displaying "HbA1c Missing", generates clinically helpful explanations:
"HbA1c is required for accurate diabetes prediction.
Please choose one of the following:
• Upload a Diabetes Report
• Enter the value manually
• Continue without this feature

Continuing without this feature may reduce prediction accuracy."
"""

from typing import Any, Dict, List, Set
from . import config


CLINICAL_IMPACT_DESCRIPTIONS: Dict[str, str] = {
    "HbA1c": "HbA1c measures 2-3 month average blood glucose and is critical for Type 2 Diabetes and Prediabetes diagnosis.",
    "Fasting_Blood_Glucose": "Fasting blood glucose is essential for evaluating acute glycemic regulation and insulin resistance.",
    "BMI": "Body Mass Index (BMI) is required to assess obesity class and baseline metabolic syndrome risk.",
    "Systolic_BP": "Systolic blood pressure is a mandatory component of hypertension and Metabolic Syndrome evaluation.",
    "Diastolic_BP": "Diastolic blood pressure is required for vascular risk assessment.",
    "Average_Daily_Steps": "Daily physical activity volume is necessary for wearable expert metabolic expenditure modeling.",
    "Resting_Heart_Rate": "Resting heart rate reflects autonomic cardiovascular health and metabolic syndrome risk.",
    "Average_Glucose": "CGM mean glucose is necessary for continuous glycemic profile modeling.",
    "Akkermansia": "Akkermansia muciniphila is a key gut barrier-protective bacterium depleted in metabolic disease.",
    "Faecalibacterium": "Faecalibacterium prausnitzii is a primary anti-inflammatory SCFA butyrate producer.",
    "Bifidobacterium": "Bifidobacterium is a core beneficial microbe essential for healthy gut homeostasis.",
    "Shannon_Diversity_Index": "Shannon Diversity Index measures overall microbiome community alpha-diversity and dysbiosis."
}


def analyze_missing_features(
    modality: str,
    features: Dict[str, Any],
    mandatory_set: Set[str],
    optional_set: Set[str]
) -> Dict[str, Any]:
    """Identify missing mandatory and optional features for a given modality.

    Args:
        modality: Name of modality ('CLINICAL', 'WEARABLE', 'GUT_MICROBIOME').
        features: Present feature dictionary.
        mandatory_set: Set of mandatory feature keys.
        optional_set: Set of optional feature keys.

    Returns:
        Structured missing feature report with user guidance prompts.
    """
    missing_mandatory: List[str] = [
        feat for feat in mandatory_set
        if feat not in features or features[feat] is None
    ]

    missing_optional: List[str] = [
        feat for feat in optional_set
        if feat not in features or features[feat] is None
    ]

    guidance_prompts: List[Dict[str, Any]] = []

    for feat in missing_mandatory:
        impact = CLINICAL_IMPACT_DESCRIPTIONS.get(
            feat, f"{feat} is a mandatory feature required for expert model prediction."
        )
        guidance_prompts.append({
            "feature": feat,
            "category": "Mandatory",
            "impact_statement": f"{feat} is required for accurate {modality.lower()} prediction. {impact}",
            "options": [
                f"Upload a report containing {feat}",
                f"Enter {feat} value manually",
                "Continue without prediction from this expert model"
            ]
        })

    for feat in missing_optional:
        impact = CLINICAL_IMPACT_DESCRIPTIONS.get(
            feat, f"{feat} improves model precision."
        )
        guidance_prompts.append({
            "feature": feat,
            "category": "Optional",
            "impact_statement": f"{feat} is optional. {impact}",
            "options": [
                f"Upload a report containing {feat}",
                f"Enter {feat} value manually",
                "Continue with reduced prediction accuracy"
            ]
        })

    return {
        "modality": modality,
        "missing_mandatory": missing_mandatory,
        "missing_optional": missing_optional,
        "has_missing_mandatory": len(missing_mandatory) > 0,
        "guidance_prompts": guidance_prompts
    }
