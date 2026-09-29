import os
import pandas as pd
import numpy as np

# Ensure test_reports directory exists
os.makedirs('test_reports', exist_ok=True)

# 1. Clinical Data
clinical_features = [
    "Age", "Gender", "Height", "Weight", "BMI", "Waist_Circumference",
    "Systolic_BP", "Diastolic_BP", "Fasting_Blood_Glucose", "HbA1c",
    "Triglycerides", "HDL", "LDL", "ALT", "AST",
    "Family_History_Diabetes", "Family_History_Hypertension", "Family_History_CVD"
]
clinical_data = {
    "Age": [45], "Gender": [1], "Height": [175], "Weight": [85], "BMI": [27.7], "Waist_Circumference": [95],
    "Systolic_BP": [135], "Diastolic_BP": [85], "Fasting_Blood_Glucose": [110], "HbA1c": [6.1],
    "Triglycerides": [180], "HDL": [40], "LDL": [130], "ALT": [45], "AST": [35],
    "Family_History_Diabetes": [1], "Family_History_Hypertension": [1], "Family_History_CVD": [0]
}
pd.DataFrame(clinical_data, columns=clinical_features).to_csv('test_reports/test_clinical_report.csv', index=False)

# 2. Wearable Data
wearable_features = [
    "Average_Daily_Steps", "Active_Minutes", "Sedentary_Time_Minutes",
    "Resting_Heart_Rate", "Heart_Rate_Variability_RMSSD", "Sleep_Duration_Hours",
    "Sleep_Efficiency_Score", "Autonomic_Stress_Score", "Activity_Energy_Expenditure",
    "Exercise_Frequency_Days",
    "CGM_Average_Glucose", "CGM_Glucose_CV", "CGM_Time_In_Range",
    "CGM_Time_Above_Range", "CGM_Time_Below_Range"
]
wearable_data = {
    "Average_Daily_Steps": [6500], "Active_Minutes": [25], "Sedentary_Time_Minutes": [600],
    "Resting_Heart_Rate": [72], "Heart_Rate_Variability_RMSSD": [45], "Sleep_Duration_Hours": [6.5],
    "Sleep_Efficiency_Score": [82], "Autonomic_Stress_Score": [65], "Activity_Energy_Expenditure": [400],
    "Exercise_Frequency_Days": [2],
    "CGM_Average_Glucose": [115], "CGM_Glucose_CV": [18], "CGM_Time_In_Range": [75],
    "CGM_Time_Above_Range": [20], "CGM_Time_Below_Range": [5]
}
pd.DataFrame(wearable_data, columns=wearable_features).to_csv('test_reports/test_wearable_report.csv', index=False)

# 3. Gut Microbiome Data
gut_taxa = [
    "Akkermansia_muciniphila", "Faecalibacterium_prausnitzii", "Roseburia_intestinalis",
    "Bifidobacterium_longum", "Bifidobacterium_adolescentis", "Bacteroides_thetaiotaomicron",
    "Bacteroides_vulgatus", "Bacteroides_fragilis", "Bacteroides_uniformis", "Prevotella_copri",
    "Ruminococcus_bromii", "Ruminococcus_gnavus", "Blautia_wexlerae", "Blautia_hansenii",
    "Collinsella_aerofaciens", "Escherichia_coli", "Klebsiella_pneumoniae", "Coprococcus_eutactus",
    "Alistipes_putredinis", "Alistipes_finegoldii", "Subdoligranulum_variable", "Enterococcus_faecalis",
    "Eubacterium_rectale", "Eubacterium_hallii", "Parabacteroides_distasonis", "Lactobacillus_acidophilus",
    "Lactobacillus_rhamnosus", "Streptococcus_thermophilus", "Eggerthella_lenta", "Christensenella_minuta",
    "Methanobrevibacter_smithii", "Dialister_invisus", "Holdemanella_biformis", "Barnesiella_intestinihominis",
    "Anaerostipes_caccae", "Phascolarctobacterium_faecium", "Veillonella_parvula", "Fusobacterium_nucleatum",
    "Bilophila_wadsworthia", "Sutterella_wadsworthensis"
]
# Generate random dirichlet distribution summing to 100%
np.random.seed(42)
alpha = np.ones(len(gut_taxa))
gut_abundances = np.random.dirichlet(alpha) * 100.0
gut_data = {taxa: [val] for taxa, val in zip(gut_taxa, gut_abundances)}
pd.DataFrame(gut_data, columns=gut_taxa).to_csv('test_reports/test_gut_report.csv', index=False)

print("Test reports generated successfully in 'test_reports/' folder.")
