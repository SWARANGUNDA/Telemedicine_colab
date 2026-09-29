// -----------------------------------------------------------------------------
// Canonical V4 Feature Specifications
// -----------------------------------------------------------------------------
export const CLINICAL_V4_FEATURES = [
  "Age", "Gender", "Height", "Weight", "BMI",
  "Waist_Circumference", "Systolic_BP", "Diastolic_BP",
  "Fasting_Blood_Glucose", "HbA1c", "Triglycerides", "HDL", "LDL",
  "ALT", "AST", "Family_History_Diabetes",
  "Family_History_Hypertension", "Family_History_CVD"
];

export const WEARABLE_V4_FEATURES = [
  "Average_Daily_Steps", "Active_Minutes", "Sedentary_Time_Minutes",
  "Resting_Heart_Rate", "Heart_Rate_Variability_RMSSD", "Sleep_Duration_Hours",
  "Sleep_Efficiency_Score", "Autonomic_Stress_Score", "Activity_Energy_Expenditure",
  "Exercise_Frequency_Days", "CGM_Average_Glucose", "CGM_Glucose_CV",
  "CGM_Time_In_Range", "CGM_Time_Above_Range", "CGM_Time_Below_Range"
];

export const GUT_V4_TAXA_40 = [
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
];

export const GUT_V4_INDICES_9 = [
  "Shannon_Diversity", "Simpson_Diversity", "Observed_Richness",
  "Pielou_Evenness", "SCFA_Producer_Index", "Butyrate_Producer_Index",
  "Barrier_Associated_Index", "Inflammation_Associated_Index",
  "Log_Firmicutes_Bacteroidetes_Ratio"
];

export const GUT_V4_TOTAL_FEATURES = [...GUT_V4_TAXA_40, ...GUT_V4_INDICES_9];

/**
 * Detect normalized modality ('clinical' | 'wearable/cgm' | 'gut_microbiome') for a file object.
 * Explicit metadata on file object takes highest precedence (e.g. for instant test shortcuts).
 */
export function detectFileModality(file) {
  if (!file) return 'clinical';
  
  if (file.modality) {
    if (file.modality === 'clinical' || file.modality === 'wearable/cgm' || file.modality === 'gut_microbiome') {
      return file.modality;
    }
    if (file.modality === 'wearable' || file.modality === 'cgm' || file.modality === 'wearables') return 'wearable/cgm';
    if (file.modality === 'gut' || file.modality === 'microbiome') return 'gut_microbiome';
    if (file.modality === 'clinical_lab') return 'clinical';
  }

  const name = (file.name || '').toLowerCase();

  if (name.includes('gut') || name.includes('microbiome') || name.includes('ayumetrix') || name.includes('16s') || name.includes('taxa')) {
    return 'gut_microbiome';
  }

  if (name.includes('wearable') || name.includes('fitbit') || name.includes('cgm') || name.includes('telemetry') || name.includes('hrv') || name.includes('garmin') || name.includes('apple_watch') || name.includes('sensor')) {
    return 'wearable/cgm';
  }

  if (name.includes('clinical') || name.includes('lab') || name.includes('cmp') || name.includes('lipid') || name.includes('cbc') || name.includes('hba1c') || name.includes('apollo')) {
    return 'clinical';
  }

  if (name.endsWith('.csv')) {
    return 'wearable/cgm';
  }

  return 'clinical';
}

