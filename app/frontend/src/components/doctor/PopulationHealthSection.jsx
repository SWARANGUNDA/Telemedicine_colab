import React from 'react';
import { Card, Badge, ProgressBar } from '../ui';
import { FileText, Watch, Dna } from 'lucide-react';

export default function PopulationHealthSection({ consultations = [] }) {
  const totalCohort = consultations.length;

  // Compute real specialization distribution from authorized DB consultations
  const specCounts = {};
  consultations.forEach(c => {
    const spec = c.specialization || c.category || 'General Medicine';
    specCounts[spec] = (specCounts[spec] || 0) + 1;
  });

  const diseaseDist = Object.keys(specCounts).map(name => {
    const count = specCounts[name];
    const pct = totalCohort > 0 ? Math.round((count / totalCohort) * 100) : 0;
    return { name, count, pct, variant: 'primary' };
  });

  // Compute real status stratification
  const statusCounts = {
    ASSIGNED: consultations.filter(c => c.status === 'ASSIGNED').length,
    ACCEPTED: consultations.filter(c => c.status === 'ACCEPTED').length,
    ACTIVE: consultations.filter(c => c.status === 'ACTIVE').length,
    COMPLETED: consultations.filter(c => c.status === 'COMPLETED').length,
  };

  const riskDist = [
    { level: 'Active Consultations', count: statusCounts.ACTIVE, pct: totalCohort > 0 ? Math.round((statusCounts.ACTIVE / totalCohort) * 100) : 0, variant: 'danger' },
    { level: 'Accepted & In-Review', count: statusCounts.ACCEPTED, pct: totalCohort > 0 ? Math.round((statusCounts.ACCEPTED / totalCohort) * 100) : 0, variant: 'warning' },
    { level: 'Pending Doctor Acceptance', count: statusCounts.ASSIGNED, pct: totalCohort > 0 ? Math.round((statusCounts.ASSIGNED / totalCohort) * 100) : 0, variant: 'primary' },
    { level: 'Completed Review Cases', count: statusCounts.COMPLETED, pct: totalCohort > 0 ? Math.round((statusCounts.COMPLETED / totalCohort) * 100) : 0, variant: 'success' },
  ];

  return (
    <Card isGlass={true} className="p-6 space-y-6 shadow-xl border-t-4 border-t-[var(--primary)]">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-4">
        <div>
          <Badge variant="primary" size="sm">POPULATION HEALTH ANALYTICS</Badge>
          <h3 className="text-lg font-extrabold text-[var(--text-main)] mt-1">Cohort Specialty & Status Distribution</h3>
        </div>
        <span className="text-xs font-mono text-[var(--text-muted)]">Active Cohort: {totalCohort} Patient Cases</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Specialty Distribution */}
        <div className="space-y-4">
          <h4 className="text-xs font-mono font-bold text-[var(--text-muted)] uppercase">Requested Specialty Breakdown</h4>
          <div className="space-y-3">
            {diseaseDist.length > 0 ? (
              diseaseDist.map((d, idx) => (
                <div key={idx} className="space-y-1 text-xs">
                  <div className="flex justify-between font-semibold">
                    <span className="text-[var(--text-main)]">{d.name}</span>
                    <span className="font-mono text-[var(--text-muted)]">{d.count} cases ({d.pct}%)</span>
                  </div>
                  <ProgressBar value={d.pct} max={100} variant={d.variant} />
                </div>
              ))
            ) : (
              <p className="text-xs text-[var(--text-muted)] italic">No specialty cases registered in cohort database.</p>
            )}
          </div>
        </div>

        {/* Status Stratification */}
        <div className="space-y-4">
          <h4 className="text-xs font-mono font-bold text-[var(--text-muted)] uppercase">Case Status Stratification</h4>
          <div className="space-y-3">
            {riskDist.map((r, idx) => (
              <div key={idx} className="space-y-1 text-xs">
                <div className="flex justify-between font-semibold">
                  <span className="text-[var(--text-main)]">{r.level}</span>
                  <span className="font-mono text-[var(--text-muted)]">{r.count} cases ({r.pct}%)</span>
                </div>
                <ProgressBar value={r.pct} max={100} variant={r.variant} />
              </div>
            ))}
          </div>
        </div>

      </div>
    </Card>
  );
}
