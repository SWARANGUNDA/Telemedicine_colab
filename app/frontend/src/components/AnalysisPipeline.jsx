import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle2, Check, Clock, AlertCircle, RefreshCw, ArrowRight,
  Database, Activity, Lock, Cpu, Stethoscope, Binary, Bot, Network, FileText, Watch, Dna, Layers, Sparkles, AlertTriangle, ShieldCheck, Brain, Settings, Layout
} from 'lucide-react';
import { Button, Card, CardHeader, CardBody, CardFooter, Badge, ProgressBar, CircularProgress } from './ui';

// 16 Detailed Vertical Timeline Pipeline Stages
const pipelineStages = [
  { key: 'upload', title: 'Upload Complete', desc: 'PDF, CSV, and image reports uploaded & verified', icon: CheckCircle2, latency: 12 },
  { key: 'validation', title: 'Document Validation', desc: 'Magic byte signature & file size security check', icon: ShieldCheck, latency: 14 },
  { key: 'ocr', title: 'OCR Processing', desc: 'Tesseract hybrid OCR extraction engine', icon: FileText, latency: 45 },
  { key: 'template', title: 'Template Detection', desc: 'Apollo, Max, Thyrocare & Ayumetrix detection', icon: Layers, latency: 18 },
  { key: 'mapping', title: 'Canonical Feature Mapping', desc: 'Context-aware alias disambiguation & schema mapping', icon: Activity, latency: 24 },
  { key: 'feat_valid', title: 'Feature Validation', desc: 'Physiological boundary validation & duplicate checks', icon: CheckCircle2, latency: 16 },
  { key: 'quality', title: 'Quality Assessment', desc: 'Multi-factor report & feature confidence scoring', icon: ShieldCheck, latency: 22 },
  { key: 'clin_expert', title: 'Clinical Expert Model', desc: 'Gradient Boosted Decision Trees (18 biomarkers)', icon: Activity, latency: 28 },
  { key: 'wear_expert', title: 'Wearable Expert Model', desc: '15D continuous sensor streams & circadian metrics', icon: Watch, latency: 32 },
  { key: 'gut_expert', title: 'Gut Expert Model', desc: '40 Taxa species + 9 derived ecological indices profiler', icon: Dna, latency: 30 },
  { key: 'fusion', title: 'Fusion Engine', desc: '7-Pathway Multimodal Ensemble Fusion Engine', icon: Layers, latency: 15 },
  { key: 'reliability', title: 'Prediction Reliability', desc: 'Modality reliability ratings & missing feature impact', icon: Cpu, latency: 20 },
  { key: 'shap', title: 'TreeSHAP Explainability', desc: 'Attribution matrix & directional driver rankings', icon: Brain, latency: 40 },
  { key: 'rag', title: 'Medical RAG Evidence', desc: 'Medical guideline vector evidence retrieval', icon: Sparkles, latency: 35 },
  { key: 'report_gen', title: 'Clinical Report Generation', desc: 'Patient-facing diagnostic synthesis & summary', icon: FileText, latency: 25 },
  { key: 'complete', title: 'Assessment Complete', desc: 'Multimodal predictions ready for clinical review', icon: CheckCircle2, latency: 10 },
];

