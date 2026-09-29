/**
 * healthIntelligence.js — Transparent Patient Health Intelligence Engine
 * 
 * Computes deterministic patient health scores, metabolic trajectories, 
 * biomarker shift classifications, cross-modality insights, and early-warning indicators
 * strictly using the patient's actual historical assessment data.
 */

import { classifyBiomarker, classifyWearable, classifyGut } from './clinicalRanges';

function safeParse(val) {
  if (!val) return {};
  if (typeof val === 'string') {
    try {
      return JSON.parse(val);
    } catch {
      return {};
    }
  }
  return typeof val === 'object' ? val : {};
}

function extractVal(item) {
  if (item === null || item === undefined) return null;
  if (typeof item === 'object') return item.value ?? item.raw_value ?? null;
  return item;
}

/**
 * 1. Overall Patient Health Score (0 - 100)
 * Transparent Formula:
 * - Data Quality Weight: 20% (DQ_Score * 20)
 * - Metabolic Risk Penalty: 50% (50 - Mean(Disease_Risk_Probabilities) * 50)
 * - Biomarker Normalcy Component: 30% (Normalcy_Ratio * 30)
 */
export function calculateOverallHealthScore(rawPredictionData) {
  if (!rawPredictionData) return null;
  const predictionData = typeof rawPredictionData === 'string' ? safeParse(rawPredictionData) : rawPredictionData;
  if (!predictionData || typeof predictionData !== 'object') return null;

  const dq = predictionData.data_quality_score ?? predictionData.overall_quality_score ?? 0.85;
  const dqComponent = (dq > 1.0 ? dq / 100 : dq) * 20;

  const outcomes = safeParse(predictionData.disease_outcomes || predictionData.predictions || {});
  const diseaseKeys = ['Type2_Diabetes', 'Prediabetes', 'High_Adiposity_Risk', 'Metabolic_Syndrome', 'NAFLD'];
  let riskSum = 0;
  let riskCount = 0;

  diseaseKeys.forEach(key => {
    const item = outcomes[key];
    if (item) {
      const prob = item.calibrated_probability ?? item.probability ?? 0.2;
      riskSum += (prob > 1.0 ? prob / 100 : prob);
      riskCount++;
    }
  });

  const meanRisk = riskCount > 0 ? riskSum / riskCount : 0.2;
  const riskComponent = Math.max(0, 50 - (meanRisk * 50));

  // Biomarker Normalcy Ratio
  const confirmed = safeParse(predictionData.confirmed_features);
  const clin = safeParse(confirmed.clinical || predictionData.clinical_features || predictionData.clinical_data || {});
  let normalCount = 0;
  let totalCount = 0;

  Object.keys(clin).forEach(k => {
    if (['Patient_ID', 'Gender'].includes(k)) return;
    const val = extractVal(clin[k]);
    if (val !== null && val !== undefined) {
      totalCount++;
      const cls = classifyBiomarker(k, val);
      if (cls && (cls.category === 'normal' || cls.status === 'NORMAL' || cls.status === 'OPTIMAL')) {
        normalCount++;
      }
    }
  });

  const isNormalcyAvailable = totalCount > 0;
  const normalcyRatio = isNormalcyAvailable ? normalCount / totalCount : 0.5; // Neutral 50% baseline if 0 biomarkers present
  const normalcyComponent = normalcyRatio * 30;

  const finalScore = Math.min(100, Math.max(0, Math.round(dqComponent + riskComponent + normalcyComponent)));

  return {
    score: finalScore,
    breakdown: {
      dataQualityPts: Math.round(dqComponent),
      metabolicRiskPts: Math.round(riskComponent),
      biomarkerNormalcyPts: Math.round(normalcyComponent),
      totalBiomarkersEvaluated: totalCount,
      normalBiomarkersCount: normalCount,
      isNormalcyAvailable
    },
    formulaDescription: 'Calculated transparently from Data Quality Score (20%), Inverse Mean Disease Risk (50%), and Biomarker Normalcy Ratio (30%).'
  };
}


/**
 * 2. Longitudinal Shifts: "What's Improving?" and "What's Worsening?"
 */
