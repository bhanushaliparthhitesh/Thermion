import { useState } from 'react';
import { Link } from 'react-router-dom';
import RunTrigger from '../components/RunTrigger';
import DecisionsTable from '../components/DecisionsTable';
import DecisionDetail from '../components/DecisionDetail';
import AgentChat from '../components/AgentChat';

export default function Dashboard() {
  const [selectedStepId, setSelectedStepId] = useState(null);

  return (
    <div>
      <div className="container" style={{ paddingTop: '32px', paddingBottom: '16px' }}>
        <Link to="/" style={{ color: 'var(--color-ash)', fontSize: '13px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
          &larr; Back to Home
        </Link>
      </div>

      <div className="container" style={{ paddingBottom: '32px' }}>
        <RunTrigger />
      </div>

      <div className="container section-gap" style={{ marginTop: '0' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
          <div>
            {selectedStepId !== null ? (
              <DecisionDetail stepId={selectedStepId} onBack={() => setSelectedStepId(null)} />
            ) : (
              <DecisionsTable onSelectDecision={(id) => setSelectedStepId(id)} />
            )}
          </div>
          <div>
            <AgentChat />
          </div>
        </div>
      </div>
    </div>
  );
}
