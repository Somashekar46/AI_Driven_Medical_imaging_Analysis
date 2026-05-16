import React, { useState, useEffect } from 'react';

export default function PatientRecords() {
  const [records, setRecords] = useState([]);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  // Load records from backend database on mount
  useEffect(() => {
    loadRecords();
    
    // Refresh records every 5 seconds
    const interval = setInterval(loadRecords, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadRecords = async () => {
    try {
      const response = await fetch('http://localhost:8000/records/all');
      if (response.ok) {
        const data = await response.json();
        console.log('📊 Records loaded from database:', data);
        setRecords(data.records || []);
      } else {
        console.error('Failed to load records');
        setRecords([]);
      }
    } catch (err) {
      console.error('Error loading records from database:', err);
      setRecords([]);
    }
  };

  const handleDeleteRecord = (id) => {
    if (window.confirm('Are you sure you want to delete this record?')) {
      // Delete from database
      fetch(`http://localhost:8000/records/${id}`, {
        method: 'DELETE'
      }).then(res => {
        if (res.ok) {
          console.log('✅ Record deleted from database');
          // Remove from local state
          setRecords(records.filter(record => record.id !== id));
          setShowDetails(false);
          setSelectedRecord(null);
        }
      }).catch(err => console.error('Error deleting record:', err));
    }
  };

  const handleViewDetails = (record) => {
    setSelectedRecord(record);
    setShowDetails(true);
  };

  const handleCloseDetails = () => {
    setShowDetails(false);
    setSelectedRecord(null);
  };

  return (
    <div className="page-wrapper">
      <div className="page-content">
        {/* Header */}
        <div style={{
          background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)',
          color: 'white',
          padding: '30px',
          borderRadius: '12px',
          marginBottom: '25px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1 style={{ margin: 0, fontSize: '2em', marginBottom: '5px' }}>👥 Patient Records</h1>
              <p style={{ margin: 0, opacity: 0.9 }}>Manage and review all patient analyses</p>
            </div>
            <div style={{
              background: 'rgba(255,255,255,0.2)',
              padding: '15px 25px',
              borderRadius: '10px',
              fontSize: '1.5em',
              fontWeight: '700'
            }}>
              {records.length}
            </div>
          </div>
        </div>

        <div className="card">
          {records.length === 0 ? (
            <div className="text-center p-20">
              <div style={{ fontSize: '3em', marginBottom: '15px' }}>📋</div>
              <p style={{ color: 'var(--text-light)', marginBottom: '10px', fontSize: '1.1em', fontWeight: '500' }}>
                No patient records yet
              </p>
              <p style={{ fontSize: '0.9em', color: 'var(--text-light)' }}>
                Patient records will appear here after successful medical image analysis
              </p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table>
                <thead>
                  <tr style={{
                    background: 'linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%)',
                    borderBottom: '2px solid var(--border-color)'
                  }}>
                    <th style={{ color: '#6366f1', fontWeight: '700' }}>👤 Patient Name</th>
                    <th style={{ color: '#8b5cf6', fontWeight: '700' }}>⚤ Gender</th>
                    <th style={{ color: '#ec4899', fontWeight: '700' }}>🔬 Model</th>
                    <th style={{ color: '#06b6d4', fontWeight: '700' }}>📊 Prediction</th>
                    <th style={{ color: '#10b981', fontWeight: '700' }}>📈 Confidence</th>
                    <th style={{ color: '#f59e0b', fontWeight: '700' }}>📅 Date</th>
                    <th style={{ color: '#6b7280', fontWeight: '700' }}>⚙️ Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((record, idx) => (
                    <tr 
                      key={record.id}
                      style={{
                        background: idx % 2 === 0 ? 'white' : '#f9fafb',
                        borderBottom: '1px solid var(--border-color)',
                        transition: 'all 0.3s ease'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = 'linear-gradient(135deg, #f0f9ff 0%, #f5f3ff 100%)'}
                      onMouseLeave={(e) => e.currentTarget.style.background = idx % 2 === 0 ? 'white' : '#f9fafb'}
                    >
                      <td style={{ fontWeight: '600', color: '#6366f1' }}>{record.patientName}</td>
                      <td style={{ textTransform: 'capitalize', fontWeight: '500' }}>{record.gender}</td>
                      <td>
                        <span style={{
                          display: 'inline-block',
                          padding: '6px 12px',
                          borderRadius: '20px',
                          backgroundColor: record.model === 'rickets' 
                            ? 'rgba(99, 102, 241, 0.1)' 
                            : 'rgba(236, 72, 153, 0.1)',
                          color: record.model === 'rickets' 
                            ? '#6366f1' 
                            : '#ec4899',
                          fontSize: '0.85em',
                          fontWeight: '600'
                        }}>
                          {record.model.toUpperCase()}
                        </span>
                      </td>
                      <td>
                        <span style={{
                          display: 'inline-block',
                          padding: '6px 12px',
                          borderRadius: '20px',
                          backgroundColor: record.prediction.toLowerCase().includes('normal')
                            ? 'rgba(16, 185, 129, 0.1)'
                            : record.prediction.toLowerCase().includes('mild')
                            ? 'rgba(245, 158, 11, 0.1)'
                            : 'rgba(239, 68, 68, 0.1)',
                          color: record.prediction.toLowerCase().includes('normal')
                            ? '#10b981'
                            : record.prediction.toLowerCase().includes('mild')
                            ? '#f59e0b'
                            : '#ef4444',
                          fontWeight: '600',
                          fontSize: '0.85em'
                        }}>
                          {record.prediction}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div style={{
                            width: '30px',
                            height: '30px',
                            borderRadius: '50%',
                            background: `conic-gradient(#10b981 0deg ${record.confidence * 360}deg, #e5e7eb ${record.confidence * 360}deg)`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'white',
                            fontSize: '0.7em',
                            fontWeight: '700'
                          }}>
                          </div>
                          <span style={{ fontWeight: '600', color: '#10b981' }}>
                            {(record.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                      <td style={{ fontSize: '0.9em' }}>
                        {new Date(record.timestamp).toLocaleDateString()}
                      </td>
                      <td>
                        <div className="table-actions" style={{ gap: '5px' }}>
                          <button
                            className="btn-primary btn-small"
                            onClick={() => handleViewDetails(record)}
                            style={{ background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)' }}
                          >
                            👁️ View
                          </button>
                          <button
                            className="btn-danger btn-small"
                            onClick={() => handleDeleteRecord(record.id)}
                          >
                            🗑️ Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Details Modal */}
      {showDetails && selectedRecord && (
        <div className="modal-overlay" onClick={handleCloseDetails}>
          <div
            className="modal"
            onClick={e => e.stopPropagation()}
            style={{ maxWidth: '600px' }}
          >
            <div className="flex-between mb-20" style={{ marginBottom: '20px' }}>
              <h2 className="modal-header" style={{ margin: 0 }}>
                {selectedRecord.patientName} - Results
              </h2>
              <button
                onClick={handleCloseDetails}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '1.5em',
                  cursor: 'pointer',
                  color: 'var(--text-dark)'
                }}
              >
                ✕
              </button>
            </div>

            <div className="modal-body">
              <div style={{ marginBottom: '20px' }}>
                <h3 style={{ color: 'var(--primary)', marginBottom: '10px', fontSize: '1em' }}>
                  Patient Information
                </h3>
                <div style={{ marginLeft: '15px', lineHeight: '2' }}>
                  <p><strong>Name:</strong> {selectedRecord.patientName}</p>
                  <p><strong>Gender:</strong> {selectedRecord.gender}</p>
                  <p><strong>Date:</strong> {new Date(selectedRecord.timestamp).toLocaleString()}</p>
                </div>
              </div>

              <div style={{ marginBottom: '20px' }}>
                <h3 style={{ color: 'var(--primary)', marginBottom: '10px', fontSize: '1em' }}>
                  Analysis Results
                </h3>
                <div style={{ marginLeft: '15px', lineHeight: '2' }}>
                  <p><strong>Model:</strong> {selectedRecord.model}</p>
                  <p>
                    <strong>Prediction:</strong>{' '}
                    <span style={{
                      padding: '4px 10px',
                      borderRadius: '15px',
                      backgroundColor: selectedRecord.model === 'rickets' 
                        ? 'rgba(102, 126, 234, 0.1)' 
                        : 'rgba(240, 147, 251, 0.1)',
                      color: selectedRecord.model === 'rickets' 
                        ? 'var(--primary)' 
                        : 'var(--secondary)',
                      fontWeight: '600'
                    }}>
                      {selectedRecord.prediction}
                    </span>
                  </p>
                  <p><strong>Confidence:</strong> {(selectedRecord.confidence * 100).toFixed(2)}%</p>
                </div>
              </div>

              {selectedRecord.allProbabilities && (
                <div style={{ marginBottom: '20px' }}>
                  <h3 style={{ color: 'var(--primary)', marginBottom: '10px', fontSize: '1em' }}>
                    Detailed Probabilities
                  </h3>
                  <div style={{ marginLeft: '15px' }}>
                    {Object.entries(selectedRecord.allProbabilities).map(([label, prob]) => (
                      <div key={label} style={{ marginBottom: '10px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                          <span style={{ fontWeight: '500' }}>{label}</span>
                          <span style={{ fontWeight: '600', color: 'var(--primary)' }}>
                            {(prob * 100).toFixed(2)}%
                          </span>
                        </div>
                        <div style={{
                          height: '8px',
                          backgroundColor: '#e0e0e0',
                          borderRadius: '4px',
                          overflow: 'hidden'
                        }}>
                          <div style={{
                            height: '100%',
                            width: `${prob * 100}%`,
                            backgroundColor: 'var(--primary)',
                            borderRadius: '4px',
                            transition: 'width 0.3s ease'
                          }}></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedRecord.imageData && (
                <div style={{ marginBottom: '20px' }}>
                  <h3 style={{ color: 'var(--primary)', marginBottom: '10px', fontSize: '1em' }}>
                    Analyzed Image
                  </h3>
                  <img
                    src={selectedRecord.imageData}
                    alt="Analyzed"
                    style={{
                      maxWidth: '100%',
                      maxHeight: '300px',
                      borderRadius: '8px',
                      border: '1px solid var(--border-color)'
                    }}
                  />
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button
                className="btn-secondary"
                onClick={handleCloseDetails}
              >
                Close
              </button>
              <button
                className="btn-danger"
                onClick={() => {
                  handleDeleteRecord(selectedRecord.id);
                }}
              >
                Delete Record
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
