import React from 'react';
import { BookOpenCheck, AlertTriangle } from 'lucide-react';
import { StatusBadge } from '../components/shared/StatusBadge';

export const MethodologyPage: React.FC = () => {
  const dataMatrix = [
    { name: 'Copernicus GLO-30 DEM', source: 'ESA / Copernicus Open Access', status: 'AVAILABLE', role: 'Slope, aspect, hydrology (TWI)' },
    { name: 'Census of India 2011 (PCA)', source: 'Office of the Registrar General & Census Commissioner', status: 'AVAILABLE', role: 'Village population, households, literacy, demographics' },
    { name: 'SHRUG v2.2 Spatial Centroids', source: 'Development Data Lab', status: 'AVAILABLE', role: 'Administrative village centroid points' },
    { name: 'Disaster History (NDMA / SDMA)', source: 'State Disaster Management Authority', status: 'NOT_ACQUIRED', role: 'Historical incident overlay (Tier 1 confirmation pending)' },
    { name: 'Critical Infrastructure (Schools, Hospitals)', source: 'OpenStreetMap / Dept. Surveys', status: 'NOT_ACQUIRED', role: 'Infrastructure exposure scoring' },
    { name: 'Road Network & Accessibility', source: 'PWD / Survey of India', status: 'NOT_ACQUIRED', role: 'Routable candidate area accessibility' },
    { name: 'Land Use / Land Cover (LULC)', source: 'ISRO Bhuvan', status: 'NOT_ACQUIRED', role: 'Forest / protected land exclusion' },
    { name: 'Capacity Planning Standards', source: 'Urban/Rural Planning Manuals', status: 'NOT_CONFIGURED', role: 'Carrying capacity per household estimation' },
  ];

  const limitations = [
    { title: 'No Verified Disaster History Dataset', desc: 'Disaster incident records from NDMA/SDMA were not acquired. Tier 1 priority cannot be confirmed by historical landslide evidence.' },
    { title: 'Administrative Centroids vs Settlement Footprints', desc: 'Village coordinates represent administrative reference points. Actual habitations, building clusters, or roads may be closer to hazard terrain than centroid distances indicate.' },
    { title: 'Census 2011 Baseline Vintage', desc: 'Demographic baseline is from Census 2011 (~15 years old). Demographic expansion and new settlements are not reflected.' },
    { title: '30-Meter DEM Spatial Precision', desc: 'Slope and hydrological indices are derived at ~30m pixel resolution. Local site micro-topography requires on-site topographic surveys.' },
    { title: 'Equal-Weight Multi-Hazard Integration', desc: 'Multi-hazard screening integrates terrain susceptibility proxy (50%) and hydrological flood exposure proxy (50%) as an uncalibrated deterministic baseline.' },
    { title: 'CA-0001 Unfiltered Extent (~361k ha)', desc: 'Due to unconfigured slope/mapping thresholds, CA-0001 represents a broad contiguous terrain polygon rather than discrete recommended sites.' },
    { title: 'Carrying Capacity Unestimated', desc: 'No carrying capacity figures are generated due to absence of verified planning standards (area per household/person).' },
    { title: 'No Automated Allocation', desc: 'The system does not allocate specific habitations to candidate areas, requiring official multi-disciplinary planning review.' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <BookOpenCheck className="w-5 h-5 text-blue-700" />
          <span>Methodology, Provenance & Transparency</span>
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Deterministic Rule-Based Spatial Architecture & Limitations Audit (SIH26191)
        </p>
      </div>

      {/* Pipeline Flow Diagram */}
      <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-4">
        <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
          Processing Pipeline Architecture (Steps 1–10)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-xs">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <span className="font-mono text-[10px] text-blue-600 font-bold block mb-1">STEPS 1–3</span>
            <p className="font-semibold text-slate-900">DEM Processing</p>
            <p className="text-[11px] text-slate-500 mt-1">Copernicus GLO-30m slope & aspect derivation in UTM 44N</p>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <span className="font-mono text-[10px] text-blue-600 font-bold block mb-1">STEPS 4–6</span>
            <p className="font-semibold text-slate-900">Multi-Hazard</p>
            <p className="text-[11px] text-slate-500 mt-1">Terrain susceptibility proxy (50%) + Hydrological TWI proxy (50%)</p>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <span className="font-mono text-[10px] text-blue-600 font-bold block mb-1">STEP 7</span>
            <p className="font-semibold text-slate-900">Red Zones</p>
            <p className="text-[11px] text-slate-500 mt-1">289 Candidate Red Zone vector polygons generated</p>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <span className="font-mono text-[10px] text-blue-600 font-bold block mb-1">STEPS 8–9</span>
            <p className="font-semibold text-slate-900">Exposure & Terrain</p>
            <p className="text-[11px] text-slate-500 mt-1">653 Habitations join + 5 candidate screened terrain areas</p>
          </div>

          <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
            <span className="font-mono text-[10px] text-blue-700 font-bold block mb-1">STEP 10</span>
            <p className="font-semibold text-blue-950">Decision Engine</p>
            <p className="text-[11px] text-blue-800 mt-1">Explainable rule-based priority tier assignment</p>
          </div>
        </div>
      </div>

      {/* Data Availability Matrix */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 bg-slate-50/50">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Dataset Acquisition & Availability Matrix
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/75 text-slate-700 font-semibold text-[11px] border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-4">Dataset Name</th>
                <th className="py-2.5 px-4">Source / Citation</th>
                <th className="py-2.5 px-4">Status</th>
                <th className="py-2.5 px-4">Pipeline Role</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-slate-800">
              {dataMatrix.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-50">
                  <td className="py-2.5 px-4 font-semibold text-slate-900">{item.name}</td>
                  <td className="py-2.5 px-4 text-slate-600">{item.source}</td>
                  <td className="py-2.5 px-4">
                    <StatusBadge status={item.status} size="sm" />
                  </td>
                  <td className="py-2.5 px-4 text-slate-600">{item.role}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Limitations Accordion / Cards */}
      <div id="limitations" className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-4">
        <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-600" />
          <span>Scientific Caveats & Limitations</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          {limitations.map((lim, idx) => (
            <div key={idx} className="p-3.5 rounded-lg border border-slate-200 bg-slate-50 space-y-1">
              <p className="font-bold text-slate-900">{idx + 1}. {lim.title}</p>
              <p className="text-slate-600 text-[11px] leading-relaxed">{lim.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
