import { Link } from 'react-router-dom';

const MOCK_CHAT = [
  { role: 'user', content: 'Why was air cooling used at step 42 instead of liquid?' },
  { role: 'agent', content: 'At step 42, the RL agent initially proposed LIQUID cooling due to a temperature deviation of 2.1°C. However, the SafetyFilter blocked this action because the projected water_usage (4.8L) exceeded the hard limit (4.5L). The system safely fell back to AIR cooling, which passed both the SafetyFilter and the Cedar authorization policy.' },
];

export default function HomePage() {
  return (
    <div>
      {/* Hero */}
      <div className="hero-floor">
        <div className="container">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '48px', textAlign: 'left' }}>
            <div style={{ maxWidth: '600px' }}>
              <h1 style={{ marginBottom: '16px' }}>Transparent AI<br/>cooling control.</h1>
              <p style={{ color: 'var(--color-ash)', fontSize: '20px', lineHeight: '1.33', letterSpacing: 'var(--tracking-body-lg)', fontWeight: 590 }}>
                Every decision checked, logged, and explained by the midnight cooling instrument.
              </p>
            </div>
            <div style={{ marginTop: '16px' }}>
              <Link to="/dashboard" style={{ color: 'var(--color-mist)', fontWeight: '510', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Open Dashboard &rarr;
              </Link>
            </div>
          </div>

          {/* Mock RunTrigger — static, no fetch */}
          <div style={{ padding: '24px', backgroundColor: 'var(--color-carbon)', borderRadius: '12px', boxShadow: 'var(--shadow-subtle)', textAlign: 'left' }}>
            <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2>Run Pipeline</h2>
                <p style={{ color: 'var(--color-ash)', marginTop: '4px' }}>Execute the Thermion safety layer and log decisions.</p>
              </div>
              <div>
                <Link to="/dashboard" className="button-primary" style={{ textDecoration: 'none' }}>
                  Open Dashboard
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Built-on strip — real technologies from the project */}
      <div className="container" style={{ paddingTop: '48px', paddingBottom: '48px', borderBottom: '1px solid var(--color-graphite)' }}>
        <p style={{ color: 'var(--color-ash)', fontSize: '12px', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '16px', fontWeight: 'var(--font-weight-regular)' }}>Built on</p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '32px', alignItems: 'center' }}>
          {['Stable-Baselines3', 'XGBoost', 'Gymnasium', 'Cedar', 'OpenSearch', 'Strands Agents', 'Ollama', 'AWS SAM', 'Docker'].map((name) => (
            <span key={name} style={{ color: 'var(--color-fog)', fontSize: '14px', fontWeight: 'var(--font-weight-regular)', whiteSpace: 'nowrap' }}>{name}</span>
          ))}
        </div>
      </div>

      {/* Three pillars — pulled from the actual feature set */}
      <div className="container" style={{ paddingTop: '64px', paddingBottom: '64px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '48px' }}>
          <div>
            <h3 style={{ fontSize: 'var(--text-subheading)', letterSpacing: '-0.012em', fontWeight: 400, marginBottom: '12px' }}>Safety-checked</h3>
            <p style={{ color: 'var(--color-ash)', fontSize: '15px', lineHeight: '1.6' }}>
              Every RL action passes through a stateless SafetyFilter before execution. Out-of-bound temperatures, water usage, and outlet temps are caught and replaced with safe fallbacks — no unsafe action ever reaches the digital twin.
            </p>
          </div>
          <div>
            <h3 style={{ fontSize: 'var(--text-subheading)', letterSpacing: '-0.012em', fontWeight: 400, marginBottom: '12px' }}>Policy-authorized</h3>
            <p style={{ color: 'var(--color-ash)', fontSize: '15px', lineHeight: '1.6' }}>
              Cedar policies encode safety bounds as declarative rules evaluated independently of application code. Actions that pass the safety filter still face a second gate — a formal authorization check that can be audited, versioned, and reviewed by non-engineers.
            </p>
          </div>
          <div>
            <h3 style={{ fontSize: 'var(--text-subheading)', letterSpacing: '-0.012em', fontWeight: 400, marginBottom: '12px' }}>Agent-explained</h3>
            <p style={{ color: 'var(--color-ash)', fontSize: '15px', lineHeight: '1.6' }}>
              A Strands-powered ops copilot retrieves logged decisions from OpenSearch and explains why each action was taken, blocked, or overridden — in plain English, with citations to the step, safety verdict, and Cedar outcome.
            </p>
          </div>
        </div>
      </div>

      {/* Feature 1 — Safety Check: text-left, visual-right */}
      <div className="container">
        <div className="feature-row">
          <div className="feature-text">
            <p style={{ color: 'var(--color-acid-lime)', fontSize: '12px', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '12px' }}>Safety layer</p>
            <h2 style={{ marginBottom: '16px' }}>Every action<br/>safety-checked.</h2>
            <p style={{ color: 'var(--color-ash)', lineHeight: '1.5' }}>
              The SafetyFilter evaluates temperature deviation, water usage, outlet temperature, and cooling efficiency against hard physical limits before any action reaches the Digital Twin. When a violation is detected, the proposed action is replaced with the safest available alternative — never silently dropped.
            </p>
            <div style={{ display: 'flex', gap: '8px', marginTop: '24px', flexWrap: 'wrap' }}>
              <span className="badge allow">PASS</span>
              <span className="badge deny">INTERVENTION</span>
              <span className="badge" style={{ color: 'var(--color-fog)' }}>Temp &lt; 6.0°C</span>
              <span className="badge" style={{ color: 'var(--color-fog)' }}>Outlet &lt; 80°C</span>
            </div>
          </div>
          <div className="feature-visual">
            <div className="card" style={{ overflow: 'hidden' }}>
              <div style={{ marginBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', color: 'var(--color-ash)' }}>Safety Filter Execution</span>
                <span style={{ fontSize: '12px', color: 'var(--color-ash)', fontFamily: 'var(--font-berkeley-mono)' }}>DEMO</span>
              </div>
              <div style={{ padding: '16px', backgroundColor: 'var(--color-obsidian)', borderRadius: 'var(--radius-inputs)', fontFamily: 'var(--font-berkeley-mono)', fontSize: '13px', color: 'var(--color-mist)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div><span style={{ color: 'var(--color-ash)' }}>[step: 42]</span> <span style={{ color: 'var(--color-fog)' }}>Proposed action:</span> <span style={{ color: 'var(--color-mist)' }}>LIQUID</span></div>
                <div style={{ color: 'var(--color-coral-red)', paddingLeft: '8px', borderLeft: '2px solid var(--color-coral-red)' }}>&#10007; INTERVENTION: water_usage (4.8L) exceeds maximum (4.5L)</div>
                <div style={{ marginTop: '8px' }}><span style={{ color: 'var(--color-ash)' }}>[step: 42]</span> <span style={{ color: 'var(--color-fog)' }}>Fallback action:</span> <span style={{ color: 'var(--color-mist)' }}>AIR</span></div>
                <div style={{ color: 'var(--color-pulse-green)', paddingLeft: '8px', borderLeft: '2px solid var(--color-pulse-green)' }}>&#10003; PASS: temperature_deviation (2.1°C) within bounds</div>
                <div style={{ color: 'var(--color-ash)', marginTop: '8px' }}>&#8627; Forwarding AIR to Digital Twin...</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Feature 2 — Audit Log: text-right, visual-left (reversed) */}
      <div className="container">
        <div className="feature-row reversed">
          <div className="feature-text">
            <p style={{ color: 'var(--color-acid-lime)', fontSize: '12px', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '12px' }}>Audit trail</p>
            <h2 style={{ marginBottom: '16px' }}>Logged, queryable,<br/>exportable.</h2>
            <p style={{ color: 'var(--color-ash)', lineHeight: '1.5' }}>
              Every decision is written to OpenSearch with full context — the RL state, proposed action, safety filter verdict, Cedar policy result, and the agent's strategy reasoning. Query any step by ID. Export the full log to markdown for compliance review or demo preparation.
            </p>
            <div style={{ display: 'flex', gap: '8px', marginTop: '24px', flexWrap: 'wrap' }}>
              <span className="badge" style={{ color: 'var(--color-signal-teal)' }}>OpenSearch</span>
              <span className="badge" style={{ color: 'var(--color-iris-violet)' }}>step_id</span>
              <span className="badge" style={{ color: 'var(--color-fog)' }}>JSON export</span>
              <span className="badge" style={{ color: 'var(--color-fog)' }}>Markdown export</span>
            </div>
          </div>
          <div className="feature-visual">
            <div className="card" style={{ overflow: 'hidden' }}>
              <div style={{ marginBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', color: 'var(--color-ash)' }}>OpenSearch Document</span>
                <span style={{ fontSize: '12px', color: 'var(--color-ash)', fontFamily: 'var(--font-berkeley-mono)' }}>DEMO</span>
              </div>
              <div style={{ overflowX: 'auto', backgroundColor: 'var(--color-obsidian)', borderRadius: 'var(--radius-inputs)', padding: '16px' }}>
                <pre className="monospaced" style={{ color: 'var(--color-mist)', fontSize: '13px', lineHeight: '1.6', margin: 0, whiteSpace: 'pre-wrap' }}>{`{
  "timestamp": "2026-09-19T20:38:00Z",
  "step_id": 42,
  "state": {
    "temperature_deviation": 2.1,
    "water_usage": 4.8,
    "liquid_outlet_temp": 65.0,
    "cooling_efficiency": 1.2
  },
  "action_label": "AIR",
  "safety_filter_verdict": {
    "intervention_applied": true,
    "risk_level": "HIGH",
    "reason": "water_usage (4.8L) > max (4.5L)"
  },
  "cedar_verdict": {
    "allowed": true,
    "reason": "Air cooling fallback permitted"
  }
}`}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Feature 3 — Agent Chat: text-left, visual-right */}
      <div className="container">
        <div className="feature-row">
          <div className="feature-text">
            <p style={{ color: 'var(--color-acid-lime)', fontSize: '12px', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '12px' }}>Explainability</p>
            <h2 style={{ marginBottom: '16px' }}>Ask why any<br/>decision was made.</h2>
            <p style={{ color: 'var(--color-ash)', lineHeight: '1.5' }}>
              The Strands-powered ops copilot queries logged decisions from OpenSearch and explains what the RL agent did and why — citing the step ID, safety verdict, and Cedar outcome. Grounded in real data, never hallucinated.
            </p>
            <div style={{ display: 'flex', gap: '8px', marginTop: '24px', flexWrap: 'wrap' }}>
              <span className="badge" style={{ color: 'var(--color-lavender)' }}>Strands Agent</span>
              <span className="badge" style={{ color: 'var(--color-fog)' }}>Ollama</span>
              <span className="badge" style={{ color: 'var(--color-fog)' }}>llama3.1</span>
            </div>
          </div>
          <div className="feature-visual">
            <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '320px' }}>
              <div style={{ marginBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', color: 'var(--color-ash)' }}>Strands Agent</span>
                <span style={{ fontSize: '12px', color: 'var(--color-ash)', fontFamily: 'var(--font-berkeley-mono)' }}>DEMO</span>
              </div>
              <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', gap: '12px', justifyContent: 'center' }}>
                {MOCK_CHAT.map((msg, i) => (
                  <div key={i} style={{
                    alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                    backgroundColor: msg.role === 'user' ? 'rgba(255,255,255,0.05)' : 'var(--color-obsidian)',
                    border: msg.role === 'agent' ? '1px solid var(--color-graphite)' : 'none',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-inputs)',
                    maxWidth: '90%',
                    color: 'var(--color-mist)',
                    fontSize: '13px',
                    lineHeight: '1.5'
                  }}>
                    {msg.content}
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                <input type="text" className="input-field" style={{ flexGrow: 1, fontSize: '13px', padding: '8px 12px' }} placeholder="Ask about any decision..." disabled />
                <Link to="/dashboard" className="button-primary" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', fontSize: '13px', padding: '8px 14px' }}>
                  Try Live
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