// Canonical Alias Normalizer Map
export const CANONICAL_ALIASES = {
  'patient_id': 'Patient_ID', 'patient id': 'Patient_ID', 'pid': 'Patient_ID', 'id': 'Patient_ID',
  'age': 'Age', 'years': 'Age',
  'gender': 'Gender', 'sex': 'Gender',
  'height': 'Height', 'height_cm': 'Height', 'height cm': 'Height', 'height (cm)': 'Height',
  'weight': 'Weight', 'weight_kg': 'Weight', 'weight kg': 'Weight', 'weight (kg)': 'Weight',
  'bmi': 'BMI', 'body mass index': 'BMI',
  'waist': 'Waist_Circumference', 'waist_circumference': 'Waist_Circumference', 'waist_circumference_cm': 'Waist_Circumference', 'waist_cm': 'Waist_Circumference', 'waist circumference': 'Waist_Circumference',
  'systolic_bp': 'Systolic_BP', 'systolic bp': 'Systolic_BP', 'sbp': 'Systolic_BP', 'systolic': 'Systolic_BP',
  'diastolic_bp': 'Diastolic_BP', 'diastolic bp': 'Diastolic_BP', 'dbp': 'Diastolic_BP', 'diastolic': 'Diastolic_BP',
  'fasting_blood_glucose': 'Fasting_Blood_Glucose', 'fasting blood glucose': 'Fasting_Blood_Glucose', 'fpg': 'Fasting_Blood_Glucose', 'fbg': 'Fasting_Blood_Glucose', 'fasting glucose': 'Fasting_Blood_Glucose',
  'hba1c': 'HbA1c', 'a1c': 'HbA1c', 'glycated hemoglobin': 'HbA1c', 'hemoglobin a1c': 'HbA1c',
  'triglycerides': 'Triglycerides', 'tg': 'Triglycerides', 'triglyceride': 'Triglycerides',
  'hdl': 'HDL', 'hdl_cholesterol': 'HDL', 'hdl cholesterol': 'HDL', 'hdl-c': 'HDL',
  'ldl': 'LDL', 'ldl_cholesterol': 'LDL', 'ldl cholesterol': 'LDL', 'ldl-c': 'LDL',
  'alt': 'ALT', 'sgpt': 'ALT', 'alanine aminotransferase': 'ALT',
  'ast': 'AST', 'sgot': 'AST', 'aspartate aminotransferase': 'AST',
  'family_history_diabetes': 'Family_History_Diabetes', 'family history diabetes': 'Family_History_Diabetes',
  'family_history_hypertension': 'Family_History_Hypertension', 'family history hypertension': 'Family_History_Hypertension',
  'family_history_cvd': 'Family_History_CVD', 'family history cvd': 'Family_History_CVD',

  // Wearables V4
  'average_daily_steps': 'Average_Daily_Steps', 'average daily steps': 'Average_Daily_Steps', 'steps': 'Average_Daily_Steps', 'daily steps': 'Average_Daily_Steps',
  'active_minutes': 'Active_Minutes', 'active minutes': 'Active_Minutes', 'mvpa': 'Active_Minutes',
  'sedentary_time_minutes': 'Sedentary_Time_Minutes', 'sedentary time minutes': 'Sedentary_Time_Minutes', 'sedentary minutes': 'Sedentary_Time_Minutes',
  'resting_heart_rate': 'Resting_Heart_Rate', 'resting heart rate': 'Resting_Heart_Rate', 'rhr': 'Resting_Heart_Rate',
  'heart_rate_variability_rmssd': 'Heart_Rate_Variability_RMSSD', 'heart rate variability': 'Heart_Rate_Variability_RMSSD', 'hrv': 'Heart_Rate_Variability_RMSSD',
  'sleep_duration_hours': 'Sleep_Duration_Hours', 'sleep duration': 'Sleep_Duration_Hours', 'sleep duration hours': 'Sleep_Duration_Hours', 'sleep hours': 'Sleep_Duration_Hours', 'sleep_duration': 'Sleep_Duration_Hours',
  'sleep_efficiency_score': 'Sleep_Efficiency_Score', 'sleep efficiency': 'Sleep_Efficiency_Score', 'sleep score': 'Sleep_Efficiency_Score',
  'autonomic_stress_score': 'Autonomic_Stress_Score', 'autonomic stress score': 'Autonomic_Stress_Score', 'stress score': 'Autonomic_Stress_Score',
  'activity_energy_expenditure': 'Activity_Energy_Expenditure', 'calories burned': 'Activity_Energy_Expenditure', 'calories': 'Activity_Energy_Expenditure', 'calories_burned': 'Activity_Energy_Expenditure',
  'exercise_frequency_days': 'Exercise_Frequency_Days', 'exercise frequency': 'Exercise_Frequency_Days', 'exercise days': 'Exercise_Frequency_Days',

  // CGM V4
  'cgm_average_glucose': 'CGM_Average_Glucose', 'average_glucose': 'CGM_Average_Glucose', 'average glucose': 'CGM_Average_Glucose', 'mean glucose': 'CGM_Average_Glucose',
  'cgm_glucose_cv': 'CGM_Glucose_CV', 'glucose_variability': 'CGM_Glucose_CV', 'glucose variability': 'CGM_Glucose_CV', 'glucose cv': 'CGM_Glucose_CV',
  'cgm_time_in_range': 'CGM_Time_In_Range', 'time_in_range': 'CGM_Time_In_Range', 'time in range': 'CGM_Time_In_Range', 'tir': 'CGM_Time_In_Range',
  'cgm_time_above_range': 'CGM_Time_Above_Range', 'time_above_range': 'CGM_Time_Above_Range', 'time above range': 'CGM_Time_Above_Range', 'tar': 'CGM_Time_Above_Range',
  'cgm_time_below_range': 'CGM_Time_Below_Range', 'time_below_range': 'CGM_Time_Below_Range', 'time below range': 'CGM_Time_Below_Range', 'tbr': 'CGM_Time_Below_Range',

  // V4 40 Species Taxa Aliases
  'akkermansia': 'Akkermansia_muciniphila', 'akkermansia muciniphila': 'Akkermansia_muciniphila', 'akkermansia_muciniphila': 'Akkermansia_muciniphila',
  'faecalibacterium': 'Faecalibacterium_prausnitzii', 'faecalibacterium prausnitzii': 'Faecalibacterium_prausnitzii', 'faecalibacterium_prausnitzii': 'Faecalibacterium_prausnitzii',
  'roseburia': 'Roseburia_intestinalis', 'roseburia intestinalis': 'Roseburia_intestinalis', 'roseburia_intestinalis': 'Roseburia_intestinalis',
  'bifidobacterium': 'Bifidobacterium_longum', 'bifidobacterium longum': 'Bifidobacterium_longum', 'bifidobacterium_longum': 'Bifidobacterium_longum',
  'bifidobacterium adolescentis': 'Bifidobacterium_adolescentis', 'bifidobacterium_adolescentis': 'Bifidobacterium_adolescentis',
  'bacteroides thetaiotaomicron': 'Bacteroides_thetaiotaomicron', 'bacteroides_thetaiotaomicron': 'Bacteroides_thetaiotaomicron',
  'bacteroides vulgatus': 'Bacteroides_vulgatus', 'bacteroides_vulgatus': 'Bacteroides_vulgatus', 'bacteroides': 'Bacteroides_vulgatus',
  'bacteroides fragilis': 'Bacteroides_fragilis', 'bacteroides_fragilis': 'Bacteroides_fragilis',
  'bacteroides uniformis': 'Bacteroides_uniformis', 'bacteroides_uniformis': 'Bacteroides_uniformis',
  'prevotella': 'Prevotella_copri', 'prevotella copri': 'Prevotella_copri', 'prevotella_copri': 'Prevotella_copri',
  'ruminococcus bromii': 'Ruminococcus_bromii', 'ruminococcus_bromii': 'Ruminococcus_bromii',
  'ruminococcus': 'Ruminococcus_gnavus', 'ruminococcus gnavus': 'Ruminococcus_gnavus', 'ruminococcus_gnavus': 'Ruminococcus_gnavus',
  'blautia': 'Blautia_wexlerae', 'blautia wexlerae': 'Blautia_wexlerae', 'blautia_wexlerae': 'Blautia_wexlerae',
  'blautia hansenii': 'Blautia_hansenii', 'blautia_hansenii': 'Blautia_hansenii',
  'collinsella': 'Collinsella_aerofaciens', 'collinsella aerofaciens': 'Collinsella_aerofaciens', 'collinsella_aerofaciens': 'Collinsella_aerofaciens',
  'escherichia': 'Escherichia_coli', 'escherichia coli': 'Escherichia_coli', 'escherichia_coli': 'Escherichia_coli', 'escherichia_shigella': 'Escherichia_coli',
  'klebsiella': 'Klebsiella_pneumoniae', 'klebsiella pneumoniae': 'Klebsiella_pneumoniae', 'klebsiella_pneumoniae': 'Klebsiella_pneumoniae',
  'coprococcus': 'Coprococcus_eutactus', 'coprococcus eutactus': 'Coprococcus_eutactus', 'coprococcus_eutactus': 'Coprococcus_eutactus',
  'alistipes': 'Alistipes_putredinis', 'alistipes putredinis': 'Alistipes_putredinis', 'alistipes_putredinis': 'Alistipes_putredinis',
  'alistipes finegoldii': 'Alistipes_finegoldii', 'alistipes_finegoldii': 'Alistipes_finegoldii',
  'subdoligranulum': 'Subdoligranulum_variable', 'subdoligranulum variable': 'Subdoligranulum_variable', 'subdoligranulum_variable': 'Subdoligranulum_variable',
  'enterococcus': 'Enterococcus_faecalis', 'enterococcus faecalis': 'Enterococcus_faecalis', 'enterococcus_faecalis': 'Enterococcus_faecalis',
  'eubacterium rectale': 'Eubacterium_rectale', 'eubacterium_rectale': 'Eubacterium_rectale',
  'eubacterium': 'Eubacterium_hallii', 'eubacterium hallii': 'Eubacterium_hallii', 'eubacterium_hallii': 'Eubacterium_hallii',
  'parabacteroides': 'Parabacteroides_distasonis', 'parabacteroides distasonis': 'Parabacteroides_distasonis', 'parabacteroides_distasonis': 'Parabacteroides_distasonis',
  'lactobacillus': 'Lactobacillus_acidophilus', 'lactobacillus acidophilus': 'Lactobacillus_acidophilus', 'lactobacillus_acidophilus': 'Lactobacillus_acidophilus',
  'lactobacillus rhamnosus': 'Lactobacillus_rhamnosus', 'lactobacillus_rhamnosus': 'Lactobacillus_rhamnosus',
  'streptococcus': 'Streptococcus_thermophilus', 'streptococcus thermophilus': 'Streptococcus_thermophilus', 'streptococcus_thermophilus': 'Streptococcus_thermophilus',
  'eggerthella': 'Eggerthella_lenta', 'eggerthella lenta': 'Eggerthella_lenta', 'eggerthella_lenta': 'Eggerthella_lenta',
  'christensenella': 'Christensenella_minuta', 'christensenella minuta': 'Christensenella_minuta', 'christensenella_minuta': 'Christensenella_minuta',
  'methanobrevibacter': 'Methanobrevibacter_smithii', 'methanobrevibacter smithii': 'Methanobrevibacter_smithii', 'methanobrevibacter_smithii': 'Methanobrevibacter_smithii',
  'dialister': 'Dialister_invisus', 'dialister invisus': 'Dialister_invisus', 'dialister_invisus': 'Dialister_invisus',
  'holdemanella': 'Holdemanella_biformis', 'holdemanella biformis': 'Holdemanella_biformis', 'holdemanella_biformis': 'Holdemanella_biformis',
  'barnesiella': 'Barnesiella_intestinihominis', 'barnesiella intestinihominis': 'Barnesiella_intestinihominis', 'barnesiella_intestinihominis': 'Barnesiella_intestinihominis',
  'anaerostipes': 'Anaerostipes_caccae', 'anaerostipes caccae': 'Anaerostipes_caccae', 'anaerostipes_caccae': 'Anaerostipes_caccae',
  'phascolarctobacterium': 'Phascolarctobacterium_faecium', 'phascolarctobacterium faecium': 'Phascolarctobacterium_faecium', 'phascolarctobacterium_faecium': 'Phascolarctobacterium_faecium',
  'veillonella': 'Veillonella_parvula', 'veillonella parvula': 'Veillonella_parvula', 'veillonella_parvula': 'Veillonella_parvula',
  'fusobacterium': 'Fusobacterium_nucleatum', 'fusobacterium nucleatum': 'Fusobacterium_nucleatum', 'fusobacterium_nucleatum': 'Fusobacterium_nucleatum',
  'bilophila': 'Bilophila_wadsworthia', 'bilophila wadsworthia': 'Bilophila_wadsworthia', 'bilophila_wadsworthia': 'Bilophila_wadsworthia',
  'sutterella': 'Sutterella_wadsworthensis', 'sutterella wadsworthensis': 'Sutterella_wadsworthensis', 'sutterella_wadsworthensis': 'Sutterella_wadsworthensis',
  'other_taxa': 'Other_Taxa', 'other taxa': 'Other_Taxa'
};

