import React from 'react';

export default function About() {
  return (
    <div className="page-wrapper">
      <div className="page-content">
        <div className="card mb-20">
          <h1 className="card-header">🏥 About Medical AI</h1>
          
          <div style={{ marginBottom: '30px' }}>
            <h2 style={{ color: 'var(--primary)', fontSize: '1.3em', marginBottom: '15px' }}>
              Project Overview
            </h2>
            <p style={{ lineHeight: '1.8', marginBottom: '15px' }}>
              Medical AI is an advanced diagnostic platform that leverages cutting-edge deep learning models 
              to assist healthcare professionals in analyzing medical images. Our system is trained to detect 
              and classify specific medical conditions with high accuracy and reliability.
            </p>
            <p style={{ lineHeight: '1.8', marginBottom: '15px' }}>
              By combining state-of-the-art neural networks with intuitive user interfaces, we aim to 
              make advanced medical diagnostics more accessible and efficient for healthcare providers worldwide.
            </p>
          </div>

          <div style={{ marginBottom: '30px' }}>
            <h2 style={{ color: 'var(--primary)', fontSize: '1.3em', marginBottom: '15px' }}>
              🧠 AI Models
            </h2>
            
            <div className="grid-2" style={{ marginBottom: '20px' }}>
              <div className="card" style={{ background: 'rgba(102, 126, 234, 0.05)', border: '2px solid var(--primary)' }}>
                <h3 style={{ color: 'var(--primary)', marginBottom: '15px', fontSize: '1.1em' }}>
                  Rickets Detection Model
                </h3>
                <ul style={{ marginLeft: '20px', lineHeight: '1.8' }}>
                  <li><strong>Architecture:</strong> EfficientNet-B3 + CBAM Attention</li>
                  <li><strong>Input Size:</strong> 300×300 pixels</li>
                  <li><strong>Training Epochs:</strong> 100+</li>
                  <li><strong>Classes:</strong> Normal, Mild, Severe</li>
                  <li><strong>Use Case:</strong> Pediatric rickets classification from X-ray images</li>
                </ul>
              </div>

              <div className="card" style={{ background: 'rgba(102, 126, 234, 0.05)', border: '2px solid var(--primary)' }}>
                <h3 style={{ color: 'var(--primary)', marginBottom: '15px', fontSize: '1.1em' }}>
                  CMVD Detection Model
                </h3>
                <ul style={{ marginLeft: '20px', lineHeight: '1.8' }}>
                  <li><strong>Architecture:</strong> ResNet50 + CBAM Attention</li>
                  <li><strong>Input Size:</strong> 224×224 pixels</li>
                  <li><strong>Training Epochs:</strong> 58</li>
                  <li><strong>Performance:</strong> AUC 0.9609</li>
                  <li><strong>Use Case:</strong> ECG-based cardiac abnormality detection</li>
                </ul>
              </div>
            </div>
          </div>

          <div style={{ marginBottom: '30px' }}>
            <h2 style={{ color: 'var(--primary)', fontSize: '1.3em', marginBottom: '15px' }}>
              ✨ Key Features
            </h2>
            <ul style={{ marginLeft: '20px', lineHeight: '1.8' }}>
              <li>🔒 <strong>Secure Authentication:</strong> User accounts with encrypted password storage</li>
              <li>📋 <strong>Patient Records:</strong> Complete patient history with analysis results</li>
              <li>🎯 <strong>Accurate Diagnostics:</strong> State-of-the-art deep learning models</li>
              <li>📊 <strong>Detailed Reports:</strong> Comprehensive analysis with confidence scores</li>
              <li>📱 <strong>Responsive Design:</strong> Works seamlessly on all devices</li>
              <li>⚡ <strong>Real-time Processing:</strong> Fast inference for immediate results</li>
            </ul>
          </div>

          <div style={{ marginBottom: '30px' }}>
            <h2 style={{ color: 'var(--primary)', fontSize: '1.3em', marginBottom: '15px' }}>
              🚀 How to Use
            </h2>
            <ol style={{ marginLeft: '20px', lineHeight: '1.8' }}>
              <li><strong>Create Account:</strong> Sign up with your email and password</li>
              <li><strong>Enter Patient Info:</strong> Provide patient name and gender before analysis</li>
              <li><strong>Upload Image:</strong> Select a medical image (X-ray, ECG, etc.)</li>
              <li><strong>View Results:</strong> Receive instant analysis with confidence scores</li>
              <li><strong>Save Records:</strong> Patient records are automatically saved for future reference</li>
              <li><strong>Access History:</strong> View all previous analyses in the Patient Records section</li>
            </ol>
          </div>

          <div style={{ marginBottom: '30px' }}>
            <h2 style={{ color: 'var(--primary)', fontSize: '1.3em', marginBottom: '15px' }}>
              ⚕️ Clinical Disclaimer
            </h2>
            <div className="alert alert-warning">
              <p style={{ marginBottom: '10px' }}>
                <strong>Important:</strong> This AI system is designed as a <strong>diagnostic aid only</strong> 
                and should not be used as a replacement for professional medical judgment. Always consult 
                qualified healthcare professionals for final diagnosis and treatment decisions.
              </p>
              <p style={{ marginBottom: '10px' }}>
                The results provided by this system are based on machine learning models trained on specific 
                datasets and may not be 100% accurate in all cases.
              </p>
              <p>
                Medical professionals using this system retain full responsibility for patient care and 
                treatment decisions.
              </p>
            </div>
          </div>

          <div style={{ marginBottom: '30px' }}>
            <h2 style={{ color: 'var(--primary)', fontSize: '1.3em', marginBottom: '15px' }}>
              🛠️ Technology Stack
            </h2>
            <div className="grid-3">
              <div>
                <h4 style={{ color: 'var(--text-dark)', marginBottom: '10px' }}>Backend</h4>
                <ul style={{ marginLeft: '15px', lineHeight: '1.6', fontSize: '0.95em' }}>
                  <li>Python 3.8+</li>
                  <li>FastAPI</li>
                  <li>PyTorch 2.4.1</li>
                  <li>PIL/Pillow</li>
                </ul>
              </div>
              <div>
                <h4 style={{ color: 'var(--text-dark)', marginBottom: '10px' }}>Frontend</h4>
                <ul style={{ marginLeft: '15px', lineHeight: '1.6', fontSize: '0.95em' }}>
                  <li>React 18.3.1</li>
                  <li>React Router v6</li>
                  <li>Vite</li>
                  <li>Modern CSS3</li>
                </ul>
              </div>
              <div>
                <h4 style={{ color: 'var(--text-dark)', marginBottom: '10px' }}>Tools</h4>
                <ul style={{ marginLeft: '15px', lineHeight: '1.6', fontSize: '0.95em' }}>
                  <li>Git & GitHub</li>
                  <li>Node.js</li>
                  <li>CUDA (optional)</li>
                  <li>Docker (optional)</li>
                </ul>
              </div>
            </div>
          </div>

          <div>
            <h2 style={{ color: 'var(--primary)', fontSize: '1.3em', marginBottom: '15px' }}>
              📧 Support & Feedback
            </h2>
            <p style={{ lineHeight: '1.8' }}>
              For technical support, bug reports, or feature requests, please contact our development team. 
              We continuously improve our models and system based on user feedback and clinical validation studies.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
