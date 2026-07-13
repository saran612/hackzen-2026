import React, { useRef, useState, useEffect, useCallback } from "react";
import { Camera, Upload, RefreshCw, AlertCircle, AlertTriangle } from "lucide-react";

export default function FaceAnalyzer({
  onAnalysisComplete,
  isAnalyzing,
  setIsAnalyzing,
  apiBase,
  compact = false,
  onReset,
  initialImage = null,
  initialRegions = null
}) {
  const [selectedImage, setSelectedImage] = useState(null);
  const [useWebcam, setUseWebcam] = useState(false);
  const [isMockCamera, setIsMockCamera] = useState(false);
  const [error, setError] = useState(null);
  const [regions, setRegions] = useState(null);
  const [hoveredRegion, setHoveredRegion] = useState(null);
  const [qualityWarnings, setQualityWarnings] = useState([]);

  useEffect(() => {
    if (initialImage) {
      setSelectedImage(initialImage);
    } else {
      setSelectedImage(null);
    }
  }, [initialImage]);

  useEffect(() => {
    if (initialRegions) {
      setRegions(initialRegions);
    } else {
      setRegions(null);
    }
  }, [initialRegions]);

  const videoElRef = useRef(null);
  const canvasRef = useRef(null);
  const imageRef = useRef(null);
  const streamRef = useRef(null);

  // Instantly bind the stream to the video node when it mounts in the DOM
  const videoRef = useCallback((node) => {
    videoElRef.current = node;
    if (node && streamRef.current && !isMockCamera) {
      node.srcObject = streamRef.current;
    }
  }, [isMockCamera]);

  // Stop webcam stream when component unmounts or mode changes
  useEffect(() => {
    return () => {
      stopWebcam();
    };
  }, []);

  const stopWebcam = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  };

  const startWebcam = async () => {
    setError(null);
    setSelectedImage(null);
    setRegions(null);
    setIsMockCamera(false);
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("mediaDevices not supported or not in secure context (HTTPS)");
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: "user" }
      });
      streamRef.current = stream;
      setUseWebcam(true);
    } catch (err) {
      console.warn("Real webcam failed, activating simulated camera: ", err);
      setUseWebcam(true);
      setIsMockCamera(true);
    }
  };

  const capturePhoto = async () => {
    if (isMockCamera) {
      try {
        const response = await fetch("/face_placeholder.png");
        const blob = await response.blob();
        const file = new File([blob], "simulated_capture.png", { type: "image/png" });
        const url = URL.createObjectURL(blob);
        setSelectedImage(url);
        setUseWebcam(false);
        setIsMockCamera(false);
        handleUpload(file);
      } catch (err) {
        console.error(err);
        setError("Failed to initialize simulated camera capture.");
      }
      return;
    }

    if (videoElRef.current) {
      const video = videoElRef.current;
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      const ctx = canvas.getContext("2d");
      // Draw mirror image for natural feel
      ctx.translate(canvas.width, 0);
      ctx.scale(-1, 1);
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      ctx.setTransform(1, 0, 0, 1, 0, 0); // reset scale

      canvas.toBlob((blob) => {
        const file = new File([blob], "webcam_capture.jpg", { type: "image/jpeg" });
        const url = URL.createObjectURL(blob);
        setSelectedImage(url);
        stopWebcam();
        setUseWebcam(false);
        handleUpload(file);
      }, "image/jpeg");
    }
  };

  const handleFileChange = (e) => {
    setError(null);
    setRegions(null);
    const file = e.target.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setSelectedImage(url);
      setUseWebcam(false);
      stopWebcam();
      handleUpload(file);
    }
  };

  const handleUpload = async (file) => {
    setIsAnalyzing(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);
    
    // Store unique session ID in localStorage
    let sessionId = localStorage.getItem("skincv_session_id");
    if (!sessionId) {
      sessionId = crypto.randomUUID();
      localStorage.setItem("skincv_session_id", sessionId);
    }
    formData.append("session_id", sessionId);

    try {
      const response = await fetch(`${apiBase}/api/analyze`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Analysis failed");
      }

      const result = await response.json();
      setRegions(result.regions);
      setQualityWarnings(result.warnings || []);
      onAnalysisComplete(result);
    } catch (err) {
      console.error(err);
      setError(err.message || "Something went wrong during skin analysis.");
      setQualityWarnings([]);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Render heatmap overlay when regions are present and image loads
  const drawOverlay = () => {
    if (!regions || !canvasRef.current || !imageRef.current) return;
    const canvas = canvasRef.current;
    const img = imageRef.current;
    
    // Set canvas dimensions equal to display image size
    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;
    
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Calculate scale factor from original image resolution to displayed dimensions
    const scaleX = img.clientWidth / img.naturalWidth;
    const scaleY = img.clientHeight / img.naturalHeight;

    // Draw region highlights
    Object.entries(regions).forEach(([name, poly]) => {
      ctx.beginPath();
      poly.forEach((pt, idx) => {
        const x = pt[0] * scaleX;
        const y = pt[1] * scaleY;
        if (idx === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.closePath();

      // Soft coloring for gender-neutral skin mapping
      const isHovered = name === hoveredRegion;
      ctx.fillStyle = isHovered ? "rgba(16, 185, 129, 0.25)" : "rgba(16, 185, 129, 0.08)";
      ctx.strokeStyle = isHovered ? "rgba(16, 185, 129, 0.8)" : "rgba(16, 185, 129, 0.4)";
      ctx.lineWidth = isHovered ? 2 : 1;
      ctx.fill();
      ctx.stroke();
    });
  };

  // Redraw overlay when window resizes or hovered region changes
  useEffect(() => {
    drawOverlay();
    window.addEventListener("resize", drawOverlay);
    return () => window.removeEventListener("resize", drawOverlay);
  }, [regions, hoveredRegion, selectedImage]);

  const handleMouseMove = (e) => {
    if (!regions || !canvasRef.current || !imageRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const img = imageRef.current;
    const scaleX = img.clientWidth / img.naturalWidth;
    const scaleY = img.clientHeight / img.naturalHeight;

    let foundRegion = null;
    // Simple point-in-polygon helper
    Object.entries(regions).forEach(([name, poly]) => {
      let inside = false;
      for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
        const xi = poly[i][0] * scaleX, yi = poly[i][1] * scaleY;
        const xj = poly[j][0] * scaleX, yj = poly[j][1] * scaleY;
        const intersect = ((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
        if (intersect) inside = !inside;
      }
      if (inside) {
        foundRegion = name;
      }
    });
    setHoveredRegion(foundRegion);
  };

  return (
    <div className={`flex flex-col items-center justify-center w-full bg-slate-900/60 backdrop-blur-md rounded-2xl border border-slate-800 ${compact ? "p-4" : "max-w-xl p-6"}`}>
      {!compact && (
        <>
          <h2 className="text-xl font-semibold text-slate-100 mb-2">Facial Skin Scan</h2>
          <p className="text-sm text-slate-400 text-center mb-6">
            Take a picture or upload a clear, front-facing portrait to analyze skin concerns.
          </p>
        </>
      )}

      {error && (
        <div className="flex items-center gap-3 w-full p-4 mb-4 bg-red-950/40 border border-red-900/50 rounded-xl text-red-300 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main View Area */}
      <div className={`relative bg-slate-950 rounded-xl overflow-hidden border border-slate-850 flex items-center justify-center ${compact ? "w-full max-w-[280px] aspect-square mx-auto" : "w-full aspect-square md:w-[480px] md:h-[480px]"}`}>
        {isAnalyzing && (
          <div className="absolute inset-0 z-20 bg-slate-950/80 flex flex-col items-center justify-center gap-4">
            <RefreshCw className="w-12 h-12 text-emerald-500 animate-spin" />
            <p className="text-slate-200 text-sm font-medium animate-pulse">Analyzing skin zones...</p>
          </div>
        )}

        {useWebcam ? (
          <div className="relative w-full h-full">
            {isMockCamera ? (
              <div className="relative w-full h-full">
                <img
                  src="/face_placeholder.png"
                  alt="Simulated Camera Feed"
                  className="w-full h-full object-cover opacity-80"
                />
                <div className="absolute top-4 right-4 bg-amber-500/90 text-slate-950 font-bold border border-amber-400 px-3 py-1 rounded text-[10px] uppercase tracking-wider animate-pulse z-20">
                  Simulated Feed
                </div>
                {/* Scanner laser sweep animation */}
                <div className="absolute inset-x-0 h-0.5 bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] animate-[bounce_3s_infinite] top-1/4 z-10" />
              </div>
            ) : (
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover scale-x-[-1]"
              />
            )}
            <button
              onClick={capturePhoto}
              className="absolute bottom-6 left-1/2 -translate-x-1/2 px-6 py-3 bg-emerald-500 hover:bg-emerald-600 active:scale-95 text-slate-950 font-semibold rounded-full shadow-lg transition duration-200 flex items-center gap-2 z-20"
            >
              <Camera className="w-5 h-5" />
              Capture Face
            </button>
          </div>
        ) : selectedImage ? (
          <div className="relative w-full h-full flex items-center justify-center group">
            {/* Quality warnings overlay */}
            {qualityWarnings.length > 0 && !compact && (
              <div className="absolute top-2 left-2 right-2 z-20 bg-amber-950/80 backdrop-blur-sm border border-amber-800/50 rounded-lg p-2.5 flex flex-col gap-1">
                <div className="flex items-center gap-1.5 text-amber-400 text-[10px] font-bold uppercase tracking-wider">
                  <AlertTriangle className="w-3 h-3" />
                  Quality Notice
                </div>
                {qualityWarnings.slice(0, 2).map((w, i) => (
                  <p key={i} className="text-[10px] text-amber-300/70 leading-relaxed pl-4">{w}</p>
                ))}
              </div>
            )}
            <img
              ref={imageRef}
              src={selectedImage}
              alt="Scan Target"
              className="w-full h-full object-cover"
              onLoad={drawOverlay}
            />
            {regions && (
              <canvas
                ref={canvasRef}
                onMouseMove={handleMouseMove}
                onMouseLeave={() => setHoveredRegion(null)}
                className="absolute inset-0 cursor-crosshair z-10"
              />
            )}
            {hoveredRegion && (
              <div className="absolute top-4 left-4 bg-slate-900/90 text-emerald-400 font-semibold border border-emerald-500/20 px-3 py-1.5 rounded-lg text-xs capitalize z-20">
                Zone: {hoveredRegion.replace(/_/g, " ")}
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center gap-6 p-10 text-center w-full h-full">
            <div className="w-16 h-16 bg-slate-900 rounded-full border border-slate-800 flex items-center justify-center text-slate-400">
              <Upload className="w-8 h-8" />
            </div>
            <div className="flex flex-col md:flex-row gap-4 w-full px-6">
              <label className="flex-1 flex items-center justify-center gap-2 px-5 py-3 border border-slate-700 hover:bg-slate-900 active:scale-95 rounded-xl cursor-pointer text-slate-200 text-sm font-medium transition duration-200">
                <Upload className="w-4 h-4" />
                Upload Photo
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>
              <button
                onClick={startWebcam}
                className="flex-1 flex items-center justify-center gap-2 px-5 py-3 bg-emerald-500 hover:bg-emerald-600 active:scale-95 text-slate-950 font-semibold rounded-xl transition duration-200 text-sm"
              >
                <Camera className="w-4 h-4" />
                Use Camera
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Mode Switches */}
      {(selectedImage || useWebcam) && !isAnalyzing && (
        <div className="flex gap-4 mt-6">
          <button
            onClick={() => {
              setSelectedImage(null);
              setUseWebcam(false);
              stopWebcam();
              setRegions(null);
              if (onReset) onReset();
            }}
            className="px-4 py-2 border border-slate-700 hover:bg-slate-900 text-slate-300 rounded-lg text-xs font-semibold transition"
          >
            Reset Scanner
          </button>
          {!useWebcam && !compact && (
            <button
              onClick={startWebcam}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold transition flex items-center gap-1.5"
            >
              <Camera className="w-3.5 h-3.5" />
              Retake with Camera
            </button>
          )}
        </div>
      )}
    </div>
  );
}
