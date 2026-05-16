import React, { useState } from 'react';
import ImageUpload from './ImageUpload';
import ResultPanel from './ResultPanel';

export default function Dashboard() {
  const [patientName, setPatientName] = useState('');
  const [gender, setGender] = useState('male');
  const [activeModel, setActiveModel] = useState('rickets');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [nameError, setNameError] = useState('');
  const [genderError, setGenderError] = useState('');

  const validatePatientInfo = () => {
    let isValid = true;
    setNameError('');
    setGenderError('');

    if (!patientName.trim()) {
      setNameError('Patient name is required');
      isValid = false;
    } else if (patientName.trim().length < 2) {
      setNameError('Patient name must be at least 2 characters');
      isValid = false;
    }

    if (!gender) {
      setGenderError('Gender is required');
      isValid = false;
    }

    return isValid;
  };

  const handleImageUpload = async (imageFile, imageBytes) => {
    if (!validatePatientInfo()) {
      return;
    }

    setLoading(true);
    setError('');
    setResults(null);

    try {
      const formData = new FormData();
      formData.append('file', imageFile);

      const endpoint = activeModel === 'cmvd' 
        ? 'http://localhost:8000/detect/cmvd' 
        : 'http://localhost:8000/detect/rickets';

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok && data.result && !data.result.error) {
        // Extract prediction info from response
        const resultData = data.result;
        const prediction = resultData.prediction || 'Unknown';
        const confidence = resultData.confidence / 100; // Convert from percentage to decimal
        
        // Use class_probabilities from model
        const probabilities = {};
        if (resultData.class_probabilities) {
          for (const [className, prob] of Object.entries(resultData.class_probabilities)) {
            probabilities[className] = prob / 100; // Convert to decimal
          }
        } else {
          probabilities[prediction] = confidence;
        }

        // Create record object
        const record = {
          id: Math.random().toString(36).substr(2, 9),
          patientName: patientName.trim(),
          gender,
          model: activeModel,
          prediction: prediction,
          confidence: confidence,
          allProbabilities: probabilities,
          imageData: null,
          timestamp: new Date().toISOString(),
        };

        // Save to backend database
        try {
          const savePayload = {
            patient_name: patientName.trim(),
            gender: gender,
            model: activeModel,
            prediction: prediction,
            confidence: confidence,
            probabilities: probabilities
          };
          
          console.log('📤 Sending record to database:', savePayload);
          
          const saveResponse = await fetch('http://localhost:8000/records/save', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(savePayload)
          });
          
          const saveText = await saveResponse.text();
          console.log('📥 Response status:', saveResponse.status);
          console.log('📥 Response text:', saveText);
          
          if (saveResponse.ok) {
            const saveData = JSON.parse(saveText);
            console.log('✅ Record saved to database:', saveData);
          } else {
            console.error('❌ Failed to save record to database - Status:', saveResponse.status);
            console.error('❌ Response:', saveText);
          }
        } catch (storageErr) {
          console.error('❌ Error saving record to database:', storageErr);
        }

        setResults({
          prediction: prediction,
          confidence: confidence,
          probabilities: probabilities,
          is_medical: true,
          model: activeModel,
          condition: resultData.condition,
          urgency: resultData.urgency,
        });
      } else {
        setError(data.detail || data.result?.error || 'Failed to analyze image. Please try again.');
      }
    } catch (err) {
      setError('Network error. Please make sure the backend is running on http://localhost:8000');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-wrapper">
      {/* Header */}
      <header style={{
        background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)',
        padding: '30px 20px',
        color: 'white'
      }}>
        <div className="page-content">
          <div className="flex-between" style={{ flexWrap: 'wrap', gap: '20px' }}>
            <div>
              <h1 style={{ fontSize: '2em', marginBottom: '5px', fontWeight: '700' }}>🏥 Medical AI Analysis</h1>
              <p style={{ opacity: 0.9, margin: 0 }}>Real-time AI Medical Image Analysis & Diagnosis</p>
            </div>
            <div className="flex" style={{ gap: '10px' }}>
              <button
                style={{
                  background: activeModel === 'rickets' 
                    ? 'rgba(255,255,255,0.3)' 
                    : 'white',
                  color: activeModel === 'rickets' 
                    ? 'white' 
                    : '#6366f1',
                  border: 'none',
                  padding: '12px 24px',
                  borderRadius: '8px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease'
                }}
                onClick={() => setActiveModel('rickets')}
              >
                🦴 Rickets
              </button>
              <button
                style={{
                  background: activeModel === 'cmvd' 
                    ? 'rgba(255,255,255,0.3)' 
                    : 'white',
                  color: activeModel === 'cmvd' 
                    ? 'white' 
                    : '#6366f1',
                  border: 'none',
                  padding: '12px 24px',
                  borderRadius: '8px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease'
                }}
                onClick={() => setActiveModel('cmvd')}
              >
                🫀 CMVD
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="page-content">
        <div className="grid-2" style={{ gap: '30px' }}>
          {/* Left Column - Patient Info & Upload */}
          <div>
            {/* Patient Info Card */}
            <div className="card" style={{
              background: 'linear-gradient(135deg, #ffffff 0%, #f9fafb 100%)',
              border: '2px solid transparent',
              backgroundImage: 'linear-gradient(135deg, #ffffff 0%, #f9fafb 100%), linear-gradient(135deg, #6366f1 0%, #ec4899 100%)',
              backgroundOrigin: 'border-box',
              backgroundClip: 'padding-box, border-box'
            }}>
              <h2 style={{
                color: '#6366f1',
                marginBottom: '20px',
                fontSize: '1.3em',
                fontWeight: '700'
              }}>👤 Patient Information</h2>

              <div className="form-group">
                <label htmlFor="patientName" style={{ color: '#4f46e5', fontWeight: '600' }}>Patient Name *</label>
                <input
                  id="patientName"
                  type="text"
                  value={patientName}
                  onChange={(e) => {
                    setPatientName(e.target.value);
                    setNameError('');
                  }}
                  placeholder="Enter patient name"
                  style={{
                    borderColor: nameError ? '#ef4444' : '#e5e7eb',
                    boxShadow: nameError ? '0 0 0 3px rgba(239, 68, 68, 0.1)' : 'none'
                  }}
                />
                {nameError && <span className="form-error" style={{ color: '#ef4444' }}>{nameError}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="gender" style={{ color: '#8b5cf6', fontWeight: '600' }}>Gender *</label>
                <select
                  id="gender"
                  value={gender}
                  onChange={(e) => {
                    setGender(e.target.value);
                    setGenderError('');
                  }}
                  style={{
                    borderColor: genderError ? '#ef4444' : '#e5e7eb',
                    boxShadow: genderError ? '0 0 0 3px rgba(239, 68, 68, 0.1)' : 'none'
                  }}
                >
                  <option value="">Select gender</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
                {genderError && <span className="form-error" style={{ color: '#ef4444' }}>{genderError}</span>}
              </div>

              <div style={{
                background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)',
                border: '2px solid rgba(99, 102, 241, 0.3)',
                borderRadius: '8px',
                padding: '15px',
                fontSize: '0.9em',
                color: '#4f46e5',
                fontWeight: '500'
              }}>
                <strong>📌 Note:</strong> Please enter patient information before uploading the image. 
                This information will be saved with the analysis results.
              </div>
            </div>

            {/* Image Upload Card */}
            <div className="card" style={{
              background: 'linear-gradient(135deg, #ffffff 0%, #f9fafb 100%)',
              border: '2px solid transparent',
              backgroundImage: 'linear-gradient(135deg, #ffffff 0%, #f9fafb 100%), linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
              backgroundOrigin: 'border-box',
              backgroundClip: 'padding-box, border-box'
            }}>
              <h2 style={{
                color: '#8b5cf6',
                marginBottom: '20px',
                fontSize: '1.3em',
                fontWeight: '700'
              }}>📸 Upload Medical Image</h2>
              <ImageUpload 
                onImageUpload={handleImageUpload}
                loading={loading}
                activeModel={activeModel}
              />
            </div>
          </div>

          {/* Right Column - Results */}
          <div>
            {error && (
              <div style={{
                background: 'linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)',
                border: '2px solid #fca5a5',
                color: '#991b1b',
                padding: '15px 20px',
                borderRadius: '12px',
                marginBottom: '20px',
                fontWeight: '500',
                display: 'flex',
                alignItems: 'center',
                gap: '10px'
              }}>
                <span style={{ fontSize: '1.3em' }}>⚠️</span>
                <div>{error}</div>
              </div>
            )}

            {loading && (
              <div className="card" style={{
                background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)',
                border: '2px solid rgba(6, 182, 212, 0.3)'
              }}>
                <div className="loading">
                  <div className="spinner"></div>
                  <div className="loading-text" style={{ color: '#0891b2', fontWeight: '600' }}>
                    🔄 Analyzing image with AI...
                  </div>
                </div>
              </div>
            )}

            {results && !loading && (
              <div className="card" style={{
                background: 'linear-gradient(135deg, #ffffff 0%, #f9fafb 100%)',
                border: '2px solid transparent',
                backgroundImage: 'linear-gradient(135deg, #ffffff 0%, #f9fafb 100%), linear-gradient(135deg, #ec4899 0%, #06b6d4 100%)',
                backgroundOrigin: 'border-box',
                backgroundClip: 'padding-box, border-box'
              }}>
                <h2 style={{
                  color: '#ec4899',
                  marginBottom: '20px',
                  fontSize: '1.3em',
                  fontWeight: '700'
                }}>✅ Analysis Results</h2>
                <ResultPanel 
                  result={results}
                  patientName={patientName}
                  gender={gender}
                  model={activeModel}
                />
              </div>
            )}

            {!loading && !results && !error && (
              <div className="card" style={{
                background: 'linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%)',
                textAlign: 'center',
                padding: '40px',
                border: '2px dashed var(--border-color)'
              }}>
                <div style={{ fontSize: '3em', marginBottom: '15px' }}>📋</div>
                <p style={{ color: 'var(--text-light)', marginBottom: '10px', fontSize: '1.1em', fontWeight: '500' }}>
                  No analysis yet
                </p>
                <p style={{ fontSize: '0.9em', color: 'var(--text-light)' }}>
                  Upload a medical image to see detailed analysis results here
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
