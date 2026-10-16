import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Network, Cpu, Play, CheckCircle, RefreshCw } from 'lucide-react';
import { apiUrl } from '../api/client';

export const FederatedLearningView: React.FC = () => {
  const [flStatus, setFlStatus] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchFlStatus = async () => {
    try {
      const res = await fetch(apiUrl('/api/federated/status'));
      const data = await res.json();
      setFlStatus(data);
    } catch (e) {
      console.error("Error fetching FL status:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFlStatus();
  }, []);

  const handleRunRound = async () => {
    try {
      setLoading(true);
      const res = await fetch(apiUrl('/api/federated/run-round'), { method: 'POST' });
      const data = await res.json();
      setFlStatus(data);
    } catch (e) {
      console.error("Error running FL round:", e);
    } finally {
      setLoading(false);
    }
  };

  const history = flStatus?.history || [];
  const regionalTwins = flStatus?.regional_twins || [];

  return (
    <div className="min-h-[calc(100vh-68px)] bg-slate-50 p-4 sm:p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Network className="w-5 h-5 text-cyan-600" /> Federated Learning Across Regional Digital Twins
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Simulates 3 Regional Twin instances sharing local model weight updates via Federated Averaging (FedAvg) to optimize global tsunami classification without raw data centralization.
          </p>
        </div>

        <button
          onClick={handleRunRound}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs shadow-md shadow-cyan-600/20 transition disabled:opacity-50"
        >
          <Play className="w-4 h-4 fill-current" /> Execute FedAvg Training Round ({flStatus?.round_number || 0})
        </button>
      </div>

      {/* 3 Regional Twin Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {regionalTwins.map((region: any) => (
          <div key={region.id} className="glass-panel p-5 rounded-3xl border border-slate-200 shadow-md space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-cyan-700 font-mono">{region.id}</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
                Local SGD Active
              </span>
            </div>

            <h3 className="text-sm font-bold text-slate-900">{region.name}</h3>

            <div className="space-y-1.5 text-xs text-slate-600 pt-2 border-t border-slate-200">
              <div className="flex justify-between">
                <span>Training Dataset:</span>
                <span className="font-mono text-slate-800">{region.samples} samples</span>
              </div>
              <div className="flex justify-between">
                <span>Local Accuracy:</span>
                <span className="font-mono font-bold text-emerald-600">{(region.local_accuracy * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-[10px]">
                <span>Weights Hash:</span>
                <span className="font-mono text-cyan-700">0x{region.weights_hash}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* FedAvg Global Model Convergence Chart */}
      <div className="glass-panel p-5 rounded-3xl border border-slate-200 shadow-md space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-cyan-600" /> Global FedAvg Accuracy Convergence
            </h3>
            <span className="text-xs text-slate-500">Aggregated Global Model Accuracy vs FedAvg Rounds</span>
          </div>

          <div className="text-right">
            <div className="text-xs text-slate-500">Global Model Accuracy</div>
            <div className="text-2xl font-black text-cyan-700 font-mono">
              {((flStatus?.global_accuracy || 0.948) * 100).toFixed(1)}%
            </div>
          </div>
        </div>

        <div className="h-60 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history}>
              <XAxis dataKey="round" stroke="#64748b" fontSize={11} />
              <YAxis domain={[0.9, 1.0]} stroke="#64748b" fontSize={11} />
              <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#cbd5e1', color: '#0f172a', borderRadius: '8px', fontSize: '11px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }} />
              <Line type="monotone" dataKey="global_accuracy" stroke="#0284c7" strokeWidth={3} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

    </div>
  );
};
