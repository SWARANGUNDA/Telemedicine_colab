import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Search,
  Bell,
  Sun,
  Moon,
  User,
  LogOut,
  Settings,
  Shield,
  Menu,
  Activity
} from 'lucide-react';
import { Avatar } from '../ui/Avatar';
import NotificationDrawer from '../NotificationDrawer';
import { notificationStore } from '../../utils/notificationStore';

export function Topbar({ user, onLogout, onToggleTheme, theme = 'dark', onOpenMobileMenu, className = '' }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [, setTick] = useState(0);
  const userId = user?.user_id || 'default_user';
  const [unreadBadgeCount, setUnreadBadgeCount] = useState(() => notificationStore.getUnreadCount(userId));

  useEffect(() => {
    const handleProfileUpdate = () => setTick(t => t + 1);
    const handleNotifUpdate = () => {
      setUnreadBadgeCount(notificationStore.getUnreadCount(userId));
    };

    window.addEventListener('telemed_profile_updated', handleProfileUpdate);
    window.addEventListener('telemed_notifications_updated', handleNotifUpdate);
    return () => {
      window.removeEventListener('telemed_profile_updated', handleProfileUpdate);
      window.removeEventListener('telemed_notifications_updated', handleNotifUpdate);
    };
  }, [userId]);

  const getBreadcrumbs = () => {
    const path = location.pathname;
    if (path === '/') return ['Overview'];
    if (path === '/intake') return ['Intake', 'New Multimodal Analysis'];
    if (path === '/xai') return ['Analytics', 'XAI Driver Analysis'];
    if (path === '/report') return ['Reports', 'Comprehensive Diagnostic Report'];
    if (path === '/records') return ['Records', 'Health History'];
    if (path === '/consultations') return ['Clinical', 'Doctor Consultations'];
    if (path === '/appointments') return ['Schedule', 'Appointments'];
    if (path === '/care') return ['Care', 'Personalized Recommendations'];
    if (path === '/account' || path === '/profile') return ['Account & Profile', 'Patient Health Profile'];
    if (path.startsWith('/doctor/profile') || path === '/doctor/account') return ['Doctor Portal', 'Professional Profile Workspace'];
    if (path.startsWith('/doctor')) return ['Doctor Portal', path.replace('/doctor/', '').toUpperCase() || 'Dashboard'];
    if (path.startsWith('/admin/account')) return ['Admin System', 'Account & System Governance'];
    if (path.startsWith('/admin')) return ['Admin Overview', path.replace('/admin/', '').toUpperCase() || 'Dashboard'];
    return ['Portal', 'Dashboard'];
  };

  const breadcrumbs = getBreadcrumbs();

  const [isNotificationDrawerOpen, setIsNotificationDrawerOpen] = useState(false);
  const [drawerNotifications, setDrawerNotifications] = useState([]);

  return (
    <>
      <header className={`sticky top-0 z-[var(--z-header)] h-[72px] bg-[var(--glass-bg)] backdrop-blur-[var(--glass-blur)] border-b border-[var(--border-subtle)] px-4 md:px-8 flex items-center justify-between transition-all duration-200 ${className}`}>
        {/* Left: Mobile Menu Button & Breadcrumb */}
        <div className="flex items-center gap-4">
          <button
            onClick={onOpenMobileMenu}
            className="lg:hidden p-2 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--bg-surface-hover)]"
          >
            <Menu className="w-6 h-6" />
          </button>

          <div className="flex items-center gap-3">
            <div className="lg:hidden w-8 h-8 rounded-lg bg-gradient-to-tr from-[var(--primary)] to-[var(--accent)] flex items-center justify-center text-white font-bold">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <nav className="flex items-center gap-2 text-xs text-[var(--text-muted)] font-medium">
              {breadcrumbs.map((crumb, idx) => (
                <React.Fragment key={idx}>
                  {idx > 0 && <span className="text-[var(--text-dim)]">/</span>}
                  <span className={idx === breadcrumbs.length - 1 ? 'text-[var(--text-main)] font-semibold' : ''}>
                    {crumb}
                  </span>
                </React.Fragment>
              ))}
            </nav>
          </div>
        </div>



        {/* Right: Actions & User Profile */}
        <div className="flex items-center gap-3">
          {/* Instagram-Style Notification Bell */}
          <button
            onClick={() => navigate('/notifications')}
            className="p-2 rounded-xl text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--bg-surface-hover)] relative transition-all group"
            title="Open Notification Center"
          >
            <Bell className="w-5 h-5 transition-transform group-hover:scale-110" />
            {unreadBadgeCount > 0 && (
              <span className="absolute -top-1 -right-1 flex h-4 min-w-[16px] px-1 items-center justify-center rounded-full bg-gradient-to-r from-rose-500 to-red-600 text-[9.5px] font-black text-white shadow-md border-2 border-[var(--bg-surface)] animate-pulse">
                {unreadBadgeCount}
              </span>
            )}
          </button>

        {/* Theme Toggle */}
        <button
          onClick={onToggleTheme}
          className="p-2 rounded-xl text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--bg-surface-hover)] transition-colors"
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
        >
          {theme === 'dark' ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5 text-slate-600" />}
        </button>

        {/* User Profile Dropdown Menu */}
        <div className="relative">
          <button
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className="flex items-center gap-2.5 p-1.5 rounded-xl hover:bg-[var(--bg-surface-hover)] transition-colors"
          >
            <Avatar user={user} name={user?.full_name || user?.name || 'User Profile'} size="sm" />
            <div className="hidden sm:flex flex-col text-left">
              <span className="text-xs font-bold text-[var(--text-main)] leading-tight">
                {user?.full_name || user?.name || (user?.role === 'DOCTOR' ? 'Dr. Medical Officer' : user?.role === 'ADMIN' ? 'System Admin' : 'Patient Account')}
              </span>
              <span className="text-[10px] font-mono text-[var(--text-muted)]">{user?.role || 'PATIENT'}</span>
            </div>
          </button>

          {showProfileMenu && (
            <div className="absolute right-0 mt-2 w-64 p-3 border border-[var(--border-medium)] shadow-2xl rounded-2xl bg-[var(--bg-primary)] z-[9999] space-y-2 ring-1 ring-black/5">
              <div className="px-3 py-2 pb-2.5 border-b border-[var(--border-subtle)] space-y-0.5">
                <p className="text-xs font-extrabold text-[var(--text-main)] tracking-tight">
                  {user?.full_name || user?.name || (user?.role === 'DOCTOR' ? 'Dr. Medical Officer' : user?.role === 'ADMIN' ? 'System Administrator' : 'Patient Account')}
                </p>
                <p className="text-[11px] font-mono text-[var(--text-muted)] truncate">{user?.email || ''}</p>
                <div className="pt-1.5 flex items-center gap-1.5">
                  <span className="px-2 py-0.5 text-[9.5px] font-mono font-bold rounded-full bg-[var(--primary-light)] text-[var(--primary)] border border-[var(--primary)]/20 uppercase">
                    {user?.role || 'PATIENT'}
                  </span>
                  <span className="text-[10px] text-emerald-500 font-mono font-semibold flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> Active Session
                  </span>
                </div>
              </div>

              <div className="space-y-1">
                <button
                  onClick={() => {
                    setShowProfileMenu(false);
                    if (user?.role === 'DOCTOR') navigate('/doctor/profile');
                    else if (user?.role === 'ADMIN') navigate('/admin/account');
                    else navigate('/account');
                  }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-[var(--text-main)] hover:bg-[var(--primary-light)] hover:text-[var(--primary)] rounded-xl transition-all"
                >
                  <Settings className="w-4 h-4 text-[var(--primary)]" />
                  Account Settings & Profile
                </button>
                <button
                  onClick={() => { setShowProfileMenu(false); navigate('/privacy'); }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-[var(--text-main)] hover:bg-[var(--primary-light)] hover:text-[var(--primary)] rounded-xl transition-all"
                >
                  <Shield className="w-4 h-4 text-[var(--primary)]" />
                  Privacy & Data Security
                </button>
              </div>

              <div className="pt-1.5 border-t border-[var(--border-subtle)]">
                <button
                  onClick={() => { setShowProfileMenu(false); if (onLogout) onLogout(); }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-bold text-rose-600 dark:text-rose-400 hover:bg-rose-500/10 rounded-xl transition-all"
                >
                  <LogOut className="w-4 h-4 text-rose-500" />
                  Sign Out Account
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
      </header>

      <NotificationDrawer
        isOpen={isNotificationDrawerOpen}
        onClose={() => setIsNotificationDrawerOpen(false)}
        notifications={drawerNotifications}
        onMarkAsRead={(id) => setDrawerNotifications(prev => prev.map(n => n.id === id ? { ...n, isRead: true } : n))}
        onMarkAllRead={() => setDrawerNotifications(prev => prev.map(n => ({ ...n, isRead: true })))}
        onDelete={(id) => setDrawerNotifications(prev => prev.filter(n => n.id !== id))}
      />
    </>
  );
}
