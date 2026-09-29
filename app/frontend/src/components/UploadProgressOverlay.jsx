import React, { useState, useEffect, useMemo } from 'react';
import {
  CheckCircle2, Loader2, FileText, Layers, Activity, ShieldCheck,
  Database, Sparkles, AlertCircle
} from 'lucide-react';

/**
 * UploadProgressOverlay — Progressive Processing Feedback
 * 
 * Shows an animated step-by-step checklist during document upload and OCR processing.
 * Driven by the `uploadStage` prop from IntakePage.
 */

const UPLOAD_STAGES = [
  { key: 'uploading', title: 'Uploading Documents', desc: 'Transferring PDF, CSV, and image files to the secure processing server...', icon: FileText },
  { key: 'detecting', title: 'Template Detection', desc: 'Identifying lab report templates (Apollo, Max, Thyrocare, Ayumetrix)...', icon: Layers },
  { key: 'extracting', title: 'OCR Text Extraction', desc: 'Running Tesseract hybrid OCR engine to extract structured text from documents...', icon: Activity },
  { key: 'normalizing', title: 'Canonical Feature Mapping', desc: 'Disambiguating aliases and mapping extracted fields to the V4 canonical schema...', icon: Database },
  { key: 'validating', title: 'Physiological Validation', desc: 'Applying clinical boundary checks and detecting impossible value outliers...', icon: ShieldCheck },
  { key: 'dq', title: 'Data Quality Scoring', desc: 'Computing multi-factor quality confidence scores across all extracted features...', icon: Sparkles },
];

export default function UploadProgressOverlay({ uploadStage, isVisible }) {
  const [completedStages, setCompletedStages] = useState(new Set());
  const [fadeOut, setFadeOut] = useState(false);

  const currentStageIdx = useMemo(() => {
    if (!uploadStage) return -1;
    if (uploadStage === 'ready') return UPLOAD_STAGES.length;
    return UPLOAD_STAGES.findIndex(s => s.key === uploadStage);
  }, [uploadStage]);

  // Track completed stages
  useEffect(() => {
    if (currentStageIdx > 0) {
      setCompletedStages(prev => {
        const next = new Set(prev);
        for (let i = 0; i < currentStageIdx; i++) {
          next.add(UPLOAD_STAGES[i].key);
        }
        return next;
      });
    }
  }, [currentStageIdx]);

  // Handle completion fade-out
  useEffect(() => {
    if (uploadStage === 'ready') {
      setCompletedStages(new Set(UPLOAD_STAGES.map(s => s.key)));
      const timer = setTimeout(() => setFadeOut(true), 800);
      return () => clearTimeout(timer);
    } else {
      setFadeOut(false);
    }
  }, [uploadStage]);

  // Reset on new upload
  useEffect(() => {
    if (uploadStage === 'uploading') {
      setCompletedStages(new Set());
      setFadeOut(false);
    }
  }, [uploadStage]);

  if (!isVisible || fadeOut) return null;

  const progressPct = Math.round(((completedStages.size + (currentStageIdx >= 0 ? 0.5 : 0)) / UPLOAD_STAGES.length) * 100);

  return (
    <div className="fixed inset-0 z-[9998] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" />

      {/* Card */}
      <div className="relative w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden animate-fade-in">
        {/* Header */}
        <div className="px-6 py-5 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-100 border border-blue-200 flex items-center justify-center">
              <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
            </div>
            <div>
              <h2 className="text-base font-extrabold text-gray-900">Processing Your Reports</h2>
              <p className="text-[11px] text-gray-500 mt-0.5">
                Extracting and validating health data from uploaded documents
              </p>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mt-4 flex items-center gap-3">
            <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-700 ease-out"
                style={{ width: `${progressPct}%` }}
              />
            </div>
            <span className="text-xs font-bold text-gray-600 tabular-nums">{Math.min(progressPct, 100)}%</span>
          </div>
        </div>

        {/* Stage Checklist */}
        <div className="px-6 py-4 space-y-1">
          {UPLOAD_STAGES.map((stage, idx) => {
            const isCompleted = completedStages.has(stage.key);
            const isCurrent = currentStageIdx === idx;
            const isPending = !isCompleted && !isCurrent;
            const Icon = stage.icon;

            return (
              <div
                key={stage.key}
                className={`flex items-start gap-3 px-3 py-2.5 rounded-xl transition-all duration-300 ${
                  isCurrent ? 'bg-blue-50 border border-blue-100' :
                  isCompleted ? 'bg-emerald-50/40' :
                  'opacity-40'
                }`}
              >
                {/* Status Icon */}
                <div className="mt-0.5 shrink-0">
                  {isCompleted ? (
                    <div className="w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center">
                      <CheckCircle2 className="w-4 h-4 text-white" />
                    </div>
                  ) : isCurrent ? (
                    <div className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center">
                      <Loader2 className="w-3.5 h-3.5 text-white animate-spin" />
                    </div>
                  ) : (
                    <div className="w-6 h-6 rounded-full border-2 border-gray-300 flex items-center justify-center">
                      <div className="w-2 h-2 rounded-full bg-gray-300" />
                    </div>
                  )}
                </div>

                {/* Text */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <Icon className={`w-4 h-4 shrink-0 ${
                      isCompleted ? 'text-emerald-600' : isCurrent ? 'text-blue-600' : 'text-gray-400'
                    }`} />
                    <span className={`text-xs font-bold ${
                      isCompleted ? 'text-emerald-700' : isCurrent ? 'text-blue-700' : 'text-gray-500'
                    }`}>
                      {stage.title}
                    </span>
                    {isCompleted && (
                      <span className="text-[9px] font-mono text-emerald-500 bg-emerald-50 px-1.5 py-0.5 rounded">Done</span>
                    )}
                    {isCurrent && (
                      <span className="text-[9px] font-mono text-blue-500 bg-blue-50 px-1.5 py-0.5 rounded animate-pulse">Running...</span>
                    )}
                  </div>
                  {(isCurrent || isCompleted) && (
                    <p className={`text-[10px] mt-0.5 ml-6 ${isCompleted ? 'text-gray-400' : 'text-gray-500'}`}>
                      {stage.desc}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer Tip */}
        <div className="px-6 py-3 border-t border-gray-100 bg-gray-50 flex items-center gap-2">
          <AlertCircle className="w-3.5 h-3.5 text-gray-400 shrink-0" />
          <span className="text-[10px] text-gray-500">
            Processing time depends on document complexity. OCR on scanned PDFs may take slightly longer.
          </span>
        </div>
      </div>
    </div>
  );
}