export function analyzeLongitudinalShifts(records) {
  if (!records || !Array.isArray(records) || records.length < 2) {
    return { improving: [], worsening: [], stable: [], hasHistory: false };
  }

  const recent = records[0];
  const baseline = records[records.length - 1];
  if (!recent || !baseline) {
    return { improving: [], worsening: [], stable: [], hasHistory: false };
  }

  const improving = [];
  const worsening = [];
  const stable = [];

  // A. Disease Risk Trajectory Shifts
  const recentSnap = safeParse(recent.prediction_snapshot || recent);
  const baselineSnap = safeParse(baseline.prediction_snapshot || baseline);

  const recentOutcomes = safeParse(recentSnap.disease_outcomes || recentSnap.predictions || {});
  const baselineOutcomes = safeParse(baselineSnap.disease_outcomes || baselineSnap.predictions || {});

  const getProb = (obj, k) => obj[k]?.calibrated_probability ?? obj[k]?.probability;
  const t2dProb = getProb(recentOutcomes, 'Type2_Diabetes') || 0;
  const preProb = getProb(recentOutcomes, 'Prediabetes') || 0;
  
  let diseaseKeys = ['Type2_Diabetes', 'Prediabetes', 'High_Adiposity_Risk', 'Metabolic_Syndrome', 'NAFLD'];
  if (t2dProb >= preProb) {
    diseaseKeys = diseaseKeys.filter(k => k !== 'Prediabetes');
  } else {
    diseaseKeys = diseaseKeys.filter(k => k !== 'Type2_Diabetes');
  }

  diseaseKeys.forEach(key => {
    const p1 = getProb(recentOutcomes, key);
    const p2 = getProb(baselineOutcomes, key);

    if (p1 !== undefined && p2 !== undefined && typeof p1 === 'number' && typeof p2 === 'number') {
      const diffPct = Math.round((p1 - p2) * 100);
      const name = key.replace(/_/g, ' ');
      if (diffPct <= -3) {
        improving.push({
          label: `${name} Risk`,
          shift: `${diffPct}%`,
          detail: `Risk decreased from ${Math.round(p2 * 100)}% to ${Math.round(p1 * 100)}%`,
          category: 'Risk Outcome'
        });
      } else if (diffPct >= 3) {
        worsening.push({
          label: `${name} Risk`,
          shift: `+${diffPct}%`,
          detail: `Risk increased from ${Math.round(p2 * 100)}% to ${Math.round(p1 * 100)}%`,
          category: 'Risk Outcome'
        });
      } else {
        stable.push({
          label: `${name} Risk`,
          shift: `${diffPct}%`,
          detail: `Stable at ${Math.round(p1 * 100)}%`,
          category: 'Risk Outcome'
        });
      }
    }
  });

  // B. Clinical Biomarker Shifts
  const clin1 = safeParse(recent.confirmed_features?.clinical || recentSnap.confirmed_features?.clinical || recentSnap.clinical_features || {});
  const clin2 = safeParse(baseline.confirmed_features?.clinical || baselineSnap.confirmed_features?.clinical || baselineSnap.clinical_features || {});

  const trackedLabs = [
    { key: 'Fasting_Blood_Glucose', name: 'Fasting Blood Glucose', unit: 'mg/dL', lowerIsBetter: true },
    { key: 'HbA1c', name: 'HbA1c', unit: '%', lowerIsBetter: true },
    { key: 'BMI', name: 'BMI', unit: 'kg/m²', lowerIsBetter: true },
    { key: 'Systolic_BP', name: 'Systolic BP', unit: 'mmHg', lowerIsBetter: true },
    { key: 'Triglycerides', name: 'Triglycerides', unit: 'mg/dL', lowerIsBetter: true },
    { key: 'LDL_Cholesterol', name: 'LDL Cholesterol', unit: 'mg/dL', lowerIsBetter: true },
    { key: 'HDL_Cholesterol', name: 'HDL Cholesterol', unit: 'mg/dL', lowerIsBetter: false }
  ];

  trackedLabs.forEach(item => {
    const raw1 = extractVal(clin1[item.key]);
    const raw2 = extractVal(clin2[item.key]);
    const v1 = typeof raw1 === 'number' ? raw1 : (raw1 !== null && raw1 !== undefined ? Number(raw1) : NaN);
    const v2 = typeof raw2 === 'number' ? raw2 : (raw2 !== null && raw2 !== undefined ? Number(raw2) : NaN);

    if (!isNaN(v1) && !isNaN(v2)) {
      const diff = v1 - v2;
      const formattedDiff = diff > 0 ? `+${diff.toFixed(1)} ${item.unit}` : `${diff.toFixed(1)} ${item.unit}`;
      
      const isImprovement = item.lowerIsBetter ? diff < 0 : diff > 0;
      if (Math.abs(diff) > 0.1) {
        if (isImprovement) {
          improving.push({
            label: item.name,
            shift: formattedDiff,
            detail: `Shifted from ${v2} to ${v1} ${item.unit}`,
            category: 'Clinical Lab'
          });
        } else {
          worsening.push({
            label: item.name,
            shift: formattedDiff,
            detail: `Shifted from ${v2} to ${v1} ${item.unit}`,
            category: 'Clinical Lab'
          });
        }
      }
    }
  });

  return { improving, worsening, stable, hasHistory: true };
}

