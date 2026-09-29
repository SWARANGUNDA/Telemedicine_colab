"""
generate_clinical_v2_dataset.py — Generator for Clinical Dataset v2.

Implements Phase A v4.0 Architectural Design Specification:
- Latent physiological factor model (7 factors)
- Mutually exclusive dysglycemia stage model (Normal, Prediabetes, T2D) via ordered multinomial model
- True long-term physiology vs single-visit observation layer
- Medically plausible treatment control reductions (Glucose, BP, Statins)
- Family history genetics layer
- Zero target leakage into X
"""

import logging
import numpy as np
import pandas as pd
from scipy.special import expit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("clinical_v2_generator")


def generate_clinical_v2(n: int = 20000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    logger.info(f"Generating Clinical Dataset v2 (N={n:,}, seed={seed})...")

    # ── 1. Demographics ──
    patient_ids = [f"P{i+1:05d}" for i in range(n)]

    # Age distribution: 20% 18-30, 30% 31-45, 30% 46-60, 20% 61-85
    age_bin = rng.choice([0, 1, 2, 3], size=n, p=[0.20, 0.30, 0.30, 0.20])
    ages = np.zeros(n, dtype=int)
    ages[age_bin == 0] = rng.integers(18, 31, size=np.sum(age_bin == 0))
    ages[age_bin == 1] = rng.integers(31, 46, size=np.sum(age_bin == 1))
    ages[age_bin == 2] = rng.integers(46, 61, size=np.sum(age_bin == 2))
    ages[age_bin == 3] = rng.integers(61, 86, size=np.sum(age_bin == 3))

    genders = rng.choice(["Male", "Female"], size=n, p=[0.50, 0.50])
    is_male = (genders == "Male").astype(float)

    # ── 2. Family History & Genetics Layer ──
    fam_diabetes = rng.binomial(1, 0.28, size=n)
    fam_htn = rng.binomial(1, 0.35, size=n)
    fam_cvd = rng.binomial(1, 0.22, size=n)

    # Standardized age factor
    age_std = (ages - 45.0) / 15.0

    # ── 3. Latent Physiological Factors (Continuous L_1 .. L_7) ──
    l_adiposity = 0.35 * age_std + 0.15 * is_male + rng.normal(0, 1.0, size=n)
    l_visceral = 0.50 * l_adiposity + 0.35 * is_male + 0.20 * age_std + rng.normal(0, 0.8, size=n)
    l_glycemic = (0.40 * l_adiposity + 0.30 * l_visceral + 0.45 * fam_diabetes + 
                  0.25 * age_std + rng.normal(0, 0.8, size=n))
    l_dyslipidemia = (0.40 * l_visceral + 0.38 * fam_cvd + 0.20 * age_std + rng.normal(0, 0.8, size=n))
    l_vascular = (0.35 * l_visceral + 0.40 * fam_htn + 0.35 * age_std + rng.normal(0, 0.8, size=n))
    l_hepatic = (0.45 * l_visceral + 0.30 * l_glycemic + 0.25 * l_dyslipidemia + rng.normal(0, 0.8, size=n))

    # ── 4. True Longitudinal Disease States & Physiology ──

    # A. Dysglycemia (Prediabetes & T2D) - Mutually Exclusive Ordered Stage Model
    l_glyc_total = 0.50 * l_glycemic + 0.30 * l_adiposity + 0.20 * age_std
    c1, c2 = -0.15, 1.05  # cutpoints

    p_normal = 1.0 - expit(l_glyc_total - c1)
    p_predia = expit(l_glyc_total - c1) - expit(l_glyc_total - c2)
    p_t2d = expit(l_glyc_total - c2)

    # Normalize probabilities to sum exactly to 1
    p_matrix = np.column_stack([p_normal, p_predia, p_t2d])
    p_matrix = p_matrix / p_matrix.sum(axis=1, keepdims=True)

    # Sample glycemic stage S_glycemic in {0: Normal, 1: Prediabetes, 2: T2D}
    s_glycemic = np.zeros(n, dtype=int)
    for i in range(n):
        s_glycemic[i] = rng.choice([0, 1, 2], p=p_matrix[i])

    t2d_target = (s_glycemic == 2).astype(int)
    predia_target = (s_glycemic == 1).astype(int)

    # Generate True Long-Term Glycemic Physiology
    fpg_true = np.zeros(n)
    hba1c_true = np.zeros(n)

    mask_norm = (s_glycemic == 0)
    mask_pred = (s_glycemic == 1)
    mask_t2d  = (s_glycemic == 2)

    fpg_true[mask_norm] = 88.0 + 3.0 * l_glyc_total[mask_norm] + rng.normal(0, 5.0, size=np.sum(mask_norm))
    hba1c_true[mask_norm] = 5.10 + 0.12 * l_glyc_total[mask_norm] + rng.normal(0, 0.12, size=np.sum(mask_norm))

    fpg_true[mask_pred] = 110.0 + 5.0 * l_glyc_total[mask_pred] + rng.normal(0, 6.0, size=np.sum(mask_pred))
    hba1c_true[mask_pred] = 5.95 + 0.18 * l_glyc_total[mask_pred] + rng.normal(0, 0.16, size=np.sum(mask_pred))

    fpg_true[mask_t2d] = 145.0 + 10.0 * l_glyc_total[mask_t2d] + rng.normal(0, 14.0, size=np.sum(mask_t2d))
    hba1c_true[mask_t2d] = 7.40 + 0.40 * l_glyc_total[mask_t2d] + rng.normal(0, 0.45, size=np.sum(mask_t2d))

    # Physiological floor clipping
    fpg_true = np.clip(fpg_true, 65.0, 320.0)
    hba1c_true = np.clip(hba1c_true, 4.2, 14.5)

    # B. Obesity (WHO True BMI >= 30.0)
    bmi_true = 26.5 + 4.5 * l_adiposity + rng.normal(0, 1.2, size=n)
    bmi_true = np.clip(bmi_true, 16.0, 52.0)
    obese_target = (bmi_true >= 30.0).astype(int)

    # True Height & Weight
    height_true = np.where(is_male == 1, rng.normal(175.0, 7.0, size=n), rng.normal(162.0, 6.5, size=n))
    height_true = np.clip(height_true, 140.0, 205.0)
    weight_true = bmi_true * ((height_true / 100.0) ** 2)

    # C. Metabolic Syndrome (ATP III criteria on true physiology)
    waist_true = np.where(is_male == 1, 85.0 + 7.5 * l_visceral + rng.normal(0, 4.0, size=n),
                                        78.0 + 7.5 * l_visceral + rng.normal(0, 4.0, size=n))
    tg_true = np.exp(4.8 + 0.35 * l_dyslipidemia + rng.normal(0, 0.2, size=n))
    hdl_true = np.where(is_male == 1, 50.0 - 6.0 * l_dyslipidemia + rng.normal(0, 4.0, size=n),
                                      58.0 - 7.0 * l_dyslipidemia + rng.normal(0, 4.5, size=n))
    ldl_true = 110.0 + 18.0 * l_dyslipidemia + rng.normal(0, 12.0, size=n)

    sbp_true = 120.0 + 10.0 * l_vascular + rng.normal(0, 6.0, size=n)
    dbp_true = 78.0 + 6.0 * l_vascular + rng.normal(0, 4.0, size=n)

    # True ATP III Criteria Counting
    c_waist = np.where(is_male == 1, waist_true >= 102.0, waist_true >= 88.0)
    c_tg    = (tg_true >= 150.0)
    c_hdl   = np.where(is_male == 1, hdl_true < 40.0, hdl_true < 50.0)
    c_bp    = (sbp_true >= 130.0) | (dbp_true >= 85.0)
    c_fpg   = (fpg_true >= 100.0)

    true_mets_count = c_waist.astype(int) + c_tg.astype(int) + c_hdl.astype(int) + c_bp.astype(int) + c_fpg.astype(int)
    mets_target = (true_mets_count >= 3).astype(int)

    # D. NAFLD (Hepatic Risk Score + Probabilistic Assignment)
    r_hepatic = expit(0.70 * l_hepatic + 0.40 * l_visceral + 0.30 * l_dyslipidemia + 0.25 * l_glycemic - 0.20)
    p_nafld = expit(3.5 * (r_hepatic - 0.50))
    nafld_target = (rng.uniform(0, 1, size=n) < p_nafld).astype(int)

    # ── 5. Treatment / Control Effects (Modifies Observed Lab Profile) ──
    tx_glucose = np.zeros(n)
    tx_hba1c   = np.zeros(n)
    tx_bp_sys  = np.zeros(n)
    tx_bp_dia  = np.zeros(n)
    tx_tg      = np.zeros(n)
    tx_ldl     = np.zeros(n)

    # Glucose Tx: 55% of T2D patients age >= 40 with fpg_true > 130
    mask_tx_glyc = (s_glycemic == 2) & (ages >= 40) & (fpg_true > 130.0)
    eligible_glyc = np.where(mask_tx_glyc)[0]
    treated_glyc = rng.choice(eligible_glyc, size=int(len(eligible_glyc) * 0.55), replace=False)
    tx_glucose[treated_glyc] = rng.normal(24.0, 5.0, size=len(treated_glyc))
    tx_hba1c[treated_glyc]   = rng.normal(0.95, 0.20, size=len(treated_glyc))

    # Antihypertensive Tx: 50% of vascular stress sbp_true >= 135 & age >= 45
    mask_tx_bp = (sbp_true >= 135.0) & (ages >= 45)
    eligible_bp = np.where(mask_tx_bp)[0]
    treated_bp = rng.choice(eligible_bp, size=int(len(eligible_bp) * 0.50), replace=False)
    tx_bp_sys[treated_bp] = rng.normal(16.0, 3.5, size=len(treated_bp))
    tx_bp_dia[treated_bp] = rng.normal(9.0, 2.5, size=len(treated_bp))

    # Lipid Tx: 45% of dyslipidemic tg_true >= 180 & age >= 50
    mask_tx_lipid = (tg_true >= 180.0) & (ages >= 50)
    eligible_lipid = np.where(mask_tx_lipid)[0]
    treated_lipid = rng.choice(eligible_lipid, size=int(len(eligible_lipid) * 0.45), replace=False)
    tx_tg[treated_lipid]  = rng.normal(35.0, 7.0, size=len(treated_lipid))
    tx_ldl[treated_lipid] = rng.normal(40.0, 8.0, size=len(treated_lipid))

    # ── 6. Single-Visit Observed Predictor Matrix (X) ──
    weight_obs = weight_true + rng.normal(0, 1.4, size=n)
    height_obs = height_true + rng.normal(0, 0.4, size=n)
    bmi_obs    = weight_obs / ((height_obs / 100.0) ** 2)
    waist_obs  = waist_true + rng.normal(0, 1.8, size=n)

    fpg_obs   = fpg_true - tx_glucose + rng.normal(0, 4.5, size=n)
    hba1c_obs = hba1c_true - tx_hba1c + rng.normal(0, 0.14, size=n)
    
    sbp_obs   = sbp_true - tx_bp_sys + rng.normal(0, 4.5, size=n)
    dbp_obs   = dbp_true - tx_bp_dia + rng.normal(0, 3.2, size=n)

    tg_obs    = np.maximum(40.0, (tg_true - tx_tg) * (1.0 + rng.normal(0, 0.08, size=n)))
    hdl_obs   = np.maximum(18.0, hdl_true + rng.normal(0, 2.5, size=n))
    ldl_obs   = np.maximum(30.0, (ldl_true - tx_ldl) + rng.normal(0, 6.0, size=n))

    # Liver Enzymes (ALT & AST reflect hepatic stress)
    alt_obs = np.exp(np.log(20.0 + 12.0 * np.maximum(0, l_hepatic + 1.0)) + rng.normal(0, 0.25, size=n))
    ast_obs = np.exp(np.log(18.0 + 9.0 * np.maximum(0, l_hepatic + 1.0)) + rng.normal(0, 0.22, size=n))

    # Round continuous features appropriately
    df_out = pd.DataFrame({
        "Patient_ID": patient_ids,
        "Age": ages,
        "Gender": genders,
        "Height": np.round(height_obs, 1),
        "Weight": np.round(weight_obs, 1),
        "BMI": np.round(bmi_obs, 2),
        "Waist_Circumference": np.round(waist_obs, 1),
        "Systolic_BP": np.round(sbp_obs, 1),
        "Diastolic_BP": np.round(dbp_obs, 1),
        "Fasting_Blood_Glucose": np.round(fpg_obs, 1),
        "HbA1c": np.round(hba1c_obs, 2),
        "Triglycerides": np.round(tg_obs, 1),
        "HDL": np.round(hdl_obs, 1),
        "LDL": np.round(ldl_obs, 1),
        "ALT": np.round(alt_obs, 1),
        "AST": np.round(ast_obs, 1),
        "Family_History_Diabetes": fam_diabetes,
        "Family_History_Hypertension": fam_htn,
        "Family_History_CVD": fam_cvd,
        "Type2_Diabetes": t2d_target,
        "Prediabetes": predia_target,
        "Obesity": obese_target,
        "Metabolic_Syndrome": mets_target,
        "NAFLD": nafld_target,
    })

    # Internal logging of latent state counts
    logger.info(f"Generated N={len(df_out):,} rows successfully.")
    logger.info(f"Latent Glycemic Stages: Normal={np.sum(s_glycemic==0)}, Prediabetes={np.sum(s_glycemic==1)}, T2D={np.sum(s_glycemic==2)}")
    logger.info(f"Target Prevalences: T2D={df_out['Type2_Diabetes'].mean():.4f}, Predia={df_out['Prediabetes'].mean():.4f}, Obese={df_out['Obesity'].mean():.4f}, MetS={df_out['Metabolic_Syndrome'].mean():.4f}, NAFLD={df_out['NAFLD'].mean():.4f}")

    return df_out


if __name__ == "__main__":
    df_v2 = generate_clinical_v2(n=20000, seed=42)
    output_path = "Clinical_Dataset_v2.csv"
    df_v2.to_csv(output_path, index=False)
    logger.info(f"Clinical_Dataset_v2.csv successfully saved to {output_path}")
