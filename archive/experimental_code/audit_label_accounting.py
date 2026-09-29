"""
audit_label_accounting.py — Exact Verification of Label Accounting in labels_v3.csv
"""

import pandas as pd
import numpy as np

def audit_labels():
    labels_df = pd.read_csv("data/multimodal_v3/labels_v3.csv")
    diseases = ["Type2_Diabetes", "Prediabetes", "Obesity", "Metabolic_Syndrome", "NAFLD"]
    
    pos_counts = {d: int(labels_df[d].sum()) for d in diseases}
    prevalences = {d: float(labels_df[d].mean()) for d in diseases}
    total_positives_sum = sum(pos_counts.values())

    # Patient label counts
    patient_label_counts = labels_df[diseases].sum(axis=1)
    label_dist = patient_label_counts.value_counts().sort_index().to_dict()

    weighted_sum = sum(k * count for k, count in label_dist.items())

    t2d_predia_overlap = int(((labels_df["Type2_Diabetes"] == 1) & (labels_df["Prediabetes"] == 1)).sum())

    print("=== EXACT LABEL ACCOUNTING AUDIT ===")
    print(f"Per-Disease Positive Counts: {pos_counts}")
    print(f"Per-Disease Prevalences: {prevalences}")
    print(f"Sum of Per-Disease Positives: {total_positives_sum}")
    print("\nPatient Label Burden Distribution (k diseases per patient):")
    for k in sorted(label_dist.keys()):
        print(f"  {k} Diseases: {label_dist[k]} patients ({label_dist[k]/20000*100:.2f}%)")

    print(f"\nWeighted Sum sum(k * count_k): {weighted_sum}")
    print(f"Mathematical Verification Match: {total_positives_sum == weighted_sum}")
    print(f"T2D & Prediabetes Overlap Count: {t2d_predia_overlap}")

    # Pairwise Phi Correlation Matrix
    corr_matrix = labels_df[diseases].corr(method="pearson")
    print("\nPairwise Phi Correlation Matrix:")
    print(np.round(corr_matrix, 4))

if __name__ == "__main__":
    audit_labels()
