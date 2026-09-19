import { useState, useEffect } from 'react';
import { getDecisionById } from '../api/client';

export default function DecisionDetail({ stepId, onBack }) {
  const [decision, setDecision] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchDecision() {
      try {
        const data = await getDecisionById(stepId);
        setDecision(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    }
    fetchDecision();
  }, [stepId]);

  if (isLoading) return <div className="card">Loading details...</div>;
  if (error) return <div className="card" style={{ color: 'var(--color-coral-red)' }}>Error: {error}</div>;
  if (!decision) return <div className="card">Decision not found.</div>;

  return (
    <div className="card">
      <div style={{ marginBottom: '24px' }}>
        <button className="button-ghost" onClick={onBack}>&larr; Back to Log</button>
      </div>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
        <div>
          <h3 style={{ marginBottom: '8px' }}>Decision Step <span className="monospaced">{decision.step_id}</span></h3>
          <p style={{ color: 'var(--color-ash)', fontSize: '14px' }}>Taken Action: <span className="monospaced" style={{ color: 'var(--color-mist)' }}>{decision.action_label}</span></p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <span className={`badge ${decision.safety_filter_verdict ? 'allow' : 'deny'}`}>
            Safety Filter: {decision.safety_filter_verdict ? 'PASS' : 'INTERVENTION'}
          </span>
          <span className={`badge ${decision.cedar_verdict ? 'allow' : 'deny'}`}>
            Cedar Policy: {decision.cedar_verdict ? 'ALLOW' : 'DENY'}
          </span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        <div className="card-subtle">
          <h4 style={{ color: 'var(--color-ash)', fontSize: '13px', marginBottom: '8px', fontWeight: 'var(--font-weight-regular)' }}>State (Input)</h4>
          <pre className="monospaced" style={{ fontSize: '12px', color: 'var(--color-mist)', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
            {JSON.stringify(decision.state, null, 2)}
          </pre>
        </div>
        <div className="card-subtle">
          <h4 style={{ color: 'var(--color-ash)', fontSize: '13px', marginBottom: '8px', fontWeight: 'var(--font-weight-regular)' }}>Reasoning</h4>
          <p>{decision.strategy_reason}</p>
          
          {decision.cedar_reason && (
            <div style={{ marginTop: '16px' }}>
              <h4 style={{ color: 'var(--color-ash)', fontSize: '13px', marginBottom: '4px', fontWeight: 'var(--font-weight-regular)' }}>Cedar Note</h4>
              <p style={{ fontSize: '13px', color: 'var(--color-coral-red)' }}>{decision.cedar_reason}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
