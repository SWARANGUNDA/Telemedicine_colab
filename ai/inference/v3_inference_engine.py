"""
v3_inference_engine.py — Core Inference Engine for v3 Expert Models.

Loads and executes frozen v3 model payloads:
- Clinical Expert v3 (18 features)
- Wearable Expert v3 (15D Standard + CGM)
- Gut Expert v3 (20 Taxa RAW)

Strictly uses saved scalers, medians, calibrators (IsotonicRegression), and tuned thresholds.
Does NOT modify or retrain any artifact.
"""

import logging
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

# Suppress benign sklearn feature name warnings on array input during inference
warnings.filterwarnings("ignore", message=".*X does not have valid feature names.*", category=UserWarning)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("v3_inference_engine")

MODEL_DIR = Path(__file__).resolve().parent / "saved_models"
DISEASES = ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]

GUT_V4_TAXA_ORDER = [
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


def _compute_v4_gut_indices(input_dict: dict) -> dict:
    """Compute 9 ecological/functional gut indices from 40 species abundances if not provided."""
    taxa_vals = []
    for t in GUT_V4_TAXA_ORDER:
        val = input_dict.get(t, None)
        if val is None:
            short_k = t.split("_")[0]
            val = input_dict.get(short_k, 0.0)
        try:
            taxa_vals.append(float(val))
        except (ValueError, TypeError):
            taxa_vals.append(0.0)

    taxa_arr = np.array(taxa_vals, dtype=float)
    if taxa_arr.sum() > 0 and taxa_arr.sum() <= 1.1:
        taxa_arr = taxa_arr * 100.0

    p_frac = taxa_arr / 100.0
    p_no_zero = np.where(p_frac > 0, p_frac, 1.0)

    shannon = float(-np.sum(p_frac * np.log(p_no_zero)))
    simpson = float(1.0 - np.sum(p_frac ** 2))
    richness = int(np.sum(taxa_arr > 0))
    pielou = float(shannon / np.log(max(richness, 2)))

    scfa_idx = float(np.mean(taxa_arr[[1, 2, 3, 4, 10, 17, 18, 20, 22, 23, 31, 34]]))
    butyrate_idx = float(np.mean(taxa_arr[[1, 2, 17, 20, 22, 23, 34]]))
    barrier_idx = float(np.mean(taxa_arr[[0, 1, 3, 4, 29]]))
    infl_idx = float(np.mean(taxa_arr[[11, 14, 15, 16, 21, 28, 37, 38]]))

    firmicutes_idx = [1, 2, 10, 11, 12, 13, 17, 20, 21, 22, 23, 25, 26, 27, 29, 31, 32, 34, 35, 36]
    bacteroidetes_idx = [5, 6, 7, 8, 9, 18, 19, 24, 33]
    firmicutes = float(np.sum(taxa_arr[firmicutes_idx]))
    bacteroidetes = float(np.sum(taxa_arr[bacteroidetes_idx]))
    log_fb = float(np.log((firmicutes + 0.01) / (bacteroidetes + 0.01)))

    return {
        "Shannon_Diversity": round(shannon, 4),
        "Simpson_Diversity": round(simpson, 4),
        "Observed_Richness": richness,
        "Pielou_Evenness": round(pielou, 4),
        "SCFA_Producer_Index": round(scfa_idx, 4),
        "Butyrate_Producer_Index": round(butyrate_idx, 4),
        "Barrier_Associated_Index": round(barrier_idx, 4),
        "Inflammation_Associated_Index": round(infl_idx, 4),
        "Log_Firmicutes_Bacteroidetes_Ratio": round(log_fb, 4)
    }


class V3InferenceEngine:
    def __init__(self, model_dir: Path = MODEL_DIR):
        self.model_dir = Path(model_dir)
        self.clinical_payload = None
        self.wearable_payload = None
        self.gut_payload = None
        self._load_payloads()

    def _load_payloads(self):
        models_dir = Path(__file__).resolve().parent.parent / "models"
        clin_path = models_dir / "clinical" / "clinical_v4_expert_payload.joblib"
        wear_path = models_dir / "wearable_cgm" / "wearable_v4_expert_payload.joblib"
        gut_path  = models_dir / "gut_microbiome" / "gut_v4_expert_payload.joblib"

        if clin_path.exists():
            self.clinical_payload = joblib.load(clin_path)
            logger.info(f"Loaded Clinical Expert payload ({clin_path.name}) successfully.")
        else:
            logger.error(f"Clinical payload not found at {clin_path}")

        if wear_path.exists():
            self.wearable_payload = joblib.load(wear_path)
            logger.info(f"Loaded Wearable Expert payload ({wear_path.name}) successfully.")
        else:
            logger.error(f"Wearable payload not found at {wear_path}")

        if gut_path.exists():
            self.gut_payload = joblib.load(gut_path)
            logger.info(f"Loaded Gut Expert payload ({gut_path.name}) successfully.")
        else:
            logger.error(f"Gut payload not found at {gut_path}")

    def predict_clinical(self, input_dict: dict) -> dict:
        """
        Executes Clinical expert model (18 features).
        Missing features are imputed using stored training medians.
        """
        if not self.clinical_payload:
            raise RuntimeError("Clinical payload is not loaded.")

        features = self.clinical_payload["features"]
        medians = self.clinical_payload["medians"]
        scalers = self.clinical_payload.get("scalers", self.clinical_payload.get("scaler"))
        models = self.clinical_payload["models"]
        calibrators = self.clinical_payload.get("calibrators", None)
        thresholds = self.clinical_payload.get("thresholds", {d: 0.5 for d in DISEASES})

        feature_vals = []
        imputed_features = []
        supplied_features = []

        for f in features:
            val = input_dict.get(f, None)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                med_val = float(medians[f]) if isinstance(medians, (pd.Series, dict)) else float(medians)
                feature_vals.append(med_val)
                imputed_features.append(f)
            else:
                try:
                    if f == "Gender" and isinstance(val, str):
                        num_val = 1.0 if val.strip().lower() in ("male", "m", "1") else 0.0
                    else:
                        num_val = float(val)
                    feature_vals.append(num_val)
                    supplied_features.append(f)
                except (ValueError, TypeError):
                    med_val = float(medians[f]) if isinstance(medians, (pd.Series, dict)) else float(medians)
                    feature_vals.append(med_val)
                    imputed_features.append(f)

        df_raw = pd.DataFrame([feature_vals], columns=features)
        
        if isinstance(scalers, dict):
            X_scaled_dict = {d: scalers[d].transform(df_raw) for d in DISEASES}
        else:
            X_scaled_single = scalers.transform(df_raw)
            X_scaled_dict = {d: X_scaled_single for d in DISEASES}

        raw_probs = {}
        calibrated_probs = {}
        binary_preds = {}
        risk_levels = {}

        for i, d in enumerate(DISEASES):
            clf = models[d] if isinstance(models, dict) else models[i]
            t_opt = thresholds[d] if isinstance(thresholds, dict) else 0.5
            X_sc = X_scaled_dict[d]
            df_sc = pd.DataFrame(X_sc, columns=features)

            raw_p = float(clf.predict_proba(df_sc)[0, 1])
            if calibrators:
                iso = calibrators[d] if isinstance(calibrators, dict) else calibrators[i]
                cal_p = float(iso.transform([raw_p])[0]) if iso is not None else raw_p
            else:
                cal_p = raw_p

            pred_cls = int(cal_p >= t_opt)

            raw_probs[d] = round(raw_p, 4)
            calibrated_probs[d] = round(cal_p, 4)
            binary_preds[d] = pred_cls
            risk_levels[d] = self._determine_risk_level(cal_p, t_opt)

        return {
            "expert": "Clinical_v4",
            "raw_probabilities": raw_probs,
            "calibrated_probabilities": calibrated_probs,
            "predictions": binary_preds,
            "thresholds": thresholds,
            "risk_levels": risk_levels,
            "supplied_features": supplied_features,
            "imputed_features": imputed_features,
            "scaled_input": X_scaled_dict["Type2_Diabetes"],
            "raw_input": input_dict
        }

    def predict_wearable(self, input_dict: dict) -> dict:
        """
        Executes Wearable expert model (15 features).
        Missing features (including CGM) are imputed using stored training medians.
        """
        if not self.wearable_payload:
            raise RuntimeError("Wearable payload is not loaded.")

        features = self.wearable_payload["features"]
        medians = self.wearable_payload["medians"]
        scalers = self.wearable_payload.get("scalers", self.wearable_payload.get("scaler"))
        models = self.wearable_payload["models"]
        calibrators = self.wearable_payload.get("calibrators", None)
        thresholds = self.wearable_payload.get("thresholds", {d: 0.5 for d in DISEASES})

        cgm_feature_names = [
            "CGM_Average_Glucose", "CGM_Glucose_CV", "CGM_Time_In_Range",
            "CGM_Time_Above_Range", "CGM_Time_Below_Range"
        ]

        feature_vals = []
        imputed_features = []
        supplied_features = []
        cgm_supplied_count = 0

        for f in features:
            val = input_dict.get(f, None)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                med_val = float(medians[f]) if isinstance(medians, (pd.Series, dict)) else float(medians)
                feature_vals.append(med_val)
                imputed_features.append(f)
            else:
                feature_vals.append(float(val))
                supplied_features.append(f)
                if f in cgm_feature_names:
                    cgm_supplied_count += 1

        X_raw = np.array(feature_vals, dtype=float).reshape(1, -1)

        if isinstance(scalers, dict):
            X_scaled_dict = {d: scalers[d].transform(X_raw) for d in DISEASES}
        else:
            X_scaled_single = scalers.transform(X_raw)
            X_scaled_dict = {d: X_scaled_single for d in DISEASES}

        raw_probs = {}
        calibrated_probs = {}
        binary_preds = {}
        risk_levels = {}

        for i, d in enumerate(DISEASES):
            clf = models[d] if isinstance(models, dict) else models[i]
            t_opt = thresholds[d] if isinstance(thresholds, dict) else 0.5
            X_sc = X_scaled_dict[d]

            raw_p = float(clf.predict_proba(X_sc)[0, 1])
            if calibrators:
                iso = calibrators[d] if isinstance(calibrators, dict) else calibrators[i]
                cal_p = float(iso.transform([raw_p])[0]) if iso is not None else raw_p
            else:
                cal_p = raw_p

            pred_cls = int(cal_p >= t_opt)

            raw_probs[d] = round(raw_p, 4)
            calibrated_probs[d] = round(cal_p, 4)
            binary_preds[d] = pred_cls
            risk_levels[d] = self._determine_risk_level(cal_p, t_opt)

        cgm_status = "FULL_MEASURED_CGM" if cgm_supplied_count == 5 else ("PARTIAL_MEASURED_CGM" if cgm_supplied_count > 0 else "IMPUTED_NO_CGM")

        return {
            "expert": "Wearable_v4",
            "cgm_status": cgm_status,
            "cgm_supplied_count": cgm_supplied_count,
            "raw_probabilities": raw_probs,
            "calibrated_probabilities": calibrated_probs,
            "predictions": binary_preds,
            "thresholds": thresholds,
            "risk_levels": risk_levels,
            "supplied_features": supplied_features,
            "imputed_features": imputed_features,
            "scaled_input": X_scaled_dict["Type2_Diabetes"],
            "raw_input": input_dict
        }



    def predict_gut(self, input_dict: dict) -> dict:
        """
        Executes Gut expert model (40 Species Taxa + 9 Derived Ecological Indices = 49 Features).
        Automatically computes missing ecological indices from 40 species abundances if not provided.
        """
        if not self.gut_payload:
            raise RuntimeError("Gut payload is not loaded.")

        features = self.gut_payload["features"]
        medians = self.gut_payload["medians"]
        scalers = self.gut_payload.get("scalers", self.gut_payload.get("scaler"))
        models = self.gut_payload["models"]
        calibrators = self.gut_payload.get("calibrators", None)
        thresholds = self.gut_payload.get("thresholds", {d: 0.5 for d in DISEASES})

        # Strip metadata/leakage fields: Patient_ID, Age, Gender, disease labels
        clean_input = {k: v for k, v in input_dict.items() if k not in ("Patient_ID", "Age", "Gender", "Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD")}

        # Check if derived indices need computation
        indices_dict = _compute_v4_gut_indices(clean_input)
        for idx_key, idx_val in indices_dict.items():
            if idx_key not in clean_input or clean_input[idx_key] is None:
                clean_input[idx_key] = idx_val

        feature_vals = []
        imputed_features = []
        supplied_features = []

        for f in features:
            val = clean_input.get(f, None)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                med_val = float(medians[f]) if isinstance(medians, (pd.Series, dict)) else float(medians)
                feature_vals.append(med_val)
                imputed_features.append(f)
            else:
                try:
                    num_val = float(val)
                    feature_vals.append(num_val)
                    supplied_features.append(f)
                except (ValueError, TypeError):
                    med_val = float(medians[f]) if isinstance(medians, (pd.Series, dict)) else float(medians)
                    feature_vals.append(med_val)
                    imputed_features.append(f)

        df_raw = pd.DataFrame([feature_vals], columns=features)
        
        # Transform using scalers (dict or single transformer)
        if isinstance(scalers, dict):
            X_scaled_dict = {d: scalers[d].transform(df_raw) for d in DISEASES}
        else:
            X_scaled_single = scalers.transform(df_raw)
            X_scaled_dict = {d: X_scaled_single for d in DISEASES}

        raw_probs = {}
        calibrated_probs = {}
        binary_preds = {}
        risk_levels = {}

        for i, d in enumerate(DISEASES):
            clf = models[d] if isinstance(models, dict) else models[i]
            t_opt = thresholds[d] if isinstance(thresholds, dict) else 0.5
            X_sc = X_scaled_dict[d]
            df_sc = pd.DataFrame(X_sc, columns=features)

            raw_p = float(clf.predict_proba(df_sc)[0, 1])
            if calibrators and d in calibrators and calibrators[d] is not None:
                cal_p = float(calibrators[d].transform([raw_p])[0])
            else:
                cal_p = raw_p

            pred_cls = int(cal_p >= t_opt)

            raw_probs[d] = round(raw_p, 4)
            calibrated_probs[d] = round(cal_p, 4)
            binary_preds[d] = pred_cls
            risk_levels[d] = self._determine_risk_level(cal_p, t_opt)

        return {
            "expert": "Gut_v4",
            "raw_probabilities": raw_probs,
            "calibrated_probabilities": calibrated_probs,
            "predictions": binary_preds,
            "thresholds": thresholds,
            "risk_levels": risk_levels,
            "supplied_features": supplied_features,
            "imputed_features": imputed_features,
            "scaled_input": X_scaled_dict["Type2_Diabetes"],
            "raw_input": clean_input
        }

    def _determine_risk_level(self, prob: float, threshold: float) -> str:
        if prob < threshold * 0.7:
            return "Low Risk"
        elif prob < threshold:
            return "Borderline Risk"
        elif prob < threshold * 1.3:
            return "Moderate Risk"
        else:
            return "High Risk"
