"""
v3_3_closure_audit.py — Final V3.3 Scientific Closure Audit

Performs:
1. All-pathway test-set evaluation (C,W,G,C+W,C+G,W+G,C+W+G)
2. Glycemic hierarchy audit (T2D/Prediabetes exclusivity, discordance, counterfactuals)
3. High_Adiposity_Risk definition + counterfactual audit
4. Stale Obesity reference scan in v3 runtime
5. Leakage, calibration, feature-order, schema, split alignment, reproducibility
6. B=1000 bootstrap with frozen test predictions
7. Serialized artifact verification
"""

import os, sys, json, hashlib, logging, warnings
sys.path.insert(0, ".")
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import (
    f1_score, precision_score, recall_score, roc_auc_score,
    brier_score_loss, precision_recall_curve, auc as sk_auc
)
from sklearn.calibration import calibration_curve

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("closure_audit")

DATA_DIR = Path("data/multimodal_v3")
DISEASES = ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]

report = {}

# ============================================================
# LOAD DATA & PAYLOADS
# ============================================================
logger.info("=== LOADING DATA & PAYLOADS ===")
labels_df = pd.read_csv(DATA_DIR / "labels_v3.csv")
split_df = pd.read_csv(DATA_DIR / "split_manifest_v3.csv")
clin_df = pd.read_csv(DATA_DIR / "clinical_v3.csv")
wear_std_df = pd.read_csv(DATA_DIR / "wearable_standard_v3.csv")
wear_cgm_df = pd.read_csv(DATA_DIR / "wearable_cgm_v3.csv")
gut_df = pd.read_csv(DATA_DIR / "gut_v3.csv")

clin_payload = joblib.load("expert_models/saved_models/clinical_v3/clinical_v3_payload.joblib")
wear_payload = joblib.load("expert_models/saved_models/wearable_v3/wearable_v3_payload.joblib")
gut_payload = joblib.load("expert_models/saved_models/gut_v3/gut_v3_payload.joblib")

test_mask = (split_df["Split"] == "Test").values
val_mask = (split_df["Split"] == "Val").values
train_mask = (split_df["Split"] == "Train").values

y_te = labels_df[DISEASES].values[test_mask]
y_va = labels_df[DISEASES].values[val_mask]

# Prepare feature matrices
X_c = clin_df[clin_payload["features"]].fillna(clin_payload["medians"]).values
X_w = pd.concat([wear_std_df[wear_payload["features"][:10]], wear_cgm_df[wear_payload["features"][10:]]], axis=1).fillna(wear_payload["medians"]).values
X_g = gut_df[gut_payload["features"]].fillna(gut_payload["medians"]).values

# Generate expert test predictions
def expert_predict(payload, X_subset):
    probs = np.zeros((X_subset.shape[0], 5))
    X_s = payload["scaler"].transform(X_subset)
    for i in range(5):
        raw = payload["models"][i].predict_proba(X_s)[:, 1]
        probs[:, i] = payload["calibrators"][i].transform(raw)
    return probs

test_c = expert_predict(clin_payload, X_c[test_mask])
test_w = expert_predict(wear_payload, X_w[test_mask])
test_g = expert_predict(gut_payload, X_g[test_mask])

# ============================================================
# 1. ALL-PATHWAY TEST-SET EVALUATION
# ============================================================
logger.info("=== SECTION 1: ALL-PATHWAY TEST-SET EVALUATION ===")