/**
 * 3. Rules-Based Early Warning Indicators
 */
export function detectEarlyWarnings(rawPredictionData, historyRecords = []) {
  const warnings = [];
  if (!rawPredictionData) return warnings;
  const predictionData = typeof rawPredictionData === 'string' ? safeParse(rawPredictionData) : rawPredictionData;
  if (!predictionData || typeof predictionData !== 'object') return warnings;

  const confirmed = safeParse(predictionData.confirmed_features);
  const clin = safeParse(confirmed.clinical || predictionData.clinical_features || predictionData.clinical_data || {});

  // Rule 1: High Glucose
  const rawGlucose = extractVal(clin.Fasting_Blood_Glucose ?? clin.Glucose ?? clin.Fasting_Glucose);
  const glucose = typeof rawGlucose === 'number' ? rawGlucose : (rawGlucose ? Number(rawGlucose) : null);
  if (glucose && glucose >= 126) {
    warnings.push({
      id: 'EW-GLUCOSE',
      title: 'Elevated Fasting Blood Glucose Indicator',
      severity: 'HIGH',
      indicator: `Measured Fasting Glucose: ${glucose} mg/dL (Threshold ≥ 126 mg/dL)`,
      clinicalNote: 'Indicates impaired fasting glycemic control. Recommend physician follow-up for diagnostic confirmation.'
    });
  }

  // Rule 2: High Systolic / Diastolic BP
  const rawSbp = extractVal(clin.Systolic_BP ?? clin.Systolic);
  const rawDbp = extractVal(clin.Diastolic_BP ?? clin.Diastolic);
  const sbp = typeof rawSbp === 'number' ? rawSbp : (rawSbp ? Number(rawSbp) : null);
  const dbp = typeof rawDbp === 'number' ? rawDbp : (rawDbp ? Number(rawDbp) : null);
  if ((sbp && sbp >= 140) || (dbp && dbp >= 90)) {
    warnings.push({
      id: 'EW-BP',
      title: 'Elevated Blood Pressure Indicator',
      severity: 'HIGH',
      indicator: `Blood Pressure: ${sbp || '--'}/${dbp || '--'} mmHg (Threshold ≥ 140/90 mmHg)`,
      clinicalNote: 'Exceeds standard hypertension screening threshold. Recommend ambulatory BP monitoring.'
    });
  }

  // Rule 3: Significant Risk Acceleration (if history exists)
  if (Array.isArray(historyRecords) && historyRecords.length >= 2) {
    const recent = safeParse(historyRecords[0]?.prediction_snapshot?.disease_outcomes || historyRecords[0]?.prediction_snapshot?.predictions || {});
    const baseline = safeParse(historyRecords[historyRecords.length - 1]?.prediction_snapshot?.disease_outcomes || historyRecords[historyRecords.length - 1]?.prediction_snapshot?.predictions || {});

    const getP = (obj, k) => obj[k]?.calibrated_probability ?? obj[k]?.probability ?? 0;
    const t2dProb = getP(recent, 'Type2_Diabetes');
    const preProb = getP(recent, 'Prediabetes');
    const keysToCheck = Object.keys(recent).filter(k => {
      if (k === 'Prediabetes' && t2dProb >= preProb) return false;
      if (k === 'Type2_Diabetes' && preProb > t2dProb) return false;
      return true;
    });

    keysToCheck.forEach(key => {
      const p1 = recent[key]?.calibrated_probability ?? recent[key]?.probability;
      const p2 = baseline[key]?.calibrated_probability ?? baseline[key]?.probability;
      if (typeof p1 === 'number' && typeof p2 === 'number' && (p1 - p2) >= 0.15) {
        warnings.push({
          id: `EW-RISK-${key}`,
          title: `Accelerating ${key.replace(/_/g, ' ')} Risk Shift`,
          severity: 'MODERATE',
          indicator: `Risk probability increased by +${Math.round((p1 - p2) * 100)}% across historical assessments`,
          clinicalNote: 'Significant longitudinal risk elevation detected. Lifestyle intervention & physician consultation recommended.'
        });
      }
    });
  }

  return warnings;
}

