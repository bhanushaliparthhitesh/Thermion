import { useState } from 'react';
import { runPipeline } from '../api/client';

export default function RunTrigger() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleRun = async () => {
    setIsLoading(true);
    setResult(null);
    try {
      const data = await runPipeline();
      setResult('Pipeline executed successfully.');
    } catch (error) {
      setResult('Error executing pipeline.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div>
        <h2>Run Pipeline</h2>
        <p style={{ color: 'var(--color-ash)', marginTop: '4px' }}>Execute the Thermion safety layer and log decisions.</p>
      </div>
      <div>
        <button 
          className="button-primary" 
          onClick={handleRun} 
          disabled={isLoading}
        >
          {isLoading ? 'Running...' : 'Execute Run'}
        </button>
        {result && <div style={{ marginTop: '8px', fontSize: '13px', color: 'var(--color-ash)' }}>{result}</div>}
      </div>
    </div>
  );
}