def compute_metrics(y_true, probs, thresholds):
    n_d = y_true.shape[1]
    preds = np.zeros_like(y_true)
    for i in range(n_d):
        preds[:, i] = (probs[:, i] >= thresholds[i]).astype(int)
    
    macro_f1 = f1_score(y_true, preds, average='macro')
    micro_f1 = f1_score(y_true, preds, average='micro')
    
    per_disease = {}
    for i, d in enumerate(DISEASES):
        f1 = f1_score(y_true[:, i], preds[:, i])
        prec = precision_score(y_true[:, i], preds[:, i], zero_division=0)
        rec = recall_score(y_true[:, i], preds[:, i], zero_division=0)
        roc = roc_auc_score(y_true[:, i], probs[:, i])
        brier = brier_score_loss(y_true[:, i], probs[:, i])
        prec_curve, rec_curve, _ = precision_recall_curve(y_true[:, i], probs[:, i])
        pr_auc = sk_auc(rec_curve, prec_curve)
        
        # Calibration (ECE)
        try:
            frac_pos, mean_pred = calibration_curve(y_true[:, i], probs[:, i], n_bins=10, strategy='uniform')
            ece = np.mean(np.abs(frac_pos - mean_pred))
        except:
            ece = float('nan')
        
        per_disease[d] = {
            "F1": round(f1, 4), "Precision": round(prec, 4), "Recall": round(rec, 4),
            "ROC_AUC": round(roc, 4), "PR_AUC": round(pr_auc, 4),
            "Brier": round(brier, 4), "ECE": round(ece, 4)
        }
    
    return {
        "Macro_F1": round(macro_f1, 4), "Micro_F1": round(micro_f1, 4),
        "per_disease": per_disease
    }, preds

# Use tuned thresholds from payloads
def get_thresholds(payload, diseases):
    thresholds = []
    for d in diseases:
        t = payload["thresholds"].get(d, payload["thresholds"].get("Obesity", 0.5))
        thresholds.append(t)
    return thresholds

clin_thresholds = get_thresholds(clin_payload, DISEASES)

# For pathway combinations, use simple mean + per-disease threshold tuning on val
def tune_thresholds_on_val(probs_val, y_val):
    thresholds = []
    for i in range(5):
        best_t, best_f1 = 0.5, 0.0
        for t in np.arange(0.1, 0.9, 0.01):
            f1 = f1_score(y_val[:, i], (probs_val[:, i] >= t).astype(int))
            if f1 > best_f1:
                best_f1, best_t = f1, t
        thresholds.append(round(best_t, 2))
    return thresholds

# Val predictions for threshold tuning
val_c = expert_predict(clin_payload, X_c[val_mask])
val_w = expert_predict(wear_payload, X_w[val_mask])
val_g = expert_predict(gut_payload, X_g[val_mask])

pathway_configs = {
    "C": {"test": test_c, "val": val_c},
    "W": {"test": test_w, "val": val_w},
    "G": {"test": test_g, "val": val_g},
    "C+W": {"test": (test_c + test_w) / 2, "val": (val_c + val_w) / 2},
    "C+G": {"test": (test_c + test_g) / 2, "val": (val_c + val_g) / 2},
    "W+G": {"test": (test_w + test_g) / 2, "val": (val_w + val_g) / 2},
    "C+W+G": {"test": (test_c + test_w + test_g) / 3, "val": (val_c + val_w + val_g) / 3},
}

pathway_results = {}
for pw, data in pathway_configs.items():
    thresholds = tune_thresholds_on_val(data["val"], y_va)
    metrics, preds = compute_metrics(y_te, data["test"], thresholds)
    metrics["thresholds"] = {d: t for d, t in zip(DISEASES, thresholds)}
    pathway_results[pw] = metrics
    logger.info(f"  {pw:8s} -> Macro F1={metrics['Macro_F1']:.4f}, Micro F1={metrics['Micro_F1']:.4f}")

report["1_pathway_test_evaluation"] = pathway_results

# C+G vs C delta
logger.info("=== C+G vs C Delta ===")
c_res = pathway_results["C"]["per_disease"]
cg_res = pathway_results["C+G"]["per_disease"]
deltas = {}
for d in DISEASES:
    deltas[d] = {
        "F1_delta": round(cg_res[d]["F1"] - c_res[d]["F1"], 4),
        "ROC_AUC_delta": round(cg_res[d]["ROC_AUC"] - c_res[d]["ROC_AUC"], 4),
        "Brier_delta": round(cg_res[d]["Brier"] - c_res[d]["Brier"], 4),
    }
    logger.info(f"  {d}: F1 delta={deltas[d]['F1_delta']:+.4f}, AUC delta={deltas[d]['ROC_AUC_delta']:+.4f}")

cg_improves = pathway_results["C+G"]["Macro_F1"] > pathway_results["C"]["Macro_F1"]
report["1_cg_vs_c_delta"] = {
    "C_Macro_F1": pathway_results["C"]["Macro_F1"],
    "CG_Macro_F1": pathway_results["C+G"]["Macro_F1"],
    "CG_improves_over_C": cg_improves,
    "per_disease_deltas": deltas
}

