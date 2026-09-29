import React from 'react';
import { Drawer, Badge, Button } from './ui';
import { Bell, CheckCircle2, Trash2, Calendar, Sparkles, FileText, MessageSquare, ShieldAlert, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function NotificationDrawer({
  isOpen,
  onClose,
  notifications = [],
  onMarkAsRead,
  onMarkAllRead,
  onDelete,
}) {
  const navigate = useNavigate();

  const getCategoryIcon = (cat) => {
    switch (cat) {
      case 'Appointments': return Calendar;
      case 'AI Analysis': return Sparkles;
      case 'Reports': return FileText;
      case 'Messages': return MessageSquare;
      default: return ShieldAlert;
    }
  };

  const unreadCount = notifications.filter(n => !n.isRead).length;

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title={`Notification Center (${unreadCount} Unread)`}
      position="right"
    >
      <div className="space-y-4 py-2">
        {/* Header Actions */}
        <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
          <span className="text-xs font-mono text-[var(--text-muted)] uppercase">Recent Alerts</span>
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={onMarkAllRead} className="!py-0.5 text-[11px]">
              Mark All Read
            </Button>
          </div>
        </div>

        {/* Notifications List */}
        {notifications.length === 0 ? (
          <div className="text-center py-12 space-y-3">
            <Bell className="w-10 h-10 mx-auto text-[var(--text-muted)]" />
            <p className="text-sm font-semibold text-[var(--text-main)]">No Notifications</p>
            <p className="text-xs text-[var(--text-muted)]">Your inbox is clear.</p>
          </div>
        ) : (
          <div className="space-y-3 max-h-[calc(100vh-220px)] overflow-y-auto pr-1">
            {notifications.map((n) => {
              const Icon = getCategoryIcon(n.category);
              return (
                <div
                  key={n.id}
                  className={`p-3.5 rounded-xl border transition-all space-y-2 ${
                    !n.isRead
                      ? 'bg-[var(--primary-light)]/30 border-[var(--primary)] shadow-sm'
                      : 'bg-[var(--bg-primary)] border-[var(--border-subtle)] opacity-80'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 rounded-lg bg-[var(--primary-light)] text-[var(--primary)]">
                        <Icon className="w-4 h-4" />
                      </div>
                      <h4 className="text-xs font-bold text-[var(--text-main)]">{n.title}</h4>
                    </div>
                    <Badge variant={n.priority === 'HIGH' ? 'danger' : 'secondary'} size="sm">
                      {n.priority}
                    </Badge>
                  </div>

                  <p className="text-xs text-[var(--text-muted)] leading-relaxed">{n.description}</p>

                  <div className="flex items-center justify-between pt-1 border-t border-[var(--border-subtle)] text-[10px]">
                    <span className="font-mono text-[var(--text-muted)]">{n.timestamp}</span>
                    <div className="flex items-center gap-1">
                      {!n.isRead && (
                        <button
                          onClick={() => onMarkAsRead(n.id)}
                          className="text-[var(--primary)] hover:underline font-semibold"
                        >
                          Mark Read
                        </button>
                      )}
                      <button
                        onClick={() => onDelete(n.id)}
                        className="text-[var(--text-muted)] hover:text-[var(--danger)] p-1"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Footer View All Link */}
        <div className="pt-3 border-t border-[var(--border-subtle)]">
          <Button
            variant="outline"
            size="md"
            className="w-full justify-center text-xs"
            rightIcon={<ArrowRight className="w-4 h-4" />}
            onClick={() => {
              onClose();
              navigate('/notifications');
            }}
          >
            View Notification Center Page
          </Button>
        </div>
      </div>
    </Drawer>
  );
}
