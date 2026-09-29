import React, { useState, useRef, useEffect } from 'react';
import { Camera, RefreshCw, Check, X, AlertTriangle } from 'lucide-react';

export default function CameraCaptureModal({ isOpen, onClose, onCaptureConfirm }) {
  const [stream, setStream] = useState(null);
  const [capturedImages, setCapturedImages] = useState([]);
  const [cameraError, setCameraError] = useState(null);
  const [facingMode, setFacingMode] = useState('environment'); // Prefer rear camera on mobile

  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      startCamera();
    } else {
      stopCamera();
      setCapturedImages([]);
      setCameraError(null);
    }
    return () => {
      stopCamera();
    };
  }, [isOpen, facingMode]);

  const startCamera = async () => {
    setCameraError(null);
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Camera access is not supported in this browser context (requires HTTPS or localhost).');
      }

      const constraints = {
        video: {
          facingMode: facingMode,
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      };

      const mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err) {
      try {
        const fallbackStream = await navigator.mediaDevices.getUserMedia({ video: true });
        setStream(fallbackStream);
        if (videoRef.current) {
          videoRef.current.srcObject = fallbackStream;
        }
      } catch (fbErr) {
        setCameraError(err.message || 'Camera permission denied or camera device unavailable.');
      }
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
  };

  const handleTakeSnapshot = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], `camera_capture_page_${capturedImages.length + 1}.jpg`, { type: 'image/jpeg' });
        const previewUrl = URL.createObjectURL(blob);
        setCapturedImages((prev) => [...prev, { file, previewUrl }]);
      }
    }, 'image/jpeg', 0.92);
  };

  const handleRetakeLast = () => {
    if (capturedImages.length === 0) return;
    const last = capturedImages[capturedImages.length - 1];
    URL.revokeObjectURL(last.previewUrl);
    setCapturedImages((prev) => prev.slice(0, -1));
  };

  const handleConfirmAllCaptures = () => {
    if (capturedImages.length === 0) return;
    const files = capturedImages.map((item) => item.file);
    onCaptureConfirm(files);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(15, 23, 42, 0.85)',
      backdropFilter: 'blur(8px)',
      zIndex: 9999,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div className="glass-card" style={{
        maxWidth: '700px',
        width: '100%',
        maxHeight: '90vh',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        padding: '24px'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Camera size={22} style={{ color: 'var(--accent-cyan)' }} />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
              Camera Medical Report Capture
            </h2>
          </div>
          <button onClick={onClose} className="btn-icon" style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {/* Video / Error Area */}
        <div style={{
          position: 'relative',
          width: '100%',
          height: '340px',
          background: '#090d16',
          borderRadius: '12px',
          overflow: 'hidden',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          {cameraError ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--accent-rose)' }}>
              <AlertTriangle size={36} style={{ marginBottom: '12px' }} />
              <p style={{ fontSize: '0.95rem', fontWeight: 600, margin: '0 0 12px 0' }}>{cameraError}</p>
              <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', margin: '0 0 16px 0' }}>
                Please check browser permissions or switch to the standard File Upload option.
              </p>
              <button className="btn btn-outline" onClick={onClose}>
                Use File Upload Instead
              </button>
            </div>
          ) : (
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          )}
          <canvas ref={canvasRef} style={{ display: 'none' }} />
        </div>

        {/* Captured Pages Previews Strip */}
        {capturedImages.length > 0 && (
          <div style={{ marginTop: '16px' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '8px' }}>
              Captured Pages ({capturedImages.length}):
            </div>
            <div style={{ display: 'flex', gap: '10px', overflowX: 'auto', paddingBottom: '6px' }}>
              {capturedImages.map((img, idx) => (
                <div key={idx} style={{ position: 'relative', width: '70px', height: '90px', borderRadius: '6px', overflow: 'hidden', border: '1px solid var(--accent-cyan)' }}>
                  <img src={img.previewUrl} alt={`Page ${idx + 1}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  <span style={{ position: 'absolute', bottom: '2px', right: '4px', fontSize: '0.65rem', background: 'rgba(0,0,0,0.7)', color: '#fff', padding: '1px 4px', borderRadius: '4px' }}>
                    P{idx + 1}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Controls */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '20px', gap: '12px', flexWrap: 'wrap' }}>
          {!cameraError && (
            <div style={{ display: 'flex', gap: '8px' }}>
              <button className="btn btn-primary" onClick={handleTakeSnapshot}>
                <Camera size={16} style={{ marginRight: '6px' }} />
                Capture Page {capturedImages.length + 1}
              </button>
              {capturedImages.length > 0 && (
                <button className="btn btn-outline" onClick={handleRetakeLast}>
                  <RefreshCw size={16} style={{ marginRight: '6px' }} />
                  Retake Last
                </button>
              )}
            </div>
          )}

          <div style={{ display: 'flex', gap: '8px', marginLeft: 'auto' }}>
            <button className="btn btn-outline" onClick={onClose}>
              Cancel
            </button>
            {capturedImages.length > 0 && (
              <button className="btn btn-primary" onClick={handleConfirmAllCaptures}>
                <Check size={16} style={{ marginRight: '6px' }} />
                Confirm {capturedImages.length} Page(s)
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
