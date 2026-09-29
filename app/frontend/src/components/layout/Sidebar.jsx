import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  FilePlus,
  BarChart3,
  FileText,
  History,
  Stethoscope,
  HeartPulse,
  ShieldCheck,
  Users,
  Cpu,
  FileCheck2,
  Lock,
  ChevronLeft,
  ChevronRight,
  Activity,
  UserCheck,
  Calendar,
  Sparkles
} from 'lucide-react';
import { Avatar } from '../ui/Avatar';

export function Sidebar({ isCollapsed, onToggleCollapse, userRole = 'PATIENT', className = '' }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [, setTick] = useState(0);

  useEffect(() => {
    const handleUpdate = () => setTick(t => t + 1);
    window.addEventListener('telemed_profile_updated', handleUpdate);
    return () => window.removeEventListener('telemed_profile_updated', handleUpdate);
  }, []);

  const patientMenu = [
    {
      group: "Clinical Insights",
      items: [
        { id: "pat-overview", label: "Overview", icon: LayoutDashboard, path: "/dashboard" },
        { id: "pat-intake", label: "New Analysis", icon: FilePlus, path: "/intake" },
        { id: "pat-xai", label: "XAI Driver Analysis", icon: BarChart3, path: "/xai" },
        { id: "pat-report", label: "Comprehensive Report", icon: FileText, path: "/report" },
      ]
    },
    {
      group: "Records & Care",
      items: [
        { id: "pat-profile", label: "Profile Workspace", icon: UserCheck, path: "/profile" },
        { id: "pat-compare", label: "Compare & Analytics", icon: BarChart3, path: "/compare" },
        { id: "pat-messages", label: "Secure Messages", icon: Activity, path: "/messages" },
        { id: "pat-notifications", label: "Notifications", icon: Lock, path: "/notifications" },
        { id: "pat-records", label: "Health Records", icon: History, path: "/records" },
        { id: "pat-consultations", label: "Consultations", icon: Stethoscope, path: "/consultations" },
        { id: "pat-appointments", label: "Appointments", icon: Calendar, path: "/appointments" },
        { id: "pat-care", label: "Care Recommendations", icon: HeartPulse, path: "/care" },
      ]
    }
  ];

  const doctorMenu = [
    {
      group: "Doctor Portal",
      items: [
        { id: "doc-dashboard", label: "Dashboard", icon: LayoutDashboard, path: "/doctor/dashboard" },
        { id: "doc-consultations", label: "Consultations", icon: Stethoscope, path: "/doctor/consultations" },
        { id: "doc-appointments", label: "Appointments", icon: Calendar, path: "/doctor/appointments" },
        { id: "doc-verification", label: "Credentials Upload", icon: UserCheck, path: "/doctor/verification" },
      ]
    }
  ];

  const adminMenu = [
    {
      group: "System Administration",
      items: [
        { id: "admin-overview", label: "System Overview", icon: LayoutDashboard, path: "/admin" },
        { id: "admin-doctors", label: "Doctor Verification", icon: ShieldCheck, path: "/admin/doctors" },
        { id: "admin-users", label: "User Management", icon: Users, path: "/admin/users" },
        { id: "admin-consultations", label: "Consultations Mgmt", icon: Stethoscope, path: "/admin/consultations" },
        { id: "admin-audit", label: "Audit & Compliance", icon: FileCheck2, path: "/admin/audit" },
        { id: "admin-system", label: "System Metrics", icon: Cpu, path: "/admin/system" },
      ]
    }
  ];

  const menuConfig = userRole === 'ADMIN' ? adminMenu : (userRole === 'DOCTOR' ? doctorMenu : patientMenu);

  return (
    <aside
      className={`fixed top-0 left-0 bottom-0 z-[var(--z-sticky)] bg-[var(--bg-sidebar)] border-r border-[var(--border-subtle)] transition-all duration-300 ease-in-out flex flex-col justify-between hidden lg:flex ${
        isCollapsed ? 'w-[80px]' : 'w-[280px]'
      } ${className}`}
    >
      {/* Brand Header */}
      <div>
        <div className="h-[72px] px-5 flex items-center justify-between border-b border-[var(--border-subtle)]">
          <div className="flex items-center gap-3 overflow-hidden cursor-pointer" onClick={() => navigate('/')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[var(--primary)] to-[var(--accent)] flex items-center justify-center text-white font-bold shadow-sm shrink-0">
              <Activity className="w-6 h-6 text-white" />
            </div>
            {!isCollapsed && (
              <div className="flex flex-col">
                <span className="font-bold text-base tracking-tight text-[var(--text-main)] leading-none">TeleMed AI</span>
                <span className="text-[10px] font-mono text-[var(--primary)] uppercase font-semibold mt-1">v4.0 Unified</span>
              </div>
            )}
          </div>

          <button
            onClick={onToggleCollapse}
            className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--bg-surface-hover)] transition-colors"
            title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            {isCollapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-6 overflow-y-auto max-h-[calc(100vh-140px)] no-scrollbar">
          {menuConfig.map((group, idx) => (
            <div key={idx} className="space-y-1">
              {!isCollapsed && (
                <div className="px-3 py-1 text-[10px] font-mono font-semibold tracking-wider text-[var(--text-dim)] uppercase">
                  {group.group}
                </div>
              )}

              {group.items.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;

                return (
                  <button
                    key={item.id || `${item.path}-${item.label}`}
                    onClick={() => navigate(item.path)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group relative ${
                      isActive
                        ? 'bg-[var(--primary-light)] text-[var(--primary)] font-semibold shadow-sm'
                        : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--bg-surface-hover)]'
                    }`}
                    title={isCollapsed ? item.label : undefined}
                  >
                    <Icon className={`w-5 h-5 shrink-0 transition-transform group-hover:scale-110 ${isActive ? 'text-[var(--primary)]' : 'text-[var(--text-muted)]'}`} />
                    {!isCollapsed && <span className="truncate">{item.label}</span>}
                    {isActive && (
                      <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-[var(--primary)] rounded-l-full" />
                    )}
                  </button>
                );
              })}
            </div>
          ))}
        </nav>
      </div>

      {/* Footer User Role Badge */}
      <div className="p-3 border-t border-[var(--border-subtle)]">
        <div className={`flex items-center gap-3 p-2 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] ${isCollapsed ? 'justify-center' : ''}`}>
          <Avatar user={{ role: userRole }} size="sm" className="rounded-lg" />
          {!isCollapsed && (
            <div className="flex flex-col overflow-hidden">
              <span className="text-xs font-bold text-[var(--text-main)] truncate">{userRole} Portal</span>
              <span className="text-[10px] font-mono text-[var(--success)] flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)] animate-pulse" />
                Active Session
              </span>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
