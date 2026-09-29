import React, { useState, useMemo } from 'react';
import {
  AlertTriangle, CheckCircle2, X, Activity, Watch, Dna,
  ShieldAlert, ArrowRight, Info, AlertCircle
} from 'lucide-react';
import { Button, Badge } from './ui';
import { CLIENT_PHYSIOLOGICAL_BOUNDS, validateClientField } from '../utils/intakeValidation';

/**
 * MissingFeatureModal — Human-in-the-Loop Data Validation
 * 
 * Intercepts the "Run Analysis" action when fields are missing.
 * Shows plausibility ranges and validation guards per missing field.
 * Allows the user to manually input values or accept population medians.
 */

const MODALITY_CONFIG = {
  clinical: { label: 'Clinical', icon: Activity, color: 'red', bgClass: 'bg-red-50', textClass: 'text-red-600', borderClass: 'border-red-200' },
  wearable: { label: 'Wearable', icon: Watch, color: 'blue', bgClass: 'bg-blue-50', textClass: 'text-blue-600', borderClass: 'border-blue-200' },
  gut: { label: 'Gut Microbiome', icon: Dna, color: 'green', bgClass: 'bg-green-50', textClass: 'text-green-600', borderClass: 'border-green-200' },
};

// Critical features that STRONGLY impact prediction accuracy when missing
const CRITICAL_FEATURES = new Set([
  'HbA1c', 'Fasting_Blood_Glucose', 'BMI', 'Systolic_BP', 'Diastolic_BP',
  'Triglycerides', 'HDL', 'Waist_Circumference',
  'CGM_Average_Glucose', 'CGM_Time_In_Range',
  'Resting_Heart_Rate', 'Sleep_Duration_Hours',
]);

function humanizeFeatureName(name) {
  return name
    .replace(/_/g, ' ')
    .replace(/CGM /g, 'CGM ')
    .replace(/BP/g, 'Blood Pressure')
    .replace(/HbA1c/g, 'HbA1c')
    .replace(/HDL/g, 'HDL Cholesterol')
    .replace(/LDL/g, 'LDL Cholesterol')
    .replace(/ALT/g, 'ALT (Liver)')
    .replace(/AST/g, 'AST (Liver)')
    .replace(/RMSSD/g, '(RMSSD)');
}

