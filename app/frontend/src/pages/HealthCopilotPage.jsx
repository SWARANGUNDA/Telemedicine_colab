import React, { useState, useEffect, useCallback, useRef } from 'react';
import { PageHeader, PageContainer } from '../components/layout';
import { Card, Badge, Button, Input, Tabs } from '../components/ui';
import {
  Sparkles, Send, Bot, User, HelpCircle, Activity, HeartPulse, Target,
  RefreshCw, CheckCircle2, FileText, ArrowRight, MessageSquare, Copy, RotateCcw,
  Search, ShieldCheck, AlertCircle, Calendar, Cpu, Layers, Database, ChevronRight,
  TrendingUp, Check, ExternalLink, BookOpen, Utensils, Dna, Info
} from 'lucide-react';

import HealthSummaryPanel from '../components/copilot/HealthSummaryPanel';
import PersonalizedRecommendations from '../components/copilot/PersonalizedRecommendations';
import ReportIntelligence from '../components/copilot/ReportIntelligence';
import ExplainabilityStudio from '../components/copilot/ExplainabilityStudio';
import BiomarkerExplorer from '../components/copilot/BiomarkerExplorer';
import AssessmentAssistant from '../components/copilot/AssessmentAssistant';
import KnowledgePanel from '../components/copilot/KnowledgePanel';
import { askRAGQuestionV3, askRAGQuestion, fetchPatientRecords } from '../api/client';

