"""
generate_multimodal_v3_dataset.py — Generator & Stage B Comprehensive QC Engine for Multimodal Dataset v3.2.2

Executes:
1. Seed initialization (20260728).
2. Demographics & Upstream Genetic Predisposition G_i sampling.
3. 11D Latent Physiology L_i sampling via Gaussian Copula with validated positive definite matrix.
4. Continuous Disease Liabilities & Stochastic Disease Labels Y_i (Ordered Probit for T2D/Predia).
5. Severity-Conditioned Two-Stage Treatment Assignment & Stochastic Response.
6. Clinical Observations Generation X_Clinical (Causal Anthropometrics Height -> BMI -> Weight).
7. Wearable Telemetry Generation X_Wearable (Standard 10D & CGM 5D with TIR+TAR+TBR=100%).
8. Gut Microbiome Composition Generation X_Gut (20 Taxa + Other_Taxa Dirichlet-Multinomial, Sum=100%).
9. Biological Fluctuation, Multi-Sensor Noise & Probabilistic Missingness (MAR/MCAR) Injection.
10. Master Split Assignment (70/15/15) & Export of 6 CSV files.
11. Comprehensive Stage B QC Audit (Sections A-I).
"""

import os
import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("multimodal_v3_generator")

SEED = 20260728
N_PATIENTS = 20000
OUTPUT_DIR = Path("data/multimodal_v3")

