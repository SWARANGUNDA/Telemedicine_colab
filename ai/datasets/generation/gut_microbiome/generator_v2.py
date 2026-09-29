"""
generator_v2.py — Revised Latent-Factor Microbiome Generator v2.

Implements:
1. 20 Predictor Taxa + Other_Taxa background community (sums to 100% total, predictor taxa sum to ~60-75%).
2. Sequencing depth & Multinomial read sampling (N ~ 25,000 reads) for realistic zero prevalence.
3. Complete community ecological diversity indices (Shannon, Simpson, Richness, Pielou Evenness).
4. Log_Firmicutes_Bacteroidetes_Ratio.
5. Cautious proxy terminology for derived functional indices:
   - SCFA_Producer_Abundance_Index
   - Butyrate_Producer_Abundance_Index
   - Barrier_Associated_Taxa_Index
   - Inflammation_Associated_Taxa_Index
6. Compositional CLR transformation with pseudocount epsilon=1e-4.
"""

import logging
import numpy as np
import pandas as pd
from typing import Tuple, Dict

logger = logging.getLogger("gut_generator_v2")

PREDICTOR_TAXA_20 = [
    "Akkermansia", "Faecalibacterium", "Roseburia", "Bifidobacterium", "Bacteroides",
    "Prevotella", "Ruminococcus", "Blautia", "Collinsella", "Escherichia_Shigella",
    "Coprococcus", "Alistipes", "Subdoligranulum", "Enterococcus", "Eubacterium",
    "Parabacteroides", "Lactobacillus", "Klebsiella", "Streptococcus", "Eggerthella"
]

ALL_COMMUNITY_COMPONENTS = PREDICTOR_TAXA_20 + ["Other_Taxa"]

FIRMICUTES = [
    "Faecalibacterium", "Roseburia", "Ruminococcus", "Blautia", "Coprococcus",
    "Subdoligranulum", "Enterococcus", "Eubacterium", "Lactobacillus", "Streptococcus"
]

BACTEROIDETES = ["Bacteroides", "Prevotella", "Alistipes", "Parabacteroides"]

SCFA_PRODUCERS = ["Faecalibacterium", "Roseburia", "Bifidobacterium", "Ruminococcus", "Coprococcus", "Eubacterium"]
BUTYRATE_PRODUCERS = ["Faecalibacterium", "Roseburia", "Coprococcus", "Subdoligranulum"]
BARRIER_ASSOCIATED = ["Akkermansia", "Faecalibacterium", "Bifidobacterium"]
INFLAMMATION_ASSOCIATED = ["Escherichia_Shigella", "Collinsella", "Enterococcus", "Klebsiella", "Streptococcus"]


