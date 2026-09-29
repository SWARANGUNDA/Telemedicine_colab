import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader, PageContainer } from '../components/layout';
import { Card, Badge, Button, Tabs, EmptyState, Modal } from '../components/ui';
import {
  Bell, CheckCircle2, Trash2, Calendar, Sparkles, FileText, MessageSquare,
  ShieldAlert, Settings, Clock, Filter, Check, ShieldCheck, Mail, Send, Pill, UserCheck, ExternalLink
} from 'lucide-react';
import { fetchPatientRecords, fetchPatientConsultations } from '../api/client';
import { notificationStore } from '../utils/notificationStore';

export default function NotificationsPage({ user, predictionData }) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [selectedNotif, setSelectedNotif] = useState(null);
  const targetUserId = user?.user_id || 'default_user';
  const [notificationsList, setNotificationsList] = useState(() => notificationStore.getNotifications(targetUserId));
  const [statusMessage, setStatusMessage] = useState('');

  useEffect(() => {
    const syncNotifications = () => {
      setNotificationsList(notificationStore.getNotifications(targetUserId));
    };
    window.addEventListener('telemed_notifications_updated', syncNotifications);
    return () => window.removeEventListener('telemed_notifications_updated', syncNotifications);
  }, [targetUserId]);

  // Preferences Toggles State
  const [preferences, setPreferences] = useState({
    reminders: true,
    aiReports: true,
    doctorMessages: true,
    systemAnnouncements: true,
    emailAlerts: true,
    pushNotifications: false,
  });

  const handleMarkAsRead = (id) => {
    const updated = notificationStore.markAsRead(id, targetUserId);
    setNotificationsList(updated);
  };

  const handleOpenNotification = (notif) => {
    setSelectedNotif(notif);
    handleMarkAsRead(notif.id);
  };

  const handleMarkAllRead = () => {
    const updated = notificationStore.markAllAsRead(targetUserId);
    setNotificationsList(updated);
    setStatusMessage('All notifications marked as read.');
    setTimeout(() => setStatusMessage(''), 3000);
  };

  const handleDelete = (id, e) => {
    if (e) e.stopPropagation();
    const updated = notificationStore.deleteNotification(id, targetUserId);
    setNotificationsList(updated);
    if (selectedNotif?.id === id) {
      setSelectedNotif(null);
    }
  };

  const filteredNotifications = notificationsList.filter(n => {
    const matchesTab = activeTab === 'all' || (activeTab === 'unread' && !n.isRead);
    const matchesCat = categoryFilter === 'ALL' || n.category === categoryFilter;
    return matchesTab && matchesCat;
  });

  const unreadCount = notificationsList.filter(n => !n.isRead).length;

  const getCategoryIcon = (cat) => {
    switch (cat) {
      case 'Appointments': return Calendar;
      case 'AI Analysis': return Sparkles;
      case 'Reports': return FileText;
      case 'Messages': return MessageSquare;
      case 'Prescriptions': return Pill;
      default: return ShieldAlert;
    }
  };

  return (
    <PageContainer className="space-y-4 py-4">
      
      {/* Header */}
      <PageHeader
        title="Notification Center & Alert Settings"
        description="Real-time clinical alerts, AI assessment updates, physician messages, and communication preferences"
        badge="Communication Hub"
        actions={
          <Button variant="outline" size="sm" leftIcon={<CheckCircle2 className="w-4 h-4" />} onClick={handleMarkAllRead}>
            Mark All as Read
          </Button>
        }
      />

      {statusMessage && (
        <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold font-mono animate-fade-in flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Tabs */}
      <Tabs
        activeTab={activeTab}
        onChange={setActiveTab}
        tabs={[
          { id: 'all', label: `All Alerts (${notificationsList.length})` },
          { id: 'unread', label: `Unread (${unreadCount})` },
          { id: 'preferences', label: 'Alert Preferences' },
        ]}
      />

      {/* TABS 1 & 2: CLICKABLE COMPACT NOTIFICATIONS LIST */}
      {(activeTab === 'all' || activeTab === 'unread') && (
        <div className="space-y-3 animate-fade-in">
          
          {/* Category Filter Bar */}
          <div className="flex items-center justify-between bg-[var(--bg-surface)] px-3 py-2 rounded-xl border border-[var(--border-subtle)]">
            <span className="text-[11px] font-mono font-bold text-[var(--text-muted)] uppercase tracking-wider">Filter Category</span>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="px-2.5 py-1 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] font-medium focus:outline-none focus:border-[var(--primary)]"
            >
              <option value="ALL">All Categories</option>
              <option value="AI Analysis">AI Analysis</option>
              <option value="Prescriptions">Prescriptions</option>
              <option value="Messages">Messages</option>
              <option value="Appointments">Appointments</option>
              <option value="Reports">Reports</option>
            </select>
          </div>

          {filteredNotifications.length === 0 ? (
            <Card isGlass={true} className="p-8 text-center space-y-2 border border-[var(--border-subtle)]">
              <Bell className="w-8 h-8 text-[var(--text-muted)] mx-auto opacity-50" />
              <h3 className="text-sm font-bold text-[var(--text-main)]">No Alerts Found</h3>
              <p className="text-xs text-[var(--text-muted)]">No notifications match your current filter selection.</p>
            </Card>
          ) : (
            <div className="space-y-2.5">
              {filteredNotifications.map((n) => {
                const Icon = getCategoryIcon(n.category);
                return (
                  <div
                    key={n.id}
                    onClick={() => handleOpenNotification(n)}
                    className={`p-3.5 rounded-2xl border cursor-pointer transition-all space-y-2 group ${
                      !n.isRead
                        ? 'bg-[var(--bg-surface)] border-l-4 border-l-[var(--primary)] border-[var(--border-medium)] shadow-md hover:border-[var(--primary)] hover:shadow-lg'
                        : 'bg-[var(--bg-primary)] border-[var(--border-subtle)] opacity-85 hover:border-[var(--primary)] hover:opacity-100'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3 flex-wrap">
                      <div className="flex items-center gap-2.5 min-w-0 flex-1">
                        <div className="p-2 rounded-xl bg-[var(--primary-light)] text-[var(--primary)] shrink-0 group-hover:scale-105 transition-transform">
                          <Icon className="w-4 h-4" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h4 className="text-xs font-black text-[var(--text-main)] group-hover:text-[var(--primary)] transition-colors truncate">
                              {n.title}
                            </h4>
                            <Badge variant={n.category === 'AI Analysis' ? 'primary' : (n.category === 'Prescriptions' ? 'success' : 'secondary')} size="sm" className="text-[9px] font-mono">
                              {n.category}
                            </Badge>
                            {!n.isRead && (
                              <span className="w-2 h-2 rounded-full bg-[var(--primary)] animate-pulse shrink-0" />
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <Badge variant={n.priority === 'HIGH' ? 'danger' : 'warning'} size="sm" className="text-[9px] font-mono">
                          {n.priority}
                        </Badge>
                        <span className="text-[10px] font-mono text-[var(--text-muted)]">{n.timestamp}</span>
                      </div>
                    </div>

                    <p className="text-xs text-[var(--text-muted)] leading-relaxed pl-9 font-medium line-clamp-2">
                      {n.description}
                    </p>

                    <div className="flex items-center justify-between pt-1 pl-9 border-t border-[var(--border-subtle)]/50">
                      <span className="text-[10px] font-mono text-[var(--primary)] font-bold group-hover:underline flex items-center gap-1">
                        Click to view details & open &rarr;
                      </span>
                      <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                        {!n.isRead && (
                          <button
                            onClick={() => handleMarkAsRead(n.id)}
                            className="text-[11px] font-bold text-[var(--primary)] hover:underline px-2 py-0.5 rounded hover:bg-[var(--primary-light)] transition-colors"
                          >
                            Mark Read
                          </button>
                        )}
                        <button
                          onClick={(e) => handleDelete(n.id, e)}
                          className="text-[11px] font-bold text-red-400 hover:text-red-300 hover:underline px-2 py-0.5 rounded hover:bg-red-500/10 transition-colors flex items-center gap-1"
                        >
                          <Trash2 className="w-3 h-3" />
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: ALERT PREFERENCES */}
      {activeTab === 'preferences' && (
        <Card isGlass={true} className="p-5 space-y-4 animate-fade-in shadow-xl max-w-3xl border border-[var(--border-medium)]">
          <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
            <div>
              <h3 className="text-sm font-bold text-[var(--text-main)]">Alert Notification Settings</h3>
              <p className="text-xs text-[var(--text-muted)]">Configure real-time teleconsultation and AI report channels</p>
            </div>
            <Badge variant="success" size="sm" className="font-mono">PREFERENCES ACTIVE</Badge>
          </div>

          <div className="space-y-2.5 text-xs">
            {[
              { id: 'reminders', label: 'Appointment Reminders', desc: 'Receive alerts 24 hours & 30 mins before teleconsultations' },
              { id: 'aiReports', label: 'AI Report Completion', desc: 'Alert when multimodal predictions & TreeSHAP drivers finish' },
              { id: 'doctorMessages', label: 'Physician Direct Messages', desc: 'Notify when your doctor sends a new message or prescription' },
              { id: 'systemAnnouncements', label: 'System & Maintenance Updates', desc: 'Platform feature updates & compliance logs' },
              { id: 'emailAlerts', label: 'Email Notifications', desc: 'Send summary alerts to registered email address' },
              { id: 'pushNotifications', label: 'Push Notifications', desc: 'Browser push alerts when platform is running' },
            ].map((pref) => (
              <div key={pref.id} className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] hover:border-[var(--primary)] transition-all">
                <div>
                  <strong className="text-xs text-[var(--text-main)] block">{pref.label}</strong>
                  <span className="text-[11px] text-[var(--text-muted)]">{pref.desc}</span>
                </div>
                <input
                  type="checkbox"
                  checked={preferences[pref.id]}
                  onChange={(e) => setPreferences({ ...preferences, [pref.id]: e.target.checked })}
                  className="w-4 h-4 rounded text-[var(--primary)] focus:ring-[var(--primary)] cursor-pointer"
                />
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* NOTIFICATION DETAIL DIALOG MODAL */}
      {selectedNotif && (
        <Modal
          isOpen={!!selectedNotif}
          onClose={() => setSelectedNotif(null)}
          title={`Clinical Notification Detail | ${selectedNotif.id}`}
          className="max-w-lg border border-[var(--primary)]/30 shadow-2xl"
        >
          <div className="space-y-4 p-1 text-xs">
            
            {/* Category & Priority Badge Header */}
            <div className="flex items-center justify-between flex-wrap gap-2 pb-3 border-b border-[var(--border-subtle)]">
              <div className="flex items-center gap-2">
                <Badge variant="primary" size="sm" className="font-mono">{selectedNotif.category}</Badge>
                <Badge variant={selectedNotif.priority === 'HIGH' ? 'danger' : 'warning'} size="sm" className="font-mono">
                  {selectedNotif.priority} PRIORITY
                </Badge>
              </div>
              <span className="text-[11px] font-mono text-[var(--text-muted)]">{selectedNotif.timestamp}</span>
            </div>

            {/* Notification Title */}
            <div>
              <h3 className="text-base font-extrabold text-[var(--text-main)]">{selectedNotif.title}</h3>
              <p className="text-[11px] font-mono text-[var(--primary)] font-semibold mt-0.5">Reference ID: {selectedNotif.id}</p>
            </div>

            {/* Detailed Content */}
            <div className="p-3.5 rounded-2xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] space-y-2 text-xs leading-relaxed">
              <p className="text-[var(--text-main)] font-medium">{selectedNotif.description}</p>
              {selectedNotif.details && (
                <p className="text-[var(--text-muted)] text-[11px] border-t border-[var(--border-subtle)]/50 pt-2 font-mono">
                  {selectedNotif.details}
                </p>
              )}
            </div>

            {/* Modal Actions */}
            <div className="pt-2 flex items-center justify-between gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDelete(selectedNotif.id)}
                className="text-red-400 border-red-500/30 hover:bg-red-500/10"
              >
                Delete Alert
              </Button>

              <div className="flex items-center gap-2">
                {selectedNotif.actionRoute && (
                  <Button
                    variant="primary"
                    size="sm"
                    leftIcon={<ExternalLink className="w-3.5 h-3.5" />}
                    onClick={() => {
                      let route = selectedNotif.actionRoute;
                      if (user?.role === 'DOCTOR' && route === '/intake') route = '/doctor/dashboard';
                      if (user?.role === 'ADMIN' && route === '/intake') route = '/admin/dashboard';
                      setSelectedNotif(null);
                      navigate(route);
                    }}
                  >
                    {user?.role === 'DOCTOR' && selectedNotif.actionRoute === '/intake'
                      ? 'Open Doctor Dashboard'
                      : user?.role === 'ADMIN' && selectedNotif.actionRoute === '/intake'
                      ? 'Open Admin Overview'
                      : selectedNotif.actionLabel || 'Open Workspace'}
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedNotif(null)}
                >
                  Close
                </Button>
              </div>
            </div>

          </div>
        </Modal>
      )}

    </PageContainer>
  );
}