# ============================================================
# 2. GLYCEMIC HIERARCHY AUDIT
# ============================================================
logger.info("=== SECTION 2: GLYCEMIC HIERARCHY AUDIT ===")
t2d_col = labels_df["Type2_Diabetes"].values
predm_col = labels_df["Prediabetes"].values

co_occurrence = int(np.sum((t2d_col == 1) & (predm_col == 1)))
total = len(t2d_col)
co_rate = co_occurrence / total

# FPG/HbA1c criteria check
fpg_col = "Fasting_Blood_Glucose" if "Fasting_Blood_Glucose" in clin_df.columns else "FPG"
fpg = clin_df[fpg_col].values
hba1c = clin_df["HbA1c"].values

# Patients with FPG >= 126 OR HbA1c >= 6.5 should be T2D, not Prediabetes
diabetic_criteria = (fpg >= 126) | (hba1c >= 6.5)
prediab_criteria = ((fpg >= 100) & (fpg < 126)) | ((hba1c >= 5.7) & (hba1c < 6.5))

# Discordance: patients meeting diabetes criteria but labeled Prediabetes=1
discord_fpg_t2d = int(np.sum(diabetic_criteria & (t2d_col == 0) & (predm_col == 1)))
discord_total_diabetic = int(np.sum(diabetic_criteria))
discord_rate = discord_fpg_t2d / discord_total_diabetic if discord_total_diabetic > 0 else 0

# Counterfactual monotonicity: FPG sweep
logger.info("  Running FPG/HbA1c counterfactual sweeps...")
base_features = {f: float(clin_payload["medians"][f]) for f in clin_payload["features"]}
base_features["Age"] = 50
base_features["Gender"] = 1
base_features["BMI"] = 28.0

fpg_sweep = [90, 100, 110, 120, 126, 130, 140, 160, 180, 200]
hba1c_sweep = [5.0, 5.5, 5.7, 6.0, 6.2, 6.5, 7.0, 7.5, 8.0]

from expert_models.v3_inference_engine import V3InferenceEngine
engine = V3InferenceEngine()

fpg_results = []
for fpg_val in fpg_sweep:
    inp = base_features.copy()
    inp[fpg_col] = fpg_val
    inp["FPG"] = fpg_val
    res = engine.predict_clinical(inp)
    fpg_results.append({
        "FPG": fpg_val,
        "T2D_prob": res["calibrated_probabilities"]["Type2_Diabetes"],
        "PreDM_prob": res["calibrated_probabilities"]["Prediabetes"]
    })

hba1c_results = []
for hba1c_val in hba1c_sweep:
    inp = base_features.copy()
    inp["HbA1c"] = hba1c_val
    res = engine.predict_clinical(inp)
    hba1c_results.append({
        "HbA1c": hba1c_val,
        "T2D_prob": res["calibrated_probabilities"]["Type2_Diabetes"],
        "PreDM_prob": res["calibrated_probabilities"]["Prediabetes"]
    })

# Check monotonicity
def check_monotonicity(results, key, prob_key):
    probs = [r[prob_key] for r in results]
    violations = sum(1 for i in range(1, len(probs)) if probs[i] < probs[i-1])
    return violations, probs

fpg_t2d_violations, fpg_t2d_probs = check_monotonicity(fpg_results, "FPG", "T2D_prob")
hba1c_t2d_violations, hba1c_t2d_probs = check_monotonicity(hba1c_results, "HbA1c", "T2D_prob")

report["2_glycemic_hierarchy"] = {
    "T2D_Prediabetes_co_occurrence": co_occurrence,
    "co_occurrence_rate": round(co_rate * 100, 4),
    "co_occurrence_PASS": co_occurrence == 0,
    "diabetic_criteria_patients": discord_total_diabetic,
    "discordant_labeled_prediabetes": discord_fpg_t2d,
    "discordance_rate": round(discord_rate * 100, 4),
    "fpg_counterfactual": fpg_results,
    "hba1c_counterfactual": hba1c_results,
    "fpg_T2D_monotonicity_violations": fpg_t2d_violations,
    "hba1c_T2D_monotonicity_violations": hba1c_t2d_violations,
}
logger.info(f"  T2D+PreDM co-occurrence: {co_occurrence} ({co_rate*100:.2f}%)")
logger.info(f"  Glycemic discordance: {discord_fpg_t2d}/{discord_total_diabetic} ({discord_rate*100:.2f}%)")
logger.info(f"  FPG T2D monotonicity violations: {fpg_t2d_violations}")
logger.info(f"  HbA1c T2D monotonicity violations: {hba1c_t2d_violations}")

