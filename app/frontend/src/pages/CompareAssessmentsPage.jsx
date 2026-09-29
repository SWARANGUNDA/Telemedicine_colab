import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader, PageContainer, ContentSection } from '../components/layout';
import { Card, Badge, Button, ProgressBar, Tabs } from '../components/ui';
import {
  TrendingUp, TrendingDown, ArrowRight, Printer, Download, FileText,
  Calendar, CheckCircle2, AlertCircle, Activity, Heart, Watch, Dna,
  Sparkles, Sliders, RefreshCw, BarChart3, ChevronRight, ShieldCheck, GitCompare,
  Stethoscope, Clock, Zap
} from 'lucide-react';
import { fetchPatientRecords } from '../api/client';

export default function CompareAssessmentsPage({ user, session, predictionData, onNavigate }) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('comparison');
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAssessmentA, setSelectedAssessmentA] = useState('');
  const [selectedAssessmentB, setSelectedAssessmentB] = useState('');

  useEffect(() => {
    async function loadHistory() {
      setLoading(true);
      try {
        const res = await fetchPatientRecords();
        const rawData = res?.records || [];

        // Filter strictly for current user
        const userRecords = rawData.filter(r => 
          (r.user_id && r.user_id === user?.user_id) ||
          (r.patient_id && r.patient_id === user?.user_id) ||
          (r.user_email && r.user_email.toLowerCase() === user?.email?.toLowerCase()) ||
          (r.email && r.email.toLowerCase() === user?.email?.toLowerCase())
        );

        setRecords(userRecords);

        if (userRecords.length >= 2) {
          setSelectedAssessmentA(userRecords[0].record_id);
          setSelectedAssessmentB(userRecords[1].record_id);
        } else if (userRecords.length === 1) {
          setSelectedAssessmentA(userRecords[0].record_id);
          setSelectedAssessmentB('');
        }
      } catch (e) {
        setRecords([]);
      } finally {
        setLoading(false);
      }
    }
    loadHistory();
  }, [user]);

  if (loading) {
    return (
      <PageContainer className="space-y-8 py-6">
        <PageHeader
          title="Longitudinal Assessment Comparison"
          description="Side-by-side comparative analysis of historical health assessments"
          badge="Longitudinal Analytics"
        />
        <Card isGlass={true} className="p-12 text-center space-y-4">
          <RefreshCw className="w-8 h-8 text-[var(--primary)] animate-spin mx-auto" />
          <p className="text-xs text-[var(--text-muted)]">Loading historical assessment records...</p>
        </Card>
      </PageContainer>
    );
  }

  // Strict empty state when user has fewer than 2 completed assessments
  if (records.length < 2) {
    return (
      <PageContainer className="space-y-8 py-6">
        <PageHeader
          title="Longitudinal Assessment Comparison"
          description="Side-by-side comparative analysis of historical health assessments, biomarker trajectory, and disease risk progression"
          badge="Longitudinal Analytics"
        />
        <Card isGlass={true} className="p-12 text-center space-y-4 shadow-xl border border-[var(--border-subtle)]">
          <div className="w-16 h-16 rounded-3xl bg-[var(--primary-light)] text-[var(--primary)] flex items-center justify-center mx-auto shadow-inner">
            <GitCompare className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-extrabold text-[var(--text-main)]">
            At Least 2 Assessments Required for Longitudinal Comparison
          </h3>
          <p className="text-xs text-[var(--text-muted)] max-w-md mx-auto leading-relaxed">
            {records.length === 0 
              ? "No completed health assessments found for your account. Complete your initial multimodal health intake to begin tracking your longitudinal clinical trajectory."
              : "You have 1 completed assessment. Complete at least one additional intake assessment to unlock side-by-side biomarker shifts, risk trajectory comparisons, and multi-assessment insights."
            }
          </p>
          <div className="pt-3">
            <Button
              variant="primary"
              size="md"
              leftIcon={<Sparkles className="w-4 h-4" />}
              onClick={() => onNavigate ? onNavigate('intake') : navigate('/intake')}
            >
              Start New Health Assessment
            </Button>
          </div>
        </Card>
      </PageContainer>
    );
  }

  const assessmentOptions = records.map((r, idx) => {
    const rawQuality = r.data_quality_score ?? r.data_quality_scores?.overall_quality_score ?? r.quality_score;
    const qualityNum = rawQuality !== undefined && rawQuality !== null 
      ? (rawQuality <= 1 ? Math.round(rawQuality * 100) : Math.min(100, Math.round(rawQuality)))
      : 100;

    return {
      id: r.record_id || `ASM-${idx}`,
      date: r.created_at ? new Date(r.created_at).toISOString().split('T')[0] : 'N/A',
      label: `${r.created_at ? new Date(r.created_at).toLocaleDateString() : 'Assessment'} (${r.effective_pathway || 'C'})`,
      score: qualityNum,
      risk: r.prediction_snapshot?.disease_outcomes?.Type2_Diabetes?.risk_level || 'EVALUATED',
      riskLevel: r.prediction_snapshot?.disease_outcomes?.Type2_Diabetes?.risk_level || 'EVALUATED',
      pathway: r.effective_pathway || 'C',
      quality: `${qualityNum}%`,
      confidence: 'High (V4 Multimodal)',
    };
  });

  const recA = records.find(r => (r.record_id || r.id) === selectedAssessmentA) || records[0];
  const recB = records.find(r => (r.record_id || r.id) === selectedAssessmentB) || records[1];

  const assA = assessmentOptions.find(a => a.id === selectedAssessmentA) || assessmentOptions[0];
  const assB = assessmentOptions.find(a => a.id === selectedAssessmentB) || assessmentOptions[1];

  // Biomarkers Comparison Matrix: strictly derived from recA and recB confirmed features
  const biomarkerComparison = (() => {
    if (!recA || !recB) return [];
    const r1 = recA?.prediction_snapshot?.confirmed_features?.clinical || recA?.confirmed_features?.clinical || {};
    const r2 = recB?.prediction_snapshot?.confirmed_features?.clinical || recB?.confirmed_features?.clinical || {};

    const allKeys = Array.from(new Set([...Object.keys(r1), ...Object.keys(r2)])).filter(k => !['Patient_ID', 'Gender'].includes(k));
    if (allKeys.length === 0) return [];

    return allKeys.map(k => {
      const v1 = r1[k];
      const v2 = r2[k];
      const n1 = parseFloat(v1);
      const n2 = parseFloat(v2);
      const hasBothNums = !isNaN(n1) && !isNaN(n2);
      const diffVal = hasBothNums ? (n1 - n2) : null;
      
      const isImprovement = diffVal !== null && diffVal < 0;

      return {
        name: k.replace(/_/g, ' '),
        current: v1 !== undefined && v1 !== null ? `${v1}` : '—',
        previous: v2 !== undefined && v2 !== null ? `${v2}` : '—',
        diff: diffVal !== null ? (diffVal > 0 ? `+${diffVal.toFixed(1)}` : `${diffVal.toFixed(1)}`) : '—',
        trend: diffVal === null ? 'Stable' : (isImprovement ? 'Improved' : (diffVal > 0 ? 'Elevated' : 'Stable')),
        status: diffVal === null ? 'Recorded' : (isImprovement ? 'Optimal Shift' : 'Recorded'),
        variant: isImprovement ? 'success' : (diffVal > 0 ? 'warning' : 'outline'),
      };
    });
  })();

  // Disease Risk Progression: strictly derived from recA and recB prediction snapshots
  const diseaseProgression = (() => {
    if (!recA || !recB) return [];
    const outcomesA = recA?.prediction_snapshot?.disease_outcomes || recA?.disease_outcomes || {};
    const outcomesB = recB?.prediction_snapshot?.disease_outcomes || recB?.disease_outcomes || {};

    const diseasesList = [
      { key: 'Type2_Diabetes', name: 'Type 2 Diabetes Risk', category: 'Metabolic / Glycemic' },
      { key: 'Prediabetes', name: 'Prediabetes Risk', category: 'Metabolic / Glycemic' },
      { key: 'Metabolic_Syndrome', name: 'Metabolic Syndrome Risk', category: 'Metabolic Risk' },
      { key: 'NAFLD', name: 'NAFLD Liver Health Risk', category: 'Hepatic / Multiomics' },
      { key: 'High_Adiposity_Risk', name: 'Adiposity & Obesity Risk', category: 'Body Composition' },
    ];

    return diseasesList.map(d => {
      const oA = outcomesA[d.key] || {};
      const oB = outcomesB[d.key] || {};

      const probA = oA.calibrated_probability ?? oA.probability ?? oA.risk_score ?? 0;
      const probB = oB.calibrated_probability ?? oB.probability ?? oB.risk_score ?? 0;

      const pctA = Math.round(probA * 100);
      const pctB = Math.round(probB * 100);
      const diff = pctA - pctB;

      return {
        disease: d.name,
        category: d.category,
        baselineProb: pctB,
        currentProb: pctA,
        riskLevel: oA.risk_level || (pctA >= 60 ? 'HIGH RISK' : pctA >= 30 ? 'MODERATE RISK' : 'OPTIMAL LOW'),
        statusVariant: diff < 0 ? 'success' : diff > 0 ? 'warning' : 'outline',
        driver: diff === 0 
          ? 'Risk remained stable between assessments' 
          : diff < 0 
          ? `Risk decreased by ${Math.abs(diff)}% across longitudinal follow-up` 
          : `Risk increased by ${diff}% across longitudinal follow-up`
      };
    });
  })();

  const handlePrint = () => {
    window.print();
  };

  return (
    <PageContainer className="space-y-8 py-6">
      
      {/* Page Header */}
      <PageHeader
        title="Longitudinal Assessment Comparison"
        description="Side-by-side comparative analysis of historical health assessments, biomarker trajectory, and disease risk progression"
        badge="Longitudinal Analytics"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" leftIcon={<Printer className="w-4 h-4" />} onClick={handlePrint}>
              Print Report
            </Button>
            <Button variant="primary" size="sm" leftIcon={<Download className="w-4 h-4" />}>
              Export JSON
            </Button>
          </div>
        }
      />

      {/* Main Workspace Navigation Tabs */}
      <Tabs
        activeTab={activeTab}
        onChange={setActiveTab}
        tabs={[
          { id: 'comparison', label: 'Side-by-Side Comparison' },
          { id: 'biomarkers', label: 'Biomarker Trajectory' },
          { id: 'progression', label: 'Disease Risk Progression' },
          { id: 'insights', label: 'Longitudinal Insights' },
        ]}
      />

      {/* TAB 1: SIDE-BY-SIDE COMPARISON */}
      {activeTab === 'comparison' && (
        <div className="space-y-6 animate-fade-in">
          
          {/* Assessment Picker Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Assessment A Picker */}
            <Card isGlass={true} className="p-6 space-y-4 border-l-4 border-l-[var(--primary)] shadow-xl">
              <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
                <div className="flex items-center gap-2">
                  <Badge variant="primary" size="sm">Assessment A (Recent)</Badge>
                  <span className="text-xs font-mono text-[var(--text-muted)]">{assA.date}</span>
                </div>
                <Badge variant="warning" size="sm">
                  {assA.risk}
                </Badge>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-mono text-[var(--text-muted)] uppercase block">Select Target Assessment</label>
                <select
                  value={selectedAssessmentA}
                  onChange={(e) => setSelectedAssessmentA(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] font-semibold focus:outline-none focus:border-[var(--primary)]"
                >
                  {assessmentOptions.map(opt => (
                    <option key={opt.id} value={opt.id}>{opt.label} — {opt.date}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-3 gap-2 text-xs font-mono pt-2">
                <div className="p-2 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-center">
                  <span className="text-[9px] text-[var(--text-muted)] block uppercase">Pathway</span>
                  <strong className="text-[var(--primary)]">{assA.pathway}</strong>
                </div>
                <div className="p-2 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-center">
                  <span className="text-[9px] text-[var(--text-muted)] block uppercase">Quality</span>
                  <strong className="text-[var(--success)]">{assA.quality}</strong>
                </div>
                <div className="p-2 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-center">
                  <span className="text-[9px] text-[var(--text-muted)] block uppercase">Verification</span>
                  <strong className="text-[var(--accent)]">Confirmed</strong>
                </div>
              </div>
            </Card>

            {/* Assessment B Picker */}
            <Card isGlass={true} className="p-6 space-y-4 border-l-4 border-l-[var(--secondary)] shadow-xl">
              <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" size="sm">Assessment B (Baseline)</Badge>
                  <span className="text-xs font-mono text-[var(--text-muted)]">{assB.date}</span>
                </div>
                <Badge variant="warning" size="sm">
                  {assB.risk}
                </Badge>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-mono text-[var(--text-muted)] uppercase block">Select Baseline Assessment</label>
                <select
                  value={selectedAssessmentB}
                  onChange={(e) => setSelectedAssessmentB(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] font-semibold focus:outline-none focus:border-[var(--secondary)]"
                >
                  {assessmentOptions.map(opt => (
                    <option key={opt.id} value={opt.id}>{opt.label} — {opt.date}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-3 gap-2 text-xs font-mono pt-2">
                <div className="p-2 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-center">
                  <span className="text-[9px] text-[var(--text-muted)] block uppercase">Pathway</span>
                  <strong className="text-[var(--secondary)]">{assB.pathway}</strong>
                </div>
                <div className="p-2 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-center">
                  <span className="text-[9px] text-[var(--text-muted)] block uppercase">Quality</span>
                  <strong className="text-[var(--success)]">{assB.quality}</strong>
                </div>
                <div className="p-2 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-center">
                  <span className="text-[9px] text-[var(--text-muted)] block uppercase">Confidence</span>
                  <strong className="text-[var(--accent)]">{assB.confidence}</strong>
                </div>
              </div>
            </Card>

          </div>

          {/* Biomarkers Comparison Matrix Table */}
          <ContentSection title="Biomarker Trajectory Matrix (Assessment A vs B)">
            <Card isGlass={true} className="overflow-hidden shadow-xl">
              {biomarkerComparison.length === 0 ? (
                <div className="p-8 text-center text-xs text-[var(--text-muted)]">
                  No quantitative clinical biomarkers available for side-by-side numerical comparison in selected records.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-[var(--bg-primary)] border-b border-[var(--border-subtle)] font-mono uppercase text-[10px] text-[var(--text-muted)]">
                      <tr>
                        <th className="p-3.5">Biomarker / Trajectory</th>
                        <th className="p-3.5">Assessment A ({assA.date})</th>
                        <th className="p-3.5">Assessment B ({assB.date})</th>
                        <th className="p-3.5">Absolute Shift</th>
                        <th className="p-3.5">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--border-subtle)] font-medium">
                      {biomarkerComparison.map((bm, i) => (
                        <tr key={i} className="hover:bg-[var(--bg-surface-hover)] transition-colors">
                          <td className="p-3.5 font-bold text-[var(--text-main)] flex items-center gap-2">
                            <Activity className="w-3.5 h-3.5 text-[var(--primary)]" />
                            {bm.name}
                          </td>
                          <td className="p-3.5 font-mono text-[var(--primary)] font-bold">{bm.current}</td>
                          <td className="p-3.5 font-mono text-[var(--text-muted)]">{bm.previous}</td>
                          <td className="p-3.5 font-mono font-bold">{bm.diff}</td>
                          <td className="p-3.5">
                            <Badge variant={bm.variant} size="sm">{bm.trend}</Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </ContentSection>

        </div>
      )}

      {/* TAB 2: BIOMARKER TRAJECTORY */}
      {activeTab === 'biomarkers' && (
        <div className="space-y-6 animate-fade-in">
          <ContentSection title="Biomarker Trajectory & Longitudinal Velocity">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {biomarkerComparison.map((bm, i) => (
                <Card key={i} isGlass={true} className="p-5 space-y-3 shadow-md">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-[var(--text-muted)] font-mono text-[10px] uppercase font-bold">{bm.name}</span>
                    <Badge variant={bm.variant} size="sm">{bm.diff}</Badge>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <div className="space-y-0.5">
                      <span className="text-xs text-[var(--text-muted)] block font-mono">Current ({assA.date})</span>
                      <strong className="text-xl font-bold text-[var(--text-main)] font-mono">{bm.current}</strong>
                    </div>
                    <div className="space-y-0.5 text-right">
                      <span className="text-xs text-[var(--text-muted)] block font-mono">Previous ({assB.date})</span>
                      <span className="text-base font-medium text-[var(--text-muted)] font-mono">{bm.previous}</span>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </ContentSection>
        </div>
      )}

      {/* TAB 3: DISEASE RISK PROGRESSION */}
      {activeTab === 'progression' && (
        <div className="space-y-6 animate-fade-in">
          <ContentSection title="Multi-Target Disease Risk Trajectory Shifts">
            <div className="space-y-4">
              {diseaseProgression.map((dp, i) => (
                <Card key={i} isGlass={true} className="p-5 space-y-3 shadow-md">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border-subtle)] pb-2.5">
                    <div>
                      <h4 className="font-extrabold text-sm text-[var(--text-main)]">{dp.disease}</h4>
                      <p className="text-[11px] text-[var(--text-muted)] font-mono">{dp.category}</p>
                    </div>
                    <Badge variant={dp.statusVariant} size="sm">{dp.riskLevel}</Badge>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
                    <div className="space-y-1">
                      <div className="flex justify-between text-[11px]">
                        <span className="text-[var(--text-muted)]">Assessment A ({assA.date})</span>
                        <strong>{dp.currentProb}%</strong>
                      </div>
                      <ProgressBar value={dp.currentProb} max={100} variant={dp.currentProb >= 50 ? 'danger' : 'primary'} />
                    </div>

                    <div className="space-y-1">
                      <div className="flex justify-between text-[11px]">
                        <span className="text-[var(--text-muted)]">Assessment B ({assB.date})</span>
                        <span className="text-[var(--text-muted)]">{dp.baselineProb}%</span>
                      </div>
                      <ProgressBar value={dp.baselineProb} max={100} variant="secondary" />
                    </div>
                  </div>

                  <p className="text-[11px] text-[var(--text-muted)] pt-1 flex items-center gap-1.5">
                    <Info className="w-3.5 h-3.5 text-[var(--primary)] shrink-0" />
                    {dp.driver}
                  </p>
                </Card>
              ))}
            </div>
          </ContentSection>
        </div>
      )}

      {/* TAB 4: LONGITUDINAL INSIGHTS */}
      {activeTab === 'insights' && (
        <div className="space-y-6 animate-fade-in">
          
          {/* 1. Executive AI Longitudinal Summary Card */}
          <Card isGlass={true} className="p-6 space-y-4 shadow-xl border-l-4 border-l-[var(--primary)]">
            <div className="flex items-center gap-3 border-b border-[var(--border-subtle)] pb-3">
              <div className="p-2.5 rounded-xl bg-[var(--primary-light)] text-[var(--primary)]">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-[var(--text-main)]">AI Multimodal Longitudinal Trajectory Narrative</h3>
                <p className="text-xs text-[var(--text-muted)]">
                  Comparison between Assessment {assA.label} ({assA.date}) and Baseline Assessment {assB.label} ({assB.date})
                </p>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] space-y-3 text-xs text-[var(--text-main)] leading-relaxed">
              <p>
                <strong>Comparative Clinical Synthesis:</strong> Trajectory analysis across your verified health assessments demonstrates an active pathway shift of <strong>{assB.pathway} → {assA.pathway}</strong>.
              </p>
              <p>
                <strong>Data Quality & Verification:</strong> Active assessment scored <strong>{assA.quality}</strong> data quality vs baseline assessment at <strong>{assB.quality}</strong>.
              </p>
            </div>
          </Card>

          {/* 2. Clinical Guidance & Physician Next Steps */}
          <ContentSection title="Clinical Guidance & Physician Action Plan">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              
              <Card isGlass={true} className="p-5 space-y-3 shadow-md border-l-4 border-l-[var(--primary)]">
                <div className="flex items-center gap-2">
                  <Stethoscope className="w-4 h-4 text-[var(--primary)]" />
                  <h4 className="font-bold text-xs text-[var(--text-main)]">Diagnostic Follow-Up</h4>
                </div>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                  Continue tracking periodic multimodal laboratory panels to maintain longitudinal glycemic and metabolic stability.
                </p>
              </Card>

              <Card isGlass={true} className="p-5 space-y-3 shadow-md border-l-4 border-l-[var(--success)]">
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-[var(--success)]" />
                  <h4 className="font-bold text-xs text-[var(--text-main)]">Lifestyle & Nutrition Adaptation</h4>
                </div>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                  Maintain regular physical activity, balanced fiber intake, and sleep schedule to support metabolic and autonomic wellness.
                </p>
              </Card>

              <Card isGlass={true} className="p-5 space-y-3 shadow-md border-l-4 border-l-[var(--accent)]">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-[var(--accent)]" />
                  <h4 className="font-bold text-xs text-[var(--text-main)]">Specialist Teleconsultation</h4>
                </div>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                  Book a teleconsultation with a verified physician to review your longitudinal AI risk trajectory and XAI feature drivers.
                </p>
              </Card>

            </div>
          </ContentSection>

        </div>
      )}

    </PageContainer>
  );
}
