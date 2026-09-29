import React, { useState, useEffect } from 'react';
import {
  FileText, History, Download, Trash2, Calendar, Activity, GitCompare,
  TrendingUp, Eye, ShieldCheck, Database, AlertTriangle, CheckCircle2,
  HelpCircle, RefreshCw, X, ChevronRight, Layers, ArrowRight, Dna, Watch,
  Sparkles, Filter, Check, ArrowUpRight, ArrowDownRight, Minus
} from 'lucide-react';
import {
  ResponsiveContainer, AreaChart, Area, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid
} from 'recharts';
import {
  Button, Card, CardHeader, CardBody, CardFooter, Badge,
  ProgressBar, Table, TableRow, TableCell, Modal, Tabs, Input, EmptyState, Alert
} from '../components/ui';
import { PageContainer, PageHeader, ContentSection } from '../components/layout';
import { fetchPatientRecords, fetchRecordDetail, exportRecord, deleteRecord } from '../api/client';
import { classifyBiomarker } from '../utils/clinicalRanges';

export default function HealthRecordsPage({ currentUser, session, predictionData, onStartAnalysis, onShareWithDoctor, onClearAssessment }) {
  const [activeTab, setActiveTab] = useState('history'); // 'history' | 'compare' | 'trends'
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);

  // Selected records for comparison (max 2)
  const [selectedForCompare, setSelectedForCompare] = useState([]);

  // Detail Modal state
  const [selectedDetailRecord, setSelectedDetailRecord] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Delete Modal state
  const [recordToDelete, setRecordToDelete] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Trends Tab state
  const [trendCategory, setTrendCategory] = useState('all'); // 'all' | 'glycemic' | 'cardio' | 'hepatic' | 'scores'
  const [featuredMetricKey, setFeaturedMetricKey] = useState('clinical.Fasting_Blood_Glucose');

  useEffect(() => {
    loadRecords();
  }, []);

  const loadRecords = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await fetchPatientRecords();
      const allRecs = data.records || [];
      const userRecs = allRecs.filter(r => 
        (r.user_id && r.user_id === currentUser?.user_id) ||
        (r.patient_id && r.patient_id === currentUser?.user_id) ||
        (r.user_email && r.user_email.toLowerCase() === currentUser?.email?.toLowerCase()) ||
        (r.email && r.email.toLowerCase() === currentUser?.email?.toLowerCase())
      );
      setRecords(userRecs);
    } catch (err) {
      setErrorMsg('Failed to load health records history.');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDetail = async (recordId) => {
    setDetailLoading(true);
    try {
      const detail = await fetchRecordDetail(recordId);
      setSelectedDetailRecord(detail);
    } catch (err) {
      alert(err.message || 'Failed to load record detail snapshot.');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleExport = async (recordId, e) => {
    if (e) e.stopPropagation();
    try {
      await exportRecord(recordId);
    } catch (err) {
      alert(err.message || 'Failed to export health record.');
    }
  };

  const handleDeleteConfirm = async () => {
    if (!recordToDelete) return;
    setDeleteLoading(true);
    try {
      await deleteRecord(recordToDelete.record_id);
      setRecords((prev) => prev.filter((r) => r.record_id !== recordToDelete.record_id));
      
      // Perform side-effect outside the state updater function
      if (records.length === 1 && records[0].record_id === recordToDelete.record_id && onClearAssessment) {
        onClearAssessment();
      }
      setSelectedForCompare((prev) => prev.filter((id) => id !== recordToDelete.record_id));
      setRecordToDelete(null);
      if (selectedDetailRecord && selectedDetailRecord.record_id === recordToDelete.record_id) {
        setSelectedDetailRecord(null);
      }
    } catch (err) {
      alert(err.message || 'Failed to delete health record.');
    } finally {
      setDeleteLoading(false);
    }
  };

  const toggleSelectForCompare = (recordId) => {
    if (selectedForCompare.includes(recordId)) {
      setSelectedForCompare((prev) => prev.filter((id) => id !== recordId));
    } else {
      if (selectedForCompare.length >= 2) {
        setSelectedForCompare([selectedForCompare[1], recordId]);
      } else {
        setSelectedForCompare((prev) => [...prev, recordId]);
      }
    }
  };

  // Helper for safe risk percentage calculation (fixes NaN%)
  const getProbPct = (info) => {
    if (!info) return '0%';
    const val = info.calibrated_probability ?? info.probability ?? info.final_fusion_probability ?? info.risk_score ?? 0;
    if (typeof val === 'number' && !isNaN(val)) {
      return `${Math.round(val * 100)}%`;
    }
    return '0%';
  };

  const getRiskVariant = (info) => {
    const val = info?.calibrated_probability ?? info?.probability ?? info?.final_fusion_probability ?? info?.risk_score ?? 0;
    if (val >= 0.5) return 'danger';
    if (val >= 0.3) return 'warning';
    return 'success';
  };

  // Metric extraction helper for Comparison & Trends
  const extractNumericVal = (record, keyPath) => {
    if (!record) return null;
    const [category, key] = keyPath.split('.');

    const cf = record.confirmed_features || {};
    if (category in cf && cf[category] && key in cf[category]) {
      const raw = cf[category][key];
      if (raw !== null && raw !== undefined && raw !== '' && !isNaN(raw)) {
        return parseFloat(raw);
      }
    }

    if (category === 'disease_outcomes') {
      const outcomes = record.prediction_snapshot?.disease_outcomes || record.prediction_snapshot?.predictions || {};
      if (key in outcomes) {
        const prob = outcomes[key]?.calibrated_probability ?? outcomes[key]?.probability ?? outcomes[key]?.final_fusion_probability;
        if (prob !== undefined && prob !== null && !isNaN(prob)) {
          return parseFloat((prob * 100).toFixed(1));
        }
      }
    }

    return null;
  };

  const trendMetricsList = [
    { label: 'Fasting Blood Glucose', path: 'clinical.Fasting_Blood_Glucose', unit: 'mg/dL', category: 'glycemic', targetRange: '70 – 99 mg/dL', color: '#06b6d4', icon: Activity },
    { label: 'HbA1c', path: 'clinical.HbA1c', unit: '%', category: 'glycemic', targetRange: '< 5.7 %', color: '#3b82f6', icon: FileText },
    { label: 'Body Mass Index (BMI)', path: 'clinical.BMI', unit: 'kg/m²', category: 'glycemic', targetRange: '18.5 – 24.9 kg/m²', color: '#8b5cf6', icon: Activity },
    { label: 'Waist Circumference', path: 'clinical.Waist_Circumference_cm', unit: 'cm', category: 'glycemic', targetRange: '< 94 cm', color: '#ec4899', icon: Activity },
    { label: 'Systolic Blood Pressure', path: 'clinical.Systolic_BP', unit: 'mmHg', category: 'cardio', targetRange: '< 120 mmHg', color: '#ef4444', icon: Activity },
    { label: 'Diastolic Blood Pressure', path: 'clinical.Diastolic_BP', unit: 'mmHg', category: 'cardio', targetRange: '< 80 mmHg', color: '#f97316', icon: Activity },
    { label: 'Triglycerides', path: 'clinical.Triglycerides', unit: 'mg/dL', category: 'cardio', targetRange: '< 150 mg/dL', color: '#eab308', icon: FileText },
    { label: 'LDL Cholesterol', path: 'clinical.LDL_Cholesterol', unit: 'mg/dL', category: 'cardio', targetRange: '< 100 mg/dL', color: '#f59e0b', icon: FileText },
    { label: 'HDL Cholesterol', path: 'clinical.HDL_Cholesterol', unit: 'mg/dL', category: 'cardio', targetRange: '> 40 mg/dL', color: '#10b981', icon: FileText },
    { label: 'ALT Liver Enzyme', path: 'clinical.ALT', unit: 'U/L', category: 'hepatic', targetRange: '7 – 35 U/L', color: '#a855f7', icon: Activity },
    { label: 'AST Liver Enzyme', path: 'clinical.AST', unit: 'U/L', category: 'hepatic', targetRange: '8 – 40 U/L', color: '#6366f1', icon: Activity },
    { label: 'Type 2 Diabetes Screening Risk', path: 'disease_outcomes.Type2_Diabetes', unit: '%', category: 'scores', targetRange: '< 30%', color: '#ef4444', icon: TrendingUp },
    { label: 'Prediabetes Risk Score', path: 'disease_outcomes.Prediabetes', unit: '%', category: 'scores', targetRange: '< 30%', color: '#f97316', icon: TrendingUp },
    { label: 'Obesity Risk Score', path: 'disease_outcomes.High_Adiposity_Risk', unit: '%', category: 'scores', targetRange: '< 30%', color: '#8b5cf6', icon: TrendingUp },
    { label: 'Metabolic Syndrome Risk Score', path: 'disease_outcomes.Metabolic_Syndrome', unit: '%', category: 'scores', targetRange: '< 30%', color: '#eab308', icon: TrendingUp },
    { label: 'NAFLD Liver Health Risk', path: 'disease_outcomes.NAFLD', unit: '%', category: 'scores', targetRange: '< 30%', color: '#10b981', icon: TrendingUp },
  ];

  const sortedChronologicalRecords = [...records].sort(
    (a, b) => new Date(a.created_at) - new Date(b.created_at)
  );

  // Custom Recharts Glassmorphism Tooltip
  const CustomRechartsTooltip = ({ active, payload, label, unit }) => {
    if (active && payload && payload.length) {
      return (
        <div className="p-3 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-medium)] shadow-xl text-xs space-y-1">
          <p className="font-mono text-[10px] text-[var(--text-muted)]">{label}</p>
          <p className="font-bold font-mono text-xs text-[var(--text-main)]">
            Measured: <span className="text-[var(--primary)] font-extrabold">{payload[0].value} {unit}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <PageContainer className="space-y-8">
      {/* Header Banner */}
      <PageHeader
        title="Persistent Health Records & History"
        description="Longitudinal archive of your multimodal health assessments, diagnostic snapshots, and interactive trend charts."
        badge={`Archived Records: ${records.length}`}
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant={activeTab === 'history' ? 'primary' : 'outline'}
              size="sm"
              leftIcon={<History className="w-4 h-4" />}
              onClick={() => setActiveTab('history')}
            >
              History ({records.length})
            </Button>
            <Button
              variant={activeTab === 'compare' ? 'primary' : 'outline'}
              size="sm"
              disabled={records.length < 2}
              leftIcon={<GitCompare className="w-4 h-4" />}
              onClick={() => setActiveTab('compare')}
            >
              Compare ({selectedForCompare.length}/2)
            </Button>
            <Button
              variant={activeTab === 'trends' ? 'primary' : 'outline'}
              size="sm"
              disabled={records.length === 0}
              leftIcon={<TrendingUp className="w-4 h-4" />}
              onClick={() => setActiveTab('trends')}
            >
              Interactive Trends
            </Button>
          </div>
        }
      />

      {loading ? (
        <Card isGlass={true} className="p-12 text-center space-y-3">
          <RefreshCw className="w-8 h-8 spin text-[var(--primary)] mx-auto" />
          <p className="text-sm text-[var(--text-muted)]">Loading persistent health records...</p>
        </Card>
      ) : errorMsg ? (
        <Alert variant="danger" title="Error Loading Records">
          {errorMsg}
          <div className="mt-3">
            <Button variant="outline" size="sm" onClick={loadRecords}>Retry</Button>
          </div>
        </Alert>
      ) : records.length === 0 ? (
        <Card isGlass={true} className="p-12 text-center space-y-4">
          <Database className="w-12 h-12 text-[var(--primary)] mx-auto opacity-80" />
          <h3 className="text-lg font-bold text-[var(--text-main)]">No Persistent Health Records Found</h3>
          <p className="text-xs text-[var(--text-muted)] max-w-md mx-auto leading-relaxed">
            You have not completed any health assessments yet. Run your first analysis in the Intake workspace to build your longitudinal clinical record.
          </p>
        </Card>
      ) : (
        <>
          {/* TAB 1: HISTORY LIST */}
          {activeTab === 'history' && (
            <div className="space-y-4">
              {records.map((record) => {
                const isSelected = selectedForCompare.includes(record.record_id);
                const outcomes = record.prediction_snapshot?.disease_outcomes || record.prediction_snapshot?.predictions || {};
                const outcomeKeys = Object.keys(outcomes);
                const dqScore = record.data_quality_score != null ? Math.round(record.data_quality_score * (record.data_quality_score <= 1 ? 100 : 1)) : 100;

                return (
                  <Card
                    key={record.record_id}
                    isGlass={true}
                    className={`p-6 transition-all border-l-4 ${
                      record.status === 'REPORT_READY' ? 'border-l-[var(--success)]' :
                      record.status === 'XAI_READY' ? 'border-l-[var(--primary)]' : 'border-l-[var(--warning)]'
                    }`}
                  >
                    <div className="flex items-start justify-between flex-wrap gap-4">
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 flex-wrap">
                          <strong className="text-sm font-extrabold text-[var(--text-main)]">
                            Record #{record.record_id}
                          </strong>
                          <Badge variant="outline" size="sm">
                            <Calendar className="w-3 h-3 mr-1 inline" />
                            {new Date(record.created_at).toLocaleString()}
                          </Badge>
                          <Badge variant="primary" size="sm">
                            Pipeline {record.pipeline_version || 'v4.0'}
                          </Badge>
                          <Badge variant="secondary" size="sm">
                            Pathway {record.effective_pathway || record.pathway_used || 'C'}
                          </Badge>
                          <Badge
                            variant={record.status === 'REPORT_READY' ? 'success' : record.status === 'XAI_READY' ? 'primary' : 'warning'}
                            size="sm"
                          >
                            {record.status}
                          </Badge>
                        </div>

                        <div className="flex items-center gap-3 text-xs text-[var(--text-muted)] flex-wrap font-mono">
                          <span>Data Quality: <strong className="text-[var(--success)]">{dqScore}%</strong></span>
                          <span>•</span>
                          <span>
                            Modalities:{' '}
                            {(record.active_modalities || ['clinical']).map((m) => (
                              <Badge key={m} variant="outline" size="sm" className="ml-1 capitalize">
                                {m}
                              </Badge>
                            ))}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Button
                          variant={isSelected ? 'primary' : 'outline'}
                          size="sm"
                          onClick={() => toggleSelectForCompare(record.record_id)}
                        >
                          {isSelected ? '✓ Selected for Compare' : '+ Compare'}
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          leftIcon={<Eye className="w-4 h-4" />}
                          onClick={() => handleOpenDetail(record.record_id)}
                        >
                          View Snapshot
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          title="Export Safe JSON"
                          onClick={(e) => handleExport(record.record_id, e)}
                        >
                          <Download className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="!text-[var(--danger)] hover:bg-red-50 dark:hover:bg-red-900/20"
                          onClick={() => setRecordToDelete(record)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}

          {/* TAB 2: COMPARE RECORDS */}
          {activeTab === 'compare' && (
            <Card isGlass={true} className="p-6 space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-extrabold text-[var(--text-main)]">Side-by-Side Assessment Comparison</h3>
                  <p className="text-xs text-[var(--text-muted)]">Comparing selected historical snapshots ({selectedForCompare.length}/2 selected)</p>
                </div>
                {selectedForCompare.length < 2 && (
                  <Badge variant="warning" size="sm">Select 2 records in History tab to compare</Badge>
                )}
              </div>

              {selectedForCompare.length === 2 && (() => {
                const recA = records.find((r) => r.record_id === selectedForCompare[0]);
                const recB = records.find((r) => r.record_id === selectedForCompare[1]);

                if (!recA || !recB) return null;

                return (
                  <div className="space-y-6">
                    <Table headers={['Biomarker / Metric', `Record #${recA.record_id}`, `Record #${recB.record_id}`, 'Delta Shift']}>
                      {[
                        { name: 'Fasting Blood Glucose', path: 'clinical.Fasting_Blood_Glucose', unit: 'mg/dL' },
                        { name: 'HbA1c', path: 'clinical.HbA1c', unit: '%' },
                        { name: 'BMI', path: 'clinical.BMI', unit: 'kg/m²' },
                        { name: 'Systolic BP', path: 'clinical.Systolic_BP', unit: 'mmHg' },
                        { name: 'Diastolic BP', path: 'clinical.Diastolic_BP', unit: 'mmHg' },
                        { name: 'Triglycerides', path: 'clinical.Triglycerides', unit: 'mg/dL' },
                        { name: 'LDL Cholesterol', path: 'clinical.LDL_Cholesterol', unit: 'mg/dL' },
                        { name: 'HDL Cholesterol', path: 'clinical.HDL_Cholesterol', unit: 'mg/dL' },
                        { name: 'ALT Liver Enzyme', path: 'clinical.ALT', unit: 'U/L' },
                        { name: 'AST Liver Enzyme', path: 'clinical.AST', unit: 'U/L' },
                      ].map((item) => {
                        const valA = extractNumericVal(recA, item.path);
                        const valB = extractNumericVal(recB, item.path);
                        const delta = (valA != null && valB != null) ? (valB - valA).toFixed(1) : null;

                        return (
                          <TableRow key={item.name}>
                            <TableCell className="font-semibold text-xs">{item.name} ({item.unit})</TableCell>
                            <TableCell className="font-mono text-xs">{valA != null ? `${valA} ${item.unit}` : 'N/A'}</TableCell>
                            <TableCell className="font-mono text-xs">{valB != null ? `${valB} ${item.unit}` : 'N/A'}</TableCell>
                            <TableCell className="font-mono text-xs font-bold">
                              {delta != null ? (
                                <span className={Number(delta) > 0 ? 'text-[var(--danger)]' : Number(delta) < 0 ? 'text-[var(--success)]' : 'text-[var(--text-muted)]'}>
                                  {Number(delta) > 0 ? `+${delta}` : delta} {item.unit}
                                </span>
                              ) : 'N/A'}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </Table>
                  </div>
                );
              })()}
            </Card>
          )}

          {/* TAB 3: INTERACTIVE TRENDS & RECHARTS GRAPH ENGINE */}
          {activeTab === 'trends' && (
            <div className="space-y-6">
              {/* Category Filter Pills & Controls */}
              <Card isGlass={true} className="p-5 space-y-4">
                <div className="flex items-center justify-between flex-wrap gap-3 border-b border-[var(--border-subtle)] pb-3">
                  <div>
                    <h3 className="text-base font-extrabold text-[var(--text-main)] flex items-center gap-2">
                      <TrendingUp className="w-5 h-5 text-[var(--primary)]" />
                      Longitudinal Biomarker Chronology & Trends
                    </h3>
                    <p className="text-xs text-[var(--text-muted)]">
                      Interactive chart engine tracking your biometrics and risk trajectory across historical assessments.
                    </p>
                  </div>
                  <Badge variant="primary" size="sm">
                    {sortedChronologicalRecords.length} Historical Data Points
                  </Badge>
                </div>

                {/* Category Pills */}
                <div className="flex items-center gap-2 overflow-x-auto pb-1">
                  {[
                    { id: 'all', label: 'All Biometrics' },
                    { id: 'glycemic', label: '🩸 Glycemic & Metabolic' },
                    { id: 'cardio', label: '❤️ Cardiovascular' },
                    { id: 'hepatic', label: '🧪 Hepatic / Liver' },
                    { id: 'scores', label: '📈 Disease Risk Scores' },
                  ].map((cat) => (
                    <button
                      key={cat.id}
                      onClick={() => {
                        setTrendCategory(cat.id);
                        const firstInCat = trendMetricsList.find(m => cat.id === 'all' || m.category === cat.id);
                        if (firstInCat) {
                          setFeaturedMetricKey(firstInCat.path);
                        }
                      }}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold font-mono transition-all ${
                        trendCategory === cat.id
                          ? 'bg-[var(--primary)] text-white shadow-sm'
                          : 'bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-[var(--text-muted)] hover:text-[var(--text-main)]'
                      }`}
                    >
                      {cat.label}
                    </button>
                  ))}
                </div>
              </Card>

              {/* FEATURED HERO RECHARTS AREA CHART */}
              {(() => {
                const categoryMetrics = trendMetricsList.filter(m => trendCategory === 'all' || m.category === trendCategory);
                const featuredMetric = categoryMetrics.find(m => m.path === featuredMetricKey) || categoryMetrics[0] || trendMetricsList[0];
                const heroPoints = sortedChronologicalRecords.map((r) => ({
                  date: new Date(r.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
                  val: extractNumericVal(r, featuredMetric.path),
                  fullDate: new Date(r.created_at).toLocaleString(),
                })).filter((dp) => dp.val !== null);

                if (heroPoints.length === 0) return null;

                const firstVal = heroPoints[0].val;
                const latestVal = heroPoints[heroPoints.length - 1].val;
                const deltaVal = (latestVal - firstVal).toFixed(1);
                const isIncreased = Number(deltaVal) > 0;
                const isDecreased = Number(deltaVal) < 0;

                return (
                  <Card isGlass={true} className="p-6 space-y-4 border-t-4 border-t-[var(--primary)]">
                    <div className="flex items-center justify-between flex-wrap gap-4 border-b border-[var(--border-subtle)] pb-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <Badge variant="primary" size="sm">Featured Trend Analysis</Badge>
                          <span className="text-xs font-mono text-[var(--text-muted)]">Reference Target: {featuredMetric.targetRange}</span>
                        </div>
                        <h3 className="text-lg font-extrabold text-[var(--text-main)] mt-1">
                          {featuredMetric.label} Trend Analysis
                        </h3>
                      </div>

                      <div className="flex items-center gap-4">
                        <div className="text-right font-mono">
                          <span className="text-[10px] text-[var(--text-muted)] block uppercase">Latest Reading</span>
                          <span className="text-2xl font-extrabold text-[var(--text-main)]">
                            {latestVal} <span className="text-xs font-normal text-[var(--text-muted)]">{featuredMetric.unit}</span>
                          </span>
                        </div>

                        <div className={`p-2 rounded-xl border flex items-center gap-1 font-mono text-xs font-bold ${
                          isIncreased ? 'bg-red-50 dark:bg-red-900/20 text-[var(--danger)] border-red-200' :
                          isDecreased ? 'bg-green-50 dark:bg-green-900/20 text-[var(--success)] border-green-200' :
                          'bg-gray-50 text-[var(--text-muted)] border-gray-200'
                        }`}>
                          {isIncreased ? <ArrowUpRight className="w-4 h-4" /> : isDecreased ? <ArrowDownRight className="w-4 h-4" /> : <Minus className="w-4 h-4" />}
                          <span>{Number(deltaVal) > 0 ? `+${deltaVal}` : deltaVal} {featuredMetric.unit}</span>
                        </div>
                      </div>
                    </div>

                    {/* Recharts Hero Area Chart */}
                    <div className="h-64 w-full pt-2">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={heroPoints} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                          <defs>
                            <linearGradient id="heroGradient" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor={featuredMetric.color} stopOpacity={0.4} />
                              <stop offset="95%" stopColor={featuredMetric.color} stopOpacity={0.0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
                          <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                          <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} domain={['auto', 'auto']} />
                          <Tooltip content={<CustomRechartsTooltip unit={featuredMetric.unit} />} />
                          <Area
                            type="monotone"
                            dataKey="val"
                            stroke={featuredMetric.color}
                            strokeWidth={3}
                            fillOpacity={1}
                            fill="url(#heroGradient)"
                            activeDot={{ r: 6, stroke: featuredMetric.color, strokeWidth: 2, fill: '#fff' }}
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </Card>
                );
              })()}

              {/* GRID OF RECHARTS MINI METRIC CARDS */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {trendMetricsList
                  .filter(m => trendCategory === 'all' || m.category === trendCategory)
                  .map((metric) => {
                    const dataPoints = sortedChronologicalRecords.map((r) => ({
                      date: new Date(r.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
                      val: extractNumericVal(r, metric.path),
                    })).filter((dp) => dp.val !== null);

                    if (dataPoints.length === 0) return null;

                    const latestVal = dataPoints[dataPoints.length - 1].val;
                    const firstVal = dataPoints[0].val;
                    const delta = (latestVal - firstVal).toFixed(1);
                    const isSelectedHero = featuredMetricKey === metric.path;

                    return (
                      <Card
                        key={metric.label}
                        isGlass={true}
                        className={`p-4 space-y-3 transition-all hover:shadow-md cursor-pointer ${
                          isSelectedHero ? 'ring-2 ring-[var(--primary)] bg-[var(--primary-light)]/10' : ''
                        }`}
                        onClick={() => setFeaturedMetricKey(metric.path)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <metric.icon className="w-4 h-4" style={{ color: metric.color }} />
                            <strong className="text-xs font-bold text-[var(--text-main)] truncate max-w-[160px]" title={metric.label}>
                              {metric.label}
                            </strong>
                          </div>
                          <Badge variant="outline" size="sm" className="font-mono text-[10px]">
                            {dataPoints.length} point(s)
                          </Badge>
                        </div>

                        <div className="flex items-baseline justify-between pt-1">
                          <div className="font-mono">
                            <span className="text-xl font-extrabold text-[var(--text-main)]">{latestVal}</span>
                            <span className="text-xs text-[var(--text-muted)] ml-1">{metric.unit}</span>
                          </div>

                          {dataPoints.length > 1 && (
                            <span className={`text-xs font-mono font-bold ${
                              Number(delta) > 0 ? 'text-[var(--danger)]' : Number(delta) < 0 ? 'text-[var(--success)]' : 'text-[var(--text-muted)]'
                            }`}>
                              {Number(delta) > 0 ? `+${delta}` : delta} {metric.unit}
                            </span>
                          )}
                        </div>

                        {/* Recharts Mini Area Chart */}
                        <div className="h-28 w-full pt-1">
                          <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={dataPoints} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                              <defs>
                                <linearGradient id={`grad-${metric.label.replace(/\s+/g, '')}`} x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor={metric.color} stopOpacity={0.35} />
                                  <stop offset="95%" stopColor={metric.color} stopOpacity={0.0} />
                                </linearGradient>
                              </defs>
                              <CartesianGrid strokeDasharray="2 2" stroke="var(--border-subtle)" vertical={false} />
                              <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={9} tickLine={false} />
                              <YAxis stroke="var(--text-muted)" fontSize={9} tickLine={false} domain={['auto', 'auto']} />
                              <Tooltip content={<CustomRechartsTooltip unit={metric.unit} />} />
                              <Area
                                type="monotone"
                                dataKey="val"
                                stroke={metric.color}
                                strokeWidth={2}
                                fillOpacity={1}
                                fill={`url(#grad-${metric.label.replace(/\s+/g, '')})`}
                                activeDot={{ r: 4, stroke: metric.color, strokeWidth: 1.5, fill: '#fff' }}
                              />
                            </AreaChart>
                          </ResponsiveContainer>
                        </div>

                        <div className="flex justify-between items-center text-[10px] text-[var(--text-muted)] pt-1 border-t border-[var(--border-subtle)] font-mono">
                          <span>Target: <strong className="text-[var(--text-main)]">{metric.targetRange}</strong></span>
                          <span className="text-[var(--primary)] hover:underline flex items-center gap-0.5">
                            Expand <ChevronRight className="w-3 h-3 inline" />
                          </span>
                        </div>
                      </Card>
                    );
                  })}
              </div>
            </div>
          )}
        </>
      )}

      {/* RECORD SNAPSHOT DETAIL MODAL */}
      {selectedDetailRecord && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedDetailRecord(null)}
          title={`Record Snapshot #${selectedDetailRecord.record_id}`}
          size="lg"
        >
          <div className="space-y-6 text-xs">
            {/* Metadata Summary Header */}
            <div className="p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] flex items-center justify-between flex-wrap gap-2">
              <div>
                <p className="text-[11px] font-mono text-[var(--text-muted)]">
                  Created: <strong>{new Date(selectedDetailRecord.created_at).toLocaleString()}</strong>
                </p>
                <p className="text-[11px] font-mono text-[var(--text-muted)] mt-0.5">
                  Pipeline Version: <strong>{selectedDetailRecord.pipeline_version || 'v4.0'}</strong> • Status: <strong>{selectedDetailRecord.status}</strong>
                </p>
              </div>
              <Badge variant="primary" size="sm">
                Pathway {selectedDetailRecord.effective_pathway || selectedDetailRecord.pathway_used || 'C'}
              </Badge>
            </div>

            {/* Model Estimated Risk Outputs (Fixed NaN%) */}
            <div className="space-y-3">
              <h4 className="text-xs font-extrabold text-[var(--text-main)] uppercase tracking-wider font-mono">
                Model-Estimated Screening Outputs
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {Object.entries(selectedDetailRecord.prediction_snapshot?.disease_outcomes || selectedDetailRecord.prediction_snapshot?.predictions || {}).map(([disease, info]) => {
                  const probPctStr = getProbPct(info);
                  const variant = getRiskVariant(info);
                  const isPositive = (info?.calibrated_probability ?? info?.probability ?? 0) >= 0.5 || info?.final_prediction === 1;

                  return (
                    <div key={disease} className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs text-[var(--text-main)]">{disease.replace(/_/g, ' ')}</span>
                        <Badge variant={variant} size="sm">{isPositive ? 'High Signal' : 'Low Signal'}</Badge>
                      </div>
                      <div className="text-xl font-extrabold font-mono text-[var(--text-main)]">
                        {probPctStr}
                      </div>
                      <p className="text-[10px] text-[var(--text-muted)] font-mono">
                        Risk Level: {info?.risk_level || (isPositive ? 'High' : 'Low')}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Formatted Biomarkers Snapshot (Replaces raw JSON dump) */}
            <div className="space-y-3">
              <h4 className="text-xs font-extrabold text-[var(--text-main)] uppercase tracking-wider font-mono">
                Extracted Biometrics & Verified Inputs
              </h4>

              {(() => {
                const cf = selectedDetailRecord.confirmed_features || {};
                const hasClin = cf.clinical && Object.keys(cf.clinical).length > 0;
                const hasWear = cf.wearable && Object.keys(cf.wearable).length > 0;
                const hasGut = cf.gut && Object.keys(cf.gut).length > 0;

                if (!hasClin && !hasWear && !hasGut) {
                  return (
                    <div className="p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-center text-xs text-[var(--text-muted)]">
                      No raw biometric snapshot stored for this record.
                    </div>
                  );
                }

                return (
                  <div className="space-y-4">
                    {hasClin && (
                      <div className="p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] space-y-2">
                        <div className="flex items-center gap-2 mb-2">
                          <FileText className="w-4 h-4 text-blue-500" />
                          <strong className="text-xs text-[var(--text-main)]">Clinical Lab Biomarkers</strong>
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                          {Object.entries(cf.clinical).map(([k, v]) => (
                            <div key={k} className="p-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                              <span className="text-[10px] text-[var(--text-muted)] block">{k.replace(/_/g, ' ')}</span>
                              <span className="font-mono font-bold text-xs text-[var(--primary)]">{v !== null && v !== undefined ? `${v}` : 'N/A'}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {hasWear && (
                      <div className="p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] space-y-2">
                        <div className="flex items-center gap-2 mb-2">
                          <Watch className="w-4 h-4 text-teal-500" />
                          <strong className="text-xs text-[var(--text-main)]">Wearable Sensor Telemetry</strong>
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                          {Object.entries(cf.wearable).map(([k, v]) => (
                            <div key={k} className="p-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                              <span className="text-[10px] text-[var(--text-muted)] block">{k.replace(/_/g, ' ')}</span>
                              <span className="font-mono font-bold text-xs text-[var(--secondary)]">{v !== null && v !== undefined ? `${v}` : 'N/A'}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {hasGut && (
                      <div className="p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] space-y-2">
                        <div className="flex items-center gap-2 mb-2">
                          <Dna className="w-4 h-4 text-purple-500" />
                          <strong className="text-xs text-[var(--text-main)]">Gut Microbiome Taxa</strong>
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                          {Object.entries(cf.gut).slice(0, 12).map(([k, v]) => (
                            <div key={k} className="p-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                              <span className="text-[10px] text-[var(--text-muted)] block truncate" title={k}>{k.replace(/_/g, ' ')}</span>
                              <span className="font-mono font-bold text-xs text-[var(--accent)]">{v !== null && v !== undefined ? `${v}%` : 'N/A'}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          </div>
        </Modal>
      )}

      {/* DELETE CONFIRMATION MODAL */}
      {recordToDelete && (
        <Modal
          isOpen={true}
          onClose={() => setRecordToDelete(null)}
          title="Confirm Record Deletion"
          size="sm"
        >
          <div className="p-4 text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-red-500/10 text-red-500 flex items-center justify-center mx-auto">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <h4 className="text-sm font-bold text-[var(--text-main)]">Delete Health Record #{recordToDelete.record_id}?</h4>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                This action will permanently purge the biometrics snapshot, risk predictions, and explainability records. This action cannot be undone.
              </p>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <Button
                variant="outline"
                size="md"
                className="flex-1"
                disabled={deleteLoading}
                onClick={() => setRecordToDelete(null)}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                size="md"
                className="flex-1"
                disabled={deleteLoading}
                onClick={handleDeleteConfirm}
              >
                {deleteLoading ? 'Deleting...' : 'Delete Permanently'}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </PageContainer>
  );
}
