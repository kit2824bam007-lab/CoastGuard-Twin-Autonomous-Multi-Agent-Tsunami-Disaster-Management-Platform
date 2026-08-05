import React, { useState } from 'react';
import { Compass, ShieldCheck, AlertTriangle, ArrowUpRight, WifiOff, MapPin, CheckCircle2, Volume2, VolumeX, Camera } from 'lucide-react';
import { TelemetryPayload } from '../types';
import { Language, getTranslation } from '../i18n';

interface CivilianViewProps {
  telemetry: TelemetryPayload | null;
  language: Language;
  onLaunchAR: () => void;
}

export const CivilianView: React.FC<CivilianViewProps> = ({ telemetry, language, onLaunchAR }) => {
  const [speaking, setSpeaking] = useState<boolean>(false);
  const t = (key: string) => getTranslation(language, key);

  const classification = telemetry?.hazard_classification;
  const predictedClass = classification?.predicted_class || 'NO_THREAT';

  const isSevere = predictedClass === 'SEVERE';
  const isWarning = predictedClass === 'WARNING' || isSevere;
  const isWatch = predictedClass === 'WATCH' || isWarning;

  // Shelter details
  const shelter = {
    name: 'Highland Sanctuary Emergency Shelter',
    distanceKm: 2.4,
    headingLabel: 'North-East (NE)',
    safeElevationM: 85
  };

  const alertText = isSevere
    ? t('inland_order')
    : (isWatch ? t('watch_order') : t('safe_order'));

  // Text-to-Speech (TTS) Voice Alert Read-Out
  const handleToggleTTS = () => {
    if ('speechSynthesis' in window) {
      if (speaking) {
        window.speechSynthesis.cancel();
        setSpeaking(false);
      } else {
        const utterance = new SpeechSynthesisUtterance(alertText);
        utterance.onend = () => setSpeaking(false);
        utterance.onerror = () => setSpeaking(false);
        
        // Map language code to TTS voice
        const langMap: Record<Language, string> = {
          en: 'en-US',
          ta: 'ta-IN',
          hi: 'hi-IN',
          es: 'es-ES',
          id: 'id-ID'
        };
        utterance.lang = langMap[language] || 'en-US';

        window.speechSynthesis.speak(utterance);
        setSpeaking(true);
      }
    } else {
      alert("Text-to-Speech is not supported in this browser.");
    }
  };

  return (
    <div className="min-h-[calc(100vh-68px)] bg-slate-950 p-4 sm:p-6 md:p-8 flex items-center justify-center">
      <div className="w-full max-w-md space-y-6">
        
        {/* Offline PWA Cache Status Banner */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-3 flex items-center justify-between text-xs text-slate-300 shadow-md">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-cyan-950 border border-cyan-800 flex items-center justify-center shrink-0">
              <WifiOff className="w-4 h-4 text-cyan-400" />
            </div>
            <div>
              <div className="font-semibold text-white">Offline PWA Evacuation Mode</div>
              <div className="text-[11px] text-slate-400">Cached via Service Worker if cell tower drops.</div>
            </div>
          </div>
        </div>

        {/* Threat Level Status Header Card */}
        <div className={`p-6 rounded-3xl border text-center shadow-2xl transition-all ${
          isSevere
            ? 'bg-red-950/90 border-red-500 text-white shadow-red-600/30 animate-pulse'
            : (isWarning
              ? 'bg-orange-950/90 border-orange-500 text-white shadow-orange-600/20'
              : (isWatch
                ? 'bg-amber-950/80 border-amber-500 text-amber-200'
                : 'bg-emerald-950/80 border-emerald-500 text-emerald-200'))
        }`}>
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-black/30 mb-3 border border-white/10">
            {isSevere || isWarning ? (
              <AlertTriangle className="w-8 h-8 text-red-400 animate-bounce" />
            ) : (
              <ShieldCheck className="w-8 h-8 text-emerald-400" />
            )}
          </div>

          <div className="text-xs uppercase font-extrabold tracking-widest opacity-80">
            {t('threat_level')}
          </div>
          <h2 className="text-3xl font-black tracking-tight mt-1 mb-2">
            {predictedClass}
          </h2>

          <p className="text-xs leading-relaxed max-w-xs mx-auto opacity-90 mb-4">
            {alertText}
          </p>

          {/* Action Buttons: TTS Voice Alert & AR Camera Wayfinding */}
          <div className="flex items-center justify-center gap-2 pt-2 border-t border-white/10">
            <button
              onClick={handleToggleTTS}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-black/40 hover:bg-black/60 text-white text-xs font-bold transition border border-white/20"
            >
              {speaking ? <VolumeX className="w-4 h-4 text-red-400 animate-pulse" /> : <Volume2 className="w-4 h-4 text-cyan-400" />}
              {speaking ? t('stop_tts') : t('read_tts')}
            </button>

            <button
              onClick={onLaunchAR}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold transition shadow-lg shadow-cyan-500/20"
            >
              <Camera className="w-4 h-4" />
              {t('launch_ar')}
            </button>
          </div>
        </div>

        {/* Directional Shelter Compass Card */}
        <div className="glass-panel p-5 rounded-3xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <Compass className="w-4 h-4 text-cyan-400" /> {t('safe_compass')}
            </span>
            <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">
              +{shelter.safeElevationM}m Elevation
            </span>
          </div>

          <div className="flex items-center gap-4 bg-slate-900/90 p-4 rounded-2xl border border-slate-800">
            <div className="w-16 h-16 rounded-2xl bg-cyan-950/80 border border-cyan-500/40 flex items-center justify-center shrink-0 shadow-lg shadow-cyan-500/20">
              <ArrowUpRight className="w-8 h-8 text-cyan-400 animate-pulse" />
            </div>

            <div>
              <div className="text-xs text-slate-400">{t('nearest_shelter')}</div>
              <div className="text-base font-bold text-white leading-tight">{shelter.name}</div>
              <div className="text-xs font-semibold text-cyan-300 mt-1 flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5" /> {shelter.distanceKm} km {shelter.headingLabel}
              </div>
            </div>
          </div>
        </div>

        {/* Plain-Language Evacuation Instructions */}
        <div className="glass-panel p-5 rounded-3xl border border-slate-800 space-y-3">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Plain-Language Instructions
          </h3>

          <ul className="space-y-2.5 text-xs text-slate-300">
            <li className="flex items-start gap-2.5 bg-slate-900/60 p-2.5 rounded-xl border border-slate-800">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span><strong>Move Inland Immediately:</strong> Walk or run inland away from shoreline.</span>
            </li>
            <li className="flex items-start gap-2.5 bg-slate-900/60 p-2.5 rounded-xl border border-slate-800">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span><strong>Follow Swarm Beacons:</strong> Follow yellow ground-rover beacons toward safe shelters.</span>
            </li>
          </ul>
        </div>

      </div>
    </div>
  );
};
