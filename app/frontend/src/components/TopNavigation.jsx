import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom';
import {
  LayoutDashboard, PlusCircle, ShieldCheck, Brain, FileText,
  FolderClock, HeartHandshake, UserCheck, Users, Stethoscope, Shield,
  Clock, Lock, Settings, History, Calendar, Bell, Check, CheckCheck,
  ChevronDown, Menu, X, LogOut, User, ShieldAlert, Sparkles, Sun, Moon, Monitor, Activity
} from 'lucide-react';
import { fetchNotifications, markNotificationRead, markAllNotificationsRead } from '../api/client';

export default function TopNavigation({
  activeNav,
  activeSubNav,
  onNavigate,
  isPredictionComplete,
  user,
  onStartNewAnalysis,
  onLogout,
  isDemoActive,
  onToggleDemo,
  onOpenComparison,
  themeMode = 'system',
  setThemeMode
}) {
  const role = user?.role || 'PATIENT';
  const docStatus = user?.doctor_profile?.verification_status || 'PENDING';

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showHealthMenu, setShowHealthMenu] = useState(false);
  const [showMoreMenu, setShowMoreMenu] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showNotifPanel, setShowNotifPanel] = useState(false);

  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  const bellRef = useRef(null);
  const notifPanelRef = useRef(null);
  const healthRef = useRef(null);
  const moreRef = useRef(null);
  const profileRef = useRef(null);

  // Poll Notifications
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

  const handleMarkRead = async (id, e) => {
    if (e) e.stopPropagation();
    try {
      await markNotificationRead(id);
      loadNotifs();
    } catch (err) {}
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      loadNotifs();
    } catch (err) {}
  };

  // Close dropdowns on outside click or Escape key
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (bellRef.current && !bellRef.current.contains(e.target) && notifPanelRef.current && !notifPanelRef.current.contains(e.target)) {
        setShowNotifPanel(false);
      }
      if (healthRef.current && !healthRef.current.contains(e.target)) {
        setShowHealthMenu(false);
      }
      if (moreRef.current && !moreRef.current.contains(e.target)) {
        setShowMoreMenu(false);
      }
      if (profileRef.current && !profileRef.current.contains(e.target)) {
        setShowProfileMenu(false);
      }
    };

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setShowNotifPanel(false);
        setShowHealthMenu(false);
        setShowMoreMenu(false);
        setShowProfileMenu(false);
        setMobileMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleOutsideClick);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  // Configure role-aware navigation groups
  let navItems = [];
  let moreItems = [];

  if (role === 'PATIENT') {
    navItems = [
      { type: 'link', key: 'dashboard', label: 'Home', icon: LayoutDashboard, nav: 'dashboard', subNav: '' },
      {
        type: 'dropdown',
        key: 'health',
        label: 'Health',
        icon: Activity,
        items: [
          { key: 'new_analysis', label: 'Health Analysis', icon: PlusCircle, nav: 'analysis', subNav: 'new_analysis' },
          { key: 'risk_dashboard', label: 'Risk Assessment', icon: ShieldCheck, nav: 'results', subNav: 'risk_dashboard', locked: !isPredictionComplete },
          { key: 'xai', label: 'XAI Explainability', icon: Brain, nav: 'results', subNav: 'xai', locked: !isPredictionComplete },
          { key: 'records', label: 'Health Records', icon: FolderClock, nav: 'records', subNav: 'reports_history' }
        ]
      },
      { type: 'link', key: 'ai_assistant', label: 'AI Assistant', icon: Brain, nav: 'results', subNav: 'report', locked: !isPredictionComplete },
      { type: 'link', key: 'consultations', label: 'Consult', icon: HeartHandshake, nav: 'consultations', subNav: '' },
    ];

    moreItems = [
      { key: 'report', label: 'AI Clinical Report', icon: FileText, nav: 'results', subNav: 'report', locked: !isPredictionComplete },
      { key: 'appointments', label: 'Appointments', icon: Calendar, nav: 'appointments', subNav: '' },
      { key: 'records_history', label: 'Assessment History', icon: FolderClock, nav: 'records', subNav: 'reports_history' },
      { key: 'patient_privacy', label: 'Data & Privacy', icon: Lock, nav: 'patient_privacy', subNav: '' },
      { key: 'account', label: 'Account Settings', icon: UserCheck, nav: 'account', subNav: 'settings' }
    ];
  } else if (role === 'DOCTOR') {
    navItems = [
      { type: 'link', key: 'dashboard', label: 'Home', icon: LayoutDashboard, nav: 'dashboard', subNav: '' },
      { type: 'link', key: 'assigned_patients', label: 'Patients', icon: Users, nav: 'assigned_patients', subNav: '', locked: docStatus !== 'VERIFIED' },
      { type: 'link', key: 'consultations', label: 'Consultations', icon: HeartHandshake, nav: 'assigned_patients', subNav: '', locked: docStatus !== 'VERIFIED' },
      { type: 'link', key: 'appointments', label: 'Schedule', icon: Calendar, nav: 'appointments', subNav: '', locked: docStatus !== 'VERIFIED' },
    ];

    moreItems = [
      { key: 'verification', label: 'Doctor Verification', icon: Clock, nav: 'verification', subNav: '', badge: docStatus },
      { key: 'account', label: 'Doctor Profile', icon: Stethoscope, nav: 'account', subNav: 'profile' }
    ];
  } else if (role === 'ADMIN') {
    navItems = [
      { type: 'link', key: 'admin_dashboard', label: 'Overview', icon: LayoutDashboard, nav: 'admin_dashboard', subNav: '' },
      { type: 'link', key: 'admin_verification', label: 'Doctors', icon: Stethoscope, nav: 'admin_verification', subNav: '' },
      { type: 'link', key: 'admin_assignments', label: 'Consultations', icon: HeartHandshake, nav: 'admin_assignments', subNav: '' },
      { type: 'link', key: 'admin_users', label: 'Users', icon: Users, nav: 'admin_users', subNav: '' },
    ];

    moreItems = [
      { key: 'appointments', label: 'Appointments', icon: Calendar, nav: 'appointments', subNav: '' },
      { key: 'admin_system', label: 'System Operations', icon: Settings, nav: 'admin_system', subNav: '' },
      { key: 'admin_audit', label: 'Audit & Governance', icon: History, nav: 'admin_audit', subNav: '' }
    ];
  }

  const isItemActive = (item) => {
    if (!item) return false;
    if (item.type === 'dropdown') {
      return item.items?.some(child => activeNav === child.nav && (!child.subNav || activeSubNav === child.subNav));
    }
    if (activeNav === item.nav) {
      if (!item.subNav || activeSubNav === item.subNav) return true;
    }
    return false;
  };

  const renderRoleBadge = () => {
    if (role === 'ADMIN') {
      return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', padding: '2px 8px', borderRadius: '12px', background: 'rgba(245, 158, 11, 0.15)', border: '1px solid rgba(245, 158, 11, 0.4)', color: '#fbbf24', fontSize: '0.72rem', fontWeight: 700 }}>
          <Shield size={11} /> ADMIN
        </span>
      );
    }
    if (role === 'DOCTOR') {
      return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', padding: '2px 8px', borderRadius: '12px', background: docStatus === 'VERIFIED' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)', border: docStatus === 'VERIFIED' ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(245, 158, 11, 0.4)', color: docStatus === 'VERIFIED' ? '#10b981' : '#fbbf24', fontSize: '0.72rem', fontWeight: 700 }}>
          <Stethoscope size={11} /> DOCTOR [{docStatus}]
        </span>
      );
    }
    return (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', padding: '2px 8px', borderRadius: '12px', background: 'rgba(6, 182, 212, 0.15)', border: '1px solid rgba(6, 182, 212, 0.4)', color: 'var(--accent-cyan)', fontSize: '0.72rem', fontWeight: 700 }}>
        <User size={11} /> PATIENT
      </span>
    );
  };

  // Notification Portal Dropdown Position Calculation
  let bellRect = bellRef.current ? bellRef.current.getBoundingClientRect() : null;
  const notifTop = bellRect ? bellRect.bottom + 8 : 64;
  const notifRight = bellRect ? window.innerWidth - bellRect.right : 24;

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 1000,
      background: 'var(--bg-primary)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid var(--border-subtle)',
      height: '64px',
      color: 'var(--text-main)',
      width: '100%'
    }}>
      <div className="top-nav-inner" style={{
        maxWidth: '1600px',
        width: 'calc(100% - 48px)',
        margin: '0 auto',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxSizing: 'border-box'
      }}>
        {/* BRAND & LOGO */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <div
          onClick={() => onNavigate('dashboard')}
          style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}
        >
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-blue))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#ffffff',
            fontWeight: 800,
            fontSize: '1.1rem',
            boxShadow: '0 4px 12px rgba(6, 182, 212, 0.3)'
          }}>
            T
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: '1.1rem', letterSpacing: '-0.02em', color: 'var(--text-main)', lineHeight: 1.1 }}>
              TeleMed <span style={{ color: 'var(--accent-cyan)' }}>AI</span>
            </div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', fontWeight: 600, letterSpacing: '0.04em' }}>
              V3.3 CLINICAL PLATFORM
            </div>
          </div>
        </div>

        {/* PRIMARY ROLE NAVIGATION (DESKTOP) */}
        <nav className="desktop-top-nav" style={{ display: 'flex', alignItems: 'center', gap: '4px', marginLeft: '12px' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isItemActive(item);

            if (item.type === 'dropdown') {
              return (
                <div key={item.key} ref={healthRef} style={{ position: 'relative' }}>
                  <button
                    onClick={() => setShowHealthMenu(!showHealthMenu)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      border: 'none',
                      background: active || showHealthMenu ? 'rgba(6, 182, 212, 0.15)' : 'transparent',
                      color: active || showHealthMenu ? 'var(--accent-cyan)' : 'var(--text-muted)',
                      fontWeight: active ? 700 : 500,
                      fontSize: '0.84rem',
                      cursor: 'pointer'
                    }}
                  >
                    <Icon size={16} />
                    <span>{item.label}</span>
                    <ChevronDown size={14} />
                  </button>

                  {showHealthMenu && (
                    <div className="glass-card" style={{
                      position: 'absolute',
                      top: '100%',
                      left: 0,
                      marginTop: '8px',
                      minWidth: '200px',
                      padding: '6px',
                      zIndex: 1100,
                      boxShadow: 'var(--shadow-lg)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '10px',
                      background: 'var(--bg-surface)'
                    }}>
                      {item.items.map((subItem) => {
                        const SubIcon = subItem.icon;
                        const subActive = activeNav === subItem.nav && (!subItem.subNav || activeSubNav === subItem.subNav);
                        return (
                          <button
                            key={subItem.key}
                            disabled={subItem.locked}
                            onClick={() => {
                              onNavigate(subItem.nav, subItem.subNav);
                              setShowHealthMenu(false);
                            }}
                            style={{
                              width: '100%',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '8px',
                              padding: '8px 12px',
                              borderRadius: '6px',
                              border: 'none',
                              background: subActive ? 'rgba(6, 182, 212, 0.15)' : 'transparent',
                              color: subItem.locked ? 'var(--text-dim)' : (subActive ? 'var(--accent-cyan)' : 'var(--text-main)'),
                              fontSize: '0.83rem',
                              cursor: subItem.locked ? 'not-allowed' : 'pointer',
                              textAlign: 'left',
                              opacity: subItem.locked ? 0.5 : 1
                            }}
                            title={subItem.locked ? "Complete prediction first to unlock" : subItem.label}
                          >
                            <SubIcon size={15} />
                            <span>{subItem.label}</span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            }

            return (
              <button
                key={item.key}
                disabled={item.locked}
                onClick={() => onNavigate(item.nav, item.subNav)}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  border: 'none',
                  background: active ? 'rgba(6, 182, 212, 0.15)' : 'transparent',
                  color: item.locked ? 'var(--text-dim)' : (active ? 'var(--accent-cyan)' : 'var(--text-muted)'),
                  fontWeight: active ? 700 : 500,
                  fontSize: '0.84rem',
                  cursor: item.locked ? 'not-allowed' : 'pointer',
                  transition: 'all 0.15s ease',
                  opacity: item.locked ? 0.5 : 1,
                  position: 'relative'
                }}
                title={item.locked ? "Complete prediction first to unlock" : item.label}
              >
                <Icon size={16} />
                <span>{item.label}</span>
              </button>
            );
          })}

          {/* MORE DROPDOWN */}
          {moreItems.length > 0 && (
            <div ref={moreRef} style={{ position: 'relative' }}>
              <button
                onClick={() => setShowMoreMenu(!showMoreMenu)}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  border: 'none',
                  background: showMoreMenu || moreItems.some(i => isItemActive(i)) ? 'rgba(6, 182, 212, 0.15)' : 'transparent',
                  color: showMoreMenu || moreItems.some(i => isItemActive(i)) ? 'var(--accent-cyan)' : 'var(--text-muted)',
                  fontWeight: moreItems.some(i => isItemActive(i)) ? 700 : 500,
                  fontSize: '0.84rem',
                  cursor: 'pointer'
                }}
              >
                <span>More</span>
                <ChevronDown size={14} />
              </button>

              {showMoreMenu && (
                <div className="glass-card" style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  marginTop: '8px',
                  minWidth: '200px',
                  padding: '6px',
                  zIndex: 1100,
                  boxShadow: 'var(--shadow-lg)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '10px',
                  background: 'var(--bg-surface)'
                }}>
                  {moreItems.map((item) => {
                    const Icon = item.icon;
                    const active = isItemActive(item);
                    return (
                      <button
                        key={item.key}
                        disabled={item.locked}
                        onClick={() => {
                          onNavigate(item.nav, item.subNav);
                          setShowMoreMenu(false);
                        }}
                        style={{
                          width: '100%',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          padding: '8px 12px',
                          borderRadius: '6px',
                          border: 'none',
                          background: active ? 'rgba(6, 182, 212, 0.15)' : 'transparent',
                          color: item.locked ? 'var(--text-dim)' : (active ? 'var(--accent-cyan)' : 'var(--text-main)'),
                          fontSize: '0.83rem',
                          cursor: item.locked ? 'not-allowed' : 'pointer',
                          textAlign: 'left',
                          opacity: item.locked ? 0.5 : 1
                        }}
                      >
                        <Icon size={15} />
                        <span>{item.label}</span>
                        {item.badge && (
                          <span style={{ fontSize: '0.65rem', padding: '1px 5px', borderRadius: '4px', background: 'rgba(245,158,11,0.2)', color: '#fbbf24', marginLeft: 'auto' }}>
                            {item.badge}
                          </span>
                        )}
                      </button>
                    );
                  })}

                </div>
              )}
            </div>
          )}
        </nav>
      </div>

      {/* RIGHT CONTROLS (Quick Action, Theme Toggle, Bell, User Profile, Hamburger) */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Action CTA Button (Patient Only) */}
        {role === 'PATIENT' && (
          <button
            className="btn btn-primary"
            onClick={onStartNewAnalysis}
            style={{ fontSize: '0.8rem', padding: '6px 14px', borderRadius: '8px', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <PlusCircle size={15} /> <span>+ New Intake</span>
          </button>
        )}

        {/* COMPACT THEME SELECTOR */}
        {typeof setThemeMode === 'function' && (
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-medium)',
            borderRadius: '8px',
            padding: '2px'
          }}>
            <button
              onClick={() => setThemeMode('light')}
              style={{
                background: themeMode === 'light' ? 'var(--accent-cyan)' : 'transparent',
                color: themeMode === 'light' ? '#ffffff' : 'var(--text-muted)',
                border: 'none',
                borderRadius: '6px',
                padding: '5px 8px',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center'
              }}
              title="Light Mode"
            >
              <Sun size={14} />
            </button>
            <button
              onClick={() => setThemeMode('dark')}
              style={{
                background: themeMode === 'dark' ? 'var(--accent-cyan)' : 'transparent',
                color: themeMode === 'dark' ? '#ffffff' : 'var(--text-muted)',
                border: 'none',
                borderRadius: '6px',
                padding: '5px 8px',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center'
              }}
              title="Dark Mode"
            >
              <Moon size={14} />
            </button>
            <button
              onClick={() => setThemeMode('system')}
              style={{
                background: themeMode === 'system' ? 'var(--accent-cyan)' : 'transparent',
                color: themeMode === 'system' ? '#ffffff' : 'var(--text-muted)',
                border: 'none',
                borderRadius: '6px',
                padding: '5px 8px',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center'
              }}
              title="System OS Theme"
            >
              <Monitor size={14} />
            </button>
          </div>
        )}

        {/* NOTIFICATION BELL */}
        <div ref={bellRef} style={{ position: 'relative' }}>
          <button
            className="btn btn-outline"
            onClick={() => setShowNotifPanel(!showNotifPanel)}
            style={{
              position: 'relative',
              padding: '8px 10px',
              borderRadius: '8px',
              background: showNotifPanel ? 'rgba(6, 182, 212, 0.15)' : 'transparent',
              borderColor: showNotifPanel ? 'var(--accent-cyan)' : 'rgba(255,255,255,0.12)'
            }}
            title="In-App Notifications"
          >
            <Bell size={18} />
            {unreadCount > 0 && (
              <span style={{
                position: 'absolute', top: '-4px', right: '-4px',
                background: '#ef4444', color: '#ffffff', fontSize: '0.68rem',
                fontWeight: 800, padding: '2px 6px', borderRadius: '10px', minWidth: '16px', textAlign: 'center'
              }}>
                {unreadCount}
              </span>
            )}
          </button>
        </div>

        {/* USER PROFILE DROPDOWN */}
        <div ref={profileRef} style={{ position: 'relative' }}>
          <button
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '4px 10px',
              borderRadius: '8px',
              background: 'rgba(30, 41, 59, 0.7)',
              border: '1px solid rgba(255,255,255,0.12)',
              cursor: 'pointer',
              color: '#ffffff'
            }}
          >
            <div style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '0.8rem'
            }}>
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="desktop-only-text" style={{ fontSize: '0.8rem', textAlign: 'left', lineHeight: 1.2 }}>
              <div style={{ fontWeight: 600 }}>{user?.full_name || 'User'}</div>
              <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>{role}</div>
            </div>
            <ChevronDown size={14} color="#94a3b8" />
          </button>

          {showProfileMenu && (
            <div className="glass-card" style={{
              position: 'absolute',
              top: '100%',
              right: 0,
              marginTop: '8px',
              width: '240px',
              padding: '12px',
              zIndex: 1100,
              boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '12px'
            }}>
              <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px', marginBottom: '8px' }}>
                <div style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--text-main)' }}>{user?.full_name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{user?.email}</div>
                <div style={{ marginTop: '6px' }}>{renderRoleBadge()}</div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <button
                  onClick={() => { onNavigate('account'); setShowProfileMenu(false); }}
                  style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', borderRadius: '6px', border: 'none', background: 'transparent', color: 'var(--text-muted)', fontSize: '0.82rem', cursor: 'pointer', textAlign: 'left' }}
                >
                  <User size={15} /> Account Settings
                </button>

                {role === 'PATIENT' && (
                  <button
                    onClick={() => { onNavigate('patient_privacy'); setShowProfileMenu(false); }}
                    style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', borderRadius: '6px', border: 'none', background: 'transparent', color: 'var(--text-muted)', fontSize: '0.82rem', cursor: 'pointer', textAlign: 'left' }}
                  >
                    <Lock size={15} /> Data & Privacy
                  </button>
                )}

                <button
                  onClick={() => { onLogout(); setShowProfileMenu(false); }}
                  style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', borderRadius: '6px', border: 'none', background: 'rgba(239, 68, 68, 0.1)', color: '#f87171', fontSize: '0.82rem', cursor: 'pointer', textAlign: 'left', marginTop: '4px' }}
                >
                  <LogOut size={15} /> Log Out
                </button>
              </div>
            </div>
          )}
        </div>

        {/* MOBILE HAMBURGER TOGGLE */}
        <button
          className="mobile-hamburger-btn"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          style={{ background: 'transparent', border: 'none', color: '#ffffff', cursor: 'pointer', padding: '6px' }}
        >
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>
      </div>

      {/* MOBILE NAV DRAWER OVERLAY */}
      {mobileMenuOpen && (
        <div className="glass-card" style={{
          position: 'fixed',
          top: '64px',
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(11, 17, 32, 0.98)',
          backdropFilter: 'blur(20px)',
          zIndex: 2000,
          padding: '20px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>{role} Navigation</span>
            {renderRoleBadge()}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {navItems.flatMap(item => item.type === 'dropdown' ? item.items : [item]).concat(moreItems).map((item) => {
              const Icon = item.icon;
              const active = isItemActive(item);
              return (
                <button
                  key={item.key}
                  disabled={item.locked}
                  onClick={() => {
                    onNavigate(item.nav, item.subNav);
                    setMobileMenuOpen(false);
                  }}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '12px 16px',
                    borderRadius: '10px',
                    border: 'none',
                    background: active ? 'rgba(6, 182, 212, 0.15)' : 'rgba(30, 41, 59, 0.5)',
                    color: item.locked ? 'var(--text-dim)' : (active ? 'var(--accent-cyan)' : 'var(--text-main)'),
                    fontWeight: active ? 700 : 500,
                    fontSize: '0.92rem',
                    cursor: item.locked ? 'not-allowed' : 'pointer',
                    textAlign: 'left'
                  }}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* FLOATING NOTIFICATION BELL PORTAL */}
      {showNotifPanel && ReactDOM.createPortal(
        (() => {
          const isMobile = window.innerWidth < 768;
          const { today, earlier, read } = (() => {
            const todayStr = new Date().toDateString();
            const t = [], e = [], r = [];
            notifications.forEach(n => {
              if (n.is_read) {
                r.push(n);
              } else if (new Date(n.created_at).toDateString() === todayStr) {
                t.push(n);
              } else {
                e.push(n);
              }
            });
            return { today: t, earlier: e, read: r };
          })();

          const getNotifIcon = (nType) => {
            const t = (nType || '').toUpperCase();
            if (t.includes('APPOINTMENT')) return <Calendar size={16} style={{ color: 'var(--accent-emerald)', flexShrink: 0 }} />;
            if (t.includes('CONSULT')) return <Stethoscope size={16} style={{ color: 'var(--accent-cyan)', flexShrink: 0 }} />;
            if (t.includes('VERIF')) return <ShieldCheck size={16} style={{ color: 'var(--accent-amber)', flexShrink: 0 }} />;
            if (t.includes('REPORT') || t.includes('ANALYSIS')) return <Activity size={16} style={{ color: 'var(--accent-cyan)', flexShrink: 0 }} />;
            return <Bell size={16} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />;
          };

          const handleNotifClick = async (n) => {
            if (!n.is_read) {
              await handleMarkRead(n.notification_id);
            }
            const targetNav = n.link_nav || n.action_url || '';
            if (targetNav) {
              onNavigate(targetNav);
            }
            setShowNotifPanel(false);
          };

          const renderGroup = (title, items) => {
            if (!items || items.length === 0) return null;
            return (
              <div style={{ marginBottom: '14px' }}>
                <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', tracking: '0.05em', marginBottom: '8px', paddingLeft: '4px' }}>
                  {title} ({items.length})
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {items.map(n => (
                    <div
                      key={n.notification_id}
                      onClick={() => handleNotifClick(n)}
                      style={{
                        padding: '12px 14px',
                        borderRadius: '10px',
                        background: n.is_read ? 'var(--bg-primary)' : 'rgba(6, 182, 212, 0.08)',
                        borderLeft: n.is_read ? '3px solid transparent' : '3px solid var(--accent-cyan)',
                        border: '1px solid var(--border-subtle)',
                        fontSize: '0.82rem',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                        display: 'flex',
                        gap: '10px',
                        alignItems: 'flex-start'
                      }}
                    >
                      {getNotifIcon(n.type)}
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '6px' }}>
                          <strong style={{ color: 'var(--text-main)', fontSize: '0.85rem', fontWeight: n.is_read ? 600 : 700 }}>
                            {n.title}
                          </strong>
                          {!n.is_read && (
                            <button
                              onClick={(e) => handleMarkRead(n.notification_id, e)}
                              style={{ background: 'none', border: 'none', color: 'var(--accent-cyan)', cursor: 'pointer', padding: '2px', flexShrink: 0 }}
                              title="Mark Read"
                            >
                              <Check size={14} />
                            </button>
                          )}
                        </div>
                        <div style={{ color: 'var(--text-muted)', marginTop: '4px', lineHeight: 1.4, fontSize: '0.82rem' }}>
                          {n.message}
                        </div>
                        <div style={{ color: 'var(--text-dim)', fontSize: '0.72rem', marginTop: '6px' }}>
                          {new Date(n.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          };

          return (
            <div
              ref={notifPanelRef}
              className="glass-card"
              style={{
                position: 'fixed',
                ...(isMobile
                  ? {
                      bottom: 0,
                      left: 0,
                      right: 0,
                      width: '100vw',
                      maxHeight: '80vh',
                      borderRadius: '20px 20px 0 0',
                      boxShadow: '0 -20px 50px rgba(0,0,0,0.7)',
                    }
                  : {
                      top: `${notifTop}px`,
                      right: `${notifRight}px`,
                      width: 'min(420px, 92vw)',
                      maxHeight: '480px',
                      borderRadius: '14px',
                      boxShadow: '0 20px 40px rgba(0,0,0,0.6)',
                    }),
                overflowY: 'auto',
                zIndex: 99999,
                padding: '18px',
                border: '1px solid var(--border-subtle)',
                background: 'var(--bg-surface)',
                backdropFilter: 'blur(20px)'
              }}
            >
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Bell size={18} style={{ color: 'var(--accent-cyan)' }} />
                  <strong style={{ fontSize: '0.95rem', color: 'var(--text-main)', fontWeight: 800 }}>Notifications</strong>
                  {unreadCount > 0 && (
                    <span className="badge badge-cyan" style={{ fontSize: '0.72rem', padding: '2px 8px' }}>
                      {unreadCount} Unread
                    </span>
                  )}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {unreadCount > 0 && (
                    <button onClick={handleMarkAllRead} className="btn btn-outline" style={{ fontSize: '0.72rem', padding: '3px 8px' }}>
                      <CheckCheck size={12} style={{ marginRight: '4px' }} /> Mark All Read
                    </button>
                  )}
                  <button
                    onClick={() => setShowNotifPanel(false)}
                    style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px' }}
                  >
                    <X size={18} />
                  </button>
                </div>
              </div>

              {/* Notification Content List */}
              {notifications.length === 0 ? (
                <div style={{ padding: '36px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                  <Bell size={32} style={{ marginBottom: '8px', opacity: 0.4, display: 'block', margin: '0 auto 8px auto' }} />
                  No in-app notifications yet.
                </div>
              ) : (
                <div>
                  {renderGroup('Today', today)}
                  {renderGroup('Earlier', earlier)}
                  {renderGroup('Read Notifications', read)}
                </div>
              )}
            </div>
          );
        })(),
        document.body
      )}
    </header>
  );
}