export function normalizeRawKey(rawKey) {
  if (!rawKey) return '';
  const clean = String(rawKey).toLowerCase().trim().replace(/[:_=\-\/\(\)]+/g, ' ').replace(/\s+/g, ' ');
  return CANONICAL_ALIASES[clean] || rawKey;
}

export function normalizeExtractedDict(extractedDict) {
  if (!extractedDict || typeof extractedDict !== 'object') return {};
  const normalized = {};
  Object.entries(extractedDict).forEach(([rawK, val]) => {
    if (val !== null && val !== undefined && val !== '') {
      const canonicalKey = normalizeRawKey(rawK);
      let numVal = val;
      if (typeof val === 'object' && val.raw_value !== undefined) {
        numVal = val.raw_value;
      }
      if (typeof numVal === 'string' && numVal.trim() !== 'Male' && numVal.trim() !== 'Female' && !isNaN(parseFloat(numVal))) {
        numVal = parseFloat(numVal);
      }
      normalized[canonicalKey] = numVal;
    }
  });
  return normalized;
}

/**
 * Computes 9 ecological and functional gut indices from 40 species taxa.
 * Robustly renormalizes any raw taxa sum to a standard 100% simplex.
 */
export function computeGutDerivedIndices(taxaDict = {}) {
  const taxaVals = GUT_V4_TAXA_40.map(t => {
    const raw = taxaDict[t];
    const val = parseFloat(raw);
    return isNaN(val) ? 0.0 : val;
  });

  const rawSum = taxaVals.reduce((acc, v) => acc + v, 0.0);
  let pFrac = taxaVals.map(() => 0.0);
  let taxaPct = taxaVals.map(() => 0.0);

  if (rawSum > 0) {
    pFrac = taxaVals.map(v => v / rawSum);
    taxaPct = taxaVals.map(v => (v / rawSum) * 100.0);
  }

  const pNoZero = pFrac.map(v => (v > 0 ? v : 1.0));
  const shannon = -pFrac.reduce((acc, v, i) => acc + v * Math.log(pNoZero[i]), 0.0);
  const simpson = 1.0 - pFrac.reduce((acc, v) => acc + v * v, 0.0);
  const richness = taxaVals.filter(v => v > 0).length;
  const pielou = shannon / Math.log(Math.max(richness, 2));

  const getMean = (indices) => {
    const vals = indices.map(idx => taxaPct[idx]);
    return vals.reduce((a, b) => a + b, 0) / Math.max(vals.length, 1);
  };

  const scfaIdx = getMean([1, 2, 3, 4, 10, 17, 18, 20, 22, 23, 31, 34]);
  const butyrateIdx = getMean([1, 2, 17, 20, 22, 23, 34]);
  const barrierIdx = getMean([0, 1, 3, 4, 29]);
  const inflIdx = getMean([11, 14, 15, 16, 21, 28, 37, 38]);

  const firmicutesIdx = [1, 2, 10, 11, 12, 13, 17, 20, 21, 22, 23, 25, 26, 27, 29, 31, 32, 34, 35, 36];
  const bacteroidetesIdx = [5, 6, 7, 8, 9, 18, 19, 24, 33];
  const firmicutes = firmicutesIdx.reduce((acc, idx) => acc + taxaPct[idx], 0.0);
  const bacteroidetes = bacteroidetesIdx.reduce((acc, idx) => acc + taxaPct[idx], 0.0);
  const logFB = Math.log((firmicutes + 0.01) / (bacteroidetes + 0.01));

  return {
    Shannon_Diversity: Number(shannon.toFixed(4)),
    Simpson_Diversity: Number(simpson.toFixed(4)),
    Observed_Richness: richness,
    Pielou_Evenness: Number(pielou.toFixed(4)),
    SCFA_Producer_Index: Number(scfaIdx.toFixed(4)),
    Butyrate_Producer_Index: Number(butyrateIdx.toFixed(4)),
    Barrier_Associated_Index: Number(barrierIdx.toFixed(4)),
    Inflammation_Associated_Index: Number(inflIdx.toFixed(4)),
    Log_Firmicutes_Bacteroidetes_Ratio: Number(logFB.toFixed(4))
  };
}