# ============================================================
# 3. HIGH ADIPOSITY RISK AUDIT
# ============================================================
logger.info("=== SECTION 3: HIGH_ADIPOSITY_RISK DEFINITION AUDIT ===")

bmi_sweep = [20, 22, 25, 27, 28, 29, 30, 31, 32, 35, 40]
bmi_results = []
for bmi_val in bmi_sweep:
    inp = base_features.copy()
    inp["BMI"] = bmi_val
    inp["Waist_Circumference"] = 70 + (bmi_val - 20) * 2.5
    res = engine.predict_clinical(inp)
    bmi_results.append({
        "BMI": bmi_val,
        "HAR_prob": res["calibrated_probabilities"]["High_Adiposity_Risk"],
    })

bmi_har_violations, bmi_har_probs = check_monotonicity(bmi_results, "BMI", "HAR_prob")

# Check v3 frontend/API for "Obesity" in output names
v3_output_files = [
    "expert_models/v3_inference_engine.py",
    "fusion_engine/v3_scientific_router.py",
    "web_platform/backend/api/v3_routes.py",
]
obesity_in_v3_output = {}
for f in v3_output_files:
    if Path(f).exists():
        content = Path(f).read_text(encoding="utf-8", errors="ignore")
        obesity_in_v3_output[f] = '"Obesity"' in content or "'Obesity'" in content

report["3_high_adiposity_risk"] = {
    "bmi_counterfactual": bmi_results,
    "bmi_HAR_monotonicity_violations": bmi_har_violations,
    "obesity_in_v3_output_files": obesity_in_v3_output,
}
logger.info(f"  BMI HAR monotonicity violations: {bmi_har_violations}")
logger.info(f"  Obesity in v3 output files: {obesity_in_v3_output}")

# ============================================================
# 4. STALE OBESITY REFERENCE SCAN
# ============================================================
logger.info("=== SECTION 4: STALE OBESITY REFERENCE SCAN ===")
v3_scan_dirs = [
    "expert_models/v3_inference_engine.py",
    "expert_models/config.py",
    "fusion_engine/v3_scientific_router.py",
    "web_platform/backend/api/v3_routes.py",
    "web_platform/frontend/js/new-analysis.js",
    "web_platform/frontend/js/dashboard.js",
    "web_platform/frontend/js/risk-results.js",
    "web_platform/frontend/js/xai-results.js",
    "web_platform/frontend/js/ai-report.js",
]

stale_refs = {}
for fp in v3_scan_dirs:
    p = Path(fp)
    if p.exists():
        content = p.read_text(encoding="utf-8", errors="ignore")
        lines = content.split("\n")
        matches = [(i+1, line.strip()) for i, line in enumerate(lines) 
                   if "Obesity" in line and "Family_History_Obesity" not in line and "#" not in line[:5]]
        if matches:
            stale_refs[fp] = matches[:5]  # cap at 5 per file

report["4_stale_obesity_scan"] = {
    "files_with_stale_refs": {k: [{"line": m[0], "text": m[1][:120]} for m in v] for k, v in stale_refs.items()},
    "total_stale_files": len(stale_refs),
}
logger.info(f"  Found stale Obesity refs in {len(stale_refs)} v3 files")
for fp in stale_refs:
    logger.info(f"    {fp}: {len(stale_refs[fp])} references")

# ============================================================
# 5. LEAKAGE, CALIBRATION, SCHEMA, SPLIT ALIGNMENT
# ============================================================
logger.info("=== SECTION 5: LEAKAGE/CALIBRATION/SCHEMA AUDIT ===")

