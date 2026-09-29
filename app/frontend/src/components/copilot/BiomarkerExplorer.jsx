import React, { useState, useEffect } from 'react';
import { Card, Badge, Input, Button } from '../ui';
import {
  Search, Activity, ChevronDown, ChevronUp, TrendingDown, TrendingUp, CheckCircle2,
  HelpCircle, FileText, Watch, Dna, Sparkles, Filter, Database, RefreshCw, Eye
} from 'lucide-react';
import { fetchPatientRecords } from '../../api/client';
import { classifyBiomarker } from '../../utils/clinicalRanges';

export default function BiomarkerExplorer({ predictionData, user }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedModality, setSelectedModality] = useState('ALL');
  const [showAll, setShowAll] = useState(false);
  const [expandedId, setExpandedId] = useState(null);

  // Fallback state for loading saved records from backend
  const [historicalRecord, setHistoricalRecord] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);

  useEffect(() => {
    async function loadFallbackRecord() {
      if (!predictionData || (!predictionData.confirmed_features && !predictionData.clinical_features && !predictionData.input_data)) {
        setHistoryLoading(true);
        try {
          const res = await fetchPatientRecords().catch(() => null);
          if (res?.records && res.records.length > 0) {
            setHistoricalRecord(res.records[0]);
          }
        } catch (err) {
          // Gracefully continue without historical fallback
        } finally {
          setHistoryLoading(false);
        }
      }
    }
    loadFallbackRecord();
  }, [predictionData]);

  // Extract active features strictly from active predictionData OR historical record
  const activeSource = predictionData || historicalRecord?.prediction_snapshot || historicalRecord;

  const clinFeats = activeSource?.confirmed_features?.clinical 
    || activeSource?.clinical_features 
    || activeSource?.clinical_data 
    || activeSource?.input_data?.clinical 
    || {};

  const wearFeats = activeSource?.confirmed_features?.wearable 
    || activeSource?.wearable_features 
    || activeSource?.wearable_data 
    || activeSource?.input_data?.wearable 
    || {};

  const gutFeats = activeSource?.confirmed_features?.gut 
    || activeSource?.gut_features 
    || activeSource?.gut_data 
    || activeSource?.input_data?.gut 
    || {};

  // Build list of strictly extracted biomarkers (NO DEMO DATA MIXING)
  const extractedBiomarkers = [
    ...Object.keys(clinFeats).filter(k => clinFeats[k] !== '' && clinFeats[k] !== null && clinFeats[k] !== undefined).map((k, idx) => {
      const val = clinFeats[k];
      const classification = classifyBiomarker ? classifyBiomarker(k, val) : null;
      return {
        id: `CLIN-${idx + 1}`,
        name: k.replace(/_/g, ' '),
        rawName: k,
        current: `${val}`,
        status: classification?.status || 'CONFIRMED',
        statusVariant: classification?.status === 'HIGH' ? 'danger' : classification?.status === 'LOW' ? 'warning' : 'success',
        modality: 'Clinical',
        emoji: '🩺',
        unit: getUnit(k),
        refRange: classification?.range || getRefRange(k),
        interp: getPlainInterpretation(k, val, 'clinical')
      };
    }),
    ...Object.keys(wearFeats).filter(k => wearFeats[k] !== '' && wearFeats[k] !== null && wearFeats[k] !== undefined).map((k, idx) => {
      const val = wearFeats[k];
      return {
        id: `WEAR-${idx + 1}`,
        name: k.replace(/_/g, ' '),
        rawName: k,
        current: `${val}`,
        status: 'ACTIVE',
        statusVariant: 'secondary',
        modality: 'Wearable',
        emoji: '⌚',
        unit: getUnit(k),
        refRange: getRefRange(k),
        interp: getPlainInterpretation(k, val, 'wearable')
      };
    }),
    ...Object.keys(gutFeats).filter(k => gutFeats[k] !== '' && gutFeats[k] !== null && gutFeats[k] !== undefined).map((k, idx) => {
      const val = gutFeats[k];
      return {
        id: `GUT-${idx + 1}`,
        name: k.replace(/_/g, ' '),
        rawName: k,
        current: `${val}`,
        status: 'PROFILED',
        statusVariant: 'accent',
        modality: 'Gut',
        emoji: '🧬',
        unit: '%',
        refRange: getRefRange(k),
        interp: getPlainInterpretation(k, val, 'gut')
      };
    })
  ];

  // Count items per modality
  const clinCount = extractedBiomarkers.filter(b => b.modality === 'Clinical').length;
  const wearCount = extractedBiomarkers.filter(b => b.modality === 'Wearable').length;
  const gutCount = extractedBiomarkers.filter(b => b.modality === 'Gut').length;

  const filteredBiomarkers = extractedBiomarkers.filter(b => {
    const matchesSearch = b.name.toLowerCase().includes(searchQuery.toLowerCase()) || b.id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesMod = selectedModality === 'ALL' || b.modality.toLowerCase() === selectedModality.toLowerCase();
    return matchesSearch && matchesMod;
  });

  const visibleBiomarkers = showAll ? filteredBiomarkers : filteredBiomarkers.slice(0, 12);
  const hasMore = filteredBiomarkers.length > 12;

  return (
    <Card isGlass={true} className="p-6 space-y-5 shadow-xl border-t-4 border-t-[var(--accent)]">
      {/* Header Banner */}
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-4 flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-[var(--accent)]" />
          <div>
            <h3 className="text-base font-extrabold text-[var(--text-main)]">Biomarker Intelligence Explorer</h3>
            <p className="text-[10px] text-[var(--text-muted)]">
              Strictly displaying measurements extracted from your uploaded health reports
            </p>
          </div>
        </div>

        <Badge variant="accent" size="sm">{extractedBiomarkers.length} Extracted Measurements</Badge>
      </div>

      {/* Controls Bar: Search & Modality Filters */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="w-full sm:w-80">
          <Input
            placeholder="Search by biomarker name (e.g. glucose, cholesterol)..."
            leftIcon={<Search className="w-4 h-4" />}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/* Filter Pills with Counts */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1">
          {[
            { id: 'ALL', label: `All Types (${extractedBiomarkers.length})` },
            { id: 'Clinical', label: `🩺 Clinical (${clinCount})` },
            { id: 'Wearable', label: `⌚ Wearable (${wearCount})` },
            { id: 'Gut', label: `🧬 Gut Microbiome (${gutCount})` },
          ].map((mod) => (
            <button
              key={mod.id}
              onClick={() => setSelectedModality(mod.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold font-mono transition-all ${
                selectedModality === mod.id
                  ? 'bg-[var(--accent)] text-white shadow-sm'
                  : 'bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-[var(--text-muted)] hover:text-[var(--text-main)]'
              }`}
            >
              {mod.label}
            </button>
          ))}
        </div>
      </div>

      {/* Biomarkers Grid */}
      {extractedBiomarkers.length === 0 ? (
        <div className="p-8 text-center space-y-2 border border-dashed border-[var(--border-subtle)] rounded-xl">
          <Activity className="w-8 h-8 text-[var(--text-muted)] mx-auto" />
          <h4 className="text-sm font-bold text-[var(--text-main)]">No Health Measurements Found</h4>
          <p className="text-xs text-[var(--text-muted)]">
            Upload your medical lab report, wearable CSV, or gut microbiome profile in New Analysis to view extracted biometrics.
          </p>
        </div>
      ) : filteredBiomarkers.length === 0 ? (
        <div className="p-8 text-center space-y-2 border border-dashed border-[var(--border-subtle)] rounded-xl">
          <HelpCircle className="w-8 h-8 text-[var(--text-muted)] mx-auto" />
          <h4 className="text-sm font-bold text-[var(--text-main)]">
            {selectedModality === 'Wearable'
              ? 'No Wearable Telemetry Uploaded'
              : selectedModality === 'Gut'
              ? 'No Gut Microbiome Profile Uploaded'
              : 'No Matching Biomarkers Found'}
          </h4>
          <p className="text-xs text-[var(--text-muted)]">
            {selectedModality === 'Wearable'
              ? 'You did not upload wearable device telemetry for this assessment.'
              : selectedModality === 'Gut'
              ? 'You did not upload a 16S/Metagenomic gut report for this assessment.'
              : `No measurements match "${searchQuery}".`}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          {visibleBiomarkers.map((b) => (
            <div key={b.id} className="p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] space-y-2.5 hover:shadow-md transition-all hover:border-[var(--accent)]">
              <div className="flex justify-between items-start">
                <div>
                  <strong className="text-xs text-[var(--text-main)] font-extrabold block">{b.emoji} {b.name}</strong>
                  <span className="text-[10px] font-mono text-[var(--text-muted)]">{b.modality} • Target Range: {b.refRange}</span>
                </div>
                <Badge variant={b.statusVariant} size="sm">{b.status}</Badge>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono p-2.5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                <div>
                  <span className="text-[9px] text-[var(--text-muted)] block uppercase font-bold">Measured Value</span>
                  <strong className="text-[var(--text-main)] text-sm">{b.current} {b.unit}</strong>
                </div>
                <div>
                  <span className="text-[9px] text-[var(--text-muted)] block uppercase font-bold">Healthy Reference</span>
                  <span className="text-[var(--text-muted)]">{b.refRange}</span>
                </div>
              </div>

              {/* Expandable plain-language explanation */}
              <button
                onClick={() => setExpandedId(expandedId === b.id ? null : b.id)}
                className="text-[11px] font-semibold text-[var(--primary)] hover:underline flex items-center gap-1 pt-1"
              >
                {expandedId === b.id ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                {expandedId === b.id ? 'Hide clinical explanation' : 'What does this measurement mean?'}
              </button>

              {expandedId === b.id && (
                <div className="p-3 rounded-xl bg-blue-50 dark:bg-blue-900/15 text-[11px] text-[var(--text-muted)] leading-relaxed animate-fade-in border border-blue-100 dark:border-blue-800 space-y-1">
                  <p className="font-semibold text-blue-900 dark:text-blue-200">💡 Clinical Interpretation:</p>
                  <p>{b.interp}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Show More / Show Less Toggle */}
      {hasMore && (
        <div className="text-center pt-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAll(!showAll)}
            leftIcon={showAll ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          >
            {showAll ? `Show Less (Top 12)` : `Show All ${filteredBiomarkers.length} Measurements`}
          </Button>
        </div>
      )}
    </Card>
  );
}

function getUnit(key) {
  const k = key.toLowerCase();
  if (k.includes('glucose') || k.includes('triglyceride') || k.includes('hdl') || k.includes('ldl') || k.includes('cholesterol')) return 'mg/dL';
  if (k.includes('hba1c')) return '%';
  if (k.includes('bmi')) return 'kg/m²';
  if (k.includes('waist') || k.includes('circumference')) return 'cm';
  if (k.includes('pressure') || k.includes('systolic') || k.includes('diastolic')) return 'mmHg';
  if (k.includes('alt') || k.includes('ast')) return 'U/L';
  if (k.includes('heart') || k.includes('resting')) return 'bpm';
  if (k.includes('step')) return 'steps/day';
  if (k.includes('sleep') || k.includes('duration')) return 'hours';
  if (k.includes('hrv') || k.includes('sdnn') || k.includes('rmssd')) return 'ms';
  return '';
}

function getRefRange(key) {
  const k = key.toLowerCase();
  if (k.includes('glucose') || k.includes('fasting')) return '70-99 mg/dL';
  if (k.includes('hba1c')) return '4.0-5.6%';
  if (k.includes('bmi')) return '18.5-24.9';
  if (k.includes('systolic')) return '90-120 mmHg';
  if (k.includes('diastolic')) return '60-80 mmHg';
  if (k.includes('triglyceride')) return '<150 mg/dL';
  if (k.includes('hdl')) return '>40 mg/dL';
  if (k.includes('ldl')) return '<100 mg/dL';
  if (k.includes('alt')) return '7-35 U/L';
  if (k.includes('ast')) return '8-33 U/L';
  if (k.includes('resting') || k.includes('heart_rate')) return '60-100 bpm';
  if (k.includes('step')) return '7,500+ steps';
  if (k.includes('sleep')) return '7-9 hours';
  if (k.includes('akkermansia')) return '1-4%';
  if (k.includes('faecalibacterium')) return '5-15%';
  if (k.includes('shannon')) return '2.5-4.0';
  return 'Standard';
}

function getPlainInterpretation(key, value, modality) {
  const k = key.toLowerCase();
  const v = parseFloat(value);

  if (k.includes('glucose') || k.includes('fasting_blood')) {
    if (v >= 126) return `Your fasting blood sugar is ${value} mg/dL, which is above the normal range (70-99 mg/dL). This level falls in the diabetic range. Consult your doctor for a personalized management plan.`;
    if (v >= 100) return `Your fasting blood sugar is ${value} mg/dL, which is slightly elevated (normal is 70-99 mg/dL). This is in the prediabetes range. Light walking post-meal and reducing refined sugar can help bring this down.`;
    return `Your fasting blood sugar is ${value} mg/dL, which is within the healthy range (70-99 mg/dL). Your body is regulating blood sugar effectively.`;
  }
  if (k.includes('hba1c')) {
    if (v >= 6.5) return `Your HbA1c is ${value}%, which reflects average blood sugar over 2-3 months. A level above 6.5% indicates diabetes. Work with your doctor on glycemic targets.`;
    if (v >= 5.7) return `Your HbA1c is ${value}%, which is in the prediabetes range (5.7-6.4%). Dietary improvements and daily activity can help improve your glycemic control.`;
    return `Your HbA1c is ${value}%, which is normal (below 5.7%). This indicates excellent long-term blood sugar stability.`;
  }
  if (k.includes('bmi')) {
    if (v >= 30) return `Your BMI is ${value}, which falls in the obese category (30+). Modest weight loss of 5-10% significantly improves insulin sensitivity and cardiovascular health.`;
    if (v >= 25) return `Your BMI is ${value}, which is in the overweight range (25-29.9). Balanced nutrition and regular physical activity can support gradual weight optimization.`;
    return `Your BMI is ${value}, which is in the healthy range (18.5-24.9). Maintain your current lifestyle habits.`;
  }
  if (k.includes('step')) {
    if (v < 5000) return `You're averaging ${value} steps per day. Aim to gradually increase to 7,500+ steps to enhance glucose clearance and cardiovascular fitness.`;
    if (v < 7500) return `You're averaging ${value} steps per day. Increasing activity to 8,500-10,000 steps daily yields major metabolic benefits.`;
    return `Great job! You're averaging ${value} steps per day, which exceeds recommended activity baselines.`;
  }
  if (k.includes('akkermansia')) {
    return `Akkermansia muciniphila is a key gut bacterium (your level: ${value}%) that protects your gut lining and supports metabolic health. Healthy levels are 1-4%.`;
  }
  if (k.includes('faecalibacterium')) {
    return `Faecalibacterium prausnitzii (your level: ${value}%) produces butyrate, an anti-inflammatory short-chain fatty acid that nourishes the colon lining. Healthy range is 5-15%.`;
  }
  if (modality === 'gut') {
    return `This gut microorganism (abundance: ${value}%) plays an active role in gut barrier integrity, inflammation, and metabolic regulation.`;
  }
  if (modality === 'wearable') {
    return `This telemetry metric (${value}) comes from your wearable sensor, tracking real-time physical strain, recovery, or cardiovascular function.`;
  }
  return `This health measurement (${key.replace(/_/g, ' ')}: ${value}) was extracted from your uploaded medical report and used in computing your ensemble risk predictions.`;
}
