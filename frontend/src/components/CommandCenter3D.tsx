import React, { useRef, useMemo, useState, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Html } from '@react-three/drei';
import * as THREE from 'three';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';
import { ShieldAlert, Radio, Battery, Wifi, AlertTriangle, Glasses, Plus, Zap } from 'lucide-react';
import { TelemetryPayload, SwarmAgentData, MeshEdge, ShorelineState } from '../types';

interface CommandCenter3DProps {
  telemetry: TelemetryPayload | null;
  bathymetryGrid: number[][] | null;
  onTriggerEvent: (magnitude: number, distanceKm: number) => void;
  onDeployAgent: (type: 'UAV' | 'USV' | 'GROUND', x: number, y: number) => void;
  onSimulateLoss: (agentId: string) => void;
  onReset: () => void;
}

// -------------------------------------------------------------
// 3D Terrain Mesh with Bathymetry & Inundation Risk Vertex Colors
// -------------------------------------------------------------
const TerrainMesh: React.FC<{ bathymetryGrid: number[][] | null; isEventActive: boolean; anomaly: number }> = ({
  bathymetryGrid,
  isEventActive,
  anomaly
}) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const size = 50;

  const { geometry, colors } = useMemo(() => {
    const geom = new THREE.PlaneGeometry(size, size, size - 1, size - 1);
    geom.rotateX(-Math.PI / 2); // Lay flat on XZ plane

    const pos = geom.attributes.position;
    const colorArray = new Float32Array(pos.count * 3);

    for (let y = 0; y < size; y++) {
      for (let x = 0; x < size; x++) {
        const idx = y * size + x;
        const elevation = bathymetryGrid ? bathymetryGrid[y]?.[x] || 0 : 0;
        
        // Scale elevation for 3D visualization height
        const zHeight = elevation > 0 ? elevation * 0.15 : elevation * 0.08;
        pos.setY(idx, zHeight);

        // Compute vertex colors
        // x=0 is deep ocean, x=20 is shoreline, x=49 is land
        let color = new THREE.Color();

        if (elevation <= 0) {
          // Ocean depth colors (dark blue to cyan near shore)
          const depthRatio = Math.min(1.0, Math.abs(elevation) / 100.0);
          color.setHSL(0.6, 0.8, 0.15 + (1 - depthRatio) * 0.25);
        } else {
          // Land elevation colors (green coast -> brown hills)
          const coastDist = x - 20;
          const riskInundated = isEventActive && (anomaly * 1.5 - 0.3 * elevation - 0.04 * coastDist) > 0.2;

          if (riskInundated) {
            // Inundation Risk Overlay Heatmap (Orange to Crimson Red)
            const riskSeverity = Math.min(1.0, (anomaly * 1.2) / 3.0);
            color.setHSL(0.0, 0.9, 0.4 + riskSeverity * 0.2); // Red glow
          } else {
            // Normal land topography (emerald to sandy brown)
            const h = 0.3 - (elevation / 120.0) * 0.2; // Green to yellow/brown
            color.setHSL(Math.max(0.08, h), 0.5, 0.25 + (elevation / 120.0) * 0.3);
          }
        }

        colorArray[idx * 3] = color.r;
        colorArray[idx * 3 + 1] = color.g;
        colorArray[idx * 3 + 2] = color.b;
      }
    }

    geom.computeVertexNormals();
    geom.setAttribute('color', new THREE.BufferAttribute(colorArray, 3));
    return { geometry: geom, colors: colorArray };
  }, [bathymetryGrid, isEventActive, anomaly]);

  return (
    <mesh ref={meshRef} geometry={geometry} position={[0, 0, 0]} receiveShadow castShadow>
      <meshStandardMaterial vertexColors roughness={0.7} metalness={0.1} wireframe={false} />
    </mesh>
  );
};

