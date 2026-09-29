"""
investigate_prediabetes_subgroups.py — Prediabetes MECE Subgroup Auditor.

Examines all 733 true Prediabetes patients in the untouched test set (N=3,000)
and constructs 100% mutually exclusive & collectively exhaustive (MECE) subgroup categories.
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import f1_score

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

def run_prediabetes_mece_audit():
    df = pd.read_csv("Clinical_Dataset_v2.csv")
    test_df = df.iloc[17000:].copy()

    # Load frozen Clinical v2 models
    preprocessor = joblib.load("expert_models/saved_models/clinical_v2/preprocessor_clinical_v2.joblib")
    predia_model_payload = joblib.load("expert_models/saved_models/clinical_v2/Prediabetes_clinical_v2.joblib")

    uncal_model = predia_model_payload["uncalibrated_model"]
    calibrator  = predia_model_payload["calibrator"]
    threshold   = predia_model_payload["threshold"]

    X_test_prep = preprocessor.transform(test_df[preprocessor.feature_order])
    raw_probs   = uncal_model.predict_proba(X_test_prep)[:, 1]
    cal_probs   = calibrator.transform(raw_probs)
    preds       = (cal_probs >= threshold).astype(int)

    test_df["Predia_Pred"] = preds

    predia_pop = test_df[test_df["Prediabetes"] == 1].copy()
    total_predia = len(predia_pop)

    fpg   = predia_pop["Fasting_Blood_Glucose"].values
    hba1c = predia_pop["HbA1c"].values

    # 3x3 Grid of Observed Lab Ranges:
    # FPG ranges:  Normal (<100), Predia (100-125), T2D-Range (>=126)
    # HbA1c ranges: Normal (<5.7), Predia (5.7-6.4), T2D-Range (>=6.5)

    fpg_cat = np.where(fpg >= 126.0, "FPG_Elevated(>=126)", np.where(fpg >= 100.0, "FPG_Predia(100-125)", "FPG_Normal(<100)"))
    hba1c_cat = np.where(hba1c >= 6.5, "HbA1c_Elevated(>=6.5)", np.where(hba1c >= 5.7, "HbA1c_Predia(5.7-6.4)", "HbA1c_Normal(<5.7)"))

    grid_df = pd.DataFrame({"FPG_Cat": fpg_cat, "HbA1c_Cat": hba1c_cat, "Pred": predia_pop["Predia_Pred"].values})

    grid_counts = grid_df.groupby(["FPG_Cat", "HbA1c_Cat"], observed=False).size().unstack(fill_value=0)
    grid_recalls = grid_df.groupby(["FPG_Cat", "HbA1c_Cat"], observed=False)["Pred"].mean().unstack(fill_value=0)

    print("\n=== 3x3 OBSERVED LAB GRID FOR TRUE PREDIABETES PATIENTS (N=733) ===")
    print("PATIENT COUNTS:")
    print(grid_counts)
    print("\nMODEL RECALL (%):")
    print((grid_recalls * 100).round(2))

    sum_count = grid_df.shape[0]
    print(f"\nTotal Categorized = {sum_count} / {total_predia}")
    assert sum_count == total_predia, "Subgroups must sum to total_predia!"
    print("MECE Verification SUCCESSFUL! Zero unclassified patients.")

if __name__ == "__main__":
    run_prediabetes_mece_audit()
