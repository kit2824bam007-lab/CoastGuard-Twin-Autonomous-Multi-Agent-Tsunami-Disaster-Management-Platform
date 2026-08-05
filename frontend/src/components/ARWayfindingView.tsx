import React, { useRef, useState, useEffect } from 'react';
import { Camera, Navigation, MapPin, X, ShieldCheck } from 'lucide-react';

interface ARWayfindingViewProps {
  onClose: () => void;
}

export const ARWayfindingView: React.FC<ARWayfindingViewProps> = ({ onClose }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [cameraActive, setCameraActive] = useState<boolean>(false);
  const [heading, setHeading] = useState<number>(45); // Target direction NE 45 degrees

  useEffect(() => {
    // Request device camera stream
    navigator.mediaDevices?.getUserMedia({ video: { facingMode: 'environment' } })
      .then(stream => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          setCameraActive(true);
        }
      })
      .catch(err => {
        console.warn("Camera stream access not available or denied:", err);
      });

    // Listen to device orientation compass heading if supported
    const handleOrientation = (e: DeviceOrientationEvent) => {
      if (e.alpha !== null) {
        setHeading(Math.round(e.alpha));
      }
    };

    window.addEventListener('deviceorientation', handleOrientation);
    return () => {
      window.removeEventListener('deviceorientation', handleOrientation);
      if (videoRef.current?.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream;
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  return (
    <div className="fixed inset-0 z-50 bg-black flex flex-col">
      {/* Real-time Phone Camera Video Stream */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="w-full h-full object-cover"
      />

      {/* Fallback pattern background if camera permission pending */}
      {!cameraActive && (
        <div className="absolute inset-0 bg-slate-950 flex flex-col items-center justify-center p-6 text-center">
          <Camera className="w-12 h-12 text-cyan-400 animate-pulse mb-3" />
          <h3 className="text-lg font-bold text-white">AR Wayfinding Camera Mode</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-xs">
            Connecting device environment camera. Point phone forward to see 3D directional overlay to shelter.
          </p>
        </div>
      )}

      {/* Top Header Bar */}
      <div className="absolute top-4 left-4 right-4 z-20 flex items-center justify-between">
        <div className="glass-panel px-3 py-1.5 rounded-xl border border-slate-700 flex items-center gap-2 text-xs font-bold text-cyan-300">
          <Navigation className="w-4 h-4 text-cyan-400 animate-spin" /> WebXR AR Wayfinding Active
        </div>

        <button
          onClick={onClose}
          className="w-10 h-10 rounded-full bg-slate-900/90 text-white flex items-center justify-center border border-slate-700 shadow-lg"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* AR HUD Overlay: 3D Directional Compass Arrow & Target Distance */}
      <div className="absolute inset-0 z-10 pointer-events-none flex flex-col items-center justify-center">
        {/* Animated AR Directional Target Ring */}
        <div className="relative w-64 h-64 border-2 border-cyan-400/40 rounded-full flex items-center justify-center animate-ping-slow">
          
          {/* Arrow pointing toward shelter heading */}
          <div
            className="w-24 h-24 flex items-center justify-center transition-transform duration-300"
            style={{ transform: `rotate(${heading}deg)` }}
          >
            <div className="w-0 h-0 border-l-[18px] border-l-transparent border-r-[18px] border-r-transparent border-b-[40px] border-b-cyan-400 drop-shadow-[0_0_15px_rgba(56,189,248,0.8)]" />
          </div>
        </div>

        {/* Floating AR Wayfinding Card */}
        <div className="mt-8 glass-panel-glow px-6 py-4 rounded-3xl border border-cyan-400/50 text-center space-y-1 shadow-2xl pointer-events-auto">
          <div className="text-[11px] font-bold text-cyan-400 uppercase tracking-widest flex items-center justify-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" /> Highland Sanctuary Shelter
          </div>
          <div className="text-2xl font-black text-white">2.4 km <span className="text-sm font-semibold text-cyan-300">NE (45°)</span></div>
          <div className="text-xs font-mono text-emerald-400">+85m Elevation Inland</div>
        </div>
      </div>
    </div>
  );
};
