import React from 'react';
import { ShieldAlert, Cpu, Network, Layers } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-white border-t border-slate-200 py-6 px-4 text-xs text-slate-600 shadow-sm">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <ShieldAlert className="w-4 h-4 text-amber-600" />
          <p>
            <strong className="text-slate-800">CoastGuard Twin Simulation Platform</strong> — Research & Decision Support Architecture. Not certified for operational disaster response.
          </p>
        </div>

        <div className="flex items-center gap-6 text-[11px] text-slate-500">
          <span className="flex items-center gap-1 font-medium">
            <Layers className="w-3.5 h-3.5 text-cyan-600" /> Layer 1-5 Closed-Loop
          </span>
          <span className="flex items-center gap-1 font-medium">
            <Network className="w-3.5 h-3.5 text-cyan-600" /> PSO Mesh Swarm
          </span>
          <span className="flex items-center gap-1 font-medium">
            <Cpu className="w-3.5 h-3.5 text-cyan-600" /> WebXR Metaverse
          </span>
        </div>
      </div>
    </footer>
  );
};
