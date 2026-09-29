/**
 * clinicalRanges.js — Centralized Clinical, Wearable, & Gut Reference Ranges Classifier.
 * Standard Medical Guidelines:
 * - ADA (American Diabetes Association) for HbA1c & Fasting Glucose
 * - ACC/AHA (American College of Cardiology / AHA) for Blood Pressure
 * - WHO / CDC for BMI
 * - NCEP ATP III for Triglycerides & Lipids
 * - ACG (American College of Gastroenterology) for ALT / AST
 */

export const CLINICAL_STATUS_TYPES = {
  NORMAL: { key: 'NORMAL', label: 'Normal', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', badgeClass: 'badge-emerald' },
  AT_RISK: { key: 'AT RISK', label: 'At Risk', color: '#fbbf24', bg: 'rgba(245, 158, 11, 0.15)', badgeClass: 'badge-amber' },
  OVERWEIGHT: { key: 'OVERWEIGHT', label: 'Overweight', color: '#fbbf24', bg: 'rgba(245, 158, 11, 0.15)', badgeClass: 'badge-amber' },
  ELEVATED: { key: 'ELEVATED', label: 'Elevated', color: '#f87171', bg: 'rgba(239, 68, 68, 0.15)', badgeClass: 'badge-rose' },
  OBESITY: { key: 'OBESITY', label: 'Obesity', color: '#f87171', bg: 'rgba(239, 68, 68, 0.15)', badgeClass: 'badge-rose' },
  LOW: { key: 'LOW', label: 'Low', color: '#60a5fa', bg: 'rgba(59, 130, 246, 0.15)', badgeClass: 'badge-cyan' },
  NOT_PROVIDED: { key: 'NOT_PROVIDED', label: 'Not Provided', color: 'var(--text-dim)', bg: 'rgba(148, 163, 184, 0.12)', badgeClass: 'badge-outline' }
};

export const CLINICAL_REFERENCE_RANGES = {
  HbA1c: {
    friendlyName: 'HbA1c',
    unit: '%',
    refRange: '< 5.7%',
    classify: (val) => {
      const num = parseFloat(val);
      if (isNaN(num)) return CLINICAL_STATUS_TYPES.NOT_PROVIDED;
      if (num >= 6.5) return { ...CLINICAL_STATUS_TYPES.ELEVATED, label: 'Elevated' };
      if (num >= 5.7) return CLINICAL_STATUS_TYPES.AT_RISK;
      return CLINICAL_STATUS_TYPES.NORMAL;
    }
  },
  Fasting_Blood_Glucose: {
    friendlyName: 'Fasting Blood Glucose',
    unit: 'mg/dL',
    refRange: '70–99 mg/dL',
    classify: (val) => {
      const num = parseFloat(val);
      if (isNaN(num)) return CLINICAL_STATUS_TYPES.NOT_PROVIDED;
      if (num < 70) return CLINICAL_STATUS_TYPES.LOW;
      if (num >= 126) return CLINICAL_STATUS_TYPES.ELEVATED;
      if (num >= 100) return CLINICAL_STATUS_TYPES.AT_RISK;
      return CLINICAL_STATUS_TYPES.NORMAL;
    }
  },
  Blood_Pressure: {
    friendlyName: 'Blood Pressure',
    unit: 'mmHg',
    refRange: '< 120/80 mmHg',
    classify: (sbp, dbp) => {
      const sys = parseFloat(sbp);
      const dia = parseFloat(dbp);
      if (isNaN(sys) && isNaN(dia)) return CLINICAL_STATUS_TYPES.NOT_PROVIDED;
      if ((!isNaN(sys) && sys >= 120) || (!isNaN(dia) && dia >= 80)) {
        return CLINICAL_STATUS_TYPES.ELEVATED;
      }
      return CLINICAL_STATUS_TYPES.NORMAL;
    }
  },
  Systolic_BP: {
    friendlyName: 'Systolic Blood Pressure',
    unit: 'mmHg',
    refRange: '< 120 mmHg',
    classify: (val) => {
      const num = parseFloat(val);
      if (isNaN(num)) return CLINICAL_STATUS_TYPES.NOT_PROVIDED;
      if (num >= 120) return CLINICAL_STATUS_TYPES.ELEVATED;
      return CLINICAL_STATUS_TYPES.NORMAL;
    }
  },
  Diastolic_BP: {
    friendlyName: 'Diastolic Blood Pressure',
    unit: 'mmHg',
    refRange: '< 80 mmHg',
    classify: (val) => {
      const num = parseFloat(val);
      if (isNaN(num)) return CLINICAL_STATUS_TYPES.NOT_PROVIDED;
      if (num >= 80) return CLINICAL_STATUS_TYPES.ELEVATED;
      return CLINICAL_STATUS_TYPES.NORMAL;
    }
  },
  BMI: {
    friendlyName: 'BMI (Body Mass Index)',
    unit: 'kg/m²',
    refRange: '18.5–24.9 kg/m²',
    classify: (val) => {
      const num = parseFloat(val);
      if (isNaN(num)) return CLINICAL_STATUS_TYPES.NOT_PROVIDED;
      if (num < 18.5) return CLINICAL_STATUS_TYPES.LOW;
      if (num >= 30.0) return CLINICAL_STATUS_TYPES.OBESITY;
      if (num >= 25.0) return CLINICAL_STATUS_TYPES.OVERWEIGHT;
      return CLINICAL_STATUS_TYPES.NORMAL;
    }
  },
  Triglycerides: {
    friendlyName: 'Triglycerides',
    unit: 'mg/dL',
    refRange: '< 150 mg/dL',
    classify: (val) => {
      const num = parseFloat(val);
      if (isNaN(num)) return CLINICAL_STATUS_TYPES.NOT_PROVIDED;
      if (num >= 150) return CLINICAL_STATUS_TYPES.ELEVATED;
      return CLINICAL_STATUS_TYPES.NORMAL;
    }
  },
  ALT: {
    friendlyName: 'ALT (Liver Enzyme)',
    unit: 'U/L',
    refRange: '7–56 U/L',
    classify: (val) => {
      const num = parseFloat(val);
      if (isNaN(num)) return CLINICAL_STATUS_TYPES.NOT_PROVIDED;
      if (num < 7) return CLINICAL_STATUS_TYPES.LOW;
      if (num > 56) return CLINICAL_STATUS_TYPES.ELEVATED;
      return CLINICAL_STATUS_TYPES.NORMAL;
    }
  },
  AST: {
    friendlyName: 'AST (Liver Enzyme)',
    unit: 'U/L',
    refRange: '10–40 U/L',
    classify: (val) => {
      const num = parseFloat(val);
      if (isNaN(num)) return CLINICAL_STATUS_TYPES.NOT_PROVIDED;
      if (num < 10) return CLINICAL_STATUS_TYPES.LOW;
      if (num > 40) return CLINICAL_STATUS_TYPES.ELEVATED;
      return CLINICAL_STATUS_TYPES.NORMAL;
    }
  },
  HDL: {
    friendlyName: 'HDL (Good Cholesterol)',
    unit: 'mg/dL',
    refRange: '≥ 40 mg/dL',
    classify: (val) => {
      const num = parseFloat(val);
      if (isNaN(num)) return CLINICAL_STATUS_TYPES.NOT_PROVIDED;
      if (num < 40) return CLINICAL_STATUS_TYPES.LOW;
      return CLINICAL_STATUS_TYPES.NORMAL;
    }
  },
  LDL: {
    friendlyName: 'LDL (Cholesterol)',
    unit: 'mg/dL',
    refRange: '< 100 mg/dL',
    classify: (val) => {
      const num = parseFloat(val);
      if (isNaN(num)) return CLINICAL_STATUS_TYPES.NOT_PROVIDED;
      if (num >= 130) return CLINICAL_STATUS_TYPES.ELEVATED;
      if (num >= 100) return { ...CLINICAL_STATUS_TYPES.AT_RISK, key: 'BORDERLINE', label: 'Borderline High' };
      return CLINICAL_STATUS_TYPES.NORMAL;
    }
  },
  Waist_Circumference: {
    friendlyName: 'Waist Circumference',
    unit: 'cm',
    refRange: '< 88–102 cm',
    classify: (val) => {
      const num = parseFloat(val);
      if (isNaN(num)) return CLINICAL_STATUS_TYPES.NOT_PROVIDED;
      if (num >= 88) return CLINICAL_STATUS_TYPES.ELEVATED;
      return CLINICAL_STATUS_TYPES.NORMAL;
    }
  },
  Age: {
    friendlyName: 'Age',
    unit: 'years',
    refRange: 'Standard',
    classify: (val) => CLINICAL_STATUS_TYPES.NORMAL
  },
  Height: {
    friendlyName: 'Height',
    unit: 'cm',
    refRange: 'Standard',
    classify: (val) => CLINICAL_STATUS_TYPES.NORMAL
  },
  Weight: {
    friendlyName: 'Weight',
    unit: 'kg',
    refRange: 'Standard',
    classify: (val) => CLINICAL_STATUS_TYPES.NORMAL
  }
};

/**
 * Classify a clinical biomarker value.
 */
export function classifyBiomarker(biomarkerKey, val, secondaryVal = null) {
  if (val === null || val === undefined || val === '' || val === 'N/A') {
    return {
      ...CLINICAL_STATUS_TYPES.NOT_PROVIDED,
      status: 'NOT_PROVIDED',
      refRange: (CLINICAL_REFERENCE_RANGES[biomarkerKey] || {}).refRange || 'Standard range',
      friendlyName: (CLINICAL_REFERENCE_RANGES[biomarkerKey] || {}).friendlyName || biomarkerKey?.replace(/_/g, ' ') || 'Measurement',
      unit: (CLINICAL_REFERENCE_RANGES[biomarkerKey] || {}).unit || ''
    };
  }

  const meta = CLINICAL_REFERENCE_RANGES[biomarkerKey];
  if (!meta) {
    const num = parseFloat(val);
    if (isNaN(num)) return { ...CLINICAL_STATUS_TYPES.NOT_PROVIDED, refRange: 'Standard range', friendlyName: biomarkerKey, unit: '' };
    return { ...CLINICAL_STATUS_TYPES.NORMAL, refRange: 'Standard range', friendlyName: biomarkerKey, unit: '' };
  }

  const result = secondaryVal !== null ? meta.classify(val, secondaryVal) : meta.classify(val);
  return {
    ...result,
    status: result.key,
    refRange: meta.refRange,
    friendlyName: meta.friendlyName,
    unit: meta.unit
  };
}

export const WEARABLE_REFERENCE_RANGES = {
  Average_Daily_Steps: { friendlyName: 'Average Daily Steps', unit: 'steps/day', refRange: '≥ 8,000 steps/day', classify: (v) => v < 5000 ? { key: 'BELOW_TARGET', label: 'Below Target', color: '#fbbf24', bg: 'rgba(245, 158, 11, 0.15)' } : { key: 'NORMAL', label: 'Target Met', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' } },
  Active_Minutes: { friendlyName: 'Active Minutes', unit: 'mins/day', refRange: '≥ 30 mins/day', classify: (v) => v < 30 ? { key: 'BELOW_TARGET', label: 'Below Target', color: '#fbbf24', bg: 'rgba(245, 158, 11, 0.15)' } : { key: 'NORMAL', label: 'Target Met', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' } },
  Sedentary_Time_Minutes: { friendlyName: 'Sedentary Time', unit: 'mins/day', refRange: '< 480 mins/day', classify: (v) => v > 600 ? { key: 'ELEVATED', label: 'Elevated Sedentary', color: '#f87171', bg: 'rgba(239, 68, 68, 0.15)' } : { key: 'NORMAL', label: 'Normal', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' } },
  Resting_Heart_Rate: { friendlyName: 'Resting Heart Rate', unit: 'bpm', refRange: '60–100 bpm', classify: (v) => (v < 60 || v > 100) ? { key: 'ELEVATED', label: 'Outside Target', color: '#fbbf24', bg: 'rgba(245, 158, 11, 0.15)' } : { key: 'NORMAL', label: 'Normal', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' } },
  Heart_Rate_Variability_RMSSD: { friendlyName: 'Heart Rate Variability (HRV)', unit: 'ms', refRange: '≥ 25 ms', classify: (v) => v < 25 ? { key: 'BELOW_TARGET', label: 'Low HRV', color: '#fbbf24', bg: 'rgba(245, 158, 11, 0.15)' } : { key: 'NORMAL', label: 'Optimal', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' } },
  Sleep_Duration: { friendlyName: 'Sleep Duration', unit: 'hours', refRange: '7.0–9.0 hours', classify: (v) => (v < 6.0 || v > 9.5) ? { key: 'BELOW_TARGET', label: 'Outside Target', color: '#fbbf24', bg: 'rgba(245, 158, 11, 0.15)' } : { key: 'NORMAL', label: 'Optimal', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' } },
  Sleep_Efficiency_Score: { friendlyName: 'Sleep Efficiency', unit: '%', refRange: '≥ 80%', classify: (v) => v < 80 ? { key: 'BELOW_TARGET', label: 'Low Efficiency', color: '#fbbf24', bg: 'rgba(245, 158, 11, 0.15)' } : { key: 'NORMAL', label: 'Optimal', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' } },
  Autonomic_Stress_Score: { friendlyName: 'Autonomic Stress Score', unit: '/100', refRange: '< 50 / 100', classify: (v) => v >= 50 ? { key: 'ELEVATED', label: 'High Stress', color: '#f87171', bg: 'rgba(239, 68, 68, 0.15)' } : { key: 'NORMAL', label: 'Low/Moderate', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' } },
  Calories_Burned: { friendlyName: 'Calories Burned', unit: 'kcal/day', refRange: 'Standard target', classify: (v) => ({ key: 'NORMAL', label: 'Recorded', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' }) },
  Exercise_Frequency_Days: { friendlyName: 'Exercise Frequency', unit: 'days/week', refRange: '≥ 3 days/week', classify: (v) => v < 3 ? { key: 'BELOW_TARGET', label: 'Below Target', color: '#fbbf24', bg: 'rgba(245, 158, 11, 0.15)' } : { key: 'NORMAL', label: 'Target Met', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' } },
  Average_Glucose: { friendlyName: 'CGM Average Glucose', unit: 'mg/dL', refRange: '70–99 mg/dL', classify: (v) => v >= 126 ? { key: 'ELEVATED', label: 'Elevated', color: '#f87171', bg: 'rgba(239, 68, 68, 0.15)' } : (v >= 100 ? { key: 'PREDIABETES', label: 'Prediabetes', color: '#fbbf24', bg: 'rgba(245, 158, 11, 0.15)' } : { key: 'NORMAL', label: 'Normal', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' }) },
  Glucose_Variability: { friendlyName: 'CGM Glucose Variability', unit: '%', refRange: '< 36%', classify: (v) => v > 36 ? { key: 'ELEVATED', label: 'High Variability', color: '#f87171', bg: 'rgba(239, 68, 68, 0.15)' } : { key: 'NORMAL', label: 'Target Met', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' } },
  Time_In_Range: { friendlyName: 'CGM Time in Range (TIR)', unit: '%', refRange: '≥ 70%', classify: (v) => v < 70 ? { key: 'BELOW_TARGET', label: 'Below Target', color: '#fbbf24', bg: 'rgba(245, 158, 11, 0.15)' } : { key: 'NORMAL', label: 'Target Met', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' } }
};

/**
 * Classify a wearable metric value.
 */
export function classifyWearable(wearableKey, val) {
  if (val === null || val === undefined || val === '' || val === 'N/A') {
    return {
      ...CLINICAL_STATUS_TYPES.NOT_PROVIDED,
      status: 'NOT_PROVIDED',
      refRange: (WEARABLE_REFERENCE_RANGES[wearableKey] || {}).refRange || 'Standard target',
      friendlyName: (WEARABLE_REFERENCE_RANGES[wearableKey] || {}).friendlyName || wearableKey?.replace(/_/g, ' ') || 'Metric',
      unit: (WEARABLE_REFERENCE_RANGES[wearableKey] || {}).unit || ''
    };
  }

  const num = parseFloat(val);
  if (isNaN(num)) {
    return {
      ...CLINICAL_STATUS_TYPES.NOT_PROVIDED,
      status: 'NOT_PROVIDED',
      refRange: (WEARABLE_REFERENCE_RANGES[wearableKey] || {}).refRange || 'Standard target',
      friendlyName: (WEARABLE_REFERENCE_RANGES[wearableKey] || {}).friendlyName || wearableKey?.replace(/_/g, ' '),
      unit: (WEARABLE_REFERENCE_RANGES[wearableKey] || {}).unit || ''
    };
  }

  const meta = WEARABLE_REFERENCE_RANGES[wearableKey];
  if (!meta) {
    return { ...CLINICAL_STATUS_TYPES.NORMAL, refRange: 'Standard target', friendlyName: wearableKey, unit: '' };
  }

  const res = meta.classify(num);
  return {
    ...res,
    status: res.key,
    refRange: meta.refRange,
    friendlyName: meta.friendlyName,
    unit: meta.unit
  };
}

export const GUT_REFERENCE_RANGES = {
  Shannon_Diversity_Index: { friendlyName: 'Shannon Diversity Index', unit: '', refRange: '≥ 3.0', classify: (v) => v < 2.5 ? { key: 'ELEVATED', label: 'Low Diversity', color: '#f87171', bg: 'rgba(239, 68, 68, 0.15)' } : (v < 3.0 ? { key: 'PREDIABETES', label: 'Moderate Diversity', color: '#fbbf24', bg: 'rgba(245, 158, 11, 0.15)' } : { key: 'NORMAL', label: 'High Diversity', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' }) },
  Akkermansia: { friendlyName: 'Akkermansia muciniphila', unit: '%', refRange: '≥ 1.0%', classify: (v) => v < 1.0 ? { key: 'PREDIABETES', label: 'Reduced', color: '#fbbf24', bg: 'rgba(245, 158, 11, 0.15)' } : { key: 'NORMAL', label: 'Optimal', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' } },
  Faecalibacterium: { friendlyName: 'Faecalibacterium prausnitzii', unit: '%', refRange: '≥ 5.0%', classify: (v) => v < 5.0 ? { key: 'PREDIABETES', label: 'Reduced', color: '#fbbf24', bg: 'rgba(245, 158, 11, 0.15)' } : { key: 'NORMAL', label: 'Optimal', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' } },
  Bifidobacterium: { friendlyName: 'Bifidobacterium spp.', unit: '%', refRange: '≥ 2.0%', classify: (v) => v < 2.0 ? { key: 'PREDIABETES', label: 'Reduced', color: '#fbbf24', bg: 'rgba(245, 158, 11, 0.15)' } : { key: 'NORMAL', label: 'Optimal', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' } },
  Roseburia: { friendlyName: 'Roseburia spp.', unit: '%', refRange: '≥ 2.0%', classify: (v) => v < 2.0 ? { key: 'PREDIABETES', label: 'Reduced', color: '#fbbf24', bg: 'rgba(245, 158, 11, 0.15)' } : { key: 'NORMAL', label: 'Optimal', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' } },
  Proteobacteria: { friendlyName: 'Proteobacteria (Phylum)', unit: '%', refRange: '≤ 10.0%', classify: (v) => v > 10.0 ? { key: 'ELEVATED', label: 'Dysbiosis Flag', color: '#f87171', bg: 'rgba(239, 68, 68, 0.15)' } : { key: 'NORMAL', label: 'Optimal', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' } }
};

/**
 * Classify a gut microbiome taxa or metric value.
 */
export function classifyGut(gutKey, val) {
  if (val === null || val === undefined || val === '' || val === 'N/A') {
    return {
      ...CLINICAL_STATUS_TYPES.NOT_PROVIDED,
      status: 'NOT_PROVIDED',
      refRange: (GUT_REFERENCE_RANGES[gutKey] || {}).refRange || '0.1–15.0%',
      friendlyName: (GUT_REFERENCE_RANGES[gutKey] || {}).friendlyName || gutKey?.replace(/_/g, ' ') || 'Taxon',
      unit: (GUT_REFERENCE_RANGES[gutKey] || {}).unit || '%'
    };
  }

  const num = parseFloat(val);
  if (isNaN(num)) {
    return {
      ...CLINICAL_STATUS_TYPES.NOT_PROVIDED,
      status: 'NOT_PROVIDED',
      refRange: (GUT_REFERENCE_RANGES[gutKey] || {}).refRange || '0.1–15.0%',
      friendlyName: (GUT_REFERENCE_RANGES[gutKey] || {}).friendlyName || gutKey?.replace(/_/g, ' '),
      unit: (GUT_REFERENCE_RANGES[gutKey] || {}).unit || '%'
    };
  }

  const meta = GUT_REFERENCE_RANGES[gutKey];
  if (!meta) {
    const isHigh = num > 15.0;
    return {
      key: isHigh ? 'PREDIABETES' : 'NORMAL',
      status: isHigh ? 'PREDIABETES' : 'NORMAL',
      label: isHigh ? 'Elevated Abundance' : 'Normal',
      color: isHigh ? '#fbbf24' : '#10b981',
      bg: isHigh ? 'rgba(245, 158, 11, 0.15)' : 'rgba(16, 185, 129, 0.15)',
      refRange: '0.1–15.0%',
      friendlyName: gutKey.replace(/_/g, ' '),
      unit: '%'
    };
  }

  const res = meta.classify(num);
  return {
    ...res,
    status: res.key,
    refRange: meta.refRange,
    friendlyName: meta.friendlyName,
    unit: meta.unit
  };
}
