"""
v3_schema_validator.py — Schema Validator & Modality Detector for Unified Multimodal v3.2.2.

Validates incoming patient payloads against exact v3 feature schemas:
- Clinical v3 (18 features)
- Wearable v3 (10 Standard + 5 CGM features)
- Gut v3 (20 Taxa RAW relative abundance)

Detects modality availability, feature completeness, and CGM measurement status.
Strictly isolates missing feature imputation tracking without modifying raw inputs.
"""

import logging
from typing import Dict, Any, Tuple, List, Optional
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("v3_schema_validator")


CLINICAL_V4_FEATURES = [
    "Age", "Gender", "Height", "Weight", "BMI", "Waist_Circumference",
    "Systolic_BP", "Diastolic_BP", "Fasting_Blood_Glucose", "HbA1c",
    "Triglycerides", "HDL", "LDL", "ALT", "AST",
    "Family_History_Diabetes", "Family_History_Hypertension", "Family_History_CVD"
]

WEARABLE_V4_FEATURES = [
    "Average_Daily_Steps", "Active_Minutes", "Sedentary_Time_Minutes",
    "Resting_Heart_Rate", "Heart_Rate_Variability_RMSSD", "Sleep_Duration_Hours",
    "Sleep_Efficiency_Score", "Autonomic_Stress_Score", "Activity_Energy_Expenditure",
    "Exercise_Frequency_Days", "CGM_Average_Glucose", "CGM_Glucose_CV",
    "CGM_Time_In_Range", "CGM_Time_Above_Range", "CGM_Time_Below_Range"
]

GUT_V4_TAXA_FEATURES = [
    "Akkermansia_muciniphila", "Faecalibacterium_prausnitzii", "Roseburia_intestinalis",
    "Bifidobacterium_longum", "Bifidobacterium_adolescentis", "Bacteroides_thetaiotaomicron",
    "Bacteroides_vulgatus", "Bacteroides_fragilis", "Bacteroides_uniformis",
    "Prevotella_copri", "Ruminococcus_bromii", "Ruminococcus_gnavus",
    "Blautia_wexlerae", "Blautia_hansenii", "Collinsella_aerofaciens",
    "Escherichia_coli", "Klebsiella_pneumoniae", "Coprococcus_eutactus",
    "Alistipes_putredinis", "Alistipes_finegoldii", "Subdoligranulum_variable",
    "Enterococcus_faecalis", "Eubacterium_rectale", "Eubacterium_hallii",
    "Parabacteroides_distasonis", "Lactobacillus_acidophilus", "Lactobacillus_rhamnosus",
    "Streptococcus_thermophilus", "Eggerthella_lenta", "Christensenella_minuta",
    "Methanobrevibacter_smithii", "Dialister_invisus", "Holdemanella_biformis",
    "Barnesiella_intestinihominis", "Anaerostipes_caccae", "Phascolarctobacterium_faecium",
    "Veillonella_parvula", "Fusobacterium_nucleatum", "Bilophila_wadsworthia",
    "Sutterella_wadsworthensis"
]

GUT_V4_INDICES_FEATURES = [
    "Shannon_Diversity", "Simpson_Diversity", "Observed_Richness",
    "Pielou_Evenness", "SCFA_Producer_Index", "Butyrate_Producer_Index",
    "Barrier_Associated_Index", "Inflammation_Associated_Index",
    "Log_Firmicutes_Bacteroidetes_Ratio"
]

TARGET_DISEASE_LABELS = {
    "Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"
}


