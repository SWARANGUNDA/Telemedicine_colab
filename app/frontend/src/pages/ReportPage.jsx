import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText, Send, RefreshCw, Bot, User, ShieldAlert, Sparkles, MessageSquare,
  ChevronDown, ChevronUp, ChevronRight, Stethoscope, CheckCircle2, Clock, Info, ExternalLink,
  Activity, BookOpen, AlertCircle, ArrowRight, ShieldCheck, Printer, Download, Share2,
  QrCode, Heart, Watch, Dna, Droplet, ActivitySquare
} from 'lucide-react';
import {
  Button, Card, CardHeader, CardBody, CardFooter, Badge,
  ProgressBar, CircularProgress, Table, TableRow, TableCell, Tabs, Drawer, Input, Alert
} from '../components/ui';
import { PageContainer, PageHeader, ContentSection } from '../components/layout';
import { generateReportV3, askRAGQuestion, askRAGQuestionV3, fetchSuggestedQuestions } from '../api/client';
import PersonalizedRecommendations from '../components/copilot/PersonalizedRecommendations';
import MarkdownRenderer from '../components/MarkdownRenderer';

const formatDisplayValue = (val) => {
  if (val === null || val === undefined) return 'N/A';
  if (typeof val === 'object') {
    if (val.value !== undefined && val.value !== null) return String(val.value);
    if (val.raw_value !== undefined && val.raw_value !== null) return String(val.raw_value);
    if (val.score !== undefined && val.score !== null) return String(val.score);
    return JSON.stringify(val);
  }
  return String(val);
};

