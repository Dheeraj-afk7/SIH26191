import React from 'react';
import { Activity, Server, Database, RefreshCw } from 'lucide-react';
import { useHealth } from '../hooks';
import { StatusBadge } from '../components/shared/StatusBadge';
import { InfoTooltip } from '../components/shared/InfoTooltip';

export const SystemStatusPage: React.FC = () => {
  const { data: health, refetch: refetchHealth, isFetching } = useHealth();

  const datasets = health?.datasets_loaded;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-700" />
              <span>System & Dataset Load Status</span>
            </h2>
            <InfoTooltip
              title="System Diagnostics"
              content="Real-time status of backend FastAPI application, in-memory spatial data loader caches, and API endpoints."
              side="bottom"
            />
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            FastAPI Backend Diagnostics & In-Memory Dataset Cache Integrity (Port 8000)
          </p>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={() => refetchHealth()}
            disabled={isFetching}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 transition-colors shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-blue-600' : ''}`} />
            <span>{isFetching ? 'Refreshing...' : 'Refresh Status'}</span>
          </button>
          <InfoTooltip
            title="Refresh Health Status"
            content="Polls GET /api/health to re-verify backend process and dataset cache availability."
            side="left"
          />
        </div>
      </div>

      {/* Backend API Service Card */}
      <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
            <Server className="w-4 h-4 text-blue-600" />
            <span>FastAPI Backend Service</span>
          </h3>
          <InfoTooltip
            title="FastAPI Microservice"
            content="High-performance ASGI server hosting deterministic spatial decision endpoints and OpenAPI schema."
            side="left"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 relative group">
            <div className="flex items-center justify-between">
              <span className="text-slate-500">API Health Status</span>
              <InfoTooltip title="Health Probe" content="Result of the GET /api/health probe check." side="top" />
            </div>
            <div className="mt-1">
              <StatusBadge status={health?.status === 'ok' ? 'PASS' : 'FAIL'} label={health?.status === 'ok' ? 'Online (200 OK)' : 'Offline'} />
            </div>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 relative group">
            <div className="flex items-center justify-between">
              <span className="text-slate-500">API Version</span>
              <InfoTooltip title="API Semantic Version" content="Current version of the SIH26191 FastAPI backend service." side="top" />
            </div>
            <p className="font-mono font-bold text-slate-900 mt-1">
              {health?.api_version || '1.0.0'}
            </p>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 relative group">
            <div className="flex items-center justify-between">
              <span className="text-slate-500">CORS Allowed Origins</span>
              <InfoTooltip title="Cross-Origin Resource Sharing" content="Whitelisted client origins allowed to invoke backend REST endpoints." side="top" />
            </div>
            <p className="font-mono text-slate-700 mt-1">
              * (Vercel & Localhost)
            </p>
          </div>
        </div>
      </div>

      {/* In-Memory Datasets Status Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
            <Database className="w-4 h-4 text-blue-600" />
            <span>DataLoader In-Memory Cache Status</span>
          </h3>
          <InfoTooltip
            title="In-Memory Spatial Cache"
            content="Fast GeoPandas in-memory spatial indexes enabling instant bounding-box queries and JSON serialization without database lag."
            side="left"
          />
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/75 text-slate-700 font-semibold text-[11px] border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-4">
                  <div className="flex items-center gap-1">
                    <span>Dataset Layer</span>
                    <InfoTooltip title="Dataset Layer" content="Logical dataset layer loaded at server boot." side="top" />
                  </div>
                </th>
                <th className="py-2.5 px-4">
                  <div className="flex items-center gap-1">
                    <span>Target File Path</span>
                    <InfoTooltip title="File System Location" content="Relative file path inside the backend repository." side="top" />
                  </div>
                </th>
                <th className="py-2.5 px-4">
                  <div className="flex items-center gap-1">
                    <span>Memory Cache</span>
                    <InfoTooltip title="Cache State" content="Whether the dataset is actively resident in server RAM." side="top" />
                  </div>
                </th>
                <th className="py-2.5 px-4">
                  <div className="flex items-center gap-1">
                    <span>API Endpoint</span>
                    <InfoTooltip title="REST Endpoint" content="The HTTP route exposing this dataset." side="top" />
                  </div>
                </th>
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
