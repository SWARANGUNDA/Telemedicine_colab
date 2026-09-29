"""
config.py — Configuration parameters, feature schemas, synonym dictionaries,
unit conversion mappings, and physiological bounds for IMDIE.
"""

from typing import Dict, List, Set

# -----------------------------------------------------------------------------
# Modality Classification Keywords & Header Identifiers
# -----------------------------------------------------------------------------
CLINICAL_KEYWORDS: Set[str] = {
    "cbc", "complete blood count", "lipid profile", "fasting blood glucose", "fpg",
    "hba1c", "blood pressure", "systolic", "diastolic", "alt", "ast", "cholesterol",
    "triglycerides", "ldl", "hdl", "liver function test", "lft", "waist",
    "family history", "clinical laboratory report", "specimen", "blood / clinical measurements"
}

WEARABLE_KEYWORDS: Set[str] = {
    "apple health", "samsung health", "google fit", "fitbit", "garmin", "cgm",
    "continuous glucose monitor", "average_daily_steps", "active_minutes",
    "sedentary_time_minutes", "resting_heart_rate", "sleep_duration",
    "calories_burned", "average_glucose", "glucose_variability", "time_in_range",
    "time_above_range", "tir", "tar", "rhr", "steps",
    "wearable & cgm health report", "wearable", "average daily steps", "active minutes",
    "sedentary time", "resting heart rate", "heart rate variability", "sleep score",
    "stress level", "average cgm glucose", "monitoring period"
}

GUT_KEYWORDS: Set[str] = {
    "16s rrna", "microbiome", "akkermansia", "faecalibacterium", "bifidobacterium",
    "roseburia", "escherichia_shigella", "escherichia", "shigella", "blautia",
    "prevotella", "collinsella", "alistipes", "shannon_diversity_index", "shannon index",
    "gut microbiome", "relative abundance", "alpha diversity",
    "gut microbiome analysis report", "firmicutes", "bacteroidetes", "bacteroides",
    "proteobacteria", "shannon diversity index", "shannon diversity", "sample type stool"
}


# -----------------------------------------------------------------------------
# Canonical Feature Schemas per Modality (V4 Publication-Grade Specifications)
# -----------------------------------------------------------------------------
CLINICAL_FEATURES: List[str] = [
    "Age", "Gender", "Height", "Weight", "BMI",
    "Waist_Circumference", "Systolic_BP", "Diastolic_BP",
    "Fasting_Blood_Glucose", "HbA1c", "Triglycerides", "HDL", "LDL",
    "ALT", "AST", "Family_History_Diabetes",
    "Family_History_Hypertension", "Family_History_CVD"
]

WEARABLE_FEATURES: List[str] = [
    "Average_Daily_Steps", "Active_Minutes", "Sedentary_Time_Minutes",
    "Resting_Heart_Rate", "Heart_Rate_Variability_RMSSD", "Sleep_Duration_Hours",
    "Sleep_Efficiency_Score", "Autonomic_Stress_Score", "Activity_Energy_Expenditure",
    "Exercise_Frequency_Days", "CGM_Average_Glucose", "CGM_Glucose_CV",
    "CGM_Time_In_Range", "CGM_Time_Above_Range", "CGM_Time_Below_Range"
]

GUT_TAXA_40: List[str] = [
    "Akkermansia_muciniphila", "Faecalibacterium_prausnitzii", "Roseburia_intestinalis",
    "Bifidobacterium_longum", "Bifidobacterium_adolescentis", "Bacteroides_thetaiotaomicron",
    "Bacteroides_vulgatus", "Bacteroides_fragilis", "Bacteroides_uniformis",
    "Prevotella_copri", "Ruminococcus_bromii", "Ruminococcus_gnavus",
    "Blautia_wexlerae", "Blautia_hansenii", "Collinsella_aerofaciens",
    "Escherichia_coli", "Klebsiella_pneumoniae", "Coprococcus_eutactus",
    "Alistipes_putredinis", "Alistipes_finegoldii", "Subdoligranulum_variable",
    "Enterococcus_faecalis", "Eubacterium_rectale", "Eubacterium_hallii",
    "Parabacteroides_distasonis", "Lactobacillus_acidophilus", "Lactobacillus_rhamnosus",
    "Streptococcus_thermophilus", "Eggerthella_lenta", "Christensenella_minuta",
    "Methanobrevibacter_smithii", "Dialister_invisus", "Holdemanella_biformis",
    "Barnesiella_intestinihominis", "Anaerostipes_caccae", "Phascolarctobacterium_faecium",
    "Veillonella_parvula", "Fusobacterium_nucleatum", "Bilophila_wadsworthia",
    "Sutterella_wadsworthensis"
]

