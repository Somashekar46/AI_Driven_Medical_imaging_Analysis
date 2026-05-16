import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Auth({ onAuthSuccess }) {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const validateForm = () => {
    const newErrors = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    if (!isLogin) {
      if (!formData.name) {
        newErrors.name = 'Name is required';
      }
      if (!formData.confirmPassword) {
        newErrors.confirmPassword = 'Please confirm password';
      } else if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = 'Passwords do not match';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) return;

    setLoading(true);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));

      // Store user data in localStorage
      const userData = {
        email: formData.email,
        name: isLogin ? 'User' : formData.name,
        loggedInAt: new Date().toISOString(),
      };

      localStorage.setItem('user', JSON.stringify(userData));
      localStorage.setItem('authToken', 'token_' + Math.random().toString(36).substr(2, 9));

      onAuthSuccess(userData);
      navigate('/dashboard');
    } catch (error) {
      setErrors({ general: 'An error occurred. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-wrapper">
      <div className="page-content flex-center" style={{ minHeight: 'calc(100vh - 70px)' }}>
        <div className="card" style={{ maxWidth: '450px', width: '100%' }}>
          <div className="text-center mb-20">
            <h1 style={{ color: 'var(--primary)', marginBottom: '10px' }}>
              🏥 Medical AI
            </h1>
            <p style={{ color: 'var(--text-light)', fontSize: '0.95em' }}>
              {isLogin ? 'Sign in to your account' : 'Create a new account'}
            </p>
          </div>

          {errors.general && (
            <div className="alert alert-error" style={{ marginBottom: '20px' }}>
              {errors.general}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {!isLogin && (
              <div className="form-group">
                <label htmlFor="name">Full Name</label>
                <input
                  id="name"
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Enter your full name"
                />
                {errors.name && <span className="form-error">{errors.name}</span>}
              </div>
            )}

            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                id="email"
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="Enter your email"
              />
              {errors.email && <span className="form-error">{errors.email}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Enter password"
              />
              {errors.password && <span className="form-error">{errors.password}</span>}
            </div>

            {!isLogin && (
              <div className="form-group">
                <label htmlFor="confirmPassword">Confirm Password</label>
                <input
                  id="confirmPassword"
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder="Confirm password"
                />
                {errors.confirmPassword && <span className="form-error">{errors.confirmPassword}</span>}
              </div>
            )}

            <button
              type="submit"
              className="btn-primary"
              disabled={loading}
              style={{ width: '100%', marginTop: '20px' }}
            >
              {loading ? (
                <span className="flex-center gap-20">
                  <span className="spinner" style={{ width: '20px', height: '20px' }}></span>
                  Processing...
                </span>
              ) : (
                isLogin ? 'Sign In' : 'Create Account'
              )}
            </button>
          </form>

          <div className="text-center mt-20">
            <p style={{ fontSize: '0.95em', marginBottom: '10px' }}>
              {isLogin ? "Don't have an account?" : 'Already have an account?'}
            </p>
            <button
              onClick={() => {
                setIsLogin(!isLogin);
                setErrors({});
              }}
              className="btn-secondary"
              style={{ width: '100%' }}
            >
              {isLogin ? 'Create Account' : 'Sign In'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