export default function MissingFeatureModal({
  isOpen,
  onClose,
  missingFields, // { clinical: ['HbA1c', ...], wearable: [...], gut: [...] }
  allFeatures,   // { clinical: [...all], wearable: [...all], gut: [...all] }
  onConfirm,     // (resolvedValues: { feature: value }) => void
  onSkipAll,     // () => void — proceed with median imputation for all
}) {
  const [resolvedValues, setResolvedValues] = useState({});
  const [validationErrors, setValidationErrors] = useState({});
  const [expandedModality, setExpandedModality] = useState(null);

  const totalMissing = useMemo(() => {
    let count = 0;
    Object.values(missingFields || {}).forEach(arr => { count += (arr || []).length; });
    return count;
  }, [missingFields]);

  const totalFeatures = useMemo(() => {
    let count = 0;
    Object.values(allFeatures || {}).forEach(arr => { count += (arr || []).length; });
    return count;
  }, [allFeatures]);

  const totalSupplied = totalFeatures - totalMissing;
  const criticalMissing = useMemo(() => {
    const list = [];
    Object.values(missingFields || {}).forEach(arr => {
      (arr || []).forEach(f => { if (CRITICAL_FEATURES.has(f)) list.push(f); });
    });
    return list;
  }, [missingFields]);

  const resolvedCount = Object.keys(resolvedValues).filter(k => {
    const v = resolvedValues[k];
    return v !== '' && v !== null && v !== undefined && !validationErrors[k];
  }).length;

  const handleValueChange = (feature, value) => {
    setResolvedValues(prev => ({ ...prev, [feature]: value }));
    if (value === '' || value === null || value === undefined) {
      setValidationErrors(prev => { const n = { ...prev }; delete n[feature]; return n; });
      return;
    }
    const err = validateClientField(feature, value);
    if (err) {
      setValidationErrors(prev => ({ ...prev, [feature]: err }));
    } else {
      setValidationErrors(prev => { const n = { ...prev }; delete n[feature]; return n; });
    }
  };

  const handleUseMedian = (feature) => {
    const bounds = CLIENT_PHYSIOLOGICAL_BOUNDS[feature];
    if (bounds) {
      const median = parseFloat(((bounds.min + bounds.max) / 2).toFixed(1));
      setResolvedValues(prev => ({ ...prev, [feature]: median }));
      setValidationErrors(prev => { const n = { ...prev }; delete n[feature]; return n; });
    }
  };

  const handleConfirm = () => {
    const hasErrors = Object.keys(validationErrors).length > 0;
    if (hasErrors) return;
    onConfirm(resolvedValues);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative w-full max-w-2xl max-h-[85vh] bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden flex flex-col animate-fade-in">
        
        {/* Header */}
        <div className="px-6 py-5 border-b border-gray-100 bg-gradient-to-r from-amber-50 to-orange-50">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-amber-100 border border-amber-200 flex items-center justify-center">
                <ShieldAlert className="w-6 h-6 text-amber-600" />
              </div>
              <div>
                <h2 className="text-lg font-extrabold text-gray-900">Missing Feature Validation</h2>
                <p className="text-xs text-gray-500 mt-0.5">
                  {totalMissing} of {totalFeatures} features are missing across active modalities
                </p>
              </div>
            </div>
            <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors">
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>

          {/* Summary Bar */}
          <div className="mt-4 flex items-center gap-4">
            <div className="flex-1">
              <div className="h-2.5 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500 bg-gradient-to-r from-emerald-400 to-emerald-500"
                  style={{ width: `${Math.round(((totalSupplied + resolvedCount) / totalFeatures) * 100)}%` }}
                />
              </div>
            </div>
            <span className="text-xs font-bold text-gray-700 tabular-nums whitespace-nowrap">
              {totalSupplied + resolvedCount} / {totalFeatures} resolved
            </span>
          </div>

          {/* Critical Warning */}
          {criticalMissing.length > 0 && (
            <div className="mt-3 flex items-start gap-2 p-3 rounded-xl bg-red-50 border border-red-200">
              <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
              <div>
                <span className="text-xs font-bold text-red-700">Critical Features Missing: </span>
                <span className="text-xs text-red-600">
                  {criticalMissing.map(f => humanizeFeatureName(f)).join(', ')}. 
                  These heavily influence prediction accuracy.
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Body — scrollable */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 custom-scrollbar">
          {Object.entries(missingFields || {}).map(([modality, fields]) => {
            if (!fields || fields.length === 0) return null;
            const config = MODALITY_CONFIG[modality];
            if (!config) return null;
            const Icon = config.icon;
            const modTotal = (allFeatures?.[modality] || []).length;
            const modSupplied = modTotal - fields.length;
            const isExpanded = expandedModality === modality || Object.keys(missingFields).length <= 2;

            return (
              <div key={modality} className={`rounded-xl border ${config.borderClass} overflow-hidden`}>
                {/* Modality Header */}
                <button
                  className={`w-full flex items-center justify-between px-4 py-3 ${config.bgClass} hover:brightness-95 transition-all`}
                  onClick={() => setExpandedModality(expandedModality === modality ? null : modality)}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-5 h-5 ${config.textClass}`} />
                    <span className={`text-sm font-bold ${config.textClass}`}>{config.label}</span>
                    <Badge variant="warning" size="sm">{fields.length} missing</Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500 font-mono">{modSupplied}/{modTotal} extracted</span>
                    <span className="text-gray-400">{isExpanded ? '▲' : '▼'}</span>
                  </div>
                </button>

                {/* Feature Rows */}
                {isExpanded && (
                  <div className="divide-y divide-gray-100">
                    {fields.map((feature) => {
                      const bounds = CLIENT_PHYSIOLOGICAL_BOUNDS[feature];
                      const currentVal = resolvedValues[feature];
                      const error = validationErrors[feature];
                      const isCritical = CRITICAL_FEATURES.has(feature);
                      const isResolved = currentVal !== undefined && currentVal !== '' && !error;

                      return (
                        <div key={feature} className={`px-4 py-3 flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 ${isResolved ? 'bg-green-50/40' : ''}`}>
                          {/* Feature Name */}
                          <div className="flex items-center gap-2 sm:w-[200px] shrink-0">
                            {isResolved ? (
                              <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                            ) : (
                              <AlertTriangle className={`w-4 h-4 shrink-0 ${isCritical ? 'text-red-500' : 'text-amber-400'}`} />
                            )}
                            <div>
                              <span className="text-xs font-bold text-gray-800">{humanizeFeatureName(feature)}</span>
                              {isCritical && <Badge variant="danger" size="sm" className="ml-1.5 !text-[9px] !px-1.5">Critical</Badge>}
                            </div>
                          </div>

                          {/* Input + Bounds */}
                          <div className="flex-1 flex items-center gap-2">
                            <div className="flex-1 relative">
                              <input
                                type="number"
                                step="any"
                                placeholder={bounds ? `${bounds.min} – ${bounds.max}` : 'Enter value'}
                                value={currentVal ?? ''}
                                onChange={(e) => handleValueChange(feature, e.target.value)}
                                className={`w-full h-9 px-3 text-xs font-mono rounded-lg border transition-colors focus:outline-none focus:ring-2 ${
                                  error
                                    ? 'border-red-300 focus:ring-red-200 bg-red-50'
                                    : isResolved
                                    ? 'border-emerald-300 focus:ring-emerald-200 bg-emerald-50'
                                    : 'border-gray-200 focus:ring-blue-200 bg-white'
                                }`}
                              />
                              {bounds && (
                                <span className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[10px] text-gray-400 font-mono pointer-events-none">
                                  {bounds.unit}
                                </span>
                              )}
                            </div>

                            {/* Use Median Button */}
                            {bounds && (
                              <button
                                onClick={() => handleUseMedian(feature)}
                                className="shrink-0 px-2.5 py-1.5 text-[10px] font-bold text-amber-700 bg-amber-50 border border-amber-200 rounded-lg hover:bg-amber-100 transition-colors whitespace-nowrap"
                                title={`Use population median: ${((bounds.min + bounds.max) / 2).toFixed(1)}`}
                              >
                                Use Median
                              </button>
                            )}
                          </div>

                          {/* Validation Error */}
                          {error && (
                            <span className="text-[10px] text-red-500 font-bold sm:w-[140px] shrink-0">{error}</span>
                          )}
                          {/* Plausibility Range */}
                          {bounds && !error && (
                            <span className="text-[10px] text-gray-400 font-mono sm:w-[140px] shrink-0">
                              Range: {bounds.min}–{bounds.max} {bounds.unit}
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-100 bg-gray-50 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Info className="w-4 h-4 text-gray-400" />
            <span className="text-[10px] text-gray-500">
              Missing features will use population median values if not provided.
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              className="text-amber-600 hover:bg-amber-50"
              onClick={onSkipAll}
            >
              Skip All (Use Defaults)
            </Button>
            <Button
              variant="primary"
              size="sm"
              leftIcon={<ArrowRight className="w-4 h-4" />}
              onClick={handleConfirm}
              disabled={Object.keys(validationErrors).length > 0}
            >
              Confirm & Run Analysis
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