GUT_INDICES_9: List[str] = [
    "Shannon_Diversity", "Simpson_Diversity", "Observed_Richness",
    "Pielou_Evenness", "SCFA_Producer_Index", "Butyrate_Producer_Index",
    "Barrier_Associated_Index", "Inflammation_Associated_Index",
    "Log_Firmicutes_Bacteroidetes_Ratio"
]

# Gut features expected by V4 Gut Expert model payload (40 Taxa + 9 Indices = 49 features)
GUT_FEATURES: List[str] = GUT_TAXA_40 + GUT_INDICES_9

# Disease targets that MUST be excluded from feature dictionary inputs
TARGET_DISEASE_LABELS: Set[str] = {
    "Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"
}


# -----------------------------------------------------------------------------
# Mandatory vs Optional Feature Schemas per Expert
# -----------------------------------------------------------------------------
CLINICAL_MANDATORY: Set[str] = {"Age", "Gender", "Height", "Weight", "BMI", "Systolic_BP", "Diastolic_BP", "Fasting_Blood_Glucose", "HbA1c"}
CLINICAL_OPTIONAL: Set[str] = {"Waist_Circumference", "LDL", "HDL", "Triglycerides", "ALT", "AST", "Family_History_Diabetes", "Family_History_Hypertension", "Family_History_CVD"}

WEARABLE_MANDATORY: Set[str] = {"Average_Daily_Steps", "Resting_Heart_Rate", "CGM_Average_Glucose"}
WEARABLE_OPTIONAL: Set[str] = {"Active_Minutes", "Sedentary_Time_Minutes", "Heart_Rate_Variability_RMSSD", "Sleep_Duration_Hours", "Sleep_Efficiency_Score", "Autonomic_Stress_Score", "Activity_Energy_Expenditure", "Exercise_Frequency_Days", "CGM_Glucose_CV", "CGM_Time_In_Range", "CGM_Time_Above_Range", "CGM_Time_Below_Range"}

GUT_MANDATORY: Set[str] = {"Akkermansia_muciniphila", "Faecalibacterium_prausnitzii", "Bifidobacterium_longum", "Shannon_Diversity"}
GUT_OPTIONAL: Set[str] = set(GUT_TAXA_40[3:]) | set(GUT_INDICES_9[1:]) | {"Other_Taxa"}



