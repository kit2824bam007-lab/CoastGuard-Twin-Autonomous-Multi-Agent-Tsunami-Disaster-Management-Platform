import React, { useState, useEffect, useRef } from 'react';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { CommandCenter3D } from './components/CommandCenter3D';
import { CivilianView } from './components/CivilianView';
import { AdminMetricsView } from './components/AdminMetricsView';
import { AuthorityBridgeView } from './components/AuthorityBridgeView';
import { FederatedLearningView } from './components/FederatedLearningView';
import { ARWayfindingView } from './components/ARWayfindingView';
import { ReplayControlPanel } from './components/ReplayControlPanel';
import { ViewMode, UserRole, DataMode, TelemetryPayload } from './types';
import { Language } from './i18n';

export const App: React.FC = () => {
  const [activeView, setActiveView] = useState<ViewMode>('COMMAND_CENTER');
  const [userRole, setUserRole] = useState<UserRole>('OPERATOR');
  const [dataMode, setDataMode] = useState<DataMode>('SIMULATED');
  const [language, setLanguage] = useState<Language>('en');
  const [highContrast, setHighContrast] = useState<boolean>(false);
  const [isSatelliteActive, setIsSatelliteActive] = useState<boolean>(false);
  const [showARCamera, setShowARCamera] = useState<boolean>(false);

  const [telemetry, setTelemetry] = useState<TelemetryPayload | null>(null);
  const [bathymetryGrid, setBathymetryGrid] = useState<number[][] | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);

  const wsRef = useRef<WebSocket | null>(null);

  // Fetch static bathymetry grid once on mount
  useEffect(() => {
    fetch('/api/sensors/bathymetry')
      .then(res => res.json())
      .then(data => {
        if (data.grid) setBathymetryGrid(data.grid);
      })
      .catch(err => console.error("Error loading bathymetry grid:", err));
  }, []);

  // WebSocket telemetry streaming with fallback polling
  useEffect(() => {
    let ws: WebSocket | null = null;
    let pollInterval: any = null;

    const connectWebSocket = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;

      ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        if (pollInterval) clearInterval(pollInterval);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'TELEMETRY_UPDATE') {
            setTelemetry(data);
            if (data.swarm?.topology?.is_satellite_failover_active !== undefined) {
              setIsSatelliteActive(data.swarm.topology.is_satellite_failover_active);
            }
          }
        } catch (e) {
          console.error("Error parsing telemetry message:", e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        startPollingFallback();
        setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = () => { ws?.close(); };
    };

    const startPollingFallback = () => {
      if (pollInterval) return;
      pollInterval = setInterval(async () => {
        try {
          const [resSensors, resTwin, resSwarm, resAlerts] = await Promise.all([
            fetch('/api/sensors/snapshot'),
            fetch('/api/twin/state'),
            fetch('/api/swarm/topology'),
            fetch('/api/alerts/severity')
          ]);

          const sData = await resSensors.json();
          const tData = await resTwin.json();
          const swData = await resSwarm.json();
          const aData = await resAlerts.json();

          setTelemetry({
            type: 'TELEMETRY_UPDATE',
            timestamp: sData.timestamp,
            is_event_active: sData.is_event_active,
            sensors: sData.sensors,
            seismic_history: sData.history.seismic,
            buoy_history: sData.history.buoy,
            twin_summary: tData.summary,
            swarm: {
              agents: swData.nodes || [],
              topology: swData
            },
            hazard_classification: aData.classification
          });
          setIsConnected(true);
        } catch (e) {
          setIsConnected(false);
        }
      }, 1500);
    };

    connectWebSocket();

    return () => {
      if (ws) ws.close();
      if (pollInterval) clearInterval(pollInterval);
    };
  }, []);

  // Action Handlers
  const handleTriggerEvent = async (magnitude: number, distanceKm: number) => {
    try {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: 'TRIGGER_EVENT', magnitude, distance_km: distanceKm }));
      } else {
        await fetch('/api/sensors/trigger-event', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ magnitude, distance_km: distanceKm })
        });
      }
    } catch (e) {
      console.error("Error triggering event:", e);
    }
  };

  const handleResetSimulation = async () => {
    try {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: 'RESET' }));
      } else {
        await fetch('/api/sensors/reset', { method: 'POST' });
      }
    } catch (e) {
      console.error("Error resetting simulation:", e);
    }
  };

  const handleToggleDataMode = async () => {
    const nextMode = dataMode === 'SIMULATED' ? 'LIVE_PUBLIC_FEEDS' : 'SIMULATED';
    try {
      await fetch('/api/live-data/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: nextMode })
      });
      setDataMode(nextMode);
    } catch (e) {
      console.error("Error toggling data mode:", e);
    }
  };

  const handleToggleSatellite = async () => {
    try {
      const res = await fetch('/api/swarm/toggle-satellite', { method: 'POST' });
      const data = await res.json();
      setIsSatelliteActive(data.is_satellite_failover_active);
    } catch (e) {
      console.error("Error toggling satellite failover:", e);
    }
  };

  const handleDeployAgent = async (type: 'UAV' | 'USV' | 'GROUND', x: number, y: number) => {
    try {
      await fetch('/api/swarm/deploy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_type: type, x, y })
      });
    } catch (e) {
      console.error("Error deploying agent:", e);
    }
  };

  const handleSimulateLoss = async (agentId: string) => {
    try {
      await fetch('/api/swarm/simulate-loss', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: agentId })
      });
    } catch (e) {
      console.error("Error simulating agent loss:", e);
    }
  };

  const isEventActive = telemetry?.is_event_active || false;

  return (
    <div className={`min-h-screen flex flex-col font-sans transition-colors ${
      highContrast ? 'bg-black text-yellow-300' : 'bg-slate-950 text-slate-100'
    }`}>
      <Navbar
        activeView={activeView}
        setActiveView={setActiveView}
        userRole={userRole}
        setUserRole={setUserRole}
        dataMode={dataMode}
        onToggleDataMode={handleToggleDataMode}
        language={language}
        setLanguage={setLanguage}
        highContrast={highContrast}
        setHighContrast={setHighContrast}
        isSatelliteActive={isSatelliteActive}
        onToggleSatellite={handleToggleSatellite}
        isConnected={isConnected}
        isEventActive={isEventActive}
        onTriggerEvent={handleTriggerEvent}
        onReset={handleResetSimulation}
      />

      <main className="flex-1 relative">
        {activeView === 'COMMAND_CENTER' && (
          <div className="flex flex-col">
            <CommandCenter3D
              telemetry={telemetry}
              bathymetryGrid={bathymetryGrid}
              onTriggerEvent={handleTriggerEvent}
              onDeployAgent={handleDeployAgent}
              onSimulateLoss={handleSimulateLoss}
              onReset={handleResetSimulation}
            />
            {/* Historical Replay Scrubbing Controller Panel */}
            <div className="p-4 bg-slate-950 border-t border-slate-800">
              <ReplayControlPanel />
            </div>
          </div>
        )}

        {activeView === 'CIVILIAN' && (
          <CivilianView
            telemetry={telemetry}
            language={language}
            onLaunchAR={() => setShowARCamera(true)}
          />
        )}

        {activeView === 'METRICS' && (
          <AdminMetricsView />
        )}

        {activeView === 'AUTHORITY' && (
          <AuthorityBridgeView />
        )}

        {activeView === 'FEDERATED' && (
          <FederatedLearningView />
        )}
      </main>

      {/* AR Camera Overlay Modal */}
      {showARCamera && (
        <ARWayfindingView onClose={() => setShowARCamera(false)} />
      )}

      <Footer />
    </div>
  );
};

export default App;