// -------------------------------------------------------------
// 3D Ocean Water Surface with Wave Ripple Dynamics
// -------------------------------------------------------------
const WaterSurface: React.FC<{ anomaly: number }> = ({ anomaly }) => {
  const waterRef = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (waterRef.current) {
      const t = clock.getElapsedTime();
      waterRef.current.position.y = (anomaly * 0.15) + Math.sin(t * 1.5) * 0.1;
    }
  });

  return (
    <mesh ref={waterRef} position={[-7.5, 0, 0]} rotation={[-Math.PI / 2, 0, 0]}>
      <planeGeometry args={[25, 50, 20, 20]} />
      <meshStandardMaterial
        color="#0284c7"
        transparent
        opacity={0.65}
        roughness={0.1}
        metalness={0.8}
      />
    </mesh>
  );
};

// -------------------------------------------------------------
// 3D Swarm Agent Markers & Target Beacons
// -------------------------------------------------------------
const Agent3DMarker: React.FC<{ agent: SwarmAgentData; onSimulateLoss: (id: string) => void }> = ({
  agent,
  onSimulateLoss
}) => {
  const groupRef = useRef<THREE.Group>(null);
  
  // Transform grid coordinates (0..50) to Three.js centered coordinates (-25..25)
  const posX = agent.position.x - 25;
  const posZ = agent.position.y - 25;
  const posY = agent.type === 'UAV' ? 7.0 : (agent.type === 'USV' ? 0.4 : 0.8);

  useFrame(({ clock }) => {
    if (groupRef.current && agent.status === 'ACTIVE') {
      const t = clock.getElapsedTime() + (hashString(agent.id) % 10);
      if (agent.type === 'UAV') {
        groupRef.current.position.y = posY + Math.sin(t * 3.0) * 0.3;
      }
    }
  });

  const agentColor = agent.status === 'LOST' 
    ? '#ef4444' 
    : (agent.type === 'UAV' ? '#38bdf8' : (agent.type === 'USV' ? '#14b8a6' : '#f59e0b'));

  return (
    <group ref={groupRef} position={[posX, posY, posZ]}>
      {/* 3D Geometry per agent type */}
      {agent.type === 'UAV' ? (
        <mesh>
          <sphereGeometry args={[0.6, 16, 16]} />
          <meshStandardMaterial color={agentColor} emissive={agentColor} emissiveIntensity={0.6} />
        </mesh>
      ) : agent.type === 'USV' ? (
        <mesh rotation={[0, Math.PI / 4, 0]}>
          <coneGeometry args={[0.7, 1.4, 4]} />
          <meshStandardMaterial color={agentColor} metalness={0.6} roughness={0.2} />
        </mesh>
      ) : (
        <mesh>
          <boxGeometry args={[0.9, 0.6, 0.9]} />
          <meshStandardMaterial color={agentColor} roughness={0.5} />
        </mesh>
      )}

      {/* Status Ring / Lost Red Beacon */}
      {agent.status === 'LOST' && (
        <mesh rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.8, 1.2, 32]} />
          <meshBasicMaterial color="#ef4444" side={THREE.DoubleSide} transparent opacity={0.8} />
        </mesh>
      )}

      {/* HTML Label on 3D Object */}
      <Html distanceFactor={35} position={[0, 1.2, 0]} center>
        <div className="flex flex-col items-center select-none pointer-events-auto">
          <button
            onClick={() => onSimulateLoss(agent.id)}
            title="Click to simulate agent loss"
            className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold whitespace-nowrap shadow-md border transition ${
              agent.status === 'LOST'
                ? 'bg-red-950/90 text-red-400 border-red-800'
                : 'bg-slate-900/90 text-cyan-300 border-slate-700 hover:border-red-500 hover:text-red-400'
            }`}
          >
            {agent.id} ({agent.battery}%)
          </button>
        </div>
      </Html>
    </group>
  );
};

// -------------------------------------------------------------
// 3D Mesh Topology Connections (Terrestrial Mesh vs LEO Satellite Rays)
// -------------------------------------------------------------
const TopologyEdges3D: React.FC<{ edges: MeshEdge[]; agents: SwarmAgentData[]; isSatelliteActive?: boolean }> = ({
  edges,
  agents,
  isSatelliteActive
}) => {
  const agentMap = useMemo(() => {
    const map = new Map<string, SwarmAgentData>();
    agents.forEach(a => map.set(a.id, a));
    return map;
  }, [agents]);

  const { linePositions, satPositions } = useMemo(() => {
    const coords: number[] = [];
    const satCoords: number[] = [];
    const satOrbitalNode = [0, 25, 0];

    agents.forEach(a => {
      if (a.status !== 'LOST') {
        const y = a.type === 'UAV' ? 7.0 : (a.type === 'USV' ? 0.4 : 0.8);
        satCoords.push(a.position.x - 25, y, a.position.y - 25);
        satCoords.push(satOrbitalNode[0], satOrbitalNode[1], satOrbitalNode[2]);
      }
    });

    edges.forEach(edge => {
      const a1 = agentMap.get(edge.source);
      const a2 = agentMap.get(edge.target);
      if (a1 && a2 && a1.status !== 'LOST' && a2.status !== 'LOST') {
        const y1 = a1.type === 'UAV' ? 7.0 : (a1.type === 'USV' ? 0.4 : 0.8);
        const y2 = a2.type === 'UAV' ? 7.0 : (a2.type === 'USV' ? 0.4 : 0.8);
        coords.push(a1.position.x - 25, y1, a1.position.y - 25);
        coords.push(a2.position.x - 25, y2, a2.position.y - 25);
      }
    });

    return {
      linePositions: new Float32Array(coords),
      satPositions: new Float32Array(satCoords)
    };
  }, [edges, agents, agentMap]);

  return (
    <group>
      {/* Terrestrial Mesh Edges */}
      {!isSatelliteActive && linePositions.length > 0 && (
        <lineSegments>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={linePositions.length / 3}
              array={linePositions}
              itemSize={3}
            />
          </bufferGeometry>
          <lineBasicMaterial color="#38bdf8" opacity={0.5} transparent linewidth={2} />
        </lineSegments>
      )}

      {/* LEO Satellite Rays & Orbital Node */}
      {isSatelliteActive && (
        <group>
          {/* Orbital Satellite Node */}
          <mesh position={[0, 25, 0]}>
            <octahedronGeometry args={[1.2, 0]} />
            <meshStandardMaterial color="#f59e0b" emissive="#f59e0b" emissiveIntensity={0.8} />
          </mesh>

          {/* Golden Rays connecting agents to LEO Satellite */}
          <lineSegments>
            <bufferGeometry>
              <bufferAttribute
                attach="attributes-position"
                count={satPositions.length / 3}
                array={satPositions}
                itemSize={3}
              />
            </bufferGeometry>
            <lineBasicMaterial color="#f59e0b" opacity={0.6} transparent linewidth={2} />
          </lineSegments>
        </group>
      )}
    </group>
  );
};

function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
  }
  return Math.abs(hash);
}

// -------------------------------------------------------------
// MAIN COMMAND CENTER 3D COMPONENT
// -------------------------------------------------------------
export const CommandCenter3D: React.FC<CommandCenter3DProps> = ({
  telemetry,
  bathymetryGrid,
  onTriggerEvent,
  onDeployAgent,
  onSimulateLoss,
  onReset
}) => {
  const [xrSupported, setXrSupported] = useState<boolean>(false);
  const [inXrMode, setInXrMode] = useState<boolean>(false);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  // Check WebXR Browser Support (VR/AR Headsets & Phones)
  useEffect(() => {
    if ('xr' in navigator && (navigator as any).xr) {
      (navigator as any).xr.isSessionSupported('immersive-vr').then((supported: boolean) => {
        setXrSupported(supported);
      }).catch(() => setXrSupported(false));
    }
  }, []);

  const handleToggleWebXR = () => {
    if (!xrSupported) {
      alert("WebXR Immersive Session not detected on this browser/hardware. Operating in interactive 3D Orbit View fallback mode.");
      return;
    }
    setInXrMode(!inXrMode);
  };

  const isEventActive = telemetry?.is_event_active || false;
  const anomaly = telemetry?.sensors?.dart_buoy?.sea_level_anomaly_m || 0.05;
  const hazard = telemetry?.hazard_classification;
  const swarmAgents = telemetry?.swarm?.agents || [];
  const topologyEdges = telemetry?.swarm?.topology?.edges || [];

  return (
    <div className="relative w-full h-[calc(100vh-68px)] bg-slate-950 overflow-hidden flex flex-col md:flex-row">
      {/* 3D Metaverse Canvas Scene */}
      <div className="relative flex-1 h-full">
        {/* WebXR Immersion Entry Button */}
        <div className="absolute top-4 left-4 z-20 flex items-center gap-2">
          <button
            onClick={handleToggleWebXR}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition shadow-lg backdrop-blur-md border ${
              inXrMode
                ? 'bg-cyan-500 text-slate-950 border-cyan-300 shadow-cyan-500/30'
                : 'bg-slate-900/80 text-cyan-400 border-cyan-500/30 hover:bg-slate-800'
            }`}
          >
            <Glasses className="w-4 h-4" />
            {xrSupported ? (inXrMode ? 'Exit VR/AR Mode' : 'Enter WebXR Metaverse') : 'WebXR Enabled (Orbit 3D Active)'}
          </button>
        </div>

        {/* Floating Hazard Status Badge Overlay */}
        <div className="absolute top-4 right-4 z-20 max-w-sm glass-panel p-3.5 rounded-2xl border border-slate-700/80 shadow-2xl">
          <div className="flex items-center justify-between gap-3 mb-2">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-cyan-400" /> Layer 5 Decision Support
            </span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider ${
              hazard?.predicted_class === 'SEVERE'
                ? 'bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse'
                : (hazard?.predicted_class === 'WARNING'
                  ? 'bg-orange-500/20 text-orange-400 border border-orange-500/40'
                  : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40')
            }`}>
              {hazard?.predicted_class || 'NO_THREAT'}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
              <div className="text-[10px] text-slate-400">Max Wave Anomaly</div>
              <div className="text-sm font-bold text-cyan-300">{anomaly.toFixed(2)} meters</div>
            </div>
            <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
              <div className="text-[10px] text-slate-400">Mesh Active Swarm</div>
              <div className="text-sm font-bold text-emerald-400">{swarmAgents.filter(a => a.status === 'ACTIVE').length} / {swarmAgents.length}</div>
            </div>
          </div>
        </div>

        <Canvas
          shadows
          camera={{ position: [30, 40, 50], fov: 45 }}
          className="w-full h-full cursor-grab active:cursor-grabbing"
        >
          <ambientLight intensity={0.6} />
          <directionalLight position={[40, 60, 20]} intensity={1.2} castShadow />
          <pointLight position={[-20, 30, -20]} intensity={0.5} color="#38bdf8" />

          {/* 3D Coastline Terrain & Inundation Overlay */}
          <TerrainMesh bathymetryGrid={bathymetryGrid} isEventActive={isEventActive} anomaly={anomaly} />

          {/* 3D Ocean Water Layer */}
          <WaterSurface anomaly={anomaly} />

          {/* 3D Swarm Agent Markers */}
          {swarmAgents.map(agent => (
            <Agent3DMarker key={agent.id} agent={agent} onSimulateLoss={onSimulateLoss} />
          ))}

          {/* 3D Topology Edge Connections (Terrestrial Mesh vs LEO Satellite Rays) */}
          <TopologyEdges3D
            edges={topologyEdges}
            agents={swarmAgents}
            isSatelliteActive={telemetry?.swarm?.topology?.is_satellite_failover_active}
          />

          <OrbitControls
            enablePan
            enableZoom
            enableRotate
            maxPolarAngle={Math.PI / 2.1}
            minDistance={10}
            maxDistance={120}
          />
        </Canvas>
      </div>

      {/* Operator Side Panel Controls & Telemetry */}
      <div className="w-full md:w-96 bg-slate-900/95 border-t md:border-t-0 md:border-l border-slate-800 p-4 flex flex-col gap-4 overflow-y-auto z-20">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Radio className="w-4 h-4 text-cyan-400" /> Command Operations Panel
          </h2>
          <button
            onClick={() => onDeployAgent('UAV', 20.0, 20.0)}
            className="flex items-center gap-1 px-2.5 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs transition"
          >
            <Plus className="w-3.5 h-3.5" /> Deploy Agent
          </button>
        </div>

        {/* Live Seismic Waveform Mini Chart */}
        <div className="glass-panel p-3 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="font-semibold text-slate-300 flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-amber-400" /> Seismic Waveform (P/S Amplitude)
            </span>
            <span className="text-[10px] text-amber-400 font-mono">
              P: {telemetry?.sensors?.seismic?.p_wave || 0} / S: {telemetry?.sensors?.seismic?.s_wave || 0}
            </span>
          </div>
          <div className="h-28 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={telemetry?.seismic_history || []}>
                <XAxis dataKey="time" hide />
                <YAxis domain={[0, 4]} hide />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                />
                <Line type="monotone" dataKey="p_wave" stroke="#38bdf8" strokeWidth={1.5} dot={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="s_wave" stroke="#f59e0b" strokeWidth={1.5} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Swarm Telemetry Roster */}
        <div className="glass-panel p-3 rounded-xl border border-slate-800 flex-1 flex flex-col">
          <div className="flex items-center justify-between text-xs mb-3">
            <span className="font-semibold text-slate-300 flex items-center gap-1.5">
              <Wifi className="w-3.5 h-3.5 text-cyan-400" /> Mesh Swarm Roster
            </span>
            <span className="text-[10px] text-slate-400 font-mono">
              {topologyEdges.length} Edges Active
            </span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2 max-h-56 pr-1">
            {swarmAgents.map(agent => (
              <div
                key={agent.id}
                onClick={() => setSelectedAgent(agent.id)}
                className={`p-2 rounded-lg border text-xs flex items-center justify-between cursor-pointer transition ${
                  agent.status === 'LOST'
                    ? 'bg-red-950/30 border-red-900/60 text-red-300'
                    : (selectedAgent === agent.id ? 'bg-cyan-950/40 border-cyan-500/60 text-white' : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700')
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    agent.status === 'LOST' ? 'bg-red-500 animate-ping' : (agent.status === 'RETURNING' ? 'bg-amber-400' : 'bg-emerald-400')
                  }`} />
                  <div>
                    <div className="font-bold font-mono">{agent.id} <span className="text-[10px] text-slate-400">({agent.type})</span></div>
                    <div className="text-[10px] text-slate-400">Pos: [{agent.position.x}, {agent.position.y}]</div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <div className="flex items-center gap-1 text-[11px] font-mono">
                      <Battery className="w-3 h-3 text-slate-400" /> {agent.battery}%
                    </div>
                    <div className="text-[9px] text-slate-400">{agent.assigned_sector}</div>
                  </div>

                  {agent.status !== 'LOST' && (
                    <button
                      onClick={(e) => { e.stopPropagation(); onSimulateLoss(agent.id); }}
                      title="Simulate Agent Disconnect"
                      className="px-1.5 py-1 rounded bg-red-500/20 hover:bg-red-500/40 text-red-400 text-[10px] font-bold border border-red-500/30 transition"
                    >
                      Disable
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Demo Scenario Controller */}
        <div className="glass-panel p-3 rounded-xl border border-slate-800 space-y-2">
          <div className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Admin Scenario Injector
          </div>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => onTriggerEvent(7.8, 45.0)}
              className="px-2.5 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white font-bold text-xs transition shadow-md shadow-red-600/20"
            >
              M7.8 Quake (45km)
            </button>
            <button
              onClick={onReset}
              className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 transition"
            >
              Reset Simulation
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
