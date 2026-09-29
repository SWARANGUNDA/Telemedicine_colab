import React, { useState, useEffect } from 'react';
import { Shield, ShieldAlert, PlusCircle, RefreshCw, LogOut, User, Stethoscope, Bell, Check, CheckCheck, X } from 'lucide-react';
import { fetchNotifications, markNotificationRead, markAllNotificationsRead } from '../api/client';

export default function Header({
  session,
  activeNav,
  activeSubNav,
  onStartNewAnalysis,
  onResetSession,
  user,
  onLogout
}) {
  const role = user?.role || 'PATIENT';
  const docStatus = user?.doctor_profile?.verification_status || 'PENDING';

  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifPanel, setShowNotifPanel] = useState(false);
  const [loadingNotifs, setLoadingNotifs] = useState(false);

  useEffect(() => {
    if (user) {
      loadNotifs();
      const interval = setInterval(loadNotifs, 10000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const loadNotifs = async () => {
    try {
      const data = await fetchNotifications();
      setNotifications(data.notifications || []);
      setUnreadCount(data.unread_count || 0);
    } catch (e) {
      // Non-blocking telemetry
    }
  };

  const handleMarkRead = async (id) => {
    try {
      await markNotificationRead(id);
      loadNotifs();
    } catch (e) {}
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      loadNotifs();
    } catch (e) {}
  };

  const renderRoleBadge = () => {
    if (role === 'ADMIN') {
      return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', padding: '4px 10px', borderRadius: '14px', background: 'rgba(245, 158, 11, 0.15)', border: '1px solid rgba(245, 158, 11, 0.4)', color: '#fbbf24', fontSize: '0.75rem', fontWeight: 700 }}>
          <Shield size={13} /> ADMIN
        </span>
      );
    }
    if (role === 'DOCTOR') {
      return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', padding: '4px 10px', borderRadius: '14px', background: docStatus === 'VERIFIED' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)', border: docStatus === 'VERIFIED' ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(245, 158, 11, 0.4)', color: docStatus === 'VERIFIED' ? '#10b981' : '#fbbf24', fontSize: '0.75rem', fontWeight: 700 }}>
          <Stethoscope size={13} /> DOCTOR [{docStatus}]
        </span>
      );
    }
    return (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', padding: '4px 10px', borderRadius: '14px', background: 'rgba(6, 182, 212, 0.15)', border: '1px solid rgba(6, 182, 212, 0.4)', color: 'var(--accent-cyan)', fontSize: '0.75rem', fontWeight: 700 }}>
        <User size={13} /> PATIENT
      </span>
    );
  };

  return (
    <header style={{
      background: 'var(--bg-sidebar)',
      borderBottom: '1px solid var(--border-subtle)',
      padding: '12px 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexWrap: 'wrap',
      gap: '16px',
      zIndex: 40,
      position: 'relative'
    }}>
      {/* Page Title & Breadcrumb */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.78rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          <span>TeleMed AI</span>
          <span>/</span>
          <span>{role} PORTAL</span>
          <span>/</span>
          <span style={{ color: 'var(--accent-cyan)' }}>{activeNav.replace(/_/g, ' ')}</span>
        </div>
        <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span>Generative AI Assisted Telemedicine Platform</span>
          {renderRoleBadge()}
        </div>
      </div>

      {/* Center Disclaimer */}
      <div style={{
        background: 'rgba(56, 189, 248, 0.08)',
        border: '1px solid rgba(56, 189, 248, 0.25)',
        borderRadius: '8px',
        padding: '6px 12px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        fontSize: '0.75rem',
        color: 'var(--accent-cyan)'
      }}>
        <ShieldAlert size={14} style={{ flexShrink: 0 }} />
        <span>Research Prototype trained on synthetic multimodal data. Not for unguided clinical diagnosis.</span>
      </div>

      {/* Right Controls & User Profile Menu */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {role === 'PATIENT' && (
          <button className="btn btn-outline" onClick={onStartNewAnalysis} style={{ fontSize: '0.8rem', padding: '6px 12px' }}>
            <PlusCircle size={14} /> New Intake
          </button>
        )}

        {/* Persistent In-App Notification Bell */}
        <div style={{ position: 'relative' }}>
          <button
            className="btn btn-outline"
            onClick={() => setShowNotifPanel(!showNotifPanel)}
            style={{ position: 'relative', padding: '6px 10px' }}
            title="In-App Notifications"
          >
            <Bell size={16} />
            {unreadCount > 0 && (
              <span style={{
                position: 'absolute', top: '-4px', right: '-4px',
                background: '#ef4444', color: '#ffffff', fontSize: '0.68rem',
                fontWeight: 800, padding: '2px 5px', borderRadius: '10px', minWidth: '16px', textAlign: 'center'
              }}>
                {unreadCount}
              </span>
            )}
          </button>

          {/* Notification Dropdown Panel */}
          {showNotifPanel && (
            <div className="glass-card" style={{
              position: 'absolute', right: 0, top: '42px', width: '360px',
              maxHeight: '420px', overflowY: 'auto', zIndex: 100, padding: '16px',
              boxShadow: '0 10px 25px rgba(0,0,0,0.5)', border: '1px solid var(--border-subtle)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
                <strong style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>Notifications ({unreadCount} Unread)</strong>
                {unreadCount > 0 && (
                  <button onClick={handleMarkAllRead} className="btn btn-outline" style={{ fontSize: '0.72rem', padding: '2px 8px' }}>
                    <CheckCheck size={12} style={{ marginRight: '4px' }} /> Mark All Read
                  </button>
                )}
              </div>

              {notifications.length === 0 ? (
                <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                  No in-app notifications.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {notifications.map(n => (
                    <div key={n.notification_id} style={{
                      padding: '10px', borderRadius: '8px',
                      background: n.is_read ? 'var(--bg-primary)' : 'rgba(6, 182, 212, 0.08)',
                      borderLeft: n.is_read ? '3px solid transparent' : '3px solid var(--accent-cyan)',
                      fontSize: '0.8rem'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <strong style={{ color: 'var(--text-main)', fontSize: '0.82rem' }}>{n.title}</strong>
                        {!n.is_read && (
                          <button onClick={() => handleMarkRead(n.notification_id)} style={{ background: 'none', border: 'none', color: 'var(--accent-cyan)', cursor: 'pointer', padding: 0 }}>
                            <Check size={14} />
                          </button>
                        )}
                      </div>
                      <div style={{ color: 'var(--text-muted)', marginTop: '4px', lineHeight: 1.4 }}>{n.message}</div>
                      <div style={{ color: 'var(--text-dim)', fontSize: '0.7rem', marginTop: '6px' }}>
                        {new Date(n.created_at).toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* User Card & Logout */}
        <div style={{
          background: 'rgba(30, 41, 59, 0.6)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: '8px',
          padding: '4px 10px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}>
          <div style={{ fontSize: '0.8rem', textAlign: 'right' }}>
            <div style={{ fontWeight: 600, color: '#f8fafc' }}>{user?.full_name || 'Authenticated User'}</div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>{user?.email}</div>
          </div>
          <button
            className="btn btn-outline"
            onClick={onLogout}
            style={{ fontSize: '0.75rem', padding: '6px 10px', color: '#f87171', borderColor: 'rgba(239, 68, 68, 0.3)' }}
            title="Log Out"
          >
            <LogOut size={14} />
          </button>
        </div>
      </div>
    </header>
  );
}
