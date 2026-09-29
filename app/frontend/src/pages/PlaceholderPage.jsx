import React from 'react';
import { Lock, Info, Construction } from 'lucide-react';

export default function PlaceholderPage({ title, level, description, role }) {
  return (
    <div style={{ padding: '40px', maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
      <div className="card" style={{ padding: '48px 32px' }}>
        <div style={{
          display: 'inline-flex',
          padding: '16px',
          borderRadius: '50%',
          background: 'rgba(6, 182, 212, 0.12)',
          color: 'var(--accent-cyan)',
          marginBottom: '20px',
        }}>
          <Construction size={40} />
        </div>

        <span style={{
          display: 'inline-block',
          padding: '6px 14px',
          borderRadius: '20px',
          background: 'rgba(59, 130, 246, 0.15)',
          border: '1px solid rgba(59, 130, 246, 0.4)',
          color: '#60a5fa',
          fontWeight: 700,
          fontSize: '0.8rem',
          letterSpacing: '0.05em',
          marginBottom: '12px',
        }}>
          {level || 'FUTURE LEVEL'} FOUNDATION
        </span>

        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, margin: '0 0 12px' }}>{title}</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: '1.6', maxWidth: '520px', margin: '0 auto 28px' }}>
          {description || 'This module foundation is registered in navigation and RBAC routes. Full feature capabilities will be implemented in subsequent project levels.'}
        </p>

        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '10px 18px',
          background: 'rgba(255, 255, 255, 0.04)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '10px',
          color: '#94a3b8',
          fontSize: '0.85rem',
        }}>
          <Lock size={14} />
          <span>Role Authorization Scope: <strong>{role || 'System'}</strong></span>
        </div>
      </div>
    </div>
  );
}
