import React, { useState, useEffect } from 'react';
import { ShieldCheck, FileJson, History, Send, Lock, Copy, Check } from 'lucide-react';
import { apiUrl } from '../api/client';

export const AuthorityBridgeView: React.FC = () => {
  const [capData, setCapData] = useState<any>(null);
  const [auditLog, setAuditLog] = useState<any[]>([]);
  const [copied, setCopied] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [resCap, resAudit] = await Promise.all([
        fetch(apiUrl('/api/authority/export-cap')),
        fetch(apiUrl('/api/authority/audit-log'))
      ]);
      const capJson = await resCap.json();
      const auditJson = await resAudit.json();

      setCapData(capJson);
      setAuditLog(auditJson.audit_log || []);
    } catch (e) {
      console.error("Error loading authority bridge data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCopyCap = () => {
    if (capData) {
      navigator.clipboard.writeText(JSON.stringify(capData, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="min-h-[calc(100vh-68px)] bg-slate-50 p-4 sm:p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-cyan-600" /> Official-Authority Handoff & Immutable Audit Ledger
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Structured Common Alerting Protocol (CAP v1.2) export for forwarding to regional warning centers (INCOIS / PTWC).
          </p>
        </div>

        <button
          onClick={fetchData}
          className="px-3.5 py-2 rounded-xl bg-white hover:bg-slate-50 text-cyan-700 font-semibold text-xs border border-slate-200 transition shadow-sm"
        >
          Refresh Handoff Report
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* CAP v1.2 JSON Export Panel */}
        <div className="glass-panel p-5 rounded-3xl border border-slate-200 shadow-md space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
              <FileJson className="w-4 h-4 text-cyan-600" /> OASIS CAP v1.2 Export Structure
            </span>

            <button
              onClick={handleCopyCap}
              className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-cyan-50 hover:bg-cyan-100 text-cyan-800 border border-cyan-200 text-xs font-semibold transition shadow-sm"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-cyan-700" />}
              {copied ? 'Copied JSON!' : 'Copy CAP Payload'}
            </button>
          </div>

          <div className="bg-slate-900 p-4 rounded-2xl border border-slate-800 font-mono text-[11px] text-cyan-300 overflow-x-auto max-h-96 shadow-inner">
            <pre>{JSON.stringify(capData, null, 2)}</pre>
          </div>

          <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs text-slate-600 flex items-center justify-between">
            <span>Target Official Warning Authorities:</span>
            <span className="font-bold text-slate-900">INCOIS (India) & NOAA / PTWC</span>
          </div>
        </div>

        {/* Immutable Audit Ledger Table */}
        <div className="glass-panel p-5 rounded-3xl border border-slate-200 shadow-md space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
              <History className="w-4 h-4 text-amber-600" /> Immutable Event Audit Ledger
            </span>
            <span className="text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-mono flex items-center gap-1 font-semibold">
              <Lock className="w-3 h-3 text-emerald-600" /> Append-Only Immutable
            </span>
          </div>

          <div className="overflow-y-auto max-h-96 pr-1 space-y-2">
            {auditLog.map((log) => (
              <div key={log.id} className="p-3 rounded-xl bg-white border border-slate-200 text-xs space-y-1 shadow-sm">
                <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
                  <span className="text-cyan-700 font-bold">{log.event_type}</span>
                  <span>{log.timestamp}</span>
                </div>
                <div className="text-slate-800 font-medium">{log.details}</div>
                <div className="text-[9px] text-slate-400 font-mono">Operator ID: {log.operator_id} | UUID: {log.id.slice(0, 8)}...</div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};