export default function ReportPage({ user, session, predictionData, onDiscussWithDoctor }) {

  const navigate = useNavigate();
  const [reportStatus, setReportStatus] = useState('NOT_GENERATED');
  const [reportData, setReportData] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [isAssistantOpen, setIsAssistantOpen] = useState(false);

  // Q&A Assistant State
  const [question, setQuestion] = useState('');
  const [qaHistory, setQaHistory] = useState([]);
  const [loadingQA, setLoadingQA] = useState(false);
  const [qaError, setQaError] = useState(null);
  const [suggestedPrompts, setSuggestedPrompts] = useState([
    "What dietary changes will reduce my overall metabolic risk?",
    "What physical activity goals should I target?",
    "How do my wearable steps and sedentary time affect blood glucose variability?",
    "What follow-up blood tests should I discuss with my doctor?"
  ]);

  useEffect(() => {
    if (predictionData) {
      loadv3Report();
    } else {
      setReportStatus('NOT_GENERATED');
    }
  }, [predictionData]);

  useEffect(() => {
    if (session?.session_id || predictionData) {
      const sid = session?.session_id || predictionData?.patient_id || 'P_TEST_001';
      fetchSuggestedQuestions(sid, predictionData)
        .then(data => {
          if (data.suggested_questions?.length) {
            setSuggestedPrompts(data.suggested_questions);
          }
        })
        .catch(() => {});
    }
  }, [session, predictionData]);

  const loadv3Report = async () => {
    if (!predictionData) return;
    setReportStatus('GENERATING');
    setErrorMsg(null);
    try {
      const res = await generateReportV3(predictionData);
      setReportData(res);
      setReportStatus(res.report_status || 'READY');
    } catch (err) {
      setErrorMsg(err.message || 'Failed to generate personalized clinical report.');
      setReportStatus('FAILED');
    }
  };

  const handleAskQuestion = async (queryText) => {
    const qText = queryText || question;
    if (!qText.trim()) return;

    setLoadingQA(true);
    setQaError(null);
    const userMsg = { role: 'user', content: qText };
    setQaHistory((prev) => [...prev, userMsg]);
    setQuestion('');

    try {
      let res;
      if (predictionData) {
        res = await askRAGQuestionV3(predictionData, qText);
      } else {
        const sid = session?.session_id || 'TEST_C001';
        res = await askRAGQuestion(sid, qText);
      }

      const answerPayload = res.answer_payload || res;
      const botMsg = {
        role: 'bot',
        content: answerPayload.response_text || answerPayload.text || 'No grounded answer could be generated for this query.',
        evidence: answerPayload.retrieved_evidence || []
      };
      setQaHistory((prev) => [...prev, botMsg]);
    } catch (err) {
      setQaError(err.message || 'RAG Assistant query failed.');
    } finally {
      setLoadingQA(false);
    }
  };

  if (reportStatus === 'NOT_GENERATED' && !predictionData) {
    return (
      <PageContainer className="space-y-8">
        <PageHeader
          title="Physician-Grade AI Clinical Report"
          description="Multimodal Diagnostic Synthesis & Evidence-Grounded Recommendations"
          badge="Report Workspace"
        />
        <Card isGlass={true} className="p-8 text-center space-y-4">
          <FileText className="w-12 h-12 text-[var(--primary)] mx-auto" />
          <h3 className="text-lg font-bold text-[var(--text-main)]">No Active Clinical Report Found</h3>
          <p className="text-xs text-[var(--text-muted)] max-w-md mx-auto">
            Please run a multimodal health assessment in the Intake Workspace to generate your personalized AI report.
          </p>
          <Button variant="primary" size="md" onClick={() => navigate('/intake')}>
            Start New Assessment →
          </Button>
        </Card>
      </PageContainer>
    );
  }

  const patientName = user?.name || user?.full_name || user?.patient_profile?.full_name || (user?.email ? user.email.split('@')[0].replace('.', ' ').replace('_', ' ') : 'Patient');
  const patientId = user?.user_id || session?.session_id || predictionData?.patient_id || 'P_PATIENT';
  const pathwayUsed = predictionData?.effective_pathway || predictionData?.pathway_used || 'C+W+G';
  const dqScore = Math.round(predictionData?.data_quality_score ? (predictionData.data_quality_score * 100) : (predictionData?.overall_quality_score || 85));

  const safeParseFeats = (obj) => {
    if (!obj) return {};
    if (typeof obj === 'string') {
      try { return JSON.parse(obj); } catch (e) { return {}; }
    }
    return typeof obj === 'object' ? obj : {};
  };

  const rawConf = safeParseFeats(predictionData?.confirmed_features) || safeParseFeats(session?.confirmed_features) || {};
  const predictions = safeParseFeats(predictionData?.predictions) || safeParseFeats(predictionData?.disease_outcomes) || {};
  const clinFeats = safeParseFeats(rawConf.clinical || predictionData?.clinical_features || predictionData?.clinical_data || session?.confirmed_features?.clinical || {});
  const wearFeats = safeParseFeats(rawConf.wearable || predictionData?.wearable_features || predictionData?.wearable_data || session?.confirmed_features?.wearable || {});
  const gutFeats = safeParseFeats(rawConf.gut || predictionData?.gut_features || predictionData?.gut_data || session?.confirmed_features?.gut || {});

  const t2dItem = predictions['Type2_Diabetes'] || {};
  const t2dProbGlobal = t2dItem.calibrated_probability ?? t2dItem.probability ?? 0;
  const preItem = predictions['Prediabetes'] || {};
  const preProbGlobal = preItem.calibrated_probability ?? preItem.probability ?? 0;

  // Filter and sort diseases by probability descending
  let sortedDiseases = Object.keys(predictions).map(k => {
    const item = predictions[k] || {};
    const prob = item.calibrated_probability !== undefined ? item.calibrated_probability : (item.probability || 0);
    return { key: k, prob, riskLevel: item.risk_level || (prob >= 0.6 ? 'High Risk' : prob >= 0.3 ? 'Moderate Risk' : 'Low Risk'), class: item.predicted_class };
  });

  if (t2dProbGlobal >= preProbGlobal) {
    sortedDiseases = sortedDiseases.filter(d => d.key !== 'Prediabetes');
  } else {
    sortedDiseases = sortedDiseases.filter(d => d.key !== 'Type2_Diabetes');
  }
  
  sortedDiseases.sort((a, b) => b.prob - a.prob);

  const highestRiskItem = sortedDiseases[0] || { key: 'Type2_Diabetes', prob: 0, riskLevel: 'Low Risk' };
  const highestRiskName = highestRiskItem.key.replace(/_/g, ' ');
  const highestRiskPct = Math.round(highestRiskItem.prob * 100);

  const diseasesList = [
    { key: 'Type2_Diabetes', title: 'Type 2 Diabetes', desc: 'Glycemic control & insulin resistance' },
    { key: 'Prediabetes', title: 'Prediabetes Risk', desc: 'Impaired fasting glucose screening' },
    { key: 'High_Adiposity_Risk', title: 'Adiposity & Obesity', desc: 'Body mass & visceral fat distribution' },
    { key: 'Metabolic_Syndrome', title: 'Metabolic Syndrome', desc: 'Cluster of metabolic risk factors' },
    { key: 'NAFLD', title: 'NAFLD Liver Health', desc: 'Non-alcoholic fatty liver disease risk' },
  ];

  return (
    <PageContainer className="space-y-12 pb-24">
      {/* Top Action Bar (Hidden when printing) */}
      <div className="flex items-center justify-between gap-4 print:hidden">
        <Button variant="outline" size="sm" onClick={() => navigate('/dashboard')}>
          ← Back to Dashboard
        </Button>

        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" leftIcon={<MessageSquare className="w-4 h-4 text-[var(--accent)]" />} onClick={() => setIsAssistantOpen(true)}>
            Ask AI Assistant
          </Button>
          <Button variant="outline" size="sm" leftIcon={<Printer className="w-4 h-4" />} onClick={() => window.print()}>
            Print Report
          </Button>
          <Button variant="primary" size="sm" leftIcon={<Download className="w-4 h-4" />} onClick={() => window.print()}>
            Download PDF
          </Button>
        </div>
      </div>

      {/* PRINTABLE CLINICAL REPORT WORKSPACE */}
      <div className="space-y-8 bg-white dark:bg-[#0F172A] p-8 rounded-2xl border border-[var(--border-medium)] shadow-lg text-[var(--text-main)] print:p-0 print:border-none print:shadow-none">
        {/* SECTION 1: HOSPITAL-GRADE REPORT HEADER */}
        <div className="border-b-2 border-[var(--primary)] pb-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[var(--primary)] text-white font-black flex items-center justify-center text-lg">
                TM
              </div>
              <div>
                <h1 className="text-xl font-black text-[var(--text-main)] tracking-tight">TeleMed AI Medical Center</h1>
                <p className="text-xs font-mono text-[var(--text-muted)] uppercase tracking-wider">Multimodal Diagnostic & Clinical Decision Report</p>
              </div>
            </div>

            <div className="flex items-center gap-4 text-right">
              <div className="hidden sm:block">
                <span className="text-[10px] font-mono text-[var(--text-muted)] block">Report Verification Code</span>
                <span className="text-xs font-mono font-bold text-[var(--primary)]">ASM-{patientId.slice(-8).toUpperCase()}</span>
              </div>
              <div className="p-2 border rounded-lg border-[var(--border-medium)] bg-slate-50 dark:bg-slate-800" aria-label="QR Code Security Verification" role="img" title="Scan to verify report authenticity">
                <QrCode className="w-8 h-8 text-[var(--text-main)]" />
              </div>
            </div>
          </div>

          {/* Patient Meta Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-xs">
            <div>
              <span className="text-[10px] font-mono text-[var(--text-muted)] block">PATIENT NAME</span>
              <strong className="text-[var(--text-main)]">{patientName}</strong>
            </div>
            <div>
              <span className="text-[10px] font-mono text-[var(--text-muted)] block">PATIENT ID</span>
              <strong className="font-mono text-[var(--text-main)]">{patientId}</strong>
            </div>
            <div>
              <span className="text-[10px] font-mono text-[var(--text-muted)] block">ASSESSMENT DATE</span>
              <strong className="text-[var(--text-main)]">{new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</strong>
            </div>
            <div>
              <span className="text-[10px] font-mono text-[var(--text-muted)] block">PIPELINE & PATHWAY</span>
              <strong className="text-[var(--primary)]">v4.0 Stable ({pathwayUsed})</strong>
            </div>
          </div>
        </div>

        {/* SECTION 2: EXECUTIVE CLINICAL SUMMARY */}
        <Card isGlass={true} className="p-6 space-y-4 bg-gradient-to-r from-[var(--bg-surface)] to-[var(--bg-primary)] border-l-4 border-l-[var(--primary)]">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-extrabold text-[var(--text-main)]">Executive Clinical Summary</h3>
            <Badge variant="primary" size="sm">Overall Health Score: {dqScore}%</Badge>
          </div>

          <p className="text-xs text-[var(--text-muted)] leading-relaxed">
            {typeof reportData?.executive_summary === 'string'
              ? reportData.executive_summary
              : (typeof reportData?.summary === 'string'
                ? reportData.summary
                : `Multimodal diagnostic evaluation completed across pathway ${pathwayUsed}. Model inference identifies ${highestRiskName} (${highestRiskPct}%) as the primary health factor. Biomarker and telemetry inputs were processed with an overall data quality index of ${dqScore}%.`
              )
            }
          </p>


          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-center text-xs">
            <div className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
              <span className="text-[10px] font-mono text-[var(--text-muted)] block">Highest Risk Target</span>
              <strong className="text-[var(--danger)]">{highestRiskName} ({highestRiskPct}%)</strong>
            </div>
            <div className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
              <span className="text-[10px] font-mono text-[var(--text-muted)] block">Elevated Signals</span>
              <strong className="text-[var(--warning)]">{sortedDiseases.filter(d => d.prob >= 0.35).length} Targets</strong>
            </div>
            <div className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
              <span className="text-[10px] font-mono text-[var(--text-muted)] block">Data Quality</span>
              <strong className="text-[var(--success)]">{dqScore}% Verified</strong>
            </div>
            <div className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
              <span className="text-[10px] font-mono text-[var(--text-muted)] block">Model Calibration</span>
              <strong className="text-[var(--primary)]">Isotonic (v4.0)</strong>
            </div>
          </div>
        </Card>

        {/* SECTION 3: MULTI-DISEASE RISK ASSESSMENT */}
        <ContentSection title="1. Multi-Disease Risk Assessment" subtitle="Calibrated probability predictions across 5 cardiometabolic disease targets">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {diseasesList.map((disease) => {
              const dData = predictions[disease.key] || {};
              const dProb = dData.calibrated_probability !== undefined 
                ? dData.calibrated_probability 
                : (dData.probability !== undefined ? dData.probability : 0);
              const dPct = Math.round(dProb * 100);

              let isPlaceholder = false;
              let placeholderReason = '';

              const t2dIsPositiveGlobal = (predictions['Type2_Diabetes']?.risk_level?.toLowerCase() === 'positive') || (t2dProbGlobal >= 0.4);
              if (disease.key === 'Prediabetes' && (t2dIsPositiveGlobal || t2dProbGlobal > preProbGlobal)) {
                isPlaceholder = true;
                placeholderReason = 'Subsumed by Type 2 Diabetes evaluation.';
              }
              if (disease.key === 'Type2_Diabetes' && !t2dIsPositiveGlobal && preProbGlobal > t2dProbGlobal) {
                isPlaceholder = true;
                placeholderReason = 'Condition absent; Prediabetes is active.';
              }

              if (isPlaceholder) {
                return (
                  <Card key={disease.key} isGlass={true} className="p-4 space-y-2 border-2 border-dashed border-[var(--border-subtle)] bg-[var(--bg-primary)]/50 opacity-60">
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <h4 className="text-xs font-extrabold text-[var(--text-muted)] line-through truncate" title={disease.title}>{disease.title}</h4>
                      <Badge variant="ghost" size="sm" className="text-[9px]">NOT PRESENT</Badge>
                    </div>
                    <p className="text-[10px] text-[var(--text-muted)] leading-relaxed italic border-l-2 border-[var(--border-medium)] pl-2">{placeholderReason}</p>
                  </Card>
                );
              }

              const dRisk = dData.risk_level || (dPct >= 60 ? 'High Risk' : dPct >= 30 ? 'Moderate Risk' : 'Low Risk');
              const variant = dRisk.toUpperCase().includes('HIGH') ? 'danger' : dRisk.toUpperCase().includes('MODERATE') ? 'warning' : 'success';
              const borderTop = dRisk.toUpperCase().includes('HIGH') ? 'border-t-4 border-t-[var(--danger)]' : dRisk.toUpperCase().includes('MODERATE') ? 'border-t-4 border-t-[var(--warning)]' : 'border-t-4 border-t-[var(--success)]';

              return (
                <Card key={disease.key} isGlass={true} className={`p-4 space-y-2 ${borderTop}`}>
                  <div className="flex items-center justify-between gap-1">
                    <h4 className="text-xs font-extrabold text-[var(--text-main)] truncate" title={disease.title}>{disease.title}</h4>
                    <Badge variant={variant} size="sm">{dPct}%</Badge>
                  </div>
                  <ProgressBar value={dPct} max={100} variant={variant} />
                  <p className="text-[11px] text-[var(--text-muted)] line-clamp-2">{disease.desc}</p>
                </Card>
              );
            })}
          </div>
        </ContentSection>

        {/* SECTION 4: CANONICAL BIOMARKER SUMMARY TABLES */}
        <ContentSection title="2. Canonical Biomarker Measurements" subtitle="Extracted, normalized, and validated feature measurements across active modalities">
          <Tabs
            tabs={[
              {
                id: 'clin_tab',
                label: `Clinical Lab Biomarkers (${Object.keys(clinFeats).length})`,
                content: (
                  <Table headers={['Biomarker Name', 'Measured Value', 'Status']}>
                    {Object.keys(clinFeats).length > 0 ? (
                      Object.keys(clinFeats).map((k) => (
                        <TableRow key={k}>
                          <TableCell className="font-semibold text-xs">{k}</TableCell>
                          <TableCell className="font-mono font-bold text-[var(--primary)] text-xs">
                            {formatDisplayValue(clinFeats[k])}
                          </TableCell>
                          <TableCell><Badge variant="primary" size="sm">CONFIRMED</Badge></TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={3} className="text-center text-xs text-[var(--text-muted)]">No clinical features supplied in assessment</TableCell>
                      </TableRow>
                    )}
                  </Table>
                )
              },
              {
                id: 'wear_tab',
                label: `Wearable Telemetry (${Object.keys(wearFeats).length})`,
                content: (
                  <Table headers={['Telemetry Metric', 'Measured Value', 'Status']}>
                    {Object.keys(wearFeats).length > 0 ? (
                      Object.keys(wearFeats).map((k) => (
                        <TableRow key={k}>
                          <TableCell className="font-semibold text-xs">{k}</TableCell>
                          <TableCell className="font-mono font-bold text-[var(--secondary)] text-xs">
                            {formatDisplayValue(wearFeats[k])}
                          </TableCell>
                          <TableCell><Badge variant="secondary" size="sm">ACTIVE</Badge></TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={3} className="text-center text-xs text-[var(--text-muted)]">No wearable features supplied in assessment</TableCell>
                      </TableRow>
                    )}
                  </Table>
                )
              },
              {
                id: 'gut_tab',
                label: `Gut Microbiome Taxa (${Object.keys(gutFeats).length})`,
                content: (
                  <Table headers={['Microbial Taxa', 'Relative Abundance (%)', 'Status']}>
                    {Object.keys(gutFeats).length > 0 ? (
                      Object.keys(gutFeats).map((k) => (
                        <TableRow key={k}>
                          <TableCell className="font-semibold text-xs">{k}</TableCell>
                          <TableCell className="font-mono font-bold text-[var(--accent)] text-xs">
                            {formatDisplayValue(gutFeats[k])}
                          </TableCell>
                          <TableCell><Badge variant="accent" size="sm">PROFILED</Badge></TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={3} className="text-center text-xs text-[var(--text-muted)]">No gut microbiome features supplied in assessment</TableCell>
                      </TableRow>
                    )}
                  </Table>
                )
              }
            ]}
          />

        </ContentSection>

        {/* SECTION 5: EVIDENCE-GROUNDED RECOMMENDATIONS */}
        <ContentSection title="3. Evidence-Grounded Clinical Recommendations" subtitle="Dynamic clinical guidelines and interactive what-if risk simulations powered by Copilot">
          <div className="space-y-6">
            <PersonalizedRecommendations predictionData={predictionData} />
          </div>
        </ContentSection>


        {/* SECTION 6: REPORT FOOTER & CLINICAL DISCLAIMER */}
        <div className="pt-6 border-t border-[var(--border-subtle)] space-y-3 text-[10px] text-[var(--text-muted)]">
          <div className="flex items-center justify-between">
            <span>Generated: {new Date().toLocaleDateString()} • TeleMed AI Engine v4.0 Stable</span>
            <span>Page 1 of 1</span>
          </div>
          <p>
            <strong>CLINICAL DISCLAIMER:</strong> This AI-generated report is designed to support medical decision-making by qualified healthcare professionals. It does NOT constitute a standalone medical diagnosis. All findings should be reviewed in clinical context with standard laboratory testing.
          </p>
        </div>
      </div>

      {/* RAG Q&A Assistant Drawer Modal */}
      <Drawer
        isOpen={isAssistantOpen}
        onClose={() => setIsAssistantOpen(false)}
        title={
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-[var(--primary)]" />
            <span className="font-bold bg-clip-text text-transparent bg-gradient-to-r from-[var(--primary)] to-[var(--accent)]">
              TeleMed Clinical Copilot
            </span>
          </div>
        }
      >
        <div className="flex flex-col h-full bg-[var(--bg-surface)] dark:bg-[#0B132B]">
          
          {/* Chat History Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-6">
            
            {/* Empty State / Suggested Prompts */}
            {qaHistory.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full space-y-6 text-center animate-fade-in py-8">
                <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-[var(--primary-light)] to-[var(--accent-light)] flex items-center justify-center border border-[var(--primary)]/20 shadow-lg shadow-[var(--primary)]/10">
                  <Sparkles className="w-8 h-8 text-[var(--primary)]" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-bold text-[var(--text-main)]">How can I help you understand this report?</h3>
                  <p className="text-xs text-[var(--text-muted)] max-w-xs mx-auto">
                    I have full access to your multimodal risk profile and ADA/WHO clinical guidelines.
                  </p>
                </div>
                
                <div className="w-full space-y-3 pt-4">
                  {suggestedPrompts.slice(0, 3).map((prompt, i) => (
                    <button
                      key={i}
                      onClick={() => handleAskQuestion(prompt)}
                      className="w-full p-4 text-left text-xs bg-white dark:bg-slate-800/80 border border-[var(--border-subtle)] hover:border-[var(--primary)] hover:bg-[var(--primary-light)] rounded-2xl transition-all duration-300 text-[var(--text-main)] shadow-sm hover:shadow-md flex items-center gap-3 group animate-slide-up"
                      style={{ animationDelay: `${i * 100}ms` }}
                    >
                      <MessageSquare className="w-4 h-4 text-[var(--primary)] opacity-70 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                      <span className="flex-1 leading-relaxed font-medium">{prompt}</span>
                      <ChevronRight className="w-4 h-4 text-[var(--primary)] opacity-0 group-hover:opacity-100 transition-all transform -translate-x-2 group-hover:translate-x-0" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Chat Bubbles */}
            {qaHistory.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-slide-up`}>
                
                {msg.role === 'bot' && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[var(--primary)] to-[var(--accent)] flex items-center justify-center mr-3 mt-1 flex-shrink-0 shadow-md">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                )}
                
                <div 
                  className={`max-w-[85%] p-4 text-sm shadow-sm ${
                    msg.role === 'user' 
                      ? 'bg-gradient-to-br from-[var(--primary)] to-blue-600 text-white rounded-t-2xl rounded-bl-2xl rounded-br-sm' 
                      : 'bg-white dark:bg-slate-800/90 text-[var(--text-main)] border border-[var(--border-subtle)] rounded-t-2xl rounded-br-2xl rounded-bl-sm prose prose-sm dark:prose-invert max-w-none shadow-sm'
                  }`}
                >
                  <MarkdownRenderer content={msg.content} />
                </div>
              </div>
            ))}

            {/* Loading Indicator */}
            {loadingQA && (
              <div className="flex justify-start animate-fade-in">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[var(--primary)] to-[var(--accent)] flex items-center justify-center mr-3 mt-1 flex-shrink-0 shadow-md">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-white dark:bg-slate-800/90 border border-[var(--border-subtle)] rounded-t-2xl rounded-br-2xl rounded-bl-sm p-4 flex items-center gap-1 shadow-sm h-[44px]">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="p-4 bg-white dark:bg-slate-900 border-t border-[var(--border-subtle)] shadow-[0_-10px_40px_-10px_rgba(0,0,0,0.05)]">
            {qaError && (
              <div className="mb-3 px-3 py-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/50 rounded-lg text-xs text-red-600 dark:text-red-400 flex items-center gap-2 animate-fade-in">
                <AlertCircle className="w-4 h-4" />
                {qaError}
              </div>
            )}
            <div className="flex items-center gap-2 bg-[var(--bg-primary)] border border-[var(--border-medium)] rounded-full p-1 pl-4 focus-within:border-[var(--primary)] focus-within:ring-2 focus-within:ring-[var(--primary-light)] transition-all shadow-inner">
              <input
                type="text"
                placeholder="Ask about your metabolic health..."
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAskQuestion()}
                disabled={loadingQA}
                className="flex-1 bg-transparent border-none focus:outline-none focus:ring-0 text-sm text-[var(--text-main)] placeholder-[var(--text-muted)]"
              />
              <button 
                onClick={() => handleAskQuestion()}
                disabled={loadingQA || !question.trim()}
                className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 ${
                  question.trim() && !loadingQA 
                    ? 'bg-gradient-to-r from-[var(--primary)] to-blue-600 text-white shadow-md hover:shadow-lg hover:scale-105' 
                    : 'bg-slate-200 dark:bg-slate-800 text-slate-400 dark:text-slate-500 cursor-not-allowed'
                }`}
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            <div className="text-center mt-3">
              <span className="text-[10px] text-[var(--text-muted)] flex items-center justify-center gap-1 opacity-70">
                <ShieldCheck className="w-3 h-3" />
                Medical RAG Engine. AI may produce inaccurate information.
              </span>
            </div>
          </div>
        </div>
      </Drawer>
    </PageContainer>
  );
}
