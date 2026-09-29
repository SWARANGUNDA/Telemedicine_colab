import React from 'react';
import { Calendar, Bot, ShieldAlert, UserCheck, MessageSquare, Sparkles, HeartPulse, ArrowRight, Stethoscope, Video, FileText } from 'lucide-react';
import { PageContainer, PageHeader, ContentSection } from '../components/layout';
import { Card, Badge, Button, EmptyState } from '../components/ui';
import PersonalizedRecommendations from '../components/copilot/PersonalizedRecommendations';

export default function CarePage({ user, predictionData, onNavigate, activeSubNav }) {
  const isAppointments = activeSubNav === 'appointments';

  if (!predictionData) {
    return (
      <PageContainer className="space-y-6 py-4">
        <PageHeader
          title="Personalized Care & Evidence Protocols"
          description="Evidence-grounded cardiometabolic management recommendations derived strictly from your active health assessment"
          badge="Care Workspace"
        />
        <Card isGlass={true} className="p-8 text-center space-y-4 border border-[var(--border-medium)] shadow-xl">
          <Bot className="w-12 h-12 text-[var(--primary)] mx-auto" />
          <h3 className="text-lg font-extrabold text-[var(--text-main)]">No Active Health Assessment Found</h3>
          <p className="text-xs text-[var(--text-muted)] max-w-md mx-auto">
            Run a health assessment in the Intake Workspace to view personalized care guidelines and clinical recommendations.
          </p>
          <Button variant="primary" size="md" onClick={() => onNavigate ? onNavigate('intake') : null}>
            Start New Assessment →
          </Button>
        </Card>
      </PageContainer>
    );
  }

  return (
    <PageContainer className="space-y-5 py-4">
      
      {/* Page Header */}
      <PageHeader
        title={isAppointments ? 'Telemedicine Consultations & Care Scheduling' : 'Personalized Care & Evidence Protocols'}
        description={
          isAppointments
            ? 'Schedule specialist consultation sessions with endocrinology and metabolic specialists.'
            : 'Evidence-grounded management recommendations derived from your verified active assessment features.'
        }
        badge={`Pathway: ${predictionData.effective_pathway || predictionData.pathway_used || 'C+W+G'}`}
        actions={
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => onNavigate ? onNavigate('report') : null}
              className="px-3.5 py-2 rounded-xl bg-[var(--bg-surface)] hover:bg-[var(--bg-surface-hover)] border border-[var(--border-subtle)] hover:border-[var(--primary)] text-[var(--text-main)] font-bold text-xs shadow-sm hover:shadow transition-all flex items-center gap-1.5"
            >
              <FileText className="w-3.5 h-3.5 text-[var(--primary)]" />
              <span>View Full Report</span>
            </button>
            <button
              onClick={() => onNavigate ? onNavigate('appointments') : null}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-extrabold text-xs shadow-md hover:shadow-lg hover:scale-[1.02] transition-all flex items-center gap-1.5"
            >
              <Calendar className="w-3.5 h-3.5" />
              <span>Book Consultation</span>
            </button>
          </div>
        }
      />

      {/* Main Evidence Recommendations */}
      <PersonalizedRecommendations predictionData={predictionData} />

      {/* Bottom Specialist & Doctor Network Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
        
        {/* Card 1: Consultation Workspace */}
        <Card isGlass={true} className="p-4.5 space-y-3.5 shadow-xl border border-[var(--border-medium)] hover:border-[var(--primary)]/60 transition-all">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-500 shrink-0">
                <Video className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-black text-xs text-[var(--text-main)]">Specialist Tele-Consultations</h4>
                <p className="text-[10.5px] text-[var(--primary)] font-semibold">Connect with endocrinologists & cardiologists</p>
              </div>
            </div>
            <Badge variant="primary" size="sm" className="font-mono text-[9px]">ENCRYPTED HD</Badge>
          </div>
          <p className="text-[11px] text-[var(--text-muted)] leading-relaxed font-medium">
            Share your calibrated assessment and SHAP explainability insights directly with verified specialists for collaborative decision support.
          </p>
          <button
            onClick={() => onNavigate ? onNavigate('consultations') : null}
            className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-black text-xs shadow-md hover:shadow-lg hover:scale-[1.005] transition-all flex items-center justify-center gap-2 group cursor-pointer"
          >
            <span>Open Consultation Workspace</span>
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
          </button>
        </Card>

        {/* Card 2: Metabolic Health Network */}
        <Card isGlass={true} className="p-4.5 space-y-3.5 shadow-xl border border-[var(--border-medium)] hover:border-[var(--primary)]/60 transition-all">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-500 shrink-0">
                <UserCheck className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-black text-xs text-[var(--text-main)]">Metabolic Health Network</h4>
                <p className="text-[10.5px] text-emerald-400 font-semibold">Multidisciplinary physician review network</p>
              </div>
            </div>
            <Badge variant="success" size="sm" className="font-mono text-[9px]">VERIFIED DIRECTORY</Badge>
          </div>
          <p className="text-[11px] text-[var(--text-muted)] leading-relaxed font-medium">
            Access licensed medical specialists trained on TeleMed multimodal precision screening and lifestyle interventions.
          </p>
          <button
            onClick={() => onNavigate ? onNavigate('appointments') : null}
            className="w-full py-2.5 px-4 rounded-xl bg-[var(--bg-surface)] hover:bg-[var(--primary-light)] border-2 border-[var(--primary)]/40 hover:border-[var(--primary)] text-[var(--primary)] font-black text-xs shadow-sm hover:shadow-md hover:scale-[1.005] transition-all flex items-center justify-center gap-2 group cursor-pointer"
          >
            <span>View Available Doctors</span>
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
          </button>
        </Card>

      </div>
    </PageContainer>
  );
}
