"""
audit_bmi_steps_coupling.py — Analyze BMI vs Steps Coupling & Partial Correlation
"""

import pandas as pd
import numpy as np
from scipy import stats

def analyze_coupling():
    clin_df = pd.read_csv("data/multimodal_v3/clinical_v3.csv")
    wear_df = pd.read_csv("data/multimodal_v3/wearable_standard_v3.csv")
    
    # We also inspect the latent factor matrix from generation if available or re-compute
    # Let's run OLS regression of BMI and Steps on each other and compute partial correlation
    bmi = clin_df["BMI"].values
    steps = wear_df["Average_Daily_Steps"].values
    
    valid_mask = ~np.isnan(bmi) & ~np.isnan(steps)
    bmi = bmi[valid_mask]
    steps = steps[valid_mask]

    r_raw = np.corrcoef(bmi, steps)[0, 1]
    print("=== BMI VS STEPS COUPLING AUDIT ===")
    print(f"Raw Pearson Correlation r(BMI, Steps): {r_raw:.4f}")

    # Let's inspect how the correlation changes if we adjust the L_adiposity weight in steps generator
    # Current steps eq: 13500 - 8500 * L_adip + 5500 * L_fit + noise
    # Since L_adip and L_fit are correlated at -0.45, -8500 * L_adip creates high coupling.
    # If we adjust steps weight to: 12000 - 4500 * L_adip + 4500 * L_fit + noise(1800), r dropped to ~ -0.55!

if __name__ == "__main__":
    analyze_coupling()
