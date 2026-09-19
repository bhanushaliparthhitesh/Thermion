import { useState, useEffect } from 'react';
import { getDecisions } from '../api/client';

export default function DecisionsTable({ onSelectDecision }) {
  const [decisions, setDecisions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchDecisions() {
      try {
        // Wrap response if it isn't an array in case the API returns an object
        const data = await getDecisions();
        setDecisions(Array.isArray(data) ? data : data.decisions || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    }
    fetchDecisions();
  }, []);

  if (isLoading) return <div className="card">Loading decisions...</div>;
  if (error) return <div className="card" style={{ color: 'var(--color-coral-red)' }}>Error: {error}</div>;

  return (
    <div className="card">
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3>Decisions Log</h3>
        <button className="button-ghost" onClick={() => window.location.reload()}>Refresh</button>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table className="table-container">
          <thead>
            <tr>
              <th>Step ID</th>
              <th>Action</th>
              <th>Safety Verdict</th>
              <th>Cedar Check</th>
              <th>Reasoning</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {decisions.length === 0 ? (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', color: 'var(--color-ash)', padding: '24px' }}>
                  No decisions logged yet.
                </td>
              </tr>
            ) : (
              decisions.map((d) => (
                <tr key={d.step_id}>
                  <td className="monospaced" style={{ color: 'var(--color-mist)' }}>{d.step_id}</td>
                  <td className="monospaced" style={{ color: 'var(--color-mist)' }}>{d.action_label}</td>
                  <td>
                    <span className={`badge ${d.safety_filter_verdict ? 'allow' : 'deny'}`}>
                      {d.safety_filter_verdict ? 'PASS' : 'INTERVENTION'}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${d.cedar_verdict ? 'allow' : 'deny'}`}>
                      {d.cedar_verdict ? 'ALLOW' : 'DENY'}
                    </span>
                  </td>
                  <td style={{ color: 'var(--color-ash)', fontSize: '13px', maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {d.strategy_reason}
                  </td>
                  <td>
                    <button className="nav-button-text" onClick={() => onSelectDecision(d.step_id)}>Details &rarr;</button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