# -----------------------------------------------------------------------------
# Feature Synonym / Alias Mappings (Extracted key ➔ Canonical Key)
# -----------------------------------------------------------------------------
FEATURE_ALIASES: Dict[str, str] = {
    # Demographics & Anthropometry
    "patient id": "Patient_ID", "pid": "Patient_ID", "id": "Patient_ID", "patient_id": "Patient_ID", "patlent id": "Patient_ID", "patient": "Patient_ID", "patlent": "Patient_ID",
    "age": "Age", "years": "Age", "agc": "Age", "age sex": "Age",
    "gender": "Gender", "sex": "Gender", "gcnder": "Gender",
    "height": "Height", "height (cm)": "Height", "height_cm": "Height", "height cm": "Height", "ht": "Height", "helght": "Height", "stature": "Height",
    "weight": "Weight", "weight (kg)": "Weight", "weight_kg": "Weight", "weight kg": "Weight", "wt": "Weight", "welght": "Weight", "body weight": "Weight", "mass": "Weight",
    "bmi": "BMI", "body mass index": "BMI",
    "waist": "Waist_Circumference", "waist circumference": "Waist_Circumference", "waist_cm": "Waist_Circumference", "waist circumference cm": "Waist_Circumference", "waist_circumference_cm": "Waist_Circumference", "waist_circumference": "Waist_Circumference", "wc": "Waist_Circumference", "walst clrcumference": "Waist_Circumference",
    
    # Vitals & Blood Pressure
    "blood pressure": "Blood_Pressure", "bp": "Blood_Pressure", "blood pressure reading": "Blood_Pressure", "repeat blood pressure": "Blood_Pressure", "blood pressurc": "Blood_Pressure", "b.p.": "Blood_Pressure",
    "sbp": "Systolic_BP", "systolic": "Systolic_BP", "systolic bp": "Systolic_BP", "systolic_bp": "Systolic_BP", "systolic blood pressure": "Systolic_BP",
    "dbp": "Diastolic_BP", "diastolic": "Diastolic_BP", "diastolic bp": "Diastolic_BP", "diastolic_bp": "Diastolic_BP", "diastolic blood pressure": "Diastolic_BP",

    # Clinical Labs
    "fpg": "Fasting_Blood_Glucose", "fbg": "Fasting_Blood_Glucose", "fbs": "Fasting_Blood_Glucose", "fasting glucose": "Fasting_Blood_Glucose", "fasting blood glucose": "Fasting_Blood_Glucose", "blood glucose": "Fasting_Blood_Glucose", "fasting_blood_glucose": "Fasting_Blood_Glucose", "fastlng blood glucosc": "Fasting_Blood_Glucose", "repeat fasting blood glucose": "Fasting_Blood_Glucose", "bsf": "Fasting_Blood_Glucose", "blood sugar fasting": "Fasting_Blood_Glucose", "fasting sugar": "Fasting_Blood_Glucose", "glu (f)": "Fasting_Blood_Glucose", "fasting blood sugar": "Fasting_Blood_Glucose", "glucose fasting": "Fasting_Blood_Glucose", "plasma glucose (fasting)": "Fasting_Blood_Glucose", "fasting plasma glucose": "Fasting_Blood_Glucose", "f.b.s": "Fasting_Blood_Glucose",
    "hba1c": "HbA1c", "a1c": "HbA1c", "glycated hemoglobin": "HbA1c", "hemoglobin a1c": "HbA1c", "hba1c %": "HbA1c", "hbalc": "HbA1c", "repeat hba1c": "HbA1c", "hgb a1c": "HbA1c", "hgb-a1c": "HbA1c", "ha1c": "HbA1c", "glycosylated hemoglobin": "HbA1c", "glyco hb": "HbA1c", "glyco hb (hba1c)": "HbA1c", "hba1c (glycated hemoglobin)": "HbA1c", "glycosylated haemoglobin": "HbA1c", "glycosylated haemolobin": "HbA1c", "glycated haemoglobin": "HbA1c", "haemoglobin a1c": "HbA1c", "haemoglobin a1c (hba1c)": "HbA1c", "glycosylated haemoglobin (hba1c)": "HbA1c", "glycosylated haemolobin (hba1c)": "HbA1c",
    "ldl": "LDL", "ldl cholesterol": "LDL", "ldl_cholesterol": "LDL", "ldl-c": "LDL", "ldl_c": "LDL", "ldl ch0lesterol": "LDL", "repeat ldl cholesterol": "LDL", "ldl mg dl": "LDL", "low density lipoprotein": "LDL", "cholesterol - ldl (direct)": "LDL", "s. cholesterol ldl": "LDL", "cholesterol - ldl": "LDL",
    "hdl": "HDL", "hdl cholesterol": "HDL", "hdl_cholesterol": "HDL", "hdl-c": "HDL", "hdl_c": "HDL", "hdl ch0lesterol": "HDL", "high density lipoprotein": "HDL", "cholesterol - hdl (direct)": "HDL", "s. cholesterol hdl": "HDL", "cholesterol - hdl": "HDL",
    "triglycerides": "Triglycerides", "tg": "Triglycerides", "triglyceride": "Triglycerides", "triglycerides mg/dl": "Triglycerides", "trlglycerldes": "Triglycerides", "triglycerides mg dl": "Triglycerides", "trig": "Triglycerides", "tgs": "Triglycerides", "tryglycerides": "Triglycerides", "trigs": "Triglycerides", "s. triglycerides": "Triglycerides", "s. tryglycerides": "Triglycerides", "serum tryglycerides": "Triglycerides", "serum triglycerides": "Triglycerides",
    "alt": "ALT", "sgpt": "ALT", "alt (sgpt)": "ALT", "alt sgpt": "ALT", "alanine aminotransferase": "ALT", "alanine transaminase": "ALT", "sgpt alt": "ALT", "alanine aminotransferase (alt/sgpt)": "ALT", "s. alt/sgpt": "ALT", "alt/sgpt": "ALT", "sgpt (alt)": "ALT",
    "ast": "AST", "sgot": "AST", "ast (sgot)": "AST", "ast sgot": "AST", "aspartate aminotransferase": "AST", "aspartate transaminase": "AST", "sgot ast": "AST", "aspartate aminotransferase (ast/sgot)": "AST", "s. ast/sgot": "AST", "ast/sgot": "AST", "sgot (ast)": "AST",
    
    # Family History
    "family history diabetes": "Family_History_Diabetes", "family_history_diabetes": "Family_History_Diabetes", "family history of diabetes": "Family_History_Diabetes", "family history: diabetes": "Family_History_Diabetes", "diabetes": "Family_History_Diabetes", "dlabetes": "Family_History_Diabetes",
    "family history hypertension": "Family_History_Hypertension", "family_history_hypertension": "Family_History_Hypertension", "family history of hypertension": "Family_History_Hypertension", "family history: hypertension": "Family_History_Hypertension", "hypertension": "Family_History_Hypertension", "hypertenslon": "Family_History_Hypertension",
    "family history cvd": "Family_History_CVD", "family_history_cvd": "Family_History_CVD", "family history of cvd": "Family_History_CVD", "family history cardiovascular disease": "Family_History_CVD", "family history: cvd": "Family_History_CVD",

    # Wearables (V4 Specifications)
    "steps": "Average_Daily_Steps", "daily steps": "Average_Daily_Steps", "average_daily_steps": "Average_Daily_Steps", "average daily steps": "Average_Daily_Steps", "step count": "Average_Daily_Steps",
    "active minutes": "Active_Minutes", "active_minutes": "Active_Minutes", "mvpa": "Active_Minutes",
    "sedentary minutes": "Sedentary_Time_Minutes", "sedentary time": "Sedentary_Time_Minutes", "sedentary_time_minutes": "Sedentary_Time_Minutes", "sedentary time minutes": "Sedentary_Time_Minutes",
    "resting heart rate": "Resting_Heart_Rate", "rhr": "Resting_Heart_Rate", "resting_heart_rate": "Resting_Heart_Rate", "pulse": "Resting_Heart_Rate", "pulse rate": "Resting_Heart_Rate", "hr": "Resting_Heart_Rate",
    "heart rate variability": "Heart_Rate_Variability_RMSSD", "hrv": "Heart_Rate_Variability_RMSSD", "heart_rate_variability_rmssd": "Heart_Rate_Variability_RMSSD",
    "sleep duration": "Sleep_Duration_Hours", "sleep hours": "Sleep_Duration_Hours", "sleep_duration": "Sleep_Duration_Hours", "sleep_duration_hours": "Sleep_Duration_Hours",
    "sleep score": "Sleep_Efficiency_Score", "sleep efficiency": "Sleep_Efficiency_Score", "sleep_efficiency_score": "Sleep_Efficiency_Score",
    "stress level": "Autonomic_Stress_Score", "autonomic stress score": "Autonomic_Stress_Score", "autonomic_stress_score": "Autonomic_Stress_Score",
    "calories burned": "Activity_Energy_Expenditure", "calories": "Activity_Energy_Expenditure", "activity_energy_expenditure": "Activity_Energy_Expenditure", "calories_burned": "Activity_Energy_Expenditure",
    "exercise frequency": "Exercise_Frequency_Days", "exercise_frequency_days": "Exercise_Frequency_Days", "exercise days": "Exercise_Frequency_Days",

    # CGM (V4 Specifications)
    "average glucose": "CGM_Average_Glucose", "mean glucose": "CGM_Average_Glucose", "average cgm glucose": "CGM_Average_Glucose", "cgm average glucose": "CGM_Average_Glucose", "cgm_average_glucose": "CGM_Average_Glucose", "average_glucose": "CGM_Average_Glucose",
    "glucose variability": "CGM_Glucose_CV", "glucose sd": "CGM_Glucose_CV", "glucose cv": "CGM_Glucose_CV", "cgm_glucose_cv": "CGM_Glucose_CV", "cgm glucose cv": "CGM_Glucose_CV", "glucose_variability": "CGM_Glucose_CV",
    "tir": "CGM_Time_In_Range", "time in range": "CGM_Time_In_Range", "time_in_range": "CGM_Time_In_Range", "cgm time in range": "CGM_Time_In_Range", "cgm_time_in_range": "CGM_Time_In_Range",
    "tar": "CGM_Time_Above_Range", "time above range": "CGM_Time_Above_Range", "time_above_range": "CGM_Time_Above_Range", "cgm time above range": "CGM_Time_Above_Range", "cgm_time_above_range": "CGM_Time_Above_Range",
    "tbr": "CGM_Time_Below_Range", "time below range": "CGM_Time_Below_Range", "time_below_range": "CGM_Time_Below_Range", "cgm time below range": "CGM_Time_Below_Range", "cgm_time_below_range": "CGM_Time_Below_Range",

    # V4 Gut Microbiome (40 Taxa + 9 Derived Indices)
    "shannon diversity index": "Shannon_Diversity", "shannon diversity": "Shannon_Diversity", "shannon index": "Shannon_Diversity", "shannon_diversity": "Shannon_Diversity", "shannon_diversity_index": "Shannon_Diversity",
    "simpson diversity": "Simpson_Diversity", "simpson_diversity": "Simpson_Diversity",
    "observed richness": "Observed_Richness", "observed_richness": "Observed_Richness",
    "pielou evenness": "Pielou_Evenness", "pielou_evenness": "Pielou_Evenness",
    "scfa producer index": "SCFA_Producer_Index", "scfa_producer_index": "SCFA_Producer_Index",
    "butyrate producer index": "Butyrate_Producer_Index", "butyrate_producer_index": "Butyrate_Producer_Index",
    "barrier associated index": "Barrier_Associated_Index", "barrier_associated_index": "Barrier_Associated_Index",
    "inflammation associated index": "Inflammation_Associated_Index", "inflammation_associated_index": "Inflammation_Associated_Index",
    "log firmicutes bacteroidetes ratio": "Log_Firmicutes_Bacteroidetes_Ratio", "log_firmicutes_bacteroidetes_ratio": "Log_Firmicutes_Bacteroidetes_Ratio",
    "other_taxa": "Other_Taxa", "other taxa": "Other_Taxa",

    # 40 Taxa Species and Genus Aliases
    "akkermansia": "Akkermansia_muciniphila", "akkermansia muciniphila": "Akkermansia_muciniphila", "akkermansia_muciniphila": "Akkermansia_muciniphila",
    "faecalibacterium": "Faecalibacterium_prausnitzii", "faecalibacterium prausnitzii": "Faecalibacterium_prausnitzii", "faecalibacterium_prausnitzii": "Faecalibacterium_prausnitzii",
    "roseburia": "Roseburia_intestinalis", "roseburia intestinalis": "Roseburia_intestinalis", "roseburia_intestinalis": "Roseburia_intestinalis",
    "bifidobacterium": "Bifidobacterium_longum", "bifidobacterium longum": "Bifidobacterium_longum", "bifidobacterium_longum": "Bifidobacterium_longum",
    "bifidobacterium adolescentis": "Bifidobacterium_adolescentis", "bifidobacterium_adolescentis": "Bifidobacterium_adolescentis",
    "bacteroides thetaiotaomicron": "Bacteroides_thetaiotaomicron", "bacteroides_thetaiotaomicron": "Bacteroides_thetaiotaomicron",
    "bacteroides vulgatus": "Bacteroides_vulgatus", "bacteroides_vulgatus": "Bacteroides_vulgatus",
    "bacteroides": "Bacteroides_vulgatus", "bacteroides fragilis": "Bacteroides_fragilis", "bacteroides_fragilis": "Bacteroides_fragilis",
    "bacteroides uniformis": "Bacteroides_uniformis", "bacteroides_uniformis": "Bacteroides_uniformis",
    "prevotella": "Prevotella_copri", "prevotella copri": "Prevotella_copri", "prevotella_copri": "Prevotella_copri",
    "ruminococcus bromii": "Ruminococcus_bromii", "ruminococcus_bromii": "Ruminococcus_bromii",
    "ruminococcus": "Ruminococcus_gnavus", "ruminococcus gnavus": "Ruminococcus_gnavus", "ruminococcus_gnavus": "Ruminococcus_gnavus",
    "blautia": "Blautia_wexlerae", "blautia wexlerae": "Blautia_wexlerae", "blautia_wexlerae": "Blautia_wexlerae",
    "blautia hansenii": "Blautia_hansenii", "blautia_hansenii": "Blautia_hansenii",
    "collinsella": "Collinsella_aerofaciens", "collinsella aerofaciens": "Collinsella_aerofaciens", "collinsella_aerofaciens": "Collinsella_aerofaciens",
    "escherichia": "Escherichia_coli", "escherichia coli": "Escherichia_coli", "escherichia_coli": "Escherichia_coli", "escherichia_shigella": "Escherichia_coli",
    "klebsiella": "Klebsiella_pneumoniae", "klebsiella pneumoniae": "Klebsiella_pneumoniae", "klebsiella_pneumoniae": "Klebsiella_pneumoniae",
    "coprococcus": "Coprococcus_eutactus", "coprococcus eutactus": "Coprococcus_eutactus", "coprococcus_eutactus": "Coprococcus_eutactus",
    "alistipes": "Alistipes_putredinis", "alistipes putredinis": "Alistipes_putredinis", "alistipes_putredinis": "Alistipes_putredinis",
    "alistipes finegoldii": "Alistipes_finegoldii", "alistipes_finegoldii": "Alistipes_finegoldii",
    "subdoligranulum": "Subdoligranulum_variable", "subdoligranulum variable": "Subdoligranulum_variable", "subdoligranulum_variable": "Subdoligranulum_variable",
    "enterococcus": "Enterococcus_faecalis", "enterococcus faecalis": "Enterococcus_faecalis", "enterococcus_faecalis": "Enterococcus_faecalis",
    "eubacterium rectale": "Eubacterium_rectale", "eubacterium_rectale": "Eubacterium_rectale",
    "eubacterium": "Eubacterium_hallii", "eubacterium hallii": "Eubacterium_hallii", "eubacterium_hallii": "Eubacterium_hallii",
    "parabacteroides": "Parabacteroides_distasonis", "parabacteroides distasonis": "Parabacteroides_distasonis", "parabacteroides_distasonis": "Parabacteroides_distasonis",
    "lactobacillus": "Lactobacillus_acidophilus", "lactobacillus acidophilus": "Lactobacillus_acidophilus", "lactobacillus_acidophilus": "Lactobacillus_acidophilus",
    "lactobacillus rhamnosus": "Lactobacillus_rhamnosus", "lactobacillus_rhamnosus": "Lactobacillus_rhamnosus",
    "streptococcus": "Streptococcus_thermophilus", "streptococcus thermophilus": "Streptococcus_thermophilus", "streptococcus_thermophilus": "Streptococcus_thermophilus",
    "eggerthella": "Eggerthella_lenta", "eggerthella lenta": "Eggerthella_lenta", "eggerthella_lenta": "Eggerthella_lenta",
    "christensenella": "Christensenella_minuta", "christensenella minuta": "Christensenella_minuta", "christensenella_minuta": "Christensenella_minuta",
    "methanobrevibacter": "Methanobrevibacter_smithii", "methanobrevibacter smithii": "Methanobrevibacter_smithii", "methanobrevibacter_smithii": "Methanobrevibacter_smithii",
    "dialister": "Dialister_invisus", "dialister invisus": "Dialister_invisus", "dialister_invisus": "Dialister_invisus",
    "holdemanella": "Holdemanella_biformis", "holdemanella biformis": "Holdemanella_biformis", "holdemanella_biformis": "Holdemanella_biformis",
    "barnesiella": "Barnesiella_intestinihominis", "barnesiella intestinihominis": "Barnesiella_intestinihominis", "barnesiella_intestinihominis": "Barnesiella_intestinihominis",
    "anaerostipes": "Anaerostipes_caccae", "anaerostipes caccae": "Anaerostipes_caccae", "anaerostipes_caccae": "Anaerostipes_caccae",
    "phascolarctobacterium": "Phascolarctobacterium_faecium", "phascolarctobacterium faecium": "Phascolarctobacterium_faecium", "phascolarctobacterium_faecium": "Phascolarctobacterium_faecium",
    "veillonella": "Veillonella_parvula", "veillonella parvula": "Veillonella_parvula", "veillonella_parvula": "Veillonella_parvula",
    "fusobacterium": "Fusobacterium_nucleatum", "fusobacterium nucleatum": "Fusobacterium_nucleatum", "fusobacterium_nucleatum": "Fusobacterium_nucleatum",
    "bilophila": "Bilophila_wadsworthia", "bilophila wadsworthia": "Bilophila_wadsworthia", "bilophila_wadsworthia": "Bilophila_wadsworthia",
    "sutterella": "Sutterella_wadsworthensis", "sutterella wadsworthensis": "Sutterella_wadsworthensis", "sutterella_wadsworthensis": "Sutterella_wadsworthensis"
}


