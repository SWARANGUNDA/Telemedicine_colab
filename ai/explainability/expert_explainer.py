"""
explainer.py — Explainable AI (SHAP) Engine.

Integrates SHAP (SHapley Additive exPlanations) independently for each expert.

Provides:
- GLOBAL EXPLANATION: Which features generally drive predictions across the dataset?
- PATIENT-LEVEL EXPLANATION: Which features drove this specific patient's prediction?

SHAP explains model behavior and feature attributions.
It does NOT prove causal biological effects.
"""

import logging
import warnings
from typing import Any, Dict, List
import numpy as np
import pandas as pd
import shap

# Suppress benign sklearn feature name warnings on array input during SHAP inference
warnings.filterwarnings("ignore", message=".*X does not have valid feature names.*", category=UserWarning)

from ai.config import expert_config as config

logger = logging.getLogger("expert_models.explainer")


class ExpertExplainer:
    """SHAP Explainer wrapper for expert model interpretability."""

    def __init__(self, fitted_model_dict: Dict[str, Any], feature_names: List[str]):
        """
        Args:
            fitted_model_dict: Map of disease ➔ fitted single-disease estimator.
            feature_names: List of predictor feature names in exact ordering.
        """
        self.fitted_model_dict = fitted_model_dict
        self.feature_names = feature_names
        self.explainers: Dict[str, shap.TreeExplainer] = {}

    def fit_explainers(self, X_background: np.ndarray):
        """Fit SHAP TreeExplainers for each target disease estimator."""
        for disease, model in self.fitted_model_dict.items():
            try:
                explainer = shap.TreeExplainer(model)
                self.explainers[disease] = explainer
                logger.info("Fitted SHAP TreeExplainer for %s", disease)
            except Exception as e:
                logger.warning("Falling back to generic SHAP Explainer for %s: %s", disease, e)
                explainer = shap.Explainer(model.predict_proba, X_background)
                self.explainers[disease] = explainer

    def compute_global_feature_importance(self, X_sample: np.ndarray) -> Dict[str, Dict[str, float]]:
        """Calculate global mean absolute SHAP values per feature for each disease.

        Returns:
            Dict mapping disease name ➔ Dict mapping feature name ➔ mean_abs_shap.
        """
        global_importance = {}

        X_df = pd.DataFrame(X_sample, columns=self.feature_names) if isinstance(X_sample, np.ndarray) and len(self.feature_names) == X_sample.shape[1] else X_sample
        for disease, explainer in self.explainers.items():
            try:
                shap_vals = explainer.shap_values(X_df)
                # Handle binary classifier output lists [shap_neg, shap_pos]
                if isinstance(shap_vals, list):
                    shap_vals = shap_vals[1]

                mean_abs = np.mean(np.abs(shap_vals), axis=0)
                feat_imp = {
                    feat: round(float(val), 4)
                    for feat, val in zip(self.feature_names, mean_abs)
                }
                # Sort descending
                sorted_imp = dict(sorted(feat_imp.items(), key=lambda x: x[1], reverse=True))
                global_importance[disease] = sorted_imp
            except Exception as e:
                logger.warning("Error computing SHAP global importance for %s: %s", disease, e)
                global_importance[disease] = {}

        return global_importance

    def explain_patient_prediction(
        self,
        patient_features_array: np.ndarray,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Generate patient-level (local) SHAP attributions for a single patient sample.

        Args:
            patient_features_array: 1D or 2D array representing a single patient (1, n_features).
            top_k: Number of top driving features to highlight.

        Returns:
            Dict containing top positive & negative risk drivers per disease.
        """
        if patient_features_array.ndim == 1:
            patient_features_array = patient_features_array.reshape(1, -1)

        patient_df = pd.DataFrame(patient_features_array, columns=self.feature_names) if isinstance(patient_features_array, np.ndarray) and len(self.feature_names) == patient_features_array.shape[1] else patient_features_array

        local_explanations = {}

        for disease, explainer in self.explainers.items():
            try:
                shap_vals = explainer.shap_values(patient_df)
                if isinstance(shap_vals, list):
                    shap_vals = shap_vals[1]

                sample_shap = shap_vals[0]  # 1D array of feature attributions
                sample_vals = patient_features_array[0]

                drivers = []
                for feat, s_val, f_val in zip(self.feature_names, sample_shap, sample_vals):
                    drivers.append({
                        "feature": feat,
                        "shap_attribution": round(float(s_val), 4),
                        "feature_value": round(float(f_val), 2) if isinstance(f_val, (int, float)) else str(f_val)
                    })

                # Sort by absolute SHAP impact
                drivers.sort(key=lambda x: abs(x["shap_attribution"]), reverse=True)

                local_explanations[disease] = {
                    "top_risk_drivers": drivers[:top_k],
                    "disclaimer": "Model attribution indicates relative feature influence on this prediction. SHAP values do not prove causal biological effects."
                }
            except Exception as e:
                logger.warning("Error explaining patient prediction for %s: %s", disease, e)
                local_explanations[disease] = {"error": str(e)}

        return local_explanations