def generate_gut_dataset_v2(
    clinical_csv_path: str = "Clinical_Dataset.csv",
    seed: int = 42,
    target_depth: int = 25000
) -> pd.DataFrame:
    """Generate revised Gut_Dataset_v2.csv with background community and sequencing noise."""
    rng = np.random.default_rng(seed)
    logger.info("Loading Clinical Dataset from %s...", clinical_csv_path)
    clinical_df = pd.read_csv(clinical_csv_path)
    n_patients = len(clinical_df)

    # Fill NaN in clinical biomarkers with population medians before normalizing
    bmi_vals = clinical_df["BMI"].fillna(clinical_df["BMI"].median()).values
    hba1c_vals = clinical_df["HbA1c"].fillna(clinical_df["HbA1c"].median()).values
    glucose_vals = clinical_df["Fasting_Blood_Glucose"].fillna(clinical_df["Fasting_Blood_Glucose"].median()).values
    trig_vals = clinical_df["Triglycerides"].fillna(clinical_df["Triglycerides"].median()).values
    alt_vals = clinical_df["ALT"].fillna(clinical_df["ALT"].median()).values

    # Step 1: Extract Latent Biological Factors (Continuums)
    bmi_norm = np.clip((bmi_vals - 18.5) / 25.0, 0, 1)
    hba1c_norm = np.clip((hba1c_vals - 4.5) / 7.0, 0, 1)
    glucose_norm = np.clip((glucose_vals - 70.0) / 150.0, 0, 1)
    trig_norm = np.clip((trig_vals - 50.0) / 300.0, 0, 1)
    alt_norm = np.clip((alt_vals - 10.0) / 90.0, 0, 1)

    dietary_fiber = rng.beta(2.5, 2.5, size=n_patients) - 0.3 * bmi_norm + rng.normal(0, 0.1, size=n_patients)
    dietary_fiber = np.clip(dietary_fiber, 0.05, 0.95)

    metabolic_stress = (0.35 * bmi_norm + 0.35 * hba1c_norm + 0.2 * trig_norm + 0.1 * alt_norm) + rng.normal(0, 0.08, size=n_patients)
    metabolic_stress = np.clip(metabolic_stress, 0, 1)

    systemic_inflammation = (0.4 * metabolic_stress + 0.4 * alt_norm + 0.2 * glucose_norm) + rng.normal(0, 0.1, size=n_patients)
    systemic_inflammation = np.clip(systemic_inflammation, 0, 1)

    individual_variation = rng.normal(0, 0.15, size=(n_patients, 21))

    # Step 2: Base concentration parameters (Dirichlet / Gamma) for 21 components (20 taxa + Other_Taxa)
    base_alpha = {
        "Akkermansia": 3.5, "Faecalibacterium": 10.5, "Roseburia": 4.5, "Bifidobacterium": 5.5,
        "Bacteroides": 16.0, "Prevotella": 8.5, "Ruminococcus": 4.0, "Blautia": 4.5,
        "Collinsella": 1.5, "Escherichia_Shigella": 1.8, "Coprococcus": 3.2, "Alistipes": 3.5,
        "Subdoligranulum": 2.8, "Enterococcus": 0.8, "Eubacterium": 2.5, "Parabacteroides": 2.8,
        "Lactobacillus": 2.2, "Klebsiella": 0.6, "Streptococcus": 1.2, "Eggerthella": 0.5,
        "Other_Taxa": 32.0  # Background community (represents ~30-40% of total microbiome)
    }

    # Modulating multipliers based on latent factors
    multipliers = np.zeros((n_patients, 21))
    for j, comp in enumerate(ALL_COMMUNITY_COMPONENTS):
        m = np.ones(n_patients)
        if comp in BARRIER_ASSOCIATED:
            m += 0.7 * dietary_fiber - 0.8 * metabolic_stress
        if comp in SCFA_PRODUCERS:
            m += 1.0 * dietary_fiber - 0.6 * metabolic_stress
        if comp in INFLAMMATION_ASSOCIATED:
            m += 1.2 * systemic_inflammation + 0.7 * metabolic_stress - 0.5 * dietary_fiber
        if comp == "Prevotella":
            m += 1.4 * dietary_fiber - 0.4 * (1 - dietary_fiber)
        if comp == "Bacteroides":
            m += 0.5 * (1 - dietary_fiber) + 0.3 * metabolic_stress
        if comp == "Other_Taxa":
            m += 0.3 * (1 - metabolic_stress)  # Healthy guts have slightly higher background diversity

        m += individual_variation[:, j]
        multipliers[:, j] = np.clip(m, 0.05, 3.5)

    # Gamma sampling for true underlying proportions
    gamma_samples = np.zeros((n_patients, 21))
    for j, comp in enumerate(ALL_COMMUNITY_COMPONENTS):
        shape = base_alpha[comp] * multipliers[:, j]
        gamma_samples[:, j] = rng.gamma(shape=shape, scale=1.0)

    # True underlying probability vectors (sums to 1.0 per patient)
    p_true = gamma_samples / gamma_samples.sum(axis=1, keepdims=True)

    # Step 3: Simulate Sequencing Depth & Read Counts (Multinomial Sampling)
    # Read depth N ~ Poisson(25,000)
    read_depths = rng.poisson(target_depth, size=n_patients)
    read_counts = np.zeros((n_patients, 21), dtype=int)

    for i in range(n_patients):
        read_counts[i] = rng.multinomial(n=read_depths[i], pvals=p_true[i])

    # Convert read counts back to relative abundance %
    rel_abundances_all = (read_counts / read_depths[:, np.newaxis]) * 100.0

    # Create DataFrame for all 21 components
    all_comp_df = pd.DataFrame(rel_abundances_all, columns=ALL_COMMUNITY_COMPONENTS)

    # Zero thresholding: Taxa with < 2 reads (or < 0.008%) set to 0.0%
    for comp in ALL_COMMUNITY_COMPONENTS:
        all_comp_df[comp] = all_comp_df[comp].apply(lambda x: 0.0 if x < 0.008 else x)

    # Re-normalize total community (20 taxa + Other_Taxa) to sum to 100.0%
    total_community_sum = all_comp_df[ALL_COMMUNITY_COMPONENTS].sum(axis=1)
    all_comp_df[ALL_COMMUNITY_COMPONENTS] = all_comp_df[ALL_COMMUNITY_COMPONENTS].div(total_community_sum, axis=0) * 100.0

    # Step 4: Compute Ecological Features on Full Community (21 components)
    p_comm = all_comp_df[ALL_COMMUNITY_COMPONENTS].values / 100.0
    p_comm_safe = np.where(p_comm > 0, p_comm, 1e-12)

    # Shannon Diversity Index H'
    shannon = -np.sum(p_comm * np.log(p_comm_safe), axis=1)

    # Simpson Diversity Index D = 1 - sum(p^2)
    simpson = 1.0 - np.sum(p_comm**2, axis=1)

    # Observed Richness (Count of taxa > 0.01%)
    richness = np.sum(p_comm > 1e-4, axis=1)

    # Pielou Evenness J' = H' / ln(Richness)
    evenness = shannon / np.log(np.maximum(richness, 2))

    # Step 5: Compute Derived Functional Proxies (from 20 predictor taxa relative abundances)
    predictor_df = all_comp_df[PREDICTOR_TAXA_20].copy()

    scfa_index = predictor_df[SCFA_PRODUCERS].sum(axis=1)
    butyrate_index = predictor_df[BUTYRATE_PRODUCERS].sum(axis=1)
    barrier_index = predictor_df[BARRIER_ASSOCIATED].sum(axis=1)
    inflammation_index = predictor_df[INFLAMMATION_ASSOCIATED].sum(axis=1)

    firmicutes_sum = predictor_df[FIRMICUTES].sum(axis=1) + 1e-4
    bacteroidetes_sum = predictor_df[BACTEROIDETES].sum(axis=1) + 1e-4
    log_fb_ratio = np.log(firmicutes_sum / bacteroidetes_sum)

    # Step 6: Compute CLR transformed features (on 20 predictor taxa + Other_Taxa)
    epsilon = 1e-4  # 0.01% pseudocount for CLR
    p_comm_eps = p_comm + epsilon
    geom_means = np.exp(np.mean(np.log(p_comm_eps), axis=1, keepdims=True))
    clr_matrix = np.log(p_comm_eps / geom_means)
    
    # We export 20 CLR predictor features
    clr_cols = [f"{t}_CLR" for t in PREDICTOR_TAXA_20]
    clr_df = pd.DataFrame(clr_matrix[:, :20], columns=clr_cols)

    # Step 7: Assemble Final Dataset
    demographics = clinical_df[["Patient_ID", "Age", "Gender"]].copy()
    disease_labels = clinical_df[["Type2_Diabetes", "Prediabetes", "Obesity", "Metabolic_Syndrome", "NAFLD", "Healthy"]].copy()

    metrics_df = pd.DataFrame({
        "Other_Taxa": all_comp_df["Other_Taxa"].round(2),
        "Shannon_Diversity_Index": np.round(shannon, 4),
        "Simpson_Diversity_Index": np.round(simpson, 4),
        "Observed_Richness": richness,
        "Pielou_Evenness": np.round(evenness, 4),
        "SCFA_Producer_Abundance_Index": np.round(scfa_index, 2),
        "Butyrate_Producer_Abundance_Index": np.round(butyrate_index, 2),
        "Barrier_Associated_Taxa_Index": np.round(barrier_index, 2),
        "Inflammation_Associated_Taxa_Index": np.round(inflammation_index, 2),
        "Log_Firmicutes_Bacteroidetes_Ratio": np.round(log_fb_ratio, 4)
    })

    # Output Column Order: Demographics + 20 Predictor Taxa Abundance + Other_Taxa + 20 CLR Features + Ecological & Functional Metrics + Disease Labels
    gut_v2_df = pd.concat([
        demographics,
        predictor_df.round(2),
        clr_df.round(4),
        metrics_df,
        disease_labels
    ], axis=1)

    logger.info("Successfully generated revised Gut_Dataset_v2.csv with %d patients and %d columns.", len(gut_v2_df), gut_v2_df.shape[1])
    return gut_v2_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df_v2 = generate_gut_dataset_v2()
    df_v2.to_csv("Gut_Dataset_v2.csv", index=False)
    print("Revised Gut_Dataset_v2.csv written to workspace root.")
