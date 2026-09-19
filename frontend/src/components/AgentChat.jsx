import { useState } from 'react';
import { askAgent } from '../api/client';

export default function AgentChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsLoading(true);

    try {
      const data = await askAgent(userMsg);
      // Fallback if data.answer doesn't exist, we just JSON.stringify the result
      const answer = data.answer || JSON.stringify(data);
      setMessages(prev => [...prev, { role: 'agent', content: answer }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'agent', content: `Error: ${err.message}`, isError: true }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '400px' }}>
      <div style={{ marginBottom: '16px' }}>
        <h3>Strands Agent</h3>
        <p style={{ color: 'var(--color-ash)', fontSize: '13px' }}>Ask why decisions were made.</p>
      </div>
      
      <div style={{ flexGrow: 1, overflowY: 'auto', marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {messages.length === 0 ? (
          <div style={{ color: 'var(--color-ash)', fontSize: '14px', textAlign: 'center', marginTop: 'auto', marginBottom: 'auto' }}>
            No messages yet. Ask a question about the latest cooling decisions.
          </div>
        ) : (
          messages.map((msg, i) => (
            <div key={i} style={{ 
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              backgroundColor: msg.role === 'user' ? 'rgba(255,255,255,0.05)' : 'var(--color-obsidian)',
              border: msg.role === 'agent' ? '1px solid var(--color-graphite)' : 'none',
              padding: '12px 16px',
              borderRadius: 'var(--radius-inputs)',
              maxWidth: '85%',
              color: msg.isError ? 'var(--color-coral-red)' : 'var(--color-mist)',
              fontSize: '14px'
            }}>
              {msg.content}
            </div>
          ))
        )}
        {isLoading && (
          <div style={{ alignSelf: 'flex-start', color: 'var(--color-ash)', fontSize: '13px' }}>
            Agent is thinking...
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '8px' }}>
        <input 
          type="text" 
          className="input-field" 
          style={{ flexGrow: 1 }} 
          placeholder="Ask why you picked a certain action..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isLoading}
        />
        <button type="submit" className="button-primary" disabled={!input.trim() || isLoading}>
          Ask
        </button>
      </form>
    </div>
  );
}