# Split alignment: no Patient_ID overlap
train_ids = set(split_df[split_df["Split"]=="Train"]["Patient_ID"])
val_ids = set(split_df[split_df["Split"]=="Val"]["Patient_ID"])
test_ids = set(split_df[split_df["Split"]=="Test"]["Patient_ID"])
train_val_leak = train_ids & val_ids
train_test_leak = train_ids & test_ids
val_test_leak = val_ids & test_ids

# Feature order verification
clin_features_match = list(clin_payload["features"]) == list(clin_df.columns[:len(clin_payload["features"])])

# Schema: all 5 diseases present in labels
label_cols = set(labels_df.columns)
diseases_present = all(d in label_cols for d in DISEASES)

# Calibration reliability diagram (compute fraction of positives in bins)
calibration_results = {}
for i, d in enumerate(DISEASES):
    try:
        frac_pos, mean_pred = calibration_curve(y_te[:, i], test_c[:, i], n_bins=10)
        ece = float(np.mean(np.abs(frac_pos - mean_pred)))
        calibration_results[d] = {"ECE": round(ece, 4), "n_bins_used": len(frac_pos)}
    except Exception as e:
        calibration_results[d] = {"ECE": float('nan'), "error": str(e)}

# Deterministic reproducibility
res1 = engine.predict_clinical(base_features.copy())
res2 = engine.predict_clinical(base_features.copy())
repro_match = all(
    res1["calibrated_probabilities"][d] == res2["calibrated_probabilities"][d] for d in DISEASES
)

report["5_leakage_calibration_schema"] = {
    "train_val_patient_leak": len(train_val_leak),
    "train_test_patient_leak": len(train_test_leak),
    "val_test_patient_leak": len(val_test_leak),
    "split_leak_PASS": len(train_val_leak) == 0 and len(train_test_leak) == 0 and len(val_test_leak) == 0,
    "all_5_diseases_in_labels": diseases_present,
    "clinical_calibration_ECE": calibration_results,
    "deterministic_reproducibility_PASS": repro_match,
    "train_n": int(train_mask.sum()),
    "val_n": int(val_mask.sum()),
    "test_n": int(test_mask.sum()),
}
logger.info(f"  Split leak: train-val={len(train_val_leak)}, train-test={len(train_test_leak)}, val-test={len(val_test_leak)}")
logger.info(f"  Reproducibility: {repro_match}")

# ============================================================
# 6. B=1000 BOOTSTRAP ON FROZEN TEST PREDICTIONS
# ============================================================
logger.info("=== SECTION 6: B=1000 BOOTSTRAP ===")
np.random.seed(42)
B = 1000
n_te = y_te.shape[0]

# C thresholds (tuned on val)
c_thresh = tune_thresholds_on_val(val_c, y_va)
cg_thresh = tune_thresholds_on_val((val_c + val_g) / 2, y_va)
cwg_thresh = tune_thresholds_on_val((val_c + val_w + val_g) / 3, y_va)

boot_c_f1 = []
boot_cg_f1 = []
boot_cwg_f1 = []
boot_delta_cg_c = []
boot_delta_cwg_c = []

boot_c_auc = {d: [] for d in DISEASES}
boot_cg_auc = {d: [] for d in DISEASES}

for b in range(B):
    idx = np.random.choice(n_te, size=n_te, replace=True)
    
    # C
    c_preds = np.array([(test_c[idx, i] >= c_thresh[i]).astype(int) for i in range(5)]).T
    c_f1 = f1_score(y_te[idx], c_preds, average='macro')
    boot_c_f1.append(c_f1)
    
    # C+G
    cg_probs = (test_c[idx] + test_g[idx]) / 2
    cg_preds = np.array([(cg_probs[:, i] >= cg_thresh[i]).astype(int) for i in range(5)]).T
    cg_f1 = f1_score(y_te[idx], cg_preds, average='macro')
    boot_cg_f1.append(cg_f1)
    
    # C+W+G
    cwg_probs = (test_c[idx] + test_w[idx] + test_g[idx]) / 3
    cwg_preds = np.array([(cwg_probs[:, i] >= cwg_thresh[i]).astype(int) for i in range(5)]).T
    cwg_f1 = f1_score(y_te[idx], cwg_preds, average='macro')
    boot_cwg_f1.append(cwg_f1)
    
    boot_delta_cg_c.append(cg_f1 - c_f1)
    boot_delta_cwg_c.append(cwg_f1 - c_f1)
    
    for i, d in enumerate(DISEASES):
        try:
            boot_c_auc[d].append(roc_auc_score(y_te[idx, i], test_c[idx, i]))
            boot_cg_auc[d].append(roc_auc_score(y_te[idx, i], cg_probs[:, i]))
        except:
            pass