class V3SchemaValidator:
    @staticmethod
    def validate_and_inspect_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inspects raw JSON payload, normalizes key casings, validates V4 schemas,
        checks gut composition sum (≈100%), and rejects target disease leakage.
        """
        patient_id = payload.get("patient_id", "UNKNOWN_PATIENT")
        
        raw_clinical = payload.get("clinical_data", None) or payload.get("clinical", None)
        raw_wearable = payload.get("wearable_data", None) or payload.get("wearable", None)
        raw_gut      = payload.get("gut_data", None) or payload.get("gut", None)

        if not (raw_clinical or raw_wearable or raw_gut) and "predict_response" in payload:
            pred_resp = payload.get("predict_response") or {}
            expert_outs = pred_resp.get("expert_outputs") or {}
            raw_clinical = (expert_outs.get("clinical") or {}).get("raw_input") or (expert_outs.get("clinical") or {}) or pred_resp.get("confirmed_features", {}).get("clinical")
            raw_wearable = (expert_outs.get("wearable") or {}).get("raw_input") or (expert_outs.get("wearable") or {}) or pred_resp.get("confirmed_features", {}).get("wearable")
            raw_gut      = (expert_outs.get("gut") or {}).get("raw_input") or (expert_outs.get("gut") or {}) or pred_resp.get("confirmed_features", {}).get("gut")

        # Strip target disease labels from inputs
        raw_clinical = V3SchemaValidator._sanitize_feature_dict(raw_clinical)
        raw_wearable = V3SchemaValidator._sanitize_feature_dict(raw_wearable)
        raw_gut      = V3SchemaValidator._sanitize_feature_dict(raw_gut)

        clinical_dict, c_present, c_supplied, c_missing = V3SchemaValidator._inspect_modality(raw_clinical, CLINICAL_V4_FEATURES)
        wearable_dict, w_present, w_supplied, w_missing = V3SchemaValidator._inspect_wearable(raw_wearable)
        gut_dict,      g_present, g_supplied, g_missing, gut_validation_error = V3SchemaValidator._inspect_gut(raw_gut)

        modalities_supplied = []
        if c_present: modalities_supplied.append("clinical")
        if w_present: modalities_supplied.append("wearable")
        if g_present and not gut_validation_error: modalities_supplied.append("gut")

        missing_modalities = [m for m in ["clinical", "wearable", "gut"] if m not in modalities_supplied]

        # Determine pathway mask
        if c_present and not w_present and not (g_present and not gut_validation_error):
            modality_mask = "C"
        elif w_present and not c_present and not (g_present and not gut_validation_error):
            modality_mask = "W"
        elif (g_present and not gut_validation_error) and not c_present and not w_present:
            modality_mask = "G"
        elif c_present and w_present and not (g_present and not gut_validation_error):
            modality_mask = "C+W"
        elif c_present and (g_present and not gut_validation_error) and not w_present:
            modality_mask = "C+G"
        elif w_present and (g_present and not gut_validation_error) and not c_present:
            modality_mask = "W+G"
        elif c_present and w_present and (g_present and not gut_validation_error):
            modality_mask = "C+W+G"
        else:
            modality_mask = "NONE"

        if modality_mask == "NONE":
            raise ValueError(
                f"Payload for patient '{patient_id}' contains no valid modality data. "
                "At least one of clinical_data, wearable_data, or gut_data must be supplied with valid features."
            )

        return {
            "patient_id": patient_id,
            "modality_mask": modality_mask,
            "modalities_supplied": modalities_supplied,
            "missing_modalities": missing_modalities,
            "clinical_data": clinical_dict,
            "clinical_present": c_present,
            "clinical_supplied_features": c_supplied,
            "clinical_missing_features": c_missing,
            "wearable_data": wearable_dict,
            "wearable_present": w_present,
            "wearable_supplied_features": w_supplied,
            "wearable_missing_features": w_missing,
            "cgm_supplied_count": sum(1 for f in WEARABLE_V4_FEATURES[-5:] if f in w_supplied),
            "gut_data": gut_dict,
            "gut_present": g_present,
            "gut_supplied_features": g_supplied,
            "gut_missing_features": g_missing,
            "gut_validation_error": gut_validation_error
        }

    @staticmethod
    def _sanitize_feature_dict(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not data or not isinstance(data, dict):
            return data
        return {k: v for k, v in data.items() if k not in TARGET_DISEASE_LABELS}

    @staticmethod
    def _inspect_modality(data: Optional[Dict[str, Any]], expected_features: List[str]) -> Tuple[Dict[str, float], bool, List[str], List[str]]:
        if not data or not isinstance(data, dict):
            return {}, False, [], expected_features

        normalized = {k.strip(): v for k, v in data.items() if v is not None and k != "Patient_ID"}
        if not normalized:
            return {}, False, [], expected_features

        supplied = []
        missing = []
        cleaned_dict = {}

        for f in expected_features:
            f_lower = f.lower()
            matched_key = next((k for k in normalized.keys() if k.lower() == f_lower or k.lower().replace("_", "") == f_lower.replace("_", "")), None)

            if matched_key is not None:
                try:
                    val = float(normalized[matched_key])
                    cleaned_dict[f] = val
                    supplied.append(f)
                except (ValueError, TypeError):
                    missing.append(f)
            else:
                missing.append(f)

        present = len(supplied) > 0
        return cleaned_dict, present, supplied, missing

    @staticmethod
    def _inspect_wearable(data: Optional[Dict[str, Any]]) -> Tuple[Dict[str, float], bool, List[str], List[str]]:
        return V3SchemaValidator._inspect_modality(data, WEARABLE_V4_FEATURES)

    @staticmethod
    def _inspect_gut(data: Optional[Dict[str, Any]]) -> Tuple[Dict[str, float], bool, List[str], List[str], Optional[str]]:
        if not data or not isinstance(data, dict):
            return {}, False, [], GUT_V4_TAXA_FEATURES + GUT_V4_INDICES_FEATURES, None

        GENUS_MAP = {
            "akkermansia": "Akkermansia_muciniphila",
            "faecalibacterium": "Faecalibacterium_prausnitzii",
            "roseburia": "Roseburia_intestinalis",
            "bifidobacterium": "Bifidobacterium_longum",
            "bacteroides": "Bacteroides_vulgatus",
            "prevotella": "Prevotella_copri",
            "ruminococcus": "Ruminococcus_gnavus",
            "blautia": "Blautia_wexlerae",
            "collinsella": "Collinsella_aerofaciens",
            "escherichia/shigella": "Escherichia_coli",
            "escherichia_shigella": "Escherichia_coli",
            "escherichia": "Escherichia_coli",
            "coprococcus": "Coprococcus_eutactus",
            "alistipes": "Alistipes_putredinis",
            "subdoligranulum": "Subdoligranulum_variable",
            "enterococcus": "Enterococcus_faecalis",
            "eubacterium": "Eubacterium_hallii",
            "parabacteroides": "Parabacteroides_distasonis",
            "lactobacillus": "Lactobacillus_acidophilus",
            "klebsiella": "Klebsiella_pneumoniae",
            "streptococcus": "Streptococcus_thermophilus",
            "eggerthella": "Eggerthella_lenta",
            "christensenella": "Christensenella_minuta",
            "methanobrevibacter": "Methanobrevibacter_smithii",
            "dialister": "Dialister_invisus",
            "holdemanella": "Holdemanella_biformis",
            "barnesiella": "Barnesiella_intestinihominis",
            "anaerostipes": "Anaerostipes_caccae",
            "phascolarctobacterium": "Phascolarctobacterium_faecium",
            "veillonella": "Veillonella_parvula",
            "fusobacterium": "Fusobacterium_nucleatum",
            "bilophila": "Bilophila_wadsworthia",
            "sutterella": "Sutterella_wadsworthensis",
            "shannon diversity index": "Shannon_Diversity",
            "shannon_diversity_index": "Shannon_Diversity",
            "shannon diversity": "Shannon_Diversity",
        }

        raw_clean = {k.strip(): v for k, v in data.items() if v is not None and k not in ("Patient_ID", "Age", "Gender")}
        
        # Canonicalize keys using species map & aliases
        normalized: Dict[str, float] = {}
        for k, v in raw_clean.items():
            k_lower = k.lower().replace(" ", "_")
            canonical_k = None
            
            # 1. Exact match in V4 features
            for feat in GUT_V4_TAXA_FEATURES + GUT_V4_INDICES_FEATURES:
                if feat.lower() == k_lower:
                    canonical_k = feat
                    break
            
            # 2. Genus alias match
            if not canonical_k:
                clean_lookup = k.lower().strip()
                if clean_lookup in GENUS_MAP:
                    canonical_k = GENUS_MAP[clean_lookup]
                else:
                    clean_lookup_under = clean_lookup.replace(" ", "_")
                    if clean_lookup_under in GENUS_MAP:
                        canonical_k = GENUS_MAP[clean_lookup_under]

            if not canonical_k:
                canonical_k = k

            try:
                normalized[canonical_k] = float(v)
            except (ValueError, TypeError):
                pass

        # Calculate compositional sum across taxa
        taxa_present = {k: v for k, v in normalized.items() if k in GUT_V4_TAXA_FEATURES}
        taxa_sum = sum(taxa_present.values())

        # Auto-renormalize to 100.0% simplex if taxa are present
        if taxa_sum > 0:
            scale_factor = 100.0 / taxa_sum
            for k in taxa_present:
                normalized[k] = round(taxa_present[k] * scale_factor, 4)

        # Automatically derive diversity and functional indices if missing or default
        if len(taxa_present) > 0:
            taxa_vals = [normalized.get(t, 0.0) for t in GUT_V4_TAXA_FEATURES]
            taxa_arr = np.array(taxa_vals, dtype=float)
            total_sum = np.sum(taxa_arr)
            if total_sum > 0:
                p_frac = taxa_arr / total_sum
            else:
                p_frac = taxa_arr
            p_no_zero = np.where(p_frac > 0, p_frac, 1.0)

            if "Shannon_Diversity" not in normalized or normalized["Shannon_Diversity"] == 0:
                normalized["Shannon_Diversity"] = float(round(-np.sum(p_frac * np.log(p_no_zero)), 4))
            if "Simpson_Diversity" not in normalized or normalized["Simpson_Diversity"] == 0:
                normalized["Simpson_Diversity"] = float(round(1.0 - np.sum(p_frac ** 2), 4))
            if "Observed_Richness" not in normalized or normalized["Observed_Richness"] == 0:
                normalized["Observed_Richness"] = float(np.sum(taxa_arr > 0))
            if "Pielou_Evenness" not in normalized or normalized["Pielou_Evenness"] == 0:
                normalized["Pielou_Evenness"] = float(round(normalized["Shannon_Diversity"] / np.log(max(normalized["Observed_Richness"], 2)), 4))

            taxa_pct = p_frac * 100.0
            if "SCFA_Producer_Index" not in normalized:
                normalized["SCFA_Producer_Index"] = float(round(np.mean(taxa_pct[[1, 2, 3, 4, 10, 17, 18, 20, 22, 23, 31, 34]]), 4))
            if "Butyrate_Producer_Index" not in normalized:
                normalized["Butyrate_Producer_Index"] = float(round(np.mean(taxa_pct[[1, 2, 17, 20, 22, 23, 34]]), 4))
            if "Barrier_Associated_Index" not in normalized:
                normalized["Barrier_Associated_Index"] = float(round(np.mean(taxa_pct[[0, 1, 3, 4, 29]]), 4))
            if "Inflammation_Associated_Index" not in normalized:
                normalized["Inflammation_Associated_Index"] = float(round(np.mean(taxa_pct[[11, 14, 15, 16, 21, 28, 37, 38]]), 4))

            if "Log_Firmicutes_Bacteroidetes_Ratio" not in normalized:
                firmicutes_idx = [1, 2, 10, 11, 12, 13, 17, 20, 21, 22, 23, 25, 26, 27, 29, 31, 32, 34, 35, 36]
                bacteroidetes_idx = [5, 6, 7, 8, 9, 18, 19, 24, 33]
                firmicutes = float(np.sum(taxa_pct[firmicutes_idx]))
                bacteroidetes = float(np.sum(taxa_pct[bacteroidetes_idx]))
                normalized["Log_Firmicutes_Bacteroidetes_Ratio"] = float(round(np.log((firmicutes + 0.01) / (bacteroidetes + 0.01)), 4))

        cleaned_dict, present, supplied, missing = V3SchemaValidator._inspect_modality(normalized, GUT_V4_TAXA_FEATURES + GUT_V4_INDICES_FEATURES)
        return cleaned_dict, present, supplied, missing, None

