import { useState, useRef, useCallback } from "react";

const MODEL_INFO = {
  cmvd: {
    title: "Upload ECG Image",
    desc: "Upload a 12-lead ECG strip or digital ECG image for CMVD analysis",
    accept: "image/png,image/jpeg,image/tiff",
    formats: "PNG · JPEG · TIFF",
    icon: "🫀",
  },
  rickets: {
    title: "Upload X-ray Image",
    desc: "Upload a pediatric wrist, knee, or chest X-ray for Rickets detection",
    accept: "image/png,image/jpeg,image/tiff",
    formats: "PNG · JPEG · TIFF",
    icon: "🦴",
  },
};

export default function ImageUpload({ onImageUpload, loading, activeModel }) {
  const [dragging, setDragging] = useState(false);
  const [preview, setPreview] = useState(null);
  const [fileName, setFileName] = useState(null);
  const inputRef = useRef(null);
  const info = MODEL_INFO[activeModel || 'rickets'];

  const handleFile = useCallback((file) => {
    if (!file || !file.type.startsWith("image/")) {
      alert("Please select a valid image file");
      return;
    }

    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(file);

    // Read as bytes for backend
    const bytesReader = new FileReader();
    bytesReader.onload = (e) => {
      onImageUpload(file, e.target.result);
    };
    bytesReader.readAsArrayBuffer(file);
  }, [onImageUpload]);

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  return (
    <div>
      <div className="image-upload-container"
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !loading && inputRef.current?.click()}
        style={{ 
          opacity: loading ? 0.6 : 1,
          cursor: loading ? 'not-allowed' : 'pointer'
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={info.accept}
          style={{ display: "none" }}
          onChange={(e) => handleFile(e.target.files[0])}
          disabled={loading}
        />

        {loading ? (
          <div className="text-center">
            <div className="spinner" style={{ margin: '0 auto 10px' }}></div>
            <p style={{ marginBottom: '5px', fontWeight: '500' }}>Analyzing image...</p>
            <small>Using {activeModel} detection model</small>
          </div>
        ) : preview ? (
          <div>
            <img src={preview} alt="Preview" className="image-preview" />
            <p style={{ marginTop: '10px', fontSize: '0.9em', color: 'var(--text-light)' }}>
              📁 {fileName}
            </p>
            <small style={{ color: 'var(--text-light)' }}>Click to upload different image</small>
          </div>
        ) : (
          <div style={{ textAlign: 'center' }}>
            <div className="image-upload-icon">{info.icon}</div>
            <p style={{ marginBottom: '5px' }}>
              Drag & drop image here or <strong>click to browse</strong>
            </p>
            <small style={{ color: 'var(--text-light)' }}>
              {info.formats} • Max 50MB
            </small>
          </div>
        )}
      </div>

      <div style={{ marginTop: '15px', fontSize: '0.85em', color: 'var(--text-light)' }}>
        <ul style={{ marginLeft: '20px', lineHeight: '1.8' }}>
          {activeModel === 'cmvd' ? (
            <>
              <li>✓ High-resolution ECG scans</li>
              <li>✓ All 12 leads must be visible</li>
              <li>✓ Clear, non-blurry images</li>
            </>
          ) : (
            <>
              <li>✓ Digital or scanned X-rays</li>
              <li>✓ Wrist or knee X-rays preferred</li>
              <li>✓ Proper positioning ensures accuracy</li>
            </>
          )}
        </ul>
      </div>
    </div>
  );
}
