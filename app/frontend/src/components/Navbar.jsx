import React from 'react';

export default function Navbar({ activePage, setActivePage, currentState }) {
  return (
    <nav style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-card)', padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }} onClick={() => setActivePage('home')}>
        <div style={{ width: '32px', height: '32px', background: 'linear-gradient(135deg, #38bdf8, #a855f7)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', color: '#fff' }}>
          TM
        </div>
        <span style={{ fontWeight: '700', fontSize: '1.1rem', letterSpacing: '-0.02em' }}>TeleMed AI Platform</span>
      </div>

      <div style={{ display: 'flex', gap: '16px' }}>
        <button className={activePage === 'home' ? 'btn-primary' : 'btn-secondary'} onClick={() => setActivePage('home')}>Home</button>
        <button className={activePage === 'intake' ? 'btn-primary' : 'btn-secondary'} onClick={() => setActivePage('intake')}>Intake & Review</button>
        {currentState === 'ANALYZED' || currentState === 'XAI_READY' || currentState === 'REPORT_READY' ? (
          <>
            <button className={activePage === 'dashboard' ? 'btn-primary' : 'btn-secondary'} onClick={() => setActivePage('dashboard')}>Risk Dashboard</button>
            <button className={activePage === 'xai' ? 'btn-primary' : 'btn-secondary'} onClick={() => setActivePage('xai')}>XAI Drivers</button>
            <button className={activePage === 'report' ? 'btn-primary' : 'btn-secondary'} onClick={() => setActivePage('report')}>Grounded Report & Q&A</button>
          </>
        ) : null}
      </div>
    </nav>
  );
}
