"""
preprocessing.py — Leakage-Safe Feature Preprocessing Pipeline.

Strictly fit ONLY on the training split (Split == 'train').
Handles:
- Categorical encoding (Gender: Male=1, Female=0)
- Preserving NaNs for GBDT models (XGBoost, LightGBM, CatBoost)
- Median imputation and scaling for complete-data models (Random Forest, Logistic Regression)
- Enforcing exact schema feature ordering
"""

import logging
from typing import List, Optional, Union
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger("expert_models.preprocessing")


class ExpertPreprocessor:
    """Leakage-safe preprocessor for expert model predictors."""

    def __init__(
        self,
        feature_order: List[str],
        preserve_nans: bool = True,
        scale_numeric: bool = False
    ):
        self.feature_order = feature_order
        self.preserve_nans = preserve_nans
        self.scale_numeric = scale_numeric
        self.imputer: Optional[SimpleImputer] = None
        self.scaler: Optional[StandardScaler] = None
        self.is_fitted: bool = False

    def _encode_categoricals(self, X: pd.DataFrame) -> pd.DataFrame:
        """Encode binary and categorical variables cleanly."""
        X_out = X.copy()
        if "Gender" in X_out.columns:
            gender_series = X_out["Gender"].astype(str).str.capitalize()
            X_out["Gender"] = gender_series.map({"Male": 1.0, "Female": 0.0}).fillna(0.5)

        # Convert boolean / binary columns to float
        for col in X_out.columns:
            if X_out[col].dtype == object or X_out[col].dtype == bool:
                X_out[col] = pd.to_numeric(X_out[col], errors="coerce")

        return X_out

    def fit(self, X_train: pd.DataFrame) -> "ExpertPreprocessor":
        """Fit preprocessor strictly on training DataFrame.

        Args:
            X_train: Training predictor DataFrame.

        Returns:
            self
        """
        logger.info("Fitting ExpertPreprocessor on training data (n=%d)", len(X_train))
        X_proc = X_train[self.feature_order].copy()
        X_proc = self._encode_categoricals(X_proc)

        if not self.preserve_nans:
            self.imputer = SimpleImputer(strategy="median")
            self.imputer.fit(X_proc)

        if self.scale_numeric:
            self.scaler = StandardScaler()
            if self.imputer is not None:
                X_imp = self.imputer.transform(X_proc)
                self.scaler.fit(X_imp)
            else:
                self.scaler.fit(X_proc.fillna(0))

        self.is_fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transform input predictor DataFrame using fitted pipeline.

        Args:
            X: Predictor DataFrame.

        Returns:
            2D numpy array of preprocessed features.
        """
        if not self.is_fitted:
            raise RuntimeError("ExpertPreprocessor must be fitted on training data before calling transform()")

        X_proc = X[self.feature_order].copy()
        X_proc = self._encode_categoricals(X_proc)

        if not self.preserve_nans and self.imputer is not None:
            arr = self.imputer.transform(X_proc)
        else:
            arr = X_proc.values.astype(np.float64)

        if self.scale_numeric and self.scaler is not None:
            arr = self.scaler.transform(arr)

        return arr

    def fit_transform(self, X_train: pd.DataFrame) -> np.ndarray:
        """Fit on training DataFrame and return transformed numpy array."""
        return self.fit(X_train).transform(X_train)
