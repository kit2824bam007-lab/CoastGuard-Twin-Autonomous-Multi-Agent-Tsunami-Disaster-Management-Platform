export type ViewMode = 'COMMAND_CENTER' | 'CIVILIAN' | 'METRICS' | 'AUTHORITY' | 'FEDERATED';
export type UserRole = 'OPERATOR' | 'RESPONDER' | 'AUTHORITY_VIEWER' | 'ADMIN';
export type DataMode = 'SIMULATED' | 'LIVE_PUBLIC_FEEDS';

export type ShorelineState = 'NORMAL' | 'RECEDING' | 'SURGING';
export type AgentType = 'UAV' | 'USV' | 'GROUND';
export type AgentStatus = 'ACTIVE' | 'RETURNING' | 'LOST';

export interface SeismicPoint {
  time: number;
  p_wave: number;
  s_wave: number;
  amplitude: number;
}

export interface BuoyPoint {
  time: number;
  anomaly_meters: number;
}

export interface SensorSnapshot {
  timestamp: number;
  tick: number;
  is_event_active: boolean;
  event_params: {
    magnitude: number;
    distance_km: number;
    start_time: number;
  };
  sensors: {
    seismic: {
      p_wave: number;
      s_wave: number;
      combined_amplitude: number;
    };
    dart_buoy: {
      sea_level_anomaly_m: number;
      status: string;
    };
    shoreline_camera: {
      state: ShorelineState;
    };
  };
  history: {
    seismic: SeismicPoint[];
    buoy: BuoyPoint[];
  };
}

export interface SwarmAgentData {
  id: string;
  type: AgentType;
  position: { x: number; y: number };
  target: { x: number; y: number };
  status: AgentStatus;
  battery: number;
  confidence_report: number;
  assigned_sector: string;
  connected_neighbors: string[];
}

export interface MeshEdge {
  source: string;
  target: string;
  distance: number;
  signal_strength: number;
}

export interface MeshTopology {
  nodes: SwarmAgentData[];
  edges: MeshEdge[];
  comm_range: number;
  is_satellite_failover_active?: boolean;
  channel_type?: string;
  total_active: number;
  total_lost: number;
}

export interface TwinRiskCell {
  x: number;
  y: number;
  elevation_m: number;
  inundation_depth_m: number;
  risk_score: number;
  risk_level: 'OCEAN' | 'NO_RISK' | 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
}

export interface TwinSummary {
  max_inundation_depth_m: number;
  high_risk_cells_count: number;
  critical_risk_cells_count: number;
  overall_threat_active: boolean;
}

export interface HazardClassification {
  predicted_class: 'NO_THREAT' | 'WATCH' | 'WARNING' | 'SEVERE';
  severity_index: number;
  confidence: number;
  class_probabilities: Record<string, number>;
}

export interface TelemetryPayload {
  type: string;
  timestamp: number;
  is_event_active: boolean;
  sensors: SensorSnapshot['sensors'];
  seismic_history: SeismicPoint[];
  buoy_history: BuoyPoint[];
  twin_summary: TwinSummary;
  swarm: {
    agents: SwarmAgentData[];
    topology: MeshTopology;
  };
  hazard_classification: HazardClassification;
}

export interface ClassifierMetrics {
  dataset_samples: number;
  train_samples: number;
  val_samples: number;
  test_samples: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  classes: string[];
  confusion_matrix_raw: number[][];
  confusion_matrix_percentage: number[][];
}

export interface BenchmarkMetricItem {
  key: string;
  title: string;
  unit: string;
  baseline: number;
  proposed_swarm: number;
  improvement_percentage: number;
  lower_is_better: boolean;
}

export interface BenchmarkData {
  timestamp: number;
  is_event_active: boolean;
  metrics: BenchmarkMetricItem[];
}
