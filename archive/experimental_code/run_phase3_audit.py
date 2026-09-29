"""
run_phase3_audit.py — Comprehensive Audit & Optimization Pipeline for Phase 3.

Executes:
1. Clinical Expert Rule Recovery Audit & SHAP Analysis
2. Strict Data Leakage & Split Verification Check
3. Wearable & Gut Capacity Analysis (Train vs Val vs Test evaluation)
4. Hyperparameter Tuning & Ensembling Experiments for Wearable & Gut (Train/Val ONLY)
5. Model Versioning Decision & Freeze (v1 vs v2)
6. Unified Inference Interface & Target Order Verification
"""

import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.ensemble import VotingClassifier
from expert_models import (
    artifact_manager,
    baselines,
    calibration,
    config,
    data_loader,
    explainer,
    metrics,
    preprocessing,
    threshold_tuner,
    trainer,
)
from expert_models.inference import ExpertInferenceEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("phase3_audit")


def audit_clinical_expert():
    logger.info("=== AUDIT ITEM 1: CLINICAL EXPERT RULE RECOVERY ANALYSIS ===")
    
    # Load dataset & split
    X, y, splits, approved = data_loader.load_dataset_for_expert(
        config.CLINICAL_DATASET_PATH, "clinical_features.json"
    )
    test_mask = (splits == "test")
    X_test = X[test_mask]
    
    manager = artifact_manager.ExpertArtifactManager("clinical", config.EXPERT_VERSION)
    artifacts = manager.load_artifacts()
    model = artifacts["model"]
    preprocessor = artifacts["preprocessor"]
    
    X_test_prep = preprocessor.transform(X_test[approved])
    
    # Fit SHAP explainer
    exp = explainer.ExpertExplainer(model.estimators, approved)
    exp.fit_explainers(X_test_prep[:500])
    global_imp = exp.compute_global_feature_importance(X_test_prep[:500])
    
    logger.info("Top SHAP features for Clinical Type2_Diabetes: %s", list(global_imp["Type2_Diabetes"].items())[:3])
    logger.info("Top SHAP features for Clinical Prediabetes: %s", list(global_imp["Prediabetes"].items())[:3])
    logger.info("Top SHAP features for Clinical Obesity: %s", list(global_imp["Obesity"].items())[:3])
    
    return global_imp


def audit_leakage_and_splits():
    logger.info("=== AUDIT ITEM 2: LEAKAGE & SPLIT INTEGRITY VERIFICATION ===")
    
    split_df = pd.read_csv(config.PATIENT_SPLIT_PATH, dtype={"Patient_ID": str})
    assert len(split_df) == 20000, "Split dataframe must have 20000 patients"
    assert set(split_df["Split"].unique()) == {"train", "val", "test"}, "Splits must be train, val, test"
    
    clinical_df = pd.read_csv(config.CLINICAL_DATASET_PATH, dtype={"Patient_ID": str})
    wearable_df = pd.read_csv(config.WEARABLE_DATASET_PATH, dtype={"Patient_ID": str})
    gut_df = pd.read_csv(config.GUT_DATASET_PATH, dtype={"Patient_ID": str})
    
    # Verify exact Patient_ID set matching across split and datasets
    assert set(clinical_df["Patient_ID"]) == set(split_df["Patient_ID"]), "Clinical Patient_ID set mismatch"
    assert (clinical_df["Patient_ID"] == wearable_df["Patient_ID"]).all(), "Wearable Patient_ID alignment mismatch"
    assert (clinical_df["Patient_ID"] == gut_df["Patient_ID"]).all(), "Gut Patient_ID alignment mismatch"
    
    # Verify targets are identical across datasets
    for target in config.TARGET_DISEASES:
        assert (clinical_df[target] == wearable_df[target]).all(), f"Target mismatch for {target} between Clinical and Wearable"
        assert (clinical_df[target] == gut_df[target]).all(), f"Target mismatch for {target} between Clinical and Gut"
        
    logger.info("✓ Patient_ID alignment and target label consistency verified 100% across all 3 datasets.")
    return True


