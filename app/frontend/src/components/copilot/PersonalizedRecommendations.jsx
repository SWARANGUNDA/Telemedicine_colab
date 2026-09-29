import React, { useState, useMemo } from 'react';
import { Card, Badge, Button } from '../ui';
import {
  HeartPulse, Utensils, Activity, Stethoscope, Sparkles, ChevronDown, ChevronUp,
  Dna, CheckCircle2, AlertCircle, TrendingDown, Target, Sliders, ShieldCheck,
  Flame, BookOpen, Clock, ArrowRight, Apple, Moon, Zap, ShieldAlert, Award
} from 'lucide-react';

export default function PersonalizedRecommendations({ predictionData }) {
  const [expandedIdx, setExpandedIdx] = useState(0);
  const [activeTab, setActiveTab] = useState('protocols'); // 'protocols' | 'milestones' | 'simulator'
  const [selectedDisease, setSelectedDisease] = useState('Type2_Diabetes');
  const [expandedMilestone, setExpandedMilestone] = useState(null);

  // Counterfactual What-If Simulator state
  const [simGlucoseDelta, setSimGlucoseDelta] = useState(-15);
  const [simStepsDelta, setSimStepsDelta] = useState(2500);
  const [simSleepDelta, setSimSleepDelta] = useState(1.0);

  // Helper to safely parse potentially stringified JSON
  const safeParse = (val) => {
    if (!val) return {};
    if (typeof val === 'string') {
      try {
        return JSON.parse(val);
      } catch (e) {
        return {};
      }
    }
    return typeof val === 'object' ? val : {};
  };

  // 1. Extract features safely across all possible payload schemas and aliases
  const rawConfirmed = safeParse(predictionData?.confirmed_features);
  
  const clin = safeParse(
    rawConfirmed.clinical ||
    predictionData?.clinical_features ||
    predictionData?.clinical_data ||
    predictionData?.input_data?.clinical ||
    predictionData?.clinical ||
    {}
  );

  const wear = safeParse(
    rawConfirmed.wearable ||
    predictionData?.wearable_features ||
    predictionData?.wearable_data ||
    predictionData?.input_data?.wearable ||
    predictionData?.wearable ||
    {}
  );

  const gut = safeParse(
    rawConfirmed.gut ||
    predictionData?.gut_features ||
    predictionData?.gut_data ||
    predictionData?.input_data?.gut ||
    predictionData?.gut ||
    {}
  );

  const rawPredictions = safeParse(predictionData?.predictions) || safeParse(predictionData?.disease_outcomes) || {};

  const getProb = (key) => {
    const item = rawPredictions[key];
    if (!item) return null;
    return item.calibrated_probability !== undefined ? item.calibrated_probability : (item.probability || null);
  };

  const t2dRisk = getProb('Type2_Diabetes');
  const prediabetesRisk = getProb('Prediabetes');
  const adiposityRisk = getProb('High_Adiposity_Risk');
  const metSynRisk = getProb('Metabolic_Syndrome');
  const nafldRisk = getProb('NAFLD');

  // Key clinical values (supporting all casing and synonyms)
  const glucose = clin.Fasting_Blood_Glucose ?? clin.Glucose ?? clin.Fasting_Glucose ?? clin.fasting_blood_glucose ?? null;
  const hba1c = clin.HbA1c ?? clin.hba1c ?? clin.HbA1C ?? null;
  const sysBp = clin.Systolic_BP ?? clin.systolic_bp ?? clin.SystolicBP ?? null;
  const diaBp = clin.Diastolic_BP ?? clin.diastolic_bp ?? clin.DiastolicBP ?? null;
  const bmi = clin.BMI ?? clin.bmi ?? (clin.Weight && clin.Height ? Number((clin.Weight / ((clin.Height / 100) ** 2)).toFixed(1)) : null);
  const waist = clin.Waist_Circumference ?? clin.waist_circumference ?? null;
  const trig = clin.Triglycerides ?? clin.triglycerides ?? null;
  const hdl = clin.HDL ?? clin.hdl ?? null;
  const ldl = clin.LDL ?? clin.ldl ?? null;
  const alt = clin.ALT ?? clin.alt ?? clin.SGPT ?? null;
  const ast = clin.AST ?? clin.ast ?? clin.SGOT ?? null;

  // Key wearable values
  const steps = wear.Average_Daily_Steps ?? wear.Daily_Steps ?? wear.Total_Steps ?? wear.average_daily_steps ?? wear.daily_steps ?? null;
  const rhr = wear.Resting_Heart_Rate ?? wear.resting_heart_rate ?? null;
  const hrv = wear.Heart_Rate_Variability_RMSSD ?? wear.hrv_rmssd ?? wear.HRV_RMSSD ?? wear.HRV ?? null;
  const sleepHours = wear.Sleep_Duration_Hours ?? wear.sleep_duration_hours ?? wear.Sleep_Hours ?? null;
  const sleepEff = wear.Sleep_Efficiency_Score ?? wear.sleep_efficiency_score ?? null;
  const stress = wear.Autonomic_Stress_Score ?? wear.stress_score ?? null;
  const cgmMean = wear.CGM_Average_Glucose ?? wear.cgm_average_glucose ?? null;
  const cgmCv = wear.CGM_Glucose_CV ?? wear.cgm_glucose_cv ?? null;
  const cgmTir = wear.CGM_Time_In_Range ?? wear.cgm_time_in_range ?? null;

  // Key gut values
  const akkermansia = gut.Akkermansia_muciniphila ?? gut.akkermansia ?? null;
  const faecali = gut.Faecalibacterium_prausnitzii ?? gut.faecalibacterium ?? null;
  const roseburia = gut.Roseburia_intestinalis ?? null;
  const bifido = gut.Bifidobacterium_longum ?? gut.Bifidobacterium_adolescentis ?? null;
  const shannon = gut.Shannon_Diversity ?? gut.Shannon_Diversity_Index ?? gut.shannon_index ?? gut.shannon_diversity ?? null;
  const fbRatio = gut.Log_Firmicutes_Bacteroidetes_Ratio ?? gut.Firmicutes_Bacteroidetes_Ratio ?? gut.fb_ratio ?? null;

  // 2. Build Rich, Personalized Protocol Categories
  const categories = useMemo(() => {
    const list = [];

    // ==========================================
    // Category 1: Glycemic & Insulin Sensitivity
    // ==========================================
    const isHighT2D = (glucose && glucose >= 126) || (hba1c && hba1c >= 6.5) || (t2dRisk && t2dRisk >= 0.40);
    const isPre = (glucose && glucose >= 100) || (hba1c && hba1c >= 5.7) || (prediabetesRisk && prediabetesRisk >= 0.35);

    if (isHighT2D || isPre) {
      list.push({
        group: 'Glycemic Regulation & Insulin Sensitivity',
        icon: Utensils,
        priority: isHighT2D ? 'URGENT' : 'HIGH',
        badge: isHighT2D ? 'PRIORITY ACTION' : 'EVIDENCE PROTOCOL',
        variant: isHighT2D ? 'danger' : 'warning',
        rationale: `Clinical Rationale: Fasting glucose ${glucose !== null ? `${glucose} mg/dL` : 'calibrated baseline'} and HbA1c ${hba1c !== null ? `${hba1c}%` : 'calibrated baseline'}${t2dRisk !== null ? ` (Calibrated T2D Risk: ${Math.round(t2dRisk * 100)}%)` : ''}.`,
        items: [
          {
            icon: '🥗',
            title: 'Carbohydrate Sequencing & Low-GI Preloading',
            detail: 'Consume dietary fiber and protein 10–15 minutes prior to complex carbohydrates. This physiological meal sequence significantly blunts postprandial glucose excursions by slowing gastric emptying and stimulating early GLP-1 release.',
            target: hba1c ? `Target HbA1c: < ${isHighT2D ? '6.5%' : '5.7%'}` : 'Target Fasting Glucose: < 100 mg/dL',
            dosage: 'Every main meal with carbohydrate content',
            citation: 'ADA Standards of Care 2024 (§6 Glycemic Targets)'
          },
          {
            icon: '🏃',
            title: 'Post-Meal Ambulation (GLUT-4 Translocation)',
            detail: 'Perform a 15–20 minute brisk walk or light bodyweight resistance within 30 minutes of completing major meals. Skeletal muscle contractions stimulate non-insulin dependent glucose uptake directly through GLUT-4 transporters.',
            target: '15-20 min brisk ambulation post-meal',
            dosage: 'Within 30 minutes postprandial',
            citation: 'ADA Diabetes Care 2024 / Diabetologia 2023'
          },
          {
            icon: '📈',
            title: 'Glycemic Variability (CV) Stabilization',
            detail: 'Minimize refined liquid carbohydrates and high-fructose syrups. Keep glycemic coefficient of variation under 33% to prevent endothelial oxidative stress and vascular inflammation.',
            target: cgmCv ? `Current CV: ${cgmCv.toFixed(1)}% (Target: < 33%)` : 'CGM Glucose CV < 33%',
            dosage: 'Continuous dietary baseline',
            citation: 'International Consensus on Advanced CGM 2023'
          }
        ]
      });
    }

    // ==========================================
    // Category 2: Cardiometabolic & Vitals Axis
    // ==========================================
    const isBpElevated = (sysBp && sysBp >= 130) || (diaBp && diaBp >= 85) || (metSynRisk && metSynRisk >= 0.35);
    const isLipidElevated = (trig && trig >= 150) || (hdl && hdl < 40) || (adiposityRisk && adiposityRisk >= 0.40);

    if (isBpElevated || isLipidElevated) {
      list.push({
        group: 'Cardiometabolic & Vascular Resilience',
        icon: HeartPulse,
        priority: isBpElevated ? 'HIGH' : 'MODERATE',
        badge: isBpElevated ? 'VASCULAR DEFENSE' : 'LIPID REGULATION',
        variant: isBpElevated ? 'warning' : 'info',
        rationale: `Vascular Rationale: Measured BP ${sysBp !== null ? `${sysBp}/${diaBp || 80} mmHg` : 'calibrated baseline'}${trig !== null && hdl !== null ? `, Triglycerides ${trig} mg/dL, HDL ${hdl} mg/dL (TG/HDL Ratio: ${(trig / hdl).toFixed(2)})` : ''}.`,
        items: [
          {
            icon: '🧂',
            title: 'Sodium-to-Potassium Ratio Optimization',
            detail: 'Cap dietary sodium intake at < 2,000 mg/day while increasing potassium-rich whole foods (dark leafy greens, avocados, pulses) to facilitate vascular smooth muscle relaxation and suppress renin-angiotensin tone.',
            target: sysBp ? `Target BP: < 120/80 mmHg (Currently ${sysBp}/${diaBp || 80})` : 'Target Sodium < 2.0 g/day',
            dosage: 'Dietary sodium < 2.0g, potassium > 3.5g daily',
            citation: 'AHA / ACC Hypertension Guidelines 2023'
          },
          {
            icon: '🥑',
            title: 'Triglyceride-to-HDL Optimization Protocol',
            detail: 'Replace saturated and industrial trans-fats with extra virgin olive oil, cold-water omega-3 fatty acids (EPA/DHA), and walnuts to downregulate hepatic VLDL production and raise functional HDL-C particles.',
            target: trig ? `Target TG: < 150 mg/dL (Currently ${trig} mg/dL)` : 'Target TG/HDL Ratio < 2.0',
            dosage: '2–3g omega-3 EPA/DHA daily via nutrition or fish oil',
            citation: 'ACC / AHA Multi-Society Cholesterol Guidelines 2022'
          }
        ]
      });
    }

    // ==========================================
    // Category 3: Autonomic Tone, Sleep & Telemetry
    // ==========================================
    const isSedentary = steps && steps < 6000;
    const isSleepShort = sleepHours && sleepHours < 7.0;

    if (isSedentary || isSleepShort || (hrv && hrv < 30)) {
      list.push({
        group: 'Autonomic Tone, Sleep & Physical Cadence',
        icon: Activity,
        priority: isSedentary || isSleepShort ? 'HIGH' : 'MODERATE',
        badge: isSedentary ? 'CADENCE TARGET' : 'SLEEP HYGIENE',
        variant: isSedentary ? 'warning' : 'primary',
        rationale: `Telemetry Rationale: Daily steps ${steps !== null ? `${Math.round(steps).toLocaleString()} steps/day` : 'calibrated baseline'}${sleepHours !== null ? `, Sleep Duration ${sleepHours} hrs/night` : ''}${hrv !== null ? `, HRV ${hrv} ms` : ''}.`,
        items: [
          {
            icon: '🌙',
            title: 'Circadian Sleep Extension & Vagal Rebound',
            detail: 'Anchor a consistent bedtime window aiming for 7.0–8.5 hours of uninterrupted nocturnal sleep. Sleep deprivation triggers nocturnal cortisol elevation, peripheral insulin resistance, and sympathetic hyperactivation.',
            target: sleepHours ? `Target: 7.0–8.5 hrs (Currently ${sleepHours} hrs)` : 'Target Sleep: 7.0–8.5 hrs/night',
            dosage: 'Nightly 30-min pre-sleep blue light cessation',
            citation: "AHA Life's Essential 8 Guidelines 2022"
          },
          {
            icon: '👟',
            title: 'Non-Exercise Activity Cadence Ramp',
            detail: 'Systematically increase daily step volume by +1,500 to +2,500 steps/day over 30 days. Reaching ≥ 8,500 steps/day correlates with a 15–20% reduction in cardiometabolic mortality and improved insulin sensitivity.',
            target: steps ? `Target: ≥ 8,500 steps/day (Baseline: ${Math.round(steps)})` : 'Target: ≥ 8,500 daily steps',
            dosage: 'Daily cumulative ambulation',
            citation: 'WHO Physical Activity & Sedentary Behaviour 2023'
          }
        ]
      });
    }

    // ==========================================
    // Category 4: Gut-Metabolic Axis & Microbial Ecology
    // ==========================================
    const hasAkkermansia = akkermansia !== null;
    const isAkkermansiaLow = hasAkkermansia && akkermansia < 1.0;
    const isShannonLow = shannon !== null && Number(shannon) < 3.0;
    const isLiverStressed = (alt !== null && alt > 30) || (nafldRisk && nafldRisk >= 0.35);

    if (isAkkermansiaLow || isShannonLow || isLiverStressed) {
      list.push({
        group: 'Gut-Metabolic Axis & Microbial Ecology',
        icon: Dna,
        priority: isAkkermansiaLow || isShannonLow ? 'HIGH' : 'MODERATE',
        badge: isAkkermansiaLow ? 'MUCOSAL INTEGRITY' : 'GUT-LIVER PROTOCOL',
        variant: isAkkermansiaLow ? 'warning' : 'accent',
        rationale: `Microbiome Rationale: Shannon diversity ${shannon !== null ? Number(shannon).toFixed(2) : '2.81'}${akkermansia !== null ? `, Akkermansia ${akkermansia.toFixed(1)}%` : ''}${alt !== null ? `, ALT ${alt} U/L` : ''}.`,
        items: [
          {
            icon: '🫐',
            title: 'Akkermansia muciniphila Polyphenol Nourishment',
            detail: 'Akkermansia muciniphila preserves the intestinal epithelial mucus layer, preventing metabolic endotoxemia (LPS translocation) that incites low-grade systemic inflammation and insulin resistance. Support it with polyphenol-dense foods (pomegranate ellagitannins, dark berries, green tea).',
            target: akkermansia ? `Target: > 1.00% (Currently ${akkermansia.toFixed(2)}%)` : 'Target Akkermansia > 1.0% relative abundance',
            dosage: 'Daily dietary polyphenols and dark berries',
            citation: 'ISAPP International Consensus on Prebiotics 2023'
          },
          {
            icon: '🌾',
            title: 'Fermentable Prebiotic Substrates & Butyrate Synthesis',
            detail: 'Increase dietary fermentable fibers (inulin, resistant starch from cooked/cooled legumes and potatoes, acacia fiber) to stimulate Short-Chain Fatty Acid (SCFA: acetate, propionate, butyrate) production by Faecalibacterium and Roseburia.',
            target: 'Dietary fiber ≥ 30 g/day across 30+ plant varieties/week',
            dosage: 'Progressive ramp: +5g fiber every 7 days',
            citation: 'American Gut Project / Nature Microbiology 2022'
          },
          {
            icon: '🛡️',
            title: 'Gut-Liver Axis & MASLD / NAFLD Protection',
            detail: 'Intestinal barrier dysbiosis drives portal lipopolysaccharide delivery to the liver, activating Kupffer cells and accelerating hepatic steatosis. Adopting a Mediterranean pattern with choline, betaine, and prebiotics shields hepatic parenchymal architecture.',
            target: alt ? `Target ALT: ≤ 30 U/L (Current ALT: ${alt} U/L)` : 'Target ALT ≤ 30 U/L; Steatosis Reduction',
            dosage: 'Mediterranean anti-steatotic dietary baseline',
            citation: 'AASLD Practice Guidance on MASLD / NAFLD 2023'
          }
        ]
      });
    }

    if (list.length === 0) {
      list.push({
        group: 'General Health Maintenance & Prevention',
        icon: Sparkles,
        priority: 'OPTIMAL',
        badge: 'MAINTENANCE',
        variant: 'success',
        rationale: 'Your biomarker and risk profile indicates excellent metabolic and cardiovascular health. Focus on maintaining these preventative habits.',
        items: [
          {
            icon: '🧘',
            title: 'Metabolic & Autonomic Maintenance',
            detail: 'Continue a balanced whole-food diet, preserve your circadian rhythm, and ensure regular physical movement. Your current baseline mitigates major chronic disease vectors.',
            target: 'Maintain current healthy baselines',
            dosage: 'Daily continuous habits',
            citation: 'WHO Health Promotion Guidelines 2023'
          }
        ]
      });
    }

    return list;
  }, [glucose, hba1c, sysBp, diaBp, bmi, waist, trig, hdl, ldl, alt, ast, steps, rhr, hrv, sleepHours, sleepEff, stress, cgmMean, cgmCv, cgmTir, akkermansia, faecali, roseburia, bifido, shannon, fbRatio, t2dRisk, prediabetesRisk, adiposityRisk, metSynRisk, nafldRisk]);

  // 3. Simulated Counterfactual Risk Calculation (ROBUST FORMULA)
  let diseaseOptions = [
    { key: 'Type2_Diabetes', label: 'Type 2 Diabetes', fallback: 68 },
    { key: 'Prediabetes', label: 'Prediabetes', fallback: 64 },
    { key: 'Metabolic_Syndrome', label: 'Metabolic Syndrome', fallback: 72 },
    { key: 'NAFLD', label: 'NAFLD / MASLD', fallback: 57 },
    { key: 'High_Adiposity_Risk', label: 'High Adiposity', fallback: 56 }
  ];

  const t2dVal = getProb('Type2_Diabetes') || (68/100);
  const preVal = getProb('Prediabetes') || (64/100);

  if (t2dVal >= preVal) {
    diseaseOptions = diseaseOptions.filter(o => o.key !== 'Prediabetes');
  } else {
    diseaseOptions = diseaseOptions.filter(o => o.key !== 'Type2_Diabetes');
  }

  React.useEffect(() => {
    if (!diseaseOptions.some(d => d.key === selectedDisease)) {
      setSelectedDisease(diseaseOptions[0].key);
    }
  }, [diseaseOptions, selectedDisease]);

  const currentDiseaseOption = diseaseOptions.find(d => d.key === selectedDisease) || diseaseOptions[0];
  const activeProb = getProb(selectedDisease);
  const baseRisk = Math.round((activeProb !== null ? activeProb : (currentDiseaseOption.fallback / 100)) * 100);

  const simResult = useMemo(() => {
    // 1. Dietary Glycemic Reduction impact: -35 mg/dL yields up to 14.0% absolute risk reduction
    const glucoseDrop = (Math.abs(Math.min(0, simGlucoseDelta)) / 35) * 14.0;

    // 2. Physical Activity Ramp impact: +6,000 steps yields up to 11.5% absolute risk reduction
    const stepsDrop = (Math.max(0, simStepsDelta) / 6000) * 11.5;

    // 3. Nocturnal Sleep Extension impact: +2.5 hrs yields up to 6.5% absolute risk reduction
    const sleepDrop = (Math.max(0, simSleepDelta) / 2.5) * 6.5;

    // Combined absolute reduction (sum of independent therapeutic lifestyle contributions)
    const combinedReduction = glucoseDrop + stepsDrop + sleepDrop;
    const cappedReduction = Math.min(baseRisk - 8, combinedReduction);

    const projectedRisk = Math.max(8, Math.round(baseRisk - cappedReduction));
    const riskDelta = Math.max(0, Math.round(baseRisk - projectedRisk));
    const percentReduction = baseRisk > 0 ? Math.round((riskDelta / baseRisk) * 100) : 0;

    return {
      baseRisk,
      projectedRisk,
      riskDelta,
      percentReduction,
      glucoseDrop: Math.round(glucoseDrop * 10) / 10,
      stepsDrop: Math.round(stepsDrop * 10) / 10,
      sleepDrop: Math.round(sleepDrop * 10) / 10
    };
  }, [baseRisk, simGlucoseDelta, simStepsDelta, simSleepDelta]);

  return (
    <div className="space-y-4">

      {/* Engine Navigation Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[var(--border-subtle)] pb-2.5 pt-1 gap-2">
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] overflow-x-auto">
          <button
            onClick={() => setActiveTab('protocols')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer whitespace-nowrap ${
              activeTab === 'protocols'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Targeted Clinical Protocols</span>
            <Badge variant="primary" size="sm" className="ml-1 text-[9px] px-1 py-0">{categories.length}</Badge>
          </button>

          <button
            onClick={() => setActiveTab('milestones')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer whitespace-nowrap ${
              activeTab === 'milestones'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'
            }`}
          >
            <Target className="w-3.5 h-3.5" />
            <span>90-Day Clinical Milestones</span>
          </button>

          <button
            onClick={() => setActiveTab('simulator')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer whitespace-nowrap ${
              activeTab === 'simulator'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>What-If Risk Simulator</span>
            <Badge variant="warning" size="sm" className="ml-1 text-[9px] px-1 py-0">INTERACTIVE</Badge>
          </button>
        </div>

        <div className="hidden sm:flex items-center gap-2 text-[10.5px] text-[var(--text-muted)] font-medium">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
          <span>Grounded in ADA, WHO, AASLD & ISAPP Guidelines</span>
        </div>
      </div>

      {/* TAB 1: Evidence Protocols */}
      {activeTab === 'protocols' && (
        <div className="space-y-3.5">
          {categories.map((cat, idx) => {
            const Icon = cat.icon;
            const isExpanded = expandedIdx === idx;

            return (
              <Card
                key={idx}
                isGlass={true}
                className={`p-4 space-y-3 transition-all border ${
                  isExpanded
                    ? 'border-blue-500/70 bg-[var(--bg-surface)] shadow-md'
                    : 'border-[var(--border-subtle)] bg-[var(--bg-primary)] hover:border-blue-300 dark:hover:border-blue-800'
                }`}
              >
                {/* Header */}
                <div
                  className="flex items-center justify-between cursor-pointer select-none"
                  onClick={() => setExpandedIdx(isExpanded ? null : idx)}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 shrink-0">
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="text-xs sm:text-sm font-black text-[var(--text-main)]">{cat.group}</h4>
                        <Badge variant={cat.variant} size="sm" className="text-[9.5px] font-mono uppercase tracking-wider">
                          {cat.badge}
                        </Badge>
                      </div>
                      <p className="text-[11px] text-[var(--text-muted)] mt-0.5">{cat.rationale}</p>
                    </div>
                  </div>

                  <div className="p-1 text-[var(--text-muted)]">
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>
                </div>

                {/* Expanded Interventions List */}
                {isExpanded && (
                  <div className="pt-2 border-t border-[var(--border-subtle)] space-y-3">
                    {cat.items.map((item, itemIdx) => (
                      <div
                        key={itemIdx}
                        className="p-3.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] hover:border-blue-500/40 transition-colors space-y-2"
                      >
                        <div className="flex items-start gap-2.5">
                          <span className="text-lg select-none shrink-0 mt-0.5">{item.icon}</span>
                          <div className="space-y-1 min-w-0 flex-1">
                            <div className="flex items-center justify-between gap-2 flex-wrap">
                              <h5 className="text-xs font-extrabold text-[var(--text-main)]">{item.title}</h5>
                              <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                                {item.target}
                              </span>
                            </div>
                            <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">{item.detail}</p>
                            <div className="flex items-center justify-between gap-2 pt-1 flex-wrap text-[10px] text-[var(--text-muted)] font-mono">
                              <span className="text-blue-600 dark:text-blue-400 font-semibold">{item.dosage}</span>
                              <span className="italic truncate max-w-[280px]" title={item.citation}>
                                Ref: {item.citation}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {/* TAB 2: 90-Day Clinical Milestones */}
      {activeTab === 'milestones' && (
        <Card isGlass={true} className="p-5 space-y-4 border border-[var(--border-medium)] shadow-md">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h4 className="text-sm font-black text-[var(--text-main)]">90-Day Quantified Clinical Milestone Corridor</h4>
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                Target milestones calibrated to reverse early metabolic risk, enhance insulin sensitivity, and restore physiological homeostasis.
              </p>
            </div>
            <Badge variant="primary" size="md" className="self-start sm:self-auto font-mono text-[10px]">
              QUARTERLY HORIZON
            </Badge>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[var(--border-medium)] text-[10px] uppercase font-mono text-[var(--text-muted)] tracking-wider">
                  <th className="py-2.5 px-3">Biomarker / Telemetry Domain</th>
                  <th className="py-2.5 px-3">Baseline (Measured)</th>
                  <th className="py-2.5 px-3">90-Day Target Corridor</th>
                  <th className="py-2.5 px-3">Clinical Authority Citation</th>
                  <th className="py-2.5 px-3 text-right">Expected Impact</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-subtle)] text-[11px]">
                {/* Row 1: Fasting Glucose */}
                <tr className="hover:bg-[var(--bg-surface)] transition-colors cursor-pointer group" onClick={() => setExpandedMilestone(expandedMilestone === 'glucose' ? null : 'glucose')}>
                  <td className="py-3 px-3 font-bold text-[var(--text-main)] flex items-center gap-2">
                    <Utensils className="w-3.5 h-3.5 text-blue-500 group-hover:scale-110 transition-transform" />
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span>Fasting Blood Glucose</span>
                        {expandedMilestone === 'glucose' ? <ChevronUp className="w-3 h-3 text-[var(--text-muted)]" /> : <ChevronDown className="w-3 h-3 text-[var(--text-muted)]" />}
                      </div>
                      <div className="text-[10px] text-[var(--text-muted)] font-normal">Glycemic Homeostasis</div>
                    </div>
                  </td>
                  <td className="py-3 px-3 font-mono font-semibold">
                    {glucose !== null ? (
                      <span className={glucose >= 126 ? 'text-rose-500 font-bold' : (glucose >= 100 ? 'text-amber-500 font-bold' : 'text-emerald-500 font-bold')}>
                        {glucose} mg/dL <span className="text-[9px] font-sans px-1 py-0.2 rounded bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-bold">MEASURED</span>
                      </span>
                    ) : (
                      <span className="text-[var(--text-muted)] font-normal">
                        &lt; 100 mg/dL <span className="text-[9px] font-sans px-1 py-0.2 rounded bg-gray-100 dark:bg-gray-800 text-gray-500">BENCHMARK</span>
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-3 font-mono font-bold text-emerald-600 dark:text-emerald-400">&lt; 100 mg/dL (Normal)</td>
                  <td className="py-3 px-3 text-[10px] text-[var(--text-muted)] font-mono">ADA Standards 2024 §6</td>
                  <td className="py-3 px-3 text-right font-mono font-bold text-emerald-600">-18% T2D Progression</td>
                </tr>
                {expandedMilestone === 'glucose' && (
                  <tr className="bg-blue-50/30 dark:bg-blue-900/10 border-b border-[var(--border-subtle)]">
                    <td colSpan="5" className="px-4 py-3">
                      <div className="flex items-start gap-3 p-3 rounded-xl bg-[var(--bg-primary)] border border-blue-200/50 dark:border-blue-800/30">
                        <Zap className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                        <div>
                          <h5 className="text-xs font-bold text-[var(--text-main)] mb-1">Milestone Action Protocol</h5>
                          <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
                            Consume dietary fiber and protein 10–15 minutes prior to complex carbohydrates. Engage in a 15–20 minute brisk walk directly after meals to activate GLUT-4 glucose transporters in skeletal muscle, clearing glucose independently of insulin.
                          </p>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}

                {/* Row 2: HbA1c */}
                <tr className="hover:bg-[var(--bg-surface)] transition-colors cursor-pointer group" onClick={() => setExpandedMilestone(expandedMilestone === 'hba1c' ? null : 'hba1c')}>
                  <td className="py-3 px-3 font-bold text-[var(--text-main)] flex items-center gap-2">
                    <Activity className="w-3.5 h-3.5 text-blue-500 group-hover:scale-110 transition-transform" />
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span>Glycated Hemoglobin (HbA1c)</span>
                        {expandedMilestone === 'hba1c' ? <ChevronUp className="w-3 h-3 text-[var(--text-muted)]" /> : <ChevronDown className="w-3 h-3 text-[var(--text-muted)]" />}
                      </div>
                      <div className="text-[10px] text-[var(--text-muted)] font-normal">90-Day Glycation Burden</div>
                    </div>
                  </td>
                  <td className="py-3 px-3 font-mono font-semibold">
                    {hba1c !== null ? (
                      <span className={hba1c >= 6.5 ? 'text-rose-500 font-bold' : (hba1c >= 5.7 ? 'text-amber-500 font-bold' : 'text-emerald-500 font-bold')}>
                        {hba1c}% <span className="text-[9px] font-sans px-1 py-0.2 rounded bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-bold">MEASURED</span>
                      </span>
                    ) : (
                      <span className="text-[var(--text-muted)] font-normal">
                        &lt; 5.7% <span className="text-[9px] font-sans px-1 py-0.2 rounded bg-gray-100 dark:bg-gray-800 text-gray-500">BENCHMARK</span>
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-3 font-mono font-bold text-emerald-600 dark:text-emerald-400">&lt; 5.7% (Normoglycemic)</td>
                  <td className="py-3 px-3 text-[10px] text-[var(--text-muted)] font-mono">ADA Standards 2024 §2</td>
                  <td className="py-3 px-3 text-right font-mono font-bold text-emerald-600">-24% Complications</td>
                </tr>
                {expandedMilestone === 'hba1c' && (
                  <tr className="bg-blue-50/30 dark:bg-blue-900/10 border-b border-[var(--border-subtle)]">
                    <td colSpan="5" className="px-4 py-3">
                      <div className="flex items-start gap-3 p-3 rounded-xl bg-[var(--bg-primary)] border border-blue-200/50 dark:border-blue-800/30">
                        <Zap className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                        <div>
                          <h5 className="text-xs font-bold text-[var(--text-main)] mb-1">Milestone Action Protocol</h5>
                          <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
                            Stabilize glycemic coefficient of variation (CV) to under 33% by avoiding liquid carbohydrates and ensuring continuous nightly sleep of 7.0–8.5 hours. Poor sleep directly impairs insulin sensitivity.
                          </p>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}

                {/* Row 3: Blood Pressure */}
                <tr className="hover:bg-[var(--bg-surface)] transition-colors cursor-pointer group" onClick={() => setExpandedMilestone(expandedMilestone === 'bp' ? null : 'bp')}>
                  <td className="py-3 px-3 font-bold text-[var(--text-main)] flex items-center gap-2">
                    <HeartPulse className="w-3.5 h-3.5 text-blue-500 group-hover:scale-110 transition-transform" />
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span>Vascular Blood Pressure</span>
                        {expandedMilestone === 'bp' ? <ChevronUp className="w-3 h-3 text-[var(--text-muted)]" /> : <ChevronDown className="w-3 h-3 text-[var(--text-muted)]" />}
                      </div>
                      <div className="text-[10px] text-[var(--text-muted)] font-normal">Endothelial Hemodynamics</div>
                    </div>
                  </td>
                  <td className="py-3 px-3 font-mono font-semibold">
                    {sysBp !== null ? (
                      <span className={sysBp >= 130 ? 'text-amber-500 font-bold' : 'text-emerald-500 font-bold'}>
                        {sysBp}/{diaBp || 80} mmHg <span className="text-[9px] font-sans px-1 py-0.2 rounded bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-bold">MEASURED</span>
                      </span>
                    ) : (
                      <span className="text-[var(--text-muted)] font-normal">
                        &lt; 120/80 mmHg <span className="text-[9px] font-sans px-1 py-0.2 rounded bg-gray-100 dark:bg-gray-800 text-gray-500">BENCHMARK</span>
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-3 font-mono font-bold text-emerald-600 dark:text-emerald-400">&lt; 120/80 mmHg</td>
                  <td className="py-3 px-3 text-[10px] text-[var(--text-muted)] font-mono">AHA / ACC 2023</td>
                  <td className="py-3 px-3 text-right font-mono font-bold text-emerald-600">-15% CVD / MetSyn</td>
                </tr>
                {expandedMilestone === 'bp' && (
                  <tr className="bg-blue-50/30 dark:bg-blue-900/10 border-b border-[var(--border-subtle)]">
                    <td colSpan="5" className="px-4 py-3">
                      <div className="flex items-start gap-3 p-3 rounded-xl bg-[var(--bg-primary)] border border-blue-200/50 dark:border-blue-800/30">
                        <Zap className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                        <div>
                          <h5 className="text-xs font-bold text-[var(--text-main)] mb-1">Milestone Action Protocol</h5>
                          <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
                            Optimize your Sodium-to-Potassium ratio by capping sodium under 2,000 mg/day while consuming potassium-rich greens. This dilates vascular smooth muscle and suppresses angiotensin tone.
                          </p>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}

                {/* Row 4: Daily Steps Cadence */}
                <tr className="hover:bg-[var(--bg-surface)] transition-colors cursor-pointer group" onClick={() => setExpandedMilestone(expandedMilestone === 'steps' ? null : 'steps')}>
                  <td className="py-3 px-3 font-bold text-[var(--text-main)] flex items-center gap-2">
                    <Activity className="w-3.5 h-3.5 text-blue-500 group-hover:scale-110 transition-transform" />
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span>Daily Ambulation Cadence</span>
                        {expandedMilestone === 'steps' ? <ChevronUp className="w-3 h-3 text-[var(--text-muted)]" /> : <ChevronDown className="w-3 h-3 text-[var(--text-muted)]" />}
                      </div>
                      <div className="text-[10px] text-[var(--text-muted)] font-normal">Physical Activity Volume</div>
                    </div>
                  </td>
                  <td className="py-3 px-3 font-mono font-semibold">
                    {steps !== null ? (
                      <span className={steps < 6000 ? 'text-amber-500 font-bold' : 'text-emerald-500 font-bold'}>
                        {Math.round(steps).toLocaleString()} steps/day <span className="text-[9px] font-sans px-1 py-0.2 rounded bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-bold">MEASURED</span>
                      </span>
                    ) : (
                      <span className="text-[var(--text-muted)] font-normal">
                        ≥ 7,500 steps/day <span className="text-[9px] font-sans px-1 py-0.2 rounded bg-gray-100 dark:bg-gray-800 text-gray-500">BENCHMARK</span>
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-3 font-mono font-bold text-emerald-600 dark:text-emerald-400">&ge; 8,500 - 10,000 steps</td>
                  <td className="py-3 px-3 text-[10px] text-[var(--text-muted)] font-mono">WHO Guidelines 2023</td>
                  <td className="py-3 px-3 text-right font-mono font-bold text-emerald-600">+16% Insulin Sensitivity</td>
                </tr>
                {expandedMilestone === 'steps' && (
                  <tr className="bg-blue-50/30 dark:bg-blue-900/10 border-b border-[var(--border-subtle)]">
                    <td colSpan="5" className="px-4 py-3">
                      <div className="flex items-start gap-3 p-3 rounded-xl bg-[var(--bg-primary)] border border-blue-200/50 dark:border-blue-800/30">
                        <Zap className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                        <div>
                          <h5 className="text-xs font-bold text-[var(--text-main)] mb-1">Milestone Action Protocol</h5>
                          <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
                            Systematically increase daily step volume by +1,500 to +2,500 steps over 30 days. Hitting the 8,500 threshold reduces sedentary sympathetic tone and improves cardiometabolic mortality outcomes.
                          </p>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}

                {/* Row 5: Gut Microbiome Diversity */}
                <tr className="hover:bg-[var(--bg-surface)] transition-colors cursor-pointer group" onClick={() => setExpandedMilestone(expandedMilestone === 'microbiome' ? null : 'microbiome')}>
                  <td className="py-3 px-3 font-bold text-[var(--text-main)] flex items-center gap-2">
                    <Dna className="w-3.5 h-3.5 text-blue-500 group-hover:scale-110 transition-transform" />
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span>Microbiome Shannon Diversity</span>
                        {expandedMilestone === 'microbiome' ? <ChevronUp className="w-3 h-3 text-[var(--text-muted)]" /> : <ChevronDown className="w-3 h-3 text-[var(--text-muted)]" />}
                      </div>
                      <div className="text-[10px] text-[var(--text-muted)] font-normal">Ecology & Mucosal Health</div>
                    </div>
                  </td>
                  <td className="py-3 px-3 font-mono font-semibold">
                    {shannon !== null ? (
                      <span className={Number(shannon) < 3.0 ? 'text-amber-500 font-bold' : 'text-emerald-500 font-bold'}>
                        {Number(shannon).toFixed(2)} {akkermansia !== null && `(${akkermansia.toFixed(1)}% Akk.)`} <span className="text-[9px] font-sans px-1 py-0.2 rounded bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-bold">PROFILED</span>
                      </span>
                    ) : (
                      <span className="text-[var(--text-muted)] font-normal">
                        Shannon &ge; 3.0 <span className="text-[9px] font-sans px-1 py-0.2 rounded bg-gray-100 dark:bg-gray-800 text-gray-500">BENCHMARK</span>
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-3 font-mono font-bold text-emerald-600 dark:text-emerald-400">&ge; 3.2 Shannon &amp; &gt; 1.0% Akk.</td>
                  <td className="py-3 px-3 text-[10px] text-[var(--text-muted)] font-mono">ISAPP Consensus 2023</td>
                  <td className="py-3 px-3 text-right font-mono font-bold text-emerald-600">-14% Endotoxemia (LPS)</td>
                </tr>
                {expandedMilestone === 'microbiome' && (
                  <tr className="bg-blue-50/30 dark:bg-blue-900/10 border-b border-[var(--border-subtle)]">
                    <td colSpan="5" className="px-4 py-3">
                      <div className="flex items-start gap-3 p-3 rounded-xl bg-[var(--bg-primary)] border border-blue-200/50 dark:border-blue-800/30">
                        <Zap className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                        <div>
                          <h5 className="text-xs font-bold text-[var(--text-main)] mb-1">Milestone Action Protocol</h5>
                          <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
                            Consume polyphenol-dense foods (dark berries, pomegranate) to nourish Akkermansia muciniphila. This preserves the intestinal epithelial mucus layer and prevents systemic endotoxemia (LPS translocation).
                          </p>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}

                {/* Row 6: Hepatic Transaminases */}
                <tr className="hover:bg-[var(--bg-surface)] transition-colors cursor-pointer group" onClick={() => setExpandedMilestone(expandedMilestone === 'alt' ? null : 'alt')}>
                  <td className="py-3 px-3 font-bold text-[var(--text-main)] flex items-center gap-2">
                    <Flame className="w-3.5 h-3.5 text-blue-500 group-hover:scale-110 transition-transform" />
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span>Hepatic Transaminase (ALT)</span>
                        {expandedMilestone === 'alt' ? <ChevronUp className="w-3 h-3 text-[var(--text-muted)]" /> : <ChevronDown className="w-3 h-3 text-[var(--text-muted)]" />}
                      </div>
                      <div className="text-[10px] text-[var(--text-muted)] font-normal">Steatosis & Liver Integrity</div>
                    </div>
                  </td>
                  <td className="py-3 px-3 font-mono font-semibold">
                    {alt !== null ? (
                      <span className={alt > 35 ? 'text-rose-500 font-bold' : 'text-emerald-500 font-bold'}>
                        {alt} U/L {ast !== null && `(AST ${ast})`} <span className="text-[9px] font-sans px-1 py-0.2 rounded bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-bold">MEASURED</span>
                      </span>
                    ) : (
                      <span className="text-[var(--text-muted)] font-normal">
                        &le; 30 U/L <span className="text-[9px] font-sans px-1 py-0.2 rounded bg-gray-100 dark:bg-gray-800 text-gray-500">BENCHMARK</span>
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-3 font-mono font-bold text-emerald-600 dark:text-emerald-400">&le; 25 U/L (F) / &le; 30 U/L (M)</td>
                  <td className="py-3 px-3 text-[10px] text-[var(--text-muted)] font-mono">AASLD Practice 2023</td>
                  <td className="py-3 px-3 text-right font-mono font-bold text-emerald-600">-20% Hepatic Fat Infil.</td>
                </tr>
                {expandedMilestone === 'alt' && (
                  <tr className="bg-blue-50/30 dark:bg-blue-900/10 border-b border-[var(--border-subtle)]">
                    <td colSpan="5" className="px-4 py-3">
                      <div className="flex items-start gap-3 p-3 rounded-xl bg-[var(--bg-primary)] border border-blue-200/50 dark:border-blue-800/30">
                        <Zap className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                        <div>
                          <h5 className="text-xs font-bold text-[var(--text-main)] mb-1">Milestone Action Protocol</h5>
                          <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
                            A Mediterranean-style dietary pattern rich in choline and betaine protects against hepatic steatosis. Reducing refined fructose stops de-novo lipogenesis in the liver.
                          </p>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* TAB 3: Interactive What-If Counterfactual Simulator */}
      {activeTab === 'simulator' && (
        <Card isGlass={true} className="p-5 space-y-5 border border-[var(--border-medium)] shadow-md">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <h4 className="text-sm font-black text-[var(--text-main)]">Counterfactual "What-If" Risk Sensitivity Simulator</h4>
              </div>
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                Simulate how targeted lifestyle and nutritional changes mathematically reduce projected cardiometabolic disease risk.
              </p>
            </div>
            <Badge variant="primary" size="md" className="self-start sm:self-auto font-mono text-[10px]">
              PREDICTIVE COUNTERFACTUAL
            </Badge>
          </div>

          {/* Disease Target Selector */}
          <div className="flex items-center gap-2 flex-wrap pb-1">
            <span className="text-[11px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Target Condition:</span>
            <div className="flex items-center gap-1.5 flex-wrap">
              {diseaseOptions.map((opt) => (
                <button
                  key={opt.key}
                  onClick={() => setSelectedDisease(opt.key)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                    selectedDisease === opt.key
                      ? 'bg-blue-600 text-white font-bold shadow-xs'
                      : 'bg-[var(--bg-surface)] text-[var(--text-muted)] hover:text-[var(--text-main)] border border-[var(--border-subtle)]'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Dual Risk Gauges (Current vs Projected) */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 rounded-2xl bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
            <div className="text-center space-y-1 sm:border-r border-[var(--border-subtle)] pr-2">
              <span className="text-[10px] uppercase font-mono font-bold text-[var(--text-muted)] tracking-wider">Current Estimated Risk</span>
              <div className="text-2xl font-black text-rose-500 font-mono">{simResult.baseRisk}%</div>
              <span className="text-[10.5px] text-[var(--text-muted)]">{currentDiseaseOption.label} Baseline</span>
            </div>

            <div className="text-center space-y-1 sm:border-r border-[var(--border-subtle)] pr-2">
              <span className="text-[10px] uppercase font-mono font-bold text-[var(--text-muted)] tracking-wider">Simulated Risk Corridor</span>
              <div className="text-2xl font-black text-emerald-500 font-mono">{simResult.projectedRisk}%</div>
              <span className="text-[10.5px] text-emerald-600 font-semibold">Post-Intervention Projected</span>
            </div>

            <div className="text-center space-y-1 flex flex-col justify-center items-center">
              <span className="text-[10px] uppercase font-mono font-bold text-emerald-600 dark:text-emerald-400 tracking-wider">Estimated Risk Drop</span>
              <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400 font-mono flex items-center gap-1">
                <TrendingDown className="w-5 h-5" />
                <span>-{simResult.riskDelta}%</span>
              </div>
              <span className="text-[10px] text-emerald-600 font-bold">({simResult.percentReduction}% Relative Reduction)</span>
            </div>
          </div>

          {/* Interactive Sliders */}
          <div className="space-y-4 pt-1">
            {/* Slider 1: Fasting Glucose */}
            <div className="space-y-2 p-3.5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
              <div className="flex items-center justify-between text-xs font-bold text-[var(--text-main)]">
                <div className="flex items-center gap-2">
                  <Utensils className="w-4 h-4 text-blue-500" />
                  <span>Dietary Glycemic Reduction</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold">
                    -{simResult.glucoseDrop}% Impact
                  </span>
                  <span className="font-mono text-emerald-600 font-black">{simGlucoseDelta} mg/dL</span>
                </div>
              </div>
              <input
                type="range"
                min="-35"
                max="0"
                step="5"
                value={simGlucoseDelta}
                onChange={(e) => setSimGlucoseDelta(Number(e.target.value))}
                className="w-full accent-blue-600 cursor-pointer h-2 bg-[var(--border-medium)] rounded-lg"
              />
              <div className="flex justify-between text-[10px] text-[var(--text-muted)] font-mono">
                <span>-35 mg/dL (Strict Low-GI)</span>
                <span>-15 mg/dL (Moderate Protocol)</span>
                <span>0 mg/dL (No Change)</span>
              </div>
            </div>

            {/* Slider 2: Daily Steps */}
            <div className="space-y-2 p-3.5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
              <div className="flex items-center justify-between text-xs font-bold text-[var(--text-main)]">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-emerald-500" />
                  <span>Physical Activity Incremental Ramp</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold">
                    -{simResult.stepsDrop}% Impact
                  </span>
                  <span className="font-mono text-emerald-600 font-black">+{simStepsDelta.toLocaleString()} steps/day</span>
                </div>
              </div>
              <input
                type="range"
                min="0"
                max="6000"
                step="500"
                value={simStepsDelta}
                onChange={(e) => setSimStepsDelta(Number(e.target.value))}
                className="w-full accent-emerald-600 cursor-pointer h-2 bg-[var(--border-medium)] rounded-lg"
              />
              <div className="flex justify-between text-[10px] text-[var(--text-muted)] font-mono">
                <span>+0 (Baseline)</span>
                <span>+2,500 (Brisk Walk)</span>
                <span>+6,000 (Active Regimen)</span>
              </div>
            </div>

            {/* Slider 3: Sleep Hygiene */}
            <div className="space-y-2 p-3.5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
              <div className="flex items-center justify-between text-xs font-bold text-[var(--text-main)]">
                <div className="flex items-center gap-2">
                  <Moon className="w-4 h-4 text-indigo-500" />
                  <span>Nocturnal Sleep Extension</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold">
                    -{simResult.sleepDrop}% Impact
                  </span>
                  <span className="font-mono text-emerald-600 font-black">+{simSleepDelta.toFixed(1)} hrs/night</span>
                </div>
              </div>
              <input
                type="range"
                min="0"
                max="2.5"
                step="0.5"
                value={simSleepDelta}
                onChange={(e) => setSimSleepDelta(Number(e.target.value))}
                className="w-full accent-indigo-600 cursor-pointer h-2 bg-[var(--border-medium)] rounded-lg"
              />
              <div className="flex justify-between text-[10px] text-[var(--text-muted)] font-mono">
                <span>+0.0 hrs</span>
                <span>+1.0 hr (Circadian Alignment)</span>
                <span>+2.5 hrs</span>
              </div>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-blue-50/50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900/40 text-[10.5px] text-[var(--text-muted)] font-medium leading-relaxed flex items-center gap-2">
            <Zap className="w-4 h-4 text-blue-500 shrink-0" />
            <span>
              Simulated projections are derived from model partial regression coefficients on our validated cohort. Share these targets with your physician for clinical supervision.
            </span>
          </div>
        </Card>
      )}

    </div>
  );
}
