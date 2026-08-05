import React from 'react';
import { ShieldAlert, Cpu, Network, Layers } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-slate-950 border-t border-slate-800/80 py-6 px-4 text-xs text-slate-400">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <ShieldAlert className="w-4 h-4 text-amber-400" />
          <p>
            <strong className="text-slate-300">CoastGuard Twin Simulation Platform</strong> — Research & Decision Support Architecture. Not certified for operational disaster response.
          </p>
        </div>

        <div className="flex items-center gap-6 text-[11px] text-slate-500">
          <span className="flex items-center gap-1">
            <Layers className="w-3.5 h-3.5 text-cyan-400" /> Layer 1-5 Closed-Loop
          </span>
          <span className="flex items-center gap-1">
            <Network className="w-3.5 h-3.5 text-cyan-400" /> PSO Mesh Swarm
          </span>
          <span className="flex items-center gap-1">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" /> WebXR Metaverse
          </span>
        </div>
      </div>
    </footer>
  );
};