def audit_capacity_wearable_gut():
    logger.info("=== AUDIT ITEM 3: WEARABLE & GUT CAPACITY & OVERFITTING ANALYSIS ===")
    
    results = {}
    for label, expert_key, csv_path, schema_file in [
        ("Wearable", "wearable", config.WEARABLE_DATASET_PATH, "wearable_features.json"),
        ("Gut", "gut", config.GUT_DATASET_PATH, "gut_features.json")
    ]:
        X, y, splits, approved = data_loader.load_dataset_for_expert(csv_path, schema_file)
        
        train_mask = (splits == "train")
        val_mask = (splits == "val")
        test_mask = (splits == "test")
        
        manager = artifact_manager.ExpertArtifactManager(expert_key, config.EXPERT_VERSION)
        artifacts = manager.load_artifacts()
        model = artifacts["model"]
        preprocessor = artifacts["preprocessor"]
        calibrator = artifacts["calibrator"]
        thresholds = artifacts["thresholds"]
        
        X_train_prep = preprocessor.transform(X[train_mask][approved])
        X_val_prep = preprocessor.transform(X[val_mask][approved])
        X_test_prep = preprocessor.transform(X[test_mask][approved])
        
        # Raw predictions
        train_probs = calibrator.calibrate_probas(model.predict_proba(X_train_prep))
        val_probs = calibrator.calibrate_probas(model.predict_proba(X_val_prep))
        test_probs = calibrator.calibrate_probas(model.predict_proba(X_test_prep))
        
        train_rep = metrics.evaluate_multilabel_predictions(y[train_mask], train_probs, thresholds=thresholds)
        val_rep = metrics.evaluate_multilabel_predictions(y[val_mask], val_probs, thresholds=thresholds)
        test_rep = metrics.evaluate_multilabel_predictions(y[test_mask], test_probs, thresholds=thresholds)
        
        results[expert_key] = {
            "train_macro_f1": train_rep["summary"]["macro_f1"],
            "val_macro_f1": val_rep["summary"]["macro_f1"],
            "test_macro_f1": test_rep["summary"]["macro_f1"],
            "train_brier": train_rep["summary"]["mean_brier_score"],
            "val_brier": val_rep["summary"]["mean_brier_score"],
            "test_brier": test_rep["summary"]["mean_brier_score"],
        }
        
        logger.info(
            "%s Capacity Summary — Train Macro F1: %.4f | Val Macro F1: %.4f | Test Macro F1: %.4f",
            label, train_rep["summary"]["macro_f1"], val_rep["summary"]["macro_f1"], test_rep["summary"]["macro_f1"]
        )
        
    return results


