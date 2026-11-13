import React from 'react';
import { MOCK_MODULE_STATUSES } from '../../mock/mockData';

export default function ModuleStatus() {
  return (
    <div className="card" style={{ height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)' }}>
            Module Integration Status
          </h3>
          <span className="badge badge-demo">Demo Mode UI</span>
        </div>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          Awaiting FastAPI verification
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {MOCK_MODULE_STATUSES.map((module) => {
          const isDisconnected = module.statusType === 'disconnected';
          return (
            <div
              key={module.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 14px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span className={`indicator-dot ${isDisconnected ? 'disconnected' : 'demo'}`} />
                <div>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>
                    {module.name}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    {module.subtext}
                  </div>
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <span
                  className={`badge ${isDisconnected ? 'badge-disconnected' : 'badge-demo'}`}
                  style={{ fontSize: '10px' }}
                >
                  {module.status}
                </span>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px', maxWidth: '190px' }}>
                  {module.details}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
