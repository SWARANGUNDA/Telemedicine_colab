import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageContainer } from '../components/layout';
import MarkdownRenderer from '../components/MarkdownRenderer';
import { Badge, Button, Modal } from '../components/ui';
import {
  MessageSquare, Send, Search, CheckCheck, UserCheck, ShieldCheck,
  FileText, Clock, RefreshCw, Sparkles, User, Bot, Calendar,
  Activity, ExternalLink, Archive, AlertCircle, Lock, Phone, Video,
  Paperclip, Filter, Plus, UploadCloud, Trash2, CheckCircle2,
  Stethoscope, FileSpreadsheet, MoreVertical, Info, X, Zap, ChevronRight,
  Shield, HeartPulse, HelpCircle, CornerDownLeft
} from 'lucide-react';
import {
  fetchUserConversations,
  fetchConsultationMessages,
  sendConsultationMessage,
  markMessagesAsRead,
  askRAGQuestion
} from '../api/client';

export default function MessagesPage({ user }) {
  const navigate = useNavigate();
  const userId = user?.user_id || user?.id || 'guest';
  const userRole = user?.role?.toUpperCase() || 'PATIENT';

  const patientFullName = user?.full_name || user?.name || user?.patient_profile?.full_name || (user?.email ? user.email.split('@')[0].replace('.', ' ').replace('_', ' ') : 'Patient');
  const patientFirstName = patientFullName.split(' ')[0] || 'Patient';

  // State Management
  const [conversations, setConversations] = useState([]);
  const [selectedConversationId, setSelectedConversationId] = useState(null);
  const [activeTab, setActiveTab] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [messageInput, setMessageInput] = useState('');
  const [messagesHistory, setMessagesHistory] = useState({});

  const [loadingConversations, setLoadingConversations] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sending, setSending] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [archivedIds, setArchivedIds] = useState(new Set());
  const [isAiThinking, setIsAiThinking] = useState(false);
  
  const aiThread = { id: 'ai-assistant', doctorName: 'TeleMed AI Copilot', specialty: 'AI Assistant', title: 'Health Insights', timestamp: 'Now', unreadCount: 0, isAi: true };
  
  // Modals & Menus
  const [showSecurityModal, setShowSecurityModal] = useState(false);
  const [showArchiveConfirm, setShowArchiveConfirm] = useState(false);
  const [showAiInfoModal, setShowAiInfoModal] = useState(false);
  const [showMenuDropdown, setShowMenuDropdown] = useState(false);

  const chatEndRef = useRef(null);

  // Auto-scroll chat feed to bottom
  const scrollToBottom = useCallback(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messagesHistory, selectedConversationId, scrollToBottom]);

  const loadConversations = useCallback(async () => {
    setLoadingConversations(true);
    setErrorMsg(null);
    try {
      const res = await fetchUserConversations();
      const rawThreads = (res && Array.isArray(res.conversations)) ? res.conversations : [];

      const seenIds = new Set();
      const dbThreads = [];
      for (const t of rawThreads) {
        const tid = t.id || t.consultation_id;
        if (tid && !seenIds.has(tid)) {
          seenIds.add(tid);
          dbThreads.push(t);
        }
      }
      
      setConversations(dbThreads);
      if (dbThreads.length > 0 && !selectedConversationId) {
        setSelectedConversationId(dbThreads[0].id || dbThreads[0].consultation_id);
      }
    } catch (err) {
      // Handled silently
    } finally {
      setLoadingConversations(false);
    }
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  const loadActiveMessages = useCallback(async (convId) => {
    if (!convId) return;

    setLoadingMessages(true);
    try {
      const res = await fetchConsultationMessages(convId);
      const msgList = Array.isArray(res) ? res : (res?.messages || []);
      const fetchedMsgs = msgList.map(m => ({
        ...m,
        status: 'sent'
      }));

      setMessagesHistory(prev => ({
        ...prev,
        [convId]: fetchedMsgs
      }));

      setConversations(prev => prev.map(c => c.id === convId ? { ...c, unreadCount: 0 } : c));
    } catch (err) {
      // Handled silently
    } finally {
      setLoadingMessages(false);
    }
  }, []);

  useEffect(() => {
    if (selectedConversationId) {
      loadActiveMessages(selectedConversationId);
    }
  }, [selectedConversationId, loadActiveMessages]);

  const handleSendMessage = async (e) => {
    if (e) e.preventDefault();
    const text = messageInput.trim();
    if (!text || sending || !selectedConversationId) return;

    if (activeConv?.isAi) {
      const userMsg = {
        message_id: `msg-${Date.now()}`,
        sender_name: user?.full_name || 'You',
        content: text,
        created_at: new Date().toISOString(),
        sender_role: user?.role || 'PATIENT',
        sender_user_id: userId,
        status: 'sent'
      };

      setMessagesHistory(prev => ({
        ...prev,
        [selectedConversationId]: [...(prev[selectedConversationId] || []), userMsg]
      }));

      setMessageInput('');
      setIsAiThinking(true);
      
      try {
        const res = await askRAGQuestion(userId, text);
        const botText = res.answer || res.answer_payload?.answer || res.answer_payload?.response_text || res.answer_payload?.response || 'I am sorry, I am unable to process that at the moment.';
        const botMsg = {
          message_id: `msg-${Date.now() + 1}`,
          sender_name: 'TeleMed AI Copilot',
          content: botText,
          created_at: new Date().toISOString(),
          sender_role: 'AI',
          sender_user_id: 'ai-assistant',
          status: 'sent',
          evidence: res.answer_payload?.retrieved_evidence || []
        };
        setMessagesHistory(prev => ({
          ...prev,
          [selectedConversationId]: [...(prev[selectedConversationId] || []), botMsg]
        }));
      } catch (err) {
        setErrorMsg(err.message || "Failed to communicate with AI Copilot.");
      } finally {
        setIsAiThinking(false);
      }
      return;
    }

    const nowIso = new Date().toISOString();
    setMessageInput('');
    setErrorMsg(null);

    // Doctor Consultation Path
    setSending(true);
    const tempMsgId = `temp_${Date.now()}`;
    const newMsg = {
      message_id: tempMsgId,
      consultation_id: selectedConversationId,
      sender_user_id: userId,
      sender_role: userRole,
      sender_name: patientFullName,
      content: text,
      created_at: nowIso,
      status: 'sending'
    };

    setMessagesHistory(prev => ({
      ...prev,
      [selectedConversationId]: [...(prev[selectedConversationId] || []), newMsg]
    }));

    try {
      const res = await sendConsultationMessage(selectedConversationId, text);
      const savedData = (res && typeof res === 'object' && res.data) ? res.data : res;
      
      setMessagesHistory(prev => ({
        ...prev,
        [selectedConversationId]: (prev[selectedConversationId] || []).map(m => 
          m.message_id === tempMsgId 
            ? { ...m, message_id: savedData?.message_id || tempMsgId, status: 'sent', created_at: savedData?.created_at || nowIso }
            : m
        )
      }));

      setConversations(prev => prev.map(c => 
        c.id === selectedConversationId ? { ...c, lastMessage: text, lastMessageTime: 'Just now' } : c
      ));
    } catch (err) {
      setErrorMsg(err.message || "Failed to send message to physician.");
      setMessagesHistory(prev => ({
        ...prev,
        [selectedConversationId]: (prev[selectedConversationId] || []).map(m => 
          m.message_id === tempMsgId ? { ...m, status: 'failed' } : m
        )
      }));
    } finally {
      setSending(false);
    }
  };

  // Resend Failed Message
  const handleRetryMessage = async (msgToRetry) => {
    if (!msgToRetry || sending) return;
    const text = msgToRetry.content;
    const convId = msgToRetry.consultation_id || selectedConversationId;

    setMessagesHistory(prev => ({
      ...prev,
      [convId]: (prev[convId] || []).filter(m => m.message_id !== msgToRetry.message_id)
    }));

    setMessageInput(text);
  };

  // Quick Prompt Preset Fill
  const handleQuickPrompt = (promptText) => {
    setMessageInput(promptText);
  };

  // Keyboard shortcut: Enter to send, Shift+Enter newline
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Archive Confirmation
  const confirmArchive = () => {
    if (!selectedConversationId) return;
    setArchivedIds(prev => new Set(prev).add(selectedConversationId));
    setShowArchiveConfirm(false);
    setShowMenuDropdown(false);
    
    const remaining = conversations.filter(c => c.id !== selectedConversationId && !archivedIds.has(c.id));
    if (remaining.length > 0) {
      setSelectedConversationId(remaining[0].id);
    }
  };

  // Timestamp formatting
  const formatTime = (ts) => {
    if (!ts) return 'Just now';
    try {
      const d = new Date(ts);
      return isNaN(d.getTime()) ? ts : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      return 'Just now';
    }
  };

  const formatDate = (ts) => {
    if (!ts) return 'Today';
    try {
      const d = new Date(ts);
      return isNaN(d.getTime()) ? ts : d.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
    } catch (e) {
      return 'Today';
    }
  };

  // Filter Conversations
  const filteredConversations = conversations.filter(c => {
    const isArchived = archivedIds.has(c.id);
    if (activeTab === 'archived') return isArchived;
    if (isArchived) return false;

    if (activeTab === 'doctors' && c.isAi) return false;
    if (activeTab === 'ai' && !c.isAi) return false;

    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      c.doctorName?.toLowerCase().includes(q) ||
      c.specialty?.toLowerCase().includes(q) ||
      c.title?.toLowerCase().includes(q) ||
      c.consultation_id?.toLowerCase().includes(q)
    );
  });
  
  let displayConversations = [...filteredConversations];
  if (activeTab === 'all' || activeTab === 'ai') {
    if (!searchQuery.trim() || aiThread.doctorName.toLowerCase().includes(searchQuery.toLowerCase())) {
        displayConversations = [aiThread, ...displayConversations];
    }
  }

  const activeConv = displayConversations.find(c => c.id === selectedConversationId) || aiThread;
  const currentMessages = messagesHistory[selectedConversationId] || [];

  return (
    <div className="max-w-[1600px] w-full mx-auto p-2 flex flex-col h-full overflow-hidden space-y-2">
      
      {/* ── TOP MODERN HEADER BAR ────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-4 bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white rounded-2xl shadow-xl border border-slate-700/50">
        <div className="flex items-center space-x-3.5">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 text-white flex-shrink-0">
            <MessageSquare className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-extrabold tracking-tight text-white">Clinical Communication Hub</h1>
              <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Live Session
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">Encrypted multi-channel communication with certified physicians and Generative AI Assistant.</p>
          </div>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            onClick={() => setShowSecurityModal(true)}
            className="flex items-center space-x-2 bg-white/10 hover:bg-white/15 text-slate-200 border border-white/15 px-3.5 py-2 rounded-xl text-xs font-semibold backdrop-blur-md transition-all cursor-pointer shadow-sm"
          >
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>HIPAA Encrypted</span>
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center justify-between shadow-sm animate-fade-in">
          <div className="flex items-center space-x-2.5">
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span className="font-medium">{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg(null)} className="font-bold text-rose-700 hover:text-rose-900 underline cursor-pointer text-xs">Dismiss</button>
        </div>
      )}

      {/* ── 3-COLUMN CLINICAL WORKSPACE GRID ─────────────────────────────────── */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-3 min-h-0">

        {/* ── LEFT COLUMN: Care Communications (3 cols) ─────────────────────── */}
        <div className="lg:col-span-3 bg-white border border-slate-200/90 rounded-2xl p-4 space-y-3.5 shadow-lg shadow-slate-100/60 flex flex-col h-full overflow-hidden">
          
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-7 h-7 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
                <Stethoscope className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Care Channels</h3>
            </div>

            <button
              onClick={loadConversations}
              className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors cursor-pointer"
              title="Refresh Communications"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingConversations ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {/* Segmented Filter Tabs */}
          <div className="grid grid-cols-4 gap-1 p-1 bg-slate-100/80 border border-slate-200/60 rounded-xl text-[11px] font-semibold text-slate-600">
            {[
              { id: 'all', label: 'All' },
              { id: 'doctors', label: 'Doctors' },
              { id: 'ai', label: 'AI Bot' },
              { id: 'archived', label: 'Saved' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-1.5 px-1 rounded-lg text-center transition-all cursor-pointer truncate ${
                  activeTab === tab.id
                    ? 'bg-white text-blue-600 font-bold shadow-sm border border-slate-200/60'
                    : 'hover:text-slate-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search care team & channels..."
              className="w-full pl-8 pr-3 py-2 text-xs bg-slate-50/80 border border-slate-200/90 rounded-xl focus:outline-none focus:border-blue-500 focus:bg-white text-slate-800 placeholder-slate-400 transition-all"
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery('')} className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600">
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Care Communications List */}
          <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
            {loadingConversations ? (
              <div className="py-12 text-center text-xs text-slate-400 space-y-2">
                <RefreshCw className="w-5 h-5 animate-spin mx-auto text-blue-600" />
                <p>Syncing care channels...</p>
              </div>
            ) : displayConversations.length === 0 ? (
              <div className="py-10 text-center space-y-2.5 px-3 border border-dashed border-slate-200/80 rounded-2xl bg-slate-50/50 my-auto">
                <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
                  <MessageSquare className="w-5 h-5" />
                </div>
                <p className="text-xs font-bold text-slate-700">No active conversations</p>
                <p className="text-[11px] text-slate-500 leading-relaxed">Book a consultation with a specialist to initiate direct physician care communications.</p>
              </div>
            ) : (
              displayConversations.map((conv, idx) => {
                const isSelected = selectedConversationId === conv.id;

                return (
                  <div
                    key={`${conv.id || 'conv'}_${idx}`}
                    onClick={() => setSelectedConversationId(conv.id)}
                    className={`p-3 rounded-2xl cursor-pointer transition-all border ${
                      isSelected
                        ? 'bg-gradient-to-r from-blue-50/90 to-indigo-50/80 border-blue-500/80 shadow-md shadow-blue-500/5 ring-1 ring-blue-500/20'
                        : 'bg-white border-slate-200/70 hover:border-slate-300 hover:bg-slate-50/80'
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      {/* Avatar Icon */}
                      <div className={`w-9 h-9 rounded-xl flex items-center justify-center text-xs font-bold flex-shrink-0 shadow-sm ${conv.isAi ? 'bg-gradient-to-tr from-purple-600 to-pink-500 text-white shadow-purple-500/20' : 'bg-gradient-to-tr from-blue-600 to-cyan-600 text-white shadow-blue-500/20'}`}>
                        {conv.isAi ? <Bot className="w-4 h-4" /> : <UserCheck className="w-4 h-4" />}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-0.5">
                          <h4 className="text-xs font-bold text-slate-900 truncate">
                            {conv.doctorName || conv.title}
                          </h4>
                          <span className="text-[10px] text-slate-400 flex-shrink-0 font-medium">
                            {conv.lastMessageTime}
                          </span>
                        </div>

                        <p className="text-[11px] font-semibold text-slate-500 truncate mb-1">
                          {conv.specialty}
                        </p>

                        <div className="flex items-center justify-between">
                          <p className="text-[11px] text-slate-600 truncate pr-2">
                            {conv.lastMessage}
                          </p>
                          {conv.unreadCount > 0 && (
                            <span className="w-2.5 h-2.5 rounded-full bg-blue-600 flex-shrink-0 ring-2 ring-blue-100" />
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          <div className="pt-2 border-t border-slate-100">
            <button
              className="w-full py-2.5 px-3 rounded-xl border border-blue-200 bg-blue-50/60 hover:bg-blue-100/80 text-blue-700 font-bold text-xs flex items-center justify-center space-x-2 transition-all cursor-pointer shadow-xs"
              onClick={() => navigate('/appointments')}
            >
              <Calendar className="w-4 h-4 text-blue-600" />
              <span>Book Doctor Consultation</span>
            </button>
          </div>
        </div>

        {/* ── CENTER COLUMN: Clinical Communication Workspace (6 cols) ──────── */}
        <div className="lg:col-span-6 bg-white border border-slate-200/90 rounded-2xl flex flex-col h-full overflow-hidden shadow-lg shadow-slate-100/60 relative">
          
          {/* Active Header */}
          <div className="p-3.5 px-5 border-b border-slate-100 flex items-center justify-between bg-white flex-shrink-0 shadow-2xs">
            <div className="flex items-center space-x-3.5 min-w-0">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xs font-bold flex-shrink-0 shadow-md bg-gradient-to-tr from-blue-600 to-cyan-600 text-white">
                <UserCheck className="w-5 h-5" />
              </div>

              <div className="min-w-0">
                <div className="flex items-center space-x-2.5">
                  <h3 className="text-sm font-extrabold text-slate-900 truncate">
                    {activeConv?.doctorName || activeConv?.title || 'Select a Conversation'}
                  </h3>
                  {activeConv?.consultation_id && (
                    <span className="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider bg-emerald-100 text-emerald-700 border border-emerald-200">
                      Verified Physician
                    </span>
                  )}
                </div>

                <p className="text-xs text-slate-500 truncate mt-0.5">
                  {activeConv?.specialty} {activeConv?.hospital ? `• ${activeConv.hospital}` : ''}
                </p>
              </div>
            </div>

            {/* Header Right Actions */}
            <div className="flex items-center space-x-2 flex-shrink-0">
              {!activeConv.isAi && activeConv.consultation_id && (
                <button
                  className="text-xs font-bold py-1.5 px-3 border border-slate-200 bg-slate-50 hover:bg-slate-100 rounded-xl text-slate-700 flex items-center space-x-1.5 transition-all cursor-pointer"
                  onClick={() => navigate('/consultations')}
                >
                  <FileText className="w-3.5 h-3.5 text-blue-600" />
                  <span>Consultation Details</span>
                </button>
              )}

              {/* Overflow Menu */}
              <div className="relative">
                <button
                  onClick={() => setShowMenuDropdown(!showMenuDropdown)}
                  className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
                  title="More Options"
                >
                  <MoreVertical className="w-4 h-4" />
                </button>

                {showMenuDropdown && (
                  <div className="absolute right-0 top-10 w-44 bg-white border border-slate-200 rounded-xl shadow-xl z-20 py-1 text-xs">
                    <button
                      onClick={() => {
                        setShowArchiveConfirm(true);
                        setShowMenuDropdown(false);
                      }}
                      className="w-full text-left px-3.5 py-2 text-rose-600 hover:bg-rose-50 flex items-center space-x-2 font-medium"
                    >
                      <Archive className="w-3.5 h-3.5" />
                      <span>Archive Thread</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Clinical Communication Timeline Feed */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4 custom-scrollbar bg-slate-50/40">
            
            {/* System Activity Timeline Marker */}
            <div className="text-center my-2">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider bg-white border border-slate-200/80 px-3 py-1 rounded-full shadow-2xs">
                Timeline Activity • {formatDate(currentMessages[0]?.created_at)}
              </span>
            </div>

            {/* Real Consultation Event Marker */}
            {activeConv?.appointment_date && (
              <div className="p-3 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200/80 rounded-2xl text-xs flex items-center space-x-3 text-blue-900 shadow-sm">
                <CheckCircle2 className="w-5 h-5 text-blue-600 flex-shrink-0" />
                <div>
                  <p className="font-bold">Appointment Confirmed with {activeConv?.doctorName}</p>
                  <p className="text-[11px] text-blue-700">Scheduled slot: {activeConv?.appointment_date} {activeConv?.appointment_time || ''}</p>
                </div>
              </div>
            )}

            {loadingMessages ? (
              <div className="py-16 text-center text-xs text-slate-400 space-y-2">
                <RefreshCw className="w-5 h-5 animate-spin mx-auto text-blue-600" />
                <p>Retrieving timeline entries...</p>
              </div>
            ) : currentMessages.length === 0 ? (
              <div className="py-16 text-center text-xs text-slate-400 space-y-2">
                <Stethoscope className="w-8 h-8 mx-auto text-slate-300" />
                <p className="font-bold text-slate-700 text-sm">Communication Timeline Active</p>
                <p className="text-slate-500">Send a message below to transmit an entry to your care team.</p>
              </div>
            ) : (
              currentMessages.map((msg, index) => {
                const isMe = msg.sender_user_id === userId || msg.sender_role === 'PATIENT';
                return (
                  <div
                    key={msg.message_id || index}
                    className={`flex flex-col ${isMe ? 'items-end' : 'items-start'} space-y-1`}
                  >
                    {/* Sender Label */}
                    <div className="flex items-center space-x-2 px-1">
                      <span className="text-[10px] font-bold text-slate-500">
                        {isMe ? 'You' : msg.sender_name || activeConv?.doctorName}
                      </span>
                      <span className="text-[10px] text-slate-400">
                        {formatTime(msg.created_at)}
                      </span>
                    </div>

                    {/* Chat Bubble Container */}
                    <div
                      className={`max-w-[85%] p-4 rounded-2xl text-xs space-y-1.5 shadow-sm transition-all ${
                        isMe
                          ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-br-none shadow-blue-500/10'
                          : 'bg-white border border-slate-200/90 text-slate-900 rounded-bl-none shadow-slate-100'
                      }`}
                    >
                      <div className="leading-relaxed">
                        {msg.sender_role === 'AI' || msg.sender_user_id === 'ai-assistant' ? (
                          <MarkdownRenderer text={msg.content} />
                        ) : (
                          <p className="whitespace-pre-wrap">{msg.content}</p>
                        )}
                      </div>

                      {/* Footer Status for Patient Messages */}
                      {isMe && (
                        <div className="flex justify-end pt-1 text-[10px] text-blue-100 items-center gap-1">
                          {msg.status === 'sending' ? (
                            <span>Transmitting...</span>
                          ) : msg.status === 'failed' ? (
                            <button
                              onClick={() => handleRetryMessage(msg)}
                              className="text-rose-200 hover:text-white font-bold underline flex items-center gap-1 cursor-pointer"
                            >
                              <AlertCircle className="w-3 h-3" /> Retry Transmission
                            </button>
                          ) : (
                            <span className="flex items-center gap-1 font-semibold text-blue-100">
                              <CheckCheck className="w-3.5 h-3.5" /> Transmitted
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            )}

            <div ref={chatEndRef} />
          </div>

          {activeConv?.isAi && (
            <div className="px-4 py-2 bg-slate-50/80 border-t border-slate-100 flex flex-wrap items-center gap-2 flex-shrink-0">
              <span className="text-[10px] font-extrabold uppercase text-purple-600 flex-shrink-0 flex items-center gap-1">
                <Zap className="w-3 h-3" /> Quick Ask:
              </span>
              {[
                "What do my latest lab results mean?",
                "Suggest dietary fiber recommendations.",
                "How to improve my sleep score?"
              ].map((prompt, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleQuickPrompt(prompt)}
                  className="px-2.5 py-1 bg-white hover:bg-purple-50 border border-slate-200 hover:border-purple-300 rounded-full text-[11px] text-slate-700 hover:text-purple-700 whitespace-nowrap transition-all cursor-pointer shadow-2xs font-medium"
                >
                  {prompt}
                </button>
              ))}
            </div>
          )}

          {/* Bottom Message Composer */}
          <form onSubmit={handleSendMessage} className="p-3.5 border-t border-slate-100 bg-white flex flex-col space-y-2 flex-shrink-0">
            <div className="flex items-center space-x-2.5">
              <button
                type="button"
                onClick={() => navigate('/intake')}
                className="p-2.5 text-slate-400 hover:text-blue-600 bg-slate-50 hover:bg-blue-50 border border-slate-200 rounded-xl transition-all cursor-pointer"
                title="Attach Health Record or Document"
              >
                <Paperclip className="w-4 h-4" />
              </button>

              <textarea
                value={messageInput}
                onChange={(e) => setMessageInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={activeConv?.isAi ? "Ask AI Assistant about lab parameters, risk scores, or health recommendations..." : "Write a secure message to your healthcare team..."}
                rows={1}
                className="flex-1 px-4 py-2.5 text-xs bg-slate-50/80 border border-slate-200 rounded-xl focus:outline-none focus:border-blue-500 focus:bg-white text-slate-900 placeholder-slate-400 resize-none overflow-hidden"
              />

              <button
                type="submit"
                disabled={!messageInput.trim() || sending || isAiThinking}
                className={`h-10 px-4 rounded-xl flex items-center justify-center space-x-1.5 text-xs font-bold text-white transition-all shadow-md cursor-pointer ${
                  !messageInput.trim() || sending || isAiThinking
                    ? 'bg-slate-300 cursor-not-allowed shadow-none'
                    : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-blue-500/20 hover:scale-[1.02]'
                }`}
              >
                {sending || isAiThinking ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <span>Send</span>
                    <Send className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </div>

            <div className="text-[10px] text-slate-400 text-center flex items-center justify-center space-x-1.5 pt-0.5">
              <Lock className="w-3 h-3 text-emerald-600" />
              <span className="font-medium">256-bit Encrypted Telehealth Communication Session</span>
            </div>
          </form>
        </div>

        {/* ── RIGHT COLUMN: Context & Care Actions (3 cols) ────────────────── */}
        <div className="lg:col-span-3 space-y-4 h-full overflow-y-auto custom-scrollbar">
          
          {/* Care Context Card */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-4 space-y-3 shadow-lg shadow-slate-100/60">
            <div className="flex items-center space-x-2">
              <div className="w-7 h-7 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
                <Activity className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                {activeConv?.isAi ? 'Care Context' : 'Consultation Details'}
              </h3>
            </div>

            <div className="p-3 bg-gradient-to-br from-slate-50 to-indigo-50/30 border border-slate-200/70 rounded-xl space-y-2 text-xs">
              {activeConv?.isAi ? (
                <>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Session Type:</span>
                    <span className="font-bold text-slate-800">AI Assistant Session</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">RAG Engine:</span>
                    <span className="font-bold text-purple-700">TeleMed AI v4.0</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500">Status:</span>
                    <span className="bg-emerald-100 text-emerald-700 text-[10px] font-extrabold px-2.5 py-0.5 rounded-full flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                      Active
                    </span>
                  </div>
                </>
              ) : (
                <>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Specialist:</span>
                    <span className="font-bold text-slate-800 truncate max-w-[130px]">{activeConv?.doctorName}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Specialty:</span>
                    <span className="font-bold text-slate-800">{activeConv?.specialty}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">ID:</span>
                    <span className="font-mono font-bold text-blue-600">{activeConv?.consultation_id}</span>
                  </div>
                  {activeConv?.appointment_date && (
                    <div className="flex justify-between">
                      <span className="text-slate-500">Slot:</span>
                      <span className="font-bold text-slate-800">{activeConv?.appointment_date}</span>
                    </div>
                  )}
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500">Status:</span>
                    <span className="bg-emerald-100 text-emerald-700 text-[10px] font-extrabold px-2 py-0.5 rounded-full">
                      {activeConv?.status || 'Active'}
                    </span>
                  </div>
                </>
              )}
            </div>

            {!activeConv?.isAi && activeConv?.consultation_id && (
              <button
                className="w-full py-2 px-3 border border-slate-200 bg-slate-50 hover:bg-slate-100 rounded-xl text-slate-700 font-bold text-xs flex items-center justify-center space-x-1.5 transition-all cursor-pointer"
                onClick={() => navigate('/consultations')}
              >
                <ExternalLink className="w-3.5 h-3.5 text-blue-600" />
                <span>View Full Consultation</span>
              </button>
            )}
          </div>

          {/* Care Actions Hub */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-4 space-y-3 shadow-lg shadow-slate-100/60">
            <div className="flex items-center space-x-2">
              <div className="w-7 h-7 rounded-lg bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-600">
                <Sparkles className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Quick Care Actions</h3>
            </div>

            <div className="space-y-2">
              <button
                onClick={() => navigate('/records')}
                className="w-full p-2.5 bg-slate-50 hover:bg-blue-50/70 border border-slate-200 hover:border-blue-300 rounded-xl text-xs font-bold text-slate-700 hover:text-blue-700 flex items-center justify-between transition-all cursor-pointer shadow-2xs group"
              >
                <div className="flex items-center space-x-2.5">
                  <FileText className="w-4 h-4 text-blue-600" />
                  <span>View Health Records</span>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
              </button>

              <button
                onClick={() => navigate('/report')}
                className="w-full p-2.5 bg-slate-50 hover:bg-emerald-50/70 border border-slate-200 hover:border-emerald-300 rounded-xl text-xs font-bold text-slate-700 hover:text-emerald-700 flex items-center justify-between transition-all cursor-pointer shadow-2xs group"
              >
                <div className="flex items-center space-x-2.5">
                  <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
                  <span>View AI Health Report</span>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
              </button>


            </div>
          </div>

        </div>

      </div>

      {/* ── SECURITY DETAILS MODAL ──────────────────────────────────────────── */}
      {showSecurityModal && (
        <Modal
          isOpen={showSecurityModal}
          onClose={() => setShowSecurityModal(false)}
          title="Security & Clinical Protocol"
        >
          <div className="space-y-3.5 text-xs text-slate-600 p-1">
            <p className="font-medium text-slate-800">Your clinical communication session is protected under active patient-doctor authentication controls:</p>
            <ul className="list-disc pl-5 space-y-1.5 text-slate-700 font-medium">
              <li>Role-authorized session verification for licensed physicians & patient.</li>
              <li>256-bit transport layer security for live messages and health telemetry data streams.</li>
              <li>Read-only authorization guards on medical records and diagnostic files.</li>
            </ul>
            <div className="pt-3 text-right">
              <Button size="sm" variant="primary" onClick={() => setShowSecurityModal(false)}>Close</Button>
            </div>
          </div>
        </Modal>
      )}

      {/* ── AI ENGINE INFO MODAL ───────────────────────────────────────────── */}
      {showAiInfoModal && (
        <Modal
          isOpen={showAiInfoModal}
          onClose={() => setShowAiInfoModal(false)}
          title="TeleMed AI Assistant Engine Details"
        >
          <div className="space-y-3.5 text-xs text-slate-600 p-1">
            <p><strong>Architecture:</strong> Multimodal RAG Engine v4.0</p>
            <p><strong>Evidence Sources:</strong> Integrated Clinical Biomarkers, Continuous Glucose Monitors, Apple/Fitbit Wearables, Ayumetrix Gut Microbiome Sequencing, and Peer-Reviewed Literature.</p>
            <div className="p-3 bg-purple-50 border border-purple-200 text-purple-900 rounded-xl space-y-1">
              <p className="font-bold flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-purple-600" /> Clinical Decision Support Notice
              </p>
              <p className="text-[11px] leading-relaxed">AI outputs provide evidence-based decision support. All clinical actions must be reviewed by your attending physician.</p>
            </div>
            <div className="pt-2 text-right">
              <Button size="sm" variant="primary" onClick={() => setShowAiInfoModal(false)}>Close</Button>
            </div>
          </div>
        </Modal>
      )}

      {/* ── ARCHIVE CONFIRMATION MODAL ──────────────────────────────────────── */}
      {showArchiveConfirm && (
        <Modal
          isOpen={showArchiveConfirm}
          onClose={() => setShowArchiveConfirm(false)}
          title="Confirm Thread Archive"
        >
          <div className="space-y-3.5 text-xs text-slate-600 p-1">
            <p>Are you sure you want to archive this communication thread? It can be retrieved anytime under the Saved tab.</p>
            <div className="flex justify-end space-x-2 pt-3">
              <Button size="sm" variant="outline" onClick={() => setShowArchiveConfirm(false)}>Cancel</Button>
              <Button size="sm" variant="primary" className="bg-rose-600 hover:bg-rose-700 text-white" onClick={confirmArchive}>Archive</Button>
            </div>
          </div>
        </Modal>
      )}

    </div>
  );
}