# -----------------------------------------------------------------------------
# Physiological Validation Ranges
# -----------------------------------------------------------------------------
PHYSIOLOGICAL_BOUNDS: Dict[str, Dict[str, float]] = {
    # Demographics & Body
    "Age": {"min": 18.0, "max": 100.0},
    "Height_cm": {"min": 120.0, "max": 230.0},
    "Weight_kg": {"min": 30.0, "max": 250.0},
    "BMI": {"min": 12.0, "max": 65.0},
    "Waist_Circumference_cm": {"min": 50.0, "max": 180.0},
    
    # Blood Pressure & Labs
    "Systolic_BP": {"min": 70.0, "max": 240.0},
    "Diastolic_BP": {"min": 40.0, "max": 140.0},
    "Fasting_Blood_Glucose": {"min": 50.0, "max": 400.0},
    "HbA1c": {"min": 3.5, "max": 16.0},
    "LDL_Cholesterol": {"min": 20.0, "max": 400.0},
    "HDL_Cholesterol": {"min": 10.0, "max": 120.0},
    "Triglycerides": {"min": 20.0, "max": 1000.0},
    "ALT": {"min": 2.0, "max": 500.0},
    "AST": {"min": 2.0, "max": 500.0},
    
    # Wearables
    "Average_Daily_Steps": {"min": 500.0, "max": 40000.0},
    "Active_Minutes": {"min": 0.0, "max": 360.0},
    "Sedentary_Time_Minutes": {"min": 60.0, "max": 1200.0},
    "Resting_Heart_Rate": {"min": 35.0, "max": 140.0},
    "Sleep_Duration": {"min": 2.0, "max": 16.0},
    "Calories_Burned": {"min": 500.0, "max": 8000.0},
    "Average_Glucose": {"min": 50.0, "max": 400.0},
    "Glucose_Variability": {"min": 2.0, "max": 80.0},
    "Time_In_Range": {"min": 0.0, "max": 100.0},
    "Time_Above_Range": {"min": 0.0, "max": 100.0},
    
    # Gut Microbiome
    "Akkermansia": {"min": 0.0, "max": 30.0},
    "Faecalibacterium": {"min": 0.0, "max": 40.0},
    "Bifidobacterium": {"min": 0.0, "max": 30.0},
    "Roseburia": {"min": 0.0, "max": 25.0},
    "Escherichia_Shigella": {"min": 0.0, "max": 25.0},
    "Blautia": {"min": 0.0, "max": 30.0},
    "Prevotella": {"min": 0.0, "max": 40.0},
    "Collinsella": {"min": 0.0, "max": 20.0},
    "Alistipes": {"min": 0.0, "max": 20.0},
    "Shannon_Diversity_Index": {"min": 0.5, "max": 6.0}
}
