import React from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    if (import.meta.env?.DEV) {
      console.warn('[TeleMed ErrorBoundary caught an unhandled component error]:', error, errorInfo);
    }
    this.setState({ errorInfo });
  }

  handleReload = () => {
    window.location.reload();
  };

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '400px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '40px 20px',
        }}>
          <div className="glass-card" style={{
            maxWidth: '600px',
            width: '100%',
            padding: '32px',
            textAlign: 'center',
            borderLeft: '4px solid var(--accent-rose, #ef4444)'
          }}>
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              background: 'rgba(239, 68, 68, 0.15)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '16px',
              color: '#f87171'
            }}>
              <AlertTriangle size={30} />
            </div>

            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, margin: '0 0 8px 0', color: 'var(--text-main, #f8fafc)' }}>
              Something went wrong in this section
            </h2>
            <p style={{ color: 'var(--text-muted, #94a3b8)', fontSize: '0.9rem', marginBottom: '20px', lineHeight: 1.5 }}>
              An unexpected component error occurred. The application recovered safely without losing system state.
            </p>

            {this.state.error && (
              <div style={{
                background: 'var(--bg-primary, #090d16)',
                border: '1px solid var(--border-subtle, rgba(255,255,255,0.08))',
                borderRadius: '8px',
                padding: '12px 16px',
                marginBottom: '24px',
                textAlign: 'left',
                fontFamily: 'monospace',
                fontSize: '0.8rem',
                color: '#fca5a5',
                overflowX: 'auto'
              }}>
                <strong>{this.state.error.name}:</strong> {this.state.error.message}
              </div>
            )}

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
              <button
                className="btn btn-cyan"
                onClick={this.handleReset}
                style={{ fontSize: '0.88rem', padding: '10px 20px', display: 'inline-flex', alignItems: 'center', gap: '8px' }}
              >
                <RefreshCw size={16} /> Recover Workspace
              </button>
              <button
                className="btn btn-outline"
                onClick={this.handleReload}
                style={{ fontSize: '0.88rem', padding: '10px 20px', display: 'inline-flex', alignItems: 'center', gap: '8px' }}
              >
                <Home size={16} /> Reload Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
