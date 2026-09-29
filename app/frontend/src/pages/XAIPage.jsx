import React, { useState, useEffect } from 'react';
import { useLocation, useSearchParams } from 'react-router-dom';
import {
  Brain, RefreshCw, AlertTriangle, ShieldCheck, TrendingUp, TrendingDown,
  Search, Filter, Download, Printer, Copy, Check, ChevronDown, ChevronUp,
  Activity, Watch, Dna, FileText, Info, Sparkles, Layers, ArrowRight, Eye
} from 'lucide-react';
import {
  Button, Card, CardHeader, CardBody, CardFooter, Badge,
  ProgressBar, CircularProgress, Table, TableRow, TableCell, Tabs, Input, EmptyState, Alert
} from '../components/ui';
import { PageContainer, PageHeader, ContentSection } from '../components/layout';
import { fetchXAIV3 } from '../api/client';
import ModalityContributionChart from '../components/ModalityContributionChart';

export default function XAIPage({ session, predictionData, xaiData, setXaiData, initialDisease, onNavigateReport }) {
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const targetFromRoute = location.state?.disease || searchParams.get('disease');

  const [selectedDisease, setSelectedDisease] = useState(targetFromRoute || initialDisease || 'Type2_Diabetes');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [modalityFilter, setModalityFilter] = useState('all'); // 'all' | 'clinical' | 'wearable' | 'gut'
  const [vizMode, setVizMode] = useState('barchart'); // 'barchart' | 'waterfall' | 'force' | 'table'
  const [showAllDrivers, setShowAllDrivers] = useState(false);
  const [copied, setCopied] = useState(false);
  const [selectedComparison, setSelectedComparison] = useState('none');

  const diseases = React.useMemo(() => [
    { key: 'Type2_Diabetes', title: 'Type 2 Diabetes' },
    { key: 'Prediabetes', title: 'Prediabetes Risk' },
    { key: 'High_Adiposity_Risk', title: 'Adiposity & Obesity' },
    { key: 'Metabolic_Syndrome', title: 'Metabolic Syndrome' },
    { key: 'NAFLD', title: 'NAFLD Liver Health' },
  ], []);

  const displayDiseases = React.useMemo(() => {
    if (!predictionData) return diseases;
    const outcomes = predictionData.disease_outcomes || predictionData.predictions || {};
    const getProb = (obj, k) => obj[k]?.calibrated_probability ?? obj[k]?.probability ?? (obj[k]?.risk_score || 0);
    const t2dProb = getProb(outcomes, 'Type2_Diabetes');
    const preProb = getProb(outcomes, 'Prediabetes');
    const t2dIsPositive = (outcomes['Type2_Diabetes']?.risk_level?.toLowerCase() === 'positive') || (t2dProb >= 0.4);

    return diseases.filter(d => {
      if (d.key === 'Prediabetes' && (t2dIsPositive || t2dProb > preProb)) return false;
      if (d.key === 'Type2_Diabetes' && !t2dIsPositive && preProb > t2dProb) return false;
      return true;
    });
  }, [predictionData, diseases]);

  useEffect(() => {
    if (predictionData && !displayDiseases.some(d => d.key === selectedDisease)) {
      setSelectedDisease(displayDiseases[0].key);
    }
  }, [predictionData, displayDiseases, selectedDisease]);

  useEffect(() => {
    if (targetFromRoute) {
      setSelectedDisease(targetFromRoute);
    } else if (initialDisease) {
      setSelectedDisease(initialDisease);
    }
  }, [targetFromRoute, initialDisease]);

  useEffect(() => {
    loadXAIV3(selectedDisease);
  }, [selectedDisease, session, predictionData]);

  const loadXAIV3 = async (diseaseKey) => {
    const clinData = session?.confirmed_features?.clinical 
      || predictionData?.confirmed_features?.clinical 
      || predictionData?.clinical_features 
      || predictionData?.clinical_data 
      || predictionData?.input_data?.clinical 
      || predictionData?.expert_outputs?.clinical?.raw_input 
      || (typeof predictionData?.expert_outputs?.clinical === 'object' ? predictionData?.expert_outputs?.clinical : null);

    const wearData = session?.confirmed_features?.wearable 
      || predictionData?.confirmed_features?.wearable 
      || predictionData?.wearable_features 
      || predictionData?.wearable_data 
      || predictionData?.input_data?.wearable 
      || predictionData?.expert_outputs?.wearable?.raw_input 
      || (typeof predictionData?.expert_outputs?.wearable === 'object' ? predictionData?.expert_outputs?.wearable : null);

    const gutData = session?.confirmed_features?.gut 
      || predictionData?.confirmed_features?.gut 
      || predictionData?.gut_features 
      || predictionData?.gut_data 
      || predictionData?.input_data?.gut 
      || predictionData?.expert_outputs?.gut?.raw_input 
      || (typeof predictionData?.expert_outputs?.gut === 'object' ? predictionData?.expert_outputs?.gut : null);

    const cleanClin = (clinData && Object.keys(clinData).length > 0) ? clinData : null;
    const cleanWear = (wearData && Object.keys(wearData).length > 0) ? wearData : null;
    const cleanGut = (gutData && Object.keys(gutData).length > 0) ? gutData : null;

    if (!cleanClin && !cleanWear && !cleanGut) {
      if (setXaiData) setXaiData(null);
      return;
    }

    const payload = session?.v3_payload || {
      patient_id: session?.session_id || predictionData?.patient_id || 'P_USER_001',
      clinical_data: cleanClin,
      wearable_data: cleanWear,
      gut_data: cleanGut,
    };

    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetchXAIV3(payload, diseaseKey);
      if (setXaiData) {
        setXaiData(res);
      }
    } catch (err) {
      setErrorMsg(err.message || 'Explainability attributions could not be generated.');
    } finally {
      setLoading(false);
    }
  };

  const attributions = xaiData?.attributions || xaiData?.attributions_by_modality || (xaiData?.clinical || xaiData?.wearable ? xaiData : {});
  const causalityDisclaimer = xaiData?.causality_disclaimer || "SHAP feature importances reflect statistical model predictor contributions, NOT biological causality.";

  // Extract all drivers across active modalities into a unified list
  const extractAllFeatures = () => {
    const list = [];
    ['clinical', 'wearable', 'gut'].forEach((mod) => {
      const modObj = attributions[mod] || {};
      const feats = modObj.all_features || modObj.top_risk_drivers || modObj.drivers || [];
      feats.forEach((f) => {
        const shapVal = typeof f === 'number' ? f : (f.shap_attribution ?? f.shap_value ?? f.attribution ?? f.shap ?? 0);
        const fName = typeof f === 'string' ? f : (f.feature_name || f.feature || f.name || 'Feature');
        const fVal = typeof f === 'object' && f !== null ? (f.value ?? f.observed_value ?? f.raw_value ?? 'N/A') : 'N/A';
        list.push({
          modality: mod,
          name: String(fName).replace(/_/g, ' '),
          value: typeof fVal === 'object' ? JSON.stringify(fVal) : String(fVal),
          shapVal: Number(shapVal) || 0,
          absShap: Math.abs(Number(shapVal) || 0),
          direction: (Number(shapVal) || 0) >= 0 ? 'Increases Risk' : 'Decreases Risk',
          range: f.range || f.reference_range || 'Standard'
        });
      });
    });

    return list.sort((a, b) => b.absShap - a.absShap);
  };

  const formatShap = (val) => {
    const num = Number(val) || 0;
    const abs = Math.abs(num);
    const formatted = abs < 0.01 && abs > 0 ? num.toFixed(4) : num.toFixed(3);
    return num >= 0 ? `+${formatted}` : formatted;
  };

  const allDrivers = extractAllFeatures();

  // Filter drivers by search and modality
  const filteredDrivers = allDrivers.filter((d) => {
    const matchesSearch = d.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesModality = modalityFilter === 'all' || d.modality === modalityFilter;
    return matchesSearch && matchesModality;
  });

  const displayedDrivers = showAllDrivers ? filteredDrivers : filteredDrivers.slice(0, 5);

  // Derive prediction meta for active disease
  const diseaseOutcome = predictionData?.disease_outcomes?.[selectedDisease] || predictionData?.predictions?.[selectedDisease] || {};
  const probVal = diseaseOutcome.probability !== undefined ? diseaseOutcome.probability : (diseaseOutcome.calibrated_probability !== undefined ? diseaseOutcome.calibrated_probability : 0);
  const probPct = Math.round(probVal * 100);
  const riskLvl = diseaseOutcome.risk_level || (probPct >= 60 ? 'High' : probPct >= 30 ? 'Moderate' : 'Low');

  // Copy Summary Handler
  const handleCopySummary = () => {
    const text = `TeleMed TreeSHAP Driver Analysis Report\nTarget: ${selectedDisease}\nProbability: ${probPct}%\nRisk Level: ${riskLvl}\nTop Risk Driver: ${allDrivers[0]?.name || 'N/A'}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!predictionData) {
    return (
      <PageContainer className="space-y-8">
        <PageHeader
          title="TreeSHAP Explainability Workspace"
          description="Directional Feature Attributions, Model Attribution Matrices & Clinical Explainability"
          badge="Explainability Engine"
        />
        <Card isGlass={true} className="p-8 text-center space-y-4">
          <Brain className="w-12 h-12 text-[var(--primary)] mx-auto" />
          <h3 className="text-lg font-bold text-[var(--text-main)]">No Active Health Assessment Found</h3>
          <p className="text-xs text-[var(--text-muted)] max-w-md mx-auto">
            Please run a multimodal health assessment in the Intake Workspace to generate TreeSHAP explainability drivers.
          </p>
          <Button variant="primary" size="md" onClick={() => onNavigateReport ? onNavigateReport() : null}>
            Start New Assessment →
          </Button>
        </Card>
      </PageContainer>
    );
  }

  return (
    <PageContainer className="space-y-12">
      {/* Page Header */}
      <PageHeader
        title="TreeSHAP Explainability Workspace"
        description="Directional Feature Attributions, Model Attribution Matrices & Clinical Explainability"
        badge="Phase 1 SHAP Engine Active"
        actions={
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm" leftIcon={<Copy className="w-4 h-4" />} onClick={handleCopySummary}>
              {copied ? 'Copied!' : 'Copy Summary'}
            </Button>
            <Button variant="outline" size="sm" leftIcon={<Printer className="w-4 h-4" />} onClick={() => window.print()}>
              Print Report
            </Button>
            <Button variant="primary" size="sm" leftIcon={<Download className="w-4 h-4" />} onClick={onNavigateReport}>
              Full Report →
            </Button>
          </div>
        }
      />

      {/* Target Disease Selector Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto no-scrollbar pb-2">
        {displayDiseases.map((d) => (
          <Button
            key={d.key}
            variant={selectedDisease === d.key ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setSelectedDisease(d.key)}
          >
            {d.title}
          </Button>
        ))}
      </div>

      {/* SECTION 1: PREDICTION SUMMARY HERO */}
      <Card isGlass={true} className="p-6 bg-gradient-to-r from-[var(--bg-surface)] to-[var(--bg-primary)] border border-[var(--border-medium)]">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-center">
          <div className="md:col-span-2 space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant={riskLvl === 'High' ? 'danger' : riskLvl === 'Moderate' ? 'warning' : 'success'} size="sm">
                {riskLvl} Risk Level
              </Badge>
              <Badge variant="accent" size="sm">Pathway: {predictionData?.effective_pathway || 'C+W+G'}</Badge>
            </div>
            <h3 className="text-xl font-extrabold text-[var(--text-main)]">{selectedDisease.replace(/_/g, ' ')} Model Prediction</h3>
            <p className="text-xs text-[var(--text-muted)]">
              TeleMed Multimodal Risk Model prediction based on confirmed clinical lab, wearable telemetry, and gut microbiome data.
            </p>
          </div>

          <div className="flex flex-col items-center justify-center border-y md:border-y-0 md:border-x border-[var(--border-subtle)] py-4 md:py-0 md:px-6">
            <CircularProgress value={probPct} size={72} strokeWidth={7} variant={riskLvl === 'High' ? 'danger' : riskLvl === 'Moderate' ? 'warning' : 'success'} />
            <span className="text-[11px] font-mono font-bold text-[var(--text-muted)] mt-1.5">{probPct}% Risk Probability</span>
          </div>

          <div className="space-y-2 text-right">
            <div className="text-xs font-mono text-[var(--text-muted)]">Data Quality Index: <strong className="text-[var(--success)]">{Math.round((predictionData?.data_quality_score || 0.92) * 100)}%</strong></div>
            <div className="text-xs font-mono text-[var(--text-muted)]">Total Active Drivers: <strong className="text-[var(--primary)]">{allDrivers.length} Features</strong></div>
            <div className="text-xs font-mono text-[var(--text-muted)]">Causality Note: <strong className="text-[var(--text-main)]">Statistical Attribution</strong></div>
          </div>
        </div>
      </Card>

      {/* SECTION 1.5: ASSESSMENT PROVENANCE — MODALITY CONTRIBUTION */}
      <ModalityContributionChart attributions={attributions} selectedDisease={selectedDisease} />


      {/* SECTION 2: GLOBAL FEATURE IMPORTANCE (HORIZONTAL SHAP RANKING BARS) */}
      <ContentSection title="Global Feature Importance Ranking" subtitle="Top statistical feature contributors increasing (red) or decreasing (green) risk score">
        <Card isGlass={true} className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xs font-semibold text-[var(--text-muted)]">Modality Filter:</span>
              {['all', 'clinical', 'wearable', 'gut'].map((mod) => (
                <Button
                  key={mod}
                  variant={modalityFilter === mod ? 'primary' : 'ghost'}
                  size="sm"
                  className="!px-3 !py-1 text-xs capitalize"
                  onClick={() => setModalityFilter(mod)}
                >
                  {mod}
                </Button>
              ))}
            </div>
          </div>

          <div className="flex justify-between items-center bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-lg p-2 px-4 shadow-sm mb-2 mt-4">
            <span className="text-xs font-semibold text-[var(--text-muted)]">
              Showing <strong className="text-[var(--text-main)]">{displayedDrivers.length}</strong> of <strong className="text-[var(--text-main)]">{filteredDrivers.length}</strong> items
            </span>
            <button
              onClick={() => setShowAllDrivers(prev => !prev)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold text-[var(--primary)] bg-[var(--primary)]/5 hover:bg-[var(--primary)]/15 transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/20"
            >
              {showAllDrivers ? (
                <>Show Less <ChevronUp className="w-4 h-4" /></>
              ) : (
                <>Show All ({filteredDrivers.length - 5} More) <ChevronDown className="w-4 h-4" /></>
              )}
            </button>
          </div>

          {/* Bidirectional Bar Chart — Risk (right/red) vs Protective (left/green) */}
          <div className="space-y-3 pt-2">
            {displayedDrivers.map((d, idx) => {
              const maxAbs = Math.max(...allDrivers.map(x => x.absShap), 0.2);
              const barWidth = Math.min(50, Math.round((d.absShap / maxAbs) * 50));
              const isRiskIncrease = d.shapVal >= 0;

              return (
                <div key={idx} className="space-y-1.5 p-2.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[var(--text-dim)] text-[11px]">#{idx + 1}</span>
                      <span className="font-bold text-[var(--text-main)] truncate max-w-[140px] sm:max-w-none" title={d.name}>{d.name}</span>
                      <Badge variant={d.modality === 'clinical' ? 'primary' : d.modality === 'wearable' ? 'secondary' : 'accent'} size="sm">
                        {d.modality}
                      </Badge>
                      <span className="text-[11px] font-mono text-[var(--text-muted)]">Observed: {d.value}</span>
                    </div>

                    <div className="flex items-center gap-2 font-mono text-xs">
                      <span className={isRiskIncrease ? 'text-[var(--danger)] font-bold' : 'text-[var(--success)] font-bold'}>
                        {formatShap(d.shapVal)}
                      </span>
                      <span className="text-[10px] text-[var(--text-muted)]">({d.direction})</span>
                    </div>
                  </div>

                  {/* Bidirectional Horizontal Bar — centered on 50% */}
                  <div className="w-full h-3 rounded-full overflow-hidden relative" style={{ background: 'linear-gradient(to right, rgba(16,185,129,0.08) 0%, rgba(16,185,129,0.08) 50%, rgba(239,68,68,0.08) 50%, rgba(239,68,68,0.08) 100%)' }}>
                    {/* Center line */}
                    <div className="absolute left-1/2 top-0 bottom-0 w-px bg-[var(--border-medium)] z-10" />
                    {isRiskIncrease ? (
                      /* Risk bar extends RIGHT from center */
                      <div
                        className="absolute top-0 bottom-0 rounded-r-full transition-all duration-500"
                        style={{
                          left: '50%',
                          width: `${barWidth}%`,
                          background: 'linear-gradient(to right, #ef4444, #dc2626)'
                        }}
                      />
                    ) : (
                      /* Protective bar extends LEFT from center */
                      <div
                        className="absolute top-0 bottom-0 rounded-l-full transition-all duration-500"
                        style={{
                          right: '50%',
                          width: `${barWidth}%`,
                          background: 'linear-gradient(to left, #10b981, #059669)'
                        }}
                      />
                    )}
                  </div>

                  {/* Labels under bar */}
                  <div className="flex justify-between text-[9px] text-[var(--text-muted)] font-mono px-1">
                    <span className="text-[var(--success)]">← Protective</span>
                    <span className="text-[var(--danger)]">Risk →</span>
                  </div>
                </div>
              );
            })}
          </div>


        </Card>
      </ContentSection>

      {/* SECTION 3: FEATURE CONTRIBUTION EXPLORER TABLE */}
      <ContentSection title="Feature Contribution Explorer" subtitle="Detailed breakdown of canonical feature values, reference ranges, and SHAP directions">
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="w-full md:w-96">
              <Input
                placeholder="Search feature by name..."
                leftIcon={<Search className="w-4 h-4" />}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="primary" size="sm">Showing {filteredDrivers.length} Features</Badge>
            </div>
          </div>

          <Table headers={['Feature Name', 'Modality', 'Observed Value', 'Reference Range', 'SHAP Value', 'Direction & Strength']}>
            {filteredDrivers.map((d, idx) => (
              <TableRow key={idx}>
                <TableCell className="font-semibold text-xs">{d.name}</TableCell>
                <TableCell>
                  <Badge variant={d.modality === 'clinical' ? 'primary' : d.modality === 'wearable' ? 'secondary' : 'accent'} size="sm">
                    {d.modality}
                  </Badge>
                </TableCell>
                <TableCell className="font-mono font-bold text-[var(--primary)] text-xs">{d.value}</TableCell>
                <TableCell className="font-mono text-xs text-[var(--text-muted)]">{d.range}</TableCell>
                <TableCell className="font-mono text-xs font-bold">
                  <span className={d.shapVal >= 0 ? 'text-[var(--danger)]' : 'text-[var(--success)]'}>
                    {formatShap(d.shapVal)}
                  </span>
                </TableCell>
                <TableCell>
                  <Badge variant={d.shapVal >= 0 ? 'danger' : 'success'} size="sm">
                    {d.direction}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </Table>
        </div>
      </ContentSection>

      {/* SECTION 4: CLINICAL INTERPRETATION & MEDICAL RAG SYNTHESIS */}
      <ContentSection title="Clinical Interpretation & Drivers Summary" subtitle="Synthesized clinical narrative grounded in TreeSHAP attributions and medical evidence">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card isGlass={true} className="p-6 space-y-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-[var(--danger)]" />
              <h4 className="text-base font-bold text-[var(--text-main)]">Primary Risk Drivers</h4>
            </div>
            <ul className="space-y-2 text-xs text-[var(--text-muted)]">
              {allDrivers.filter(d => d.shapVal > 0).slice(0, 3).map((d, idx) => (
                <li key={idx} className="p-3 bg-[var(--bg-primary)] rounded-xl border border-[var(--border-subtle)]">
                  <strong className="text-[var(--text-main)] block mb-0.5">{d.name} (+{d.shapVal.toFixed(3)} SHAP)</strong>
                  Measured value of <span className="font-mono text-[var(--danger)] font-bold">{d.value}</span> in {d.modality} modality increases statistical risk score for {selectedDisease.replace(/_/g, ' ')}.
                </li>
              ))}
              {allDrivers.filter(d => d.shapVal > 0).length === 0 && (
                <li className="p-3 bg-[var(--bg-primary)] rounded-xl border border-[var(--border-subtle)] text-[var(--text-muted)]">
                  No positive risk drivers identified for this target.
                </li>
              )}
            </ul>
          </Card>

          <Card isGlass={true} className="p-6 space-y-4">
            <div className="flex items-center gap-2">
              <TrendingDown className="w-5 h-5 text-[var(--success)]" />
              <h4 className="text-base font-bold text-[var(--text-main)]">Protective Factors & Data Notes</h4>
            </div>
            <ul className="space-y-2 text-xs text-[var(--text-muted)]">
              {allDrivers.filter(d => d.shapVal < 0).slice(0, 3).map((d, idx) => (
                <li key={idx} className="p-3 bg-[var(--bg-primary)] rounded-xl border border-[var(--border-subtle)]">
                  <strong className="text-[var(--text-main)] block mb-0.5">{d.name} ({d.shapVal.toFixed(3)} SHAP)</strong>
                  Measured value of <span className="font-mono text-[var(--success)] font-bold">{d.value}</span> in {d.modality} modality actively decreases statistical risk estimate.
                </li>
              ))}
              <li className="p-3 bg-[var(--bg-primary)] rounded-xl border border-[var(--border-subtle)]">
                <strong className="text-[var(--text-main)] block mb-0.5">Model Reliability Note</strong>
                {causalityDisclaimer}
              </li>
            </ul>
          </Card>
        </div>
      </ContentSection>

    </PageContainer>
  );
}