def run_generation_and_qc():
    np.random.seed(SEED)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Initializing Multimodal Dataset v3.2.2 Generator (N={N_PATIENTS}, Seed={SEED})...")

    # ------------------------------------------------------------------
    # 1. Demographics & Upstream Genetic Predisposition (G_i)
    # ------------------------------------------------------------------
    patient_ids = [f"P{i+1:05d}" for i in range(N_PATIENTS)]
    age = np.random.randint(18, 86, size=N_PATIENTS)
    gender = np.random.binomial(1, 0.50, size=N_PATIENTS) # 0 = Female, 1 = Male

    # Upstream Genetic Predisposition Vectors
    G_glyc   = np.random.normal(0, 1, size=N_PATIENTS)
    G_vasc   = np.random.normal(0, 1, size=N_PATIENTS)
    G_dyslip = np.random.normal(0, 1, size=N_PATIENTS)

    fam_hist_diabetes = np.random.binomial(1, 1.0 / (1.0 + np.exp(-(-1.2 + 1.2 * G_glyc))))
    fam_hist_htn      = np.random.binomial(1, 1.0 / (1.0 + np.exp(-(-1.0 + 1.1 * G_vasc))))
    fam_hist_cvd      = np.random.binomial(1, 1.0 / (1.0 + np.exp(-(-1.5 + 0.9 * G_dyslip + 0.7 * G_vasc))))

    # ------------------------------------------------------------------
    # 2. 11D Shared Latent Physiology (L_i) via Gaussian Copula
    # ------------------------------------------------------------------
    # 11 Factors: 0:glyc, 1:IR, 2:adip, 3:visc, 4:vasc, 5:dyslip, 6:hep, 7:infl, 8:fit, 9:auto, 10:dysb
    R_physio = np.eye(11)
    R_physio[0, 1] = R_physio[1, 0] = 0.55
    R_physio[0, 2] = R_physio[2, 0] = 0.35
    R_physio[0, 3] = R_physio[3, 0] = 0.45
    R_physio[0, 5] = R_physio[5, 0] = 0.30
    R_physio[0, 6] = R_physio[6, 0] = 0.25
    R_physio[0, 7] = R_physio[7, 0] = 0.25
    R_physio[0, 8] = R_physio[8, 0] = -0.30
    R_physio[0, 10] = R_physio[10, 0] = 0.30

    R_physio[1, 2] = R_physio[2, 1] = 0.40
    R_physio[1, 3] = R_physio[3, 1] = 0.50
    R_physio[1, 5] = R_physio[5, 1] = 0.35
    R_physio[1, 6] = R_physio[6, 1] = 0.40
    R_physio[1, 7] = R_physio[7, 1] = 0.30
    R_physio[1, 8] = R_physio[8, 1] = -0.35

    R_physio[2, 3] = R_physio[3, 2] = 0.65
    R_physio[2, 4] = R_physio[4, 2] = 0.30
    R_physio[2, 5] = R_physio[5, 2] = 0.35
    R_physio[2, 8] = R_physio[8, 2] = -0.45

    R_physio[3, 4] = R_physio[4, 3] = 0.35
    R_physio[3, 5] = R_physio[5, 3] = 0.45
    R_physio[3, 6] = R_physio[6, 3] = 0.50
    R_physio[3, 7] = R_physio[7, 3] = 0.35
    R_physio[3, 8] = R_physio[8, 3] = -0.40
    R_physio[3, 10] = R_physio[10, 3] = 0.30

    R_physio[4, 5] = R_physio[5, 4] = 0.25
    R_physio[4, 9] = R_physio[9, 4] = 0.35

    R_physio[5, 6] = R_physio[6, 5] = 0.45
    R_physio[5, 7] = R_physio[7, 5] = 0.30

    R_physio[6, 7] = R_physio[7, 6] = 0.35
    R_physio[6, 10] = R_physio[10, 6] = 0.25

    R_physio[7, 8] = R_physio[8, 7] = -0.30
    R_physio[7, 9] = R_physio[9, 7] = 0.25
    R_physio[7, 10] = R_physio[10, 7] = 0.40

    R_physio[8, 9] = R_physio[9, 8] = -0.35
    R_physio[8, 10] = R_physio[10, 8] = -0.25

    R_physio[9, 10] = R_physio[10, 9] = 0.20

    # Project to nearest positive definite if needed
    eigvals = np.linalg.eigvalsh(R_physio)
    if np.any(eigvals <= 0):
        vals = np.maximum(eigvals, 1e-5)
        vecs = np.linalg.eigh(R_physio)[1]
        R_physio = vecs @ np.diag(vals) @ vecs.T
        inv_d = 1.0 / np.sqrt(np.diag(R_physio))
        R_physio = np.diag(inv_d) @ R_physio @ np.diag(inv_d)

    # Shift latent mean based on genetics and age
    mu_Z = np.zeros((N_PATIENTS, 11))
    mu_Z[:, 0] = 0.35 * G_glyc + 0.008 * (age - 45)  # L_glyc
    mu_Z[:, 1] = 0.30 * G_glyc + 0.006 * (age - 45)  # L_IR
    mu_Z[:, 4] = 0.35 * G_vasc + 0.012 * (age - 45)  # L_vasc
    mu_Z[:, 5] = 0.35 * G_dyslip + 0.006 * (age - 45)# L_dyslip

    L_chol = np.linalg.cholesky(R_physio)
    Z_raw = np.random.normal(0, 1, size=(N_PATIENTS, 11))
    Z = mu_Z + Z_raw @ L_chol.T

    L = norm.cdf(Z) # Transform to (0, 1) bounded latent factors

    L_glyc = L[:, 0]
    L_IR   = L[:, 1]
    L_adip = L[:, 2]
    L_visc = L[:, 3]
    L_vasc = L[:, 4]
    L_dysl = L[:, 5]
    L_hep  = L[:, 6]
    L_infl = L[:, 7]
    L_fit  = L[:, 8]
    L_auto = L[:, 9]
    L_dysb = L[:, 10]

    # ------------------------------------------------------------------
    # 3. Continuous Disease Liabilities & Ground-Truth Labels (Y)
    # ------------------------------------------------------------------
    eta_d = np.random.normal(0, 0.70, size=(N_PATIENTS, 5))

    # A. Non-Glycemic Diseases (Calibrated to Target Population Prevalences)
    R_obese = -3.80 + 3.6 * L_adip + 1.6 * L_visc + eta_d[:, 2]
    P_obese = 1.0 / (1.0 + np.exp(-R_obese))
    Y_Obesity = np.random.binomial(1, P_obese)

    R_mets = -4.40 + 2.2 * L_visc + 1.6 * L_vasc + 1.4 * L_dysl + 1.0 * L_IR + eta_d[:, 3]
    P_mets = 1.0 / (1.0 + np.exp(-R_mets))
    Y_MetS = np.random.binomial(1, P_mets)

    R_nafld = -3.80 + 3.0 * L_hep + 1.8 * L_visc + 1.2 * L_dysl + eta_d[:, 4]
    P_nafld = 1.0 / (1.0 + np.exp(-R_nafld))
    Y_NAFLD = np.random.binomial(1, P_nafld)

    # B. Glycemic Ordered Probit Model (T2D ~ 28%, Predia ~ 25%, Normal ~ 47%)
    R_glyc = -2.65 + 3.0 * L_glyc + 1.4 * L_IR + 0.8 * L_visc + eta_d[:, 0]
    theta_normal = -0.30
    theta_T2D    = 1.10

    P_normal = norm.cdf(theta_normal - R_glyc)
    P_predia = norm.cdf(theta_T2D - R_glyc) - norm.cdf(theta_normal - R_glyc)
    P_t2d    = 1.0 - norm.cdf(theta_T2D - R_glyc)

    # Clean numerical probabilities
    P_normal = np.clip(P_normal, 0.0, 1.0)
    P_predia = np.clip(P_predia, 0.0, 1.0)
    P_t2d    = np.clip(P_t2d, 0.0, 1.0)
    P_sum    = P_normal + P_predia + P_t2d
    P_normal /= P_sum
    P_predia /= P_sum
    P_t2d    /= P_sum

    glyc_state = np.zeros(N_PATIENTS, dtype=int)
    for i in range(N_PATIENTS):
        glyc_state[i] = np.random.choice([0, 1, 2], p=[P_normal[i], P_predia[i], P_t2d[i]])

    Y_Prediabetes = (glyc_state == 1).astype(int)
    Y_T2D         = (glyc_state == 2).astype(int)

    # ------------------------------------------------------------------
    # 4. Severity-Conditioned Stochastic Treatment Model
    # ------------------------------------------------------------------
    P_tx_glyc = 1.0 / (1.0 + np.exp(-(-3.0 + 4.8 * L_glyc + 2.0 * L_IR + 0.02 * (age - 45))))
    P_tx_bp   = 1.0 / (1.0 + np.exp(-(-3.2 + 5.0 * L_vasc + 1.8 * L_visc + 0.03 * (age - 45))))
    P_tx_lip  = 1.0 / (1.0 + np.exp(-(-3.5 + 4.6 * L_dysl + 2.2 * L_visc + 0.02 * (age - 45))))

    Tx_glyc_assigned = np.random.binomial(1, P_tx_glyc)
    Tx_bp_assigned   = np.random.binomial(1, P_tx_bp)
    Tx_lip_assigned  = np.random.binomial(1, P_tx_lip)

    Tx_glucose_resp = Tx_glyc_assigned * np.random.gamma(shape=6.0, scale=4.0, size=N_PATIENTS)
    Tx_hba1c_resp   = Tx_glyc_assigned * np.random.gamma(shape=9.0, scale=0.10, size=N_PATIENTS)
    Tx_bp_resp      = Tx_bp_assigned   * np.random.gamma(shape=5.0, scale=2.4, size=N_PATIENTS)
    Tx_lip_resp     = Tx_lip_assigned  * np.random.gamma(shape=8.0, scale=0.05, size=N_PATIENTS)

    # ------------------------------------------------------------------
    # 5. Clinical Observations Generation (X_Clinical, 18 Features)
    # ------------------------------------------------------------------
    # Height by Gender
    height = np.where(gender == 1, np.random.normal(175.0, 7.0, size=N_PATIENTS), np.random.normal(162.0, 6.0, size=N_PATIENTS))
    height = np.clip(height, 135.0, 215.0)

    # Causal Anthropometrics: Height -> L_adip -> BMI_true -> Weight_true -> Weight_obs -> BMI_obs
    BMI_true = 18.5 + 22.0 * L_adip + 5.5 * L_visc
    Weight_true = BMI_true * ((height / 100.0) ** 2)
    Weight_obs = Weight_true + np.random.normal(0, 1.2, size=N_PATIENTS)
    Weight_obs = np.clip(Weight_obs, 35.0, 220.0)
    BMI_obs = Weight_obs / ((height / 100.0) ** 2)
    BMI_obs = np.clip(BMI_obs, 15.0, 55.0)

    waist = 65.0 + 38.0 * L_visc + 18.0 * L_adip + 0.15 * (height - 170.0) + np.random.normal(0, 2.5, size=N_PATIENTS)
    waist = np.clip(waist, 50.0, 160.0)

    sbp = 100.0 + 42.0 * L_vasc + 14.0 * L_visc - Tx_bp_resp + np.random.normal(0, 4.0, size=N_PATIENTS)
    sbp = np.clip(sbp, 85.0, 210.0)

    dbp = 65.0 + 24.0 * L_vasc + 8.0 * L_visc - 0.5 * Tx_bp_resp + np.random.normal(0, 2.8, size=N_PATIENTS)
    dbp = np.clip(dbp, 50.0, 130.0)

    fpg = 70.0 + 105.0 * L_glyc + 22.0 * L_IR - Tx_glucose_resp + np.random.normal(0, 4.5, size=N_PATIENTS) + np.random.normal(0, 2.0, size=N_PATIENTS)
    fpg = np.clip(fpg, 60.0, 350.0)

    hba1c = 4.8 + 4.0 * L_glyc + 1.1 * L_IR - Tx_hba1c_resp + np.random.normal(0, 0.12, size=N_PATIENTS)
    hba1c = np.clip(hba1c, 4.0, 15.0)

    tg = np.exp(np.log(75.0) + 1.25 * L_dysl + 0.55 * L_visc - Tx_lip_resp) + np.random.normal(0, 8.0, size=N_PATIENTS)
    tg = np.clip(tg, 40.0, 750.0)

    hdl = np.exp(np.log(58.0) - 0.45 * L_dysl - 0.35 * L_visc + 0.25 * L_fit) + np.random.normal(0, 2.5, size=N_PATIENTS)
    hdl = np.clip(hdl, 15.0, 120.0)

    ldl = np.exp(np.log(110.0) + 0.65 * L_dysl + 0.25 * L_visc - 0.70 * Tx_lip_resp) + np.random.normal(0, 6.0, size=N_PATIENTS)
    ldl = np.clip(ldl, 30.0, 300.0)

    alt = np.exp(np.log(16.0) + 1.45 * L_hep + 0.45 * L_infl) + np.random.normal(0, 2.0, size=N_PATIENTS)
    alt = np.clip(alt, 8.0, 250.0)

    ast = np.exp(np.log(18.0) + 1.25 * L_hep + 0.35 * L_infl) + np.random.normal(0, 2.0, size=N_PATIENTS)
    ast = np.clip(ast, 8.0, 250.0)

    clinical_df = pd.DataFrame({
        "Patient_ID": patient_ids,
        "Age": age,
        "Gender": gender,
        "Height": np.round(height, 1),
        "Weight": np.round(Weight_obs, 1),
        "BMI": np.round(BMI_obs, 2),
        "Waist_Circumference": np.round(waist, 1),
        "Systolic_BP": np.round(sbp, 1),
        "Diastolic_BP": np.round(dbp, 1),
        "Fasting_Blood_Glucose": np.round(fpg, 1),
        "HbA1c": np.round(hba1c, 2),
        "Triglycerides": np.round(tg, 1),
        "HDL": np.round(hdl, 1),
        "LDL": np.round(ldl, 1),
        "ALT": np.round(alt, 1),
        "AST": np.round(ast, 1),
        "Family_History_Diabetes": fam_hist_diabetes,
        "Family_History_Hypertension": fam_hist_htn,
        "Family_History_CVD": fam_hist_cvd
    })

    # ------------------------------------------------------------------
    # 6. Wearable Telemetry Generation (v3.2.3 Revision)
    # ------------------------------------------------------------------
    # Independent lifestyle/occupational movement variance & sensor noise
    L_behavioral = np.random.normal(0, 1.0, size=N_PATIENTS)
    eps_steps    = np.random.normal(0, 2200.0, size=N_PATIENTS)
    eps_act      = np.random.normal(0, 18.0, size=N_PATIENTS)
    eps_sed      = np.random.normal(0, 50.0, size=N_PATIENTS)
    eps_rhr      = np.random.normal(0, 4.0, size=N_PATIENTS)
    eps_hrv      = np.random.normal(0, 4.0, size=N_PATIENTS)
    eps_sleep    = np.random.normal(0, 0.7, size=N_PATIENTS)
    eps_eff      = np.random.normal(0, 5.0, size=N_PATIENTS)
    eps_stress   = np.random.normal(0, 6.0, size=N_PATIENTS)
    eps_cal      = np.random.normal(0, 250.0, size=N_PATIENTS)

    steps = np.clip(12500.0 - 4200.0 * L_adip + 6200.0 * L_fit + 2500.0 * L_behavioral + eps_steps, 1000, 25000)
    act_mins = np.clip(75.0 - 28.0 * L_adip + 52.0 * L_fit + 15.0 * L_behavioral + eps_act, 0, 180)
    sed_mins = np.clip(480.0 + 240.0 * L_adip - 320.0 * L_fit - 80.0 * L_behavioral + eps_sed, 240, 1200)
    rhr = np.clip(54.0 + 26.0 * L_auto - 16.0 * L_fit + 8.0 * L_infl + eps_rhr, 40, 110)
    hrv = np.clip(np.exp(np.log(55.0) - 0.75 * L_auto + 0.55 * L_fit - 0.35 * L_infl) + eps_hrv, 10.0, 140.0)
    sleep_dur = np.clip(7.6 - 1.8 * L_auto - 0.8 * L_visc + eps_sleep, 3.5, 11.0)
    sleep_eff = np.clip(92.0 - 25.0 * L_auto - 12.0 * L_infl + eps_eff, 30.0, 100.0)
    stress_score = np.clip(15.0 + 65.0 * L_auto + 15.0 * L_infl + eps_stress, 5.0, 95.0)
    activity_cal = np.clip(2200.0 + 900.0 * L_fit - 200.0 * L_adip + 400.0 * L_behavioral + eps_cal, 500, 4500)

    lambda_ex = np.clip(4.5 - 1.8 * L_adip + 3.2 * L_fit + 1.2 * L_behavioral, 0.5, 6.5)
    exercise_freq = np.clip(np.random.poisson(lam=lambda_ex), 0, 7)

    wearable_std_df = pd.DataFrame({
        "Patient_ID": patient_ids,
        "Average_Daily_Steps": np.round(steps, 0),
        "Active_Minutes": np.round(act_mins, 1),
        "Sedentary_Time_Minutes": np.round(sed_mins, 1),
        "Resting_Heart_Rate": np.round(rhr, 1),
        "Heart_Rate_Variability_RMSSD": np.round(hrv, 1),
        "Sleep_Duration_Hours": np.round(sleep_dur, 2),
        "Sleep_Efficiency_Score": np.round(sleep_eff, 1),
        "Autonomic_Stress_Score": np.round(stress_score, 1),
        "Activity_Energy_Expenditure": np.round(activity_cal, 0),
        "Exercise_Frequency_Days": exercise_freq
    })

    # CGM Telemetry Simplex Normalization (TIR + TAR + TBR = 100%)
    G_telemetry = 88.0 + 92.0 * L_glyc + 32.0 * L_IR - Tx_glucose_resp + np.random.normal(0, 5.0, size=N_PATIENTS)
    cgm_avg = np.clip(G_telemetry, 60.0, 350.0)
    cgm_cv  = np.clip(14.0 + 0.28 * (cgm_avg - 80.0) + 12.0 * L_IR + np.random.normal(0, 2.0, size=N_PATIENTS), 8.0, 65.0)

    tbr_raw = np.clip(0.5 + 4.0 / (1.0 + np.exp(-(0.10 * (cgm_cv - 36.0) - 0.05 * (cgm_avg - 100.0)))) + np.random.normal(0, 0.5, size=N_PATIENTS), 0.0, 15.0)
    tar_raw = np.clip(100.0 / (1.0 + np.exp(-(0.045 * (cgm_avg - 130.0) + 0.02 * (cgm_cv - 36.0)))) + np.random.normal(0, 2.0, size=N_PATIENTS), 0.0, 100.0 - tbr_raw)
    tir_raw = np.maximum(0.0, 100.0 - tar_raw - tbr_raw)

    # Exact Simplex Normalization
    raw_sums = tir_raw + tar_raw + tbr_raw
    tir = (tir_raw / raw_sums) * 100.0
    tar = (tar_raw / raw_sums) * 100.0
    tbr = (tbr_raw / raw_sums) * 100.0

    wearable_cgm_df = pd.DataFrame({
        "Patient_ID": patient_ids,
        "CGM_Average_Glucose": np.round(cgm_avg, 1),
        "CGM_Glucose_CV": np.round(cgm_cv, 2),
        "CGM_Time_In_Range": np.round(tir, 2),
        "CGM_Time_Above_Range": np.round(tar, 2),
        "CGM_Time_Below_Range": np.round(tbr, 2)
    })

    # ------------------------------------------------------------------
    # 7. Gut Microbiome Composition Generation (X_Gut, 30 Features)
    # ------------------------------------------------------------------
    taxa_20 = [
        "Akkermansia", "Faecalibacterium", "Roseburia", "Bifidobacterium", "Bacteroides",
        "Prevotella", "Ruminococcus", "Blautia", "Collinsella", "Escherichia_Shigella",
        "Coprococcus", "Alistipes", "Subdoligranulum", "Enterococcus", "Eubacterium",
        "Parabacteroides", "Lactobacillus", "Klebsiella", "Streptococcus", "Eggerthella"
    ]

    alpha0 = np.array([3.5, 12.0, 5.5, 6.0, 18.0, 7.0, 4.0, 8.0, 2.5, 1.2, 3.0, 2.8, 3.2, 0.8, 2.2, 2.0, 1.8, 0.6, 1.5, 0.5, 12.0])
    b_dysb = np.array([-1.20, -1.40, -1.10, -0.90, 0.20, 0.15, -0.60, 0.10, 0.45, 1.85, -0.70, -0.40, -0.65, 1.65, -0.50, 0.10, -0.20, 1.75, 1.10, 1.95, -0.20])
    b_infl = np.array([-0.80, -0.95, -0.70, -0.60, 0.10, 0.05, -0.40, 0.00, 0.30, 1.35, -0.50, -0.25, -0.45, 1.20, -0.35, 0.05, -0.15, 1.40, 0.85, 1.50, -0.10])
    b_fit  = np.array([0.45, 0.60, 0.50, 0.40, -0.10, -0.15, 0.30, -0.10, -0.20, -0.55, 0.35, 0.20, 0.30, -0.45, 0.25, -0.05, 0.10, -0.50, -0.35, -0.60, 0.10])

    gut_abundances = np.zeros((N_PATIENTS, 21))
    for i in range(N_PATIENTS):
        eps = np.random.normal(0, 0.25, size=21)
        a_i = alpha0 * np.exp(b_dysb * L_dysb[i] + b_infl * L_infl[i] - b_fit * L_fit[i] + eps)
        p_dir = np.random.dirichlet(a_i)
        
        # Multinomial read sampling (Sequencing depth N=50,000)
        n_reads = np.random.negative_binomial(50, 50.0 / (50000.0 + 50.0))
        n_reads = max(10000, n_reads)
        counts = np.random.multinomial(n_reads, p_dir)
        counts[counts < 5] = 0 # Biological detection threshold
        
        c_sum = counts.sum()
        if c_sum > 0:
            gut_abundances[i, :] = (counts / c_sum) * 100.0
        else:
            gut_abundances[i, :] = p_dir * 100.0

    gut_df_dict = {"Patient_ID": patient_ids}
    for idx, t_name in enumerate(taxa_20):
        gut_df_dict[t_name] = np.round(gut_abundances[:, idx], 4)
    gut_df_dict["Other_Taxa"] = np.round(gut_abundances[:, 20], 4)

    # Derived Ecological & Functional Features
    p_frac = gut_abundances / 100.0
    p_no_zero = np.where(p_frac > 0, p_frac, 1.0)

    shannon = -np.sum(p_frac * np.log(p_no_zero), axis=1)
    simpson = 1.0 - np.sum(p_frac ** 2, axis=1)
    richness = np.sum(gut_abundances > 0, axis=1)
    pielou = shannon / np.log(np.maximum(richness, 2))

    scfa_idx = np.mean(gut_abundances[:, [0, 1, 2, 3, 10, 11, 12, 14]], axis=1)
    butyrate_idx = np.mean(gut_abundances[:, [1, 2, 10, 14]], axis=1)
    barrier_idx = np.mean(gut_abundances[:, [0, 1, 3]], axis=1)
    infl_idx = np.mean(gut_abundances[:, [9, 13, 17, 18, 19]], axis=1)
    
    firmicutes = np.sum(gut_abundances[:, [1, 2, 6, 7, 10, 12, 13, 14, 16, 18]], axis=1)
    bacteroidetes = np.sum(gut_abundances[:, [4, 5, 11, 15]], axis=1)
    log_fb = np.log((firmicutes + 0.01) / (bacteroidetes + 0.01))

    gut_df_dict["Shannon_Diversity"] = np.round(shannon, 4)
    gut_df_dict["Simpson_Diversity"] = np.round(simpson, 4)
    gut_df_dict["Observed_Richness"] = richness
    gut_df_dict["Pielou_Evenness"]   = np.round(pielou, 4)
    gut_df_dict["SCFA_Producer_Index"] = np.round(scfa_idx, 4)
    gut_df_dict["Butyrate_Producer_Index"] = np.round(butyrate_idx, 4)
    gut_df_dict["Barrier_Associated_Index"] = np.round(barrier_idx, 4)
    gut_df_dict["Inflammation_Associated_Index"] = np.round(infl_idx, 4)
    gut_df_dict["Log_Firmicutes_Bacteroidetes_Ratio"] = np.round(log_fb, 4)

    gut_df = pd.DataFrame(gut_df_dict)

    # ------------------------------------------------------------------
    # 8. Inject Probabilistic Missingness (MAR / MCAR)
    # ------------------------------------------------------------------
    # Clinical Transaminases MAR (12%)
    p_alt_miss = np.clip(1.0 / (1.0 + np.exp(-(-1.2 - 0.02 * (age - 45) - 0.01 * (BMI_obs - 25) - 0.005 * (fpg - 100)))), 0.05, 0.22)
    alt_mask = np.random.binomial(1, p_alt_miss).astype(bool)
    clinical_df.loc[alt_mask, "ALT"] = np.nan
    clinical_df.loc[alt_mask, "AST"] = np.nan

    # Wearable Sensor Dropout MAR (18%)
    p_sensor_drop = np.clip(1.0 / (1.0 + np.exp(-(-1.8 + 0.015 * (age - 45) + 0.03 * (BMI_obs - 25)))), 0.08, 0.28)
    wear_drop_mask = np.random.binomial(1, p_sensor_drop).astype(bool)
    wearable_std_df.loc[wear_drop_mask, "Heart_Rate_Variability_RMSSD"] = np.nan
    wearable_std_df.loc[wear_drop_mask, "Sleep_Efficiency_Score"] = np.nan

    # Wearable Complete Device Absence MCAR (5%)
    dev_abs_mask = np.random.binomial(1, 0.05, size=N_PATIENTS).astype(bool)
    wearable_std_df.loc[dev_abs_mask, wearable_std_df.columns[1:]] = np.nan

    # CGM Structural MAR (80% missing / 20% available)
    dev_access = np.random.normal(0, 1, size=N_PATIENTS)
    p_cgm_avail = np.clip(1.0 / (1.0 + np.exp(-(-2.2 + 0.025 * (age - 45) + 0.015 * (fpg - 100) + 1.2 * fam_hist_diabetes + 0.5 * dev_access))), 0.05, 0.35)
    cgm_avail_mask = np.random.binomial(1, p_cgm_avail).astype(bool)
    wearable_cgm_df.loc[~cgm_avail_mask, wearable_cgm_df.columns[1:]] = np.nan

    # Gut Sequencing Failure MCAR (10%)
    gut_fail_mask = np.random.binomial(1, 0.10, size=N_PATIENTS).astype(bool)
    gut_df.loc[gut_fail_mask, gut_df.columns[1:]] = np.nan

    # ------------------------------------------------------------------
    # 9. Labels & Master Split Manifest
    # ------------------------------------------------------------------
    labels_df = pd.DataFrame({
        "Patient_ID": patient_ids,
        "Type2_Diabetes": Y_T2D,
        "Prediabetes": Y_Prediabetes,
        "Obesity": Y_Obesity,
        "Metabolic_Syndrome": Y_MetS,
        "NAFLD": Y_NAFLD
    })

    # Frozen Master 70/15/15 Patient Split Assignment
    split_assignment = np.array(["Train"] * 14000 + ["Val"] * 3000 + ["Test"] * 3000)
    split_df = pd.DataFrame({
        "Patient_ID": patient_ids,
        "Split": split_assignment
    })

    # Save Export Files
    clinical_df.to_csv(OUTPUT_DIR / "clinical_v3.csv", index=False)
    wearable_std_df.to_csv(OUTPUT_DIR / "wearable_standard_v3.csv", index=False)
    wearable_cgm_df.to_csv(OUTPUT_DIR / "wearable_cgm_v3.csv", index=False)
    gut_df.to_csv(OUTPUT_DIR / "gut_v3.csv", index=False)
    labels_df.to_csv(OUTPUT_DIR / "labels_v3.csv", index=False)
    split_df.to_csv(OUTPUT_DIR / "split_manifest_v3.csv", index=False)

    logger.info(f"Successfully generated all 6 dataset files in {OUTPUT_DIR}.")

    # Return DataFrames for Stage B QC Audit
    return clinical_df, wearable_std_df, wearable_cgm_df, gut_df, labels_df, split_df, L

if __name__ == "__main__":
    run_generation_and_qc()