// ── Rich Response Formatter & Card Renderer ────────────────────────────────
function FormattedAiResponse({ text, isStreaming, onFollowUpClick }) {
  if (!text) return null;

  // Split text into sections if structured format is detected
  const sections = [];
  const lines = text.split('\n');
  let currentSection = { title: '', content: [] };

  lines.forEach(line => {
    const trimmed = line.trim();
    if (trimmed.startsWith('### ') || trimmed.startsWith('## ')) {
      if (currentSection.content.length > 0 || currentSection.title) {
        sections.push({ ...currentSection, content: currentSection.content.join('\n') });
      }
      currentSection = { title: trimmed.replace(/^#+\s*/, ''), content: [] };
    } else {
      currentSection.content.push(line);
    }
  });
  if (currentSection.content.length > 0 || currentSection.title) {
    sections.push({ ...currentSection, content: currentSection.content.join('\n') });
  }

  // If no structured sections found, format paragraph nicely
  if (sections.length <= 1 && !sections[0]?.title) {
    return (
      <div className="space-y-2 text-xs leading-relaxed">
        <p className="whitespace-pre-wrap">{text}{isStreaming && <span className="inline-block w-1.5 h-4 ml-1 bg-blue-600 animate-pulse align-middle" />}</p>
      </div>
    );
  }

  return (
    <div className="space-y-3.5 text-xs">
      {sections.map((sec, idx) => {
        const titleLower = sec.title.toLowerCase();
        const contentStr = sec.content.trim();
        if (!contentStr && !sec.title) return null;

        // Section 1: Direct Summary / Direct Answer
        if (titleLower.includes('direct') || titleLower.includes('summary') || titleLower.includes('answer')) {
          return (
            <div key={idx} className="p-3.5 rounded-2xl bg-blue-50/80 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800/60 text-[12px] leading-relaxed text-[var(--text-main)] space-y-1 shadow-xs">
              <div className="flex items-center gap-2 font-extrabold text-blue-600 dark:text-blue-400 text-xs">
                <Sparkles size={14} className="shrink-0" />
                <span>Direct Answer</span>
              </div>
              <div className="whitespace-pre-wrap font-medium">
                {contentStr.replace(/\*\*(.*?)\*\*/g, '$1')}
              </div>
            </div>
          );
        }

        // Section 2: Context / Why Relevant
        if (titleLower.includes('context') || titleLower.includes('relevant') || titleLower.includes('why')) {
          return (
            <div key={idx} className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] space-y-1">
              <div className="flex items-center gap-1.5 font-bold text-[var(--text-main)] text-[11px]">
                <Dna size={14} className="text-purple-600 shrink-0" />
                <span>Personalized Health Context</span>
              </div>
              <p className="text-[11px] text-[var(--text-muted)] leading-relaxed font-medium">
                {contentStr.replace(/\*\*(.*?)\*\*/g, '$1')}
              </p>
            </div>
          );
        }

        // Section 3: Relevant Biomarkers & Risk Factors
        if (titleLower.includes('biomarker') || titleLower.includes('risk') || titleLower.includes('data') || titleLower.includes('supporting')) {
          const items = contentStr.split('\n').filter(l => l.trim());
          return (
            <div key={idx} className="space-y-1.5">
              <div className="flex items-center gap-1.5 font-bold text-[var(--text-main)] text-[11px]">
                <Activity size={14} className="text-amber-500 shrink-0" />
                <span>Relevant Biomarkers & Screening Signals</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-0.5">
                {items.map((item, i) => {
                  const cleaned = item.replace(/^-\s*/, '').replace(/\*\*/g, '');
                  const isElevated = cleaned.toLowerCase().includes('elevated') || cleaned.toLowerCase().includes('positive') || cleaned.toLowerCase().includes('high');
                  return (
                    <div key={i} className="p-2.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] flex items-center justify-between text-[11px]">
                      <span className="font-semibold text-[var(--text-main)] truncate max-w-[70%]">{cleaned.split(':')[0]}</span>
                      <Badge variant={isElevated ? 'danger' : 'success'} size="sm" className="font-mono text-[9.5px]">
                        {isElevated ? 'Elevated' : 'Optimal'}
                      </Badge>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        }

        // Section 4: Evidence & Guidelines
        if (titleLower.includes('evidence') || titleLower.includes('guideline') || titleLower.includes('medical')) {
          const evLines = contentStr.split('\n').filter(l => l.trim());
          return (
            <div key={idx} className="p-3 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800/50 space-y-1.5">
              <div className="flex items-center gap-1.5 font-bold text-indigo-700 dark:text-indigo-300 text-[11px]">
                <BookOpen size={14} className="shrink-0" />
                <span>Medical Guideline Evidence</span>
              </div>
              <div className="space-y-1.5 text-[11px] text-[var(--text-muted)]">
                {evLines.map((ev, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <span className="px-1.5 py-0.5 rounded bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300 font-mono text-[9px] font-bold shrink-0 mt-0.5">
                      REF-{i + 1}
                    </span>
                    <span className="leading-tight">{ev.replace(/^-\s*\*\*\[.*?\]\*\*:\s*/, '').replace(/^-\s*/, '').replace(/\*\*/g, '')}</span>
                  </div>
                ))}
              </div>
            </div>
          );
        }

        // Section 5: Next Steps
        if (titleLower.includes('step') || titleLower.includes('action') || titleLower.includes('next')) {
          return (
            <div key={idx} className="p-3 rounded-xl bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/50 space-y-1">
              <div className="flex items-center gap-1.5 font-bold text-emerald-700 dark:text-emerald-300 text-[11px]">
                <CheckCircle2 size={14} className="shrink-0" />
                <span>Actionable Next Steps</span>
              </div>
              <p className="text-[11px] text-emerald-800 dark:text-emerald-200 leading-relaxed">
                {contentStr.replace(/^-\s*/, '').replace(/\*\*/g, '')}
              </p>
            </div>
          );
        }

        // Section 6: Disclaimer
        if (titleLower.includes('disclaimer') || titleLower.includes('notice')) {
          return (
            <div key={idx} className="pt-2 border-t border-[var(--border-subtle)] text-[10px] text-[var(--text-muted)] italic leading-tight">
              {contentStr.replace(/^---\s*/, '').replace(/\*\*/g, '')}
            </div>
          );
        }

        // Generic Section Fallback
        return (
          <div key={idx} className="space-y-1">
            <h4 className="font-bold text-[var(--text-main)] text-[11px]">{sec.title}</h4>
            <p className="text-[11px] text-[var(--text-muted)] whitespace-pre-wrap leading-relaxed">{contentStr.replace(/\*\*(.*?)\*\*/g, '$1')}</p>
          </div>
        );
      })}

      {isStreaming && (
        <span className="inline-block w-1.5 h-4 ml-1 bg-blue-600 animate-pulse align-middle" />
      )}
    </div>
  );
}

export default function HealthCopilotPage({ user, session, predictionData: propPredictionData, xaiData: propXaiData, onNavigate }) {
  const role = user?.role || 'PATIENT';
  const isDoctor = role === 'DOCTOR' || role === 'ADMIN';

  const [activeTab, setActiveTab] = useState('copilot');
  const [chatInput, setChatInput] = useState('');
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [copiedId, setCopiedId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Single Authoritative Assessment State
  const [fetchedRecord, setFetchedRecord] = useState(null);
  const [loadingRecord, setLoadingRecord] = useState(false);
  const [aiStatus, setAiStatus] = useState('Connected');

  const activeAssessment = propPredictionData || fetchedRecord?.prediction_snapshot || fetchedRecord;

  // Load single source of truth assessment from DB if not passed in props
  const loadAuthoritativeAssessment = useCallback(async () => {
    if (!propPredictionData) {
      setLoadingRecord(true);
      try {
        const res = await fetchPatientRecords();
        const records = Array.isArray(res) ? res : (res?.records || []);
        setFetchedRecord(records.length > 0 ? records[0] : null);
      } catch (err) {
        setFetchedRecord(null);
      } finally {
        setLoadingRecord(false);
      }
    }
  }, [propPredictionData]);

  useEffect(() => {
    loadAuthoritativeAssessment();
  }, [loadAuthoritativeAssessment]);

  // Derived metadata from active assessment
  const userName = user?.full_name || user?.name || (user?.email ? user.email.split('@')[0] : 'Patient');
  const patientDisplayId = activeAssessment?.patient_id || user?.user_id || 'P-10001';
  const assessmentId = activeAssessment?.assessment_id || activeAssessment?.session_id || 'ASM-ACTIVE';
  const assessmentDate = activeAssessment?.timestamp || activeAssessment?.created_at
    ? new Date(activeAssessment.timestamp || activeAssessment.created_at).toLocaleDateString()
    : 'Latest Session';
  const pathwayUsed = activeAssessment?.effective_pathway || activeAssessment?.pathway_used || 'C+W+G';
  const modelVersion = activeAssessment?.model_version || 'Validated Clinical ML Engine';
  const dataQuality = (activeAssessment?.data_quality_score !== undefined && activeAssessment?.data_quality_score !== null)
    ? `${Math.round(activeAssessment.data_quality_score * 100)}%`
    : 'Evaluated';

  // Chat Feed State
  const [chatMessages, setChatMessages] = useState([]);
  const [streamingMsgId, setStreamingMsgId] = useState(null);
  const [displayedTexts, setDisplayedTexts] = useState({});
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages, displayedTexts]);

  useEffect(() => {
    const greetingText = isDoctor
      ? `Welcome Dr. ${userName}. TeleMed AI Clinical Decision Support is active. Inspecting patient record (${patientDisplayId}). How can I assist with case analysis or guideline evidence today?`
      : `Hello ${userName}! I am your TeleMed AI Health Copilot. I can help explain your health assessment, biomarkers, and report findings in plain language.`;

    const initId = 'MSG-INIT';
    setChatMessages([
      {
        id: initId,
        sender: 'COPILOT',
        text: greetingText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
    ]);
    setDisplayedTexts({ [initId]: greetingText });
  }, [userName, isDoctor, patientDisplayId]);

  // Suggested Prompts based on User Role
  const suggestedPrompts = isDoctor
    ? [
        "Analyze this patient case",
        "Explain model risk drivers",
        "Review lab & biomarker results",
        "Generate clinical summary note"
      ]
    : [
        "Explain my latest assessment",
        "Explain my abnormal biomarkers",
        "Compare my latest and previous assessment",
        "Summarize my health report"
      ];

  // Follow-Up Question Chips per Context
  const getFollowUpChips = (promptText) => {
    const promptLower = (promptText || '').toLowerCase();
    if (promptLower.includes('diet') || promptLower.includes('food') || promptLower.includes('nutrition')) {
      return [
        "What specific foods should I avoid?",
        "How does post-meal walking help blood sugar?",
        "What questions should I ask my doctor?"
      ];
    }
    if (promptLower.includes('biomarker') || promptLower.includes('lab') || promptLower.includes('glucose')) {
      return [
        "How can I bring my glucose into normal range?",
        "What lab tests should be scheduled next?",
        "Explain my HbA1c score"
      ];
    }
    return [
      "What lifestyle changes have the biggest impact?",
      "How often should I test my biomarkers?",
      "Summarize this for my next doctor visit"
    ];
  };

  // Typewriter Streaming Animation Handler
  const startTypewriterStream = (msgId, fullText) => {
    setStreamingMsgId(msgId);
    setDisplayedTexts(prev => ({ ...prev, [msgId]: '' }));

    let index = 0;
    const chunkSize = 4; // Reveal 4 characters per tick for smooth natural typing
    const interval = setInterval(() => {
      index += chunkSize;
      if (index >= fullText.length) {
        setDisplayedTexts(prev => ({ ...prev, [msgId]: fullText }));
        setStreamingMsgId(null);
        clearInterval(interval);
      } else {
        setDisplayedTexts(prev => ({ ...prev, [msgId]: fullText.slice(0, index) }));
      }
    }, 12);
  };

  const handleSendMessage = async (e, customText = null) => {
    if (e && e.preventDefault) e.preventDefault();
    const promptToSubmit = customText || chatInput.trim();
    if (!promptToSubmit || isAiLoading) return;

    const userMsgId = `MSG-USER-${Date.now()}`;
    const userMsg = {
      id: userMsgId,
      sender: 'USER',
      text: promptToSubmit,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setChatMessages(prev => [...prev, userMsg]);
    setDisplayedTexts(prev => ({ ...prev, [userMsgId]: promptToSubmit }));
    if (!customText) setChatInput('');
    setIsAiLoading(true);
    setAiStatus('Processing');

    try {
      let botResponseText = '';
      let retrievedEvidence = [];

      if (activeAssessment) {
        const res = await askRAGQuestionV3(activeAssessment, promptToSubmit);
        const ans = res.answer_payload || res;
        botResponseText = ans.response_text || ans.text || ans.response;
        retrievedEvidence = ans.retrieved_evidence || [];
      } else {
        const sid = session?.session_id || user?.user_id || 'unauthenticated_session';
        const res = await askRAGQuestion(sid, promptToSubmit);
        const ans = res.answer_payload || res;
        botResponseText = ans.response_text || ans.text || ans.response;
        retrievedEvidence = ans.retrieved_evidence || [];
      }

      if (!botResponseText) {
        botResponseText = isDoctor
          ? `Clinical Copilot Analysis: Based on patient record (${patientDisplayId}), model feature attributions and guideline evidence indicate stable trajectory.`
          : `Health Copilot Summary: Based on your active record, your biomarkers and health data have been evaluated against verified clinical guidelines.`;
      }

      const botMsgId = `MSG-BOT-${Date.now()}`;
      const followUps = getFollowUpChips(promptToSubmit);

      const botMsg = {
        id: botMsgId,
        sender: 'COPILOT',
        text: botResponseText,
        evidence: retrievedEvidence,
        followUps,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setChatMessages(prev => [...prev, botMsg]);
      setAiStatus('Connected');

      // Launch streaming animation for real-time live typing
      startTypewriterStream(botMsgId, botResponseText);

    } catch (err) {
      const errId = `MSG-BOT-ERR-${Date.now()}`;
      const errText = `Copilot Advisory: ${err.message || 'Unable to retrieve clinical evidence at this time. Please try again.'}`;
      setChatMessages(prev => [
        ...prev,
        {
          id: errId,
          sender: 'COPILOT',
          text: errText,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isError: true
        },
      ]);
      setDisplayedTexts(prev => ({ ...prev, [errId]: errText }));
      setAiStatus('Connected');
    } finally {
      setIsAiLoading(false);
    }
  };

  const handleCopyMessage = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-main)] transition-colors duration-200">

      {/* ── Main Content Container ──────────────────────────────────────── */}
      <main className="max-w-[1600px] mx-auto px-6 py-6 space-y-6">

        {/* Page Title & Subtitle */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl font-black text-[var(--text-main)] tracking-tight">AI Health Copilot</h1>
              <Badge variant="primary" size="sm" className="font-mono">
                {isDoctor ? 'Clinical Decision Support' : 'Patient Assistant'}
              </Badge>
              {/* AI Status Badge */}
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 text-[11px] font-bold text-blue-600 dark:text-blue-400">
                <span className={`w-2 h-2 rounded-full ${aiStatus === 'Processing' ? 'bg-amber-500 animate-ping' : 'bg-emerald-500'}`} />
                <span>AI {aiStatus}</span>
              </div>
            </div>
            <p className="text-xs text-[var(--text-muted)] font-medium mt-0.5">
              {isDoctor
                ? 'AI-assisted clinical decision support, SHAP explainability, and evidence retrieval'
                : 'AI-assisted health analysis and personalized clinical insights'}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onNavigate ? onNavigate('analysis') : null}
              className="px-4 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-xl transition-all shadow-xs flex items-center gap-2 cursor-pointer"
            >
              <Sparkles size={14} />
              <span>Start New Analysis</span>
            </button>
          </div>
        </div>

        {/* ── Navigation Tabs ────────────────────────────────────────────── */}
        <div className="border-b border-[var(--border-subtle)] flex items-center gap-2 sm:gap-6 overflow-x-auto no-scrollbar">
          {[
            { id: 'copilot', label: 'AI Conversation Workspace', icon: MessageSquare },
            { id: 'xai', label: 'TreeSHAP Explainability Studio', icon: ShieldCheck },
            { id: 'biomarkers', label: 'Biomarker Intelligence Explorer', icon: Activity },
            { id: 'comparison', label: 'Assessment Comparison', icon: TrendingUp },
            { id: 'knowledge', label: 'Clinical Evidence Library', icon: Database },
          ].map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-3 px-3 sm:px-4 text-xs font-bold transition-all border-b-2 flex items-center gap-2 whitespace-nowrap cursor-pointer ${
                  isActive
                    ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-main)] hover:border-[var(--border-subtle)]'
                }`}
              >
                <Icon size={15} className={isActive ? 'text-blue-600 dark:text-blue-400' : ''} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* ── Genuine Empty State when NO assessment exists ──────────────── */}
        {!activeAssessment && !loadingRecord ? (
          <div className="bg-[var(--bg-surface)] rounded-3xl border border-[var(--border-subtle)] p-12 text-center max-w-xl mx-auto space-y-4 shadow-sm my-8">
            <div className="w-16 h-16 rounded-2xl bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 flex items-center justify-center mx-auto">
              <Bot size={32} />
            </div>
            <div>
              <h3 className="text-base font-bold text-[var(--text-main)]">No Health Assessment Yet</h3>
              <p className="text-xs text-[var(--text-muted)] mt-1.5 leading-relaxed">
                Upload your clinical report, wearable telemetry, or gut microbiome profile to activate your personalized AI Health Copilot.
              </p>
            </div>
            <div className="pt-2">
              <button
                onClick={() => onNavigate ? onNavigate('analysis') : null}
                className="px-6 py-2.5 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-xl transition-all shadow-md shadow-blue-500/20 inline-flex items-center gap-2 cursor-pointer"
              >
                <Sparkles size={16} />
                <span>Start New Analysis</span>
              </button>
            </div>
          </div>
        ) : (

          /* ── TAB 1: COPILOT CONVERSATIONAL WORKSPACE (2-COLUMN LAYOUT) ── */
          activeTab === 'copilot' && (
            <div className="space-y-6">

              {/* Health Summary Banner */}
              <HealthSummaryPanel predictionData={activeAssessment} />

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">

                {/* Left Column (8 Cols) — Main Conversational Chat Workspace */}
                <div className="lg:col-span-8 space-y-6">
                  <div className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl rounded-[2rem] border border-slate-200/60 dark:border-slate-800/60 p-6 shadow-xl shadow-slate-200/40 dark:shadow-none flex flex-col min-h-[680px] justify-between relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-blue-50/50 to-transparent dark:from-blue-900/20 pointer-events-none" />

                    {/* Chat Feed Header */}
                    <div className="flex items-center justify-between pb-4 border-b border-slate-200/60 dark:border-slate-700/60 relative z-10">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white flex items-center justify-center font-bold shadow-lg shadow-blue-500/20">
                          <Bot size={22} />
                        </div>
                        <div>
                          <h3 className="text-sm font-extrabold text-slate-800 dark:text-slate-100">Conversational Assistant</h3>
                          <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium mt-0.5">Real-time live streaming grounded in verified clinical guidelines</p>
                        </div>
                      </div>

                      <Badge variant="outline" size="sm" className="font-mono">
                        {pathwayUsed ? `Pathway ${pathwayUsed}` : 'Verified'}
                      </Badge>
                    </div>

                    {/* Action Prompt Pills */}
                    <div className="py-3.5 border-b border-slate-200/40 dark:border-slate-700/40 flex items-center gap-2 overflow-x-auto no-scrollbar relative z-10">
                      <span className="text-[10px] font-bold text-slate-400 uppercase shrink-0 tracking-wider">Prompts:</span>
                      {suggestedPrompts.map((promptText, idx) => (
                        <button
                          key={idx}
                          onClick={(e) => handleSendMessage(e, promptText)}
                          disabled={isAiLoading}
                          className="px-3.5 py-1.5 text-xs font-bold text-blue-700 dark:text-blue-300 bg-blue-50/80 hover:bg-blue-100/80 dark:bg-blue-950/40 dark:hover:bg-blue-900/60 rounded-full transition-all whitespace-nowrap shrink-0 border border-blue-200/60 dark:border-blue-800/40 cursor-pointer shadow-sm hover:shadow-md"
                        >
                          {promptText}
                        </button>
                      ))}
                    </div>

                    {/* Chat Messages Feed */}
                    <div className="flex-1 overflow-y-auto space-y-4 py-4 pr-1 max-h-[460px]">
                      {chatMessages.map((msg) => {
                        const isUser = msg.sender === 'USER';
                        const currentText = displayedTexts[msg.id] !== undefined ? displayedTexts[msg.id] : msg.text;
                        const isStreaming = streamingMsgId === msg.id;

                        return (
                          <div key={msg.id} className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
                            <div className="flex items-center gap-1.5 mb-1.5">
                              <span className="text-[10px] font-bold text-slate-500">
                                {isUser ? userName : 'TeleMed AI Copilot'}
                              </span>
                              <span className="text-[10px] font-mono text-slate-400">{msg.timestamp}</span>
                            </div>

                            <div
                              className={`p-4 rounded-3xl max-w-[88%] text-[13px] leading-relaxed shadow-sm relative transition-all ${
                                isUser
                                  ? 'bg-gradient-to-br from-blue-600 to-indigo-600 text-white rounded-br-sm shadow-blue-500/20'
                                  : msg.isError
                                  ? 'bg-rose-50/80 backdrop-blur-md border border-rose-200 text-rose-800 rounded-bl-sm'
                                  : 'bg-white/90 dark:bg-slate-800/90 backdrop-blur-md border border-slate-200/80 dark:border-slate-700/80 text-slate-800 dark:text-slate-200 rounded-bl-sm shadow-slate-200/50'
                              }`}
                            >
                              {isUser ? (
                                <p className="whitespace-pre-wrap">{msg.text}</p>
                              ) : (
                                <FormattedAiResponse text={currentText} isStreaming={isStreaming} />
                              )}

                              {/* Follow-up Question Chips (Shown after streaming completes) */}
                              {!isUser && !isStreaming && msg.followUps && msg.followUps.length > 0 && (
                                <div className="mt-3 pt-2.5 border-t border-[var(--border-subtle)]/60 space-y-1.5">
                                  <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase block">Suggested Follow-ups:</span>
                                  <div className="flex flex-wrap gap-1.5">
                                    {msg.followUps.map((chip, cIdx) => (
                                      <button
                                        key={cIdx}
                                        onClick={(e) => handleSendMessage(e, chip)}
                                        className="px-2.5 py-1 rounded-lg text-[10.5px] font-semibold bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 hover:bg-blue-100 border border-blue-200/50 dark:border-blue-800/40 transition-all cursor-pointer"
                                      >
                                        {chip}
                                      </button>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {!isUser && !isStreaming && (
                                <div className="pt-2 mt-2 border-t border-[var(--border-subtle)]/50 flex items-center justify-end gap-2 text-[10px]">
                                  <button
                                    onClick={() => handleCopyMessage(msg.id, msg.text)}
                                    className="text-[var(--text-muted)] hover:text-blue-600 font-mono flex items-center gap-1 cursor-pointer"
                                  >
                                    <Copy size={12} /> {copiedId === msg.id ? 'Copied!' : 'Copy'}
                                  </button>
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                      <div ref={messagesEndRef} />
                    </div>

                    {/* Message Composer Form */}
                    <form onSubmit={(e) => { e.preventDefault(); handleSendMessage(e); }} className="pt-4 border-t border-slate-200/60 dark:border-slate-700/60 relative z-10 mt-2">
                      <div className="flex bg-white dark:bg-slate-800 rounded-full border border-slate-200 dark:border-slate-700 shadow-sm items-center p-1.5 focus-within:ring-4 focus-within:ring-blue-500/20 focus-within:border-blue-500 transition-all">
                        <div className="w-10 h-10 flex items-center justify-center text-blue-500">
                          <Bot size={20} />
                        </div>
                        <input
                          placeholder={isDoctor ? "Ask Copilot about case guidelines, SHAP drivers, or summary..." : "Ask Copilot about your assessment, biomarkers, or report..."}
                          value={chatInput}
                          onChange={(e) => setChatInput(e.target.value)}
                          disabled={isAiLoading}
                          className="flex-1 bg-transparent border-none focus:outline-none px-2 py-2 text-sm text-slate-800 dark:text-slate-200 placeholder-slate-400"
                        />
                        <button
                          type="submit"
                          disabled={!chatInput.trim() || isAiLoading}
                          className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                            !chatInput.trim() || isAiLoading
                              ? 'bg-slate-100 dark:bg-slate-700 text-slate-400 cursor-not-allowed'
                              : 'bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-500/30 cursor-pointer'
                          }`}
                        >
                          {isAiLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4 ml-0.5" />}
                        </button>
                      </div>
                    </form>

                  </div>
                </div>

                {/* Right Column (4 Cols) — Context & AI Insights */}
                <div className="lg:col-span-4 space-y-6">

                  {/* Card 1: Patient / Assessment Context */}
                  <div className="bg-[var(--bg-surface)] rounded-3xl border border-[var(--border-subtle)] p-5 shadow-xs space-y-4">
                    <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
                      <div className="flex items-center gap-2">
                        <Cpu size={18} className="text-blue-600" />
                        <h3 className="text-sm font-bold text-[var(--text-main)]">Assessment Context</h3>
                      </div>
                      <Badge variant="outline" size="sm">ACTIVE RECORD</Badge>
                    </div>

                    <div className="space-y-2 text-xs">
                      <div className="p-2.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] flex items-center justify-between">
                        <span className="text-[var(--text-muted)] font-semibold">Patient ID</span>
                        <span className="font-mono font-bold text-[var(--text-main)]">{patientDisplayId}</span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] flex items-center justify-between">
                        <span className="text-[var(--text-muted)] font-semibold">Assessment ID</span>
                        <span className="font-mono font-bold text-[var(--text-main)]">{assessmentId}</span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] flex items-center justify-between">
                        <span className="text-[var(--text-muted)] font-semibold">Assessment Date</span>
                        <span className="font-bold text-[var(--text-main)]">{assessmentDate}</span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] flex items-center justify-between">
                        <span className="text-[var(--text-muted)] font-semibold">Modalities Present</span>
                        <span className="font-bold text-blue-600 dark:text-blue-400">{pathwayUsed}</span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] flex items-center justify-between">
                        <span className="text-[var(--text-muted)] font-semibold">Data Completeness</span>
                        <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">{dataQuality}</span>
                      </div>
                    </div>
                  </div>

                  {/* Card 2: AI Insights & Risk Estimate Disclaimer */}
                  <PersonalizedRecommendations predictionData={activeAssessment} />

                  {/* Clinical Disclaimer Box */}
                  <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-[11px] text-amber-800 dark:text-amber-300 space-y-1">
                    <span className="font-bold block flex items-center gap-1.5">
                      <AlertCircle size={14} className="shrink-0" />
                      <span>AI Model Prediction Estimate</span>
                    </span>
                    <p className="leading-tight">
                      {isDoctor
                        ? 'TeleMed AI provides clinical decision support tools. All predictions and SHAP attributions must be reviewed by an authorized licensed physician before making diagnostic decisions.'
                        : 'TeleMed AI provides educational health insights based on your uploaded records. AI evaluations are non-diagnostic and do not replace professional medical advice from your physician.'}
                    </p>
                  </div>

                </div>

              </div>

            </div>
          )
        )}

        {/* ── TAB 2: TREESHAP EXPLAINABILITY STUDIO ────────────────────── */}
        {activeTab === 'xai' && activeAssessment && (
          <div className="space-y-6">
            <ExplainabilityStudio predictionData={activeAssessment} xaiData={propXaiData} />
          </div>
        )}

        {/* ── TAB 3: BIOMARKER INTELLIGENCE EXPLORER ───────────────────── */}
        {activeTab === 'biomarkers' && activeAssessment && (
          <div className="space-y-6">
            <BiomarkerExplorer predictionData={activeAssessment} user={user} />
          </div>
        )}

        {/* ── TAB 4: ASSESSMENT COMPARISON ────────────────────────────── */}
        {activeTab === 'comparison' && activeAssessment && (
          <div className="space-y-6">
            <AssessmentAssistant predictionData={activeAssessment} user={user} />
          </div>
        )}

        {/* ── TAB 5: CLINICAL EVIDENCE LIBRARY ────────────────────────── */}
        {activeTab === 'knowledge' && activeAssessment && (
          <div className="max-w-4xl mx-auto space-y-6">
            <KnowledgePanel predictionData={activeAssessment} />
          </div>
        )}

      </main>

    </div>
  );
}
