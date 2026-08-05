import React, { useState, useEffect } from 'react';
import { Play, Pause, SkipBack, RotateCcw, Film } from 'lucide-react';

export const ReplayControlPanel: React.FC = () => {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentFrame, setCurrentFrame] = useState<number>(0);
  const [timeline, setTimeline] = useState<any[]>([]);

  useEffect(() => {
    fetch('/api/replay/timeline/SESSION-M7.8-DEMO')
      .then(res => res.json())
      .then(data => {
        if (data.frames) setTimeline(data.frames);
      })
      .catch(e => console.error("Error loading replay timeline:", e));
  }, []);

  useEffect(() => {
    let timer: any = null;
    if (isPlaying) {
      timer = setInterval(() => {
        setCurrentFrame(prev => {
          if (prev >= timeline.length - 1) {
            setIsPlaying(false);
            return 0;
          }
          return prev + 1;
        });
      }, 1000);
    }
    return () => { if (timer) clearInterval(timer); };
  }, [isPlaying, timeline.length]);

  const frameData = timeline[currentFrame] || {};

  return (
    <div className="glass-panel p-4 rounded-2xl border border-slate-800 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
          <Film className="w-4 h-4 text-cyan-400" /> Responder Training Replay Control (Session M7.8)
        </span>
        <span className="text-xs font-mono text-cyan-300">
          Frame: {currentFrame + 1} / {timeline.length || 30} ({frameData.timestamp_rel_sec || 0}s)
        </span>
      </div>

      {/* Scrub Slider */}
      <div className="space-y-1">
        <input
          type="range"
          min={0}
          max={Math.max(0, timeline.length - 1)}
          value={currentFrame}
          onChange={(e) => setCurrentFrame(parseInt(e.target.value))}
          className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
        />
        <div className="flex justify-between text-[10px] text-slate-500 font-mono">
          <span>0s (Quake Onset)</span>
          <span>15s (Wave Surge)</span>
          <span>30s (Evacuation Complete)</span>
        </div>
      </div>

      {/* Timeline Frame Data Cards */}
      <div className="grid grid-cols-4 gap-2 text-xs">
        <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
          <div className="text-[10px] text-slate-400">Hazard Class</div>
          <div className="font-bold text-amber-400 font-mono">{frameData.hazard_class || 'NO_THREAT'}</div>
        </div>
        <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
          <div className="text-[10px] text-slate-400">Buoy Anomaly</div>
          <div className="font-bold text-cyan-300 font-mono">{frameData.buoy_sea_level_anomaly_m || 0.05}m</div>
        </div>
        <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
          <div className="text-[10px] text-slate-400">Shore State</div>
          <div className="font-bold text-slate-200 font-mono">{frameData.shoreline_state || 'NORMAL'}</div>
        </div>
        <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
          <div className="text-[10px] text-slate-400">Active Swarm</div>
          <div className="font-bold text-emerald-400 font-mono">{frameData.active_swarm_count || 9} Agents</div>
        </div>
      </div>

      {/* Play Controls */}
      <div className="flex items-center gap-2 pt-1">
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs transition"
        >
          {isPlaying ? <Pause className="w-3.5 h-3.5 fill-current" /> : <Play className="w-3.5 h-3.5 fill-current" />}
          {isPlaying ? 'Pause Replay' : 'Play Timeline'}
        </button>

        <button
          onClick={() => { setIsPlaying(false); setCurrentFrame(0); }}
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition"
        >
          <RotateCcw className="w-3.5 h-3.5" /> Reset
        </button>
      </div>
    </div>
  );
};