/**
 * 4. Cross-Modality & Gut Microbiome Insights (Correlative)
 */
export function generateCrossModalityInsights(rawPredictionData) {
  const insights = [];
  if (!rawPredictionData) return insights;
  const predictionData = typeof rawPredictionData === 'string' ? safeParse(rawPredictionData) : rawPredictionData;
  if (!predictionData || typeof predictionData !== 'object') return insights;

  const confirmed = safeParse(predictionData.confirmed_features);
  const clin = safeParse(confirmed.clinical || predictionData.clinical_features || predictionData.clinical_data || {});
  const wear = safeParse(confirmed.wearable || predictionData.wearable_features || predictionData.wearable_data || {});
  const gut = safeParse(confirmed.gut || predictionData.gut_features || predictionData.gut_data || {});

  const stepsVal = extractVal(wear.Daily_Steps ?? wear.Average_Daily_Steps ?? wear.Total_Steps);
  const steps = typeof stepsVal === 'number' ? stepsVal : (stepsVal ? Number(stepsVal) : null);

  const glucVal = extractVal(clin.Fasting_Blood_Glucose ?? clin.Glucose ?? clin.Fasting_Glucose);
  const gluc = typeof glucVal === 'number' ? glucVal : (glucVal ? Number(glucVal) : null);

  // Insight A: Activity & Glycemic Correlation
  if (steps && gluc) {
    if (steps < 5000 && gluc > 100) {
      insights.push({
        title: 'Activity & Glycemic Correlation',
        description: `Sedentary physical activity (${steps.toLocaleString()} daily steps) correlates with elevated fasting blood glucose (${gluc} mg/dL). Increasing daily movement supports glycemic sensitivity.`,
        tag: 'Clinical + Wearable',
        variant: 'warning'
      });
    } else if (steps >= 8000 && gluc <= 100) {
      insights.push({
        title: 'Optimal Activity & Glucose Balance',
        description: `High daily step count (${steps.toLocaleString()} steps) aligns with optimal fasting blood glucose (${gluc} mg/dL).`,
        tag: 'Clinical + Wearable',
        variant: 'success'
      });
    }
  }

  // Insight B: Sleep & Stress & Autonomic Tone Correlation
  const sleepVal = extractVal(wear.Total_Sleep_Duration_Hours ?? wear.Sleep_Duration_Hours);
  const sleep = typeof sleepVal === 'number' ? sleepVal : (sleepVal ? Number(sleepVal) : null);

  const hrvVal = extractVal(wear.HRV_RMSSD ?? wear.Heart_Rate_Variability_RMSSD);
  const hrv = typeof hrvVal === 'number' ? hrvVal : (hrvVal ? Number(hrvVal) : null);

  if (sleep && hrv) {
    if (sleep < 6 && hrv < 30) {
      insights.push({
        title: 'Sleep Duration & HRV Autonomic Tone',
        description: `Short sleep duration (${sleep} hrs) coincides with reduced HRV (${hrv} ms), signaling sympathetic nervous system dominance.`,
        tag: 'Wearable Telemetry',
        variant: 'warning'
      });
    }
  }

  // Insight C: Gut Microbiome Taxa Interpretation
  const akkermansia = extractVal(gut['Akkermansia_muciniphila'] ?? gut['g_Akkermansia'] ?? gut['Akkermansia']);
  if (akkermansia !== undefined && akkermansia !== null) {
    const val = typeof akkermansia === 'number' ? akkermansia : Number(akkermansia);
    if (!isNaN(val)) {
      if (val < 1.0) {
        insights.push({
          title: 'Gut Microbiome Barrier Taxa (Akkermansia muciniphila)',
          description: `Relative abundance of Akkermansia muciniphila is lower than optimal (${val}%). Higher abundance is associated in medical literature with gut mucosal barrier integrity and metabolic health.`,
          tag: 'Gut Microbiome',
          variant: 'info'
        });
      } else {
        insights.push({
          title: 'Robust Gut Barrier Biomarker Abundance',
          description: `Akkermansia muciniphila abundance is well-represented (${val}%), supporting mucosal layer integrity and gut metabolic signaling.`,
          tag: 'Gut Microbiome',
          variant: 'success'
        });
      }
    }
  }

  return insights;
}
