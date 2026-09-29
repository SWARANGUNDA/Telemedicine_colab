// Global Notification Store with strict per-user isolation and persistent read state

function getActiveUser() {
  try {
    const saved = localStorage.getItem('telemed_user');
    if (saved) {
      const u = JSON.parse(saved);
      return u;
    }
  } catch (e) {}
  return null;
}

function getActiveUserId() {
  const u = getActiveUser();
  if (u?.user_id) return u.user_id;
  if (u?.id) return u.id;
  return 'default_user';
}

function getInitialNotificationsForUser(userId, role) {
  const userRole = (role || getActiveUser()?.role || 'PATIENT').toUpperCase();
  
  if (userRole === 'DOCTOR') {
    return [
      {
        id: `NOT-WELCOME-DOC-${userId || 'NEW'}`,
        category: 'Welcome',
        title: 'Welcome to TeleMed AI Physician Portal',
        description: 'Your verified doctor workspace is active. Review assigned patient consultations, intake assessments, and clinical guidelines.',
        details: 'Connected to TeleMed Precision AI v4.0. Physician verification active.',
        timestamp: 'Just now',
        priority: 'HIGH',
        isRead: false,
        actionRoute: '/doctor/dashboard',
        actionLabel: 'Open Doctor Dashboard'
      }
    ];
  }

  if (userRole === 'ADMIN') {
    return [
      {
        id: `NOT-WELCOME-ADM-${userId || 'NEW'}`,
        category: 'Welcome',
        title: 'Welcome to TeleMed AI Admin Console',
        description: 'System administration portal initialized. Monitor doctor verifications, patient consultation queues, and compliance audit logs.',
        details: 'Connected to TeleMed Precision AI v4.0. Admin Level 5 Privilege.',
        timestamp: 'Just now',
        priority: 'HIGH',
        isRead: false,
        actionRoute: '/admin/dashboard',
        actionLabel: 'Open Admin Overview'
      }
    ];
  }

  return [
    {
      id: `NOT-WELCOME-${userId || 'NEW'}`,
      category: 'Welcome',
      title: 'Welcome to TeleMed AI Patient Portal',
      description: 'Your patient workspace is initialized. Complete your first intake assessment to calculate personalized risk vectors and clinical guidelines.',
      details: 'Connected to TeleMed Precision AI v4.0. Multimodal clinical, wearable, and microbiome signals ready for intake.',
      timestamp: 'Just now',
      priority: 'HIGH',
      isRead: false,
      actionRoute: '/intake',
      actionLabel: 'Start Intake Assessment'
    }
  ];
}

export const notificationStore = {
  getNotifications(targetUserId) {
    const uid = targetUserId || getActiveUserId();
    if (uid === 'default_user') return [];
    
    const key = `telemed_notifications_${uid}`;
    const userRole = (getActiveUser()?.role || 'PATIENT').toUpperCase();

    try {
      const stored = localStorage.getItem(key);
      if (stored !== null) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) {
          // Dynamically sanitize legacy cached notifications for Doctors and Admins
          const sanitized = parsed.map(n => {
            if (n.id && n.id.startsWith('NOT-WELCOME-')) {
              if (userRole === 'DOCTOR' && (n.actionRoute === '/intake' || n.title.includes('Patient'))) {
                return { ...getInitialNotificationsForUser(uid, 'DOCTOR')[0], isRead: n.isRead };
              }
              if (userRole === 'ADMIN' && (n.actionRoute === '/intake' || n.title.includes('Patient'))) {
                return { ...getInitialNotificationsForUser(uid, 'ADMIN')[0], isRead: n.isRead };
              }
            }
            return n;
          });

          // Save sanitized back to localStorage
          localStorage.setItem(key, JSON.stringify(sanitized));
          return sanitized;
        }
      }
    } catch (e) {}
    
    // Check if user has already been initialized previously
    const welcomedKey = `telemed_welcomed_${uid}`;
    try {
      if (localStorage.getItem(welcomedKey)) {
        localStorage.setItem(key, JSON.stringify([]));
        return [];
      }
    } catch (e) {}

    const initial = getInitialNotificationsForUser(uid, userRole);
    try {
      localStorage.setItem(key, JSON.stringify(initial));
      localStorage.setItem(welcomedKey, 'true');
    } catch (e) {}
    return initial;
  },

  getUnreadCount(targetUserId) {
    const list = this.getNotifications(targetUserId);
    return list.filter(n => !n.isRead).length;
  },

  markAsRead(id, targetUserId) {
    const uid = targetUserId || getActiveUserId();
    const key = `telemed_notifications_${uid}`;
    const list = this.getNotifications(uid);
    const updated = list.map(n => n.id === id ? { ...n, isRead: true } : n);
    try {
      localStorage.setItem(key, JSON.stringify(updated));
    } catch (e) {}
    window.dispatchEvent(new CustomEvent('telemed_notifications_updated'));
    return updated;
  },

  markAllAsRead(targetUserId) {
    const uid = targetUserId || getActiveUserId();
    const key = `telemed_notifications_${uid}`;
    const list = this.getNotifications(uid);
    const updated = list.map(n => ({ ...n, isRead: true }));
    try {
      localStorage.setItem(key, JSON.stringify(updated));
    } catch (e) {}
    window.dispatchEvent(new CustomEvent('telemed_notifications_updated'));
    return updated;
  },

  deleteNotification(id, targetUserId) {
    const uid = targetUserId || getActiveUserId();
    const key = `telemed_notifications_${uid}`;
    const list = this.getNotifications(uid);
    const updated = list.filter(n => n.id !== id);
    try {
      localStorage.setItem(key, JSON.stringify(updated));
    } catch (e) {}
    window.dispatchEvent(new CustomEvent('telemed_notifications_updated'));
    return updated;
  }
};