def ci95(arr):
    return [round(float(np.percentile(arr, 2.5)), 4), round(float(np.percentile(arr, 97.5)), 4)]

report["6_bootstrap_B1000"] = {
    "C_Macro_F1_95CI": ci95(boot_c_f1),
    "C_Macro_F1_mean": round(float(np.mean(boot_c_f1)), 4),
    "CG_Macro_F1_95CI": ci95(boot_cg_f1),
    "CG_Macro_F1_mean": round(float(np.mean(boot_cg_f1)), 4),
    "CWG_Macro_F1_95CI": ci95(boot_cwg_f1),
    "CWG_Macro_F1_mean": round(float(np.mean(boot_cwg_f1)), 4),
    "delta_CG_minus_C_95CI": ci95(boot_delta_cg_c),
    "delta_CG_minus_C_mean": round(float(np.mean(boot_delta_cg_c)), 4),
    "delta_CWG_minus_C_95CI": ci95(boot_delta_cwg_c),
    "delta_CWG_minus_C_mean": round(float(np.mean(boot_delta_cwg_c)), 4),
    "CG_significantly_better_than_C": 0.0 < ci95(boot_delta_cg_c)[0],
    "per_disease_C_AUC_95CI": {d: ci95(boot_c_auc[d]) for d in DISEASES if boot_c_auc[d]},
    "per_disease_CG_AUC_95CI": {d: ci95(boot_cg_auc[d]) for d in DISEASES if boot_cg_auc[d]},
}
logger.info(f"  C  Macro F1: {np.mean(boot_c_f1):.4f} {ci95(boot_c_f1)}")
logger.info(f"  C+G Macro F1: {np.mean(boot_cg_f1):.4f} {ci95(boot_cg_f1)}")
logger.info(f"  C+W+G Macro F1: {np.mean(boot_cwg_f1):.4f} {ci95(boot_cwg_f1)}")
logger.info(f"  Delta C+G - C: {np.mean(boot_delta_cg_c):+.4f} {ci95(boot_delta_cg_c)}")

# ============================================================
# 7. ARTIFACT VERIFICATION
# ============================================================
logger.info("=== SECTION 7: ARTIFACT VERIFICATION ===")

def file_hash(path):
    if Path(path).exists():
        return hashlib.md5(Path(path).read_bytes()).hexdigest()
    return "NOT_FOUND"

artifacts = {
    "clinical_v3_payload": {
        "path": "expert_models/saved_models/clinical_v3/clinical_v3_payload.joblib",
        "expected_arch": "CatBoostClassifier",
    },
    "wearable_v3_payload": {
        "path": "expert_models/saved_models/wearable_v3/wearable_v3_payload.joblib",
        "expected_arch": "LGBMClassifier",
    },
    "gut_v3_payload": {
        "path": "expert_models/saved_models/gut_v3/gut_v3_payload.joblib",
        "expected_arch": "XGBClassifier",
    },
    "wg_stacker": {
        "path": "expert_models/saved_models/fusion_v3/wg_logistic_regression_stacker.joblib",
        "expected_arch": "LogisticRegression",
    },
}

artifact_results = {}
for name, info in artifacts.items():
    h = file_hash(info["path"])
    payload = joblib.load(info["path"]) if Path(info["path"]).exists() else None
    
    if payload and "models" in payload:
        actual_arch = type(payload["models"][0]).__name__
    elif payload and "stacker_models" in payload:
        actual_arch = type(payload["stacker_models"][0]).__name__
    elif payload and "stacker_type" in payload:
        actual_arch = payload["stacker_type"]
    else:
        actual_arch = "UNKNOWN"
    
    arch_match = info["expected_arch"] in actual_arch
    artifact_results[name] = {
        "path": info["path"],
        "md5": h,
        "expected_arch": info["expected_arch"],
        "actual_arch": actual_arch,
        "arch_MATCH": arch_match,
    }
    logger.info(f"  {name}: {actual_arch} (expected {info['expected_arch']}) MATCH={arch_match} md5={h[:12]}")

