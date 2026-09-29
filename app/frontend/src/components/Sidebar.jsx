import React from 'react';
import {
  LayoutDashboard, PlusCircle, ShieldCheck, Brain, FileText,
  FolderClock, HeartHandshake, UserCheck, PanelLeftClose, PanelLeft,
  Users, Stethoscope, Shield, Clock, Lock, FileSpreadsheet, Settings, History, Calendar
} from 'lucide-react';

export default function Sidebar({
  activeNav,
  activeSubNav,
  onNavigate,
  isCollapsed,
  onToggleCollapse,
  isPredictionComplete,
  user
}) {
  const role = user?.role || 'PATIENT';

  // Role-specific navigation items
  let primaryItems = [];
  let secondaryItems = [];

  if (role === 'PATIENT') {
    primaryItems = [
      { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, nav: 'dashboard', subNav: '' },
      { key: 'new_analysis', label: 'Health Analysis', icon: PlusCircle, nav: 'analysis', subNav: 'new_analysis' },
      { key: 'risk_dashboard', label: 'Risk Assessment', icon: ShieldCheck, nav: 'results', subNav: 'risk_dashboard', locked: !isPredictionComplete },
      { key: 'xai', label: 'XAI Explainability', icon: Brain, nav: 'results', subNav: 'xai', locked: !isPredictionComplete },
      { key: 'report', label: 'AI Clinical Report', icon: FileText, nav: 'results', subNav: 'report', locked: !isPredictionComplete }
    ];

    secondaryItems = [
      { key: 'records', label: 'Health Records', icon: FolderClock, nav: 'records', subNav: 'reports_history' },
      { key: 'consultations', label: 'Consult a Doctor', icon: HeartHandshake, nav: 'consultations', subNav: '' },
      { key: 'appointments', label: 'Appointments', icon: Calendar, nav: 'appointments', subNav: '' },
      { key: 'patient_privacy', label: 'Data & Privacy', icon: Lock, nav: 'patient_privacy', subNav: '' },
      { key: 'account', label: 'Patient Profile', icon: UserCheck, nav: 'account', subNav: 'settings' }
    ];
  } else if (role === 'DOCTOR') {
    const docStatus = user?.doctor_profile?.verification_status || 'PENDING';
    primaryItems = [
      { key: 'dashboard', label: 'Doctor Dashboard', icon: LayoutDashboard, nav: 'dashboard', subNav: '' },
      { key: 'verification', label: 'Verification Status', icon: Clock, nav: 'verification', subNav: '', badge: docStatus },
      { key: 'assigned_patients', label: 'Assigned Consultations', icon: Users, nav: 'assigned_patients', subNav: '', locked: docStatus !== 'VERIFIED' },
    ];

    secondaryItems = [
      { key: 'appointments', label: 'Appointments', icon: Calendar, nav: 'appointments', subNav: '', locked: docStatus !== 'VERIFIED' },
      { key: 'account', label: 'Doctor Profile', icon: Stethoscope, nav: 'account', subNav: 'profile' }
    ];
  } else if (role === 'ADMIN') {
    primaryItems = [
      { key: 'admin_dashboard', label: 'Admin Overview', icon: LayoutDashboard, nav: 'admin_dashboard', subNav: '' },
      { key: 'admin_verification', label: 'Doctor Verification', icon: Stethoscope, nav: 'admin_verification', subNav: '' },
      { key: 'admin_assignments', label: 'Consultation Queue', icon: Users, nav: 'admin_assignments', subNav: '' },
      { key: 'admin_users', label: 'User Directory', icon: Users, nav: 'admin_users', subNav: '' },
    ];

    secondaryItems = [
      { key: 'appointments', label: 'Appointments Schedule', icon: Calendar, nav: 'appointments', subNav: '' },
      { key: 'admin_system', label: 'System Operations', icon: Settings, nav: 'admin_system', subNav: '' },
      { key: 'admin_audit', label: 'Audit & Governance', icon: History, nav: 'admin_audit', subNav: '' },
    ];
  }

  const isCurrentActive = (item) => {
    if (activeNav === item.nav) {
      if (!item.subNav || activeSubNav === item.subNav) return true;
    }
    return false;
  };

  return (
    <aside style={{
      width: isCollapsed ? '72px' : '260px',
      background: 'var(--bg-sidebar)',
      borderRight: '1px solid var(--border-subtle)',
      display: 'flex',
      flexDirection: 'column',
      transition: 'width 0.25s ease',
      zIndex: 50,
      flexShrink: 0,
      minHeight: '100vh'
    }}>
      {/* Brand Header */}
      <div style={{
        padding: isCollapsed ? '20px 12px' : '20px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: isCollapsed ? 'center' : 'space-between',
        borderBottom: '1px solid var(--border-subtle)'
      }}>
        {!isCollapsed && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '34px',
              height: '34px',
              borderRadius: '9px',
              background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-blue))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              fontWeight: 800,
              fontSize: '1rem'
            }}>
              T
            </div>
            <div>
              <div style={{ fontWeight: 800, fontSize: '1.05rem', color: 'var(--text-main)', letterSpacing: '-0.02em', lineHeight: 1.2 }}>
                TeleMed <span style={{ color: 'var(--accent-cyan)' }}>AI</span>
              </div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase' }}>
                {role} SHELL
              </div>
            </div>
          </div>
        )}

        <button
          onClick={onToggleCollapse}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            padding: '6px',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
          title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          {isCollapsed ? <PanelLeft size={20} /> : <PanelLeftClose size={20} />}
        </button>
      </div>

      {/* Navigation List */}
      <div style={{ flex: 1, padding: '16px 12px', overflowY: 'auto' }}>
        {!isCollapsed && (
          <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px', paddingLeft: '8px' }}>
            {role} Portal
          </div>
        )}

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {primaryItems.map((item) => {
            const Icon = item.icon;
            const active = isCurrentActive(item);

            return (
              <button
                key={item.key}
                disabled={item.locked}
                onClick={() => onNavigate(item.nav, item.subNav)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: isCollapsed ? '12px' : '10px 12px',
                  justifyContent: isCollapsed ? 'center' : 'flex-start',
                  borderRadius: '8px',
                  border: 'none',
                  background: active ? 'rgba(6, 182, 212, 0.15)' : 'transparent',
                  color: active ? 'var(--accent-cyan)' : item.locked ? 'var(--text-dim)' : 'var(--text-muted)',
                  cursor: item.locked ? 'not-allowed' : 'pointer',
                  fontWeight: active ? 600 : 400,
                  fontSize: '0.875rem',
                  transition: 'all 0.15s ease',
                  position: 'relative'
                }}
                title={item.locked ? "Complete prerequisites or admin verification first" : item.label}
              >
                <Icon size={18} style={{ flexShrink: 0 }} />
                {!isCollapsed && <span style={{ flex: 1, textAlign: 'left' }}>{item.label}</span>}
                {!isCollapsed && item.badge && (
                  <span style={{ fontSize: '0.65rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(245, 158, 11, 0.2)', color: '#fbbf24', fontWeight: 700 }}>
                    {item.badge}
                  </span>
                )}
                {!isCollapsed && item.locked && (
                  <span style={{ fontSize: '0.65rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(255,255,255,0.06)', color: 'var(--text-dim)' }}>
                    LOCKED
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {!isCollapsed && (
          <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em', margin: '20px 0 8px', paddingLeft: '8px' }}>
            Modules & System
          </div>
        )}

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {secondaryItems.map((item) => {
            const Icon = item.icon;
            const active = isCurrentActive(item);

            return (
              <button
                key={item.key}
                onClick={() => onNavigate(item.nav, item.subNav)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: isCollapsed ? '12px' : '10px 12px',
                  justifyContent: isCollapsed ? 'center' : 'flex-start',
                  borderRadius: '8px',
                  border: 'none',
                  background: active ? 'rgba(6, 182, 212, 0.15)' : 'transparent',
                  color: active ? 'var(--accent-cyan)' : 'var(--text-muted)',
                  cursor: 'pointer',
                  fontWeight: active ? 600 : 400,
                  fontSize: '0.875rem',
                }}
              >
                <Icon size={18} style={{ flexShrink: 0 }} />
                {!isCollapsed && <span>{item.label}</span>}
              </button>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
