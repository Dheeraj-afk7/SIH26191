import React from 'react';
import { Activity, Server, Database, RefreshCw } from 'lucide-react';
import { useHealth } from '../hooks';
import { StatusBadge } from '../components/shared/StatusBadge';

export const SystemStatusPage: React.FC = () => {
  const { data: health, refetch: refetchHealth } = useHealth();

  const datasets = health?.datasets_loaded;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-700" />
            <span>System & Dataset Load Status</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            FastAPI Backend Diagnostics & In-Memory Dataset Cache Integrity (Port 8000)
          </p>
        </div>

        <button
          onClick={() => refetchHealth()}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Status</span>
        </button>
      </div>

      {/* Backend API Service Card */}
      <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-4">
        <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
          <Server className="w-4 h-4 text-blue-600" />
          <span>FastAPI Backend Service</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <span className="text-slate-500">API Health Status</span>
            <div className="mt-1">
              <StatusBadge status={health?.status === 'ok' ? 'PASS' : 'FAIL'} label={health?.status === 'ok' ? 'Online (200 OK)' : 'Offline'} />
            </div>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <span className="text-slate-500">API Version</span>
            <p className="font-mono font-bold text-slate-900 mt-1">
              {health?.api_version || '1.0.0'}
            </p>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <span className="text-slate-500">CORS Allowed Origins</span>
            <p className="font-mono text-slate-700 mt-1">
              localhost:3000, localhost:8000
            </p>
          </div>
        </div>
      </div>

      {/* In-Memory Datasets Status Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 bg-slate-50/50">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
            <Database className="w-4 h-4 text-blue-600" />
            <span>DataLoader In-Memory Cache Status</span>
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/75 text-slate-700 font-semibold text-[11px] border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-4">Dataset Layer</th>
                <th className="py-2.5 px-4">Target File Path</th>
                <th className="py-2.5 px-4">Memory Cache</th>
                <th className="py-2.5 px-4">API Endpoint</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-slate-800">
              <tr>
                <td className="py-2.5 px-4 font-semibold">Decision Summary</td>
                <td className="py-2.5 px-4 font-mono text-slate-600">data/processed/decision/decision_summary.json</td>
                <td className="py-2.5 px-4">
                  <StatusBadge status={datasets?.decision_summary ? 'PASS' : 'FAIL'} label={datasets?.decision_summary ? 'Loaded' : 'Not Loaded'} size="sm" />
                </td>
                <td className="py-2.5 px-4 font-mono text-blue-600">/api/decision/summary</td>
              </tr>
              <tr>
                <td className="py-2.5 px-4 font-semibold">Village Priority Profiles</td>
                <td className="py-2.5 px-4 font-mono text-slate-600">data/processed/decision/village_priority_profiles.gpkg</td>
                <td className="py-2.5 px-4">
                  <StatusBadge status={datasets?.villages ? 'PASS' : 'FAIL'} label={datasets?.villages ? 'Loaded (653 records)' : 'Not Loaded'} size="sm" />
                </td>
                <td className="py-2.5 px-4 font-mono text-blue-600">/api/villages</td>
              </tr>
              <tr>
                <td className="py-2.5 px-4 font-semibold">Candidate Red Zones</td>
                <td className="py-2.5 px-4 font-mono text-slate-600">data/outputs/candidate_hazard_based_red_zones.geojson</td>
                <td className="py-2.5 px-4">
                  <StatusBadge status={datasets?.red_zones ? 'PASS' : 'FAIL'} label={datasets?.red_zones ? 'Loaded (289 zones)' : 'Not Loaded'} size="sm" />
                </td>
                <td className="py-2.5 px-4 font-mono text-blue-600">/api/red-zones</td>
              </tr>
              <tr>
                <td className="py-2.5 px-4 font-semibold">Candidate Feasible Areas</td>
                <td className="py-2.5 px-4 font-mono text-slate-600">data/outputs/candidate_topographically_feasible_areas_attributed.geojson</td>
                <td className="py-2.5 px-4">
                  <StatusBadge status={datasets?.candidate_areas ? 'PASS' : 'FAIL'} label={datasets?.candidate_areas ? 'Loaded (5 areas)' : 'Not Loaded'} size="sm" />
                </td>
                <td className="py-2.5 px-4 font-mono text-blue-600">/api/candidate-areas</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