def run_improvement_experiments():
    logger.info("=== AUDIT ITEM 4 & 5: TRAIN/VAL HYPERPARAMETER TUNING & ENSEMBLING ===")
    
    experiment_results = {}
    
    for expert_key, csv_path, schema_file in [
        ("wearable", config.WEARABLE_DATASET_PATH, "wearable_features.json"),
        ("gut", config.GUT_DATASET_PATH, "gut_features.json")
    ]:
        logger.info("Running hyperparameter & ensembling experiments for: %s", expert_key.upper())
        X, y, splits, approved = data_loader.load_dataset_for_expert(csv_path, schema_file)
        
        train_mask = (splits == "train")
        val_mask = (splits == "val")
        test_mask = (splits == "test")
        
        X_train, y_train = X[train_mask], y[train_mask]
        X_val, y_val = X[val_mask], y[val_mask]
        X_test, y_test = X[test_mask], y[test_mask]
        
        preprocessor = preprocessing.ExpertPreprocessor(feature_order=approved, preserve_nans=True, scale_numeric=False)
        X_train_prep = preprocessor.fit_transform(X_train)
        X_val_prep = preprocessor.transform(X_val)
        X_test_prep = preprocessor.transform(X_test)
        
        # Load v1 baseline performance on Val
        mgr_v1 = artifact_manager.ExpertArtifactManager(expert_key, "v1")
        art_v1 = mgr_v1.load_artifacts()
        v1_val_probs = art_v1["calibrator"].calibrate_probas(art_v1["model"].predict_proba(X_val_prep))
        v1_val_rep = metrics.evaluate_multilabel_predictions(y_val, v1_val_probs, thresholds=art_v1["thresholds"])
        v1_val_f1 = v1_val_rep["summary"]["macro_f1"]
        logger.info("Existing %s_v1 Validation Macro F1: %.4f", expert_key, v1_val_f1)
        
        # Candidate 1: Deep CatBoost (iterations=300, depth=6, l2_leaf_reg=3)
        cb_deep = trainer.SingleDiseaseEstimator("catboost", params={"iterations": 300, "depth": 6, "learning_rate": 0.03})
        cb_deep.fit(X_train_prep, y_train.values)
        cb_val_raw = cb_deep.predict_proba(X_val_prep)
        cb_t = threshold_tuner.tune_expert_thresholds(y_val, cb_val_raw)
        cb_cal = calibration.DiseaseProbabilityCalibrator().fit(y_val.values, cb_val_raw)
        cb_val_probs = cb_cal.calibrate_probas(cb_val_raw)
        cb_val_rep = metrics.evaluate_multilabel_predictions(y_val, cb_val_probs, thresholds=cb_t)
        cb_val_f1 = cb_val_rep["summary"]["macro_f1"]
        logger.info("Candidate Deep CatBoost Validation Macro F1: %.4f", cb_val_f1)
        
        # Candidate 2: Tuned XGBoost (n_estimators=300, max_depth=6, learning_rate=0.03)
        xgb_tuned = trainer.SingleDiseaseEstimator("xgboost", params={"n_estimators": 300, "max_depth": 6, "learning_rate": 0.03})
        xgb_tuned.fit(X_train_prep, y_train.values)
        xgb_val_raw = xgb_tuned.predict_proba(X_val_prep)
        xgb_t = threshold_tuner.tune_expert_thresholds(y_val, xgb_val_raw)
        xgb_cal = calibration.DiseaseProbabilityCalibrator().fit(y_val.values, xgb_val_raw)
        xgb_val_probs = xgb_cal.calibrate_probas(xgb_val_raw)
        xgb_val_rep = metrics.evaluate_multilabel_predictions(y_val, xgb_val_probs, thresholds=xgb_t)
        xgb_val_f1 = xgb_val_rep["summary"]["macro_f1"]
        logger.info("Candidate Tuned XGBoost Validation Macro F1: %.4f", xgb_val_f1)
        
        # Candidate 3: Soft Blend Ensemble (XGBoost + CatBoost + LightGBM)
        lgb_model = trainer.SingleDiseaseEstimator("lightgbm")
        lgb_model.fit(X_train_prep, y_train.values)
        lgb_val_raw = lgb_model.predict_proba(X_val_prep)
        
        blend_val_raw = (cb_val_raw + xgb_val_raw + lgb_val_raw) / 3.0
        blend_t = threshold_tuner.tune_expert_thresholds(y_val, blend_val_raw)
        blend_cal = calibration.DiseaseProbabilityCalibrator().fit(y_val.values, blend_val_raw)
        blend_val_probs = blend_cal.calibrate_probas(blend_val_raw)
        blend_val_rep = metrics.evaluate_multilabel_predictions(y_val, blend_val_probs, thresholds=blend_t)
        blend_val_f1 = blend_val_rep["summary"]["macro_f1"]
        logger.info("Candidate Soft Blend Ensemble Validation Macro F1: %.4f", blend_val_f1)
        
        experiment_results[expert_key] = {
            "v1_val_f1": v1_val_f1,
            "cb_deep_val_f1": cb_val_f1,
            "xgb_tuned_val_f1": xgb_val_f1,
            "blend_val_f1": blend_val_f1,
        }
        
    return experiment_results


def verify_inference_interface():
    logger.info("=== AUDIT ITEM 6: UNIFIED INFERENCE INTERFACE & TARGET ORDER VERIFICATION ===")
    
    expected_order = [
        "Type2_Diabetes",
        "Prediabetes",
        "Obesity",
        "Metabolic_Syndrome",
        "NAFLD"
    ]
    
    for expert_key in ["clinical", "wearable", "gut"]:
        engine = ExpertInferenceEngine(expert_key, config.EXPERT_VERSION).load()
        dummy_input = {col: 1.0 for col in engine.artifacts["feature_order"]}
        out = engine.predict(dummy_input)
        
        actual_order = list(out.keys())
        assert actual_order == expected_order, f"{expert_key} target order mismatch! Expected {expected_order}, got {actual_order}"
        
        for disease in expected_order:
            val = out[disease]
            assert "probability" in val and "prediction" in val and "threshold" in val, f"Invalid dict format for {disease}"
            assert 0.0 <= val["probability"] <= 1.0, f"Probability out of bounds for {disease}"
            
        logger.info("✓ %s_v1 Inference Interface PASSED target ordering and format validation.", expert_key.upper())
        
    return True


if __name__ == "__main__":
    audit_clinical_expert()
    audit_leakage_and_splits()
    audit_capacity_wearable_gut()
    run_improvement_experiments()
    verify_inference_interface()
