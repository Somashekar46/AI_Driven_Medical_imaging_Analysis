import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate, useLocation } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import PatientRecords from './components/PatientRecords';
import About from './components/About';
import Auth from './components/Auth';
import './index.css';

function Navigation({ user, onLogout }) {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('authToken');
    onLogout();
    navigate('/auth');
  };

  const isActive = (path) => location.pathname === path ? 'active' : '';

  return (
    <nav>
      <div className="nav-container">
        <Link to="/" className="nav-brand">
          🏥 Medical AI
        </Link>

        {user && (
          <>
            <ul className="nav-center">
              <li><Link to="/dashboard" className={`nav-link ${isActive('/dashboard')}`}>Dashboard</Link></li>
              <li><Link to="/records" className={`nav-link ${isActive('/records')}`}>Patient Records</Link></li>
              <li><Link to="/about" className={`nav-link ${isActive('/about')}`}>About</Link></li>
            </ul>

            <div className="nav-right">
              <span style={{ color: 'white', fontSize: '0.95em' }}>👤 {user.name}</span>
              <button className="logout-btn" onClick={handleLogout}>
                Logout
              </button>
            </div>
          </>
        )}
      </div>
    </nav>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const handleAuthSuccess = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    setUser(null);
  };

  if (loading) {
    return (
      <div className="flex-center" style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)' }}>
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <Router>
      <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        {user && <Navigation user={user} onLogout={handleLogout} />}

        <Routes>
          {!user ? (
            <>
              <Route path="*" element={<Auth onAuthSuccess={handleAuthSuccess} />} />
            </>
          ) : (
            <>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/records" element={<PatientRecords />} />
              <Route path="/about" element={<About />} />
              <Route path="/" element={<Dashboard />} />
            </>
          )}
        </Routes>
      </div>
    </Router>
  );
}
