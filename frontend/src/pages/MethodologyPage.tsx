import React from 'react';
import { BookOpenCheck, AlertTriangle } from 'lucide-react';
import { StatusBadge } from '../components/shared/StatusBadge';
import { InfoTooltip } from '../components/shared/InfoTooltip';

export const MethodologyPage: React.FC = () => {
  const dataMatrix = [
    { name: 'Copernicus GLO-30 DEM', source: 'ESA / Copernicus Open Access', status: 'AVAILABLE', role: 'Slope, aspect, hydrology (TWI)', tip: 'Global 30m digital elevation model processed in UTM Zone 44N.' },
    { name: 'Census of India 2011 (PCA)', source: 'Office of the Registrar General & Census Commissioner', status: 'AVAILABLE', role: 'Village population, households, literacy, demographics', tip: 'Primary Census Abstract baseline attributes for 653 habitations.' },
    { name: 'SHRUG v2.2 Spatial Centroids', source: 'Development Data Lab', status: 'AVAILABLE', role: 'Administrative village centroid points', tip: 'Administrative polygon centroids matching Census 2011 village identifiers.' },
    { name: 'Disaster History (NDMA / SDMA)', source: 'State Disaster Management Authority', status: 'NOT_ACQUIRED', role: 'Historical incident overlay (Tier 1 confirmation pending)', tip: 'Official landslide and flash flood incident database not yet acquired.' },
    { name: 'Critical Infrastructure (Schools, Hospitals)', source: 'OpenStreetMap / Dept. Surveys', status: 'NOT_ACQUIRED', role: 'Infrastructure exposure scoring', tip: 'Road network, lifelines, and emergency facility layers pending.' },
    { name: 'Road Network & Accessibility', source: 'PWD / Survey of India', status: 'NOT_ACQUIRED', role: 'Routable candidate area accessibility', tip: 'Network distance and slope routing to candidate terrain clusters.' },
    { name: 'Land Use / Land Cover (LULC)', source: 'ISRO Bhuvan', status: 'NOT_ACQUIRED', role: 'Forest / protected land exclusion', tip: 'Reserve forest and wildlife sanctuary mask pending ingestion.' },
    { name: 'Capacity Planning Standards', source: 'Urban/Rural Planning Manuals', status: 'NOT_CONFIGURED', role: 'Carrying capacity per household estimation', tip: 'Standard square meters required per household or person unconfigured.' },
  ];

  const limitations = [
    { title: 'No Verified Disaster History Dataset', desc: 'Disaster incident records from NDMA/SDMA were not acquired. Tier 1 priority cannot be confirmed by historical landslide evidence.', tip: 'Historical validation requires disaster event logs.' },
    { title: 'Administrative Centroids vs Settlement Footprints', desc: 'Village coordinates represent administrative reference points. Actual habitations, building clusters, or roads may be closer to hazard terrain than centroid distances indicate.', tip: 'Centroid planar distances are proxy metrics.' },
    { title: 'Census 2011 Baseline Vintage', desc: 'Demographic baseline is from Census 2011 (~15 years old). Demographic expansion and new settlements are not reflected.', tip: 'Population figures represent 2011 baseline.' },
    { title: '30-Meter DEM Spatial Precision', desc: 'Slope and hydrological indices are derived at ~30m pixel resolution. Local site micro-topography requires on-site topographic surveys.', tip: 'Micro-relief variations require total station surveys.' },
    { title: 'Equal-Weight Multi-Hazard Integration', desc: 'Multi-hazard screening integrates terrain susceptibility proxy (50%) and hydrological flood exposure proxy (50%) as an uncalibrated deterministic baseline.', tip: 'Deterministic equal weighting proxy.' },
    { title: 'CA-0001 Unfiltered Extent (~361k ha)', desc: 'Due to unconfigured slope/mapping thresholds, CA-0001 represents a broad contiguous terrain polygon rather than discrete recommended sites.', tip: 'Unconfigured upper slope limit.' },
    { title: 'Carrying Capacity Unestimated', desc: 'No carrying capacity figures are generated due to absence of verified planning standards (area per household/person).', tip: 'Carrying capacity not estimated.' },
    { title: 'No Automated Allocation', desc: 'The system does not allocate specific habitations to candidate areas, requiring official multi-disciplinary planning review.', tip: 'Official multi-disciplinary planning required.' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <BookOpenCheck className="w-5 h-5 text-blue-700" />
            <span>Methodology, Provenance & Transparency</span>
          </h2>
          <InfoTooltip
            title="Scientific Methodology Audit"
            content="Complete transparency audit of data provenance, processing pipeline steps, deterministic decision logic, and scientific limitations."
            side="bottom"
          />
        </div>
        <p className="text-xs text-slate-500 mt-0.5">
          Deterministic Rule-Based Spatial Architecture & Limitations Audit (SIH26191)
        </p>
      </div>

      {/* Pipeline Flow Diagram */}
      <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Processing Pipeline Architecture (Steps 1–10)
          </h3>
          <InfoTooltip
            title="10-Step Deterministic Pipeline"
            content="Step-by-step reproducible GIS processing from raw DEM to decision-support village profiles."
            side="left"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-xs">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 relative group">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-blue-600 font-bold block mb-1">STEPS 1–3</span>
              <InfoTooltip title="DEM Processing" content="Copernicus GLO-30m slope & aspect derivation reprojected to UTM Zone 44N (EPSG:32644)." side="top" />
            </div>
            <p className="font-semibold text-slate-900">DEM Processing</p>
            <p className="text-[11px] text-slate-500 mt-1">Copernicus GLO-30m slope & aspect derivation in UTM 44N</p>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 relative group">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-blue-600 font-bold block mb-1">STEPS 4–6</span>
              <InfoTooltip title="Multi-Hazard Screening" content="Equal-weight integration of terrain slope proxy and hydrological Topographic Wetness Index (TWI)." side="top" />
            </div>
            <p className="font-semibold text-slate-900">Multi-Hazard</p>
            <p className="text-[11px] text-slate-500 mt-1">Terrain susceptibility proxy (50%) + Hydrological TWI proxy (50%)</p>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 relative group">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-blue-600 font-bold block mb-1">STEP 7</span>
              <InfoTooltip title="Candidate Red Zones" content="Extraction of 289 vector polygons representing moderate-to-higher multi-hazard screening zones." side="top" />
            </div>
            <p className="font-semibold text-slate-900">Red Zones</p>
            <p className="text-[11px] text-slate-500 mt-1">289 Candidate Red Zone vector polygons generated</p>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 relative group">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-blue-600 font-bold block mb-1">STEPS 8–9</span>
              <InfoTooltip title="Exposure & Terrain" content="Spatial join of 653 Census habitations and screening of 5 candidate terrain feasibility clusters." side="top" />
            </div>
            <p className="font-semibold text-slate-900">Exposure & Terrain</p>
            <p className="text-[11px] text-slate-500 mt-1">653 Habitations join + 5 candidate screened terrain areas</p>
          </div>

          <div className="p-3 bg-blue-50 rounded-lg border border-blue-200 relative group">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-blue-700 font-bold block mb-1">STEP 10</span>
              <InfoTooltip title="Decision Engine" content="Deterministic, rule-based tier assignment evaluating distance to red zones and centroid hazard class." side="top" />
            </div>
            <p className="font-semibold text-blue-950">Decision Engine</p>
            <p className="text-[11px] text-blue-800 mt-1">Explainable rule-based priority tier assignment</p>
          </div>
        </div>
      </div>

      {/* Data Availability Matrix */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Dataset Acquisition & Availability Matrix
          </h3>
          <InfoTooltip
            title="Data Provenance Matrix"
            content="Tracks which datasets are ingested into the platform vs pending official acquisition from departments."
            side="left"
          />
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/75 text-slate-700 font-semibold text-[11px] border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-4">
                  <div className="flex items-center gap-1">
                    <span>Dataset Name</span>
                    <InfoTooltip title="Dataset Name" content="Name of the spatial or demographic dataset." side="top" />
                  </div>
                </th>
                <th className="py-2.5 px-4">
                  <div className="flex items-center gap-1">
                    <span>Source / Citation</span>
                    <InfoTooltip title="Data Source" content="Publishing agency or open data repository." side="top" />
                  </div>
                </th>
                <th className="py-2.5 px-4">
                  <div className="flex items-center gap-1">
                    <span>Status</span>
                    <InfoTooltip title="Acquisition Status" content="AVAILABLE = in memory; NOT_ACQUIRED = pending; NOT_CONFIGURED = threshold not set." side="top" />
                  </div>
                </th>
                <th className="py-2.5 px-4">
                  <div className="flex items-center gap-1">
                    <span>Pipeline Role</span>
                    <InfoTooltip title="Pipeline Role" content="How this dataset is utilized in the decision-support engine." side="top" />
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-slate-800">
              {dataMatrix.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-50">
                  <td className="py-2.5 px-4 font-semibold text-slate-900">
                    <div className="flex items-center gap-1">
                      <span>{item.name}</span>
                      <InfoTooltip title={item.name} content={item.tip} side="right" />
                    </div>
                  </td>
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
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>Scientific Caveats & Limitations</span>
          </h3>
          <InfoTooltip
            title="Scientific Caveats"
            content="Essential scientific and administrative caveats that evaluators and planners must review."
            side="left"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          {limitations.map((lim, idx) => (
            <div key={idx} className="p-3.5 rounded-lg border border-slate-200 bg-slate-50 space-y-1 relative group">
              <div className="flex items-center justify-between">
                <p className="font-bold text-slate-900">{idx + 1}. {lim.title}</p>
                <InfoTooltip title={lim.title} content={lim.tip} side="top" />
              </div>
              <p className="text-slate-600 text-[11px] leading-relaxed">{lim.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
