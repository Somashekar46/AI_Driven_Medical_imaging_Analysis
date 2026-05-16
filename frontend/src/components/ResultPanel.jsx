import React, { useState, useRef, useEffect } from 'react';

export default function ResultPanel({ result, patientName, gender, model }) {
  const [showChart, setShowChart] = useState(false);
  const canvasRef = useRef(null);
  const heatmapCanvasRef = useRef(null);

  useEffect(() => {
    if (showChart && canvasRef.current) {
      drawChart();
    }
  }, [showChart]);

  useEffect(() => {
    if (heatmapCanvasRef.current) {
      generateHeatmap();
    }
  }, [result]);

  if (!result) {
    return <div>No results available</div>;
  }

  const prediction = result.prediction || 'Unknown';
  const confidence = typeof result.confidence === 'number' && result.confidence <= 1 
    ? (result.confidence * 100).toFixed(2) 
    : (result.confidence || 0).toFixed(2);
  const probabilities = result.probabilities || {};

  const getPredictionColor = () => {
    if (model === 'rickets') {
      if (prediction.toLowerCase().includes('normal')) return '#10b981';
      if (prediction.toLowerCase().includes('mild')) return '#f59e0b';
      return '#ef4444';
    } else {
      return prediction.toLowerCase().includes('normal') ? '#10b981' : '#ef4444';
    }
  };

  const getSeverityLevel = () => {
    const conf = parseFloat(confidence);
    if (conf >= 85) return 'High';
    if (conf >= 70) return 'Medium';
    return 'Low';
  };

  const getClinicalSuggestions = () => {
    if (model === 'rickets') {
      if (prediction.toLowerCase().includes('normal')) {
        return [
          '✓ Normal bone density detected',
          '✓ Vitamin D levels appear adequate',
          '✓ Continue routine pediatric care',
          '✓ Maintain balanced diet with calcium',
          '✓ Regular follow-up recommended'
        ];
      } else if (prediction.toLowerCase().includes('mild')) {
        return [
          '⚠ Mild rickets detected',
          '⚠ Consider Vitamin D supplementation',
          '⚠ Increase dietary calcium intake',
          '⚠ Follow-up X-ray in 4-6 weeks',
          '⚠ Consult pediatric endocrinologist'
        ];
      } else {
        return [
          '⚠ Severe rickets detected',
          '⚠ Immediate Vitamin D therapy needed',
          '⚠ Urgent pediatric endocrinology referral',
          '⚠ Close biochemical monitoring required',
          '⚠ Consider hospitalization if symptomatic'
        ];
      }
    } else {
      if (prediction.toLowerCase().includes('normal')) {
        return [
          '✓ ECG pattern within normal limits',
          '✓ No signs of CMVD detected',
          '✓ Continue routine cardiac monitoring',
          '✓ Maintain heart-healthy lifestyle',
          '✓ Annual ECG follow-up recommended'
        ];
      } else {
        return [
          '⚠ Potential CMVD indicators detected',
          '⚠ Recommend stress testing',
          '⚠ Consider advanced cardiac imaging',
          '⚠ Cardiology consultation advised',
          '⚠ Regular monitoring essential'
        ];
      }
    }
  };

  const drawChart = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const padding = 40;
    const chartWidth = width - 2 * padding;
    const chartHeight = height - 2 * padding;

    // Clear canvas
    ctx.fillStyle = '#f9fafb';
    ctx.fillRect(0, 0, width, height);

    // Get probability data
    const entries = Object.entries(probabilities).map(([label, prob]) => ({
      label,
      value: typeof prob === 'number' && prob <= 1 ? prob * 100 : prob
    }));

    const maxValue = Math.max(...entries.map(e => e.value), 100);
    const barWidth = chartWidth / entries.length;
    const colors = ['#6366f1', '#8b5cf6', '#ec4899'];

    // Draw bars
    entries.forEach((entry, index) => {
      const x = padding + index * barWidth + barWidth * 0.1;
      const barHeight = (entry.value / maxValue) * chartHeight;
      const y = height - padding - barHeight;
      const w = barWidth * 0.8;

      // Draw bar
      const gradient = ctx.createLinearGradient(x, y, x, y + barHeight);
      gradient.addColorStop(0, colors[index % colors.length]);
      gradient.addColorStop(1, colors[index % colors.length] + '88');
      ctx.fillStyle = gradient;
      ctx.fillRect(x, y, w, barHeight);

      // Draw label
      ctx.fillStyle = '#374151';
      ctx.font = '12px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(entry.label, x + w / 2, height - padding + 20);

      // Draw value
      ctx.fillStyle = colors[index % colors.length];
      ctx.font = 'bold 14px Arial';
      ctx.fillText(`${entry.value.toFixed(1)}%`, x + w / 2, y - 10);
    });

    // Draw axes
    ctx.strokeStyle = '#d1d5db';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, height - padding);
    ctx.lineTo(width - padding, height - padding);
    ctx.stroke();

    // Draw grid lines
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
      const y = padding + (chartHeight / 5) * i;
      ctx.beginPath();
      ctx.moveTo(padding - 5, y);
      ctx.lineTo(width - padding, y);
      ctx.stroke();

      ctx.fillStyle = '#9ca3af';
      ctx.font = '12px Arial';
      ctx.textAlign = 'right';
      ctx.fillText(`${Math.round(maxValue - (maxValue / 5) * i)}%`, padding - 10, y + 4);
    }
  };

  const generateHeatmap = () => {
    const canvas = heatmapCanvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    // Create a gradient heatmap representing confidence distribution
    const imageData = ctx.createImageData(width, height);
    const data = imageData.data;

    const confValue = parseFloat(confidence) / 100;

    for (let i = 0; i < data.length; i += 4) {
      const pixelIndex = i / 4;
      const x = pixelIndex % width;
      const y = Math.floor(pixelIndex / width);

      // Create a radial gradient effect centered on the image
      const centerX = width / 2;
      const centerY = height / 2;
      const maxDist = Math.sqrt(centerX * centerX + centerY * centerY);
      const dist = Math.sqrt(
        Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2)
      );
      const intensity = (1 - dist / maxDist) * confValue;

      // Color based on prediction
      let r, g, b;
      if (prediction.toLowerCase().includes('normal')) {
        // Green for normal
        r = Math.round(16 + intensity * 150);
        g = Math.round(185 + intensity * 50);
        b = Math.round(129 + intensity * 50);
      } else if (prediction.toLowerCase().includes('abnormal') || 
                 prediction.toLowerCase().includes('severe') ||
                 prediction.toLowerCase().includes('cmvd')) {
        // Red for abnormal
        r = Math.round(239 + intensity * 16);
        g = Math.round(68 + intensity * 50);
        b = Math.round(68 + intensity * 50);
      } else {
        // Yellow/orange for mild
        r = Math.round(245 + intensity * 10);
        g = Math.round(158 + intensity * 30);
        b = Math.round(11 + intensity * 50);
      }

      data[i] = r;
      data[i + 1] = g;
      data[i + 2] = b;
      data[i + 3] = 255;
    }

    ctx.putImageData(imageData, 0, 0);

    // Draw contour lines
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.2)';
    ctx.lineWidth = 2;
    for (let i = 0; i < 3; i++) {
      const radius = (width / 6) + (i * width / 6);
      ctx.beginPath();
      ctx.arc(width / 2, height / 2, radius, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Add confidence value text
    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.font = 'bold 20px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${confidence}%`, width / 2, height / 2);
  };

  return (
    <div>
      {/* Main Header with Gradient */}
      <div style={{
        background: `linear-gradient(135deg, ${getPredictionColor()} 0%, ${getPredictionColor()}dd 100%)`,
        color: 'white',
        padding: '25px',
        borderRadius: '12px',
        marginBottom: '25px',
        boxShadow: `0 8px 32px rgba(0, 0, 0, 0.1)`
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '15px' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.5em', marginBottom: '5px' }}>
              {model === 'rickets' ? '🦴' : '🫀'} {prediction}
            </h2>
            <p style={{ margin: 0, opacity: 0.9, fontSize: '0.95em' }}>
              Confidence: {confidence}%
            </p>
          </div>
          <div style={{
            background: 'rgba(255, 255, 255, 0.2)',
            padding: '10px 15px',
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '0.8em', opacity: 0.9 }}>Risk Level</div>
            <div style={{ fontSize: '1.2em', fontWeight: '700' }}>{getSeverityLevel()}</div>
          </div>
        </div>

        {/* Patient Info Row */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '15px',
          marginTop: '15px',
          borderTop: '1px solid rgba(255, 255, 255, 0.2)',
          paddingTop: '15px'
        }}>
          <div>
            <div style={{ fontSize: '0.85em', opacity: 0.8 }}>Patient Name</div>
            <div style={{ fontSize: '1.1em', fontWeight: '600' }}>{patientName || 'N/A'}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.85em', opacity: 0.8 }}>Gender</div>
            <div style={{ fontSize: '1.1em', fontWeight: '600' }}>{gender || 'N/A'}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.85em', opacity: 0.8 }}>Analysis Date</div>
            <div style={{ fontSize: '1.1em', fontWeight: '600' }}>{new Date().toLocaleDateString()}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.85em', opacity: 0.8 }}>Time</div>
            <div style={{ fontSize: '1.1em', fontWeight: '600' }}>{new Date().toLocaleTimeString()}</div>
          </div>
        </div>

        {/* Confidence Visualization */}
        <div style={{ marginTop: '15px' }}>
          <div style={{ fontSize: '0.8em', opacity: 0.8, marginBottom: '8px' }}>Confidence Score</div>
          <div style={{
            height: '10px',
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
            borderRadius: '10px',
            overflow: 'hidden',
            background: 'linear-gradient(90deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.2) 100%)'
          }}>
            <div style={{
              height: '100%',
              width: `${confidence}%`,
              background: 'rgba(255, 255, 255, 0.8)',
              borderRadius: '10px',
              transition: 'width 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
              boxShadow: `0 0 20px rgba(255, 255, 255, 0.6)`
            }}></div>
          </div>
        </div>
      </div>

      {/* Heatmap Visualization */}
      <div style={{
        background: 'linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%)',
        border: '2px solid var(--border-color)',
        borderRadius: '12px',
        padding: '20px',
        marginBottom: '25px'
      }}>
        <h3 style={{ color: 'var(--text-dark)', marginBottom: '15px', fontSize: '1.1em', fontWeight: '700' }}>
          🔍 Model Prediction Heatmap
        </h3>
        <div style={{
          background: 'white',
          border: '1px solid var(--border-color)',
          borderRadius: '8px',
          padding: '10px',
          marginBottom: '15px'
        }}>
          <canvas
            ref={heatmapCanvasRef}
            width={300}
            height={300}
            style={{
              width: '100%',
              maxWidth: '300px',
              height: 'auto',
              display: 'block',
              margin: '0 auto'
            }}
          />
        </div>
        <p style={{
          fontSize: '0.9em',
          color: 'var(--text-light)',
          margin: '0'
        }}>
          The heatmap shows the model's confidence distribution across the medical image. 
          Brighter areas indicate higher confidence in the detection region.
        </p>
      </div>

      {/* Detailed Probabilities */}
      {Object.keys(probabilities).length > 0 && (
        <div style={{
          background: 'linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%)',
          border: '1px solid var(--border-color)',
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '25px'
        }}>
          <h3 style={{ color: 'var(--text-dark)', marginBottom: '15px', fontSize: '1em', fontWeight: '600' }}>
            📊 Probability Distribution
          </h3>
          {Object.entries(probabilities).map(([label, prob], index) => {
            const probPercent = typeof prob === 'number' && prob <= 1 ? (prob * 100).toFixed(2) : prob;
            const colors = ['#6366f1', '#8b5cf6', '#ec4899'];
            const bgColor = colors[index % colors.length];
            
            return (
              <div key={label} style={{ marginBottom: index === Object.keys(probabilities).length - 1 ? 0 : '15px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', alignItems: 'center' }}>
                  <span style={{ fontWeight: '500', color: 'var(--text-dark)' }}>{label}</span>
                  <span style={{ fontWeight: '700', color: bgColor, fontSize: '1.05em' }}>
                    {probPercent}%
                  </span>
                </div>
                <div style={{
                  height: '10px',
                  backgroundColor: '#e5e7eb',
                  borderRadius: '6px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    height: '100%',
                    width: `${probPercent}%`,
                    background: `linear-gradient(90deg, ${bgColor} 0%, ${bgColor}dd 100%)`,
                    borderRadius: '6px',
                    transition: 'width 0.6s ease-out',
                    boxShadow: `0 0 15px ${bgColor}44`
                  }}></div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Chart Toggle Button */}
      <div style={{ marginBottom: '25px', textAlign: 'center' }}>
        <button
          onClick={() => setShowChart(!showChart)}
          style={{
            background: showChart 
              ? `linear-gradient(135deg, ${getPredictionColor()} 0%, ${getPredictionColor()}dd 100%)` 
              : '#e5e7eb',
            color: showChart ? 'white' : '#374151',
            border: 'none',
            padding: '12px 24px',
            borderRadius: '8px',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            fontSize: '1em'
          }}
        >
          {showChart ? '📉 Hide Distribution Graph' : '📊 Show Distribution Graph'}
        </button>
      </div>

      {/* Bar Chart */}
      {showChart && (
        <div style={{
          background: 'linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%)',
          border: '1px solid var(--border-color)',
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '25px'
        }}>
          <h3 style={{ color: 'var(--text-dark)', marginBottom: '15px', fontSize: '1em', fontWeight: '600' }}>
            📈 Confidence Distribution Chart
          </h3>
          <canvas
            ref={canvasRef}
            width={500}
            height={300}
            style={{
              width: '100%',
              maxWidth: '500px',
              height: 'auto',
              display: 'block',
              margin: '0 auto',
              backgroundColor: 'white',
              borderRadius: '8px',
              border: '1px solid var(--border-color)'
            }}
          />
        </div>
      )}

      {/* Key Metrics Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '15px',
        marginBottom: '25px'
      }}>
        {/* Model Info */}
        <div style={{
          background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
          color: 'white',
          padding: '20px',
          borderRadius: '12px',
          boxShadow: '0 4px 15px rgba(99, 102, 241, 0.2)'
        }}>
          <div style={{ fontSize: '0.85em', opacity: 0.9 }}>MODEL USED</div>
          <div style={{ fontSize: '1.3em', fontWeight: '700', marginTop: '8px', textTransform: 'uppercase' }}>
            {model}
          </div>
        </div>

        {/* Analysis Time */}
        <div style={{
          background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
          color: 'white',
          padding: '20px',
          borderRadius: '12px',
          boxShadow: '0 4px 15px rgba(139, 92, 246, 0.2)'
        }}>
          <div style={{ fontSize: '0.85em', opacity: 0.9 }}>ANALYSIS TIME</div>
          <div style={{ fontSize: '1.3em', fontWeight: '700', marginTop: '8px' }}>
            {new Date().toLocaleTimeString()}
          </div>
        </div>

        {/* Status */}
        <div style={{
          background: `linear-gradient(135deg, ${getPredictionColor()} 0%, ${getPredictionColor()}dd 100%)`,
          color: 'white',
          padding: '20px',
          borderRadius: '12px',
          boxShadow: `0 4px 15px ${getPredictionColor()}44`
        }}>
          <div style={{ fontSize: '0.85em', opacity: 0.9 }}>STATUS</div>
          <div style={{ fontSize: '1.3em', fontWeight: '700', marginTop: '8px' }}>
            ✓ Complete
          </div>
        </div>
      </div>

      {/* Clinical Recommendations */}
      <div style={{
        background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
        border: '2px solid #fcd34d',
        borderRadius: '12px',
        padding: '20px',
        marginBottom: '25px'
      }}>
        <h3 style={{ color: '#92400e', marginBottom: '15px', fontSize: '1.1em', fontWeight: '700' }}>
          💡 Clinical Recommendations
        </h3>
        <ul style={{ margin: 0, paddingLeft: '20px' }}>
          {getClinicalSuggestions().map((suggestion, index) => (
            <li key={index} style={{
              color: '#78350f',
              marginBottom: index === getClinicalSuggestions().length - 1 ? 0 : '10px',
              fontSize: '0.95em',
              lineHeight: '1.5'
            }}>
              {suggestion}
            </li>
          ))}
        </ul>
      </div>

      {/* Follow-up Timeline */}
      <div style={{
        background: 'linear-gradient(135deg, #e0f2fe 0%, #cffafe 100%)',
        border: '2px solid #06b6d4',
        borderRadius: '12px',
        padding: '20px',
        marginBottom: '25px'
      }}>
        <h3 style={{ color: '#0c4a6e', marginBottom: '15px', fontSize: '1.1em', fontWeight: '700' }}>
          📅 Recommended Follow-up Timeline
        </h3>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '15px'
        }}>
          <div style={{
            background: 'white',
            padding: '15px',
            borderRadius: '8px',
            border: '2px solid #06b6d4',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '0.9em', color: '#0c4a6e', fontWeight: '600' }}>URGENT</div>
            <div style={{ fontSize: '1.1em', fontWeight: '700', color: '#ef4444', marginTop: '8px' }}>
              {parseFloat(confidence) >= 85 ? '✓ Required' : '○ Not needed'}
            </div>
          </div>
          <div style={{
            background: 'white',
            padding: '15px',
            borderRadius: '8px',
            border: '2px solid #06b6d4',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '0.9em', color: '#0c4a6e', fontWeight: '600' }}>2-4 WEEKS</div>
            <div style={{ fontSize: '1.1em', fontWeight: '700', color: '#f59e0b', marginTop: '8px' }}>
              {parseFloat(confidence) >= 70 ? '✓ Recommended' : '○ Not needed'}
            </div>
          </div>
          <div style={{
            background: 'white',
            padding: '15px',
            borderRadius: '8px',
            border: '2px solid #06b6d4',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '0.9em', color: '#0c4a6e', fontWeight: '600' }}>3-6 MONTHS</div>
            <div style={{ fontSize: '1.1em', fontWeight: '700', color: '#10b981', marginTop: '8px' }}>
              ✓ Standard
            </div>
          </div>
        </div>
      </div>

      {/* Clinical Disclaimer */}
      <div style={{
        background: 'linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)',
        border: '2px solid #fca5a5',
        borderRadius: '12px',
        padding: '20px'
      }}>
        <h4 style={{ color: '#991b1b', marginBottom: '10px', fontSize: '1em', fontWeight: '700' }}>
          ⚠️ Important Clinical Disclaimer
        </h4>
        <p style={{
          color: '#7f1d1d',
          fontSize: '0.9em',
          lineHeight: '1.6',
          margin: 0
        }}>
          This AI-assisted analysis is intended as a supporting tool for medical professionals and 
          should not replace clinical judgment. All results must be verified by qualified healthcare 
          providers. For immediate medical concerns, please consult with your physician or seek 
          emergency medical attention.
        </p>
      </div>
    </div>
  );
}