report["7_artifact_verification"] = artifact_results

# ============================================================
# SAVE REPORT
# ============================================================
output_path = Path("scripts/v3_3_closure_audit_results.json")
with open(output_path, "w") as f:
    json.dump(report, f, indent=2, default=str)

logger.info(f"\n=== CLOSURE AUDIT COMPLETE ===")
logger.info(f"Results saved to {output_path}")

# Print summary
print("\n" + "="*70)
print("  V3.3 SCIENTIFIC CLOSURE AUDIT — SUMMARY")
print("="*70)
print(f"\n--- PATHWAY TEST-SET COMPARISON ---")
print(f"{'Pathway':<10} {'Macro F1':>10} {'Micro F1':>10}")
print("-"*32)
for pw in ["C", "W", "G", "C+W", "C+G", "W+G", "C+W+G"]:
    r = pathway_results[pw]
    print(f"{pw:<10} {r['Macro_F1']:>10.4f} {r['Micro_F1']:>10.4f}")

print(f"\n--- C+G vs C DELTA ---")
print(f"  C Macro F1:   {pathway_results['C']['Macro_F1']:.4f}")
print(f"  C+G Macro F1: {pathway_results['C+G']['Macro_F1']:.4f}")
print(f"  Delta:        {pathway_results['C+G']['Macro_F1'] - pathway_results['C']['Macro_F1']:+.4f}")
print(f"  C+G improves: {cg_improves}")

print(f"\n--- GLYCEMIC HIERARCHY ---")
print(f"  T2D+PreDM co-occurrence:     {co_occurrence} ({co_rate*100:.2f}%)")
print(f"  Glycemic discordance:        {discord_fpg_t2d}/{discord_total_diabetic} ({discord_rate*100:.2f}%)")
print(f"  FPG T2D monotonicity viols:  {fpg_t2d_violations}")
print(f"  HbA1c T2D monotonicity viols:{hba1c_t2d_violations}")

print(f"\n--- BOOTSTRAP (B=1000) ---")
print(f"  C   Macro F1: {np.mean(boot_c_f1):.4f} 95%CI {ci95(boot_c_f1)}")
print(f"  C+G Macro F1: {np.mean(boot_cg_f1):.4f} 95%CI {ci95(boot_cg_f1)}")
print(f"  C+W+G Macro F1: {np.mean(boot_cwg_f1):.4f} 95%CI {ci95(boot_cwg_f1)}")
print(f"  Delta C+G-C: {np.mean(boot_delta_cg_c):+.4f} 95%CI {ci95(boot_delta_cg_c)}")
sig = 0.0 < ci95(boot_delta_cg_c)[0]
print(f"  C+G > C significant: {sig}")

print(f"\n--- LEAKAGE/SCHEMA ---")
print(f"  Split leak: {report['5_leakage_calibration_schema']['split_leak_PASS']}")
print(f"  Reproducibility: {repro_match}")
print(f"  All diseases in labels: {diseases_present}")

print(f"\n--- STALE OBESITY ---")
print(f"  V3 files with stale Obesity: {len(stale_refs)}")

print(f"\n--- ARTIFACTS ---")
all_match = all(v["arch_MATCH"] for v in artifact_results.values())
print(f"  All architectures match: {all_match}")

# Final recommendation
issues = []
if co_occurrence > 0:
    issues.append(f"T2D+PreDM co-occurrence: {co_occurrence}")
if not report["5_leakage_calibration_schema"]["split_leak_PASS"]:
    issues.append("Split leakage detected")
if not all_match:
    issues.append("Architecture mismatch in artifacts")
if len(stale_refs) > 0:
    for f in stale_refs:
        if "v3_inference" in f or "v3_scientific" in f or "v3_routes" in f:
            issues.append(f"Stale Obesity in v3 runtime: {f}")

print(f"\n{'='*70}")
if issues:
    print(f"  RECOMMENDATION: FIX")
    for iss in issues:
        print(f"    ⚠ {iss}")
else:
    print(f"  RECOMMENDATION: FREEZE [OK]")
print(f"{'='*70}")
