"""
audit_multimodal_v3_dataset.py — Comprehensive Stage B QC Engine for Multimodal Dataset v3.2.2

Audits Sections A through I:
A. Dataset Integrity
B. Target Analysis
C. Clinical Audit
D. Wearable Audit
E. Gut Audit
F. Cross-Modal Audit
G. Shortcut/Leakage Audit
H. Missingness Leakage Audit
I. Final QC Verdict
"""

import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("multimodal_v3_qc")

DATA_DIR = Path("data/multimodal_v3")

def run_stage_b_qc():
    logger.info("==================================================================")
    logger.info("  STARTING STAGE B COMPREHENSIVE QC AUDIT FOR MULTIMODAL V3.2.2  ")
    logger.info("==================================================================")

    clin_df = pd.read_csv(DATA_DIR / "clinical_v3.csv")
    wear_std_df = pd.read_csv(DATA_DIR / "wearable_standard_v3.csv")
    wear_cgm_df = pd.read_csv(DATA_DIR / "wearable_cgm_v3.csv")
    gut_df = pd.read_csv(DATA_DIR / "gut_v3.csv")
    labels_df = pd.read_csv(DATA_DIR / "labels_v3.csv")
    split_df = pd.read_csv(DATA_DIR / "split_manifest_v3.csv")

    qc_summary = {}

    # ------------------------------------------------------------------
    # SECTION A: DATASET INTEGRITY
    # ------------------------------------------------------------------
    logger.info("--- SECTION A: DATASET INTEGRITY ---")
    dims = {
        "clinical_v3": clin_df.shape,
        "wearable_standard_v3": wear_std_df.shape,
        "wearable_cgm_v3": wear_cgm_df.shape,
        "gut_v3": gut_df.shape,
        "labels_v3": labels_df.shape,
        "split_manifest_v3": split_df.shape
    }

    dup_ids = sum([df["Patient_ID"].duplicated().sum() for df in [clin_df, wear_std_df, wear_cgm_df, gut_df, labels_df, split_df]])
    
    # Check 100% ID alignment across files
    id_align = (
        np.array_equal(clin_df["Patient_ID"], wear_std_df["Patient_ID"]) and
        np.array_equal(clin_df["Patient_ID"], wear_cgm_df["Patient_ID"]) and
        np.array_equal(clin_df["Patient_ID"], gut_df["Patient_ID"]) and
        np.array_equal(clin_df["Patient_ID"], labels_df["Patient_ID"]) and
        np.array_equal(clin_df["Patient_ID"], split_df["Patient_ID"])
    )

    split_counts = split_df["Split"].value_counts().to_dict()

    nan_pcts = {}
    for name, df in [("clinical", clin_df), ("wear_std", wear_std_df), ("wear_cgm", wear_cgm_df), ("gut", gut_df)]:
        nan_pcts[name] = df.isnull().mean().round(4).to_dict()

    # Impossible value checks (e.g. negative height/weight, steps > 50k, exercise > 7)
    imp_vals = 0
    if (clin_df["Height"] <= 0).sum() > 0 or (clin_df["Weight"] <= 0).sum() > 0: imp_vals += 1
    if (wear_std_df["Exercise_Frequency_Days"] > 7).sum() > 0 or (wear_std_df["Exercise_Frequency_Days"] < 0).sum() > 0: imp_vals += 1

    qc_summary["Section_A_Integrity"] = {
        "verdict": "PASS" if (dup_ids == 0 and id_align and imp_vals == 0) else "FAIL",
        "file_dimensions": dims,
        "duplicate_patient_ids": dup_ids,
        "cross_file_id_alignment": id_align,
        "split_counts": split_counts,
        "impossible_values_count": imp_vals,
        "nan_percentages": nan_pcts
    }
    logger.info(f"Section A Verdict: {qc_summary['Section_A_Integrity']['verdict']}")

    # ------------------------------------------------------------------
    # SECTION B: TARGET ANALYSIS
    # ------------------------------------------------------------------
    logger.info("--- SECTION B: TARGET ANALYSIS ---")
    diseases = ["Type2_Diabetes", "Prediabetes", "Obesity", "Metabolic_Syndrome", "NAFLD"]
    prevs = {d: round(float(labels_df[d].mean()), 4) for d in diseases}

    co_occ = labels_df[diseases].T.dot(labels_df[diseases]).to_dict()
    num_labels_dist = labels_df[diseases].sum(axis=1).value_counts().to_dict()
    t2d_predia_overlap = int(((labels_df["Type2_Diabetes"] == 1) & (labels_df["Prediabetes"] == 1)).sum())

    qc_summary["Section_B_Targets"] = {
        "verdict": "PASS" if t2d_predia_overlap == 0 else "FAIL",
        "prevalence": prevs,
        "co_occurrence_matrix": co_occ,
        "labels_per_patient_distribution": num_labels_dist,
        "t2d_prediabetes_overlap_count": t2d_predia_overlap
    }
    logger.info(f"Section B Verdict: {qc_summary['Section_B_Targets']['verdict']} (Prevalences: {prevs})")

    # ------------------------------------------------------------------
    # SECTION C: CLINICAL AUDIT & RULE DISAGREEMENT
    # ------------------------------------------------------------------
    logger.info("--- SECTION C: CLINICAL AUDIT ---")
    # Disagreement rates with simple deterministic rules
    rule_t2d = ((clin_df["Fasting_Blood_Glucose"] >= 126) | (clin_df["HbA1c"] >= 6.5)).astype(int)
    disagree_t2d = round(float(np.mean(rule_t2d != labels_df["Type2_Diabetes"])), 4)

    rule_obese = (clin_df["BMI"] >= 30.0).astype(int)
    disagree_obese = round(float(np.mean(rule_obese != labels_df["Obesity"])), 4)

    # ATP III Criteria Check
    c1 = (clin_df["Waist_Circumference"] >= np.where(clin_df["Gender"] == 1, 102, 88))
    c2 = (clin_df["Triglycerides"] >= 150)
    c3 = (clin_df["HDL"] < np.where(clin_df["Gender"] == 1, 40, 50))
    c4 = ((clin_df["Systolic_BP"] >= 130) | (clin_df["Diastolic_BP"] >= 85))
    c5 = (clin_df["Fasting_Blood_Glucose"] >= 100)
    rule_mets = ((c1.astype(int) + c2.astype(int) + c3.astype(int) + c4.astype(int) + c5.astype(int)) >= 3).astype(int)
    disagree_mets = round(float(np.mean(rule_mets != labels_df["Metabolic_Syndrome"])), 4)

    qc_summary["Section_C_Clinical"] = {
        "verdict": "PASS" if (disagree_t2d > 0.03 and disagree_obese > 0.03 and disagree_mets > 0.03) else "PASS WITH WARNING",
        "rule_disagreement_rates": {
            "T2D_rule_disagreement": disagree_t2d,
            "Obesity_rule_disagreement": disagree_obese,
            "MetS_rule_disagreement": disagree_mets
        }
    }
    logger.info(f"Section C Verdict: {qc_summary['Section_C_Clinical']['verdict']} (Disagreements: T2D={disagree_t2d}, Obese={disagree_obese}, MetS={disagree_mets})")

    # ------------------------------------------------------------------
    # SECTION D: WEARABLE AUDIT
    # ------------------------------------------------------------------
    logger.info("--- SECTION D: WEARABLE AUDIT ---")
    cgm_valid = wear_cgm_df.dropna(subset=["CGM_Time_In_Range", "CGM_Time_Above_Range", "CGM_Time_Below_Range"])
    cgm_sums = cgm_valid["CGM_Time_In_Range"] + cgm_valid["CGM_Time_Above_Range"] + cgm_valid["CGM_Time_Below_Range"]
    cgm_sum_pass = np.allclose(cgm_sums, 100.0, atol=1e-2)

    cgm_avail_rate = round(float(wear_cgm_df["CGM_Average_Glucose"].notnull().mean()), 4)

    qc_summary["Section_D_Wearable"] = {
        "verdict": "PASS" if cgm_sum_pass else "FAIL",
        "cgm_availability_rate": cgm_avail_rate,
        "cgm_simplex_normalization_pass": cgm_sum_pass
    }
    logger.info(f"Section D Verdict: {qc_summary['Section_D_Wearable']['verdict']} (CGM Avail={cgm_avail_rate})")

    # ------------------------------------------------------------------
    # SECTION E: GUT AUDIT
    # ------------------------------------------------------------------
    logger.info("--- SECTION E: GUT AUDIT ---")
    taxa_20 = [
        "Akkermansia", "Faecalibacterium", "Roseburia", "Bifidobacterium", "Bacteroides",
        "Prevotella", "Ruminococcus", "Blautia", "Collinsella", "Escherichia_Shigella",
        "Coprococcus", "Alistipes", "Subdoligranulum", "Enterococcus", "Eubacterium",
        "Parabacteroides", "Lactobacillus", "Klebsiella", "Streptococcus", "Eggerthella"
    ]
    all_21 = taxa_20 + ["Other_Taxa"]

    gut_valid = gut_df.dropna(subset=all_21)
    gut_sums = gut_valid[all_21].sum(axis=1)
    gut_sum_pass = np.allclose(gut_sums, 100.0, atol=1e-2)

    zero_prevs = {t: round(float((gut_valid[t] == 0.0).mean()), 4) for t in taxa_20}
    seq_fail_rate = round(float(gut_df["Akkermansia"].isnull().mean()), 4)

    qc_summary["Section_E_Gut"] = {
        "verdict": "PASS" if gut_sum_pass else "FAIL",
        "microbiome_composition_sum_pass": gut_sum_pass,
        "sequencing_failure_rate": seq_fail_rate,
        "taxon_zero_prevalences": zero_prevs
    }
    logger.info(f"Section E Verdict: {qc_summary['Section_E_Gut']['verdict']} (Gut Fail={seq_fail_rate})")

    # ------------------------------------------------------------------
    # SECTION F: CROSS-MODAL AUDIT (Shared Physiology Verification v3.2.3)
    # ------------------------------------------------------------------
    logger.info("--- SECTION F: CROSS-MODAL AUDIT (v3.2.3 REVISION) ---")
    
    r_bmi_steps   = round(float(clin_df["BMI"].corr(wear_std_df["Average_Daily_Steps"])), 4)
    r_waist_steps = round(float(clin_df["Waist_Circumference"].corr(wear_std_df["Average_Daily_Steps"])), 4)
    r_bmi_act     = round(float(clin_df["BMI"].corr(wear_std_df["Active_Minutes"])), 4)
    r_fpg_steps   = round(float(clin_df["Fasting_Blood_Glucose"].corr(wear_std_df["Average_Daily_Steps"])), 4)
    r_hba1c_steps = round(float(clin_df["HbA1c"].corr(wear_std_df["Average_Daily_Steps"])), 4)
    r_steps_hrv   = round(float(wear_std_df["Average_Daily_Steps"].corr(wear_std_df["Heart_Rate_Variability_RMSSD"])), 4)
    r_steps_rhr   = round(float(wear_std_df["Average_Daily_Steps"].corr(wear_std_df["Resting_Heart_Rate"])), 4)
    r_steps_sleep = round(float(wear_std_df["Average_Daily_Steps"].corr(wear_std_df["Sleep_Duration_Hours"])), 4)

    r_fpg_akk   = round(float(clin_df["Fasting_Blood_Glucose"].corr(gut_df["Akkermansia"])), 4)
    r_steps_akk = round(float(wear_std_df["Average_Daily_Steps"].corr(gut_df["Akkermansia"])), 4)

    # Complete Clinical <-> Wearable correlation matrix
    clin_cols = ["BMI", "Waist_Circumference", "Fasting_Blood_Glucose", "HbA1c", "Systolic_BP", "Triglycerides"]
    wear_cols = ["Average_Daily_Steps", "Active_Minutes", "Sedentary_Time_Minutes", "Resting_Heart_Rate", "Heart_Rate_Variability_RMSSD"]
    
    clin_wear_corr = {}
    high_corrs = []
    for c_col in clin_cols:
        clin_wear_corr[c_col] = {}
        for w_col in wear_cols:
            val = round(float(clin_df[c_col].corr(wear_std_df[w_col])), 4)
            clin_wear_corr[c_col][w_col] = val
            if abs(val) > 0.75:
                high_corrs.append(f"{c_col} <-> {w_col}: r = {val}")

    qc_summary["Section_F_CrossModal"] = {
        "verdict": "PASS" if len(high_corrs) == 0 else "PASS WITH WARNING",
        "high_cross_modal_correlations_gt_0.75": high_corrs,
        "key_v3_2_3_couplings": {
            "BMI_vs_Steps": r_bmi_steps,
            "Waist_vs_Steps": r_waist_steps,
            "BMI_vs_Active_Minutes": r_bmi_act,
            "FPG_vs_Steps": r_fpg_steps,
            "HbA1c_vs_Steps": r_hba1c_steps,
            "Steps_vs_HRV": r_steps_hrv,
            "Steps_vs_Resting_HR": r_steps_rhr,
            "Steps_vs_Sleep": r_steps_sleep,
            "FPG_vs_Akkermansia": r_fpg_akk,
            "Steps_vs_Akkermansia": r_steps_akk
        },
        "clinical_wearable_correlation_matrix": clin_wear_corr
    }
    logger.info(f"Section F Verdict: {qc_summary['Section_F_CrossModal']['verdict']} (BMI vs Steps = {r_bmi_steps}, Waist vs Steps = {r_waist_steps}, High Corrs > 0.75 = {len(high_corrs)})")

    # ------------------------------------------------------------------
    # SECTION G: SHORTCUT / LEAKAGE AUDIT (Single-Feature ROC-AUC)
    # ------------------------------------------------------------------
    logger.info("--- SECTION G: SHORTCUT & LEAKAGE AUDIT ---")
    single_aucs = {}
    suspicious_aucs = []

    for disease in diseases:
        y_true = labels_df[disease].values
        for feat in ["Fasting_Blood_Glucose", "HbA1c", "BMI", "Systolic_BP", "Triglycerides", "ALT"]:
            x_val = clin_df[feat].fillna(clin_df[feat].median()).values
            auc = roc_auc_score(y_true, x_val)
            auc_clean = round(float(max(auc, 1.0 - auc)), 4)
            single_aucs[f"{feat}_vs_{disease}"] = auc_clean
            if auc_clean >= 0.9500:
                suspicious_aucs.append(f"{feat}_vs_{disease}: {auc_clean}")

    qc_summary["Section_G_Leakage"] = {
        "verdict": "PASS" if len(suspicious_aucs) == 0 else "FAIL",
        "suspicious_auc_count": len(suspicious_aucs),
        "suspicious_aucs": suspicious_aucs,
        "single_feature_aucs": single_aucs
    }
    logger.info(f"Section G Verdict: {qc_summary['Section_G_Leakage']['verdict']} (Suspicious AUCs >= 0.95: {len(suspicious_aucs)})")

    # ------------------------------------------------------------------
    # SECTION H: MISSINGNESS LEAKAGE AUDIT
    # ------------------------------------------------------------------
    logger.info("--- SECTION H: MISSINGNESS LEAKAGE AUDIT ---")
    cgm_miss_indicator = wear_cgm_df["CGM_Average_Glucose"].isnull().astype(int)
    cgm_miss_aucs = {}
    for disease in diseases:
        auc = roc_auc_score(labels_df[disease], cgm_miss_indicator)
        cgm_miss_aucs[disease] = round(float(max(auc, 1.0 - auc)), 4)

    qc_summary["Section_H_MissingnessLeakage"] = {
        "verdict": "PASS" if all(a < 0.75 for a in cgm_miss_aucs.values()) else "PASS WITH WARNING",
        "cgm_missingness_indicator_aucs": cgm_miss_aucs
    }
    logger.info(f"Section H Verdict: {qc_summary['Section_H_MissingnessLeakage']['verdict']} (CGM Missing AUCs: {cgm_miss_aucs})")

    # ------------------------------------------------------------------
    # SECTION I: OVERALL QC VERDICT
    # ------------------------------------------------------------------
    all_verdicts = [v["verdict"] for v in qc_summary.values()]
    final_verdict = "APPROVE FOR MODEL TRAINING" if all("FAIL" not in v for v in all_verdicts) else "REQUIRES GENERATOR CORRECTION"

    qc_summary["Final_Verdict"] = final_verdict
    logger.info("==================================================================")
    logger.info(f"  FINAL STAGE B QC VERDICT: {final_verdict}")
    logger.info("==================================================================")

    def convert_types(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(v) for v in obj]
        return obj

    qc_summary_clean = convert_types(qc_summary)

    with open("multimodal_v3_stage_b_qc_results.json", "w") as f:
        json.dump(qc_summary_clean, f, indent=2)

    return qc_summary_clean

if __name__ == "__main__":
    run_stage_b_qc()
