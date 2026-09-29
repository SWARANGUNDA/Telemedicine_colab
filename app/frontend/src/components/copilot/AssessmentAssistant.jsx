import React, { useState, useEffect } from 'react';
import { Card, Badge, Button, EmptyState } from '../ui';
import { Activity, TrendingDown, TrendingUp, CheckCircle2, GitCompare, Calendar, ArrowRight, ChevronDown, ChevronUp } from 'lucide-react';
import { fetchPatientRecords } from '../../api/client';

export default function AssessmentAssistant({ predictionData, user }) {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    async function loadHistory() {
      try {
        const data = await fetchPatientRecords(user?.user_id || 'me');
        const list = Array.isArray(data) ? data : (data?.records || []);
        if (list.length > 0) {
          setRecords(list.sort((a, b) => new Date(b.created_at || b.date || 0) - new Date(a.created_at || a.date || 0)));
        }
      } catch (e) {
        // Handled silently
      } finally {
        setLoading(false);
      }
    }
    loadHistory();
  }, [user]);

  // Current assessment data
  const currentPredictions = predictionData?.predictions || predictionData?.disease_outcomes || {};
  const currentPathway = predictionData?.effective_pathway || predictionData?.pathway_used || 'N/A';
  const currentDate = new Date().toLocaleDateString('en-US', { month: 'short', year: 'numeric' });

  const getCurrentRisk = (diseaseKey) => {
    const item = currentPredictions[diseaseKey];
    if (!item) return null;
    const prob = item.calibrated_probability !== undefined ? item.calibrated_probability : (item.probability || 0);
    return Math.round(prob * 100);
  };

  const t2dCurrent = getCurrentRisk('Type2_Diabetes');
  const preCurrent = getCurrentRisk('Prediabetes');
  const adipCurrent = getCurrentRisk('High_Adiposity_Risk');

  // Find the most recent previous record for comparison
  const previousRecord = records.length > 0 ? records[0] : null;
  const prevPredictions = previousRecord?.prediction_data?.predictions || previousRecord?.prediction_data?.disease_outcomes || {};

  const getPrevRisk = (diseaseKey) => {
    const item = prevPredictions[diseaseKey];
    if (!item) return null;
    const prob = item.calibrated_probability !== undefined ? item.calibrated_probability : (item.probability || 0);
    return Math.round(prob * 100);
  };

  const t2dPrev = getPrevRisk('Type2_Diabetes');
  const prePrev = getPrevRisk('Prediabetes');

  const hasPrevious = previousRecord && t2dPrev !== null;
  const riskDelta = (t2dCurrent !== null && t2dPrev !== null) ? (t2dCurrent - t2dPrev) : null;
  const prevDate = previousRecord?.created_at
    ? new Date(previousRecord.created_at).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
    : 'Previous';

  if (!predictionData) {
    return (
      <Card isGlass={true} className="p-6 space-y-4 shadow-xl border-l-4 border-l-[var(--success)]">
        <div className="flex items-center gap-2 border-b border-[var(--border-subtle)] pb-3">
          <Activity className="w-5 h-5 text-[var(--success)]" />
          <h3 className="text-base font-extrabold text-[var(--text-main)]">Assessment History</h3>
        </div>
        <EmptyState
          icon={<GitCompare className="w-8 h-8 text-[var(--text-muted)]" />}
          title="No Assessment Data"
          description="Run a health assessment to see your results and track changes over time."
        />
      </Card>
    );
  }

  return (
    <Card isGlass={true} className="p-6 space-y-4 shadow-xl border-l-4 border-l-[var(--success)]">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-[var(--success)]" />
          <div>
            <h3 className="text-base font-extrabold text-[var(--text-main)]">Assessment Comparison</h3>
            <p className="text-[10px] text-[var(--text-muted)]">How your health has changed between assessments</p>
          </div>
        </div>
        {riskDelta !== null && (
          <Badge variant={riskDelta <= 0 ? 'success' : 'danger'} size="sm">
            {riskDelta <= 0 ? `${riskDelta}%` : `+${riskDelta}%`} Change
          </Badge>
        )}
      </div>

      <div className="space-y-3 text-xs">
        {/* Current vs Previous comparison grid */}
        <div className="grid grid-cols-2 gap-2 text-center font-mono">
          {hasPrevious ? (
            <>
              <div className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
                <span className="text-[10px] text-[var(--text-muted)] block uppercase">{prevDate} Assessment</span>
                <div className="text-lg font-extrabold text-[var(--warning)]">{t2dPrev}% Risk</div>
                <span className="text-[10px] text-[var(--text-muted)]">
                  Type 2 Diabetes
                </span>
              </div>
              <div className="p-3 rounded-xl bg-[var(--primary-light)]/30 border border-[var(--primary)]">
                <span className="text-[10px] text-[var(--primary)] block uppercase font-bold">{currentDate} (Current)</span>
                <div className={`text-lg font-extrabold ${riskDelta <= 0 ? 'text-[var(--success)]' : 'text-[var(--danger)]'}`}>
                  {t2dCurrent}% Risk
                </div>
                <span className={`text-[10px] font-bold ${riskDelta <= 0 ? 'text-[var(--success)]' : 'text-[var(--danger)]'}`}>
                  Type 2 Diabetes
                </span>
              </div>
            </>
          ) : (
            <>
              <div className="p-3 rounded-xl bg-[var(--bg-primary)] border border-dashed border-[var(--border-subtle)]">
                <span className="text-[10px] text-[var(--text-muted)] block uppercase">Previous Assessment</span>
                <div className="text-lg font-extrabold text-[var(--text-muted)]">—</div>
                <span className="text-[10px] text-[var(--text-muted)]">No prior data yet</span>
              </div>
              <div className="p-3 rounded-xl bg-[var(--primary-light)]/30 border border-[var(--primary)]">
                <span className="text-[10px] text-[var(--primary)] block uppercase font-bold">{currentDate} (Current)</span>
                <div className="text-lg font-extrabold text-[var(--text-main)]">{t2dCurrent ?? '—'}% Risk</div>
                <span className="text-[10px] text-[var(--text-muted)]">Type 2 Diabetes</span>
              </div>
            </>
          )}
        </div>

        {/* Narrative Summary */}
        <div className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] space-y-1">
          <strong className="text-xs text-[var(--text-main)] font-bold">What This Means for You</strong>
          <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
            {hasPrevious && riskDelta !== null ? (
              riskDelta < 0 
                ? `Great news! Comparing your ${prevDate} assessment with ${currentDate}, your diabetes risk decreased by ${Math.abs(riskDelta)} percentage points. This improvement suggests that lifestyle changes or treatments are having a positive effect on your health.`
                : riskDelta > 0
                  ? `Comparing your ${prevDate} assessment with ${currentDate}, your diabetes risk increased by ${riskDelta} percentage points. This change may be influenced by diet, activity levels, or other factors. Consider discussing these results with your doctor.`
                  : `Your diabetes risk has remained stable between your ${prevDate} and ${currentDate} assessments. Maintaining consistent health habits is important for long-term wellness.`
            ) : (
              `This is your first recorded assessment (Pathway: ${currentPathway}). Your Type 2 Diabetes risk is currently at ${t2dCurrent ?? 'N/A'}%. Run another assessment in the future to track how your health changes over time.`
            )}
          </p>
        </div>

        {/* Show Details Toggle */}
        {hasPrevious && (
          <>
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="text-[11px] font-semibold text-[var(--primary)] hover:underline flex items-center gap-1"
            >
              {showDetails ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              {showDetails ? 'Hide detailed comparison' : 'Show detailed comparison'}
            </button>

            {showDetails && (
              <div className="space-y-2 animate-fade-in">
                {[
                  { label: 'Type 2 Diabetes', current: t2dCurrent, prev: t2dPrev },
                  { label: 'Prediabetes', current: preCurrent, prev: prePrev },
                  { label: 'Adiposity & Obesity', current: adipCurrent, prev: getPrevRisk('High_Adiposity_Risk') },
                  { label: 'Metabolic Syndrome', current: getCurrentRisk('Metabolic_Syndrome'), prev: getPrevRisk('Metabolic_Syndrome') },
                  { label: 'NAFLD Liver Health', current: getCurrentRisk('NAFLD'), prev: getPrevRisk('NAFLD') },
                ].map((item, idx) => {
                  const delta = (item.current !== null && item.prev !== null) ? item.current - item.prev : null;
                  return (
                    <div key={idx} className="flex items-center justify-between p-2 rounded-lg bg-[var(--bg-surface)] text-[11px]">
                      <span className="font-semibold text-[var(--text-main)]">{item.label}</span>
                      <div className="flex items-center gap-3 font-mono">
                        <span className="text-[var(--text-muted)]">{item.prev ?? '—'}%</span>
                        <ArrowRight className="w-3 h-3 text-[var(--text-muted)]" />
                        <span className="font-bold text-[var(--text-main)]">{item.current ?? '—'}%</span>
                        {delta !== null && (
                          <Badge variant={delta <= 0 ? 'success' : 'danger'} size="sm">
                            {delta <= 0 ? `${delta}%` : `+${delta}%`}
                          </Badge>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}

        {/* History count */}
        {!loading && (
          <p className="text-[10px] text-[var(--text-muted)] text-center font-mono pt-1">
            {records.length} saved assessment{records.length !== 1 ? 's' : ''} in your health history
          </p>
        )}
      </div>
    </Card>
  );
}