export const CLIENT_PHYSIOLOGICAL_BOUNDS = {
  Age: { min: 18, max: 100, unit: 'years' },
  Height: { min: 120, max: 230, unit: 'cm' },
  Weight: { min: 30, max: 250, unit: 'kg' },
  BMI: { min: 12, max: 65, unit: 'kg/m²' },
  Waist_Circumference: { min: 50, max: 180, unit: 'cm' },
  Systolic_BP: { min: 70, max: 240, unit: 'mmHg' },
  Diastolic_BP: { min: 40, max: 140, unit: 'mmHg' },
  Fasting_Blood_Glucose: { min: 50, max: 400, unit: 'mg/dL' },
  HbA1c: { min: 3.5, max: 16.0, unit: '%' },
  Triglycerides: { min: 20, max: 1000, unit: 'mg/dL' },
  HDL: { min: 10, max: 120, unit: 'mg/dL' },
  LDL: { min: 20, max: 400, unit: 'mg/dL' },
  ALT: { min: 2, max: 500, unit: 'U/L' },
  AST: { min: 2, max: 500, unit: 'U/L' },
  Family_History_Diabetes: { min: 0, max: 1, unit: 'binary' },
  Family_History_Hypertension: { min: 0, max: 1, unit: 'binary' },
  Family_History_CVD: { min: 0, max: 1, unit: 'binary' },

  Average_Daily_Steps: { min: 500, max: 40000, unit: 'steps' },
  Active_Minutes: { min: 0, max: 360, unit: 'mins' },
  Sedentary_Time_Minutes: { min: 60, max: 1200, unit: 'mins' },
  Resting_Heart_Rate: { min: 35, max: 140, unit: 'bpm' },
  Heart_Rate_Variability_RMSSD: { min: 5, max: 250, unit: 'ms' },
  Sleep_Duration_Hours: { min: 2, max: 16, unit: 'hrs' },
  Sleep_Efficiency_Score: { min: 30, max: 100, unit: '%' },
  Autonomic_Stress_Score: { min: 0, max: 100, unit: 'score' },
  Activity_Energy_Expenditure: { min: 100, max: 5000, unit: 'kcal' },
  Exercise_Frequency_Days: { min: 0, max: 7, unit: 'days/wk' },
  CGM_Average_Glucose: { min: 50, max: 400, unit: 'mg/dL' },
  CGM_Glucose_CV: { min: 2, max: 80, unit: '%' },
  CGM_Time_In_Range: { min: 0, max: 100, unit: '%' },
  CGM_Time_Above_Range: { min: 0, max: 100, unit: '%' },
  CGM_Time_Below_Range: { min: 0, max: 100, unit: '%' }
};

export function validateClientField(fieldName, value) {
  if (value === '' || value === null || value === undefined) return '';
  const bounds = CLIENT_PHYSIOLOGICAL_BOUNDS[fieldName];
  if (!bounds) return '';
  const num = parseFloat(value);
  if (isNaN(num)) return `Must be a valid number`;
  if (num < bounds.min || num > bounds.max) {
    return `Must be [${bounds.min} - ${bounds.max}]`;
  }
  return '';
}