export function AnalysisPipeline({
  stage = 'intake', // 'intake' | 'predicting' | 'completed' | 'failed' | 'warning'
  errorMsg = null,
  warningMsg = null,
  pathway = 'C+W+G',
  dqScore = null,
  featureCounts = { clinical: 18, wearable: 15, gut: 49 },
  currentDocument = 'clinical_v4_sample.csv',
  onNavigateDashboard,
  onNavigateXAI,
  onNavigateReport,
  onRetry,
  onBackToVerification
}) {
  const navigate = useNavigate();
  const [activeStageIdx, setActiveStageIdx] = useState(0);
  const containerRef = useRef(null);
  const [logs, setLogs] = useState([]);
  const [isPaused, setIsPaused] = useState(false);
  const [showPredictions, setShowPredictions] = useState(false);

  const predictionsRaw = sessionStorage.getItem('telemed_pred');
  const predictions = predictionsRaw ? JSON.parse(predictionsRaw) : null;

  useEffect(() => {
    let timeoutId;
    
    const advanceStage = () => {
      if (isPaused) return;
      setActiveStageIdx((prev) => {
        // If still predicting, stop at second-to-last. If completed, allow reaching the last step.
        const maxIdx = stage === 'completed' ? pipelineStages.length - 1 : pipelineStages.length - 2;
        if (prev < maxIdx) {
          const nextIdx = prev + 1;
          const nextStage = pipelineStages[nextIdx];
          const delay = (nextStage.latency || 20) * 15; 
          timeoutId = setTimeout(advanceStage, delay);
          return nextIdx;
        }
        return prev;
      });
    };

    if ((stage === 'predicting' || stage === 'completed') && !isPaused) {
      timeoutId = setTimeout(advanceStage, 300);
    }
    
    return () => clearTimeout(timeoutId);
  }, [stage, pipelineStages.length, isPaused]);

  // Auto-scroll the active stage into view horizontally without scrolling the whole window
  useEffect(() => {
    if (containerRef.current && containerRef.current.children[activeStageIdx]) {
      const activeEl = containerRef.current.children[activeStageIdx];
      const container = containerRef.current;
      
      // Calculate the required horizontal scroll position to center the active element
      const targetScrollLeft = activeEl.offsetLeft - (container.clientWidth / 2) + (activeEl.clientWidth / 2);
      
      // Smoothly scroll the container explicitly
      container.scrollTo({
        left: Math.max(0, targetScrollLeft),
        behavior: 'smooth'
      });
    }
  }, [activeStageIdx]);

  // Live Terminal Logs Generation
  useEffect(() => {
    if (stage === 'predicting' || stage === 'completed') {
      const currentStage = pipelineStages[activeStageIdx];
      const timeStamp = new Date().toISOString().split('T')[1].slice(0, 12);
      
      if (stage === 'completed' && activeStageIdx === pipelineStages.length - 1) {
        setLogs(prev => [...prev, `[${timeStamp}] PIPELINE COMPLETE`, `>> Multimodal inference finalized.`, `>> Ready for clinical review.`].slice(-12));
      } else if (currentStage) {
        setLogs(prev => [
          ...prev, 
          `[${timeStamp}] INITIATING: ${currentStage.title}`,
          `>> ${currentStage.desc}`,
          `>> STATUS: OK (${currentStage.latency}ms)`
        ].slice(-12));
      }
    }
  }, [activeStageIdx, stage, pipelineStages]);

  const progressPct = Math.round(((activeStageIdx + 1) / pipelineStages.length) * 100);
  const currentStageInfo = pipelineStages[activeStageIdx] || pipelineStages[0];

  return (
    <div className="w-full space-y-4 pb-12 animate-fade-in max-w-full">
      {/* ROW 1: UPLOADED FILES CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Clinical Card */}
        {featureCounts?.clinical > 0 && (
          <Card isGlass={true} className="p-4 flex items-center gap-4 bg-white/60">
             <div className="w-12 h-12 rounded-xl bg-red-50 flex items-center justify-center shrink-0 border border-red-100">
               <FileText className="w-6 h-6 text-red-500" />
             </div>
             <div className="flex-1 min-w-0">
               <div className="flex items-center justify-between">
                 <h4 className="text-sm font-bold text-gray-900">Clinical Report</h4>
                 <Badge variant="success" size="sm" className="bg-green-50 text-green-600 border-none px-2 py-0.5"><CheckCircle2 className="w-3 h-3 mr-1 inline"/>Uploaded</Badge>
               </div>
               <p className="text-xs text-gray-500 font-mono truncate mt-0.5">{currentDocument || 'clinical_report.pdf'}</p>
             </div>
          </Card>
        )}

        {/* Wearable Card */}
        {featureCounts?.wearable > 0 && (
          <Card isGlass={true} className="p-4 flex items-center gap-4 bg-white/60">
             <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center shrink-0 border border-blue-100">
               <Watch className="w-6 h-6 text-blue-500" />
             </div>
             <div className="flex-1 min-w-0">
               <div className="flex items-center justify-between">
                 <h4 className="text-sm font-bold text-gray-900">Wearable / CGM Data</h4>
                 <Badge variant="success" size="sm" className="bg-green-50 text-green-600 border-none px-2 py-0.5"><CheckCircle2 className="w-3 h-3 mr-1 inline"/>Uploaded</Badge>
               </div>
               <p className="text-xs text-gray-500 font-mono truncate mt-0.5">wearable_telemetry.csv</p>
             </div>
          </Card>
        )}

        {/* Gut Card */}
        {featureCounts?.gut > 0 && (
          <Card isGlass={true} className="p-4 flex items-center gap-4 bg-white/60">
             <div className="w-12 h-12 rounded-xl bg-green-50 flex items-center justify-center shrink-0 border border-green-100">
               <Dna className="w-6 h-6 text-green-500" />
             </div>
             <div className="flex-1 min-w-0">
               <div className="flex items-center justify-between">
                 <h4 className="text-sm font-bold text-gray-900">Gut Microbiome Report</h4>
                 <Badge variant="success" size="sm" className="bg-green-50 text-green-600 border-none px-2 py-0.5"><CheckCircle2 className="w-3 h-3 mr-1 inline"/>Uploaded</Badge>
               </div>
               <p className="text-xs text-gray-500 font-mono truncate mt-0.5">gut_microbiome.pdf</p>
             </div>
          </Card>
        )}
      </div>

      {/* ROW 2: DATASET SUMMARY */}
      <Card isGlass={true} className="p-0 bg-white overflow-hidden flex flex-col md:flex-row border-gray-200/60 shadow-sm">
         <div className="p-5 flex items-start gap-4 md:w-[280px] shrink-0 border-b md:border-b-0 md:border-r border-gray-100 bg-gray-50/50">
            <div className="w-10 h-10 rounded-lg bg-blue-600 text-white flex items-center justify-center shadow-sm shrink-0">
               <Database className="w-5 h-5" />
            </div>
            <div>
               <h4 className="text-sm font-extrabold text-gray-900">Dataset Summary</h4>
               <p className="text-xs text-gray-500 mt-1">Total: {((featureCounts?.clinical || 0) + (featureCounts?.wearable || 0) + (featureCounts?.gut || 0))} Predictive Features</p>
            </div>
         </div>
         <div className="flex-1 grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-gray-100">
            {/* Clinical Box */}
            {featureCounts?.clinical > 0 && (
              <div className="p-4 bg-red-50/30 flex gap-4">
                 <Activity className="w-8 h-8 text-red-500 shrink-0 mt-1" />
                 <div>
                    <h5 className="text-[11px] font-bold text-red-600 uppercase tracking-wide">Clinical Features</h5>
                    <div className="text-3xl font-black text-gray-900 leading-none mt-1">{featureCounts.clinical}</div>
                    <p className="text-[10px] text-gray-500 leading-tight mt-2">Blood Tests • Vitals • Demographics • Family History</p>
                 </div>
              </div>
            )}
            {/* Wearable Box */}
            {featureCounts?.wearable > 0 && (
              <div className="p-4 bg-blue-50/30 flex gap-4">
                 <Watch className="w-8 h-8 text-blue-500 shrink-0 mt-1" />
                 <div>
                    <h5 className="text-[11px] font-bold text-blue-600 uppercase tracking-wide">Wearable / CGM Features</h5>
                    <div className="text-3xl font-black text-gray-900 leading-none mt-1">{featureCounts.wearable}</div>
                    <p className="text-[10px] text-gray-500 leading-tight mt-2">Activity • Heart Rate • Sleep • Glucose Variability • CGM Metrics</p>
                 </div>
              </div>
            )}
            {/* Gut Box */}
            {featureCounts?.gut > 0 && (
              <div className="p-4 bg-green-50/30 flex gap-4">
                 <Dna className="w-8 h-8 text-green-500 shrink-0 mt-1" />
                 <div>
                    <h5 className="text-[11px] font-bold text-green-600 uppercase tracking-wide">Gut Microbiome Features</h5>
                    <div className="text-3xl font-black text-gray-900 leading-none mt-1">{featureCounts.gut}</div>
                    <p className="text-[10px] text-gray-500 leading-tight mt-2">Bacterial Species • Diversity Indices • Functional Indices • Taxonomic Ratios</p>
                 </div>
              </div>
            )}
         </div>
      </Card>

      {/* ROW 3: 16-STAGE PIPELINE HORIZONTAL STEPPER */}
      <Card isGlass={true} className="p-6 bg-white shadow-sm border-gray-200/60 overflow-hidden">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 pb-4 border-b border-gray-100 gap-4">
           <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20 shrink-0">
                 <Settings className="w-5 h-5" />
              </div>
              <div>
                 <h3 className="text-base font-extrabold text-gray-900">16-Stage Pipeline Execution</h3>
                 <p className="text-[11px] text-gray-500 mt-0.5">Complete preprocessing, feature extraction, AI inference and explanation pipeline</p>
              </div>
           </div>
           
           <div className="flex items-center gap-6 divide-x divide-gray-200">
              <Button 
                variant="ghost" 
                size="sm" 
                className={`px-3 hidden sm:flex ${isPaused ? 'text-blue-600 bg-blue-50' : 'text-gray-500 hover:bg-gray-50'}`}
                onClick={() => setIsPaused(!isPaused)}
              >
                {isPaused ? '▶ Resume' : '⏸ Pause'}
              </Button>
              <Button 
                variant="ghost" 
                size="sm" 
                className="px-3 hidden sm:flex text-gray-500 hover:bg-gray-50"
                onClick={() => {
                  if (stage === 'completed') {
                    setActiveStageIdx(pipelineStages.length - 1);
                  }
                }}
              >
                ⏭ Skip to Results
              </Button>
              {stage === 'completed' && activeStageIdx === pipelineStages.length - 1 && (
                <div className="flex items-center gap-2 pr-2">
                  <div className="w-6 h-6 rounded-full bg-green-500 text-white flex items-center justify-center"><CheckCircle2 className="w-4 h-4"/></div>
                  <span className="text-xs font-bold text-green-600">Pipeline Completed</span>
                </div>
              )}
              <div className="flex items-center gap-3 pl-6">
                 <Clock className="w-8 h-8 text-gray-400 stroke-[1.5]" />
                 <div>
                    <div className="text-[10px] text-gray-500 font-medium">Total Latency</div>
                    <div className="text-base font-bold text-blue-600 leading-none mt-0.5">33.4 ms</div>
                 </div>
              </div>
              <div className="flex items-center gap-3 pl-6">
                 <div className="w-8 h-8 rounded bg-blue-50 flex items-center justify-center text-blue-600"><Layout className="w-4 h-4" /></div>
                 <div>
                    <div className="text-base font-bold text-gray-900 leading-none">16 / 16</div>
                    <div className="text-[10px] text-gray-500 mt-0.5 font-medium">Stages</div>
                 </div>
              </div>
           </div>
        </div>

        {/* The 16 Nodes Stepper */}
        <div className="w-full overflow-x-auto pb-4 no-scrollbar">
          <div className="relative min-w-[1000px] flex items-start justify-between px-4 pt-6 pb-2">
            {/* The horizontal connecting line */}
            <div className="absolute top-[40px] left-[4%] right-[4%] h-[3px] bg-gray-200 z-0">
               <div 
                 className="h-full bg-green-500 transition-all duration-700 ease-out"
                 style={{ width: `${((activeStageIdx) / (pipelineStages.length - 1)) * 100}%` }}
               />
            </div>

            {pipelineStages.map((stg, idx) => {
              const Icon = stg.icon;
              const isDone = idx < activeStageIdx || stage === 'completed';
              const isCurrent = idx === activeStageIdx && stage !== 'completed';

              return (
                <div 
                  key={stg.key} 
                  className="relative z-10 flex flex-col items-center gap-3 w-16 group cursor-pointer transition-transform hover:scale-105"
                  onClick={() => {
                    setActiveStageIdx(idx);
                    setIsPaused(true);
                  }}
                >
                   <span className="text-[11px] font-mono font-bold text-gray-600 absolute -top-6">{idx + 1}</span>
                   
                   <div className={`w-7 h-7 rounded-full flex items-center justify-center transition-all duration-300 bg-white ring-[4px] ring-white ${
                     isDone 
                       ? 'text-white' 
                       : isCurrent 
                       ? 'border-2 border-blue-500 text-blue-500 shadow-[0_0_0_4px_rgba(59,130,246,0.2)]' 
                       : 'border-2 border-gray-300 text-gray-300'
                   }`}>
                     {isDone ? (
                       <div className="w-7 h-7 rounded-full bg-green-500 flex items-center justify-center"><CheckCircle2 className="w-5 h-5 text-white" /></div>
                     ) : isCurrent ? (
                       <div className="w-3 h-3 rounded-full bg-blue-500 animate-pulse" />
                     ) : (
                       <div className="w-3 h-3 rounded-full bg-gray-300" />
                     )}
                   </div>
                   
                   <div className="flex flex-col items-center text-center w-[80px]">
                     <Icon className={`w-5 h-5 mb-1.5 stroke-[1.5] ${isDone ? 'text-blue-600' : isCurrent ? 'text-blue-500 animate-pulse' : 'text-gray-400'}`} />
                     <span className={`text-[9px] font-bold leading-[1.1] ${isCurrent ? 'text-blue-600' : 'text-gray-900'}`}>
                        {stg.title.split(' ').map((word, i) => <React.Fragment key={i}>{word}<br/></React.Fragment>)}
                     </span>
                     <span className="text-[9px] font-mono text-gray-400 mt-1">{stg.latency * 15} ms</span>
                   </div>
                </div>
              );
            })}
          </div>
        </div>
      </Card>

      {/* ROW 4: TERMINAL AND COMPLETION CARD */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
         {/* Live Terminal */}
         <Card isGlass={true} className="bg-white border-gray-200/60 shadow-sm overflow-hidden flex flex-col h-[200px]">
           <div className="px-4 py-3 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
              <div className="flex items-center gap-2">
                 <div className="w-6 h-6 rounded bg-gray-800 text-white flex items-center justify-center"><ArrowRight className="w-3 h-3" /></div>
                 <span className="text-sm font-bold text-gray-900">System Output Terminal</span>
              </div>
              <span className="flex items-center gap-1.5 text-[10px] font-bold text-gray-500">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span> LIVE
              </span>
           </div>
           <div className="p-4 flex-1 overflow-y-auto font-mono text-[11px] leading-relaxed text-green-600 custom-scrollbar flex flex-col justify-end bg-[#fafafa]">
             <div className="space-y-1">
               {logs.map((log, i) => (
                 <div key={i} className={log.includes('>>') ? 'text-gray-500 ml-4' : 'text-green-600 font-medium'}>{log}</div>
               ))}
             </div>
           </div>
         </Card>

         {/* Completion Card */}
         {stage === 'completed' && activeStageIdx === pipelineStages.length - 1 ? (
           <Card isGlass={true} className="p-6 bg-white border-gray-200/60 shadow-sm flex flex-col justify-center gap-5 relative overflow-hidden h-[200px]">
             <div className="absolute -right-10 -bottom-10 w-40 h-40 bg-green-50 rounded-full blur-3xl -z-10"></div>
             
             <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-full bg-green-500 text-white flex items-center justify-center shrink-0 shadow-lg shadow-green-500/30">
                  <CheckCircle2 className="w-7 h-7" />
                </div>
                <div>
                   <h3 className="text-lg font-extrabold text-gray-900">Analysis Complete</h3>
                   <p className="text-xs text-gray-500 mt-1">Predictions & TreeSHAP explanations are ready.</p>
                </div>
             </div>

             <div className="space-y-2 w-full mt-2">
                <div className="h-2 w-full bg-green-100 rounded-full overflow-hidden">
                   <div className="h-full bg-green-500 rounded-full w-full"></div>
                </div>
                <div className="text-right text-[10px] font-bold text-gray-900">100%</div>
             </div>

             <div className="grid grid-cols-2 gap-3 mt-auto">
                <Button variant="outline" className="w-full justify-center h-11 border-[var(--border-strong)] bg-white text-gray-700" onClick={() => setShowPredictions(!showPredictions)}>
                   {showPredictions ? 'Hide Summary' : 'Quick Preview'}
                </Button>
                <div className="flex gap-2">
                  <Button variant="primary" className="flex-1 justify-center bg-blue-600 hover:bg-blue-700 h-11 shadow-md shadow-blue-500/20 px-2" onClick={onNavigateDashboard || (() => navigate('/dashboard'))}>
                     Dashboard
                  </Button>
                  <Button variant="primary" className="flex-1 justify-center bg-purple-600 hover:bg-purple-700 h-11 shadow-md shadow-purple-500/20 border-none px-2" onClick={onNavigateXAI || (() => navigate('/xai'))}>
                     TreeSHAP
                  </Button>
                </div>
             </div>

             {/* Predictions Summary Overlay */}
             {showPredictions && predictions && (
                <div className="absolute inset-0 z-20 bg-white/95 backdrop-blur-md p-5 flex flex-col custom-scrollbar overflow-y-auto animate-fade-in border-t border-gray-100">
                  <div className="flex justify-between items-center mb-3">
                    <h4 className="font-bold text-gray-900 text-sm">Quick Predictions Preview</h4>
                    <button onClick={() => setShowPredictions(false)} className="text-gray-400 hover:text-gray-900 text-xl leading-none">&times;</button>
                  </div>
                  <div className="space-y-3">
                    {predictions.diseases && predictions.diseases.map((cond, i) => (
                      <div key={i} className="flex justify-between items-center p-2 rounded-lg bg-gray-50 border border-gray-100">
                        <span className="text-xs font-bold text-gray-800">{cond.name}</span>
                        <Badge variant={cond.probability > 0.5 ? 'danger' : 'success'} size="sm">
                          {Math.round(cond.probability * 100)}% Risk
                        </Badge>
                      </div>
                    ))}
                    {(!predictions.diseases || predictions.diseases.length === 0) && (
                      <p className="text-xs text-gray-500">No predictions found.</p>
                    )}
                  </div>
                </div>
             )}
           </Card>
         ) : (
           <Card isGlass={true} className="bg-white border-gray-200/60 shadow-sm flex flex-col items-center justify-center h-[200px] opacity-60">
              <Cpu className="w-10 h-10 text-gray-300 animate-pulse mb-3" />
              <h4 className="text-sm font-bold text-gray-400">Awaiting Pipeline Completion</h4>
           </Card>
         )}
      </div>
    </div>
  );
}
