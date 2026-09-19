import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import HomePage from './pages/HomePage';
import Dashboard from './pages/Dashboard';
import './styles.css';

function App() {
  return (
    <BrowserRouter>
      <div>
        <nav className="nav-bar">
          <div className="nav-container">
            <Link to="/" className="nav-logo" style={{ textDecoration: 'none' }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ display: 'inline', verticalAlign: 'middle', marginRight: '8px' }}>
                <polygon points="12 2 2 22 22 22"></polygon>
              </svg>
              Thermion
            </Link>
            <div className="nav-links">
              <Link to="/" className="nav-button-text" style={{ textDecoration: 'none' }}>Home</Link>
              <Link to="/dashboard" className="nav-button-text" style={{ textDecoration: 'none' }}>Dashboard</Link>
            </div>
          </div>
        </nav>

        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>

        <footer style={{ borderTop: '1px solid var(--color-graphite)', padding: '48px 0', marginTop: '96px', textAlign: 'center', color: 'var(--color-ash)', fontSize: '13px' }}>
          <p>Thermion &copy; 2026. Built with React and Vite.</p>
        </footer>
      </div>
    </BrowserRouter>
  );
}

export default App;
