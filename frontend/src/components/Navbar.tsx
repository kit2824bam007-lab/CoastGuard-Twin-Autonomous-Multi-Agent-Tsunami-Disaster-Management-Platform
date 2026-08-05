import React from 'react';
import { ShieldAlert, Activity, Users, BarChart3, Radio, Play, RotateCcw, ShieldCheck, Network, Globe, UserCheck, Satellite, Eye } from 'lucide-react';
import { ViewMode, UserRole, DataMode } from '../types';
import { Language, getTranslation } from '../i18n';

interface NavbarProps {
  activeView: ViewMode;
  setActiveView: (view: ViewMode) => void;
  userRole: UserRole;
  setUserRole: (role: UserRole) => void;
  dataMode: DataMode;
  onToggleDataMode: () => void;
  language: Language;
  setLanguage: (lang: Language) => void;
  highContrast: boolean;
  setHighContrast: (contrast: boolean) => void;
  isSatelliteActive: boolean;
  onToggleSatellite: () => void;
  isConnected: boolean;
  isEventActive: boolean;
  onTriggerEvent: (magnitude: number, distanceKm: number) => void;
  onReset: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeView,
  setActiveView,
  userRole,
  setUserRole,
  dataMode,
  onToggleDataMode,
  language,
  setLanguage,
  highContrast,
  setHighContrast,
  isSatelliteActive,
  onToggleSatellite,
  isConnected,
  isEventActive,
  onTriggerEvent,
  onReset,
}) => {
  const t = (key: string) => getTranslation(language, key);

  return (
    <header className={`w-full border-b sticky top-0 z-50 transition-all ${
      highContrast ? 'bg-black border-yellow-400 text-yellow-300' : 'bg-slate-900/95 backdrop-blur-md border-slate-800 text-slate-100'
    }`}>
      {/* Simulation Banner Notice */}
      <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-1 text-center text-xs font-medium text-amber-300 flex items-center justify-center gap-2">
        <ShieldAlert className="w-3.5 h-3.5 animate-pulse text-amber-400" />
        <span>{t('sim_notice')}</span>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-2 overflow-x-auto">
        {/* Brand Logo & Name */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Radio className="w-5 h-5 text-white animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white">{t('brand_title')}</h1>
              <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                v2.0 Real-World
              </span>
            </div>
            <p className="text-xs text-slate-400">Autonomous Digital Twin & Swarm Intelligence</p>
          </div>
        </div>

        {/* View Mode Switcher Tabs (Role Filtered) */}
        <nav className="hidden lg:flex items-center gap-1 bg-slate-950/60 p-1.5 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveView('COMMAND_CENTER')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeView === 'COMMAND_CENTER' ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            {t('nav_3d')}
          </button>

          <button
            onClick={() => setActiveView('CIVILIAN')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeView === 'CIVILIAN' ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            {t('nav_civilian')}
          </button>

          <button
            onClick={() => setActiveView('METRICS')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeView === 'METRICS' ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            {t('nav_metrics')}
          </button>

          {userRole !== 'RESPONDER' && (
            <button
              onClick={() => setActiveView('AUTHORITY')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeView === 'AUTHORITY' ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              CAP Handoff
            </button>
          )}

          {userRole === 'ADMIN' && (
            <button
              onClick={() => setActiveView('FEDERATED')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeView === 'FEDERATED' ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Network className="w-3.5 h-3.5" />
              FL Twins
            </button>
          )}
        </nav>

        {/* Controls Bar: Data Mode, Role, Language, Satellite, High Contrast */}
        <div className="flex items-center gap-2 shrink-0">
          {/* Data Mode Toggle */}
          <button
            onClick={onToggleDataMode}
            title="Toggle between Simulated Data and USGS/NOAA Live Public Feeds"
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-bold border transition ${
              dataMode === 'LIVE_PUBLIC_FEEDS'
                ? 'bg-emerald-950 text-emerald-300 border-emerald-700 animate-pulse'
                : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            {dataMode === 'LIVE_PUBLIC_FEEDS' ? 'USGS Live Feeds' : 'Simulated Data'}
          </button>

          {/* Satellite Comms Failover Trigger */}
          <button
            onClick={onToggleSatellite}
            title="Simulate Terrestrial Damage & Failover to LEO Satellite Comms"
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-bold border transition ${
              isSatelliteActive
                ? 'bg-amber-950 text-amber-300 border-amber-600 animate-pulse'
                : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
          >
            <Satellite className="w-3.5 h-3.5 text-amber-400" />
            {isSatelliteActive ? 'LEO Sat Active' : 'Terrestrial Mesh'}
          </button>

          {/* Role Selector */}
          <select
            value={userRole}
            onChange={(e) => setUserRole(e.target.value as UserRole)}
            className="bg-slate-950 border border-slate-800 text-slate-300 text-[11px] font-semibold rounded-lg px-2 py-1 focus:outline-none"
          >
            <option value="OPERATOR">Operator Mode</option>
            <option value="RESPONDER">Field Responder</option>
            <option value="AUTHORITY_VIEWER">Authority Viewer</option>
            <option value="ADMIN">System Admin</option>
          </select>

          {/* Language Selector */}
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value as Language)}
            className="bg-slate-950 border border-slate-800 text-slate-300 text-[11px] font-bold rounded-lg px-2 py-1 focus:outline-none"
          >
            <option value="en">English (EN)</option>
            <option value="ta">தமிழ் (TA)</option>
            <option value="hi">हिंदी (HI)</option>
            <option value="es">Español (ES)</option>
            <option value="id">Bahasa (ID)</option>
          </select>

          {/* High Contrast Toggle */}
          <button
            onClick={() => setHighContrast(!highContrast)}
            title="Toggle High Contrast Mode"
            className="p-1 rounded-lg bg-slate-950 border border-slate-800 text-slate-400 hover:text-slate-200"
          >
            <Eye className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </header>
  );
};
